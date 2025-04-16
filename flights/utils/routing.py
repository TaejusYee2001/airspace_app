import heapq
from collections import defaultdict

def a_star_routing(start, goal, graph, airports_data):
    def heuristic(a_code, b_code):
        # Euclidean distance as heuristic
        ax, ay = airports_data[a_code]['latitude'], airports_data[a_code]['longitude']
        bx, by = airports_data[b_code]['latitude'], airports_data[b_code]['longitude']
        return ((ax - bx) ** 2 + (ay - by) ** 2) ** 0.5
    
    frontier = [(0, start, [])]  # (priority, current_airport, path_so_far)
    visited = set()
    
    while frontier:
        cost, current, path = heapq.heappop(frontier)
        
        if current in visited:
            continue
        visited.add(current)
        
        path = path + [current]
        
        if current == goal:
            return path
        
        for neighbor, dist in graph[current]:
            if neighbor not in visited:
                priority = cost + dist + heuristic(neighbor, goal)
                heapq.heappush(frontier, (priority, neighbor, path))
    
    return None  # No path found   