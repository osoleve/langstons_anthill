# Getting Started

Copy this folder to wherever you want to work, then open it in Claude Code.

The `CLAUDE.md` file is the instruction set. Claude Code will read it automatically.

The `plugins/cards/starter_cards.py` is a bootstrap plugin that will fire introductory 
cards to get the game systems building. It unregisters itself once all starters have 
fired or become ineligible.

## First Session

Just tell Claude Code to read CLAUDE.md and start building the engine. The starter 
cards will fire automatically once the tick loop is running and conditions are met.

## Adding New Cards Later

Drop new card plugins in `plugins/cards/`. They should follow the same pattern:
- `PLUGIN_ID` constant
- `register(bus, state_path, log_path)` function  
- `unregister(bus)` function (optional)
- Register handlers on the event bus for whatever events trigger your card

Cards from external models (Gemini, Kimi, o3, etc.) are just plugins that make API 
calls and emit `card_drawn` events with whatever prompts come back.

## The Point

There isn't a designed game here. The game emerges from Claude responding to cards, 
getting bored, and building systems to satisfy requirements. After a week or a month, 
look at what exists. That's the game.
