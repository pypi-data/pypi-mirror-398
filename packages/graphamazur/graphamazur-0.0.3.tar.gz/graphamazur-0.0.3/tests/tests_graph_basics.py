from src.graphamazur.graph_basics import *


def test_graph_create():
    g = create_graph()
    assert isinstance(g, dict)
    assert len(g) == 0
    print("Test graph_create complete\n")


def test_add_vertex():
    g = create_graph()
    add_vertex(g, 'A')
    add_vertex(g, 'B')
    add_vertex(g, 'C')
    assert 'A' in g
    assert 'B' in g
    assert 'C' in g
    assert len(g) == 3
    print("Test add_vertex complete\n")


def test_add_edge():
    g = create_graph()
    add_edge(g, 'A', 'B', 5)
    add_edge(g, 'B', 'C', 3)
    assert ('B', 5) in g['A']
    assert ('A', 5) in g['B']
    assert ('C', 3) in g['B']
    assert ('B', 3) in g['C']
    print("Test add_edge complete\n")


def test_create_from_list():
    edges = [('A', 'B', 2), ('B', 'C', 3), ('A', 'C', 4)]
    g = create_from_list(edges)
    assert len(g) == 3
    assert count_edges(g) == 3
    print("Test create_from_list complete\n")


def test_count_functions():
    edges = [('A', 'B'), ('B', 'C'), ('C', 'D')]
    g = create_from_list(edges)
    assert count_vertex(g) == 4
    assert count_edges(g) == 3
    print("Test count_functions complete\n")


def test_get_vertices_edges():
    edges = [('A', 'B', 2), ('B', 'C', 3)]
    g = create_from_list(edges)
    vertices = get_vertices(g)
    edges_list = get_edges(g)
    assert set(vertices) == {'A', 'B', 'C'}
    assert len(edges_list) == 2
    print("Test get_vertices_edges complete\n")


def test_matrix():
    edges = [('A', 'B', 2), ('B', 'C', 3)]
    g = create_from_list(edges)
    matrix, vertices = smejnost_matrix(g)
    print("Test matrix complete\n")


def test_basics_all():
    tests = [
        test_graph_create,
        test_add_vertex,
        test_add_edge,
        test_create_from_list,
        test_count_functions,
        test_get_vertices_edges,
        test_matrix
    ]

    for test in tests:
        try:
            test()
        except AssertionError as e:
            print(f"✗ {test.__name__} FAILED: {e}")
            return False
        except Exception as e:
            print(f"✗ {test.__name__} ERROR: {e}")
            return False
    return True


if __name__ == "__main__":
    test_graph_create()
    test_add_vertex()
    test_add_edge()
    test_create_from_list()
    test_count_functions()
    test_get_vertices_edges()
    test_matrix()