from __future__ import annotations
import random
from typing import Any


def generate_random_tree(depth: int = 3) -> Any:
    if depth == 0:
        return random.choice(["x", "y", random.randint(1, 10)])
    operator = random.choice(["+", "-", "*", "/"])
    return [operator, generate_random_tree(depth - 1), generate_random_tree(depth - 1)]


def evaluate(tree: Any, vars: dict[str, float]) -> float:
    if isinstance(tree, (int, float)):
        return float(tree)
    if isinstance(tree, str):
        return float(vars[tree])

    operator, left, right = tree
    left_val = evaluate(left, vars)
    right_val = evaluate(right, vars)

    if operator == "+":
        return left_val + right_val
    if operator == "-":
        return left_val - right_val
    if operator == "*":
        return left_val * right_val
    if operator == "/":
        return left_val / right_val if right_val != 0 else float("inf")

    raise ValueError(f"Unknown operator: {operator}")


def fitness(tree: Any, target: float, vars: dict[str, float]) -> float:
    try:
        result = evaluate(tree, vars)
        return -abs(result - target)
    except Exception:
        return float("-inf")


def selection_gp(population: list[Any], fitness_scores: list[float]) -> list[Any]:
    selected = []
    for _ in range(len(population) // 2):
        i, j = random.sample(range(len(population)), 2)
        selected.append(population[i] if fitness_scores[i] > fitness_scores[j] else population[j])
    return selected


def crossover_gp(parent1: Any, parent2: Any) -> Any:
    if not isinstance(parent1, list) or not isinstance(parent2, list):
        return parent1 if random.random() < 0.5 else parent2

    operator = parent1[0]
    if random.random() < 0.5:
        return [operator, parent2[1], parent1[2]]
    return [operator, parent1[1], parent2[2]]


def mutate_gp(tree: Any, mutation_rate: float = 0.1) -> Any:
    if random.random() < mutation_rate:
        return generate_random_tree(depth=2)
    if isinstance(tree, list):
        return [tree[0], mutate_gp(tree[1], mutation_rate), mutate_gp(tree[2], mutation_rate)]
    return tree


def run_symbolic_gp(
    variables: dict[str, float] | None = None,
    target_value: float = 21.0,
    generations: int = 50,
    pop_size: int = 20,
    mutation_rate: float = 0.1,
    seed: int | None = None,
) -> dict:
    if seed is not None:
        random.seed(seed)

    variables = variables or {"x": 4.0, "y": 5.0}

    population = [generate_random_tree(depth=3) for _ in range(pop_size)]
    best_tree = population[0]
    best_fit = float("-inf")

    for gen in range(generations):
        fitness_scores = [fitness(tree, target_value, variables) for tree in population]

        zipped = sorted(zip(fitness_scores, population), key=lambda x: x[0], reverse=True)
        population = [x[1] for x in zipped[: pop_size // 2]]

        best_tree = population[0]
        best_fit = fitness(best_tree, target_value, variables)
        if best_fit == 0:
            return {
                "found": True,
                "generation": gen,
                "best_tree": best_tree,
                "fitness": best_fit,
                "value": evaluate(best_tree, variables),
            }

        new_population = []
        while len(new_population) < pop_size:
            if len(population) < 2:
                break
            parent1, parent2 = random.sample(population, 2)
            child = crossover_gp(parent1, parent2)
            child = mutate_gp(child, mutation_rate)
            new_population.append(child)

        population = new_population[:pop_size]

    return {
        "found": False,
        "generation": generations,
        "best_tree": best_tree,
        "fitness": best_fit,
        "value": evaluate(best_tree, variables),
    }
