from src.graphamazur.graph_basics import *

def prim_algorithm(graph):
    if not graph:
        return []

    start_vertex = list(graph.keys())[0]
    visited = {start_vertex}
    mst_edges = []

    while len(visited) < len(graph):
        min_edge = None
        min_weight = float('inf')

        for v in visited:
            for neighbor, weight in graph[v]:
                if neighbor not in visited and weight < min_weight:
                    min_weight = weight
                    min_edge = (v, neighbor, weight)

        if min_edge:
            v1, v2, weight = min_edge
            mst_edges.append((v1, v2, weight))
            visited.add(v2)

    return mst_edges

def kruskal_algorithm(graph):
    edges = get_edges(graph)

    edges.sort(key=lambda x: x[2])
    vertices = list(graph.keys())
    parent = {v: v for v in vertices}
    rank = {v: 0 for v in vertices}

    def find(parent, vertex):
        if parent[vertex] != vertex:
            parent[vertex] = find(parent, parent[vertex])
        return parent[vertex]
    def union(parent, rank, v1, v2):
        root1 = find(parent, v1)
        root2 = find(parent, v2)
        if root1 != root2:
            if rank[root1] > rank[root2]:
                parent[root2] = root1
            elif rank[root1] < rank[root2]:
                parent[root1] = root2
            else:
                parent[root2] = root1
                rank[root1] += 1
    mst_edges = []
    for edge in edges:
        v1, v2, weight = edge
        if find(parent, v1) != find(parent, v2):
            union(parent, rank, v1, v2)
            mst_edges.append((v1, v2, weight))
        if len(mst_edges) == len(vertices) - 1:
            break
    return mst_edges


def dijkstra_algorithm(graph, start_vertex):
    if start_vertex not in graph:
        print(f"Ошибка: вершины {start_vertex} нет в графе")
        return {}, {}
    distances = {vertex: float('inf') for vertex in graph}
    previous = {vertex: None for vertex in graph}
    distances[start_vertex] = 0
    unvisited = set(graph.keys())
    while unvisited:
        current = None
        min_dist = float('inf')
        for vertex in unvisited:
            if distances[vertex] < min_dist:
                min_dist = distances[vertex]
                current = vertex

        if current is None:
            break
        unvisited.remove(current)
        for neighbor, weight in graph[current]:
            new_distance = distances[current] + weight

            if new_distance < distances[neighbor]:
                distances[neighbor] = new_distance
                previous[neighbor] = current

    return distances, previous


# ========== ПРОСТОЙ ВЫВОД РЕЗУЛЬТАТОВ ==========

def show_prim_result(edges):
    print("Результат алгоритма Прима:")
    if not edges:
        print("  Пусто")
        return
    total = 0
    for v1, v2, w in edges:
        print(f"  {v1} - {v2} (вес {w})")
        total += w
    print(f"Всего рёбер: {len(edges)}")
    print(f"Общий вес: {total}")
    print()

def show_kruskal_result(edges):
    print("Результат алгоритма Краскала:")
    if not edges:
        print("  Пусто")
        return
    total = 0
    for v1, v2, w in edges:
        print(f"  {v1} - {v2} (вес {w})")
        total += w
    print(f"Всего рёбер: {len(edges)}")
    print(f"Общий вес: {total}")
    print()


def show_dijkstra_result(distances, previous, start):
    print(f"Результат алгоритма Дейкстры из вершины {start}:")
    for vertex in distances:
        dist = distances[vertex]
        if dist == float('inf'):
            print(f"  До {vertex}: нет пути")
        else:
            path = []
            current = vertex
            while current is not None:
                path.append(current)
                current = previous[current]
            path.reverse()
            path_str = " -> ".join(path)
            print(f"  До {vertex}: расстояние {dist}, путь: {path_str}")
    print()
