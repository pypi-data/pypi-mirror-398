import heapq
def deykstra(graph, start, end):
    # в алгоритме обычно используется бессконечность, я использовал просто очень большое число
    inf = 10**10

    # создаём множество вершин, расстояние до каждой равно inf
    distances = {v: inf for v in graph}
    # обнуляем нашу начальную вершину
    distances[start] = 0
    # создаём множество для родительских вершин (чтоб можно было восстановить путь)
    parent = {}
    # создаём очередь
    priority_queue = [(0,start)]
    while priority_queue:
        current_distance, current_vertex = heapq.heappop(priority_queue)
        
        if current_vertex == end:
            break

        if current_distance > distances[current_vertex]:
            continue

        for neighbor, weight in graph[current_vertex].items():
            new_distance = current_distance + weight
            # если есть дистанция короче, меняем на неё
            if new_distance < distances[neighbor]:
                distances[neighbor] = new_distance
                parent[neighbor] = current_vertex
                heapq.heappush(priority_queue, (new_distance, neighbor))
    
    # здесь начинается процесс восстановления пути
    path = []
    current_vertex = end
    while current_vertex != start:
        path.append(current_vertex)
        current_vertex = parent.get(current_vertex)
    path.append(start)
    path.reverse()

    return path, distances[end]