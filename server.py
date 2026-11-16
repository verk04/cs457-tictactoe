#!/usr/bin/env python3
# server.py - tic-tac-toe server
# Main thread accepts connections, each player gets a worker thread,
# and all game state is protected by one lock (see docs/concurrency_design.md).
# Usage: python3 server.py -p 8080

import argparse
import random
import socket
import sys
import threading

from protocol import MessageReader, port_type, send_msg

HOST = "0.0.0.0"
PLAYER_IDS = ("Player 1", "Player 2")
BOARD_MARK = {"Player 1": "P1", "Player 2": "P2"}
EMPTY = "-"

# FSM states from fsm_specification.md
INIT = "INIT"
WAITING_FOR_PLAYERS = "WAITING_FOR_PLAYERS"
GAME_START = "GAME_START"
PLAYER_TURN = "PLAYER_TURN"
EVALUATE_MOVE = "EVALUATE_MOVE"
CHECK_WIN_DRAW = "CHECK_WIN_DRAW"
GAME_OVER = "GAME_OVER"
CLEANUP = "CLEANUP"

# board indexes for every winning line
WIN_LINES = (
    (0, 1, 2), (3, 4, 5), (6, 7, 8),
    (0, 3, 6), (1, 4, 7), (2, 5, 8),
    (0, 4, 8), (2, 4, 6),
)


def other_player(player_id):
    return "Player 2" if player_id == "Player 1" else "Player 1"


class GameState:
    # Everything the threads share. Public methods take the lock;
    # methods starting with _ expect the lock to already be held.

    def __init__(self):
        self.state_lock = threading.Lock()
        self.players = {}       # player_id -> socket
        self.connected = set()  # players that have sent CONNECT
        self.board = [EMPTY] * 9
        self.active_player = None
        self.scores = {"Player 1": 0, "Player 2": 0, "draws": 0}
        self.state = INIT
        self._transition(WAITING_FOR_PLAYERS)

    def reserve_seat(self, sock):
        # called from the accept loop, returns None if the game is full
        with self.state_lock:
            if self.state != WAITING_FOR_PLAYERS:
                return None
            for player_id in PLAYER_IDS:
                if player_id not in self.players:
                    self.players[player_id] = sock
                    return player_id
            return None

    def handle_connect(self, player_id, sock):
        with self.state_lock:
            if self.players.get(player_id) is not sock:
                return
            self.connected.add(player_id)
            print(f"[SERVER] {player_id} sent CONNECT")

            if len(self.connected) < len(PLAYER_IDS):
                self._send(sock, {"msg_type": "LOBBY_WAIT",
                                  "message": "Waiting for opponent..."})
            else:
                self._start_game()

    def handle_move(self, player_id, sock, msg):
        # the whole move is checked and applied inside the lock so two
        # threads can't both change the board at the same time
        with self.state_lock:
            if self.players.get(player_id) is not sock:
                return

            if self.state != PLAYER_TURN:
                self._send_error(sock, "The game has not started yet.")
                return
            if msg.get("player_id") != player_id:
                self._send_error(sock, "player_id does not match your "
                                       "connection.")
                return
            if player_id != self.active_player:
                self._send_error(sock, "It is not your turn.")
                return

            self._transition(EVALUATE_MOVE)
            cell = msg.get("cell")
            if not self._is_valid_cell(cell):
                # bad move, same player tries again
                self._send_error(sock, "Invalid move. Pick an empty cell "
                                       "from 1 to 9.")
                self._transition(PLAYER_TURN)
                return

            self.board[cell - 1] = BOARD_MARK[player_id]
            print(f"[SERVER] {player_id} placed {BOARD_MARK[player_id]} "
                  f"in cell {cell}")

            self._transition(CHECK_WIN_DRAW)
            winner = self._check_winner()
            game_ended = winner is not None or EMPTY not in self.board
            next_player = None if game_ended else other_player(player_id)

            self._broadcast({"msg_type": "STATE_UPDATE",
                             "board": self.board,
                             "active_player": next_player})

            if not game_ended:
                self.active_player = next_player
                self._transition(PLAYER_TURN)
                return

            if winner:
                self.scores[winner] += 1
                result = f"{winner} wins"
            else:
                self.scores["draws"] += 1
                result = "Draw - the board is full"
            self._game_over(result)

    def handle_disconnect(self, player_id, sock):
        with self.state_lock:
            if self.players.get(player_id) is not sock:
                return  # already cleaned up after GAME_OVER

            print(f"[SERVER] {player_id} disconnected")
            del self.players[player_id]
            self.connected.discard(player_id)

            if self.state == WAITING_FOR_PLAYERS:
                return  # no game yet, just free the seat

            # left mid-game, so the other player wins by forfeit
            winner = other_player(player_id)
            self.scores[winner] += 1
            self._game_over(f"{winner} wins - opponent disconnected")

    def send_error(self, player_id, sock, message):
        with self.state_lock:
            if self.players.get(player_id) is sock:
                self._send_error(sock, message)

    def _transition(self, new_state):
        print(f"[FSM] {self.state} -> {new_state}")
        self.state = new_state

    def _start_game(self):
        self._transition(GAME_START)
        self.board = [EMPTY] * 9
        self.active_player = random.choice(PLAYER_IDS)

        # each client also gets told which player it is
        for player_id, sock in self.players.items():
            self._send(sock, {"msg_type": "GAME_START",
                              "first_turn": self.active_player,
                              "player_id": player_id})

        self._transition(PLAYER_TURN)
        self._broadcast({"msg_type": "STATE_UPDATE",
                         "board": self.board,
                         "active_player": self.active_player})

    def _game_over(self, result):
        self._transition(GAME_OVER)
        print(f"[SERVER] Game over: {result}")
        self._broadcast({"msg_type": "GAME_OVER",
                         "result": result,
                         "scores": self.scores})

        # close this match's sockets and go back to the lobby
        self._transition(CLEANUP)
        for sock in self.players.values():
            try:
                sock.shutdown(socket.SHUT_RDWR)  # unblocks that thread's recv
            except OSError:
                pass
            sock.close()
        self.players.clear()
        self.connected.clear()
        self.board = [EMPTY] * 9
        self.active_player = None
        self._transition(WAITING_FOR_PLAYERS)

    def _is_valid_cell(self, cell):
        if not isinstance(cell, int) or isinstance(cell, bool):
            return False
        if not 1 <= cell <= 9:
            return False
        return self.board[cell - 1] == EMPTY

    def _check_winner(self):
        for a, b, c in WIN_LINES:
            mark = self.board[a]
            if mark != EMPTY and mark == self.board[b] == self.board[c]:
                return "Player 1" if mark == "P1" else "Player 2"
        return None

    def _send(self, sock, msg):
        # if a send fails, that client's own thread handles the cleanup
        try:
            send_msg(sock, msg)
        except OSError:
            pass

    def _send_error(self, sock, message):
        self._send(sock, {"msg_type": "ERROR", "message": message})

    def _broadcast(self, msg):
        for sock in self.players.values():
            self._send(sock, msg)


def handle_client(game, sock, addr, player_id):
    # worker thread for one client
    reader = MessageReader(sock)
    try:
        while True:
            msg = reader.read()
            if msg is None:
                break  # client closed the connection

            msg_type = msg.get("msg_type")
            if msg_type == "CONNECT":
                game.handle_connect(player_id, sock)
            elif msg_type == "MOVE":
                game.handle_move(player_id, sock, msg)
            elif msg_type == "DISCONNECT":
                break
            elif msg_type == "MALFORMED":
                game.send_error(player_id, sock, "Malformed message.")
            else:
                game.send_error(player_id, sock,
                                f"Unknown msg_type: {msg_type}")
    except OSError:
        pass  # connection reset, or closed during CLEANUP
    finally:
        game.handle_disconnect(player_id, sock)
        sock.close()
        print(f"[SERVER] Connection {addr[0]}:{addr[1]} closed")


def parse_args():
    parser = argparse.ArgumentParser(
        description="Tic-Tac-Toe game server.",
        epilog="Example: python3 server.py -p 8080")
    parser.add_argument("-p", dest="port", type=port_type, required=True,
                        metavar="PORT",
                        help="listening port (1024-65535)")
    return parser.parse_args()


def main():
    args = parse_args()

    server_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    try:
        server_sock.bind((HOST, args.port))
    except OSError as e:
        print(f"[ERROR] Could not bind to port {args.port}: {e.strerror}")
        sys.exit(1)
    server_sock.listen()
    print(f"[SERVER] Listening on {HOST}:{args.port}")

    game = GameState()

    try:
        # main thread only accepts connections
        while True:
            conn, addr = server_sock.accept()
            player_id = game.reserve_seat(conn)
            if player_id is None:
                print(f"[SERVER] Rejected {addr[0]}:{addr[1]} (game full)")
                try:
                    send_msg(conn, {
                        "msg_type": "ERROR",
                        "message": "Game is full. Try again later.",
                    })
                except OSError:
                    pass
                conn.close()
                continue

            print(f"[SERVER] {addr[0]}:{addr[1]} assigned {player_id}")
            worker = threading.Thread(target=handle_client,
                                      args=(game, conn, addr, player_id),
                                      daemon=True)
            worker.start()
    except KeyboardInterrupt:
        print("\n[SERVER] Shutting down.")
    finally:
        server_sock.close()


if __name__ == "__main__":
    main()