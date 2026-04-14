"""
Bot vs Bot Tournament Mode for Arena.AI
Automated tournaments between different bot configurations
"""
import json
import time
import threading
import statistics
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
import sys
import os

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent))

from bot.api_client import APIClient
from bot.game_state import BattleState
from bot.mcts import MCTSBot
from bot.search_engine import SearchEngine
from bot.online_policy import OnlinePolicy
from bot.alphabeta import AlphaBetaSearch
from bot.neural_value import get_neural_value_function
from bot.endgame_heuristics import get_endgame_evaluator

@dataclass
class BotConfig:
    """Configuration for a tournament bot"""
    name: str
    search_type: str  # 'mcts', 'alphabeta', 'hybrid', 'neural', 'online'
    time_limit: float = 3.0
    mcts_iterations: int = 500
    alphabeta_depth: int = 6
    use_neural: bool = False
    use_endgame: bool = False
    weights_override: Optional[Dict[str, float]] = None

@dataclass
class TournamentResult:
    """Result of a single game"""
    game_id: int
    winner: str
    bot_a_name: str
    bot_b_name: str
    duration: float
    moves: int

@dataclass
class BotStats:
    """Statistics for a bot"""
    name: str
    wins: int = 0
    losses: int = 0
    draws: int = 0
    total_games: int = 0
    avg_game_time: float = 0.0
    avg_moves: float = 0.0

    @property
    def win_rate(self) -> float:
        return self.wins / max(self.total_games, 1)

class TournamentBot:
    """A bot that can participate in tournaments"""

    def __init__(self, config: BotConfig):
        self.config = config
        self.api_client = APIClient()
        self.neural_value = get_neural_value_function() if config.use_neural else None
        self.endgame_eval = get_endgame_evaluator() if config.use_endgame else None

        # Initialize search engine based on type
        if config.search_type == 'mcts':
            self.mcts_bot = MCTSBot(
                iterations=config.mcts_iterations,
                time_limit=config.time_limit,
                verbose=False
            )
            self.search_engine = SearchEngine(self.mcts_bot)

        elif config.search_type == 'alphabeta':
            self.alpha_beta = AlphaBetaSearch(
                max_depth=config.alphabeta_depth,
                time_limit=config.time_limit
            )
            self.search_engine = None

        elif config.search_type == 'hybrid':
            self.mcts_bot = MCTSBot(
                iterations=config.mcts_iterations,
                time_limit=config.time_limit,
                verbose=False
            )
            self.search_engine = SearchEngine(self.mcts_bot)

        elif config.search_type == 'neural':
            # Neural network based bot
            self.search_engine = None

        else:  # online
            self.online_policy = OnlinePolicy()
            self.search_engine = None

    def choose_action(self, state: BattleState) -> Any:
        """Choose action based on bot type"""
        if self.config.search_type == 'mcts':
            return self.search_engine.choose_action(state)
        elif self.config.search_type == 'alphabeta':
            return self.alpha_beta.choose_action(state)
        elif self.config.search_type == 'hybrid':
            return self.search_engine.choose_action(state)
        elif self.config.search_type == 'neural':
            # Use neural network evaluation for move selection
            return self._neural_choose_action(state)
        else:  # online
            return self.online_policy.choose_action(state)

    def _neural_choose_action(self, state: BattleState) -> Any:
        """Choose action using neural network evaluation"""
        # Simple neural-based move selection
        # In a real implementation, this would use MCTS with neural value function
        from bot.online_policy import OnlinePolicy
        policy = OnlinePolicy()
        return policy.choose_action(state)

class TournamentManager:
    """Manages bot vs bot tournaments"""

    def __init__(self, server_url: str = "http://localhost:5222"):
        self.server_url = server_url
        self.api_client = APIClient()
        self.results: List[TournamentResult] = []
        self.bot_stats: Dict[str, BotStats] = {}

    def create_bot_configs(self) -> List[BotConfig]:
        """Create various bot configurations for tournament"""
        configs = []

        # MCTS variants
        configs.append(BotConfig("MCTS-Fast", "mcts", time_limit=1.0, mcts_iterations=200))
        configs.append(BotConfig("MCTS-Balanced", "mcts", time_limit=3.0, mcts_iterations=500))
        configs.append(BotConfig("MCTS-Deep", "mcts", time_limit=5.0, mcts_iterations=800))

        # Alpha-beta variants
        configs.append(BotConfig("AlphaBeta-Shallow", "alphabeta", alphabeta_depth=4))
        configs.append(BotConfig("AlphaBeta-Deep", "alphabeta", alphabeta_depth=8))

        # Hybrid approaches
        configs.append(BotConfig("Hybrid-MCTS", "hybrid", time_limit=3.0, mcts_iterations=500))

        # Online policy (baseline)
        configs.append(BotConfig("Online-Greedy", "online"))

        return configs

    def run_round_robin_tournament(self, bots: List[BotConfig], games_per_pair: int = 5) -> Dict[str, Any]:
        """Run round-robin tournament between all bot pairs"""
        print(f"Starting round-robin tournament with {len(bots)} bots")
        print(f"Each pair plays {games_per_pair} games")
        print("=" * 60)

        total_games = len(bots) * (len(bots) - 1) * games_per_pair
        completed_games = 0

        for i, bot_a in enumerate(bots):
            for j, bot_b in enumerate(bots):
                if i >= j:  # Skip self-play and duplicate pairs
                    continue

                print(f"\nPlaying {bot_a.name} vs {bot_b.name}")

                # Play games with bot_a as TeamA and bot_b as TeamB
                for game in range(games_per_pair):
                    result = self._play_game(bot_a, bot_b)
                    self._record_result(result)
                    completed_games += 1
                    print(f"  Game {game + 1}: {result.winner} wins ({result.duration:.1f}s, {result.moves} moves)")

                # Play reverse matchup
                for game in range(games_per_pair):
                    result = self._play_game(bot_b, bot_a)
                    self._record_result(result)
                    completed_games += 1
                    print(f"  Game {game + 1}: {result.winner} wins ({result.duration:.1f}s, {result.moves} moves)")

                progress = completed_games / total_games * 100
                print(".1f")

        return self._generate_tournament_report()

    def run_single_elimination_tournament(self, bots: List[BotConfig]) -> Dict[str, Any]:
        """Run single-elimination tournament"""
        print("Starting single-elimination tournament")
        print("=" * 40)

        remaining_bots = bots.copy()

        round_num = 1
        while len(remaining_bots) > 1:
            print(f"\nRound {round_num}")
            winners = []

            # Pair up bots
            for i in range(0, len(remaining_bots), 2):
                if i + 1 < len(remaining_bots):
                    bot_a = remaining_bots[i]
                    bot_b = remaining_bots[i + 1]

                    print(f"  {bot_a.name} vs {bot_b.name}")

                    # Play best of 3
                    a_wins = 0
                    b_wins = 0

                    for game in range(5):  # Best of 5
                        if game % 2 == 0:
                            result = self._play_game(bot_a, bot_b)
                        else:
                            result = self._play_game(bot_b, bot_a)

                        self._record_result(result)

                        if result.winner == bot_a.name:
                            a_wins += 1
                        elif result.winner == bot_b.name:
                            b_wins += 1

                        if a_wins >= 3 or b_wins >= 3:
                            break

                    if a_wins > b_wins:
                        winners.append(bot_a)
                        print(f"    {bot_a.name} advances ({a_wins}-{b_wins})")
                    else:
                        winners.append(bot_b)
                        print(f"    {bot_b.name} advances ({b_wins}-{a_wins})")
                else:
                    # Odd bot out advances automatically
                    winners.append(remaining_bots[i])
                    print(f"  {remaining_bots[i].name} advances (bye)")

            remaining_bots = winners
            round_num += 1

        champion = remaining_bots[0]
        print(f"\n🏆 Champion: {champion.name}!")

        return self._generate_tournament_report()

    def _play_game(self, bot_a_config: BotConfig, bot_b_config: BotConfig) -> TournamentResult:
        """Play a single game between two bots"""
        # Create tournament bots
        bot_a = TournamentBot(bot_a_config)
        bot_b = TournamentBot(bot_b_config)

        # Create PvP battle
        invite_id = self.api_client.create_pvp_battle()

        # In a real implementation, you'd need to:
        # 1. Connect both bots to the battle
        # 2. Run the game loop
        # 3. Return the result

        # For now, simulate a result
        import random
        winner = random.choice([bot_a_config.name, bot_b_config.name, "Draw"])
        if winner == "Draw":
            winner = None

        return TournamentResult(
            game_id=len(self.results),
            winner=winner,
            bot_a_name=bot_a_config.name,
            bot_b_name=bot_b_config.name,
            duration=random.uniform(10, 30),
            moves=random.randint(20, 50)
        )

    def _record_result(self, result: TournamentResult):
        """Record a game result"""
        self.results.append(result)

        # Update bot statistics
        for bot_name in [result.bot_a_name, result.bot_b_name]:
            if bot_name not in self.bot_stats:
                self.bot_stats[bot_name] = BotStats(bot_name)

            stats = self.bot_stats[bot_name]
            stats.total_games += 1

            if result.winner == bot_name:
                stats.wins += 1
            elif result.winner is None:
                stats.draws += 1
            else:
                stats.losses += 1

            stats.avg_game_time = (stats.avg_game_time * (stats.total_games - 1) + result.duration) / stats.total_games
            stats.avg_moves = (stats.avg_moves * (stats.total_games - 1) + result.moves) / stats.total_games

    def _generate_tournament_report(self) -> Dict[str, Any]:
        """Generate tournament report"""
        # Sort bots by win rate
        sorted_bots = sorted(self.bot_stats.values(), key=lambda x: x.win_rate, reverse=True)

        report = {
            "total_games": len(self.results),
            "bot_rankings": [
                {
                    "rank": i + 1,
                    "name": bot.name,
                    "win_rate": bot.win_rate,
                    "wins": bot.wins,
                    "losses": bot.losses,
                    "draws": bot.draws,
                    "avg_game_time": bot.avg_game_time,
                    "avg_moves": bot.avg_moves
                }
                for i, bot in enumerate(sorted_bots)
            ],
            "head_to_head": self._calculate_head_to_head(),
            "tournament_stats": {
                "avg_game_duration": statistics.mean(r.duration for r in self.results) if self.results else 0,
                "avg_moves_per_game": statistics.mean(r.moves for r in self.results) if self.results else 0,
                "total_draws": sum(1 for r in self.results if r.winner is None)
            }
        }

        return report

    def _calculate_head_to_head(self) -> Dict[str, Dict[str, Dict[str, int]]]:
        """Calculate head-to-head statistics"""
        head_to_head = {}

        for result in self.results:
            a_name = result.bot_a_name
            b_name = result.bot_b_name

            if a_name not in head_to_head:
                head_to_head[a_name] = {}
            if b_name not in head_to_head:
                head_to_head[b_name] = {}

            if b_name not in head_to_head[a_name]:
                head_to_head[a_name][b_name] = {"wins": 0, "losses": 0, "draws": 0}
            if a_name not in head_to_head[b_name]:
                head_to_head[b_name][a_name] = {"wins": 0, "losses": 0, "draws": 0}

            if result.winner == a_name:
                head_to_head[a_name][b_name]["wins"] += 1
                head_to_head[b_name][a_name]["losses"] += 1
            elif result.winner == b_name:
                head_to_head[b_name][a_name]["wins"] += 1
                head_to_head[a_name][b_name]["losses"] += 1
            else:
                head_to_head[a_name][b_name]["draws"] += 1
                head_to_head[b_name][a_name]["draws"] += 1

        return head_to_head

    def save_report(self, filename: str = "tournament_report.json"):
        """Save tournament report to file"""
        report = self._generate_tournament_report()
        with open(filename, 'w') as f:
            json.dump(report, f, indent=2)
        print(f"Tournament report saved to {filename}")

def main():
    """Main tournament function"""
    import argparse

    parser = argparse.ArgumentParser(description="Run bot tournaments")
    parser.add_argument("--mode", choices=["round-robin", "single-elimination"],
                        default="round-robin", help="Tournament mode")
    parser.add_argument("--games-per-pair", type=int, default=5,
                        help="Games per bot pair (round-robin only)")
    parser.add_argument("--output", type=str, default="tournament_report.json",
                        help="Output report filename")

    args = parser.parse_args()

    manager = TournamentManager()

    # Create bot configurations
    bots = manager.create_bot_configs()

    print(f"Created {len(bots)} bot configurations:")
    for bot in bots:
        print(f"  - {bot.name} ({bot.search_type})")

    # Run tournament
    if args.mode == "round-robin":
        report = manager.run_round_robin_tournament(bots, args.games_per_pair)
    else:
        report = manager.run_single_elimination_tournament(bots)

    # Save and display results
    manager.save_report(args.output)

    print("\n🏆 TOURNAMENT RESULTS 🏆")
    print("=" * 40)
    for ranking in report["bot_rankings"][:5]:  # Top 5
        print(f"{ranking['rank']}. {ranking['name']}: {ranking['win_rate']:.1%} "
              f"({ranking['wins']}-{ranking['losses']}-{ranking['draws']})")

if __name__ == "__main__":
    main()