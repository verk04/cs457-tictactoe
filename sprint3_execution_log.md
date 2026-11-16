# Sprint 3: Execution Log

Local test on localhost (127.0.0.1), port 8080. One server and two clients, each in its own terminal. The game was played to the end (draw), with 9 moves total. In Player 2's 5th turn, an invalid move (cell 2, already taken) was rejected with an `ERROR` and the player retried.

## Server (Terminal 1)

```
archlinux% python3 server.py -p 8080
[SERVER] Listening on 0.0.0.0:8080
[FSM] INIT -> WAITING_FOR_PLAYERS
[SERVER] 127.0.0.1:56778 assigned Player 1
[SERVER] Player 1 sent CONNECT
[SERVER] 127.0.0.1:34304 assigned Player 2
[SERVER] Player 2 sent CONNECT
[FSM] WAITING_FOR_PLAYERS -> GAME_START
[FSM] GAME_START -> PLAYER_TURN
[FSM] PLAYER_TURN -> EVALUATE_MOVE
[SERVER] Player 1 placed P1 in cell 5
[FSM] EVALUATE_MOVE -> CHECK_WIN_DRAW
[FSM] CHECK_WIN_DRAW -> PLAYER_TURN
[FSM] PLAYER_TURN -> EVALUATE_MOVE
[SERVER] Player 2 placed P2 in cell 1
[FSM] EVALUATE_MOVE -> CHECK_WIN_DRAW
[FSM] CHECK_WIN_DRAW -> PLAYER_TURN
[FSM] PLAYER_TURN -> EVALUATE_MOVE
[SERVER] Player 1 placed P1 in cell 7
[FSM] EVALUATE_MOVE -> CHECK_WIN_DRAW
[FSM] CHECK_WIN_DRAW -> PLAYER_TURN
[FSM] PLAYER_TURN -> EVALUATE_MOVE
[SERVER] Player 2 placed P2 in cell 3
[FSM] EVALUATE_MOVE -> CHECK_WIN_DRAW
[FSM] CHECK_WIN_DRAW -> PLAYER_TURN
[FSM] PLAYER_TURN -> EVALUATE_MOVE
[SERVER] Player 1 placed P1 in cell 2
[FSM] EVALUATE_MOVE -> CHECK_WIN_DRAW
[FSM] CHECK_WIN_DRAW -> PLAYER_TURN
[FSM] PLAYER_TURN -> EVALUATE_MOVE
[SERVER] Player 2 placed P2 in cell 8
[FSM] EVALUATE_MOVE -> CHECK_WIN_DRAW
[FSM] CHECK_WIN_DRAW -> PLAYER_TURN
[FSM] PLAYER_TURN -> EVALUATE_MOVE
[SERVER] Player 1 placed P1 in cell 6
[FSM] EVALUATE_MOVE -> CHECK_WIN_DRAW
[FSM] CHECK_WIN_DRAW -> PLAYER_TURN
[FSM] PLAYER_TURN -> EVALUATE_MOVE
[FSM] EVALUATE_MOVE -> PLAYER_TURN
[FSM] PLAYER_TURN -> EVALUATE_MOVE
[SERVER] Player 2 placed P2 in cell 4
[FSM] EVALUATE_MOVE -> CHECK_WIN_DRAW
[FSM] CHECK_WIN_DRAW -> PLAYER_TURN
[FSM] PLAYER_TURN -> EVALUATE_MOVE
[SERVER] Player 1 placed P1 in cell 9
[FSM] EVALUATE_MOVE -> CHECK_WIN_DRAW
[FSM] CHECK_WIN_DRAW -> GAME_OVER
[SERVER] Game over: Draw - the board is full
[FSM] GAME_OVER -> CLEANUP
[FSM] CLEANUP -> WAITING_FOR_PLAYERS
[SERVER] Connection 127.0.0.1:56778 closed
[SERVER] Connection 127.0.0.1:34304 closed
```

## Client 1 — Player 1, X (Terminal 2)

```
archlinux% python3 client.py -i localhost -p 8080
Resolved localhost -> 127.0.0.1
Connected to 127.0.0.1:8080
Waiting for opponent...

========== Game Start ==========
You are Player 1 (X).
Player 1 goes first.

 1 | 2 | 3 
---+---+---
 4 | 5 | 6 
---+---+---
 7 | 8 | 9 

>>> Your Turn (X)
Your move (1-9, or q to quit): 5

 1 | 2 | 3 
---+---+---
 4 | X | 6 
---+---+---
 7 | 8 | 9 

Waiting for Player 2...

 O | 2 | 3 
---+---+---
 4 | X | 6 
---+---+---
 7 | 8 | 9 

>>> Your Turn (X)
Your move (1-9, or q to quit): 7

 O | 2 | 3 
---+---+---
 4 | X | 6 
---+---+---
 X | 8 | 9 

Waiting for Player 2...

 O | 2 | O 
---+---+---
 4 | X | 6 
---+---+---
 X | 8 | 9 

>>> Your Turn (X)
Your move (1-9, or q to quit): 2

 O | X | O 
---+---+---
 4 | X | 6 
---+---+---
 X | 8 | 9 

Waiting for Player 2...

 O | X | O 
---+---+---
 4 | X | 6 
---+---+---
 X | O | 9 

>>> Your Turn (X)
Your move (1-9, or q to quit): 6

 O | X | O 
---+---+---
 4 | X | X 
---+---+---
 X | O | 9 

Waiting for Player 2...

 O | X | O 
---+---+---
 O | X | X 
---+---+---
 X | O | 9 

>>> Your Turn (X)
Your move (1-9, or q to quit): 9

 O | X | O 
---+---+---
 O | X | X 
---+---+---
 X | O | X 


========== Game Over ==========
Draw - the board is full
Score -> Player 1 (X): 0  |  Player 2 (O): 0  |  Draws: 1
```

## Client 2 — Player 2, O (Terminal 3)

```
archlinux% python3 client.py -i localhost -p 8080
Resolved localhost -> 127.0.0.1
Connected to 127.0.0.1:8080

========== Game Start ==========
You are Player 2 (O).
Player 1 goes first.

 1 | 2 | 3 
---+---+---
 4 | 5 | 6 
---+---+---
 7 | 8 | 9 

Waiting for Player 1...

 1 | 2 | 3 
---+---+---
 4 | X | 6 
---+---+---
 7 | 8 | 9 

>>> Your Turn (O)
Your move (1-9, or q to quit): 1

 O | 2 | 3 
---+---+---
 4 | X | 6 
---+---+---
 7 | 8 | 9 

Waiting for Player 1...

 O | 2 | 3 
---+---+---
 4 | X | 6 
---+---+---
 X | 8 | 9 

>>> Your Turn (O)
Your move (1-9, or q to quit): 3

 O | 2 | O 
---+---+---
 4 | X | 6 
---+---+---
 X | 8 | 9 

Waiting for Player 1...

 O | X | O 
---+---+---
 4 | X | 6 
---+---+---
 X | 8 | 9 

>>> Your Turn (O)
Your move (1-9, or q to quit): 8

 O | X | O 
---+---+---
 4 | X | 6 
---+---+---
 X | O | 9 

Waiting for Player 1...

 O | X | O 
---+---+---
 4 | X | X 
---+---+---
 X | O | 9 

>>> Your Turn (O)
Your move (1-9, or q to quit): 2
[SERVER] Invalid move. Pick an empty cell from 1 to 9.
Your move (1-9, or q to quit): 4

 O | X | O 
---+---+---
 O | X | X 
---+---+---
 X | O | 9 

Waiting for Player 1...

 O | X | O 
---+---+---
 O | X | X 
---+---+---
 X | O | X 


========== Game Over ==========
Draw - the board is full
Score -> Player 1 (X): 0  |  Player 2 (O): 0  |  Draws: 1
```