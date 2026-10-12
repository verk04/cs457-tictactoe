# Protocol Blueprint
## Framing Rule

Every message is a JSON object, ending with a newline character, \n. As the server receives data from players, it will add data into a buffer, waiting for a \n before processing. Once the new line is found, everything before it is treated as a message, and everything after it is a new message.

Wire stream example (two messages sent back-to-back):

{"msg_type":"CONNECT"}\n{"msg_type":"MOVE","player_id":"Player 1","cell":5}\n

Without the \n separating them, the server would see one unbroken blob of text and wouldn't know where the first message ends and the second begins.

## Message Types

## CONNECT — Client → Server

json
{
  "msg_type": "CONNECT"
}

## LOBBY_WAIT — Server → Client

json
{
  "msg_type": "LOBBY_WAIT",
  "message": "Waiting for opponent..."
}

## GAME_START — Server → Both Clients

json
{
  "msg_type": "GAME_START",
  "first_turn": "Player 1"
}

## MOVE — Client → Server

json
{
  "msg_type": "MOVE",
  "player_id": "Player 1",
  "cell": 5
}

## STATE_UPDATE — Server → Both Clients

json
{
  "msg_type": "STATE_UPDATE",
  "board": ["-", "P1", "-", "-", "-", "-", "-", "-", "-"],
  "active_player": "Player 2"
}

## ERROR — Server → Client

json
{
  "msg_type": "ERROR",
  "message": "It is not your turn."
}

## DISCONNECT — Client → Server

json
{
  "msg_type": "DISCONNECT",
  "player_id": "Player 1"
}

## GAME_OVER — Server → Client(s)

json
{
  "msg_type": "GAME_OVER",
  "result": "Player 2 wins - opponent disconnected"
}