"""SPHARA basis functions

This module provides a class for determining SPHARA basis functions. Methods
are provided to determine basis functions using different discretization
schemes of the Laplace-Beltrami operator, as FEM, inverse euclidean and unit.
"""

from scipy import linalg

import numpy as np
from numpy.typing import NDArray

import spharapy.trimesh as tm

FloatArray = NDArray[np.floating]


class SpharaBasis:
    """SPHARA basis functions class

    This class can be used to determine SPHARA basis functions for spatially
    irregularly sampled functions whose topology is described by a triangular
    mesh.

    Parameters
    ----------
    triangsamples : trimesh object
        A trimesh object from the package spharapy in which the triangulation
        of the spatial arrangement of the sampling points is stored. The SPHARA
        basis functions are determined for this triangulation of the sample
        points.
    mode : {'unit', 'inv_euclidean', 'fem'}, optional
        The discretization method used to estimate the Laplace-Beltrami
        operator. Using the option 'unit' all edges of
        the mesh are weighted by unit weighting function. The option
        'inv_euclidean' results in edge weights corresponding to the
        inverse Euclidean distance of the edge lengths. The option
        'fem' uses a FEM discretization. The default weighting
        function is 'fem'.

    Attributes
    ----------
    triangsamples: trimesh object
        Triangulation of the spatial arrangement of the sampling points
    mode: {'unit', 'inv_euclidean', 'fem'}
        Discretization used to estimate the Laplace-Beltrami
        operator

    """

    def __init__(self, triangsamples=None, mode="fem"):
        self.triangsamples = triangsamples
        self.mode = mode
        self._basis = None
        self._frequencies = None
        self._massmatrix = None

    @property
    def triangsamples(self):
        """Get or set the triangsamples object.

        The parameter `triangsamples` has to be an instance of the
        class `spharapy.trimesh.TriMesh`. Setting the triangsamples
        object will simultaneously check the correct format.

        """

        return self._triangsamples

    @triangsamples.setter
    def triangsamples(self, triangsamples):
        if not isinstance(triangsamples, tm.TriMesh):
            raise TypeError("triangsamples is no instance of TriMesh")
        # pylint: disable=W0201
        self._triangsamples = triangsamples
        self._basis = None
        self._frequencies = None
        self._massmatrix = None

    @property
    def mode(self):
        """Get or set the discretization method.

        The discretization method used to estimate the Laplace-Beltrami
        operator, choosen from {'unit', 'inv_euclidean', 'fem'}. Setting
        the triangsamples object will simultaneously check the
        correct format.

        """

        return self._mode

    @mode.setter
    def mode(self, mode):
        # plausibility test of option 'mode'
        if mode not in ("unit", "inv_euclidean", "fem"):
            raise ValueError("Unrecognized mode '{mode}'")
        # pylint: disable=W0201
        self._mode = mode
        self._basis = None
        self._frequencies = None
        self._massmatrix = None

    def basis(self):
        r"""Return the SPHARA basis for the triangulated sample points

        This method determines a SPHARA basis for spatially distributed
        sampling points described by a triangular mesh. A discrete
        Laplace-Beltrami operator in matrix form is determined for the
        given triangular grid. The discretization method used to construct
        the Laplace-Beltrami operator is specified in the attribute
        :attr:`mode`.

        In the FEM case (``mode='fem'``), a generalized symmetric definite
        eigenproblem

        :math:`-\boldsymbol{S} \, \boldsymbol{\Phi} =
        \boldsymbol{\tau} \boldsymbol{B} \boldsymbol{\Phi}`

        is solved, where :math:`\boldsymbol{S}` is the stiffness
        matrix, :math:`\boldsymbol{B}` is the mass matrix,
        :math:`\boldsymbol{\Phi}` is the matrix of eigenvectors and
        :math:`\boldsymbol{\tau}` is a vector with the eigenvalues
        :math:`\tau_i \ge 0`. The columns of :math:`\boldsymbol{\Phi}`
        form the SPHARA basis functions. For coordinates given in
        metric units (e.g., metres), the eigenvalues :math:`\tau_i` act
        as squared spatial angular frequencies (squared wave numbers);
        spatial frequencies :math:`f_i` and wavelengths :math:`\lambda_i`
        follow from

        :math:`\sqrt{\tau_i} = 2 \pi f_i = 2 \pi / \lambda_i`.

        For the graph-based discretizations (``mode='unit'`` or
        ``'inv_euclidean'``), the eigenvalues still provide a meaningful
        ordering from smooth (low “frequency”) to highly oscillatory
        basis functions, but they do not have a direct metric
        interpretation in terms of physical distances.

        Returns
        -------
        basis : array, shape (n_points, n_points)
            Matrix which contains the SPHARA basis functions column by column.
            The number of vertices of the triangular mesh is ``n_points``.
        frequencies : array, shape (n_points,)
            Eigenvalues :math:`\tau_i` of the discrete Laplace-Beltrami operator
            (or of the generalized FEM eigenproblem). In FEM mode they can be
            interpreted as squared spatial angular frequencies
            (squared wave numbers).

        Examples
        --------

        >>> from spharapy import trimesh as tm
        >>> from spharapy import spharabasis as sb
        >>> testtrimesh = tm.TriMesh([[0, 1, 2]], [[1., 0., 0.], [0., 2., 0.],
        ...                                        [0., 0., 3.]])
        >>> sb_fem = sb.SpharaBasis(testtrimesh, mode='fem')
        >>> sb_fem.basis()
        (array([[ 0.53452248, -0.49487166,  1.42857143],
                [ 0.53452248, -0.98974332, -1.14285714],
                [ 0.53452248,  1.48461498, -0.28571429]]),
         array([  2.33627569e-16,   1.71428571e+00,   5.14285714e+00]))

        """

        # lazy evaluation, compute the basis at the first request and store
        # it until the triangular mesh or the discretization method is changed
        if self._basis is None or self._frequencies is None:
            if self.mode == "fem":
                self._massmatrix = self.triangsamples.massmatrix(mode="normal")
                stiffmatrix = self.triangsamples.stiffnessmatrix()
                self._frequencies, self._basis = linalg.eigh(-stiffmatrix, self._massmatrix)
                # self._basis =
            else:  # 'unit' and 'inv_euclidean' discretization
                laplacianmatrix = self.triangsamples.laplacianmatrix(mode=self.mode)
                self._frequencies, self._basis = linalg.eigh(laplacianmatrix)

        # return the SPHARA basis
        return self._basis, self._frequencies

    def massmatrix(self):
        """Return the massmatrix

        The method returns the mass matrix of the triangular mesh.

        """
        # lazy evaluation, compute the mass matrix at the first request and
        # store it until the triangular mesh or the discretization method
        # is changed
        if self._massmatrix is None:
            self._massmatrix = self.triangsamples.massmatrix(mode="normal")

        return self._massmatrix

    def eigenvalues(self) -> FloatArray:
        r"""Return eigenvalues of the discrete Laplace–Beltrami operator.

        This is a convenience wrapper around :meth:`basis` that returns only
        the eigenvalues associated with the SPHARA basis.

        Returns
        -------
        eigenvalues : numpy.ndarray of shape (n_points,)
            Eigenvalues :math:`\tau_i \ge 0` of the discrete Laplace–Beltrami
            operator (or of the generalized FEM eigenproblem in
            ``mode='fem'``), ordered from smallest (DC) to largest spatial
            variation.
        """
        _, freqs = self.basis()
        return np.asarray(freqs, dtype=float)

    def spatial_angular_frequencies(self) -> FloatArray:
        r"""Return spatial angular frequencies for FEM-based SPHARA basis.

        For FEM discretization (``mode='fem'``) and coordinates in a
        consistent metric unit (e.g., metres), the eigenvalues :math:`\tau_i`
        of the Laplace–Beltrami operator behave like squared spatial angular
        frequencies (squared wave numbers). This method returns

        .. math::
            \omega_i = \sqrt{\tau_i}.

        For non-FEM modes the eigenvalues do not have a direct metric
        interpretation. In this case a :class:`RuntimeError` is raised.

        Returns
        -------
        omega : numpy.ndarray of shape (n_points,)
            Spatial angular frequencies :math:`\omega_i = \sqrt{\tau_i}`.

        Raises
        ------
        RuntimeError
            If :attr:`mode` is not ``'fem'``.
        """
        if self.mode != "fem":
            raise RuntimeError(
                "spatial_angular_frequencies() is only defined for FEM "
                "discretization (mode='fem')."
            )
        tau = self.eigenvalues()
        return np.sqrt(np.maximum(tau, 0.0))

    def spatial_frequencies(self) -> FloatArray:
        r"""Return spatial frequencies for FEM-based SPHARA basis.

        For FEM discretization (``mode='fem'``), the spatial frequencies
        :math:`f_i` corresponding to the eigenvalues :math:`\tau_i` are given by

        .. math::
            f_i = \omega_i / (2 \pi) = \sqrt{\tau_i} / (2 \pi).

        For non-FEM modes the eigenvalues are unitless and have no direct
        metric interpretation. In this case a :class:`RuntimeError` is
        raised.

        Returns
        -------
        frequencies : numpy.ndarray of shape (n_points,)
            Spatial frequencies :math:`f_i` (in inverse length units, e.g.
            1/m if the coordinates are given in metres).

        Raises
        ------
        RuntimeError
            If :attr:`mode` is not ``'fem'``.
        """
        omega = self.spatial_angular_frequencies()
        return omega / (2.0 * np.pi)

    def spatial_wavelengths(self) -> FloatArray:
        r"""Return spatial wavelengths for FEM-based SPHARA basis.

        For FEM discretization (``mode='fem'``), the spatial
        wavelengths :math:`\lambda_i` corresponding to the eigenvalues
        :math:`\tau_i` are defined by

        .. math::
            \lambda_i = 2 \pi / \sqrt{\tau_i} = 1 / f_i.

        The DC component (zero eigenvalue) is assigned an infinite wavelength.

        Returns
        -------
        wavelengths : numpy.ndarray of shape (n_points,)
            Spatial wavelengths :math:`\lambda_i`. The DC component receives
            ``np.inf``.

        Raises
        ------
        RuntimeError
            If :attr:`mode` is not ``'fem'``.

        """
        omega = self.spatial_angular_frequencies()
        wavelengths = np.empty_like(omega)
        # DC mode: omega == 0 → infinite wavelength
        zero_mask = omega == 0.0
        nonzero_mask = ~zero_mask
        wavelengths[zero_mask] = np.inf
        wavelengths[nonzero_mask] = 2.0 * np.pi / omega[nonzero_mask]
        return wavelengths
    
