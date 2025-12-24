from __future__ import annotations
import random
import numpy as np


def create_initial_population(pop_size: int) -> list[float]:
    return [random.uniform(0, 2) for _ in range(pop_size)]


def fitness_function(x: float) -> float:
    return float(x * np.sin(10 * x) + x)


def tournament_selection(pop: list[float], k: int = 3) -> float:
    selected = random.sample(pop, k)
    selected.sort(key=fitness_function, reverse=True)
    return selected[0]


def crossover_uniform(parent1: float, parent2: float, swap_rate: float = 0.5) -> float:
    if random.random() < swap_rate:
        alpha = random.random()
        return float(alpha * parent1 + (1 - alpha) * parent2)
    return float(parent1)


def mutate(child: float, mutation_rate: float = 0.1) -> float:
    if random.random() < mutation_rate:
        child += random.uniform(-0.2, 0.2)
        child = max(0.0, min(2.0, child))
    return float(child)


def run_continuous_opt_ga(generations: int = 400, pop_size: int = 100, seed: int | None = None) -> dict:
    if seed is not None:
        random.seed(seed)
        np.random.seed(seed)

    population = create_initial_population(pop_size)

    for _ in range(generations):
        new_population = []
        for _ in range(pop_size):
            parent1 = tournament_selection(population)
            parent2 = tournament_selection(population)
            child = crossover_uniform(parent1, parent2)
            child = mutate(child)
            new_population.append(child)
        population = new_population

    best = max(population, key=fitness_function)
    return {"best_x": best, "best_value": fitness_function(best)}
