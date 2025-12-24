from __future__ import annotations
import argparse

from .linear_equation_ga import run_linear_equation_ga
from .tsp_ga import run_tsp_ga
from .eight_queens_ga import run_eight_queens_ga
from .graph_coloring_ga import run_graph_coloring_ga
from .continuous_opt_ga import run_continuous_opt_ga
from .knapsack_ga import run_knapsack_ga
from .symbolic_gp import run_symbolic_gp


def main() -> None:
    parser = argparse.ArgumentParser(prog="genetic-toolkit")
    sub = parser.add_subparsers(dest="cmd", required=True)

    sub.add_parser("linear")
    tsp = sub.add_parser("tsp")
    tsp.add_argument("--cities", type=int, default=10)
    tsp.add_argument("--gens", type=int, default=100)

    sub.add_parser("queens")
    sub.add_parser("coloring")
    sub.add_parser("continuous")
    sub.add_parser("knapsack")
    sub.add_parser("gp")

    parser.add_argument("--seed", type=int, default=None)

    args = parser.parse_args()

    if args.cmd == "linear":
        print(run_linear_equation_ga(seed=args.seed))
    elif args.cmd == "tsp":
        print(run_tsp_ga(n_cities=args.cities, generations=args.gens, seed=args.seed))
    elif args.cmd == "queens":
        print(run_eight_queens_ga(seed=args.seed))
    elif args.cmd == "coloring":
        print(run_graph_coloring_ga(seed=args.seed))
    elif args.cmd == "continuous":
        print(run_continuous_opt_ga(seed=args.seed))
    elif args.cmd == "knapsack":
        print(run_knapsack_ga(seed=args.seed))
    elif args.cmd == "gp":
        print(run_symbolic_gp(seed=args.seed))
