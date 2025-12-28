from combigraphs.combfuncs import place

def count_routes_of_lenght_k_infull_graph(n, k):
    """Подсчет числа путей длины k между двумя фиксированными вершинами в полном графе."""
    if k == 1:
        return 1
    if k > n - 1:
        return 0
    return place.placement(n - 2, k - 1)  # n-2 потому что первая и последняя зафиксированы, k - 1, между зафиксироваными всего k - 1 вершин.

def test_count_routes_of_lenght_k_infull_graph():
    assert count_routes_of_lenght_k_infull_graph(5, 3)
    print("test_count_routes_of_lenght_k_infull_graph complete!")
    
if __name__ == '__main__':
    test_count_routes_of_lenght_k_infull_graph()
    print(count_routes_of_lenght_k_infull_graph(6, 2))