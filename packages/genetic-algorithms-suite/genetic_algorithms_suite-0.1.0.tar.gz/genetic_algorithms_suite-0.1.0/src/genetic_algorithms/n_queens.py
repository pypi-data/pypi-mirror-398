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
