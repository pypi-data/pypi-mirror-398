r""".. _sphara_filtering_eeg:


Spatial SPHARA filtering of EEG data
====================================

.. topic:: Section contents

   In this tutorial we show how to use the SPHARA basis functions to
   design spatial low-pass filters for application to EEG data. The
   FEM discretization of the Laplace-Beltrami operator is used to
   calculate the SPHARA basis functions. We then construct different
   low-pass designs (ideal, Gaussian, Butterworth) using the helper
   functions provided by :mod:`spharapy.spectral_filters`.

Introduction
------------

The human head as a volume conductor exhibits spatial low-pass filter
properties. For this reason, the potential distribution of the EEG on
the scalp surface can be represented by a few low-frequency SPHARA
basis functions, compare :ref:`sphara_analysis_eeg`. In contrast,
single channel dropouts and spatially uncorrelated sensor noise
exhibit an almost equally distributed spatial SPHARA spectrum. This
fact can be exploited for the design of a spatial filter for the
suppression of uncorrelated sensor noise.

"""

######################################################################
# At the beginning we import three modules of the SpharaPy package as
# well as several other packages and single functions from
# packages.

# Code source: Uwe Graichen
# License: BSD 3 clause

# import modules from spharapy package
# import additional modules used in this tutorial
import matplotlib.pyplot as plt
import numpy as np
from mpl_toolkits.mplot3d import Axes3D  # noqa: F401  (registers 3D)

import spharapy.datasets as sd
import spharapy.spharafilter as sf
import spharapy.trimesh as tm
import spharapy.spectral_filters as sfilt

######################################################################
# Import the spatial configuration of the EEG sensors and the SEP data
# --------------------------------------------------------------------
# In this tutorial we show how to use the SPHARA basis functions to
# design spatial low-pass filters for application to EEG data. The
# FEM discretization of the Laplace-Beltrami operator is used to
# calculate the SPHARA basis functions. We then construct different
# low-pass designs (ideal, Gaussian, Butterworth) using the helper
# functions provided by :mod:`spharapy.spectral_filters`.


# loading the 256 channel EEG dataset from spharapy sample datasets
mesh_in = sd.load_eeg_256_channel_study()

######################################################################
# The dataset includes lists of vertices, triangles, and sensor
# labels, as well as EEG data from previously performed experiment
# addressing the cortical activation related to somatosensory-evoked
# potentials (SEP).

print(mesh_in.keys())

######################################################################
# The triangulation of the EEG sensor setup consists of 256 vertices
# and 480 triangles. The EEG data consists of 256 channels and 369
# time samples, 50 ms before to 130 ms after stimulation. The sampling
# frequency is 2048 Hz.

vertlist = np.array(mesh_in["vertlist"])
trilist = np.array(mesh_in["trilist"])
eegdata = np.array(mesh_in["eegdata"])
print("vertices = ", vertlist.shape)
print("triangles = ", trilist.shape)
print("eegdata = ", eegdata.shape)

######################################################################

fig = plt.figure()
fig.subplots_adjust(left=0.02, right=0.98, top=0.98, bottom=0.02)
ax = fig.add_subplot(111, projection="3d")
ax.set_xlabel("x")
ax.set_ylabel("y")
ax.set_zlabel("z")
ax.set_title("The triangulated EEG sensor setup")
ax.view_init(elev=20.0, azim=80.0)
ax.set_aspect("auto")
ax.plot_trisurf(
    vertlist[:, 0],
    vertlist[:, 1],
    vertlist[:, 2],
    triangles=trilist,
    color="lightblue",
    edgecolor="black",
    linewidth=0.5,
    shade=True,
)
plt.show()

######################################################################

x = np.arange(-50, 130, 1 / 2.048)
figeeg = plt.figure()
axeeg = figeeg.gca()
axeeg.plot(x, eegdata[:, :].transpose())
axeeg.set_xlabel("t/ms")
axeeg.set_ylabel("V/µV")
axeeg.set_title("SEP data")
axeeg.set_ylim(-3.5, 3.5)
axeeg.set_xlim(-50, 130)
axeeg.grid(True)
plt.show()


######################################################################
# Create a SpharaPy TriMesh instance
# ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
# In the next step we create an instance of the class
# :class:`spharapy.trimesh.TriMesh` from the list of vertices and
# triangles.

# create an instance of the TriMesh class
mesh_eeg = tm.TriMesh(trilist, vertlist)

######################################################################
# SPHARA filter using FEM discretisation
# --------------------------------------
# Create a SpharaPy SpharaFilter instance
# ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
#
# In the following step of the tutorial we determine an instance of
# the class SpharaFilter, which is used to compute the SPHARA basis.
# For the determination of the SPHARA basis we use a Laplace-Beltrami
# operator, which is discretized by the FEM approach.

sphara_filter_fem = sf.SpharaFilter(mesh_eeg, mode="fem")
basis_functions_fem, natural_frequencies_fem = sphara_filter_fem.basis()


######################################################################
# Visualization the basis functions
# ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
# The first 15 spatially low-frequency SPHARA basis functions are
# shown below, starting with DC at the top left.
#

figsb1, axes1 = plt.subplots(nrows=5, ncols=3, figsize=(8, 12), subplot_kw={"projection": "3d"})
for i in range(np.size(axes1)):
    colors = np.mean(basis_functions_fem[trilist, i + 0], axis=1)
    ax = axes1.flat[i]
    ax.set_xlabel("x")
    ax.set_ylabel("y")
    ax.set_zlabel("z")
    ax.view_init(elev=60.0, azim=80.0)
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
    trisurfplot.set_clim(-0.01, 0.01)

cbar = figsb1.colorbar(
    trisurfplot,
    ax=axes1.ravel().tolist(),
    shrink=0.85,
    orientation="horizontal",
    fraction=0.05,
    pad=0.05,
    anchor=(0.5, -4.5),
)

plt.subplots_adjust(left=0.0, right=1.0, bottom=0.08, top=1.0)
plt.show()


######################################################################
# Design SPHARA low-pass filters in the spectral domain
# ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
#
# The eigenvalues returned by :meth:`~spharapy.spharabasis.SpharaBasis.basis`
# for ``mode="fem"`` are proportional to squared spatial wave numbers.
# We derive a one-dimensional SPHARA frequency axis from them and
# design three different low-pass filters:
#
# * an ideal ("brick-wall") low-pass that keeps the first 20 modes,
# * a Gaussian low-pass with smooth roll-off, and
# * a Butterworth low-pass of order 4.
#
# Each filter is represented by a real-valued transfer function
# :math:`H_i` on the SPHARA frequency axis and handed to
# :class:`spharapy.spharafilter.SpharaFilter` via the ``specification``
# argument.

# derive SPHARA "frequencies" from the FEM eigenvalues
sphara_freq = np.sqrt(np.maximum(natural_frequencies_fem, 0.0))
sphara_freq_rel = sphara_freq / sphara_freq.max()

# --- ideal low-pass: keep the first 20 SPHARA modes -----------------
n_modes_ideal = 20
spec_ideal = np.zeros_like(sphara_freq_rel)
spec_ideal[:n_modes_ideal] = 1.0

# --- Gaussian low-pass ----------------------------------------------
cutoff_rel = 0.15  # relative cutoff (0..1) on the SPHARA frequency axis
half_power_db = -3.01029995664  # −3 dB ≈ half power

spec_gauss = sfilt.transfer_func_gaussian_lowpass(
    sphara_freq_rel,
    fc=cutoff_rel,
    dB=half_power_db,
)

# --- Butterworth low-pass (order 4) ---------------------------------
butter_order = 4
spec_butter = sfilt.transfer_func_butterworth_lowpass(
    sphara_freq_rel,
    fc=cutoff_rel,
    order=butter_order,
    dB=half_power_db,
)

# create filter instances for later use
sphara_filter_ideal = sf.SpharaFilter(mesh_eeg, mode="fem", specification=spec_ideal)
sphara_filter_gauss = sf.SpharaFilter(mesh_eeg, mode="fem", specification=spec_gauss)
sphara_filter_butter = sf.SpharaFilter(mesh_eeg, mode="fem", specification=spec_butter)

# optional: visualise the three transfer functions
fig_tf, ax_tf = plt.subplots(figsize=(6, 4))
ax_tf.plot(sphara_freq_rel, spec_ideal, label="ideal (20 modes)")
ax_tf.plot(sphara_freq_rel, spec_gauss, label="Gaussian")
ax_tf.plot(sphara_freq_rel, spec_butter, label=f"Butterworth (order {butter_order})")
ax_tf.set_xlabel("relative SPHARA frequency")
ax_tf.set_ylabel("gain")
ax_tf.set_title("SPHARA low-pass transfer functions")
ax_tf.grid(True)
ax_tf.legend()
plt.show()


######################################################################
# SPHARA filtering of the EEG data
# ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
#
# In the next step we perform the SPHARA filtering of the EEG
# data. As a result, the butterfly plots of all channels of the EEG
# with and without filtering are compared for three different
# low-pass designs.

# perform the SPHARA filtering
eeg_spatial = eegdata.transpose()  # shape: (n_samples, n_channels)

eeg_filt_ideal = sphara_filter_ideal.filter(eeg_spatial).transpose()
eeg_filt_gauss = sphara_filter_gauss.filter(eeg_spatial).transpose()
eeg_filt_butter = sphara_filter_butter.filter(eeg_spatial).transpose()

figsteeg, axes = plt.subplots(nrows=4, figsize=(8, 9), sharex=True)

for ax in axes:
    ax.axvline(13, color="red")
    ax.axvline(19, color="blue")
    ax.axvline(30, color="green")

axes[0].plot(x, eegdata[:, :].transpose())
axes[0].set_title("Unfiltered EEG data")
axes[0].set_ylabel("V/µV")
axes[0].set_ylim(-2.5, 2.5)
axes[0].set_xlim(-50, 130)
axes[0].grid(True)

axes[1].plot(x, eeg_filt_ideal[:, :].transpose())
axes[1].set_title("SPHARA ideal low-pass, 20 modes")
axes[1].set_ylabel("V/µV")
axes[1].set_ylim(-2.5, 2.5)
axes[1].set_xlim(-50, 130)
axes[1].grid(True)

axes[2].plot(x, eeg_filt_gauss[:, :].transpose())
axes[2].set_title("SPHARA Gaussian low-pass")
axes[2].set_ylabel("V/µV")
axes[2].set_ylim(-2.5, 2.5)
axes[2].set_xlim(-50, 130)
axes[2].grid(True)

axes[3].plot(x, eeg_filt_butter[:, :].transpose())
axes[3].set_title(f"SPHARA Butterworth low-pass (order {butter_order})")
axes[3].set_ylabel("V/µV")
axes[3].set_xlabel("t/ms")
axes[3].set_ylim(-2.5, 2.5)
axes[3].set_xlim(-50, 130)
axes[3].grid(True)

plt.subplots_adjust(left=0.1, right=0.95, bottom=0.08, top=0.95, hspace=0.35)
plt.show()


######################################################################
# Application of the the spatial SPHARA filter to data with artificial noise
# ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
#
# In a final step the EEG data are disturbed by white noise with
# different noise levels (3 dB, 0 dB and -3 dB). A spatial Gaussian
# low-pass SPHARA filter is applied to these data. The results of the
# filtering are shown below.

# vector with noise levels in dB
db_val_vec = [3, 0, -3]

# compute the power of the SEP data
power_sep = np.sum(np.square(np.absolute(eegdata))) / eegdata.size

# compute a vector with standard deviations of the noise in relation
# to signal power for the given noise levels
noise_sd_vec = list(map(lambda db_val: np.sqrt(power_sep / (10 ** (db_val / 10))), db_val_vec))

# add the noise to the EEG data
eegdata_noise = list(
    map(lambda noise_sd: eegdata + np.random.normal(0, noise_sd, [256, 369]), noise_sd_vec)
)

# filter the EEG data containing the artificial noise
eegdata_noise_filt = list(
    map(
        lambda eeg_noise: sphara_filter_gauss.filter(eeg_noise.transpose()).transpose(),
        eegdata_noise,
    )
)

######################################################################

figfilt, axesfilt = plt.subplots(nrows=4, ncols=2, figsize=(8, 10.5))

axesfilt[0, 0].plot(x, eegdata[:, :].transpose())
axesfilt[0, 0].set_title("EEG data")
axesfilt[0, 0].set_ylabel("V/µV")
axesfilt[0, 0].set_xlabel("t/ms")
axesfilt[0, 0].set_ylim(-2.5, 2.5)
axesfilt[0, 0].set_xlim(-50, 130)
axesfilt[0, 0].grid(True)

axesfilt[0, 1].plot(x, eeg_filt_gauss[:, :].transpose())
axesfilt[0, 1].set_title("SPHARA Gaussian low-pass filtered EEG data")
axesfilt[0, 1].set_ylabel("V/µV")
axesfilt[0, 1].set_xlabel("t/ms")
axesfilt[0, 1].set_ylim(-2.5, 2.5)
axesfilt[0, 1].set_xlim(-50, 130)
axesfilt[0, 1].grid(True)

for i in range(3):
    axesfilt[i + 1, 0].plot(x, eegdata_noise[i].transpose())
    axesfilt[i + 1, 0].set_title("EEG data + noise, SNR " + str(db_val_vec[i]) + "dB")
    axesfilt[i + 1, 0].set_ylabel("V/µV")
    axesfilt[i + 1, 0].set_xlabel("t/ms")
    axesfilt[i + 1, 0].set_ylim(-2.5, 2.5)
    axesfilt[i + 1, 0].set_xlim(-50, 130)
    axesfilt[i + 1, 0].grid(True)

    axesfilt[i + 1, 1].plot(x, eegdata_noise_filt[i].transpose())
    axesfilt[i + 1, 1].set_title(
        "EEG + noise, SNR "
        + str(db_val_vec[i])
        + " dB,\n SPHARA Gaussian low-pass"
    )
    axesfilt[i + 1, 1].set_ylabel("V/µV")
    axesfilt[i + 1, 1].set_xlabel("t/ms")
    axesfilt[i + 1, 1].set_ylim(-2.5, 2.5)
    axesfilt[i + 1, 1].set_xlim(-50, 130)
    axesfilt[i + 1, 1].grid(True)

plt.subplots_adjust(left=0.07, right=0.97, bottom=0.05, top=0.95, hspace=0.45)
plt.show()
# sphinx_gallery_thumbnail_number = 6
