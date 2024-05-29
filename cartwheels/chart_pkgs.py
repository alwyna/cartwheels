# Cartwheels  Copyright (C) 2024  Alwyn Aswin

from typing import Dict, List, Tuple, Iterator

from cartwheels.pkg_nfo import PkgNfo


class ChartPackages:
    """Helper method to convert the pkg graph from object format to adj matrix."""

    def __init__(self, pkgs: Dict[str, PkgNfo]):
        self._pkgs = pkgs
        """Reverse index"""

        self._vertices: List[str] = sorted(pkgs.keys())
        self._vertices_r: Dict[str, int] = {self._vertices[i]: i for i in range(len(self._vertices))}
        self._edges_i: List[Tuple[int, int]] = []
        self._catalog_edges()
        self._adj: List[List[float]]
        self._create_adj_matrix()
        self._lplcn: List[List[float]]

    @property
    def vertices(self) -> List[str]:
        """
        Return the vertex names (as indexed list)
        :return:
        """
        return self._vertices

    @property
    def edges(self) -> List[Tuple[int, int]]:
        """
        Return the edges as tuples of integer between dependent and depended
        :return:
        """
        return self._edges_i

    @property
    def named_edges(self) -> Iterator[Tuple[str, str]]:
        """
        Return the edges as tuples of integer between dependent and depended
        :return:
        """
        for edge in self._edges_i:
            yield self._vertices[edge[0]], self._vertices[edge[1]]

    @property
    def vertex_lookup(self) -> Dict[str, int]:
        """A lookup aid from vertex name to its index"""
        return self._vertices_r

    def _catalog_edges(self) -> None:
        """
        Catalog the edges between 2 related dependencies
        :return:
        """
        for vertex in self._vertices:
            for pkg in self._pkgs[vertex].dependencies:
                if vertex in self._vertices_r and pkg.get_key() in self._vertices_r:
                    self._edges_i.append((self._vertices_r[vertex], self._vertices_r[pkg.get_key()]))

    def _create_adj_matrix(self) -> None:
        """
        Create the adjacency matrix by iterating through the edges.
        :return:
        """
        self._adj = [[0 for i in range(len(self._vertices))] for j in range(len(self._vertices))]
        for edge in self._edges_i:
            self._adj[edge[0]][edge[1]] = 1  # If cataloged to work, assume it works

    @property
    def adj(self) -> List[List[float]]:
        """Return the adjacency matrix"""
        return self._adj
