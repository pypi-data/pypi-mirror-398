from bernoulli_moivre.moivre_laplace.moivre_laplace import local_moivre_laplace,integral_moivre_laplace


def test_local_formula():
    value = local_moivre_laplace(n=100, k=50, p=0.5)
    assert value > 0


def test_integral_formula():
    value = integral_moivre_laplace(n=100, k1=45, k2=55, p=0.5)
    assert 0 < value < 1