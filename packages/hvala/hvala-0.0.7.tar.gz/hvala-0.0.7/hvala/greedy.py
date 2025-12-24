import networkx as nx

def min_weighted_dominating_set_max_degree_1(G, weight = 'weight'):
    """
    Find the minimum weighted dominating set for a graph with maximum degree 1.
    
    In such graphs, each connected component is either:
    - An isolated vertex (degree 0): must be in the dominating set
    - An edge (two vertices of degree 1): choose the one with minimum weight
    
    Args:
        G: NetworkX undirected graph with maximum degree 1
        weight: Name of the weight attribute (default: 'weight')
        
    Returns:
        Set of vertices forming the minimum weighted dominating set
        
    Raises:
        ValueError: If the graph has a vertex with degree > 1
    """
    # Verify maximum degree constraint
    max_degree = max(dict(G.degree()).values()) if G.nodes() else 0
    if max_degree > 1:
        raise ValueError(f"Graph has maximum degree {max_degree}, expected ≤ 1")
    
    dominating_set = set()
    visited = set()
    
    for node in G.nodes():
        if node in visited:
            continue
            
        degree = G.degree(node)
        
        if degree == 0:
            # Isolated vertex - must dominate itself
            dominating_set.add(node)
            visited.add(node)
            
        elif degree == 1:
            # Part of an edge - choose the vertex with minimum weight
            neighbor = list(G.neighbors(node))[0]
            
            if neighbor not in visited:
                # Get weights (default to 1 if not specified)
                node_weight = G.nodes[node].get(weight, 1)
                neighbor_weight = G.nodes[neighbor].get(weight, 1)
                
                # Choose the vertex with minimum weight
                # In case of tie, choose lexicographically smaller (for determinism)
                if (node_weight < neighbor_weight or 
                    (node_weight == neighbor_weight and node < neighbor)):
                    dominating_set.add(node)
                else:
                    dominating_set.add(neighbor)
                
                visited.add(node)
                visited.add(neighbor)
    
    return dominating_set

def min_weighted_vertex_cover_max_degree_1(G, weight = 'weight'):
    """
    Find the minimum weighted vertex cover for a graph with maximum degree 1.
   
    In such graphs, each connected component is either:
    - An isolated vertex (degree 0): not needed in vertex cover (no edges to cover)
    - An edge (two vertices of degree 1): choose the one with minimum weight
   
    Args:
        G: NetworkX undirected graph with maximum degree 1
        weight: Name of the weight attribute (default: 'weight')
       
    Returns:
        Set of vertices forming the minimum weighted vertex cover
       
    Raises:
        ValueError: If the graph has a vertex with degree > 1
    """
    # Verify maximum degree constraint
    max_degree = max(dict(G.degree()).values()) if G.nodes() else 0
    if max_degree > 1:
        raise ValueError(f"Graph has maximum degree {max_degree}, expected ≤ 1")
   
    vertex_cover = set()
    visited = set()
   
    for node in G.nodes():
        if node in visited:
            continue
           
        degree = G.degree(node)
       
        if degree == 0:
            # Isolated vertex - no edges to cover, skip
            visited.add(node)
           
        elif degree == 1:
            # Part of an edge - choose the vertex with minimum weight
            neighbor = list(G.neighbors(node))[0]
           
            if neighbor not in visited:
                # Get weights (default to 1 if not specified)
                node_weight = G.nodes[node].get(weight, 1)
                neighbor_weight = G.nodes[neighbor].get(weight, 1)
               
                # Choose the vertex with minimum weight
                # In case of tie, choose lexicographically smaller (for determinism)
                if (node_weight < neighbor_weight or
                    (node_weight == neighbor_weight and node < neighbor)):
                    vertex_cover.add(node)
                else:
                    vertex_cover.add(neighbor)
               
                visited.add(node)
                visited.add(neighbor)
   
    return vertex_cover