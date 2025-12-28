def create_graph(n):
    return {i: [] for i in range(1, n + 1)} # Словарь для каждой вершины с списком значений - с какой вершиной есть ребро. Изначально пустой!

def add_edge(graph, u, v): # будем строить неорграфы
    graph[u].append(v) 
    graph[v].append(u)

def test_add_edge():
    example = create_graph(3)
    assert example == {1: [], 2: [], 3: []} 
    add_edge(example, 1, 3)
    add_edge(example, 2, 1)
    add_edge(example, 3, 2)
    assert example == {1: [3, 2], 2: [1, 3], 3: [1, 2]}
    print("test_add_edge complete!")

if __name__ == '__main__':
    test_add_edge()
    example = create_graph(5)
    add_edge(example, 1, 2)
    add_edge(example, 1, 3)
    add_edge(example, 2, 5)
    add_edge(example, 2, 4)
    add_edge(example, 3, 5)
    print("Проверка", example)