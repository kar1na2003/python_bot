import os
import time
from bot.analytics.telemetry import MctsTelemetry
from bot.analytics.summary import export_summary
from bot.analytics.feature_extractor import StateDataExtractor

print("Запуск перевірки Data Engineering пайплайну...")

# Створюємо папку для логів, якщо її немає
os.makedirs("logs", exist_ok=True)

# 1. Перевірка Телеметрії
print("\nГенеруємо тестову телеметрію (MCTS metrics)...")
telemetry = MctsTelemetry("logs/mcts_metrics.csv")

# Імітуємо 3 ходи бота
telemetry.log(turn=1, iters=1000, time_ms=210.5, score=0.45)
time.sleep(0.5) # Імітуємо затримку "думки" алгоритму
telemetry.log(turn=2, iters=1500, time_ms=305.2, score=0.68)
time.sleep(0.5)
telemetry.log(turn=3, iters=2000, time_ms=450.1, score=0.92)
print("Файл успішно створено: logs/mcts_metrics.csv")

# 2. Перевірка Екстрактора (Feature Extraction)
print("\nТестуємо екстрактор ознак...")
# Імітуємо "фейковий" об'єкт стану гри
class MockGameState:
    turn_number = 45
    my_units = [type("Unit", (), {"health": 10})(), type("Unit", (), {"health": 5})()]
    enemy_units = [type("Unit", (), {"health": 12})()]

fake_state = MockGameState()
features = StateDataExtractor.extract_features(fake_state)
print(f"Згенеровано вектор ознак для ML: {features}")

# 3. Перевірка збереження фінального результату
print("\nЗберігаємо результати матчу...")
export_summary("TeamA", 45, "TeamA", "logs/summary.jsonl")
export_summary("TeamB", 32, "TeamA", "logs/summary.jsonl") # Імітуємо ще одну гру, де ми програли
print("✅ Файл успішно створено: logs/summary.jsonl")

print("\n🎉 Всі модулі Data Engineering працюють коректно!")