from __future__ import annotations
import numpy as np


def init_population(pop_size: int) -> np.ndarray:
    return np.random.randint(0, 8, (pop_size, 8))


def fitness(population: np.ndarray) -> np.ndarray:
    fitness_vals = []
    for individual in population:
        conflicts = 0
        for i in range(len(individual)):
            row = int(individual[i])
            for j in range(len(individual)):
                if i == j:
                    continue
                d = abs(i - j)
                if individual[j] in [row, row - d, row + d]:
                    conflicts += 1
        fitness_vals.append(conflicts)
    return -1 * np.array(fitness_vals, dtype=float)


def selection(population: np.ndarray, fitness_vals: np.ndarray) -> np.ndarray:
    probs = fitness_vals.copy()
    min_fitness = abs(probs.min()) + 1.0
    probs = probs + min_fitness
    probs = probs / probs.sum()

    n = len(population)
    indices = np.arange(n)
    selected_indices = np.random.choice(indices, size=n, p=probs)
    return population[selected_indices]


def crossover(parent1: np.ndarray, parent2: np.ndarray, pc: float) -> tuple[np.ndarray, np.ndarray]:
    r = np.random.random()
    if r < pc:
        point = np.random.randint(1, 8)
        child1 = np.concatenate([parent1[:point], parent2[point:]])
        child2 = np.concatenate([parent2[:point], parent1[point:]])
    else:
        child1 = parent1.copy()
        child2 = parent2.copy()
    return child1, child2


def mutation(individual: np.ndarray, pm: float) -> np.ndarray:
    r = np.random.random()
    if r < pm:
        m = np.random.randint(8)
        individual[m] = np.random.randint(8)
    return individual


def crossover_mutation(selected_pop: np.ndarray, pc: float, pm: float) -> np.ndarray:
    n = len(selected_pop)
    new_pop = np.empty((n, 8), dtype=int)

    for i in range(0, n, 2):
        parent1 = selected_pop[i]
        parent2 = selected_pop[i + 1]
        child1, child2 = crossover(parent1, parent2, pc)
        new_pop[i] = child1
        new_pop[i + 1] = child2

    for i in range(n):
        new_pop[i] = mutation(new_pop[i], pm)
    return new_pop


def run_eight_queens_ga(pop_size: int = 100, max_generations: int = 1000, pc: float = 0.7, pm: float = 0.01, seed: int | None = None) -> dict:
    if seed is not None:
        np.random.seed(seed)

    population = init_population(pop_size)
    best_fitness_overall = None
    best_solution = None
    best_gen = None

    for gen in range(max_generations):
        fitness_vals = fitness(population)
        best_i = int(fitness_vals.argmax())
        best_fit = float(fitness_vals[best_i])

        if best_fitness_overall is None or best_fit > best_fitness_overall:
            best_fitness_overall = best_fit
            best_solution = population[best_i].copy()
            best_gen = gen

        if best_fitness_overall == 0:
            break

        selected_pop = selection(population, fitness_vals)
        if len(selected_pop) % 2 == 1:
            selected_pop = selected_pop[:-1]
        population = crossover_mutation(selected_pop, pc, pm)

    return {
        "best_solution": best_solution,
        "best_fitness": best_fitness_overall,
        "generation": best_gen,
    }
