#!/usr/bin/env python3
# client.py - tic-tac-toe client
# Usage: python3 client.py -i server.verkhovoy.edu -p 8080

import argparse
import socket
import sys

from protocol import MessageReader, port_type, send_msg

CONNECT_TIMEOUT = 5  # seconds
SYMBOL = {"P1": "X", "P2": "O"}


def parse_args():
    parser = argparse.ArgumentParser(
        description="Tic-Tac-Toe game client.",
        epilog="Example: python3 client.py -i server.verkhovoy.edu -p 8080")
    parser.add_argument("-i", dest="hostname", required=True,
                        metavar="SERVER_HOSTNAME",
                        help="server DNS hostname or IP address")
    parser.add_argument("-p", dest="port", type=port_type, required=True,
                        metavar="PORT",
                        help="server port (1024-65535)")
    return parser.parse_args()


def resolve_server(hostname):
    # DNS lookup, exit cleanly if it fails instead of crashing
    try:
        return socket.gethostbyname(hostname)
    except (socket.gaierror, UnicodeError):
        print(f"[ERROR] Unable to resolve DNS hostname '{hostname}'.")
        print("Please check your Cisco router DNS configuration "
              "('ip dns server' / 'ip host') or verify domain spelling.")
        sys.exit(1)


def connect(server_ip, port):
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(CONNECT_TIMEOUT)
    try:
        sock.connect((server_ip, port))
    except ConnectionRefusedError:
        print(f"[ERROR] Connection refused by {server_ip}:{port}. "
              "Is the server running?")
        sys.exit(1)
    except OSError as e:
        print(f"[ERROR] Could not connect to {server_ip}:{port}: {e}")
        sys.exit(1)
    sock.settimeout(None)
    return sock


def symbol_for(player_id):
    return "X" if player_id == "Player 1" else "O"


def render_board(board):
    # empty cells show their number so the player knows what to type
    cells = [SYMBOL.get(mark, str(i + 1)) for i, mark in enumerate(board)]
    rows = [f" {cells[r]} | {cells[r + 1]} | {cells[r + 2]} "
            for r in (0, 3, 6)]
    return "\n---+---+---\n".join(rows)


def format_scores(scores):
    return (f"Score -> Player 1 (X): {scores['Player 1']}  |  "
            f"Player 2 (O): {scores['Player 2']}  |  "
            f"Draws: {scores['draws']}")


def try_send(sock, msg):
    # if the server already closed, keep going so we still read GAME_OVER
    try:
        send_msg(sock, msg)
    except OSError:
        pass


def prompt_cell():
    while True:
        text = input("Your move (1-9, or q to quit): ").strip().lower()
        if text in ("q", "quit"):
            return None
        if text.isdigit() and 1 <= int(text) <= 9:
            return int(text)
        print("Please enter a number from 1 to 9.")


def take_turn(sock, player_id):
    # returns False if the player quit
    cell = prompt_cell()
    if cell is None:
        try_send(sock, {"msg_type": "DISCONNECT", "player_id": player_id})
        return False
    try_send(sock, {"msg_type": "MOVE", "player_id": player_id,
                    "cell": cell})
    return True


def play(sock):
    send_msg(sock, {"msg_type": "CONNECT"})
    reader = MessageReader(sock)
    player_id = None
    my_turn = False

    while True:
        msg = reader.read()
        if msg is None:
            print("\n[INFO] Server closed the connection.")
            return

        msg_type = msg.get("msg_type")

        if msg_type == "LOBBY_WAIT":
            print(msg.get("message", "Waiting for opponent..."))

        elif msg_type == "GAME_START":
            player_id = msg["player_id"]
            print("\n========== Game Start ==========")
            print(f"You are {player_id} ({symbol_for(player_id)}).")
            print(f"{msg['first_turn']} goes first.")

        elif msg_type == "STATE_UPDATE":
            print()
            print(render_board(msg["board"]))
            print()
            active = msg.get("active_player")
            my_turn = (active == player_id)
            if active is None:
                continue  # game ended, GAME_OVER is next
            if my_turn:
                print(f">>> Your Turn ({symbol_for(player_id)})")
                if not take_turn(sock, player_id):
                    return
            else:
                print(f"Waiting for {active}...")

        elif msg_type == "ERROR":
            print(f"[SERVER] {msg.get('message')}")
            if player_id is None and "full" in msg.get("message", ""):
                return
            if my_turn:  # bad move, try again
                if not take_turn(sock, player_id):
                    return

        elif msg_type == "GAME_OVER":
            print("\n========== Game Over ==========")
            print(msg.get("result"))
            if "scores" in msg:
                print(format_scores(msg["scores"]))
            return

        else:
            print(f"[WARN] Unknown message from server: {msg}")


def main():
    args = parse_args()
    server_ip = resolve_server(args.hostname)
    print(f"Resolved {args.hostname} -> {server_ip}")
    sock = connect(server_ip, args.port)
    print(f"Connected to {server_ip}:{args.port}")

    try:
        play(sock)
    except (KeyboardInterrupt, EOFError):
        print("\nGoodbye!")
    except OSError as e:
        print(f"\n[ERROR] Connection lost: {e}")
    finally:
        sock.close()


if __name__ == "__main__":
    main()