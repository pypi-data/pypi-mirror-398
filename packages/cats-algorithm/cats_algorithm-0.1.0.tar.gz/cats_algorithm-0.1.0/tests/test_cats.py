import numpy as np
from cats_algorithm import CATS

def test_tsp():
    cost_matrix = np.array([[0, 1], [1, 0]])
    products = [0, 1]
    
    # Define objective function
    def tsp_cost(schedule):
        return sum(cost_matrix[schedule[i]][schedule[i + 1]] for i in range(len(schedule) - 1)) + cost_matrix[schedule[-1]][schedule[0]]
    
    solver = CATS(
        objective_function=tsp_cost,
        products=products,
        n_iter=1,  # Run only 1 iteration for test speed
        random_seed=42
    )
    path, cost = solver.search()
    
    assert path is not None, "Path should not be None"
    assert sorted(path) == sorted(products), "Path must include all products"
    assert cost == tsp_cost(path), f"Expected cost {tsp_cost(path)}, got {cost}"
    
if __name__ == "__main__":
    test_tsp()