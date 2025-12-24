import random

NUM_REGIONS = 5
NUM_COLORS = 3
POP_SIZE = 30
GENERATIONS = 200
MUTATION_RATE = 0.1

adjacency = {
    0: [1, 2],
    1: [0, 2, 3],
    2: [0, 1, 3],
    3: [1, 2, 4],
    4: [3]
}

def create_individual():
    return [random.randint(0, NUM_COLORS - 1) for _ in range(NUM_REGIONS)]

def create_population():
    return [create_individual() for _ in range(POP_SIZE)]

def fitness(individual):
    conflicts = 0
    for region in adjacency:
        for neighbor in adjacency[region]:
            if individual[region] == individual[neighbor]:
                conflicts += 1
    return conflicts // 2

def selection(population):
    population.sort(key=fitness)
    return population[0], population[1]

def crossover(parent1, parent2):
    point = random.randint(1, NUM_REGIONS - 1)
    return parent1[:point] + parent2[point:], parent2[:point] + parent1[point:]

def mutation(individual):
    for i in range(NUM_REGIONS):
        if random.random() < MUTATION_RATE:
            individual[i] = random.randint(0, NUM_COLORS - 1)

def genetic_algorithm():
    population = create_population()
    for _ in range(GENERATIONS):
        new_population = []
        parent1, parent2 = selection(population)
        child1, child2 = crossover(parent1, parent2)
        mutation(child1)
        mutation(child2)
        new_population.extend([child1, child2])
        while len(new_population) < POP_SIZE:
            new_population.append(create_individual())
        population = new_population
        best = min(population, key=fitness)
        if fitness(best) == 0:
            return best
    return min(population, key=fitness)
