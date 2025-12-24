from __future__ import annotations
import numpy as np


def initialize_population(n: int, gene_min: int = 0, gene_max: int = 30) -> np.ndarray:
    return np.random.randint(gene_min, gene_max, (n, 4))


def compute_fitness(chromosome: np.ndarray) -> tuple[np.ndarray, np.ndarray, float, np.ndarray, np.ndarray]:
    objective = np.abs(30 - (chromosome[:, 0] + 2 * chromosome[:, 1] + 3 * chromosome[:, 2] + 4 * chromosome[:, 3]))
    fitness = 1.0 / (1.0 + objective)

    total = float(fitness.sum())
    prob = fitness / total
    cum_sum = np.cumsum(prob)
    return objective, fitness, total, prob, cum_sum


def selection(chromosome: np.ndarray, cum_sum: np.ndarray) -> np.ndarray:
    rand_nums = np.random.random(chromosome.shape[0])
    new_chromosome = np.zeros((chromosome.shape[0], 4), dtype=int)

    for i in range(len(rand_nums)):
        for j in range(len(cum_sum)):
            if rand_nums[i] < cum_sum[j]:
                new_chromosome[i, :] = chromosome[j, :]
                break
    return new_chromosome


def crossover(chromosome: np.ndarray, pc: float = 0.25) -> np.ndarray:
    n = chromosome.shape[0]
    rand_nums = np.random.random(n)
    flag = rand_nums < pc

    cross_chromosome = chromosome[flag]
    len_cross = len(cross_chromosome)
    if len_cross == 0:
        return chromosome

    cross_values = np.random.randint(1, 3, len_cross)
    cpy_chromosome = np.copy(cross_chromosome)

    for i in range(len_cross):
        c_val = int(cross_values[i])
        if i == len_cross - 1:
            cross_chromosome[i, c_val:] = cpy_chromosome[0, c_val:]
        else:
            cross_chromosome[i, c_val:] = cpy_chromosome[i + 1, c_val:]

    idx = 0
    for i in range(n):
        if flag[i]:
            chromosome[i, :] = cross_chromosome[idx, :]
            idx += 1
    return chromosome


def mutation(chromosome: np.ndarray, pm: float = 0.1, gene_min: int = 0, gene_max: int = 30) -> np.ndarray:
    total_gen = chromosome.size
    no_of_mutations = int(np.round(pm * total_gen))
    if no_of_mutations <= 0:
        return chromosome

    gen_num = np.random.randint(0, total_gen - 1, no_of_mutations)
    replacing_num = np.random.randint(gene_min, gene_max, no_of_mutations)

    for i in range(no_of_mutations):
        a = int(gen_num[i])
        row = a // 4
        col = a % 4
        chromosome[row, col] = int(replacing_num[i])
    return chromosome


def run_linear_equation_ga(n: int = 6, epochs: int = 50, seed: int | None = None) -> dict:
    if seed is not None:
        np.random.seed(seed)

    chromosome = initialize_population(n)

    for epoch in range(epochs):
        objective, fitness_vals, total, prob, cum_sum = compute_fitness(chromosome)
        best_idx = int(np.argmax(fitness_vals))

        if int(objective[best_idx]) == 0:
            return {
                "found": True,
                "epoch": epoch,
                "best": chromosome[best_idx].copy(),
                "objective": int(objective[best_idx]),
                "fitness": float(fitness_vals[best_idx]),
                "final_population": chromosome.copy(),
            }

        chromosome = selection(chromosome, cum_sum)
        chromosome = crossover(chromosome)
        chromosome = mutation(chromosome)

    objective, fitness_vals, *_ = compute_fitness(chromosome)
    best_idx = int(np.argmax(fitness_vals))
    return {
        "found": False,
        "epoch": epochs,
        "best": chromosome[best_idx].copy(),
        "objective": int(objective[best_idx]),
        "fitness": float(fitness_vals[best_idx]),
        "final_population": chromosome.copy(),
    }
