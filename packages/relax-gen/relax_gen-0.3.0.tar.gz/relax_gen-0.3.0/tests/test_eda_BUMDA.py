import numpy as np
from relax_gen import GEN
import pytest
import pandas as pd

bd = pd.read_csv("tests/data.csv")


def test_alg_eda_aprox():
    model = GEN(datos=bd.values,
                population=200,
                num_variables=6,
                num_cycles=2000,
                i_max=10,
                i_min=-10
                )
    
    resultado, fitness = model.alg_eda()

    assert fitness == pytest.approx(0, abs=100.0)