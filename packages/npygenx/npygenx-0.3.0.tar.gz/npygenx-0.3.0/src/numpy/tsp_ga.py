from __future__ import annotations
import random
import numpy as np


def create_route(n: int) -> list[int]:
    route = list(range(n))
    random.shuffle(route)
    return route


def initial_population(pop_size: int, n: int) -> list[list[int]]:
    return [create_route(n) for _ in range(pop_size)]


def distance(a: tuple[float, float], b: tuple[float, float]) -> float:
    return float(np.sqrt((a[0] - b[0]) ** 2 + (a[1] - b[1]) ** 2))


def route_distance(route: list[int], cities: list[tuple[float, float]]) -> float:
    total = 0.0
    for i in range(len(route) - 1):
        total += distance(cities[route[i]], cities[route[i + 1]])
    total += distance(cities[route[-1]], cities[route[0]])
    return float(total)


def fitness(route: list[int], cities: list[tuple[float, float]]) -> float:
    d = route_distance(route, cities)
    return 1.0 / d if d > 0 else float("inf")


def crossover(parent_1: list[int], parent_2: list[int], n_cities: int) -> tuple[list[int], list[int]]:
    cut = random.randint(1, n_cities - 1)
    offspring_1 = parent_1[0:cut] + [city for city in parent_2 if city not in parent_1[0:cut]]
    offspring_2 = parent_2[0:cut] + [city for city in parent_1 if city not in parent_2[0:cut]]
    return offspring_1, offspring_2


def mutate(route: list[int], mutation_rate: float) -> list[int]:
    for i in range(len(route)):
        if random.random() < mutation_rate:
            j = random.randint(0, len(route) - 1)
            route[i], route[j] = route[j], route[i]
    return route


def genetic_algorithm(
    cities: list[tuple[float, float]],
    pop_size: int = 100,
    top_parents: int = 20,
    mutation_rate: float = 0.01,
    generations: int = 300,
    seed: int | None = None,
) -> tuple[list[tuple[list[int], int, float]], list[int], float]:
    if seed is not None:
        random.seed(seed)
        np.random.seed(seed)

    n = len(cities)
    population = initial_population(pop_size, n)
    history: list[tuple[list[int], int, float]] = []

    for gen in range(generations):
        population = sorted(population, key=lambda x: fitness(x, cities), reverse=True)
        parents = population[:top_parents]

        children: list[list[int]] = []
        while len(children) < (pop_size - top_parents):
            parent1, parent2 = random.sample(parents, 2)
            child1, child2 = crossover(parent1, parent2, n)
            children.append(mutate(child1, mutation_rate))
            if len(children) < (pop_size - top_parents):
                children.append(mutate(child2, mutation_rate))

        population = parents + children
        best_route = population[0]
        best_dist = route_distance(best_route, cities)
        history.append((best_route[:], gen, best_dist))

    best_route = sorted(population, key=lambda x: fitness(x, cities), reverse=True)[0]
    best_distance = route_distance(best_route, cities)
    return history, best_route, best_distance


def run_tsp_ga(
    n_cities: int = 10,
    pop_size: int = 50,
    top_parents: int = 10,
    mutation_rate: float = 0.01,
    generations: int = 100,
    seed: int | None = None,
) -> dict:
    if seed is not None:
        random.seed(seed)
        np.random.seed(seed)

    cities = [(random.uniform(0, 100), random.uniform(0, 100)) for _ in range(n_cities)]
    history, best_route, best_distance = genetic_algorithm(
        cities,
        pop_size=pop_size,
        top_parents=top_parents,
        mutation_rate=mutation_rate,
        generations=generations,
        seed=seed,
    )
    return {
        "cities": cities,
        "history": history,
        "best_route": best_route,
        "best_distance": best_distance,
    }
