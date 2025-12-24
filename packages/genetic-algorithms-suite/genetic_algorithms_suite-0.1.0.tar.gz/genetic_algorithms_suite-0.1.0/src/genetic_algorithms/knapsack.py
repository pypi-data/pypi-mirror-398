import random

weights = [2,3,4,5]
values = [3,4,5,6]
capacity = 5
POP_SIZE = 20
GENERATIONS = 100
MUTATION_RATE = 0.1

def create_individual():
    return [random.randint(0,1) for _ in range(len(weights))]

def create_population():
    return [create_individual() for _ in range(POP_SIZE)]

def fitness(individual):
    total_weight = sum([weights[i] for i in range(len(individual)) if individual[i]==1])
    total_value = sum([values[i] for i in range(len(individual)) if individual[i]==1])
    if total_weight>capacity:
        return 0
    return total_value

def selection(population):
    population = sorted(population, key=fitness, reverse=True)
    return population[0], population[1]

def crossover(p1, p2):
    point = random.randint(1, len(p1)-1)
    return p1[:point]+p2[point:], p2[:point]+p1[point:]

def mutation(individual):
    for i in range(len(individual)):
        if random.random()<MUTATION_RATE:
            individual[i] = 1 - individual[i]

def genetic_algorithm():
    population = create_population()
    for _ in range(GENERATIONS):
        new_population=[]
        parent1, parent2 = selection(population)
        child1, child2 = crossover(parent1, parent2)
        mutation(child1)
        mutation(child2)
        new_population.extend([child1, child2])
        while len(new_population)<POP_SIZE:
            new_population.append(create_individual())
        population = new_population
    best = max(population, key=fitness)
    return best, fitness(best)
