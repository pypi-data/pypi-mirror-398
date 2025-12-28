from math import comb

def classical_probability(favorable: int, total: int) -> float:
    if total <= 0:
        raise ValueError("Общее число исходов должно быть положительным")
    if favorable < 0 or favorable > total:
        raise ValueError("Некорректное число благоприятных исходов")
    return favorable / total


def bernoulli_probability(n: int, k: int, p: float) -> float:
    if not (0 <= p <= 1):
        raise ValueError("p должно быть в [0,1]")
    return comb(n, k) * (p ** k) * ((1 - p) ** (n - k))


def expected_value(values: list, probabilities: list) -> float:
    if len(values) != len(probabilities):
        raise ValueError("Списки должны быть одинаковой длины")
    if abs(sum(probabilities) - 1) > 1e-6:
        raise ValueError("Сумма вероятностей должна быть равна 1")
    return sum(x * p for x, p in zip(values, probabilities))


def total_probability(hypotheses_probs: list, conditional_probs: list) -> float:
    if len(hypotheses_probs) != len(conditional_probs):
        raise ValueError("Списки должны быть одинаковой длины")
    if abs(sum(hypotheses_probs) - 1) > 1e-6:
        raise ValueError("Сумма вероятностей гипотез должна быть равна 1")

    return sum(
        ph * pa_h
        for ph, pa_h in zip(hypotheses_probs, conditional_probs)
    )


def bayes_probability(
    hypothesis_index: int,
    hypotheses_probs: list,
    conditional_probs: list
) -> float:
    if hypothesis_index < 0 or hypothesis_index >= len(hypotheses_probs):
        raise IndexError("Некорректный индекс гипотезы")

    p_a = total_probability(hypotheses_probs, conditional_probs)
    if p_a == 0:
        raise ZeroDivisionError("Полная вероятность равна 0")

    return (
        hypotheses_probs[hypothesis_index]
        * conditional_probs[hypothesis_index]
        / p_a
    )