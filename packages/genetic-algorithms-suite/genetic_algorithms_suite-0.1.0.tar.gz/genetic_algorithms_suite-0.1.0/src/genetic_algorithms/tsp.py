import random
import math

cities = [(0,0),(2,6),(5,2),(6,6),(8,3)]
NUM_CITIES = len(cities)
POP_SIZE = 50
GENERATIONS = 300
MUTATION_RATE = 0.1

def distance(c1,c2):
    return math.sqrt((c1[0]-c2[0])**2 + (c1[1]-c2[1])**2)

def total_distance(path):
    dist = 0
    for i in range(len(path)):
        dist += distance(cities[path[i]], cities[path[(i+1)%NUM_CITIES]])
    return dist

def create_individual():
    path = list(range(NUM_CITIES))
    random.shuffle(path)
    return path

def create_population():
    return [create_individual() for _ in range(POP_SIZE)]

def selection(population):
    population.sort(key=total_distance)
    return population[0], population[1]

def crossover(p1,p2):
    start,end = sorted(random.sample(range(NUM_CITIES),2))
    child = [-1]*NUM_CITIES
    child[start:end] = p1[start:end]
    pointer = 0
    for city in p2:
        if city not in child:
            while child[pointer]!=-1:
                pointer+=1
            child[pointer]=city
    return child

def mutation(path):
    if random.random()<MUTATION_RATE:
        i,j=random.sample(range(NUM_CITIES),2)
        path[i],path[j]=path[j],path[i]

def genetic_algorithm():
    population = create_population()
    for _ in range(GENERATIONS):
        new_population=[]
        parent1,parent2 = selection(population)
        child1 = crossover(parent1,parent2)
        child2 = crossover(parent2,parent1)
        mutation(child1)
        mutation(child2)
        new_population.extend([child1,child2])
        while len(new_population)<POP_SIZE:
            new_population.append(create_individual())
        population = new_population
    best = min(population,key=total_distance)
    return best, total_distance(best)
