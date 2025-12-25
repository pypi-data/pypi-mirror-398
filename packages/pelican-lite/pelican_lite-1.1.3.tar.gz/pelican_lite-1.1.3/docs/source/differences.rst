Differences compared to the original PELICAN implementation
===========================================================

We summarize the key differences and design choices that went into this implementation,
compared to the original PELICAN implementation available on https://github.com/abogatskiy/PELICAN.

Efficiency improvements
-----------------------

- Sparse tensors: For batches that contain graphs with different node counts,
  the original PELICAN implementation uses zero-padding to create dense tensors,
  i.e. rectangular objects of shape (B, Nmax, C) for batch size B, C channels,
  and Nmax the maximum node count of a graph in the full batch.
  Even though they do not contribute to the final result, all operations have to
  be performed also on the padded entries, which becomes costly espacially at large
  batch sizes. In this implementation, we avoid zero-padding and instead use sparse
  tensors, which have shape (Nbatch, C) with Nbatch the total number of nodes in the
  batch, summing over the nodes of all graphs. To keep track of which nodes belong to
  which graph, we use a ``batch`` vector of shape (Nbatch,) that contains the graph
  index of each node. Alternatively, one can use a ``ptr`` vector of shape (B+1,)
  that contains the indices where the first, second etc graph starts in the sparse tensor.
  Following the PyTorch Geometric convention, we also support a ``edge_index`` tensor
  that contains the list of edges in the graph. To estimate the memory savings from using
  sparse tensors, consider a batch of B=100 jets with on average 50 particles per jet,
  but ranging up to Nmax=100. Using sparse tensors saves roughly a factor of 2 in memory
  when storing node tensors, and roughly a factor of 2*2=4 when storing edge tensors.
  Using the top-tagging dataset, we find a 8x reduced memory cost for batch size B=100.
- ``torch.compile``: The aggregations in PELICAN require many sequential operations. Fusing
  them into a single operation using ``torch.compile`` can therefore lead to significant speedups.
  We find this to be particularly important when using sparse tensors, where less high-level kernels are available.
  When training on the top-tagging dataset with B=1 using a H100 GPU, we find that our ``torch.compile``'d implementation
  is roughly 2x faster than the original PELICAN, whereas the non-``torch.compile``'d version is roughly 50% slower.
  Note that at B=1 our implementation does not benefit yet from the speedup from memory savings.
  Going to B=100, we find that our ``torch.compile``'d implementation is roughly 3x faster, whereas the
  non-``torch.compile``'d version is roughly 20% slower than the original PELICAN.

Design choices
--------------

- We use RMSNorm instead of BatchNorm. This is because BatchNorm can lead to instabilities
  when the batch size is small, or when the node count per graph varies strongly.
  RMSNorm is a simpler normalization that does not depend on the batch statistics.
- The official PELICAN implementation supports a range of additional options, e.g. IRC safety,
  ``folklore``, ``skip_order_zero``. We do not support these options in this implementation
  to keep the code base simple and focused on the core architecture.
- Our implementation of channel-wise rescalings differs slightly from the original PELICAN.
  The official implementation rescales aggregation maps by :math:`1/N^\alpha`, where N
  is the number of nodes in the graph, and :math:`\alpha` is a learnable parameter.
  In our implementation, the scaling factor is learned directly.
