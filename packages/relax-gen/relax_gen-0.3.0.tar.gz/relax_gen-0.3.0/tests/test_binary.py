import numpy as np
from relax_gen import GEN
import pytest

def funcion_test(x):
    return (np.sin(5*x) + 1.5*np.sin(2*x)) * np.exp(-0.1 * x**2)

def test_alg_binary_aprox():
    """
    Probamos que el algoritmo GEN entregue un valor
    cercano al que esperamos (~0.4).
    """
    modelo = GEN(funcion_test, 
            population=300, 
            i_min=-2, 
            i_max=2
            )

    result = modelo.alg_stn_bin()

    assert result == pytest.approx(0.4, abs=0.2)
