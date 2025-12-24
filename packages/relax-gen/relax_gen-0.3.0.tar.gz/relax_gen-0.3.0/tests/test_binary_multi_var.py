import numpy as np
from relax_gen import GEN
import pytest

def ackley(valor, a=20, b=0.2, c=2*np.pi):
    x = valor[:,0]
    y = valor[:,1]

    term1 = -a * np.exp(-b * np.sqrt(0.5 * (x**2 + y**2)))
    term2 = -np.exp(0.5 * (np.cos(c * x) + np.cos(c * y)))
    return term1 + term2 + a + np.e

def test_alg_binary_mult_aprox():
    """
    Probamos que el algoritmo GEN entregue un valor
    cercano al que esperamos (0,0).
    """
    modelo = GEN(ackley, 
            population=300, 
            i_min=-2, 
            i_max=2,
            num_variables=2
            )

    result = modelo.alg_stn_bin()

    assert result == pytest.approx(np.array([0, 0]), abs=2.0)