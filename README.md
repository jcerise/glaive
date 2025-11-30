## Glaive - A traditional Roguelike
Get in, kill everything standing in your way, grab as much treasure as you can carry, and get out alive.

![Screenshot](/screenshots/hero-shot.png "Glaive")

Written in Python, using BearLibTerminal for graphics and input handling.

Utilizes a homebrew ECS to handle game logic and complex entity interactions.

Currently implemented features:
- Terminal rendering via BearLibTerminal
- Input via a stackable InputHandler system (allows for changing input mappings based on game state)
- Lightweight ECS with system scheduling and resource insertion
- Mapping capabilities
- Camera
- FOV

Upcoming features:
- User Interface
- Actual gameplay (proper map generation, enemies, combat, enemy pathfinding)
- Items, inventory
- Equipment
- Ranged combat
- Spell casting
- Saving and loading
- Multi-layer dungeons
- AI systems (possibly djikstra maps?)

### AI NOTICE
This is 100% brain coded, AI code generation is not used on this project
