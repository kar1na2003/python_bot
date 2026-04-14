"""
Train neural network value function from game data
"""
import json
import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import Dataset, DataLoader
import numpy as np
from pathlib import Path
from glob import glob
from typing import List, Dict, Any
import argparse

from bot.neural_value import NeuralValueNetwork, FeatureExtractor

class GameDataset(Dataset):
    """Dataset for training neural network from game data"""

    def __init__(self, game_data: List[Dict[str, Any]], feature_extractor: FeatureExtractor):
        self.samples = []
        self.feature_extractor = feature_extractor

        for game in game_data:
            self._process_game(game)

    def _process_game(self, game: Dict[str, Any]):
        """Process a single game into training samples"""
        winner = game.get("winner")
        if winner not in ["TeamA", "TeamB"]:
            return  # Skip draws or invalid games

        # Process each state in the game
        for state_data in game.get("states", []):
            try:
                # Convert state data to BattleState-like object
                # This is a simplified version - in practice you'd reconstruct full state
                mock_state = self._create_mock_state(state_data)

                # Determine target value based on game outcome and state
                if winner == "TeamA":
                    target = 1.0 if state_data.get("current_team") == "TeamA" else -1.0
                else:
                    target = -1.0 if state_data.get("current_team") == "TeamA" else 1.0

                # Add some noise and discount for non-terminal states
                if not state_data.get("is_terminal", False):
                    target *= 0.9  # Discount factor
                    target += np.random.normal(0, 0.1)  # Add noise

                self.samples.append((mock_state, target))

            except Exception as e:
                continue  # Skip problematic states

    def _create_mock_state(self, state_data: Dict[str, Any]) -> Any:
        """Create a mock state object for feature extraction"""
        # This is a placeholder - in real implementation you'd create proper BattleState
        class MockState:
            def __init__(self, data):
                self.data = data
                self.units = []
                self.team_a_units = []
                self.team_b_units = []
                
                # Add mock units based on state_data
                for unit_data in data.get("units", []):
                    mock_unit = MockUnit(unit_data)
                    self.units.append(mock_unit)
                    if mock_unit.team_name == "TeamA":
                        self.team_a_units.append(mock_unit)
                    else:
                        self.team_b_units.append(mock_unit)

                # Add required attributes for neural network
                self.turn_number = data.get("turn", 0)
                self.winner = data.get("winner")
                self.next_unit_info = type('obj', (object,), {'team_name': data.get("current_team", "TeamA")})()
                
                # Create team_a and team_b objects with units attribute
                self.team_a = type('obj', (object,), {'units': self.team_a_units})()
                self.team_b = type('obj', (object,), {'units': self.team_b_units})()

        class MockUnit:
            def __init__(self, data):
                self.health = data.get("health", 10)
                self.x_position = data.get("x", 0)
                self.y_position = data.get("y", 0)
                self.unit_type = data.get("type", "Light")
                self.team_name = data.get("team", "TeamA")
                self.name = f"{self.team_name}_{self.unit_type}_{self.x_position}_{self.y_position}"
                self.is_dead = self.health <= 0  # Add is_dead attribute

        return MockState(state_data)

    def __len__(self):
        return len(self.samples)

    def __getitem__(self, idx):
        state, target = self.samples[idx]
        features = self.feature_extractor.extract(state)
        return features, torch.tensor(target, dtype=torch.float32)

def train_neural_network(training_data_path: str, model_save_path: str,
                        epochs: int = 100, batch_size: int = 32, learning_rate: float = 0.001,
                        resume: bool = False, checkpoint_interval: int = 10):
    """Train the neural network value function"""

    # Load training data
    print(f"Loading training data from {training_data_path}")
    with open(training_data_path, 'r') as f:
        game_data = json.load(f)

    print(f"Loaded {len(game_data)} games")

    # Create dataset
    feature_extractor = FeatureExtractor()
    dataset = GameDataset(game_data, feature_extractor)
    dataloader = DataLoader(dataset, batch_size=batch_size, shuffle=True)

    print(f"Created dataset with {len(dataset)} samples")

    # Create model
    model = NeuralValueNetwork()
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    model.to(device)

    optimizer = optim.Adam(model.parameters(), lr=learning_rate)
    criterion = nn.MSELoss()

    start_epoch = 0
    if resume:
        model_path_obj = Path(model_save_path)
        checkpoint_pattern = f"{model_path_obj.name}.checkpoint_*"
        checkpoint_files = sorted(
            model_path_obj.parent.glob(checkpoint_pattern),
            key=lambda p: int(p.name.rsplit("_", 1)[-1]) if p.name.rsplit("_", 1)[-1].isdigit() else -1
        )
        if checkpoint_files:
            latest_checkpoint = checkpoint_files[-1]
            print(f"Resuming from checkpoint {latest_checkpoint}")
            checkpoint = torch.load(latest_checkpoint, map_location=device)
            model.load_state_dict(checkpoint["model_state_dict"])
            optimizer.load_state_dict(checkpoint["optimizer_state_dict"])
            start_epoch = checkpoint.get("epoch", 0)
        else:
            print("No checkpoint found. Starting from scratch.")

    # Training loop
    print("Starting training...")
    model.train()

    avg_loss = 0.0  # Initialize before loop to avoid UnboundLocalError

    for epoch in range(start_epoch, epochs):
        total_loss = 0.0
        num_batches = 0

        for features, targets in dataloader:
            features = features.to(device)
            targets = targets.to(device)

            optimizer.zero_grad()
            outputs = model(features)
            loss = criterion(outputs.squeeze(), targets)
            loss.backward()
            optimizer.step()

            total_loss += loss.item()
            num_batches += 1

        if num_batches > 0:
            avg_loss = total_loss / num_batches
        print(f"Epoch {epoch + 1}/{epochs}, Loss: {avg_loss:.6f}")


        # Save checkpoint every N epochs if checkpoint_interval is enabled
        if checkpoint_interval > 0 and (epoch + 1) % checkpoint_interval == 0:
            checkpoint_path = f"{model_save_path}.checkpoint_{epoch + 1}"
            torch.save({
                'epoch': epoch + 1,
                'model_state_dict': model.state_dict(),
                'optimizer_state_dict': optimizer.state_dict(),
                'loss': avg_loss,
            }, checkpoint_path)
            print(f"Saved checkpoint to {checkpoint_path}")

    # Save final model
    torch.save({
        'model_state_dict': model.state_dict(),
        'optimizer_state_dict': optimizer.state_dict(),
        'final_loss': avg_loss,
    }, model_save_path)

    print(f"Training complete. Model saved to {model_save_path}")

def generate_training_data(output_path: str, num_games: int = 1000):
    """Generate training data by playing games"""
    print(f"Generating {num_games} games for training data...")

    # This would run games and record states
    # For now, create mock data
    training_games = []

    for game_id in range(num_games):
        game = {
            "game_id": game_id,
            "winner": "TeamA" if np.random.random() > 0.4 else "TeamB",  # Slight bias
            "states": []
        }

        # Generate mock states
        num_states = np.random.randint(10, 50)
        for state_id in range(num_states):
            state = {
                "turn": state_id,
                "current_team": "TeamA" if state_id % 2 == 0 else "TeamB",
                "is_terminal": state_id == num_states - 1,
                "units": []
            }

            # Generate mock units
            for team in ["TeamA", "TeamB"]:
                for i in range(np.random.randint(3, 8)):
                    unit = {
                        "id": f"{team}_unit_{i}",
                        "team": team,
                        "type": np.random.choice(["Light", "Heavy", "Fast", "ShortRange", "LongRange"]),
                        "health": np.random.randint(1, 11),
                        "x": np.random.randint(0, 21),
                        "y": np.random.randint(0, 21)
                    }
                    state["units"].append(unit)

            game["states"].append(state)

        training_games.append(game)

    # Save to file
    with open(output_path, 'w') as f:
        json.dump(training_games, f, indent=2)

    print(f"Generated {len(training_games)} games saved to {output_path}")

def main():
    parser = argparse.ArgumentParser(description="Train neural network value function")
    parser.add_argument("--train", action="store_true", help="Train the neural network")
    parser.add_argument("--generate-data", action="store_true", help="Generate training data")
    parser.add_argument("--data-path", type=str, default="data/training_games.json",
                        help="Path to training data")
    parser.add_argument("--model-path", type=str, default="models/value_network.pth",
                        help="Path to save trained model")
    parser.add_argument("--epochs", type=int, default=100, help="Number of training epochs")
    parser.add_argument("--batch-size", type=int, default=32, help="Batch size")
    parser.add_argument("--learning-rate", type=float, default=0.001, help="Learning rate")
    parser.add_argument("--checkpoint-interval", type=int, default=10, help="Save checkpoint every N epochs")
    parser.add_argument("--resume", action="store_true", help="Resume training from latest checkpoint")
    parser.add_argument("--num-games", type=int, default=1000, help="Number of games to generate")

    args = parser.parse_args()

    if args.generate_data:
        generate_training_data(args.data_path, args.num_games)

    if args.train:
        train_neural_network(
            args.data_path,
            args.model_path,
            args.epochs,
            args.batch_size,
            args.learning_rate,
            args.resume,
            args.checkpoint_interval,
        )

if __name__ == "__main__":
    main()