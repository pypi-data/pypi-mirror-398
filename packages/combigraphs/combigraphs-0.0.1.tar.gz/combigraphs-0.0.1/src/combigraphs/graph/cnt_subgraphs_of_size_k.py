from combigraphs.combfuncs import comb

def count_subgraphs_of_size_k(graph, k):
    '''Находит максимальное количество подграфов размера k вершин'''
    n = len(graph)
    return comb.combination(n, k)

def test_count_subgraphs_of_size_k():
    test_graph = {1: [2, 3], 2: [1, 5, 4], 3: [1, 5], 4: [2], 5: [2, 3]}
    assert count_subgraphs_of_size_k(test_graph, len(test_graph) - 1) == len(test_graph)
    print("test_count_subgraphs_of_size_k complete!")


if __name__ == '__main__':
    example = {1: [2, 3], 2: [1, 5, 4], 3: [1, 5], 4: [2], 5: [2, 3]}
    test_count_subgraphs_of_size_k()
    print(count_subgraphs_of_size_k(example, 2))