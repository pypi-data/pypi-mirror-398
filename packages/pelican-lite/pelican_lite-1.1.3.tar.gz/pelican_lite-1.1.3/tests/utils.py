import torch

from pelican.utils import get_batch_from_ptr, get_edge_index_from_ptr


def generate_batch(G=8, N_min=10, N_max=20, C=16, batch=None, edge_index=None):
    """
    Generate random batch, edge_index, graph, nodes, and edges for testing,
    assuming a fully connected graph.

    Parameters
    ----------
    G : int
        Number of graphs in the batch.
    N_range : list
        Range of number of nodes per graph.
    C : int
        Number of channels (features) for graph, nodes, and edges.
    batch : torch.Tensor, optional
        Predefined batch tensor, by default None.
    edge_index : torch.Tensor, optional
        Predefined edge_index tensor, by default None.

    Returns
    -------
    batch : torch.Tensor
        Batch tensor of shape (N).
    edge_index : torch.Tensor
        Edge index tensor of shape (2, E).
    graph : torch.Tensor
        Graph-level features of shape (G, C).
    nodes : torch.Tensor
        Node-level features of shape (G, N).
    edges : torch.Tensor
        Edge-level features of shape (G, E).
    """
    if batch is None or edge_index is None:
        length = torch.randint(low=N_min, high=N_max, size=(G,))
        ptr = torch.zeros(G + 1, dtype=torch.long)
        ptr[1:] = torch.cumsum(length, dim=0)
        batch = get_batch_from_ptr(ptr)
        shape = torch.Size((batch.shape[0], C))
        edge_index = get_edge_index_from_ptr(ptr, shape, remove_self_loops=False)
    else:
        assert batch is not None and edge_index is not None
    graph = torch.randn(G, C) if C > 0 else None
    nodes = torch.randn(batch.numel(), C) if C > 0 else None
    edges = torch.randn(edge_index.size(1), C) if C > 0 else None
    return batch, edge_index, graph, nodes, edges


def permute_single_graph(edge_index, graph=None, nodes=None, edges=None, permutation=None):
    # this code assumes a single graph (G=1)
    N = edge_index.max().item() + 1
    if permutation is None:
        permutation = torch.randperm(N)

    permutation_inverse = torch.empty_like(permutation)
    permutation_inverse[permutation] = torch.arange(N)
    edge_index_perm = permutation_inverse[edge_index]
    key = edge_index_perm[0] * N + edge_index_perm[1]
    order = key.argsort()

    graph_perm = graph if graph is not None else None
    nodes_perm = nodes[permutation] if nodes is not None else None
    edges_perm = edges[order] if edges is not None else None
    return permutation, graph_perm, nodes_perm, edges_perm, edge_index_perm[:, order]
