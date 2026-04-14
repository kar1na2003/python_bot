"""
Neural Network Value Function for Arena.AI bot
Uses PyTorch for position evaluation
"""
import torch
import torch.nn as nn
import torch.optim as optim
import numpy as np
from typing import List, Dict, Any, Optional
import json
import os
from pathlib import Path

class NeuralValueNetwork(nn.Module):
    """Neural network for position evaluation"""

    def __init__(self, input_size: int = 266, hidden_sizes: List[int] = [128, 64, 32]):
        super(NeuralValueNetwork, self).__init__()

        layers = []
        prev_size = input_size

        for hidden_size in hidden_sizes:
            layers.extend([
                nn.Linear(prev_size, hidden_size),
                nn.ReLU(),
                nn.BatchNorm1d(hidden_size),
                nn.Dropout(0.1)
            ])
            prev_size = hidden_size

        # Output layer for value estimation (-1 to 1)
        layers.append(nn.Linear(prev_size, 1))
        layers.append(nn.Tanh())

        self.network = nn.Sequential(*layers)

    def forward(self, x):
        # Handle single sample for inference
        if x.dim() == 1:
            x = x.unsqueeze(0)

        # Store original training mode
        was_training = self.training

        # For single sample inference, temporarily set to eval mode
        if not was_training and x.size(0) == 1:
            # Batch norm will use running stats in eval mode
            pass  # Already in eval mode
        elif was_training and x.size(0) == 1:
            # Temporarily switch to eval mode for single sample
            self.eval()

        output = self.network(x)

        # Restore training mode if it was changed
        if was_training and x.size(0) == 1:
            self.train()

        # Squeeze back if input was 1D
        if output.size(0) == 1:
            output = output.squeeze(0)

        return output

class NeuralValueFunction:
    """Neural network-based position evaluator"""

    def __init__(self, model_path: Optional[str] = None):
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.model = NeuralValueNetwork().to(self.device)
        self.optimizer = optim.Adam(self.model.parameters(), lr=0.001)
        self.criterion = nn.MSELoss()

        if model_path and os.path.exists(model_path):
            self.load_model(model_path)

        self.training_data = []
        self.feature_extractor = FeatureExtractor()

    def extract_features(self, state) -> torch.Tensor:
        """Extract features from game state"""
        return self.feature_extractor.extract(state)

    def evaluate_position(self, state, for_team: str = "TeamA") -> float:
        """Evaluate position using neural network"""
        self.model.eval()  # Ensure eval mode
        with torch.no_grad():
            features = self.extract_features(state)
            value = self.model(features).item()

            # Adjust for team perspective
            if for_team == "TeamB":
                value = -value

            return value

    def train_step(self, states: List[Any], targets: List[float], epochs: int = 10):
        """Train the network on batch of positions"""
        self.model.train()

        features_list = []
        for state in states:
            features = self.extract_features(state)
            features_list.append(features)

        X = torch.stack(features_list).to(self.device)
        y = torch.tensor(targets, dtype=torch.float32).to(self.device)

        for epoch in range(epochs):
            self.optimizer.zero_grad()
            outputs = self.model(X).squeeze()
            loss = self.criterion(outputs, y)
            loss.backward()
            self.optimizer.step()

        return loss.item()

    def save_model(self, path: str):
        """Save model to file"""
        torch.save({
            'model_state_dict': self.model.state_dict(),
            'optimizer_state_dict': self.optimizer.state_dict(),
        }, path)

    def load_model(self, path: str):
        """Load model from file"""
        checkpoint = torch.load(path, map_location=self.device)
        self.model.load_state_dict(checkpoint['model_state_dict'])
        self.optimizer.load_state_dict(checkpoint['optimizer_state_dict'])

class FeatureExtractor:
    """Extract numerical features from game state"""

    def __init__(self):
        self.max_units = 16  # Maximum units per team
        self.feature_size = self._calculate_feature_size()

    def _calculate_feature_size(self) -> int:
        """Calculate total feature vector size"""
        # Unit features: health, position, type, etc.
        unit_features = 8  # health, x, y, type_onehot(4), team
        unit_total = unit_features * self.max_units * 2  # Both teams

        # Global features
        global_features = 10  # turn number, arena size, etc.

        return unit_total + global_features

    def extract(self, state) -> torch.Tensor:
        """Extract feature vector from state"""
        features = []

        # Extract unit features for both teams
        for team_name in ["TeamA", "TeamB"]:
            team_units = [u for u in state.units if u.team_name == team_name]
            team_features = self._extract_team_features(team_units, team_name)
            features.extend(team_features)

        # Global features
        global_features = self._extract_global_features(state)
        features.extend(global_features)

        return torch.tensor(features, dtype=torch.float32)

    def _extract_team_features(self, units: List[Any], team_name: str) -> List[float]:
        """Extract features for a team"""
        features = []

        # Sort units by some consistent order (by name)
        units = sorted(units, key=lambda u: u.name)

        for i in range(self.max_units):
            if i < len(units):
                unit = units[i]
                unit_features = [
                    unit.health / 10.0,  # Normalize health
                    unit.x_position / 20.0,  # Normalize position
                    unit.y_position / 20.0,
                    1.0 if unit.unit_type == "Light" else 0.0,
                    1.0 if unit.unit_type == "Heavy" else 0.0,
                    1.0 if unit.unit_type == "Fast" else 0.0,
                    1.0 if unit.unit_type == "ShortRange" else 0.0,
                    1.0 if team_name == "TeamA" else 0.0
                ]
            else:
                # Padding for missing units
                unit_features = [0.0] * 8

            features.extend(unit_features)

        return features

    def _extract_global_features(self, state) -> List[float]:
        """Extract global game features"""
        all_units = state.team_a.units + state.team_b.units
        return [
            getattr(state, 'turn_number', 0) / 100.0,  # Normalize turn number (default to 0 if not present)
            len([u for u in all_units if u.team_name == "TeamA" and not u.is_dead]) / 8.0,
            len([u for u in all_units if u.team_name == "TeamB" and not u.is_dead]) / 8.0,
            1.0 if state.winner else 0.0,
            1.0 if state.winner == "TeamA" else 0.0,
            1.0 if state.winner == "TeamB" else 0.0,
            0.0,  # Reserved
            0.0,  # Reserved
            0.0,  # Reserved
            0.0   # Reserved
        ]

# Global instance
neural_value_function = NeuralValueFunction()

def get_neural_value_function():
    """Get the global neural value function instance"""
    return neural_value_function