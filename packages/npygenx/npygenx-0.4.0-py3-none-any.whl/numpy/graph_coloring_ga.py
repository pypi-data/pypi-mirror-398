from __future__ import annotations
import random


def random_chromosome(num_genes: int, num_colors: int) -> list[int]:
    return [random.randint(0, num_colors - 1) for _ in range(num_genes)]


def initial_population(pop_size: int, num_genes: int, num_colors: int) -> list[list[int]]:
    return [random_chromosome(num_genes, num_colors) for _ in range(pop_size)]


def fitness(chromosome: list[int], graph: dict[int, list[int]]) -> float:
    conflicts = 0
    for node, neighbors in graph.items():
        for n in neighbors:
            if chromosome[node] == chromosome[n]:
                conflicts += 1
    conflicts //= 2
    return 1.0 / (1.0 + conflicts)


def selection(population: list[list[int]], graph: dict[int, list[int]], k: int = 3) -> list[int]:
    selected = random.sample(population, k)
    selected.sort(key=lambda x: fitness(x, graph), reverse=True)
    return selected[0]


def crossover(parent1: list[int], parent2: list[int]) -> tuple[list[int], list[int]]:
    if len(parent1) > 2:
        point = random.randint(1, len(parent1) - 2)
        child1 = parent1[:point] + parent2[point:]
        child2 = parent2[:point] + parent1[point:]
        return child1, child2
    return parent1[:], parent2[:]


def mutate(chromosome: list[int], mutation_rate: float, num_colors: int) -> list[int]:
    for i in range(len(chromosome)):
        if random.random() < mutation_rate:
            old_color = chromosome[i]
            new_color = random.randint(0, num_colors - 1)
            while new_color == old_color:
                new_color = random.randint(0, num_colors - 1)
            chromosome[i] = new_color
    return chromosome


def map_coloring_ga(
    graph: dict[int, list[int]],
    num_colors: int,
    pop_size: int = 100,
    generations: int = 500,
    crossover_rate: float = 0.8,
    mutation_rate: float = 0.01,
    seed: int | None = None,
) -> tuple[list[int] | None, float]:
    if seed is not None:
        random.seed(seed)

    num_genes = len(graph)
    population = initial_population(pop_size, num_genes, num_colors)
    best_solution: list[int] | None = None
    best_fitness = 0.0

    for _ in range(generations):
        fitness_values = [fitness(ch, graph) for ch in population]
        best_index = fitness_values.index(max(fitness_values))
        current_best = population[best_index]
        current_best_fit = fitness_values[best_index]

        if current_best_fit > best_fitness:
            best_solution = current_best[:]
            best_fitness = current_best_fit

        if best_fitness == 1.0:
            break

        population.sort(key=lambda ch: fitness(ch, graph), reverse=True)
        new_population = population[:2]

        while len(new_population) < pop_size:
            parent1 = selection(population, graph)
            parent2 = selection(population, graph)

            if random.random() < crossover_rate:
                child1, child2 = crossover(parent1, parent2)
            else:
                child1, child2 = parent1[:], parent2[:]

            mutate(child1, mutation_rate, num_colors)
            mutate(child2, mutation_rate, num_colors)
            new_population.extend([child1, child2])

        population = new_population[:pop_size]

    return best_solution, best_fitness


def run_graph_coloring_ga(seed: int | None = None) -> dict:
    graph = {
        0: [1, 2],
        1: [0, 2, 3],
        2: [0, 1, 4, 3],
        3: [1, 4, 2],
        4: [2, 3],
    }
    solution, fit = map_coloring_ga(graph, num_colors=3, pop_size=50, generations=100, seed=seed)
    return {"graph": graph, "solution": solution, "fitness": fit}
