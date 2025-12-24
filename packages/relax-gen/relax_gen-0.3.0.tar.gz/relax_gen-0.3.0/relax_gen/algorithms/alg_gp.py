import numpy as np
import random
import operator
import copy
from typing import List, Callable, Tuple

def protected_div(a, b):
    return a / b if abs(b) > 0.001 else 1

OPERATORS = {
    '+': operator.add,
    '-': operator.sub,
    '*': operator.mul,
    '/': protected_div,
}

TERMINALS = ['x', lambda: random.uniform(-5, 5)]  

class Node:
    def __init__(self, value, children=None):
        self.value = value 
        self.children = children if children else []
    
    def evaluate(self, x):
        if isinstance(self.value, (int, float)):
            return self.value
        elif self.value == 'x':
            return x
        elif self.value in OPERATORS:
            op_func = OPERATORS[self.value]
            child_values = [child.evaluate(x) for child in self.children]
            try:
                return op_func(*child_values)
            except (ZeroDivisionError, OverflowError, ValueError):
                return 1e10  # Error penalty
        return 0
    
    def copy(self):
        new_children = [child.copy() for child in self.children]
        return Node(self.value, new_children)
    
    def to_string(self):
        # Transform the tree into a readable mathematical expression
        if isinstance(self.value, (int, float)):
            return str(round(self.value, 2))
        elif self.value == 'x':
            return 'x'
        elif self.value in OPERATORS:
            if len(self.children) == 2:
                left = self.children[0].to_string()
                right = self.children[1].to_string()
                return f"({left} {self.value} {right})"
            elif len(self.children) == 1:
                child = self.children[0].to_string()
                return f"{self.value}({child})"
        return ""
    
    def get_size(self):
        # Return the total number of nodes in the tree
        return 1 + sum(child.get_size() for child in self.children)
    
    def get_all_nodes(self):
        # Return all nodes in the tree
        nodes = [self]
        for child in self.children:
            nodes.extend(child.get_all_nodes())
        return nodes


class cl_alg_gp():
    def __init__(self, data, population, num_ciclos, max_depth):
        self.data = data
        self.population = population
        self.num_ciclos = num_ciclos
        self.max_depth = max_depth


    def run(self):
        # X first column, Y second column
        X, Y = self.data[:, 0], self.data[:, 1]
        
        populations = self.create_population(self.population, self.max_depth)
        best_individual = None
        best_fitness = float('inf')

        for gen in range(self.num_ciclos):
            fitnesses = [self.fitness(ind, X, Y) for ind in populations]
        
            
            gen_best_idx = fitnesses.index(min(fitnesses))
            if fitnesses[gen_best_idx] < best_fitness:
                best_fitness = fitnesses[gen_best_idx]
                best_individual = populations[gen_best_idx].copy()


            new_population = []
        
            # Elitism: keep the best individual
            new_population.append(best_individual.copy())
            
            while len(new_population) < self.population:
                # Selection
                parent1 = self.tournament_selection(populations, fitnesses)
                parent2 = self.tournament_selection(populations, fitnesses)
                
                # Crossover
                if random.random() < 0.9:
                    child1, child2 = self.crossover(parent1, parent2)
                else:
                    child1, child2 = parent1.copy(), parent2.copy()
                
                # Mutation
                child1 = self.mutate(child1)
                child2 = self.mutate(child2)
                
                new_population.extend([child1, child2])
            
            population = new_population[:self.population]
        
        # Return the best individual and its fitness
        finally_fitness = self.fitness(best_individual, X, Y)

        return best_individual, finally_fitness

    
    def create_random_tree(self, max_depth, method='grow'):
        if max_depth == 0:
            terminal = random.choice(TERMINALS)
            if callable(terminal):
                return Node(terminal())
            return Node(terminal)
    
        if method == 'grow':
            if random.random() < 0.3:
                terminal = random.choice(TERMINALS)
                if callable(terminal):
                    return Node(terminal())
                return Node(terminal)
        
        op = random.choice(list(OPERATORS.keys()))
        num_children = 2  # All operators are binary
        children = [self.create_random_tree(max_depth - 1, method) for _ in range(num_children)]
        return Node(op, children)


    def create_population(self, population_size, max_depth):
        population = []
        for i in range(population_size):
            depth = random.randint(1, max_depth)
            method = 'grow' if random.random() < 0.5 else 'full' 
            population.append(self.create_random_tree(depth, method))
        return population
    
    def fitness(self, individual, X, Y):
        predictions = []
        for x_val in X:
            pred = individual.evaluate(x_val)
            if not np.isfinite(pred):
                return 1e10
            predictions.append(pred)
        
        predictions = np.array(predictions)
        mse = np.mean((predictions - Y) ** 2)
        
        # Parsimony penalty (prevents excessive growth or "bloat")
        complexity_penalty = individual.get_size() * 0.001 
        return mse + complexity_penalty
        
    def tournament_selection(self, population, fitnesses, tournament_size=3):
        tournament_indices = random.sample(range(len(population)), tournament_size)
        tournament_fitnesses = [fitnesses[i] for i in tournament_indices]
        winner_idx = tournament_indices[tournament_fitnesses.index(min(tournament_fitnesses))]
        return population[winner_idx]

    def crossover(self, parent1, parent2):
        child1 = parent1.copy()
        child2 = parent2.copy()
        
        # Select random nodes for crossover  
        nodes1 = child1.get_all_nodes()
        nodes2 = child2.get_all_nodes()
        
        if len(nodes1) > 1 and len(nodes2) > 1:
            node1 = random.choice(nodes1[1:])  # Avoid root
            node2 = random.choice(nodes2[1:])
            
            # Swap subtrees
            node1.value, node2.value = node2.value, node1.value
            node1.children, node2.children = node2.children, node1.children
        
        return child1, child2
    
    def mutate(self, individual, mutation_rate=0.1):
        if random.random() < mutation_rate:
            nodes = individual.get_all_nodes()
            if len(nodes) > 1:
                node_to_mutate = random.choice(nodes)
                new_subtree = self.create_random_tree(self.max_depth // 2)
                node_to_mutate.value = new_subtree.value
                node_to_mutate.children = new_subtree.children
        return individual