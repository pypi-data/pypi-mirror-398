import pyperf
from tuple_list_benchmark.base import funcs

if __name__ == "__main__":
    runner = pyperf.Runner()
    sizes = [10, 50, 100, 500, 1000, 10000, 100000]

    for n in sizes:
        for func in funcs['tuple']:
            runner.bench_func(f'{func.__name__.split("_")[-1]}_{n}', func, n)
