import random
import math

POP_SIZE = 30
GENERATIONS = 200
MUTATION_RATE = 0.1
X_MIN, X_MAX = 0, 10

def create_individual():
    return random.uniform(X_MIN, X_MAX)

def create_population():
    return [create_individual() for _ in range(POP_SIZE)]

def fitness(x):
    return x*math.sin(10*x)+x

def selection(population, k=3):
    competitors = random.sample(population, k)
    return max(competitors, key=fitness)

def crossover(p1, p2):
    alpha = random.random()
    return alpha*p1 + (1-alpha)*p2

def mutation(x):
    if random.random()<MUTATION_RATE:
        x += random.uniform(-0.5,0.5)
        x = max(X_MIN, min(X_MAX, x))
    return x

def genetic_algorithm():
    population = create_population()
    for _ in range(GENERATIONS):
        new_population=[]
        for _ in range(POP_SIZE):
            p1 = selection(population)
            p2 = selection(population)
            child = crossover(p1,p2)
            child = mutation(child)
            new_population.append(child)
        population = new_population
    best = max(population, key=fitness)
    return best, fitness(best)
