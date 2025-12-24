# Author: Luis Iracheta
# Artificial intelligence engineering
# Universidad Iberoamericana León
import numpy as np



#*****************************Class of algoritm stand binary for rank***********************************
class cl_alg_stn_bin():
    def __init__(self, funtion, population, cant_genes, num_ciclos, 
                 selection_percent, crossing, mutation_percent, i_min,
                    i_max, optimum, select_mode, num_variables):
        self.funtion = funtion
        self.population = population
        self.cant_genes = cant_genes
        self.num_ciclos = num_ciclos
        self.selection_percent = selection_percent
        self.crossing = crossing
        self.mutation_percent = mutation_percent
        self.i_min = i_min
        self.i_max = i_max
        self.optimum = optimum
        self.select_mode = select_mode
        self.chromosome_length = cant_genes * num_variables
        self.num_variables = num_variables

#*****************************Run method***********************************
    def run(self):
        print(f"\n[INFO] Starting algorithm: Standard Binary for {self.select_mode}")
         # Create initial binary population
        self.bin_population = self.create_binary_population(self.population, self.chromosome_length)
        if self.select_mode == 'ranking':
            select_function = self.selection_Ranking
        elif self.select_mode == 'roulette':
            select_function = self.new_population_roulette
      
        
         # Main loop of the algorithm
        for i in range(self.num_ciclos):
            self.Crossing_bin = self.crossing_binary_population(self.bin_population, self.crossing)
            self.Mutations_bin = self.mutations_binary_population(self.Crossing_bin, self.mutation_percent)

            self.select_bin = select_function(self.Mutations_bin, self.selection_percent, self.i_min, self.i_max, self.optimum)

            self.bin_population = self.select_bin.copy()

     
         # Decode the best individual
        best_population_decimal = self.decode_binary_population(self.bin_population, self.i_min, self.i_max)
        best_individual = best_population_decimal[0]

        # Print the best solution found depending on the optimization type
        if self.optimum == 'max':
            print(f"[INFO] Best solution found: {best_individual} with fitness: {self.fitness_binary_population(self.bin_population, self.i_min, self.i_max).max()}")
        else:
            print(f"[INFO] Best solution found: {best_individual} with fitness: {self.fitness_binary_population(self.bin_population, self.i_min, self.i_max).min()}")
        
        print(f"[INFO] Ending algoritm stand binary for {self.select_mode}\n")
        
        # return the best individual
        return best_individual
# *****************************Methods of the algorithm***********************************

    def create_binary_population(self, n, l):
        # n: número de individuos
        # l: longitud de la representación binaria
        self.bin_population = np.random.randint(0, 2, size=(n, l))
        return self.bin_population

    def decode_binary_population(self, P, Imin, Imax):
            # P: población binaria
            # Imin, Imax: límites (asumo los mismos para todas las variables)
            [r, longitud_total] = P.shape # r: N° individuos, longitud_total: N° total de genes
            
            # Longitud de bits por variable, que es self.cant_genes
            c = self.cant_genes 
            num_v = self.num_variables

            # La salida es una matriz (r, num_v) donde cada fila es un individuo 
            # y cada columna es una variable decodificada (x1, x2, ...)
            rescaled_population = np.zeros((r, num_v))

            for i in range(r): # Iteramos sobre cada individuo
                for k in range(num_v): # Iteramos sobre cada variable del individuo
                    # 1. Definir el segmento binario para la variable k
                    start_index = k * c
                    end_index = (k + 1) * c
                    segmento_binario = P[i, start_index:end_index]
                    
                    # 2. Decodificar el segmento a entero (decimal)
                    decimal_val = 0
                    for j in range(c):
                        # Transformar de binario a entero decimal
                        # c-j-1 se usa para dar el peso correcto (de derecha a izquierda)
                        decimal_val += segmento_binario[j] * 2 ** (c - j - 1)
                    
                    # 3. Reescalar el valor decimal al rango [Imin, Imax]
                    # Formula de reescalado: (Imax - Imin) * decimal / (2^c - 1) + Imin
                    rescaled_population[i, k] = (Imax - Imin) * decimal_val / (2 ** c - 1) + Imin

            # Devolvemos la matriz de individuos decodificados (r filas, num_v columnas)
            return rescaled_population

    def fitness_binary_population(self, population, Imin, Imax):
            # x será una matriz (r, num_v)
            x = self.decode_binary_population(population, Imin, Imax)
            
            # Asumiendo que self.funtion acepta una matriz (r, num_v) 
            # y devuelve un vector de fitness (r,)
            fitness = self.funtion(x) 
            return fitness
    

    def crossing_binary_population(self, population, cross_percent):
        [r, c] = population.shape
        # cross_percent: percent of population to cross, between 0 and 0.5
        cross_percent = float(cross_percent)
        num_cross = int(r * cross_percent)
        AuxMatrix = np.zeros((2 * num_cross, c))

        for i in range(num_cross):
            r1 = np.random.randint(0, r, size=(1, 2)) # Select two random parents

            # Select the parents to cross
            father1 = population[r1[0, 0], :]
            father2 = population[r1[0, 1], :]

            # Select the crossing point
            r2 = np.random.randint(0, c)

            # Create the children
            children1 = np.concatenate((father1[0:r2], father2[r2:]))
            children2 = np.concatenate((father2[0:r2], father1[r2:]))

            # Save the children in the auxiliary matrix
            AuxMatrix[2 * i, :] = children1
            AuxMatrix[2 * i + 1, :] = children2
        return AuxMatrix


    def mutations_binary_population(self, population, mutation_percent):
        # population: binary population
        # mutation_percent: percent of genes to mutate, between 0 and 0.5
        [r, c] = population.shape
        n = int(mutation_percent * c * r) # Number of genes to mutate
        for i in range(n):
            r1 = np.random.randint(0, r) # Number aleatory to select the individual to mutate
            r2 = np.random.randint(0, c) # Number aleatory to select the gene to mutate
            
            # Compare the value of the gene and change it
            if (population[r1, r2] == 0):
                population[r1, r2] = 1
            else:
                population[r1, r2] = 0

        return population
    

#*****************************Selection by ranking***********************************

    def selection_Ranking(self, poblacion, select_percent, Imin, Imax, optimum='max'):
        [r, c] = poblacion.shape
        pnew = np.zeros((r, c))  # Matrix to save the new population
        n = int(select_percent * r)  # Number of individuals to select

        fitness = self.fitness_binary_population(poblacion, Imin, Imax).reshape(r, 1)  # Se agrega una columna para guardar su valor Fitness
        expanded_population = np.concatenate([poblacion, fitness], axis=1)  # axis = 0 -> son los renglones, 1 son las columnas

        if (optimum == 'max'):
            indices = np.argsort(expanded_population[:, -1])[::-1]
        elif (optimum == 'min'):
            indices = np.argsort(expanded_population[:, -1])
        else:
            raise ValueError("The optimum parameter must be 'max' or 'min'")
        # Le indicamos con la función argsort que ordene nuesta poblacion, pero como ordena de menos a mayor
        # agregamos el [::1] para que invierta el orden

        organized_population = expanded_population[indices] 
        # Matriz apartir de los indices que ya tenemos

        select_organized_population = organized_population[0:n, :]
        # Seleccionamos hasta el limite establecido "n"

        cleaned_population = select_organized_population[:,0:c]
        # Quitamos el indice de aptitud para quedarnos solo con la población

        for i in range(r):
            for j in range(c):
                if (i < n):
                    pnew[i,j] = cleaned_population[i,j]
                    # Insertamos la población nueva a la matriz de selección
                else:
                    pnew[i, j] = np.random.randint(0,2)
                    # Cuando se acaba, rellenamos con numeros aleatorios
        return pnew
#****************************Selection by Roulette********************************

    def selection_Roulette(self, population, Imin, Imax, optimum='max'):
            [r, c] = population.shape 
            aptitud = self.fitness_binary_population(population, Imin, Imax)
            minFitness = np.min(aptitud)
    # --- Ajuste según el tipo de problema ---
            if optimum == 'min':
                aptitud = np.max(aptitud) - aptitud + 1e-6  # invertir valores
            elif optimum == 'max':
                minFitness = np.min(aptitud)
                if minFitness < 0:
                    aptitud = aptitud - minFitness + 1e-6
            
            # Se evita dividir por 0 en lo siguiente
            if np.sum(aptitud) == 0:
                probabilidad = np.ones(r)/r
            else:
                probabilidad = aptitud / np.sum(aptitud)

            # Se optienen las probabilidades acumuladas
            acumuladas = np.cumsum(probabilidad)

            #Generamos un numero aleatorio para la simulación de la ruleta
            num = np.random.rand()

            # Se busca el individuo donde cae num
            for i in range(r):
                if (num < acumuladas[i]):
                    ganador = population[i,:]
                    break
            return ganador

    def new_population_roulette(self, poblacion, selection_percent, Imin, Imax, optimum,):
        [r,c] = poblacion.shape
        pNew = np.zeros((r,c))

        # Se repite el torneo
        for i in range (r):
            pNew[i,:] = self.selection_Roulette(poblacion, Imin, Imax, optimum)
        return pNew