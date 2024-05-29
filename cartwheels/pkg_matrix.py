# Cartwheels  Copyright (C) 2024  Alwyn Aswin

from typing import Tuple, Iterator, List

import numpy as np

from cartwheels.chart_pkgs import ChartPackages


class PkgMatrix:
    """
    Used to group and reduce the complexity of the sparse graph
    """

    def __init__(self, chart: ChartPackages):
        self._chart = chart
        self._adj = np.array(chart.adj)

    @property
    def A(self) -> np.ndarray:
        """
        Returns the adjacency matrix
        :return: a numpy array that describes the connection between nodes
        """
        return self._adj

    @property
    def D(self) -> np.ndarray:
        """
        Returns the degree matrix. The sum of the columns tell us how many connectivity.
        :return: A numpy array that describes how many connection are directly using the package
        """
        return np.diag(np.sum(self.A, 0))

    @property
    def L(self) -> np.ndarray:
        """
        Returns the laplacian matrix of the array
        :return: Returns ndarray
        """
        return self.D - self.A

    @property
    def Es(self) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        """
        Returns the *pre-sorted* eigen values and vectors
        """
        val, vec = np.linalg.eig(self.L)
        return val[np.argsort(val)], vec[:, np.argsort(val)], np.argsort(val)

    def shrink_A(self, preserve_list: List[str]) -> None:
        """
        Shrinks the adjacency matrix and remove un-referenced entries.
        :return:
        """
        # These
        may_be_nots = np.argwhere(np.all(self.A[..., :] == 0, axis=0)).ravel().tolist()
        nots = [i for i in may_be_nots if not any(map(lambda j: self._chart.vertices[i].startswith(j), preserve_list))]
        self._adj = np.delete(self.A, nots, axis=0)
        self._adj = np.delete(self.A, nots, axis=1)

    @property
    def Cs(self) -> Iterator[np.ndarray]:
        """
        Returns the full connectivity matrices at each number of hops
        :return: The connectivity matrix n-hop away.
        """
        yield self.A
        a_sum = np.zeros(self.A.shape)
        a = self.A
        a_prime = np.matmul(a, self.A)
        while np.any(a_prime):
            a_sum = a_prime + a_sum
            yield a_sum
            a = a_prime
            a_prime = np.matmul(a, self.A)
