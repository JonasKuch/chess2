# Chess2

A comprehensive Python implementation of a chess game featuring a graphical user interface, AI-powered move generation using neural networks, and support for various game modes.

## Table of Contents

- [Features](#features)
- [Installation](#installation)
- [Usage](#usage)
- [Project Structure](#project-structure)
- [Modules Overview](#modules-overview)
- [AI and Neural Network](#ai-and-neural-network)
- [GUI Components](#gui-components)
- [Contributing](#contributing)
- [License](#license)

## Features

- **Complete Chess Game Logic**: Full implementation of chess rules including piece movements, check/checkmate detection, castling, en passant, and pawn promotion
- **Graphical User Interface**: Pygame-based GUI with intuitive board rendering and piece visualization
- **AI Opponent**: Neural network-powered bot trained on Leela Chess Zero data for intelligent move generation
- **Move History and Undo/Redo**: Complete move caching system with takeback functionality
- **Game Modes**: Support for human vs human, human vs AI, and AI analysis
- **Data Handling**: Tools for working with pre-processed chess datasets in Leela Chess Zero format with bitboard representations
- **Extensible Architecture**: Modular design allowing easy addition of new features

## Installation

### Prerequisites

- Python 3.8+
- PyTorch (for neural network functionality)
- Pygame (for GUI)
- Stockfish (optional, for enhanced AI analysis)

### Setup

1. Clone the repository:
```bash
git clone <repository-url>
cd chess2
```

2. Create a virtual environment:
```bash
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -e .
```

4. (Optional) Install additional dependencies for AI training:
```bash
pip install torch torchvision torchaudio
pip install stockfish  # For enhanced AI analysis
```

## Usage

### Basic Game

Run a game with GUI:
```python
from chess2.game import Game

game = Game()
game.play()
```

### Headless Game

Run without GUI for testing or AI analysis:
```python
from chess2.game import Game

game = Game(in_gui=False)
# Implement your own game loop or analysis
```

### AI Move Generation

Use the neural network bot:
```python
from chess2.bot.move_generation import MoveGenerator

bot = MoveGenerator("path/to/model.pth")
# Move using the model
next_board = bot.model_move(board.turn, board)
# Or use Stockfish as a reference engine
next_board_sf = bot.stockfish_move(board.turn, board)
```

### Data Processing

Load pre-processed chess training data:
```python
from chess2.bot import ChessDataset
from torch.utils.data import DataLoader

# Load training data from pickle or HDF5 format
dataset = ChessDataset("path/to/data.pkl", start=0, end=1000)
loader = DataLoader(dataset, batch_size=32, shuffle=True)

for boards, flags, prob_idx in loader:
    # boards: bitboard representation
    # flags: additional position information
    # prob_idx: preferred move index
    pass
```

## Project Structure

```
chess2/
├── src/chess2/
│   ├── __init__.py          # Main package exports
│   ├── board.py             # Board representation and state management
│   ├── enums.py             # Color, PieceType, and Action enumerations
│   ├── game.py              # Main game loop and metadata
│   ├── move.py              # Move history, undo/redo, repetition detection
│   ├── players.py           # Player representation
│   ├── bot/                 # AI and machine learning components
│   │   ├── __init__.py
│   │   ├── dataset.py       # PyTorch dataset for training
│   │   ├── neural_network.py # Neural network architecture
│   │   ├── move_generation.py # AI move selection logic
│   │   ├── create_trainingset.py # Data processing utilities
│   │   ├── training.py      # Training scripts
│   │   ├── unpack_leela.py  # Leela Chess Zero data handling
│   │   └── data/            # Training data and models
│   ├── gui/                 # Graphical user interface
│   │   ├── __init__.py
│   │   ├── gui.py           # Main game loop for GUI
│   │   ├── window.py        # Window management
│   │   ├── board_renderer.py # Board visualization
│   │   ├── pieces_renderer.py # Piece rendering
│   │   ├── event_handler.py # Input handling
│   │   ├── button.py        # UI buttons
│   │   ├── start_screen.py  # Game start interface
│   │   └── end_screen.py    # Game end interface
│   └── pieces/              # Chess piece implementations
│       ├── __init__.py
│       ├── base.py          # Base Piece class
│       ├── pawn.py          # Pawn-specific logic
│       ├── rook.py          # Rook-specific logic
│       ├── knight.py        # Knight-specific logic
│       ├── bishop.py        # Bishop-specific logic
│       ├── queen.py         # Queen-specific logic
│       └── king.py          # King-specific logic
├── examples/                # Usage examples
│   └── debug_game.py        # Basic game example
├── tests/                   # Unit tests (currently empty)
├── chess.ipynb              # Jupyter notebook with project overview
├── pyproject.toml           # Project configuration
└── README.md               # This file
```

## Modules Overview

### Core Game Logic

- **`board.py`**: Manages the 8x8 chess board, piece positions, and game state. Handles board initialization, piece placement, and state queries.

- **`game.py`**: Orchestrates the overall game flow, including turn management, move validation, and game end conditions. Integrates GUI and AI components.

- **`move.py`**: Implements move history tracking with undo/redo functionality and threefold repetition detection for draws.

- **`enums.py`**: Defines core enumerations for colors, piece types, and game actions.

- **`players.py`**: Simple player representation with name and color attributes.

### Chess Pieces

Located in `pieces/`, each piece type inherits from a base `Piece` class and implements specific movement rules:

- **Base Piece**: Common functionality for all pieces
- **Pawn**: Handles pawn-specific moves, promotion, and en passant
- **Rook**: Rook movement and castling logic
- **Knight**: L-shaped knight moves
- **Bishop**: Diagonal bishop movement
- **Queen**: Combination of rook and bishop moves
- **King**: King movement, castling, and check detection

### AI and Neural Network

The `bot/` directory contains the machine learning components:

- **`neural_network.py`**: Implements a convolutional neural network architecture inspired by AlphaZero, featuring residual blocks for position evaluation.

- **`move_generation.py`**: Implements policy-driven move selection, including methods for model move (`model_move`), Stockfish move (`stockfish_move`), and all-legal-board generation (`get_all_possible_next_boards`). Supports pawn promotion, randomized selection, and board cloning for safe position exploration.

- **`dataset.py`**: PyTorch Dataset class for loading chess training data from pre-processed pickle or HDF5 files containing bitboard representations.

- **`create_trainingset.py`**: Utility functions for FEN to tensor conversion, UCI move indexing, and legal move mask generation. Used for position analysis and data conversion.

- **`training.py`**: Contains training loops and optimization procedures for the neural network.

### Graphical User Interface

The `gui/` directory provides a complete Pygame-based interface:

- **`gui.py`**: Main game loop handling rendering and user interaction.
- **`window.py`**: Window creation and management.
- **`board_renderer.py`**: Renders the chess board grid and coordinates.
- **`pieces_renderer.py`**: Handles piece sprite rendering and animation.
- **`event_handler.py`**: Processes mouse and keyboard input.
- **`button.py`**: Reusable UI button components.
- **`start_screen.py`**: Initial game setup and menu.
- **`end_screen.py`**: Game over screen with results and replay options.

## AI and Neural Network

The AI system uses a deep convolutional neural network trained on millions of chess positions. The architecture consists of:

1. **Input Layer**: 8x8x12 board representation (12 planes for different piece types and colors)
2. **Convolutional Layers**: Initial 3x3 convolution with 64 filters
3. **Residual Blocks**: 4 residual blocks for deep feature extraction
4. **Policy Head**: Predicts move probabilities (1858 possible moves)
5. **Value Head**: Evaluates position quality (-1 to 1)

Training data is in Leela Chess Zero format, using bitboard representations of chess positions. Data is pre-processed into pickle or HDF5 files containing: board bitboards, position flags, and preferred move indices. The system can be trained from scratch or fine-tuned on existing models.

## GUI Components

The GUI provides an intuitive chess experience with:

- **Visual Board**: Clear 8x8 grid with coordinate labels
- **Piece Sprites**: High-quality piece images with smooth movement
- **Interactive Controls**: Click-to-move interface with piece highlighting
- **Game Information**: Move history, captured pieces, and game status
- **Menu System**: Start screen for game configuration, end screen for results

## Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature-name`
3. Make your changes and add tests
4. Run existing tests: `python -m pytest tests/`
5. Commit your changes: `git commit -am 'Add feature'`
6. Push to the branch: `git push origin feature-name`
7. Submit a pull request

### Development Setup

For development with additional tools:

```bash
pip install -e ".[dev]"
# Install pre-commit hooks
pre-commit install
```

## License

This project is licensed under the MIT License - see the LICENSE file for details.