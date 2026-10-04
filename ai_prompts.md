# AI Prompting & Constraint Strategy

## 1. Permitted AI Tools
- Claude (Anthropic)
- GitHub Copilot (inline suggestions only, for boilerplate)

## 2. Purpose

This document records how AI coding assistants will be constrained in Sprint
3 so that generated code implements the exact wire protocol defined in
`protocol_blueprint.md` and the exact state transitions defined in
`fsm_specification.md`, rather than inventing its own message formats or
game-loop structure.

## 3. Constraint Strategy

1. **Spec-first prompting.** Every implementation prompt pastes the relevant
   section of `protocol_blueprint.md` (message schema) or
   `fsm_specification.md` (Mermaid diagram) directly into the prompt as
   ground truth, and explicitly instructs the model not to deviate from the
   field names, types, or state names given.
2. **One component per prompt.** Rather than asking for the whole
   client/server at once, requests are scoped narrowly (e.g., "implement only
   the `recv_exact`/newline-framing receive loop," "implement only the
   `EVALUATE_MOVE` win-check function") so output can be checked against the
   spec line-by-line.
3. **Explicit framing/field lock.** Prompts state the exact framing rule
   (newline-delimited JSON) and exact JSON keys (`msg_type`, `player_id`,
   `payload`, `timestamp`) so the model cannot substitute an alternate
   serialization or key naming scheme.
4. **Verification pass.** After generation, the resulting code is manually
   diffed against the message tables in `protocol_blueprint.md` and the
   Mermaid states in `fsm_specification.md` to confirm every message type and
   every state/transition listed there is actually implemented.

## 4. Example Constrained Prompt

```
You are implementing a function for a Tic-Tac-Toe network server.

Use exactly this message envelope (do not change field names or add new
top-level keys):

{
  "msg_type": "<TYPE>",
  "player_id": "<string>",
  "payload": { },
  "timestamp": <unix epoch int>
}

Framing rule: each message is a single-line JSON object terminated by \n.
Do not use length-prefix framing.

Implement only the server-side `evaluate_move(board, row, col, active_player)`
function described by the EVALUATE_MOVE state in fsm_specification.md:
- Reject if row/col not in range 0-2 -> return ERROR code INVALID_COORDINATES
- Reject if board[row][col] is not empty -> return ERROR code CELL_OCCUPIED
- Otherwise place the mark and return success

Do not implement networking, win-checking, or any other state in this
function.
```

## 5. Implementation Risk Management

- Protocol and FSM are finalized *before* any code is written (Sprint 1
  deliverable), so AI-generated code has an unambiguous target to match.
- Work is broken into the same components named in the FSM (`CONNECT`
  handling, `MOVE` validation, `CHECK_WIN_DRAW`, disconnect handling) so
  progress can be tracked and tested state-by-state rather than all at once.
- Prior coursework experience with Python sockets (CS 457 labs) is used to
  sanity-check AI output rather than accepting it uncritically, particularly
  around the `recv()` buffering and exception-handling patterns shown in
  `protocol_blueprint.md`.
- Time buffer: core gameplay logic (board/win-check) is implemented first
  since it has no networking dependency, followed by the server loop, then
  the client — so a partially-working milestone exists at each step before
  the Sprint 3 deadline.
