def all_routes(graph, start, end, route=None): 
    '''Находит все пути из вершины start в вершину end'''
    if route is None:
        route = [start]
    else:
        route = route + [start]

    if start == end:
        return [route]

    routes = []
    for neighbor in graph[start]:
        if neighbor not in route:  # избегаем циклов
            new_paths = all_routes(graph, neighbor, end, route)
            for p in new_paths:
                routes.append(p)
    return routes

if __name__ == '__main__':
    example = {1: [2, 3], 2: [1, 5, 4], 3: [1, 5], 4: [2], 5: [2, 3]}
    print(all_routes(example, 3, 4))