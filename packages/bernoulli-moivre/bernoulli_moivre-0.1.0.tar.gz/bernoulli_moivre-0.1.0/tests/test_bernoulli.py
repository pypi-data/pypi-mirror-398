from bernoulli_moivre.bernoulli.bernoulli import bernoulli_probability

def test_bernoulli_basic():
    result = bernoulli_probability(n=10, k=5, p=0.5)
    assert abs(result - 0.24609375) < 1e-6


def test_bernoulli_zero():
    assert bernoulli_probability(5, 10, 0.3) == 0.0