# AI Prompting Strategy

When using an AI tool to help write the code for this project, I will give it 
the exact message formats and field names from protocol_blueprint.md and the 
exact states from fsm_specification.md, and tell it to follow them exactly 
instead of inventing its own format. I will also ask it to build one piece 
at a time (like just the MOVE handling, or just the EVALUATE_MOVE check) so 
I can check that the output actually matches my schema before moving on.

## Example Prompt

"Using this exact JSON message format: {"msg_type": "MOVE", "player_id": 
"Player 1", "cell": 5} - write a Python function that checks if a cell 
number (1-9) is valid and not already taken on the board. Do not change the 
field names. Do not add extra fields."