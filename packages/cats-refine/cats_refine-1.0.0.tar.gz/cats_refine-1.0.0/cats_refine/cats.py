import numpy as np
import random
import copy
from typing import Callable, List, Any, Tuple

class CATS:
    """Matrix-Based Metaheuristic Optimizer with Optuna tuning support."""
    
    def __init__(
        self,
        objective_function: Callable[[List[Any]], float],
        products: List[Any],
        n_cats: int = 10,
        n_iter: int = 50,
        penalty: float = 0.2,
        random_seed: int = None,
    ):
        self.objective_function = objective_function
        self.products = list(products)
        self.n_cats = n_cats
        self.n_iter = n_iter
        self.penalty = penalty
        self.n_dim = len(products)
        
        if random_seed is not None:
            random.seed(random_seed)
            np.random.seed(random_seed)

        # Initialize Probability Matrix (Pheromone-like)
        self.matrix = np.ones((self.n_dim, self.n_dim)) / self.n_dim
        self.best_solution = None
        self.best_cost = float('inf')

    def _generate_schedule(self) -> List[Any]:
        """Generates a solution based on the probability matrix."""
        remaining = list(range(self.n_dim))
        idx_sequence = []
        
        current_pos = 0
        while remaining:
            probs = self.matrix[current_pos, remaining]
            probs /= probs.sum()
            next_idx = np.random.choice(remaining, p=probs)
            idx_sequence.append(next_idx)
            remaining.remove(next_idx)
            current_pos = next_idx
            
        return [self.products[i] for i in idx_sequence]

    def search(self) -> Tuple[List[Any], float]:
        """Main optimization loop."""
        for _ in range(self.n_iter):
            solutions = []
            for _ in range(self.n_cats):
                sol = self._generate_schedule()
                cost = self.objective_function(sol)
                solutions.append((sol, cost))
                
                if cost < self.best_cost:
                    self.best_cost = cost
                    self.best_solution = copy.deepcopy(sol)

            # Update Matrix (Reinforce best paths)
            self.matrix *= (1 - self.penalty) # Evaporation
            best_idx = [self.products.index(p) for p in self.best_solution]
            for i in range(len(best_idx)-1):
                self.matrix[best_idx[i], best_idx[i+1]] += self.penalty
                
        return self.best_solution, self.best_cost