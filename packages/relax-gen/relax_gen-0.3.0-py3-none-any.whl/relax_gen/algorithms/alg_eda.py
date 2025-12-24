import numpy as np
import pandas as pd


class cl_alg_eda():
    def __init__(self, datos, population, num_variables, num_ciclos,
                 i_min, i_max, possibility_selection, metric, model):
        self.x = datos[:,0]
        self.y = datos[:,1]
        self.datos = datos
        self.population = population
        self.num_variables = num_variables
        self.num_ciclos = num_ciclos
        self.i_min = i_min
        self.i_max = i_max
        self.possibility_selection = possibility_selection
        self.metric = metric
        self.model = model
        

    def run(self):
        population_EDA = self.create_individual(self.population, self.num_variables, self.i_min, self.i_max)
        best_solution = None
        best_fitness = float('inf')

        #  Identify the model to be used
        if self.model == "polynomial":
            self.model = self.polynomial_model
        elif self.model == "exponential":
            self.model = self.exponential_model
        elif self.model == "sine":
            self.model = self.sine_model
        else:
            raise ValueError("Modelo no soportado")

        for k in range(self.num_ciclos):
            fitness = self.fitness_eda(population_EDA, self.x, self.y, self.model, self.metric)
            num_elite = max(2, int(self.population * self.possibility_selection))
            index_elite = np.argsort(fitness)[:num_elite]
            population_elite = population_EDA[index_elite, :]

            mu, sigma = self.BUMDA_media_std(population_elite, 
                                             fitness[index_elite], 
                                             self.i_min, self.i_max)
            
            population_EDA = self.create_new_individual(self.population, mu, sigma)

            idx_best = np.argmin(fitness)
            if fitness[idx_best] < best_fitness:
                best_fitness = fitness[idx_best]
                best_solution = population_EDA[idx_best].copy()

        return best_solution, best_fitness
            





    def create_individual(self, population, num_variables, i_min, i_max):
        poblacion = np.zeros((population, num_variables))
        for i in range(population):
            for j in range(num_variables):
                poblacion[i][j] = np.random.uniform(i_min, i_max)
        return poblacion

    def fitness_eda(self, population, x, y, model, metric):
        r = population.shape[0]
        fitness = np.zeros(r)

        for i in range(r):
            y_pred = model(x, population[i])

            if metric == "mse":
                fitness[i] = np.mean((y - y_pred) ** 2)

            elif metric == "rmse":
                fitness[i] = np.sqrt(np.mean((y - y_pred) ** 2))

            elif metric == "mae":
                fitness[i] = np.mean(np.abs(y - y_pred))

            elif metric == "norm":
                fitness[i] = np.linalg.norm(y - y_pred)

            else:
                raise ValueError("Métrica no soportada")

        return fitness

    def selection_eda(self, population, fitness, possibility_selection):
        [r,c] = population.shape
        ordered_indexes = np.argsort(fitness)
        size_elite = int(r * possibility_selection)
        population_elite = np.zeros((size_elite, c))
        for i in range(size_elite):
            population_elite[i,:] = population[ordered_indexes[i],:]
        return population_elite

    def distribution_estimation(self, population_elite):
        '''
        In this function, we estimate the distribution of 
        the elite population and return the mean and 
        standard deviations of each variable.
        Inputs:
        population_elite: numpy array of shape (num_elite, num_variables)
            The elite population selected based on fitness.
        '''
        dim = population_elite.shape[1] # We get the number of variables for each individual
        media = np.zeros(dim)
        stds = np.zeros(dim)

        for i in range(dim):
            media[i] = np.mean(population_elite[:,i])
            stds[i] = np.std(population_elite[:,i])

        return media, stds # of the variables

    def create_new_individual(self, population, mean, std):
        '''
        This function creates a new population based on the
        estimated distribution (mean and std) of the elite population.
        '''
        dim = len(mean)
        new_population = np.zeros((population, dim))
        for i in range(population):
            for j in range(dim):
                new_population[i][j] = np.random.normal(mean[j], std[j])
        
        return new_population
    
    def BUMDA_media_std(self, population_elite, g, i_min, i_max, beta=1.0, eps=1e-6):
        m, d = population_elite.shape

        # tranform the fitness en Boltzmann probabilities
        w = np.exp(-beta * np.array(g, dtype=np.float64))
        w_sum = np.sum(w)
        if w_sum == 0:
            w = np.ones_like(w) / len(w)
        else:
            w = w / w_sum
        
        mu = np.zeros(d)
        sigma = np.zeros(d)

        for j in range(d):
            xj = population_elite[:, j]
            mu_j = np.sum(w * xj)              # meand ponderada
            var_j = np.sum(w * (xj - mu_j) ** 2)  # weighted variance
            sigma_j = np.sqrt(max(var_j, eps))  # avoid sigma 0

            # if sigma_j is too large, limit (i_min, i_max)
            max_sigma = (i_max - i_min) / 2.0
            sigma_j = min(sigma_j, max_sigma)

            mu[j] = mu_j
            sigma[j] = sigma_j


        return mu, sigma
    

    def polynomial_model(self, x, params):
        y = np.zeros_like(x, dtype=float)
        for i, a in enumerate(params):
            y += a * x**i
        return y
    
    def exponential_model(self, x, params):
        a, b = params
        return a * np.exp(b * x)
    
    def sine_model(self, x, params):
        a, b, c = params
        return a * np.sin(b * x + c)




