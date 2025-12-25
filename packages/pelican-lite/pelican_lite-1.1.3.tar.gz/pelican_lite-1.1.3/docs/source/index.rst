PELICAN-lite documentation
==========================

This is an efficient reimplementation of the PELICAN architecture.
PELICAN was first published at the `ML4PS workshop 2022 <https://arxiv.org/abs/2211.00454>`_ and on `JHEP <https://arxiv.org/abs/2307.16506>`_.
The official implementation is available on https://github.com/abogatskiy/PELICAN.

This implementation aims to improve efficiency and ease of use.
For toptagging with batch size 100, we find 8x reduced memory usage and a 3x training speedup compared to the original implementation.
PELICAN-lite can be used as the Frames-Net in `Lorentz Local Canonicalization (LLoCa) <https://github.com/heidelberg-hepml/lloca>`_.

* :doc:`quickstart`
* :doc:`differences`
* :doc:`api`

Citation
--------

If you find this package useful, please cite these papers:

.. code-block:: bib

   @article{Favaro:2025pgz,
      author = "Favaro, Luigi and Gerhartz, Gerrit and Hamprecht, Fred A. and Lippmann, Peter and Pitz, Sebastian and Plehn, Tilman and Qu, Huilin and Spinner, Jonas",
      title = "{Lorentz-Equivariance without Limitations}",
      eprint = "2508.14898",
      archivePrefix = "arXiv",
      primaryClass = "hep-ph",
      month = "8",
      year = "2025"
   }
   @article{Bogatskiy:2023nnw,
      author = "Bogatskiy, Alexander and Hoffman, Timothy and Miller, David W. and Offermann, Jan T. and Liu, Xiaoyang",
      title = "{Explainable equivariant neural networks for particle physics: PELICAN}",
      eprint = "2307.16506",
      archivePrefix = "arXiv",
      primaryClass = "hep-ph",
      doi = "10.1007/JHEP03(2024)113",
      journal = "JHEP",
      volume = "03",
      pages = "113",
      year = "2024"
   }
   @article{Bogatskiy:2022czk,
      author = "Bogatskiy, Alexander and Hoffman, Timothy and Miller, David W. and Offermann, Jan T.",
      title = "{PELICAN: Permutation Equivariant and Lorentz Invariant or Covariant Aggregator Network for Particle Physics}",
      eprint = "2211.00454",
      archivePrefix = "arXiv",
      primaryClass = "hep-ph",
      month = "11",
      year = "2022"
   }

.. toctree::
   :maxdepth: 1
   :caption: Usage
   :hidden:
   :titlesonly:

   quickstart
   differences

.. toctree::
   :maxdepth: 2
   :caption: Reference
   :hidden:

   api
