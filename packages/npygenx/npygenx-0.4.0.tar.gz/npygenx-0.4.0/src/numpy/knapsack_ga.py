from __future__ import annotations
import random


DEFAULT_VALUES = [60, 100, 120, 80, 150]
DEFAULT_WEIGHTS = [10, 20, 30, 25, 50]
DEFAULT_MAX_WEIGHT = 50


def initialize_population(pop_size: int, num_items: int) -> list[list[int]]:
    return [[random.randint(0, 1) for _ in range(num_items)] for _ in range(pop_size)]


def fitness(chromosome: list[int], values: list[int], weights: list[int], max_weight: int) -> int:
    total_value = sum(chromosome[i] * values[i] for i in range(len(chromosome)))
    total_weight = sum(chromosome[i] * weights[i] for i in range(len(chromosome)))
    if total_weight > max_weight:
        return 0
    return total_value


def selection(population: list[list[int]], values: list[int], weights: list[int], max_weight: int) -> list[list[int]]:
    population = sorted(population, key=lambda ch: fitness(ch, values, weights, max_weight), reverse=True)
    return population[: len(population) // 2]


def crossover(parent1: list[int], parent2: list[int]) -> tuple[list[int], list[int]]:
    if len(parent1) > 1:
        point = random.randint(1, len(parent1) - 1)
        child1 = parent1[:point] + parent2[point:]
        child2 = parent2[:point] + parent1[point:]
        return child1, child2
    return parent1[:], parent2[:]


def mutate(chromosome: list[int], mutation_rate: float = 0.1) -> list[int]:
    for i in range(len(chromosome)):
        if random.random() < mutation_rate:
            chromosome[i] = 1 - chromosome[i]
    return chromosome


def run_knapsack_ga(
    pop_size: int = 10,
    generations: int = 50,
    mutation_rate: float = 0.1,
    values: list[int] | None = None,
    weights: list[int] | None = None,
    max_weight: int = DEFAULT_MAX_WEIGHT,
    seed: int | None = None,
) -> dict:
    if seed is not None:
        random.seed(seed)

    values = values or DEFAULT_VALUES
    weights = weights or DEFAULT_WEIGHTS

    population = initialize_population(pop_size, len(values))

    for _ in range(generations):
        selected = selection(population, values, weights, max_weight)
        next_generation: list[list[int]] = []

        while len(next_generation) < pop_size:
            parent1, parent2 = random.sample(selected, 2)
            child1, child2 = crossover(parent1, parent2)
            next_generation.append(mutate(child1, mutation_rate))
            if len(next_generation) < pop_size:
                next_generation.append(mutate(child2, mutation_rate))

        population = next_generation

    best_solution = max(population, key=lambda ch: fitness(ch, values, weights, max_weight))
    best_value = fitness(best_solution, values, weights, max_weight)
    best_weight = sum(best_solution[i] * weights[i] for i in range(len(best_solution)))

    return {"best_items": best_solution, "best_value": best_value, "best_weight": best_weight}
