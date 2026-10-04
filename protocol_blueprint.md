# Application-Layer Protocol Blueprint — Tic-Tac-Toe

## 1. Transport Layer & Packet Framing Mechanism

- **Transport Protocol:** TCP
- **Serialization Format:** JSON
- **Framing Mechanism:** Newline-Delimited JSON (`\n` framing)

### Framing Rule

Every JSON message is UTF-8 encoded as a single line and terminated by a newline
character `\n` (0x0A). The JSON object itself must not contain a literal
unescaped newline (standard `json.dumps()` output satisfies this). The receiver
accumulates incoming bytes into a stream buffer until a `\n` is encountered,
extracts the complete line, and deserializes it with `json.loads()`.

This handles both TCP coalescing (multiple messages arriving in one `recv()`
chunk) and fragmentation (one message split across multiple `recv()` calls),
since the receiver only acts once a full line has been assembled in the buffer.

### Receiver Pattern (Python)

```python
buffer = ""

def handle_incoming(sock, buffer):
    data = sock.recv(4096).decode("utf-8")
    if not data:
        return None  # peer closed connection (EOF)
    buffer += data
    messages = []
    while "\n" in buffer:
        line, buffer = buffer.split("\n", 1)
        if line.strip():
            messages.append(json.loads(line))
    return messages, buffer
```

### Wire Stream Example (Continuous Stream)

```
{"msg_type":"CONNECT","player_id":"Player_1","timestamp":1727970000}\n{"msg_type":"MOVE","player_id":"Player_1","payload":{"row":0,"col":2},"timestamp":1727970005}\n
```

---

## 2. Application Message Types

All messages share this envelope:

```json
{
  "msg_type": "<TYPE>",
  "player_id": "<string>",
  "payload": { },
  "timestamp": 1727970000
}
```

| Message Type | Direction | Purpose |
|---|---|---|
| `CONNECT` | Client → Server | Client requests to join the game room with a player alias. |
| `LOBBY_WAIT` | Server → Client | Server tells Player 1 it is waiting for Player 2 to connect. |
| `GAME_START` | Server → Clients | Server starts the game and assigns roles (X / O) and turn order. |
| `MOVE` | Client → Server | Active player submits a cell selection (row, col). |
| `STATE_UPDATE` | Server → Clients | Server broadcasts the updated board and whose turn is active. |
| `ERROR` | Server → Client | Server rejects an out-of-turn move, invalid coordinates, or malformed message. |
| `DISCONNECT` | Client → Server | Client signals intentional departure/quit before closing the socket. |
| `GAME_OVER` | Server → Clients | Server broadcasts the final outcome: Win / Draw / Forfeit. |

### 2.1 `CONNECT`
```json
{
  "msg_type": "CONNECT",
  "player_id": "Alice",
  "payload": {},
  "timestamp": 1727970000
}
```

### 2.2 `LOBBY_WAIT`
```json
{
  "msg_type": "LOBBY_WAIT",
  "player_id": "SERVER",
  "payload": {
    "message": "Waiting for an opponent to connect..."
  },
  "timestamp": 1727970001
}
```

### 2.3 `GAME_START`
```json
{
  "msg_type": "GAME_START",
  "player_id": "SERVER",
  "payload": {
    "your_symbol": "X",
    "opponent_id": "Bob",
    "first_turn": "Alice"
  },
  "timestamp": 1727970002
}
```

### 2.4 `MOVE`
```json
{
  "msg_type": "MOVE",
  "player_id": "Alice",
  "payload": {
    "row": 0,
    "col": 2
  },
  "timestamp": 1727970005
}
```
- `row`, `col`: integers, zero-indexed, range `0-2`.

### 2.5 `STATE_UPDATE`
```json
{
  "msg_type": "STATE_UPDATE",
  "player_id": "SERVER",
  "payload": {
    "board": ["-", "-", "X", "-", "O", "-", "-", "-", "-"],
    "active_player": "Bob"
  },
  "timestamp": 1727970006
}
```
- `board`: flat array of 9 cells, each `"X"`, `"O"`, or `"-"` (empty), read left-to-right, top-to-bottom.

### 2.6 `ERROR`
```json
{
  "msg_type": "ERROR",
  "player_id": "SERVER",
  "payload": {
    "code": "OUT_OF_TURN",
    "message": "It is not your turn."
  },
  "timestamp": 1727970007
}
```
- `code` values used: `OUT_OF_TURN`, `CELL_OCCUPIED`, `INVALID_COORDINATES`, `MALFORMED_MESSAGE`.

### 2.7 `DISCONNECT`
```json
{
  "msg_type": "DISCONNECT",
  "player_id": "Alice",
  "payload": {
    "reason": "player_quit"
  },
  "timestamp": 1727970010
}
```

### 2.8 `GAME_OVER`
```json
{
  "msg_type": "GAME_OVER",
  "player_id": "SERVER",
  "payload": {
    "result": "WIN",
    "winner": "Alice",
    "reason": "three_in_a_row"
  },
  "timestamp": 1727970011
}
```
- `result` values: `WIN`, `DRAW`, `FORFEIT`.
- `reason` values: `three_in_a_row`, `board_full`, `opponent_disconnected`.

---

## 3. Connection Termination & Socket Lifecycle Management

### 3.1 Graceful Disconnect (Application Layer)
A client intending to quit sends a `DISCONNECT` message before calling
`sock.close()`. This lets the server notify the opponent, declare a win by
forfeit, and free server resources immediately, without waiting on a socket
timeout.

### 3.2 Transport-Layer Teardown (TCP FIN)
When a process exits normally or calls `sock.close()`, the OS performs the
standard TCP 4-way FIN handshake. On the server, the next `recv()` call on
that socket returns `b""` (zero bytes) — this is the EOF signal, **not** an
exception:

```python
data = sock.recv(4096)
if not data:
    logger.info("Peer disconnected (EOF / TCP FIN).")
    handle_client_disconnect(player_id)
```
A receive loop that doesn't check `if not data: break` will spin at 100% CPU
re-reading an empty string, so this check is always present in our dispatch
loop.

### 3.3 Abrupt Termination (TCP RST / Network Drops)
If a client is killed abruptly (`kill -9`, crash, severed CML link) with no
FIN handshake, the server's next read or write on that socket raises an
exception rather than returning cleanly. We catch these explicitly:

```python
try:
    data = sock.recv(4096)
    if not data:
        trigger_state_transition("CLIENT_DISCONNECTED")
except (ConnectionResetError, BrokenPipeError, ConnectionAbortedError) as e:
    logger.warning(f"Connection lost abruptly: {e}")
    trigger_state_transition("CLIENT_DISCONNECTED")
```

In both the clean (EOF) and abrupt (exception) cases, the server transitions
to the same `CLIENT_DISCONNECTED` handling path: the remaining player is
declared the winner by forfeit, a `GAME_OVER` (`FORFEIT`) message is sent to
any still-connected client, and the server cleans up and resets for a new
game.
