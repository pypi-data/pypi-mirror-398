from .gen import GEN
from .algorithms.alg_bin import cl_alg_stn_bin
from .algorithms.alg_quantum import cl_alg_quantum
from .algorithms.alg_eda import cl_alg_eda
from .algorithms.alg_gp import cl_alg_gp

class RelaxGEN(GEN):
    def __init__(self, funtion=None, population=None, **kwargs):
        super().__init__(funtion, population, **kwargs)
        # Almacena los parámetros específicos como atributos directos
        self.num_genes = kwargs.get("num_genes")
        self.num_cycles = kwargs.get("num_cycles")
        self.selection_percent = kwargs.get("selection_percent")
        self.crossing = kwargs.get("crossing")
        self.mutation_percent = kwargs.get("mutation_percent")
        self.i_min = kwargs.get("i_min")
        self.i_max = kwargs.get("i_max")
        self.optimum = kwargs.get("optimum")
        self.num_qubits = kwargs.get("num_qubits")
        self.select_mode = kwargs.get("select_mode")
        self.num_variables = kwargs.get("num_variables")
        self.data = kwargs.get("data")
        self.possibility_selection = kwargs.get("possibility_selection")
        self.metric = kwargs.get("metric")
        self.model = kwargs.get("model")
        self.max_depth = kwargs.get("max_depth")

    
    def alg_stn_bin(self):
        algorithm = cl_alg_stn_bin(
            funtion=self.funtion,
            population=self.population,
            cant_genes=self.num_genes,
            cant_ciclos=self.num_cycles,
            selection_percent=self.selection_percent,
            crossing=self.crossing,
            mutation_percent=self.mutation_percent,
            i_min=self.i_min,
            i_max=self.i_max,
            optimum=self.optimum,
            num_variables=self.num_variables,
            select_mode=self.select_mode
        )
        return algorithm.run()

    def alg_quantum(self):
        algorithm = cl_alg_quantum(
            funtion=self.funtion,
            population=self.population,
            num_qubits=self.num_qubits,
            cant_ciclos=self.num_cycles,
            mutation_percent=self.mutation_percent,
            i_min=self.i_min,
            i_max=self.i_max,
            optimum=self.optimum
        )
        return algorithm.run()
    
    def alg_eda(self):
        algorithm = cl_alg_eda(
            datos = self.data,
            population=self.population,
            num_variables=self.num_variables,
            num_ciclos=self.num_ciclos,
            i_min=self.i_min,
            i_max=self.i_max,
            possibility_selection=self.possibility_selection,
            metric=self.metric,
            model=self.model
        )
        return algorithm.run()
    
    def alg_gp(self): # Genetic programming algorithm
        algorithm = cl_alg_gp(
            data = self.data,
            population = self.population,
            num_ciclos = self.num_ciclos,
            max_depth = self.max_depth
        )
        return algorithm.run()