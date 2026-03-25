# Chess2

A comprehensive chess game implementation in Python featuring a graphical user interface, AI bot with neural network evaluation, and tools for training chess models.

## Features

- **Complete Chess Logic**: Full implementation of chess rules including all piece movements, special moves (castling, en passant, pawn promotion), and game states (check, checkmate, stalemate)
- **Graphical User Interface**: Beautiful pygame-based GUI with piece images and interactive gameplay
- **AI Bot**: Neural network-powered chess engine trained on large datasets
- **Training Tools**: Scripts for processing chess databases, training neural networks, and evaluating models
- **Game Analysis**: Move validation, position evaluation, and game state tracking

## Installation

### Prerequisites

- Python 3.8+
- pip

### Install Dependencies

```bash
# Clone the repository
git clone <repository-url>
cd chess2

# Install the package
pip install -e .

# Install additional dependencies for GUI and AI
pip install pygame torch h5py numpy orjson python-chess
```

## Usage

### Playing the Game

#### GUI Mode (Recommended)

```python
from chess2.game import Game

# Start a new game with GUI
game = Game()
game.play()
```

This launches the graphical chess interface where you can:
- Play against another human player
- Play against the AI bot
- Use takeback functionality
- View game history

#### Command Line Mode

```python
from chess2.board import Board
from chess2 import Color

# Initialize a new game
board = Board()
board.initialize()

# Make moves programmatically
# Example: Move pawn from e2 to e4
pawn = board.grid[1][4]  # e2 in 0-based coordinates
pawn.move((4, 3))  # e4

# Update the board display
board.update_grid()
```

### AI Bot

The project includes a trained neural network chess bot:

```python
from chess2.bot import MoveGenerator

# Load a trained model
bot = MoveGenerator("src/chess2/bot/saved_models/model_new.pth")

# Get the best move for the current position
best_move = bot.get_best_move(board, Color.WHITE)
```

## Project Structure

```
chess2/
├── src/chess2/
│   ├── __init__.py          # Package initialization
│   ├── board.py             # Chess board representation and logic
│   ├── enums.py             # Color, PieceType, Action enums
│   ├── game.py              # Main game loop and GUI integration
│   ├── move.py              # Move representation and history
│   ├── players.py           # Player classes
│   ├── pieces/              # Chess piece implementations
│   │   ├── base.py          # Abstract piece base class
│   │   ├── pawn.py          # Pawn movement logic
│   │   ├── rook.py          # Rook movement logic
│   │   ├── knight.py        # Knight movement logic
│   │   ├── bishop.py        # Bishop movement logic
│   │   ├── queen.py         # Queen movement logic
│   │   └── king.py          # King movement logic
│   ├── gui/                 # Graphical user interface
│   │   ├── gui.py           # Main GUI loop
│   │   ├── window.py        # Window management
│   │   ├── board_renderer.py # Board drawing
│   │   ├── pieces_renderer.py # Piece rendering
│   │   ├── button.py        # UI buttons
│   │   ├── event_handler.py # Input handling
│   │   ├── start_screen.py  # Game start screen
│   │   └── end_screen.py    # Game end screen
│   └── bot/                 # AI and training components
│       ├── __init__.py
│       ├── neural_network.py # PyTorch neural network model
│       ├── move_generation.py # AI move generation
│       ├── dataset.py       # Training data handling
│       ├── training.py      # Model training script
│       ├── create_trainingset.py # Dataset creation from PGN
│       ├── dataset_filter.py # Data filtering utilities
│       ├── unpack_leela.py  # Leela Chess Zero data processing
│       └── data/            # Training datasets
├── examples/                # Usage examples
├── tests/                   # Unit tests
└── pyproject.toml           # Project configuration
```

## Training the AI

### Data Preparation

The bot uses chess games from Lichess database for training:

```bash
# Process raw game data
python -m chess2.bot.create_trainingset

# Filter and prepare training data
python -m chess2.bot.dataset_filter
```

### Training the Model

```python
# Run training script
python src/chess2/bot/training.py
```

The training process includes:
- Policy head for move prediction
- Value head for position evaluation
- Self-play data augmentation
- Validation and testing

### Model Evaluation

Evaluate trained models on test datasets:

```python
from chess2.bot import ChessDataset
import torch

# Load test data
test_data = ChessDataset("src/chess2/bot/data/testing_data.h5")

# Load model and evaluate
model = torch.load("saved_models/model_new.pth")
# ... evaluation code
```

## Development

### Running Tests

```bash
python -m pytest tests/
```

### Code Style

The project follows standard Python conventions. Use type hints and docstrings for new code.

### Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## Dependencies

- **pygame**: GUI framework
- **torch**: Neural network framework
- **h5py**: HDF5 file handling for datasets
- **numpy**: Numerical computations
- **orjson**: Fast JSON processing
- **python-chess**: Chess move validation and PGN handling

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- Chess piece images and GUI assets
- Lichess database for training data
- PyTorch community for neural network tools
- Python-chess library for chess utilities
