import numpy as np
from cats_refine import CATS, compare_algorithms, generate_report

# Example: Solve a 5-city TSP
def my_objective(sol):
    return sum(sol) # Simple dummy objective

cities = [10, 20, 30, 40, 50]
model = CATS(my_objective, cities, n_iter=20)
sol, cost = model.search()

bench = compare_algorithms(my_objective, cities)
generate_report("colab_test", "Colab Run", "Testing in Colab environment", {}, sol, cost, bench)

# To download from Colab:
from google.colab import files
files.download('colab_test.pdf')
files.download('colab_test.xlsx')