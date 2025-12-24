import math

SQRT_2P = math.sqrt(2 * math.pi)


def local_moivre_laplace(n: int, k: int, p: float) -> float:
    """
    Локальная формула Муавра–Лапласа:
    P(X = k) ≈ 1 / sqrt(npq) * phi(x)
    """
    if not (0 < p < 1):
        raise ValueError("p должно быть в интервале (0, 1)")

    q = 1 - p
    x = (k - n * p) / math.sqrt(n * p * q)
    phi = math.exp(-(x ** 2 / 2)) / SQRT_2P
    return phi / math.sqrt(n * p * q)


def integral_moivre_laplace(n: int, k1: int, k2: int, p: float) -> float:
    """
    Интегральная формула Муавра–Лапласа:
    P(k1 <= X <= k2) ≈ phi(x2) - phi(x1)
    """
    if not (0 < p < 1):
        raise ValueError("p должно быть в интервале (0, 1)")

    q = 1 - p

    def phi(x):
        return 0.5 * (1 + math.erf(x / math.sqrt(2)))

    x1 = (k1 - n * p) / math.sqrt(n * p * q)
    x2 = (k2 - n * p) / math.sqrt(n * p * q)

    return phi(x2) - phi(x1)