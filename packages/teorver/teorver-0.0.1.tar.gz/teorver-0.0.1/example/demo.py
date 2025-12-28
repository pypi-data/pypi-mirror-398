from src.teorver import *

print("\n1. КОМБИНАТОРИКА:")
print(f"   Факториал 6: {factorial(6)}")
print(f"   Перестановки из 4: P(4) = {permutations(4)}")
print(f"   Размещения из 5 по 2: A(5,2) = {arrangements(5, 2)}")
print(f"   Сочетания из 5 по 2: C(5,2) = {combinations(5, 2)}")
print(f"   Размещения с повторениями 3^2: {arrangements_with_repetition(3, 2)}")
print(f"   Сочетания с повторениями из 3 по 2: {combinations_with_repetition(3, 2)}")

print("\n2. ВЕРОЯТНОСТЬ:")
print(f"   Классическая вероятность (орёл): {classical_probability(1, 2)}")
print(f"   Вероятность Бернулли (2 успеха из 4): {bernoulli_probability(4, 2, 0.5):.4f}")

print("\n3. РЕАЛЬНЫЙ ПРИМЕР:")
print("   В лотерее 100 билетов, 5 выигрышных.")
print(f"   Вероятность выиграть с 1 билетом: {classical_probability(5, 100):.3f}")
print(f"   Вероятность выиграть с 3 билетами: {classical_probability(15, 100):.3f}")