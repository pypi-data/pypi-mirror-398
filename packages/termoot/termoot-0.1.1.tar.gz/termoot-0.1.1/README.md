# Termoot

A terminal-based multiplayer shooter game built with Python and curses.

## Features

- Single-player mode with AI opponent
- Smooth terminal-based graphics using Unicode characters
- WASD movement controls
- Spacebar to shoot
- Color support for player and enemy
- Win/loss detection with rematch option

## Installation

### From PyPI

```bash
pip install termoot
termoot
```

### From source

```bash
git clone https://github.com/TangoBeee/termoot.git
cd termoot
pip install -e .
termoot
```

## Controls

- **W/A/S/D**: Move up/left/down/right
- **Spacebar**: Shoot
- **ESC**: Quit in-game
- **Arrow Keys**: Navigate menu

## Requirements

- Python 3.10 or higher
- Terminal with Unicode support
- Color terminal (recommended)

## Development

```bash
# Clone the repository
git clone https://github.com/TangoBeee/termoot.git
cd termoot

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install in development mode
pip install -e .

# Run the game
termoot
```

## Project Structure

```
termoot/
├── main.py              # Entry point and lobby
├── game/
│   ├── constants.py     # Game constants
│   ├── state.py         # Game state management
│   └── loop.py          # Main game loop
├── entities/
│   ├── player.py        # Player logic
│   ├── enemy.py         # Enemy AI
│   └── bullet.py        # Bullet mechanics
├── world/
│   └── walls.py         # Map generation
├── ui/
│   ├── draw.py          # Rendering functions
│   ├── dialogs.py       # UI dialogs
│   └── lobby.py         # Menu screen
├── network/             # (Future) Multiplayer
└── audio/               # (Future) Sound effects
```

## License

MIT License

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.
