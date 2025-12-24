import pytest
import numpy as np
import random
from relax_gen.algorithms.alg_gp import Node, cl_alg_gp, OPERATORS, TERMINALS, protected_div


# ==================== FIXTURES ====================
@pytest.fixture
def simple_linear_data():
    """Datos simples para función lineal: y = 2x + 3"""
    np.random.seed(42)
    X = np.linspace(-10, 10, 30)
    Y = 2 * X + 3
    return np.column_stack((X, Y))


@pytest.fixture
def quadratic_data():
    """Datos para función cuadrática: y = x² + 2x + 1"""
    np.random.seed(42)
    X = np.linspace(-5, 5, 40)
    Y = X**2 + 2*X + 1 + np.random.normal(0, 0.5, 40)
    return np.column_stack((X, Y))


@pytest.fixture
def simple_node():
    """Nodo simple para tests"""
    left = Node(3)
    right = Node(4)
    return Node('+', [left, right])


@pytest.fixture
def gp_instance(quadratic_data):
    """Instancia de cl_alg_gp con parámetros estándar"""
    return cl_alg_gp(
        data=quadratic_data,
        population=50,
        num_ciclos=10,
        max_depth=4
    )


# ==================== TESTS DE LA CLASE NODE ====================
class TestNode:
    """Tests para la clase Node"""
    
    def test_node_creation_constant(self):
        """Prueba creación de nodo con constante"""
        node = Node(5)
        assert node.value == 5
        assert len(node.children) == 0
    
    def test_node_creation_variable(self):
        """Prueba creación de nodo con variable"""
        node = Node('x')
        assert node.value == 'x'
        assert len(node.children) == 0
    
    def test_node_creation_operator(self):
        """Prueba creación de nodo con operador"""
        left = Node(3)
        right = Node(4)
        node = Node('+', [left, right])
        assert node.value == '+'
        assert len(node.children) == 2
    
    def test_evaluate_constant(self):
        """Evaluar nodo constante"""
        node = Node(10)
        assert node.evaluate(5) == 10
        assert node.evaluate(100) == 10
    
    def test_evaluate_variable(self):
        """Evaluar nodo variable"""
        node = Node('x')
        assert node.evaluate(5) == 5
        assert node.evaluate(-3) == -3
        assert node.evaluate(0) == 0
    
    def test_evaluate_addition(self):
        """Evaluar suma: 3 + 4"""
        left = Node(3)
        right = Node(4)
        node = Node('+', [left, right])
        assert node.evaluate(999) == 7
    
    def test_evaluate_subtraction(self):
        """Evaluar resta: 10 - 3"""
        left = Node(10)
        right = Node(3)
        node = Node('-', [left, right])
        assert node.evaluate(0) == 7
    
    def test_evaluate_multiplication(self):
        """Evaluar multiplicación: 3 * 4"""
        left = Node(3)
        right = Node(4)
        node = Node('*', [left, right])
        assert node.evaluate(0) == 12
    
    def test_evaluate_division(self):
        """Evaluar división: 12 / 3"""
        left = Node(12)
        right = Node(3)
        node = Node('/', [left, right])
        assert node.evaluate(0) == 4
    
    def test_evaluate_division_by_zero_protected(self):
        """Evaluar división por cero (protegida)"""
        left = Node(10)
        right = Node(0)
        node = Node('/', [left, right])
        result = node.evaluate(0)
        assert result == 1  # División protegida retorna 1
    
    def test_evaluate_complex_tree(self):
        """Evaluar árbol complejo: (x + 2) * 3"""
        x_node = Node('x')
        two = Node(2)
        add = Node('+', [x_node, two])
        three = Node(3)
        mult = Node('*', [add, three])
        
        assert mult.evaluate(0) == 6   # (0 + 2) * 3
        assert mult.evaluate(1) == 9   # (1 + 2) * 3
        assert mult.evaluate(5) == 21  # (5 + 2) * 3
    
    def test_evaluate_nested_operations(self):
        """Evaluar operaciones anidadas: ((2 + 3) * 4) - 5"""
        two = Node(2)
        three = Node(3)
        add = Node('+', [two, three])
        four = Node(4)
        mult = Node('*', [add, four])
        five = Node(5)
        sub = Node('-', [mult, five])
        
        assert sub.evaluate(999) == 15  # ((2+3)*4)-5 = 15
    
    def test_copy_creates_new_instance(self):
        """Prueba que copy crea nueva instancia"""
        left = Node(3)
        right = Node(4)
        original = Node('+', [left, right])
        copied = original.copy()
        
        assert copied.value == original.value
        assert copied is not original
        assert copied.children[0] is not original.children[0]
    
    def test_copy_deep_copy(self):
        """Prueba que copy es profunda (deep copy)"""
        original = Node('+', [Node(1), Node(2)])
        copied = original.copy()
        
        # Modificar copia no debe afectar original
        copied.value = '-'
        assert original.value == '+'
    
    def test_to_string_simple(self):
        """Convertir árbol simple a string"""
        left = Node(3)
        right = Node(4)
        node = Node('+', [left, right])
        result = node.to_string()
        
        assert '3' in result
        assert '4' in result
        assert '+' in result
    
    def test_to_string_with_variable(self):
        """Convertir árbol con variable a string"""
        x = Node('x')
        five = Node(5)
        node = Node('*', [x, five])
        result = node.to_string()
        
        assert 'x' in result
        assert '5' in result
        assert '*' in result
    
    def test_get_size_single_node(self):
        """Tamaño de un solo nodo"""
        node = Node(5)
        assert node.get_size() == 1
    
    def test_get_size_tree(self):
        """Tamaño de árbol: (3 + 4)"""
        left = Node(3)
        right = Node(4)
        node = Node('+', [left, right])
        assert node.get_size() == 3
    
    def test_get_size_complex_tree(self):
        """Tamaño de árbol complejo"""
        # ((2 + 3) * 4) tiene 5 nodos
        node = Node('*', [
            Node('+', [Node(2), Node(3)]),
            Node(4)
        ])
        assert node.get_size() == 5
    
    def test_get_all_nodes_single(self):
        """Obtener todos los nodos de nodo único"""
        node = Node(5)
        all_nodes = node.get_all_nodes()
        assert len(all_nodes) == 1
        assert all_nodes[0] is node
    
    def test_get_all_nodes_tree(self):
        """Obtener todos los nodos de árbol"""
        left = Node(3)
        right = Node(4)
        node = Node('+', [left, right])
        all_nodes = node.get_all_nodes()
        
        assert len(all_nodes) == 3
        assert node in all_nodes
        assert left in all_nodes
        assert right in all_nodes


# ==================== TESTS DE FUNCIONES AUXILIARES ====================
class TestHelperFunctions:
    """Tests para funciones auxiliares"""
    
    def test_protected_div_normal(self):
        """División protegida con valores normales"""
        assert protected_div(10, 2) == 5
        assert protected_div(15, 3) == 5
    
    def test_protected_div_by_zero(self):
        """División protegida por cero exacto"""
        assert protected_div(10, 0) == 1
    
    def test_protected_div_by_small_number(self):
        """División protegida por número muy pequeño"""
        assert protected_div(10, 0.0001) == 1
        assert protected_div(10, -0.0001) == 1
    
    def test_protected_div_negative(self):
        """División protegida con negativos"""
        assert protected_div(-10, 2) == -5
        assert protected_div(10, -2) == -5


# ==================== TESTS DE LA CLASE cl_alg_gp ====================
class TestClAlgGp:
    """Tests para la clase cl_alg_gp"""
    
    def test_initialization(self, quadratic_data):
        """Prueba inicialización correcta"""
        gp = cl_alg_gp(
            data=quadratic_data,
            population=50,
            num_ciclos=10,
            max_depth=4
        )
        
        assert gp.population == 50
        assert gp.num_ciclos == 10
        assert gp.max_depth == 4
        assert np.array_equal(gp.data, quadratic_data)
    
    def test_create_random_tree_depth_zero(self, gp_instance):
        """Crear árbol con profundidad 0 (terminal)"""
        tree = gp_instance.create_random_tree(max_depth=0)
        
        assert tree.value == 'x' or isinstance(tree.value, (int, float))
        assert len(tree.children) == 0
    
    def test_create_random_tree_depth_positive(self, gp_instance):
        """Crear árbol con profundidad positiva"""
        tree = gp_instance.create_random_tree(max_depth=3)
        
        assert tree is not None
        assert hasattr(tree, 'value')
        assert hasattr(tree, 'children')
    
    def test_create_random_tree_grow_method(self, gp_instance):
        """Crear árbol con método 'grow'"""
        random.seed(42)
        tree = gp_instance.create_random_tree(max_depth=3, method='grow')
        
        assert tree is not None
        assert tree.get_size() >= 1
    
    def test_create_random_tree_full_method(self, gp_instance):
        """Crear árbol con método 'full'"""
        random.seed(42)
        tree = gp_instance.create_random_tree(max_depth=2, method='full')
        
        assert tree is not None
        # Método 'full' debería crear árbol más completo
        assert tree.get_size() >= 1
    
    def test_create_population_size(self, gp_instance):
        """Crear población con tamaño correcto"""
        pop = gp_instance.create_population(population_size=30, max_depth=3)
        
        assert len(pop) == 30
    
    def test_create_population_all_valid(self, gp_instance):
        """Todos los individuos de la población son válidos"""
        pop = gp_instance.create_population(population_size=20, max_depth=3)
        
        for individual in pop:
            assert individual is not None
            assert hasattr(individual, 'evaluate')
            assert hasattr(individual, 'get_size')
    
    def test_create_population_variety(self, gp_instance):
        """Población tiene variedad (no todos iguales)"""
        pop = gp_instance.create_population(population_size=10, max_depth=3)
        
        sizes = [ind.get_size() for ind in pop]
        # Debería haber variedad en tamaños
        assert len(set(sizes)) > 1
    
   
    
    def test_fitness_constant_prediction(self, gp_instance):
        """Fitness con predicción constante"""
        tree = Node(5)
        X = np.array([1, 2, 3, 4, 5])
        Y = np.array([5, 5, 5, 5, 5])
        
        fit = gp_instance.fitness(tree, X, Y)
        assert fit < 0.1
    
    def test_fitness_poor_prediction(self, gp_instance):
        """Fitness con predicción pobre"""
        tree = Node(0)  # Predice siempre 0
        X = np.array([1, 2, 3, 4, 5])
        Y = np.array([100, 200, 300, 400, 500])
        
        fit = gp_instance.fitness(tree, X, Y)
        assert fit > 1000  # Error muy grande
    

    
    def test_tournament_selection_returns_individual(self, gp_instance):
        """Selección por torneo retorna individuo"""
        pop = gp_instance.create_population(10, 3)
        fitnesses = [1.0, 5.0, 2.0, 8.0, 3.0, 4.0, 6.0, 7.0, 9.0, 10.0]
        
        selected = gp_instance.tournament_selection(pop, fitnesses, tournament_size=3)
        
        assert selected is not None
        assert selected in pop
    
    def test_tournament_selection_prefers_better_fitness(self, gp_instance):
        """Selección por torneo prefiere mejor fitness"""
        pop = [Node(i) for i in range(10)]
        fitnesses = [9, 8, 7, 6, 5, 4, 3, 2, 1, 0]  # El último es el mejor
        
        # Ejecutar varias veces y contar selecciones
        random.seed(42)
        selections = []
        for _ in range(100):
            selected = gp_instance.tournament_selection(pop, fitnesses, tournament_size=3)
            selections.append(pop.index(selected))
        
        # Los individuos con mejor fitness deberían ser seleccionados más
        avg_index = np.mean(selections)
        assert avg_index > 5  # Debería tender hacia índices altos (mejor fitness)
    
    def test_crossover_returns_two_children(self, gp_instance):
        """Cruce retorna dos hijos"""
        parent1 = gp_instance.create_random_tree(max_depth=3)
        parent2 = gp_instance.create_random_tree(max_depth=3)
        
        child1, child2 = gp_instance.crossover(parent1, parent2)
        
        assert child1 is not None
        assert child2 is not None
    
    def test_crossover_creates_new_instances(self, gp_instance):
        """Cruce crea nuevas instancias (no modifica padres)"""
        parent1 = gp_instance.create_random_tree(max_depth=3)
        parent2 = gp_instance.create_random_tree(max_depth=3)
        
        orig_p1_string = parent1.to_string()
        orig_p2_string = parent2.to_string()
        
        child1, child2 = gp_instance.crossover(parent1, parent2)
        
        # Los padres originales no deben cambiar
        assert parent1.to_string() == orig_p1_string
        assert parent2.to_string() == orig_p2_string
    
    def test_crossover_with_single_node_trees(self, gp_instance):
        """Cruce con árboles de un solo nodo"""
        parent1 = Node(5)
        parent2 = Node(10)
        
        child1, child2 = gp_instance.crossover(parent1, parent2)
        
        # Debe manejar el caso sin errores
        assert child1 is not None
        assert child2 is not None
    
    def test_mutate_preserves_validity(self, gp_instance):
        """Mutación preserva validez del árbol"""
        random.seed(42)
        tree = gp_instance.create_random_tree(max_depth=3)
        
        mutated = gp_instance.mutate(tree.copy(), mutation_rate=1.0)
        
        assert mutated is not None
        assert hasattr(mutated, 'evaluate')
        assert mutated.get_size() >= 1
    
    def test_mutate_with_zero_rate(self, gp_instance):
        """Mutación con tasa 0 no cambia el árbol"""
        tree = gp_instance.create_random_tree(max_depth=3)
        original_string = tree.to_string()
        
        mutated = gp_instance.mutate(tree, mutation_rate=0.0)
        
        # Con tasa 0, debería mantenerse igual
        assert mutated.to_string() == original_string
    
    def test_mutate_with_high_rate(self, gp_instance):
        """Mutación con tasa alta cambia el árbol"""
        random.seed(42)
        tree = gp_instance.create_random_tree(max_depth=3)
        
        # Guardar copia para comparar
        original = tree.copy()
        
        # Mutar muchas veces con tasa alta
        changed = False
        for _ in range(10):
            mutated = gp_instance.mutate(tree.copy(), mutation_rate=0.8)
            if mutated.to_string() != original.to_string():
                changed = True
                break
        
        assert changed  # Al menos una mutación debería cambiar el árbol


# ==================== TESTS DEL ALGORITMO COMPLETO ====================
class TestRunMethod:
    """Tests para el método run() que ejecuta el algoritmo completo"""
    
    def test_run_executes_without_error(self, simple_linear_data):
        """Algoritmo ejecuta sin errores"""
        gp = cl_alg_gp(
            data=simple_linear_data,
            population=30,
            num_ciclos=5,
            max_depth=3
        )
        
        best_individual, best_fitness = gp.run()
        
        assert best_individual is not None
        assert isinstance(best_fitness, (int, float))
        assert np.isfinite(best_fitness)
    
    def test_run_returns_valid_tree(self, simple_linear_data):
        """run() retorna árbol válido"""
        gp = cl_alg_gp(
            data=simple_linear_data,
            population=30,
            num_ciclos=5,
            max_depth=3
        )
        
        best_individual, _ = gp.run()
        
        # Verificar que puede evaluar
        result = best_individual.evaluate(5)
        assert np.isfinite(result)
        
        # Verificar que tiene métodos necesarios
        assert hasattr(best_individual, 'to_string')
        assert hasattr(best_individual, 'get_size')
    
    def test_run_fitness_improves_or_stable(self, simple_linear_data):
        """Fitness mejora o se mantiene estable"""
        random.seed(42)
        np.random.seed(42)
        
        gp = cl_alg_gp(
            data=simple_linear_data,
            population=50,
            num_ciclos=20,
            max_depth=4
        )
        
        best_individual, final_fitness = gp.run()
        
        # El fitness final debería ser razonable
        assert final_fitness < 1000  # No debería ser penalización máxima
    
  
    def test_run_with_different_parameters(self):
        """Algoritmo funciona con diferentes parámetros"""
        np.random.seed(42)
        X = np.linspace(0, 10, 20)
        Y = X * 3
        data = np.column_stack((X, Y))
        
        # Configuración pequeña
        gp_small = cl_alg_gp(data=data, population=20, num_ciclos=5, max_depth=3)
        best_small, fitness_small = gp_small.run()
        
        # Configuración mediana
        gp_medium = cl_alg_gp(data=data, population=50, num_ciclos=10, max_depth=4)
        best_medium, fitness_medium = gp_medium.run()
        
        assert best_small is not None
        assert best_medium is not None
        assert np.isfinite(fitness_small)
        assert np.isfinite(fitness_medium)


# ==================== TESTS DE CASOS LÍMITE ====================
class TestEdgeCases:
    """Tests para casos límite y situaciones especiales"""
    
    def test_single_data_point(self):
        """Algoritmo con un solo punto de datos"""
        data = np.array([[5.0, 25.0]])
        
        gp = cl_alg_gp(data=data, population=20, num_ciclos=5, max_depth=3)
        best, fitness = gp.run()
        
        assert best is not None
        assert np.isfinite(fitness)
    
    
    
    def test_negative_values(self):
        """Datos con valores negativos"""
        X = np.linspace(-10, -1, 20)
        Y = -2 * X + 5
        data = np.column_stack((X, Y))
        
        gp = cl_alg_gp(data=data, population=50, num_ciclos=15, max_depth=4)
        best, fitness = gp.run()
        
        assert best is not None
        assert np.isfinite(fitness)
    
    def test_large_values(self):
        """Datos con valores grandes"""
        X = np.linspace(100, 200, 20)
        Y = X / 10
        data = np.column_stack((X, Y))
        
        gp = cl_alg_gp(data=data, population=30, num_ciclos=10, max_depth=3)
        best, fitness = gp.run()
        
        assert best is not None
        assert np.isfinite(fitness)
    
    def test_small_population(self):
        """Algoritmo con población muy pequeña"""
        np.random.seed(42)
        X = np.linspace(0, 5, 10)
        Y = X * 2
        data = np.column_stack((X, Y))
        
        gp = cl_alg_gp(data=data, population=5, num_ciclos=5, max_depth=3)
        best, fitness = gp.run()
        
        assert best is not None
        assert np.isfinite(fitness)


# ==================== TESTS DE INTEGRACIÓN ====================
class TestIntegration:
    """Tests de integración del sistema completo"""
    
    def test_full_workflow_simple(self):
        """Flujo completo con problema simple"""
        # Preparar datos: y = x + 1
        np.random.seed(42)
        X = np.linspace(0, 10, 25)
        Y = X + 1
        data = np.column_stack((X, Y))
        
        # Crear instancia
        gp = cl_alg_gp(
            data=data,
            population=50,
            num_ciclos=20,
            max_depth=4
        )
        
        # Ejecutar
        best_individual, final_fitness = gp.run()
        
        # Verificaciones
        assert best_individual is not None
        assert np.isfinite(final_fitness)
        assert final_fitness < 100
        
        # Verificar que puede hacer predicciones
        test_x = 15
        prediction = best_individual.evaluate(test_x)
        assert np.isfinite(prediction)
    
    def test_comparison_with_target_function(self, quadratic_data):
        """Comparar resultado con función objetivo"""
        gp = cl_alg_gp(
            data=quadratic_data,
            population=100,
            num_ciclos=30,
            max_depth=5
        )
        
        best_individual, _ = gp.run()
        
        # Extraer X, Y originales
        X_test = quadratic_data[:10, 0]
        Y_test = quadratic_data[:10, 1]
        
        # Hacer predicciones
        predictions = [best_individual.evaluate(x) for x in X_test]
        
        # Calcular correlación
        correlation = np.corrcoef(predictions, Y_test)[0, 1]
        
        # La correlación debería ser positiva y razonablemente alta
        assert correlation > 0.5


