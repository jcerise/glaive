## Glaive - A traditional Roguelike
Get in, kill everything standing in your way, grab as much treasure as you can carry, and get out alive.

![Screenshot](/screenshots/hero-shot.png "Glaive")
![Screenshot](/screenshots/inventory.png "Glaive")
![Screenshot](/screenshots/examine.png "Glaive")

Written in Python, using BearLibTerminal for graphics and input handling.

Utilizes a homebrew ECS to handle game logic and complex entity interactions.

Currently implemented features:
- Terminal rendering via BearLibTerminal
- Input via a stackable InputHandler system (allows for changing input mappings based on game state)
- Lightweight ECS with system scheduling and resource insertion
- Mapping capabilities
- Camera
- FOV
- User Interface
- Items, inventory
  - Equipment
  - Item rarities with affixes and prefixes
  - Consumables, with a robust effect system
  - Throwing items
    - Potions shatter and create pools with effects
    - Scrolls cast a targeted spell with potential AoE effects
- Look/Examine system with complete entity descriptions

Upcoming features:
- Actual gameplay (proper map generation, enemies, combat, enemy pathfinding)
- Ranged combat
- Spell casting
- Saving and loading
- Multi-layer dungeons
- AI systems (possibly djikstra maps? behavior trees?)

### AI NOTICE
This is 100% brain coded, AI code generation is not used on this project. AI assitance is used for bug fixing in some areas.
