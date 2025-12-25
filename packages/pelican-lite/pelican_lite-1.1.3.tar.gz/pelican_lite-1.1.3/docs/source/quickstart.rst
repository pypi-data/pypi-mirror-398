Quickstart
==========


Installation
------------

Before using the package, install it via pip:

.. code-block:: bash

   pip install pelican-lite

Alternatively, if you're developing locally:

.. code-block:: bash

   git clone https://github.com/heidelberg-hepml/pelican-lite.git
   cd pelican
   pip install -e .
   pip install -r requirements.txt
   pre-commit install

0. Generate particle data
-------------------------

We start by generating toy particle data, for instance for an amplitude regression task.
We describe particles by a four-momentum and one scalar feature, for instance the particle type.
Using random numbers, we generate a batch of 128 events with 10 particles each.

.. code-block:: python

   import torch
   num_scalars = 1
   B, N = 128, 10
   mass = 1
   p3 = torch.randn(B, N, 3)
   E = (mass**2 + (p3**2).sum(dim=-1, keepdims=True)).sqrt()
   fourmomenta = torch.cat([E, p3], dim=-1) # (128, 10, 4)
   scalars = torch.randn(B, N, num_scalars) # (128, 10, 1)

1. Represent particle data as a sparse tensor
---------------------------------------------

At the core of this PELICAN implementation is the representation of sparse tensors.
Instead of relying on zero-padding, this approach flattens the batch and node dimensions into a common node-across-batch dimension.
The ``ptr`` or ``batch`` objects carry the information of which batch a node belongs to.
In addition the ``edge_index`` allows us to operate on arbitrary graphs, instead of only fully connected graphs.
Note that no zero-padding is required for the toy data that we are using in this demo.

.. code-block:: python

    from pelican.utils import get_batch_from_ptr, get_edge_index_from_ptr, get_edge_index_from_shape

    scalars_sparse = scalars.flatten(end_dim=-2)
    fourmomenta_sparse = fourmomenta.flatten(end_dim=-2)
    print(scalars_sparse.shape, fourmomenta_sparse.shape) # (1280, 1) (1280, 4)

    # approach 1 (assumes dense tensors)
    edge_index, batch = get_edge_index_from_shape(fourmomenta.shape, remove_self_loops=False)
    print(edge_index.shape, batch.shape) # (2, 12800) (1280,)

    # approach 2 (start from generic ptr)
    ptr = torch.arange(B+1) * N
    batch_2 = get_batch_from_ptr(ptr)
    edge_index_2 = get_edge_index_from_ptr(ptr, fourmomenta_sparse.shape, remove_self_loops=False)

    # consistency checks
    assert torch.all(batch == batch_2)
    assert torch.all(edge_index == edge_index_2)

2. Organize PELICAN inputs into ranks
-------------------------------------

PELICAN assumes Lorentz-invariant inputs and processes them with permutation-equivariant operations.
To this end, the inputs to the architecture have to be organized by their transformation behaviour under permutations.
There is graph-level information (rank 0), node-level information (rank 1), and edge-level information (rank 2).
Extending this framework to higher-order representations is straight-forward,
however those are expected to be less relevant in high-energy physics applications.

In our case, we first have the particle-wise scalar information as rank 1 inputs.
To turn the Lorentz vectors :math:`p_i^\mu` into Lorentz-invariants,
we can take their inner products :math:`p_i^\mu p_{j,\mu}`, or equivalently :math:`(p_i+p_j)^\mu (p_i+p_j)_\mu`, as rank 2 or edge-level information.
Note that the particle masses :math:`m_i^2 = p_i^\mu p_{i,\mu}` are node-level invariants, but emerge from the set of rank 2 objects.
There are no rank 0 objects in this example, but they are also supported in the PELICAN architecture.

.. code-block:: python

    from pelican.utils import get_edge_attr

    in_rank1 = scalars_sparse
    in_rank2 = get_edge_attr(fourmomenta_sparse, edge_index).unsqueeze(-1)
    print(in_rank1.shape, in_rank2.shape) # (1280, 1) (12800, 1)

3. Process inputs with PELICAN network
--------------------------------------

We are now ready to process our data with a PELICAN network.
It first projects all input data into rank 2 representations, processes them in that representation,
and finally maps them back to outputs of rank 0, 1, or 2.

.. code-block:: python

    from pelican.nets import PELICAN

    for out_rank in range(3):
        net = PELICAN(
            in_channels_rank2=1,
            in_channels_rank1=num_scalars,
            in_channels_rank0=0,
            out_rank=out_rank,
            out_channels=1,
            num_blocks=2,
            hidden_channels=16,
        )
        out = net(edge_index, batch, in_rank2=in_rank2, in_rank1=in_rank1)
        print(out_rank, out.shape) # (0, (128, 1)) (1, (1280, 1)) (2, (12800, 1))
