"""SPHARA filter

This module provides a class to perform a spatial filtering using a
SPHARA basis. The class is derived from
:class:`spharapy.spharabasis.SpharaBasis`. It provides methodes to
design different types of filters and to apply this filters to
spatially irregularly sampled data.

"""

from typing import cast

import numpy as np
from numpy.typing import ArrayLike, NDArray

from spharapy.spharabasis import SpharaBasis

FloatArray = NDArray[np.floating]

class SpharaFilter(SpharaBasis):
    """SPHARA filter class

    This class is used to design different types of filters and to
    apply this filters to spatially irregularly sampled data.

    Parameters
    ----------
    triangsamples : trimesh object
        A trimesh object from the package spharapy in which the triangulation
        of the spatial arrangement of the sampling points is stored. The SPHARA
        basic functions are determined for this triangulation of the sample
        points.
    mode : {'unit', 'inv_euclidean', 'fem'}, optional
        The discretisation method used to estimate the Laplace-Beltrami
        operator. Using the option 'unit' all edges of
        the mesh are weighted by unit weighting function. The option
        'inv_euclidean' results in edge weights corresponding to the
        inverse Euclidean distance of the edge lengths. The option
        'fem' uses a FEM discretisation. The default weighting
        function is 'fem'.
    specification : integer or array, shape (1, n_points)
        If an integer value for specification is passed to the
        constructor, it must be within the interval (-n_points,
        n_points), where n_points is the number of spatial sample
        points. If a positive integer value is passed, a spatial
        low-pass filter with the corresponding number of SPHARA basis
        functions is created, if a negative integer value is passed, a
        spatial low-pass filter is created. If a vector is passed,
        then all SPHARA basis functions corresponding to nonzero
        elements of the vector are used to create the filter. The
        default value of specification is 0, it means a neutral
        all-pass filter is designed and applied.

    """

    def __init__(self, triangsamples=None, mode="fem", specification=0):
        SpharaBasis.__init__(self, triangsamples, mode)
        # internal fields
        self._basis = None
        self._frequencies = None
        self._massmatrix = None
        self._filtermatrix = None

        # default all-pass (ensures not-None even if someone bypasses the setter)
        n = self._triangsamples.vertlist.shape[0]
        self._specification = np.ones(n, dtype=float)

        # now apply the user-provided spec (calls the setter above)
        self.specification = specification

    @property
    def specification(self):
        """Get or set the specification of the filter.

        The parameter `specification` has to be an integer or a vector.
        Setting the `specification` will simultaneously apply a plausibility
        check.

        """

        return self._specification

    @specification.setter
    def specification(self, specification) -> None:
        n = self._triangsamples.vertlist.shape[0]

        if isinstance(specification, int):
            if abs(specification) > n:
                raise ValueError("The number of selected basis functions is too large.")
            if specification == 0:
                self._specification = np.ones(n, dtype=float)
            else:
                v = np.zeros(n, dtype=float)
                if specification > 0:
                    v[:specification] = 1.0
                else:
                    v[specification:] = 1.0
                self._specification = v

        elif isinstance(specification, (list, tuple, np.ndarray)):
            arr = np.asarray(specification, dtype=float)
            if arr.shape[0] != n:
                raise IndexError(
                    "The length of the specification vector does not match "
                    "the number of spatial sample points."
                )
            self._specification = arr

        else:
            raise TypeError("The parameter specification has to be int or a vector.")

    def _ensure_ready(self) -> None:
        # compute basis lazily if needed
        if self._basis is None or self._frequencies is None:
            self.basis()
        if self._basis is None:
            raise RuntimeError("SPHARA basis not initialized; call basis() first.")
        if self._mode == "fem" and self._massmatrix is None:
            raise RuntimeError("Mass matrix not initialized for FEM mode.")
        if self._specification is None:
            raise RuntimeError("Filter specification (transfer vector) not set.")

    def filter(self, data: ArrayLike) -> FloatArray:
        r"""Perform the SPHARA filtering

        This method performs the spatial SPHARA filtering
        for data defined at spatially distributed sampling points
        described by a triangular mesh. The filtering is
        performed by matrix multiplication of the data matrix and a
        precalculated filter matrix.

        Parameters
        ----------
        data : array, shape(m, n_points)
            A matrix with data to be filtered by spatial SPHARA
            filter. The number of vertices of the triangular mesh is
            n_points. The order of the spatial sample points must
            correspond to that in the vertex list used to determine
            the SPHARA basis functions.

        Returns
        -------
        data_filtered : array, shape (m, n_points)
            A matrix containing the filtered data.

        Examples
        --------

        >>> import numpy as np
        >>> from spharapy import trimesh as tm
        >>> from spharapy import spharafilter as sf
        >>> # define the simple test mesh
        >>> testtrimesh = tm.TriMesh([[0, 1, 2]], [[1., 0., 0.], [0., 2., 0.],
        ...                                        [0., 0., 3.]])
        >>> # create a spatial lowpass filter, FEM discretisation
        >>> sf_fem = sf.SpharaFilter(testtrimesh, mode='fem',
        ...                          specification=[1., 1., 0.])
        >>> # create some test data
        >>> data = np.concatenate([[[0., 0., 0.], [1., 1., 1.]],
        ...                          np.transpose(sf_fem.basis()[0])])
        >>> data
        array([[ 0.        ,  0.        ,  0.        ],
               [ 1.        ,  1.        ,  1.        ],
               [ 0.53452248,  0.53452248,  0.53452248],
               [-0.49487166, -0.98974332,  1.48461498],
               [ 1.42857143, -1.14285714, -0.28571429]])
        >>> # filter the test data
        >>> data_filtered = sf_fem.filter(data)
        >>> data_filtered
        array([[  0.00000000e+00,   0.00000000e+00,   0.00000000e+00],
               [  1.00000000e+00,   1.00000000e+00,   1.00000000e+00],
               [  5.34522484e-01,   5.34522484e-01,   5.34522484e-01],
               [ -4.94871659e-01,  -9.89743319e-01,   1.48461498e+00],
               [ -1.69271249e-16,  -2.75762028e-16,   3.10220481e-16]])

        """
        # Guarantee state
        self._ensure_ready()

        # Local, non-None aliases (help mypy)
        basis: FloatArray = cast(FloatArray, np.asarray(self._basis, dtype=float))
        H: FloatArray = cast(FloatArray, np.asarray(self._specification, dtype=float))
        M: FloatArray | None = (
            None
            if self._massmatrix is None
            else cast(FloatArray, np.asarray(self._massmatrix, dtype=float))
        )

        # Build filter matrix once (use broadcasting instead of np.diag for speed)
        if self._filtermatrix is None:
            basis_fun_sel: FloatArray = basis * H  # scales columns of basis
            if self._mode == "fem" and M is not None:
                self._filtermatrix = M @ basis_fun_sel @ basis_fun_sel.T
            else:
                self._filtermatrix = basis_fun_sel @ basis_fun_sel.T

        F: FloatArray = cast(FloatArray, self._filtermatrix)

        Xa: FloatArray = cast(FloatArray, np.asarray(data, dtype=float))
        squeezed = False
        if Xa.ndim == 1:
            Xa = Xa[None, :]
            squeezed = True

        # Dimension check before multiply
        if basis.shape[0] != Xa.shape[1]:
            raise ValueError(
                f"Dimension mismatch: data has {Xa.shape[1]} vertices, basis expects {basis.shape[0]}."
            )

        data_filtered: FloatArray = Xa @ F
        if squeezed:
            data_filtered = cast(FloatArray, data_filtered[0])
        return data_filtered

def spectral_grid(self) -> FloatArray:
    """Return the SPHARA spectral grid used by this filter.

    This is equivalent to
    :meth:`~spharapy.spharabasis.SpharaBasis.eigenvalues` and can be
    used together with the transfer-function helpers in
    :mod:`spharapy.spectral_filters`.

    Returns
    -------
    numpy.ndarray
        Eigenvalues :math:`τ_i` associated with the SPHARA basis.

    """
    return self.eigenvalues()
    
