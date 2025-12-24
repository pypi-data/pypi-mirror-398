r""".. _quick_start:


Quick start with SpharaPy
=========================

.. topic:: Section contents

   In this tutorial, we briefly introduce the vocabulary used in
   spatial harmonic analysis (SPHARA) and we give a simple learning
   example to SpharaPy. In addition, we show how to design a simple
   spatial low-pass filter in the SPHARA domain.


SPHARA -- The problem setting
-----------------------------

Fourier analysis is one of the standard tools in digital signal and
image processing. In ordinary digital image data, the pixels are
arranged in a Cartesian or rectangular grid. Performing the Fourier
transform, the image data :math:`x[m,n]` is compared (using a scalar
product) with a two-dimensional Fourier basis :math:`f[k,l] =
\mathrm{e}^{-2\pi \mathrm{i} \cdot \left(\frac{mk}{M} + \frac{nl}{N}
\right) }`. In Fourier transform on a Cartesian grid, the Fourier
basis used is usually inherently given in the transformation rule

.. math::

   X[k,l] = \sum_{m=0}^{M-1} \sum_{n=0}^{N-1} x[m,n] \cdot
   \mathrm{e}^{-2\pi \mathrm{i} \cdot \left(\frac{mk}{M} +
   \frac{nl}{N} \right) }\,.

A Fourier basis can be obtained as a solution to Laplace's eigenvalue
problem (related to the Helmholtz equation)

.. math::

   \mathbf{L} \boldsymbol{\varphi}_i = \lambda_i \boldsymbol{\varphi}_i\,,\qquad\qquad(1)

where :math:`\mathbf{L}` is a discrete :term:`Laplace–Beltrami
operator` in matrix notation, the eigenvectors
:math:`\boldsymbol{\varphi}_i` contain the spatial harmonic functions
and the eigenvalues :math:`\lambda_i \ge 0` are real-valued. When
:math:`\mathbf{L}` is obtained from a finite element discretization of
the Laplace–Beltrami operator, the quantities
:math:`\sqrt{\lambda_i}` can be interpreted as spatial angular
frequencies; see :ref:`introduction` for details.


An arbitrary arrangement of sample points on a surface in
three-dimensional space can be described by means of a
:term:`triangular mesh`. A spatial harmonic basis (**SPHARA basis**)
for such a mesh can be obtained by discretizing a Laplace–Beltrami
operator for the mesh and solving the eigenvalue problem in equation
(1). SpharaPy provides classes and functions to support these tasks:

- managing triangular meshes describing the spatial arrangement of
  the sample points,
- determining the Laplace–Beltrami operator of these meshes,
- computing a basis for spatial Fourier analysis of data defined
  on the triangular mesh, and
- performing the SPHARA transform and filtering, including
  filter design in the SPHARA domain via :mod:`spharapy.spectral_filters`.

"""

######################################################################
# The SpharaPy package
# --------------------
# The SpharaPy package consists of several modules:
#
# - :mod:`spharapy.trimesh`
# - :mod:`spharapy.spharabasis`
# - :mod:`spharapy.spharatransform`
# - :mod:`spharapy.spharafilter`
# - :mod:`spharapy.spectral_filters`
# - :mod:`spharapy.datasets`
#
# In the following we use a subset of these modules to briefly show
# how a SPHARA basis can be calculated for given spatial sample points
# and how a simple spatial low-pass filter can be designed in the
# SPHARA domain.
#
# The :mod:`spharapy.trimesh` module contains the
# :class:`spharapy.trimesh.TriMesh` class, which can be used to
# specify the configuration of the spatial sample points. The SPHARA
# basis functions can be determined using the
# :mod:`spharapy.spharabasis` module. The :mod:`spharapy.datasets`
# module is an interface to the example data sets provided with the
# SpharaPy package. Spatial filtering in the SPHARA domain is
# supported by :mod:`spharapy.spharafilter` and
# :mod:`spharapy.spectral_filters`.

# Code source: Uwe Graichen
# License: BSD 3 clause

# import modules from spharapy package
# import additional modules used in this tutorial
import matplotlib.pyplot as plt
import numpy as np
from mpl_toolkits.mplot3d import Axes3D  # noqa: F401  (registers 3D)

import spharapy.datasets as sd
import spharapy.spharabasis as sb
import spharapy.spharafilter as sf
import spharapy.spectral_filters as spf
import spharapy.trimesh as tm

######################################################################
# Specification of the spatial configuration of the sample points
# ---------------------------------------------------------------
#
# To illustrate some basic functionality of the SpharaPy package, we
# load a simple triangle mesh from the example data sets.

# loading the simple mesh from spharapy sample datasets
mesh_in = sd.load_simple_triangular_mesh()

######################################################################
# The imported mesh is defined by a **list of triangles** and a **list of
# vertices**. The data are stored in a dictionary with the two keys
# 'vertlist' and 'trilist'

print(mesh_in.keys())

######################################################################
# The simple, triangulated surface consists of 131 vertices and 232
# triangles and is the triangulation of a hemisphere of a unit ball.

vertlist = np.array(mesh_in["vertlist"])
trilist = np.array(mesh_in["trilist"])
print("vertices = ", vertlist.shape)
print("triangles = ", trilist.shape)

######################################################################

fig = plt.figure()
fig.subplots_adjust(left=0.02, right=0.98, top=0.98, bottom=0.02)
ax = fig.add_subplot(111, projection="3d")
ax.set_xlabel("x")
ax.set_ylabel("y")
ax.set_zlabel("z")
ax.view_init(elev=60.0, azim=45.0)
ax.set_aspect("auto")
ax.plot_trisurf(
    vertlist[:, 0],
    vertlist[:, 1],
    vertlist[:, 2],
    triangles=trilist,
    color="lightblue",
    edgecolor="black",
    linewidth=1,
)
plt.show()


######################################################################
#
# Determining the Laplace–Beltrami Operator
# -----------------------------------------
#
# In a further step, an instance of the class
# :class:`spharapy.trimesh.TriMesh` is created from the lists of
# vertices and triangles. The class :class:`spharapy.trimesh.TriMesh`
# provides a number of methods to determine certain properties of the
# triangle mesh required to generate the SPHARA basis.

# print all implemented methods of the TriMesh class
print([func for func in dir(tm.TriMesh) if not func.startswith("__")])

######################################################################

# create an instance of the TriMesh class
simple_mesh = tm.TriMesh(trilist, vertlist)

######################################################################
# For the simple triangle mesh an instance of the class
# :class:`spharapy.spharabasis.SpharaBasis` is created and the finite
# element discretization ('fem') is used. The complete set of SPHARA
# basis functions and the corresponding Laplace–Beltrami eigenvalues
# are determined.

sphara_basis = sb.SpharaBasis(simple_mesh, "fem")
basis_functions, eigenvalues_fem = sphara_basis.basis()

######################################################################
# The set of SPHARA basis functions can be used for spatial Fourier
# analysis of the spatially irregularly sampled data.
#
# The first 15 spatially low-frequency SPHARA basis functions are
# shown below, starting with DC at the top left.

# sphinx_gallery_thumbnail_number = 2
figsb1, axes1 = plt.subplots(nrows=5, ncols=3, figsize=(8, 12), subplot_kw={"projection": "3d"})
for i in range(np.size(axes1)):
    colors = np.mean(basis_functions[trilist, i + 0], axis=1)
    ax = axes1.flat[i]
    ax.set_xlabel("x")
    ax.set_ylabel("y")
    ax.set_zlabel("z")
    ax.view_init(elev=45.0, azim=15.0)
    ax.set_aspect("auto")
    trisurfplot = ax.plot_trisurf(
        vertlist[:, 0],
        vertlist[:, 1],
        vertlist[:, 2],
        triangles=trilist,
        cmap=plt.cm.bwr,
        edgecolor="white",
        linewidth=0.0,
    )
    trisurfplot.set_array(colors)
    trisurfplot.set_clim(-1, 1)

cbar = figsb1.colorbar(
    trisurfplot,
    ax=axes1.ravel().tolist(),
    shrink=0.75,
    orientation="horizontal",
    fraction=0.05,
    pad=0.05,
    anchor=(0.5, -4.0),
)

plt.subplots_adjust(left=0.0, right=1.0, bottom=0.08, top=1.0)
plt.show()

######################################################################
# Designing a Gaussian SPHARA low-pass filter
# -------------------------------------------
#
# In this final part of the quick-start example we show how to design
# a simple Gaussian low-pass filter in the SPHARA domain using the
# :mod:`spharapy.spectral_filters` module and how such a transfer
# function can be used with :class:`spharapy.spharafilter.SpharaFilter`.
#
# For illustration, we design a Gaussian low-pass whose cutoff is
# chosen such that approximately the first 40 basis functions (with
# the lowest eigenvalues) are passed with only moderate attenuation.

# create a SpharaFilter instance using FEM discretisation
sphara_filter_fem = sf.SpharaFilter(simple_mesh, mode="fem")

# compute the associated SPHARA basis and Laplace–Beltrami eigenvalues
basis_filt, eigenvalues_filt = sphara_filter_fem.basis()

# choose a cutoff eigenvalue corresponding (approximately) to the
# 40th spatial mode
cutoff_index = 40
fc_eig = float(eigenvalues_filt[cutoff_index])

# design a Gaussian low-pass transfer function in the SPHARA domain
# (here we work directly on the eigenvalue axis; for FEM discretisation
# the square roots of the eigenvalues can be interpreted as spatial
# angular frequencies, see :ref:`introduction`).
h_gauss = spf.transfer_func_gaussian_lowpass(
    eigenvalues_filt,
    fc=fc_eig,
    dB=-6.0,
)

# assign the filter specification (transfer vector) to the SpharaFilter
sphara_filter_fem.specification = h_gauss

print(
    "Designed a Gaussian SPHARA low-pass filter with cutoff at eigenvalue "
    f"index {cutoff_index}."
)

######################################################################
# The resulting transfer vector ``h_gauss`` can now be used to filter
# spatial data defined on the vertices of ``simple_mesh`` via the
# :meth:`spharapy.spharafilter.SpharaFilter.filter` method.
