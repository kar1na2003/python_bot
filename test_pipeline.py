import os
import time
import random
from bot.analytics.telemetry import MctsTelemetry
from bot.analytics.summary import export_summary
from bot.analytics.action_logger import ActionLogger, export_summary_csv

print("🚀 Запуск генерації ВЕЛИКОГО датасету (Телеметрія + Аналітика)...")

os.makedirs("logs", exist_ok=True)

# Очищаємо старі файли
for file in ["mcts_metrics.csv", "summary.jsonl", "detailed_actions.csv", "matches_summary.csv"]:
    if os.path.exists(f"logs/{file}"):
        os.remove(f"logs/{file}")

telemetry = MctsTelemetry("logs/mcts_metrics.csv")
action_logger = ActionLogger("logs/detailed_actions.csv")

# Типи юнітів та дії для генерації
unit_types = ["Heavy", "ShortRange", "LongRange", "Fast", "Light"]
actions = ["Move", "Attack", "SkipTurn"]
columns = "ABCDEFGHIJ"

for game_id in range(1, 101): # 100 ігор
    total_turns = random.randint(30, 60)
    print(f"Імітація гри {game_id}...")
    
    for turn in range(1, total_turns + 1):
        # 1. Записуємо телеметрію
        iters = random.choice([1000, 2000, 3000, 5000])
        time_ms = iters * random.uniform(0.18, 0.25)
        score = min(0.99, max(0.1, 0.4 + (turn / total_turns) * 0.5 + random.uniform(-0.1, 0.1)))
        telemetry.log(turn=turn, iters=iters, time_ms=round(time_ms, 2), score=round(score, 4))
        
        # 2. Генеруємо детальні кроки для цієї гри (3-5 дій за хід)
        for _ in range(random.randint(3, 5)):
            team = random.choice(["TeamA", "TeamB"])
            unit_id = random.randint(1, 10)
            u_name = f"{team}_{unit_id}"
            u_type = random.choice(unit_types)
            act = random.choice(actions)
            target = f"{'TeamB' if team == 'TeamA' else 'TeamA'}_{random.randint(1,10)}" if act == "Attack" else "None"
            hp = random.randint(0, 15)
            pos = f"{random.choice(columns)}{random.randint(1, 20)}"
            
            action_logger.log_action(game_id, team, u_name, u_type, act, target, hp, pos)
            
    # Зберігаємо результат матчу
    winner = "TeamA" if random.random() > 0.3 else "TeamB"
    is_victory = winner == "TeamA"
    
    # Зберігаємо і в старий формат, і в нову табличку
    export_summary(winner, total_turns, "TeamA", "logs/summary.jsonl")
    export_summary_csv(game_id, winner, is_victory, "logs/matches_summary.csv")

print("\n✅ Готово! У папці logs створено 4 ідеальних файли для Data Аналітика!")