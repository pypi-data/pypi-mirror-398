def create_graph(): #создание графа
    graph = {}
    return graph


def add_vertex(graph, name):  # добавляем вершину
    if name not in graph:
        graph[name] = []


def add_edge(graph, v1, v2, weight=1):  # добавляем ребро
    add_vertex(graph, v1)
    add_vertex(graph, v2)
    graph[v1].append((v2, weight))  # ОШИБКА БЫЛА: было (v1, weight), должно быть (v2, weight)
    graph[v2].append((v1, weight))  # ОШИБКА БЫЛА: было (v2, weight), должно быть (v1, weight)


def create_from_list(edge_list):
    graph = {}
    for edge in edge_list:
        if len(edge) == 2:
            v1, v2 = edge
            add_edge(graph, v1, v2, 1)  # вес по умолчанию 1
        elif len(edge) == 3:
            v1, v2, w = edge
            add_edge(graph, v1, v2, w)  # с указанным весом
    return graph


def count_vertex(graph):
    return len(graph)


def count_edges(graph):
    c = 0
    for i in graph.values():  # проходим по вершинам
        c += len(i)  # считаем количество связей вершины
    return c // 2


def get_vertices(graph):
    return list(graph.keys())


def get_edges(graph):
    edges = []
    seen = set()
    for v1 in graph:
        for v2, weight in graph[v1]:
            key = tuple(sorted((v1, v2)))
            if key not in seen:
                edges.append((v1, v2, weight))
                seen.add(key)
    return edges


def smejnost_matrix(graph):  # создаем матрицу смежности
    vertices = sorted(graph.keys())
    vertex_index = {vertex: i for i, vertex in enumerate(vertices)}
    n = len(vertices)
    matrix = [[0] * n for _ in range(n)]
    for vertex in vertices:  # веса ребер в матрицу
        i = vertex_index[vertex]  # номер строки для этой вершины
        # Проходим по всем соседям вершины
        for neighbor, weight in graph[vertex]:
            j = vertex_index[neighbor]  # номер столбца для соседа
            matrix[i][j] = weight
    return matrix, vertices


def print_smejnost_matrix(graph):  # вывод матрицы для пользователя
    matrix, vertices = smejnost_matrix(graph)
    print("матрица смежности")
    print("   ", end="")
    for num in vertices:
        print(num, end=" ")
    print("")
    for i in range(len(matrix)):  # по строкам матрицы
        print(vertices[i] + ":", end=" ")  # имя вершины
        row = matrix[i]  # текущая строка
        for j in range(len(row)):  # по столбцам
            print(row[j], end=" ")  # элемент матрицы
        print()


def print_edges(graph):
    print("Рёбра графа:")
    for vertex in graph:
        # Для каждой вершины смотрим её соседей
        for neighbor, weight in graph[vertex]:
            # Чтобы не выводить ребро дважды, печатаем только если vertex < neighbor
            if vertex < neighbor:
                print(f"{vertex} — {neighbor} (вес: {weight})")
