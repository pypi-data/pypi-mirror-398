import numpy as np

def init_pop(pop_size):
    return np.random.randint(8, size=(pop_size, 8))

def calc_fitness(population):
    fitness_vals = []
    for x in population:
        penalty = 0
        for i in range(8):
            r = x[i]
            for j in range(8):
                if i==j:
                    continue
                d = abs(i-j)
                if x[j] in [r, r-d, r+d]:
                    penalty += 1
        fitness_vals.append(penalty)
    return -1 * np.array(fitness_vals)

def selection(population, fitness_vals):
    probs = fitness_vals.copy()
    probs += abs(probs.min()) + 1
    probs = probs / probs.sum()
    N = len(population)
    indices = np.arange(N)
    selected_indices = np.random.choice(indices, size=N, p=probs)
    return population[selected_indices]

def crossover(p1, p2, pc):
    if np.random.random() < pc:
        m = np.random.randint(1, 8)
        ch1 = np.concatenate((p1[:m], p2[m:]))
        ch2 = np.concatenate((p2[:m], p1[m:]))
    else:
        ch1 = p1.copy()
        ch2 = p2.copy()
    return ch1, ch2

def mutation(individual, pm):
    if np.random.random() < pm:
        m = np.random.randint(8)
        individual[m] = np.random.randint(8)
    return individual

def crossover_mutation(selected_pop, pc, pm):
    N = len(selected_pop)
    new_pop = np.empty((N, 8), dtype=int)
    for i in range(0, N, 2):
        p1 = selected_pop[i]
        p2 = selected_pop[i+1]
        ch1, ch2 = crossover(p1, p2, pc)
        new_pop[i] = ch1
        new_pop[i+1] = ch2
    for i in range(N):
        mutation(new_pop[i], pm)
    return new_pop

def run_genetic_algorithm():
    POP_SIZE = 100
    MAX_GENERATIONS = 2000
    PC = 0.7
    PM = 0.05
    population = init_pop(POP_SIZE)
    best_solution = None
    best_fitness = -9999

    for generation in range(MAX_GENERATIONS):
        fitness_vals = calc_fitness(population)
        current_best_index = np.argmax(fitness_vals)
        current_best_fitness = fitness_vals[current_best_index]

        if current_best_fitness > best_fitness:
            best_fitness = current_best_fitness
            best_solution = population[current_best_index]

        if best_fitness == 0:
            return best_solution

        selected_pop = selection(population, fitness_vals)
        population = crossover_mutation(selected_pop, PC, PM)

    return best_solution


# """
# =============================================================================
# COMPLETE GENETIC ALGORITHMS IMPLEMENTATIONS
# All algorithms from the PDFs with detailed explanations
# =============================================================================
# """

# import random
# import math
# import matplotlib.pyplot as plt
# from typing import List, Dict, Tuple

# # =============================================================================
# # 1. LINEAR EQUATION PROBLEM
# # Problem: Find a, b, c, d where a + 2b + 3c + 4d = 30
# # =============================================================================

# """
# ALGORITHM: Linear Equation GA

# INPUT: 
#     - Target value = 30
#     - Coefficients = [1, 2, 3, 4]
#     - Population size, generations, rates

# STEPS:
# 1. Initialize population with random [a,b,c,d] chromosomes
# 2. For each generation:
#    a. Calculate objective: |a + 2b + 3c + 4d - 30|
#    b. Calculate fitness: 1/(1 + objective)
#    c. Selection using Roulette Wheel
#    d. Crossover at random point
#    e. Mutation of random genes
#    f. Track best solution
# 3. Return best chromosome

# OUTPUT: Best [a,b,c,d] and error
# """

# class LinearEquationGA:
#     def __init__(self, pop_size=6, generations=50, crossover_rate=0.25, mutation_rate=0.1):
#         self.pop_size = pop_size
#         self.generations = generations
#         self.crossover_rate = crossover_rate
#         self.mutation_rate = mutation_rate
#         self.target = 30
#         self.coefficients = [1, 2, 3, 4]
        
#     def create_chromosome(self):
#         """Step 1a: Create random chromosome [a,b,c,d]"""
#         return [random.randint(0, 30) for _ in range(4)]
    
#     def initialize_population(self):
#         """Step 1b: Create initial population"""
#         return [self.create_chromosome() for _ in range(self.pop_size)]
    
#     def calculate_objective(self, chromosome):
#         """Step 2a: Calculate |a + 2b + 3c + 4d - 30|"""
#         result = sum(chromosome[i] * self.coefficients[i] for i in range(4))
#         return abs(result - self.target)
    
#     def calculate_fitness(self, objective):
#         """Step 2b: Calculate fitness = 1/(1+objective)"""
#         return 1 / (1 + objective)
    
#     def roulette_wheel_selection(self, population):
#         """Step 2c: Roulette Wheel Selection"""
#         # Calculate fitness for all chromosomes
#         fitness_values = []
#         for chrom in population:
#             obj = self.calculate_objective(chrom)
#             fit = self.calculate_fitness(obj)
#             fitness_values.append(fit)
        
#         # Calculate probabilities
#         total_fitness = sum(fitness_values)
#         if total_fitness == 0:
#             return [random.choice(population).copy() for _ in range(self.pop_size)]
        
#         probabilities = [f / total_fitness for f in fitness_values]
        
#         # Calculate cumulative probabilities
#         cumulative = []
#         cum_sum = 0
#         for p in probabilities:
#             cum_sum += p
#             cumulative.append(cum_sum)
        
#         # Select new population
#         new_population = []
#         for _ in range(self.pop_size):
#             r = random.random()
#             for i, cum_prob in enumerate(cumulative):
#                 if r <= cum_prob:
#                     new_population.append(population[i].copy())
#                     break
        
#         return new_population
    
#     def crossover(self, population):
#         """Step 2d: Single-point crossover"""
#         new_population = []
        
#         for i in range(0, self.pop_size, 2):
#             parent1 = population[i]
#             parent2 = population[i+1] if i+1 < self.pop_size else population[0]
            
#             if random.random() < self.crossover_rate:
#                 # Random crossover point
#                 point = random.randint(1, 3)
#                 child1 = parent1[:point] + parent2[point:]
#                 child2 = parent2[:point] + parent1[point:]
#                 new_population.extend([child1, child2])
#             else:
#                 new_population.extend([parent1.copy(), parent2.copy()])
        
#         return new_population[:self.pop_size]
    
#     def mutate(self, population):
#         """Step 2e: Random mutation"""
#         total_genes = self.pop_size * 4
#         num_mutations = int(self.mutation_rate * total_genes)
        
#         for _ in range(num_mutations):
#             chrom_idx = random.randint(0, self.pop_size - 1)
#             gene_idx = random.randint(0, 3)
#             population[chrom_idx][gene_idx] = random.randint(0, 30)
        
#         return population
    
#     def run(self):
#         """Main GA Loop"""
#         print("="*70)
#         print("1. LINEAR EQUATION GA: a + 2b + 3c + 4d = 30")
#         print("="*70)
        
#         # Step 1: Initialize
#         population = self.initialize_population()
#         best_solution = None
#         best_error = float('inf')
#         history = []
        
#         print("\nInitial Population:")
#         for i, chrom in enumerate(population):
#             error = self.calculate_objective(chrom)
#             print(f"  Chromosome {i+1}: {chrom} → Error: {error}")
        
#         # Step 2: Evolution loop
#         for gen in range(self.generations):
#             # Selection
#             population = self.roulette_wheel_selection(population)
            
#             # Crossover
#             population = self.crossover(population)
            
#             # Mutation
#             population = self.mutate(population)
            
#             # Track best
#             for chrom in population:
#                 error = self.calculate_objective(chrom)
#                 if error < best_error:
#                     best_error = error
#                     best_solution = chrom.copy()
            
#             history.append(best_error)
            
#             if (gen + 1) % 10 == 0:
#                 print(f"\nGeneration {gen + 1}: Best Error = {best_error}")
            
#             if best_error == 0:
#                 print(f"\n✓ Perfect solution found at generation {gen + 1}!")
#                 break
        
#         # Step 3: Results
#         print("\n" + "="*70)
#         print("FINAL SOLUTION:")
#         a, b, c, d = best_solution
#         result = a + 2*b + 3*c + 4*d
#         print(f"  a={a}, b={b}, c={c}, d={d}")
#         print(f"  Result: {a} + 2×{b} + 3×{c} + 4×{d} = {result}")
#         print(f"  Error: {best_error}")
#         print("="*70)
        
#         return best_solution, best_error, history


# # =============================================================================
# # 2. KNAPSACK PROBLEM
# # Problem: Select items to maximize value without exceeding weight limit
# # =============================================================================

# """
# ALGORITHM: Knapsack GA

# INPUT:
#     - Items with value and weight
#     - Maximum weight capacity
#     - GA parameters

# STEPS:
# 1. Initialize population with random binary chromosomes [0,1,...]
#    (1=take item, 0=leave item)
# 2. For each generation:
#    a. Calculate fitness (total value, 0 if overweight)
#    b. Tournament selection (pick best of 3 random)
#    c. Single-point crossover
#    d. Bit-flip mutation
#    e. Track best solution
# 3. Return best selection

# OUTPUT: Best chromosome and total value
# """

# class KnapsackGA:
#     def __init__(self, items, max_weight, pop_size=10, generations=50):
#         self.items = items
#         self.max_weight = max_weight
#         self.pop_size = pop_size
#         self.generations = generations
#         self.num_items = len(items)
#         self.crossover_rate = 0.7
#         self.mutation_rate = 0.1
        
#     def create_chromosome(self):
#         """Step 1a: Create random binary chromosome"""
#         return [random.randint(0, 1) for _ in range(self.num_items)]
    
#     def initialize_population(self):
#         """Step 1b: Create initial population"""
#         return [self.create_chromosome() for _ in range(self.pop_size)]
    
#     def calculate_fitness(self, chromosome):
#         """Step 2a: Calculate fitness (total value or 0 if overweight)"""
#         total_value = 0
#         total_weight = 0
        
#         for i in range(self.num_items):
#             if chromosome[i] == 1:
#                 total_value += self.items[i]['value']
#                 total_weight += self.items[i]['weight']
        
#         # Penalty for exceeding weight
#         if total_weight > self.max_weight:
#             return 0
        
#         return total_value
    
#     def tournament_selection(self, population):
#         """Step 2b: Tournament selection"""
#         new_population = []
        
#         for _ in range(self.pop_size):
#             # Select 3 random competitors
#             competitors = random.sample(population, 3)
#             # Pick the best one
#             winner = max(competitors, key=self.calculate_fitness)
#             new_population.append(winner.copy())
        
#         return new_population
    
#     def crossover(self, population):
#         """Step 2c: Single-point crossover"""
#         new_population = []
        
#         for i in range(0, self.pop_size, 2):
#             parent1 = population[i]
#             parent2 = population[i+1] if i+1 < self.pop_size else population[0]
            
#             if random.random() < self.crossover_rate:
#                 point = random.randint(1, self.num_items - 1)
#                 child1 = parent1[:point] + parent2[point:]
#                 child2 = parent2[:point] + parent1[point:]
#                 new_population.extend([child1, child2])
#             else:
#                 new_population.extend([parent1.copy(), parent2.copy()])
        
#         return new_population[:self.pop_size]
    
#     def mutate(self, population):
#         """Step 2d: Bit-flip mutation"""
#         for chromosome in population:
#             if random.random() < self.mutation_rate:
#                 gene = random.randint(0, self.num_items - 1)
#                 chromosome[gene] = 1 - chromosome[gene]  # Flip bit
        
#         return population
    
#     def run(self):
#         """Main GA Loop"""
#         print("\n\n" + "="*70)
#         print("2. KNAPSACK PROBLEM")
#         print("="*70)
#         print(f"Max Weight: {self.max_weight}")
#         print("Items:")
#         for item in self.items:
#             print(f"  - {item['name']}: Value={item['value']}, Weight={item['weight']}")
        
#         # Step 1: Initialize
#         population = self.initialize_population()
#         best_solution = None
#         best_fitness = 0
#         history = []
        
#         # Step 2: Evolution loop
#         for gen in range(self.generations):
#             population = self.tournament_selection(population)
#             population = self.crossover(population)
#             population = self.mutate(population)
            
#             # Track best
#             for chrom in population:
#                 fitness = self.calculate_fitness(chrom)
#                 if fitness > best_fitness:
#                     best_fitness = fitness
#                     best_solution = chrom.copy()
            
#             history.append(best_fitness)
            
#             if (gen + 1) % 10 == 0:
#                 print(f"\nGeneration {gen + 1}: Best Fitness = {best_fitness}")
        
#         # Step 3: Results
#         print("\n" + "="*70)
#         print("FINAL SOLUTION:")
#         print(f"  Best Chromosome: {best_solution}")
#         print(f"  Total Value: {best_fitness}")
        
#         total_weight = sum(self.items[i]['weight'] for i in range(len(best_solution)) 
#                           if best_solution[i] == 1)
#         print(f"  Total Weight: {total_weight}/{self.max_weight}")
        
#         print("\n  Selected Items:")
#         for i in range(len(best_solution)):
#             if best_solution[i] == 1:
#                 print(f"    ✓ {self.items[i]['name']}: Value={self.items[i]['value']}, Weight={self.items[i]['weight']}")
#         print("="*70)
        
#         return best_solution, best_fitness, history


# # =============================================================================
# # 3. TRAVELING SALESMAN PROBLEM (TSP)
# # Problem: Find shortest route visiting all cities exactly once
# # =============================================================================

# """
# ALGORITHM: TSP GA

# INPUT:
#     - Distance matrix between cities
#     - GA parameters

# STEPS:
# 1. Initialize population with random city permutations
# 2. For each generation:
#    a. Calculate fitness = 1/total_distance
#    b. Tournament selection
#    c. Order Crossover (OX) to maintain valid routes
#    d. Swap mutation (exchange two cities)
#    e. Track best route
# 3. Return shortest route

# OUTPUT: Best route and its distance
# """

# class TravelingSalesmanGA:
#     def __init__(self, distances, pop_size=20, generations=100):
#         self.distances = distances
#         self.num_cities = len(distances)
#         self.pop_size = pop_size
#         self.generations = generations
#         self.crossover_rate = 0.8
#         self.mutation_rate = 0.2
        
#     def create_chromosome(self):
#         """Step 1a: Create random route (permutation)"""
#         route = list(range(self.num_cities))
#         random.shuffle(route)
#         return route
    
#     def initialize_population(self):
#         """Step 1b: Create initial population"""
#         return [self.create_chromosome() for _ in range(self.pop_size)]
    
#     def calculate_distance(self, route):
#         """Step 2a: Calculate total distance of route"""
#         total = 0
#         for i in range(len(route)):
#             city1 = route[i]
#             city2 = route[(i + 1) % len(route)]
#             total += self.distances[city1][city2]
#         return total
    
#     def calculate_fitness(self, route):
#         """Step 2a: Calculate fitness = 1/distance"""
#         distance = self.calculate_distance(route)
#         return 1 / distance if distance > 0 else 0
    
#     def tournament_selection(self, population):
#         """Step 2b: Tournament selection"""
#         new_population = []
        
#         for _ in range(self.pop_size):
#             competitors = random.sample(population, 3)
#             winner = max(competitors, key=self.calculate_fitness)
#             new_population.append(winner.copy())
        
#         return new_population
    
#     def order_crossover(self, parent1, parent2):
#         """Step 2c: Order Crossover (OX) - maintains valid permutation"""
#         size = len(parent1)
#         point1 = random.randint(0, size - 2)
#         point2 = random.randint(point1 + 1, size - 1)
        
#         # Create child1
#         child1 = [-1] * size
#         child1[point1:point2] = parent1[point1:point2]
        
#         # Fill remaining positions from parent2
#         pos = point2
#         for city in parent2[point2:] + parent2[:point2]:
#             if city not in child1:
#                 child1[pos % size] = city
#                 pos += 1
        
#         # Create child2
#         child2 = [-1] * size
#         child2[point1:point2] = parent2[point1:point2]
        
#         pos = point2
#         for city in parent1[point2:] + parent1[:point2]:
#             if city not in child2:
#                 child2[pos % size] = city
#                 pos += 1
        
#         return child1, child2
    
#     def crossover(self, population):
#         """Step 2c: Perform crossover on population"""
#         new_population = []
        
#         for i in range(0, self.pop_size, 2):
#             parent1 = population[i]
#             parent2 = population[i+1] if i+1 < self.pop_size else population[0]
            
#             if random.random() < self.crossover_rate:
#                 child1, child2 = self.order_crossover(parent1, parent2)
#                 new_population.extend([child1, child2])
#             else:
#                 new_population.extend([parent1.copy(), parent2.copy()])
        
#         return new_population[:self.pop_size]
    
#     def mutate(self, population):
#         """Step 2d: Swap mutation"""
#         for route in population:
#             if random.random() < self.mutation_rate:
#                 i, j = random.sample(range(self.num_cities), 2)
#                 route[i], route[j] = route[j], route[i]
        
#         return population
    
#     def run(self):
#         """Main GA Loop"""
#         print("\n\n" + "="*70)
#         print("3. TRAVELING SALESMAN PROBLEM (TSP)")
#         print("="*70)
        
#         # Step 1: Initialize
#         population = self.initialize_population()
#         best_route = None
#         best_distance = float('inf')
#         history = []
        
#         print("\nDistance Matrix:")
#         for row in self.distances:
#             print("  ", row)
        
#         # Step 2: Evolution loop
#         for gen in range(self.generations):
#             population = self.tournament_selection(population)
#             population = self.crossover(population)
#             population = self.mutate(population)
            
#             # Track best
#             for route in population:
#                 distance = self.calculate_distance(route)
#                 if distance < best_distance:
#                     best_distance = distance
#                     best_route = route.copy()
            
#             history.append(best_distance)
            
#             if (gen + 1) % 20 == 0:
#                 print(f"\nGeneration {gen + 1}: Best Distance = {best_distance:.2f}")
        
#         # Step 3: Results
#         print("\n" + "="*70)
#         print("FINAL SOLUTION:")
#         print(f"  Best Route: {best_route}")
#         print(f"  Total Distance: {best_distance:.2f}")
#         print("\n  Route Path:")
#         for i in range(len(best_route)):
#             city1 = best_route[i]
#             city2 = best_route[(i + 1) % len(best_route)]
#             dist = self.distances[city1][city2]
#             print(f"    City {city1} → City {city2}: Distance = {dist}")
#         print("="*70)
        
#         return best_route, best_distance, history


# # =============================================================================
# # 4. COLOR MAP PROBLEM
# # Problem: Color map so no two adjacent regions have same color
# # =============================================================================

# """
# ALGORITHM: Color Map GA

# INPUT:
#     - Graph (adjacency list)
#     - Number of colors
#     - GA parameters

# STEPS:
# 1. Initialize population with random color assignments
# 2. For each generation:
#    a. Calculate fitness = 1/(1 + conflicts)
#       (conflicts = adjacent regions with same color)
#    b. Tournament selection
#    c. Uniform crossover
#    d. Random color mutation
#    e. Track best coloring
# 3. Return coloring with minimum conflicts

# OUTPUT: Best coloring and number of conflicts
# """

# class ColorMapGA:
#     def __init__(self, graph, num_colors=3, pop_size=20, generations=100):
#         self.graph = graph
#         self.nodes = list(graph.keys())
#         self.num_colors = num_colors
#         self.colors = list(range(num_colors))
#         self.pop_size = pop_size
#         self.generations = generations
#         self.crossover_rate = 0.7
#         self.mutation_rate = 0.2
        
#     def create_chromosome(self):
#         """Step 1a: Create random coloring"""
#         return {node: random.choice(self.colors) for node in self.nodes}
    
#     def initialize_population(self):
#         """Step 1b: Create initial population"""
#         return [self.create_chromosome() for _ in range(self.pop_size)]
    
#     def count_conflicts(self, coloring):
#         """Step 2a: Count conflicting edges"""
#         conflicts = 0
#         for node in self.graph:
#             for neighbor in self.graph[node]:
#                 if coloring[node] == coloring[neighbor]:
#                     conflicts += 1
#         return conflicts // 2  # Each conflict counted twice
    
#     def calculate_fitness(self, coloring):
#         """Step 2a: Calculate fitness"""
#         conflicts = self.count_conflicts(coloring)
#         return 1 / (1 + conflicts)
    
#     def tournament_selection(self, population):
#         """Step 2b: Tournament selection"""
#         new_population = []
        
#         for _ in range(self.pop_size):
#             competitors = random.sample(population, 3)
#             winner = max(competitors, key=self.calculate_fitness)
#             new_population.append(winner.copy())
        
#         return new_population
    
#     def crossover(self, population):
#         """Step 2c: Uniform crossover"""
#         new_population = []
        
#         for i in range(0, self.pop_size, 2):
#             parent1 = population[i]
#             parent2 = population[i+1] if i+1 < self.pop_size else population[0]
            
#             if random.random() < self.crossover_rate:
#                 child1 = {}
#                 child2 = {}
                
#                 for j, node in enumerate(self.nodes):
#                     if j < len(self.nodes) // 2:
#                         child1[node] = parent1[node]
#                         child2[node] = parent2[node]
#                     else:
#                     # Change terminal
#                     node.value = random.choice(self.terminals)
        
#         return population
    
#     def run(self, test_cases):
#         """Main GA Loop"""
#         print("\n\n" + "="*70)
#         print("5. TREE PROBLEM (Expression Tree Evolution)")
#         print("="*70)
#         print(f"Target Value: {self.target}")
#         print(f"Test Cases: {test_cases}")
        
#         # Step 1: Initialize
#         population = self.initialize_population()
#         best_tree = None
#         best_fitness = 0
#         history = []
        
#         # Step 2: Evolution loop
#         for gen in range(self.generations):
#             population = self.tournament_selection(population, test_cases)
#             population = self.crossover(population)
#             population = self.mutate(population)
            
#             # Track best
#             for tree in population:
#                 fitness = self.calculate_fitness(tree, test_cases)
#                 if fitness > best_fitness:
#                     best_fitness = fitness
#                     best_tree = tree.copy()
            
#             history.append(best_fitness)
            
#             if (gen + 1) % 20 == 0:
#                 print(f"\nGeneration {gen + 1}: Best Fitness = {best_fitness:.4f}")
        
#         # Step 3: Results
#         print("\n" + "="*70)
#         print("FINAL SOLUTION:")
#         print(f"  Best Expression: {best_tree}")
#         print(f"  Fitness: {best_fitness:.4f}")
#         print("\n  Test Results:")
#         for variables in test_cases:
#             try:
#                 result = best_tree.evaluate(variables)
#                 print(f"    {variables} → {result:.2f}")
#             except:
#                 print(f"    {variables} → Error")
#         print("="*70)
        
#         return best_tree, best_fitness, history


# # =============================================================================
# # 6. AVOIDING LOCAL MINIMA/MAXIMA
# # Problem: Find global maximum of f(x) = x*sin(10πx) + x
# # =============================================================================

# """
# ALGORITHM: Local Minima Avoidance GA

# INPUT:
#     - Function to optimize
#     - Search range
#     - GA parameters

# STEPS:
# 1. Initialize population with random x values in range
# 2. For each generation:
#    a. Evaluate f(x) for each chromosome
#    b. Tournament selection (maintains diversity)
#    c. Arithmetic crossover
#    d. Gaussian mutation (helps escape local optima)
#    e. Track best solution
# 3. Return global maximum

# OUTPUT: Best x value and f(x)
# """

# class LocalMinimaGA:
#     def __init__(self, pop_size=50, generations=100, x_min=-1, x_max=2):
#         self.pop_size = pop_size
#         self.generations = generations
#         self.x_min = x_min
#         self.x_max = x_max
#         self.crossover_rate = 0.9
#         self.mutation_rate = 0.1
        
#     def objective_function(self, x):
#         """Function to maximize: f(x) = x*sin(10πx) + x"""
#         return x * math.sin(10 * math.pi * x) + x
    
#     def create_chromosome(self):
#         """Step 1a: Create random x value"""
#         return random.uniform(self.x_min, self.x_max)
    
#     def initialize_population(self):
#         """Step 1b: Create initial population"""
#         return [self.create_chromosome() for _ in range(self.pop_size)]
    
#     def calculate_fitness(self, x):
#         """Step 2a: Calculate fitness"""
#         return self.objective_function(x)
    
#     def tournament_selection(self, population):
#         """Step 2b: Tournament selection (k=3)"""
#         new_population = []
        
#         for _ in range(self.pop_size):
#             competitors = random.sample(population, 3)
#             winner = max(competitors, key=self.calculate_fitness)
#             new_population.append(winner)
        
#         return new_population
    
#     def crossover(self, population):
#         """Step 2c: Arithmetic crossover"""
#         new_population = []
        
#         for i in range(0, self.pop_size, 2):
#             parent1 = population[i]
#             parent2 = population[i+1] if i+1 < self.pop_size else population[0]
            
#             if random.random() < self.crossover_rate:
#                 alpha = random.random()
#                 child1 = alpha * parent1 + (1 - alpha) * parent2
#                 child2 = (1 - alpha) * parent1 + alpha * parent2
#                 new_population.extend([child1, child2])
#             else:
#                 new_population.extend([parent1, parent2])
        
#         return new_population[:self.pop_size]
    
#     def mutate(self, population):
#         """Step 2d: Gaussian mutation"""
#         for i in range(len(population)):
#             if random.random() < self.mutation_rate:
#                 # Add Gaussian noise
#                 mutation = random.gauss(0, 0.1)
#                 population[i] += mutation
                
#                 # Keep in bounds
#                 population[i] = max(self.x_min, min(self.x_max, population[i]))
        
#         return population
    
#     def run(self):
#         """Main GA Loop"""
#         print("\n\n" + "="*70)
#         print("6. AVOIDING LOCAL MINIMA/MAXIMA")
#         print("="*70)
#         print(f"Function: f(x) = x*sin(10πx) + x")
#         print(f"Range: [{self.x_min}, {self.x_max}]")
        
#         # Step 1: Initialize
#         population = self.initialize_population()
#         best_x = None
#         best_fitness = float('-inf')
#         history = []
        
#         # Step 2: Evolution loop
#         for gen in range(self.generations):
#             population = self.tournament_selection(population)
#             population = self.crossover(population)
#             population = self.mutate(population)
            
#             # Track best
#             for x in population:
#                 fitness = self.calculate_fitness(x)
#                 if fitness > best_fitness:
#                     best_fitness = fitness
#                     best_x = x
            
#             history.append(best_fitness)
            
#             if (gen + 1) % 20 == 0:
#                 print(f"\nGeneration {gen + 1}: Best f(x) = {best_fitness:.6f} at x = {best_x:.6f}")
        
#         # Step 3: Results
#         print("\n" + "="*70)
#         print("FINAL SOLUTION:")
#         print(f"  Best x: {best_x:.6f}")
#         print(f"  Best f(x): {best_fitness:.6f}")
#         print("="*70)
        
#         return best_x, best_fitness, history


# # =============================================================================
# # MAIN EXECUTION - RUN ALL ALGORITHMS
# # =============================================================================

# if __name__ == "__main__":
#     print("\n")
#     print("╔" + "="*68 + "╗")
#     print("║" + " "*15 + "GENETIC ALGORITHMS COMPLETE SUITE" + " "*20 + "║")
#     print("╚" + "="*68 + "╝")
    
#     # 1. LINEAR EQUATION
#     print("\n\n")
#     linear_ga = LinearEquationGA(pop_size=6, generations=50)
#     solution1, error1, history1 = linear_ga.run()
    
#     # 2. KNAPSACK
#     items = [
#         {'name': 'Item 1', 'value': 60, 'weight': 10},
#         {'name': 'Item 2', 'value': 100, 'weight': 20},
#         {'name': 'Item 3', 'value': 120, 'weight': 30}
#     ]
#     knapsack_ga = KnapsackGA(items=items, max_weight=50, pop_size=10, generations=50)
#     solution2, fitness2, history2 = knapsack_ga.run()
    
#     # 3. TSP
#     distances = [
#         [0, 10, 15, 20, 25],
#         [10, 0, 35, 25, 30],
#         [15, 35, 0, 30, 20],
#         [20, 25, 30, 0, 15],
#         [25, 30, 20, 15, 0]
#     ]
#     tsp_ga = TravelingSalesmanGA(distances=distances, pop_size=20, generations=100)
#     solution3, distance3, history3 = tsp_ga.run()
    
#     # 4. COLOR MAP
#     graph = {
#         'A': ['B', 'C', 'D'],
#         'B': ['A', 'C'],
#         'C': ['A', 'B', 'D'],
#         'D': ['A', 'C']
#     }
#     color_ga = ColorMapGA(graph=graph, num_colors=3, pop_size=20, generations=100)
#     solution4, conflicts4, history4 = color_ga.run()
    
#     # 5. TREE PROBLEM
#     test_cases = [
#         {'x': 1, 'y': 2},
#         {'x': 2, 'y': 3},
#         {'x': 3, 'y': 4}
#     ]
#     tree_ga = TreeGA(target=10, max_depth=4, pop_size=20, generations=100)
#     solution5, fitness5, history5 = tree_ga.run(test_cases)
    
#     # 6. LOCAL MINIMA AVOIDANCE
#     local_ga = LocalMinimaGA(pop_size=50, generations=100)
#     solution6, fitness6, history6 = local_ga.run()
    
#     # PLOT ALL RESULTS
#     print("\n\n" + "="*70)
#     print("GENERATING PLOTS...")
#     print("="*70)
    
#     fig, axes = plt.subplots(2, 3, figsize=(15, 10))
#     fig.suptitle('Genetic Algorithms - Fitness Evolution', fontsize=16, fontweight='bold')
    
#     # Plot 1: Linear Equation
#     axes[0, 0].plot(history1, linewidth=2, color='blue')
#     axes[0, 0].set_title('Linear Equation', fontweight='bold')
#     axes[0, 0].set_xlabel('Generation')
#     axes[0, 0].set_ylabel('Error')
#     axes[0, 0].grid(True, alpha=0.3)
    
#     # Plot 2: Knapsack
#     axes[0, 1].plot(history2, linewidth=2, color='green')
#     axes[0, 1].set_title('Knapsack Problem', fontweight='bold')
#     axes[0, 1].set_xlabel('Generation')
#     axes[0, 1].set_ylabel('Total Value')
#     axes[0, 1].grid(True, alpha=0.3)
    
#     # Plot 3: TSP
#     axes[0, 2].plot(history3, linewidth=2, color='red')
#     axes[0, 2].set_title('Traveling Salesman', fontweight='bold')
#     axes[0, 2].set_xlabel('Generation')
#     axes[0, 2].set_ylabel('Distance')
#     axes[0, 2].grid(True, alpha=0.3)
    
#     # Plot 4: Color Map
#     axes[1, 0].plot(history4, linewidth=2, color='purple')
#     axes[1, 0].set_title('Color Map', fontweight='bold')
#     axes[1, 0].set_xlabel('Generation')
#     axes[1, 0].set_ylabel('Conflicts')
#     axes[1, 0].grid(True, alpha=0.3)
    
#     # Plot 5: Tree Problem
#     axes[1, 1].plot(history5, linewidth=2, color='orange')
#     axes[1, 1].set_title('Tree Problem', fontweight='bold')
#     axes[1, 1].set_xlabel('Generation')
#     axes[1, 1].set_ylabel('Fitness')
#     axes[1, 1].grid(True, alpha=0.3)
    
#     # Plot 6: Local Minima
#     axes[1, 2].plot(history6, linewidth=2, color='brown')
#     axes[1, 2].set_title('Local Minima Avoidance', fontweight='bold')
#     axes[1, 2].set_xlabel('Generation')
#     axes[1, 2].set_ylabel('f(x)')
#     axes[1, 2].grid(True, alpha=0.3)
    
#     plt.tight_layout()
#     plt.savefig('ga_results.png', dpi=300, bbox_inches='tight')
#     print("\n✓ Plots saved as 'ga_results.png'")
#     plt.show()
    
#     print("\n\n" + "="*70)
#     print("ALL ALGORITHMS COMPLETED SUCCESSFULLY!")
#     print("="*70)
#                         child1[node] = parent2[node]
#                         child2[node] = parent1[node]
                
#                 new_population.extend([child1, child2])
#             else:
#                 new_population.extend([parent1.copy(), parent2.copy()])
        
#         return new_population[:self.pop_size]
    
#     def mutate(self, population):
#         """Step 2d: Random color change"""
#         for coloring in population:
#             if random.random() < self.mutation_rate:
#                 node = random.choice(self.nodes)
#                 coloring[node] = random.choice(self.colors)
        
#         return population
    
#     def run(self):
#         """Main GA Loop"""
#         print("\n\n" + "="*70)
#         print("4. COLOR MAP PROBLEM")
#         print("="*70)
#         print(f"Number of Colors: {self.num_colors}")
#         print("Graph Structure:")
#         for node, neighbors in self.graph.items():
#             print(f"  {node} → {neighbors}")
        
#         # Step 1: Initialize
#         population = self.initialize_population()
#         best_coloring = None
#         best_conflicts = float('inf')
#         history = []
        
#         # Step 2: Evolution loop
#         for gen in range(self.generations):
#             population = self.tournament_selection(population)
#             population = self.crossover(population)
#             population = self.mutate(population)
            
#             # Track best
#             for coloring in population:
#                 conflicts = self.count_conflicts(coloring)
#                 if conflicts < best_conflicts:
#                     best_conflicts = conflicts
#                     best_coloring = coloring.copy()
            
#             history.append(best_conflicts)
            
#             if (gen + 1) % 20 == 0:
#                 print(f"\nGeneration {gen + 1}: Best Conflicts = {best_conflicts}")
            
#             if best_conflicts == 0:
#                 print(f"\n✓ Perfect coloring found at generation {gen + 1}!")
#                 break
        
#         # Step 3: Results
#         print("\n" + "="*70)
#         print("FINAL SOLUTION:")
#         print(f"  Best Coloring: {best_coloring}")
#         print(f"  Conflicts: {best_conflicts}")
        
#         if best_conflicts == 0:
#             print("\n  ✓ Valid coloring! No adjacent regions have the same color.")
#         else:
#             print(f"\n  ✗ Solution has {best_conflicts} conflicts.")
        
#         print("\n  Color Assignment:")
#         for node, color in best_coloring.items():
#             print(f"    Node {node}: Color {color}")
#         print("="*70)
        
#         return best_coloring, best_conflicts, history


# # =============================================================================
# # 5. TREE PROBLEM (Expression Tree)
# # Problem: Evolve mathematical expression trees
# # =============================================================================

# """
# ALGORITHM: Tree (Expression) GA

# INPUT:
#     - Target value to achieve
#     - Available operations (+, -, *, /)
#     - Variables and constants

# STEPS:
# 1. Initialize population with random expression trees
# 2. For each generation:
#    a. Evaluate each tree and calculate fitness
#    b. Tournament selection
#    c. Subtree crossover (exchange tree branches)
#    d. Mutation (change operator or value)
#    e. Track best tree
# 3. Return best expression

# OUTPUT: Best expression tree and its value
# """

# class TreeNode:
#     """Node in expression tree"""
#     def __init__(self, value, left=None, right=None):
#         self.value = value
#         self.left = left
#         self.right = right
#         self.is_operator = value in ['+', '-', '*', '/']
    
#     def evaluate(self, variables):
#         """Evaluate tree recursively"""
#         if not self.is_operator:
#             # Leaf node: number or variable
#             if isinstance(self.value, (int, float)):
#                 return self.value
#             else:
#                 return variables.get(self.value, 0)
        
#         # Operator node
#         left_val = self.left.evaluate(variables)
#         right_val = self.right.evaluate(variables)
        
#         if self.value == '+':
#             return left_val + right_val
#         elif self.value == '-':
#             return left_val - right_val
#         elif self.value == '*':
#             return left_val * right_val
#         elif self.value == '/':
#             return left_val / right_val if right_val != 0 else 1
    
#     def copy(self):
#         """Deep copy of tree"""
#         if self.is_operator:
#             return TreeNode(self.value, self.left.copy(), self.right.copy())
#         else:
#             return TreeNode(self.value)
    
#     def __str__(self):
#         """String representation"""
#         if not self.is_operator:
#             return str(self.value)
#         return f"({self.left} {self.value} {self.right})"


# class TreeGA:
#     def __init__(self, target, max_depth=4, pop_size=20, generations=100):
#         self.target = target
#         self.max_depth = max_depth
#         self.pop_size = pop_size
#         self.generations = generations
#         self.operators = ['+', '-', '*', '/']
#         self.terminals = [1, 2, 3, 4, 5, 'x', 'y']
#         self.crossover_rate = 0.7
#         self.mutation_rate = 0.1
        
#     def create_random_tree(self, depth=0):
#         """Step 1a: Create random expression tree"""
#         if depth >= self.max_depth or (depth > 0 and random.random() < 0.5):
#             # Create leaf node
#             return TreeNode(random.choice(self.terminals))
#         else:
#             # Create operator node
#             operator = random.choice(self.operators)
#             left = self.create_random_tree(depth + 1)
#             right = self.create_random_tree(depth + 1)
#             return TreeNode(operator, left, right)
    
#     def initialize_population(self):
#         """Step 1b: Create initial population"""
#         return [self.create_random_tree() for _ in range(self.pop_size)]
    
#     def calculate_fitness(self, tree, test_cases):
#         """Step 2a: Calculate fitness"""
#         total_error = 0
        
#         for variables in test_cases:
#             try:
#                 result = tree.evaluate(variables)
#                 error = abs(result - self.target)
#                 total_error += error
#             except:
#                 total_error += 1000  # Penalty for invalid expressions
        
#         return 1 / (1 + total_error)
    
#     def tournament_selection(self, population, test_cases):
#         """Step 2b: Tournament selection"""
#         new_population = []
        
#         for _ in range(self.pop_size):
#             competitors = random.sample(population, 3)
#             winner = max(competitors, key=lambda t: self.calculate_fitness(t, test_cases))
#             new_population.append(winner.copy())
        
#         return new_population
    
#     def get_random_subtree(self, tree):
#         """Helper: Get random subtree"""
#         nodes = []
        
#         def collect_nodes(node):
#             if node:
#                 nodes.append(node)
#                 if node.left:
#                     collect_nodes(node.left)
#                 if node.right:
#                     collect_nodes(node.right)
        
#         collect_nodes(tree)
#         return random.choice(nodes) if nodes else tree
    
#     def crossover(self, population):
#         """Step 2c: Subtree crossover"""
#         new_population = []
        
#         for i in range(0, self.pop_size, 2):
#             parent1 = population[i].copy()
#             parent2 = population[i+1].copy() if i+1 < self.pop_size else population[0].copy()
            
#             if random.random() < self.crossover_rate:
#                 # Exchange random subtrees
#                 subtree1 = self.get_random_subtree(parent1)
#                 subtree2 = self.get_random_subtree(parent2)
                
#                 # Swap subtrees
#                 temp = subtree1.copy()
#                 if subtree1.is_operator:
#                     subtree1.value = subtree2.value
#                     subtree1.left = subtree2.left
#                     subtree1.right = subtree2.right
#                 else:
#                     subtree1.value = subtree2.value
                
#                 new_population.extend([parent1, parent2])
#             else:
#                 new_population.extend([parent1, parent2])
        
#         return new_population[:self.pop_size]
    
#     def mutate(self, population):
#         """Step 2d: Mutation"""
#         for tree in population:
#             if random.random() < self.mutation_rate:
#                 node = self.get_random_subtree(tree)
                
#                 if node.is_operator:
#                     # Change operator
#                     node.value = random.choice(self.operators)
#                 else: