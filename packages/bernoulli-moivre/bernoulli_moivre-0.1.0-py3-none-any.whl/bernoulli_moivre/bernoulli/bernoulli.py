import math

def bernoulli_probability(n: int, k: int, p: float) -> float:
    """
    Формула Бернулли:
    P(X = k) = C(n, k) * p^k * (1 - p)^(n - k)
    """
    if not (0 <= k <= n):
        return 0.0
    if not (0 <= p <= 1):
        raise ValueError("p должно быть в диапазоне [0, 1]")

    c = math.comb(n, k)
    return c * (p ** k) * ((1 - p) ** (n - k))