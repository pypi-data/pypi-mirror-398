from graph_basics import create_graph, add_edge, count_vertex, count_edges, print_edges
from algorithms import prim_algorithm, kruskal_algorithm, dijkstra_algorithm
from algorithms import show_prim_result, show_kruskal_result, show_dijkstra_result
def main():
    print("Программа алгоритмов графы")
    print()
    # Создаём граф
    g = create_graph()
    # Добавляем рёбра
    add_edge(g, "A", "B", 4)
    add_edge(g, "A", "C", 2)
    add_edge(g, "B", "C", 1)
    add_edge(g, "B", "D", 5)
    add_edge(g, "C", "D", 8)
    add_edge(g, "D", "E", 3)
    print(f"Граф создан: {count_vertex(g)} вершин, {count_edges(g)} рёбер")
    print()
    print_edges(g)
    print()
    # Алгоритм Прима
    prim_edges = prim_algorithm(g)
    show_prim_result(prim_edges)

    # Алгоритм Краскала
    kruskal_edges = kruskal_algorithm(g)
    show_kruskal_result(kruskal_edges)

    # Алгоритм Дейкстры
    distances, previous = dijkstra_algorithm(g, "A")
    show_dijkstra_result(distances, previous, "A")

    print("Программа завершена")


if __name__ == "__main__":
    main()
