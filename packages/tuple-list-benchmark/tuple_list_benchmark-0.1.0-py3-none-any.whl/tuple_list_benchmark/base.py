def tuple_range(n):
    return tuple(range(n))
def tuple_mul(n):
    return (0,) * n
def list_range(n):
    return list(range(n))
def list_mul(n):
    return [0] * n

funcs = {
    'tuple': [tuple_range, tuple_mul],
    'list': [list_range, list_mul],
}
