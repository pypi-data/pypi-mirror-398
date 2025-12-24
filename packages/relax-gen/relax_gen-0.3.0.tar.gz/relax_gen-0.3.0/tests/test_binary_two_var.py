import numpy as np
from relax_gen import GEN
import pytest

# ----------------- Función Objetivo -----------------
def sphere_function_3d(valor):
    # La suma de los cuadrados de todas las variables
    fitness = np.sum(valor**2, axis=1)
    return fitness
# ----------------------------------------------------

def test_alg_binary_sphere_3d_aprox():
    """
    Prueba que el AG binario multivariable encuentre el óptimo 
    cercano a [0, 0, 0] para la Función Esférica.
    """
    
    # 1. Instanciar el modelo con 3 variables y minimización
    modelo = GEN(funtion=sphere_function_3d, 
                 population=10, 
                 num_genes=20,     # 20 bits/variable -> Cromosoma total de 60 bits
                 num_cycles=15,    
                 selection_percent=0.5,
                 crossing=0.8, 
                 mutation_percent=0.01,
                 i_min=-5.12,       
                 i_max=5.12,
                 optimum='min',     
                 select_mode='ranking',
                 num_variables=3    # Tres variables
                 )

    result = modelo.alg_stn_bin() 
    
    # 3. Definir el óptimo esperado
    esperado = np.array([0.0, 0.0, 0.0])

    assert result == pytest.approx(esperado, abs=1.0)