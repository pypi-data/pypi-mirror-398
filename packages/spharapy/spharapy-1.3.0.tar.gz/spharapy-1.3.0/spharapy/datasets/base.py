"""
Base IO code to provide sample datasets
"""

from pathlib import Path

import numpy as np

__author__ = "Uwe Graichen"
__copyright__ = "Copyright 2018-2025, Uwe Graichen"
__credits__ = ["Uwe Graichen"]
__license__ = "BSD-3-Clause"
__version__ = "1.2.0"
__maintainer__ = "Uwe Graichen"
__email__ = "uwe.graichen@tu-ilmenau.de, uwe.graichen@kl.ac.at"
__status__ = "Release"


def load_minimal_triangular_mesh():
    r"""Returns the triangulation of a single triangle

    The data set consists of a list of three vertices at the unit vectors
    of vector space :math:`\mathbb{R}^3` and a list of a single
    triangle.

    ===================    =
    Number of vertices     3
    Number of triangles    1
    ===================    =

    Parameters
    ----------
    None

    Returns
    -------
    triangulation : dictionary
        Dictionary-like object containing the triangulation of a single
        triangle. The attributes are: ``vertlist``, the list of vertices,
        ``trilist``, the list of triangles.
    """
    vert = np.array([[1.0, 0.0, 0.0], [0.0, 1.0, 0.0], [0.0, 0.0, 1.0]], dtype=float)
    tri = np.array([[0, 1, 2]], dtype=int)
    return {"vertlist": vert, "trilist": tri}


def load_simple_triangular_mesh():
    """Returns the triangulation of a simple triangular mesh

    The data set consists of a triangulation of an unit hemisphere.

    ===================    ===
    Number of vertices     131
    Number of triangles    232
    ===================    ===

    Parameters
    ----------
    None

    Returns
    -------
    triangulation : dictionary
        Dictionary-like object containing the triangulation of a
        simple triangular mesh. The attributes are: ``vertlist``, the
        list of vertices, ``trilist``, the list of triangles.
    """
    root = Path(__file__).resolve().parent

    # import vertices data
    datavertices = np.loadtxt(
        root / "data/simple_mesh_vert.csv", delimiter=",", dtype=float
    )  # FloatArray

    # import of triangle list
    datatriangles = np.loadtxt(
        root / "data/simple_mesh_tri.csv", delimiter=",", dtype=int
    )  # IntArray

    return {"vertlist": datavertices, "trilist": datatriangles}


def load_eeg_256_channel_study():
    r"""Load sensor setup and measured EEG data

    The data set consists of a triangulation of a 256 channel
    equidistant EEG cap and EEG data from previously performed
    experiment addressing the cortical activation related to
    somatosensory-evoked potentials (SEP). During the experiment the
    median nerve of the right forearm was stimulated by bipolar
    electrodes (stimulation rate: 3.7 Hz, interstimulus interval: 270
    ms, stimulation strength: motor plus sensor threshold
    :cite:`mauguiere99,cruccu08`, constant current rectangular pulse
    wave impulses with a length of 50 \mu s, number of stimulations:
    6000). Data were sampled at 2048 Hz and software high-pass (24
    dB/oct, cutoff-frequency 2 Hz) and notch (50 Hz and two harmonics)
    filtered. All trials were manually checked for artifacts, the
    remaining trials were averaged, see also S1 data set in
    :cite:`graichen15`.

    ===================    ========================================
    Number of vertices     256
    Number of triangles    480
    SEP Data (EEG)         256 channels, 369 time samples
    Time range             50 ms before to 130 ms after stimulation
    Sampling frequency     2048 Hz
    ===================    ========================================

    Parameters
    ----------
    None

    Returns
    -------
    triangulation and EEG data: dictionary
        Dictionary-like object containing the triangulation of a
        simple triangular mesh. The attributes are: ``vertlist``, the
        list of vertices, ``trilist``, the list of triangles,
        ``labellist`` the list of labels of the EEG channels, ``eegdata``,
        an array containing the EEG data.
    """
    root = Path(__file__).resolve().parent

    # import vertices data
    datavertices = np.loadtxt(
        root / "data/eeg_256_channels_vert.csv", delimiter=",", dtype=float
    )  # FloatArray

    # import of triangle list
    datatriangles = np.loadtxt(
        root / "data/eeg_256_channels_tri.csv", delimiter=",", dtype=int
    )  # IntArray

    # import the sensor labels
    datalabels = np.loadtxt(
        root / "data/eeg_256_channels_label.csv", delimiter=",", dtype=str
    )  # StrArray

    # import SEP EEG data
    eegdata = np.loadtxt(
        root / "data/eeg_256_channels_sep_data.csv", delimiter=",", dtype=float
    )  # FloatArray

    return {
        "vertlist": datavertices,
        "trilist": datatriangles,
        "labellist": datalabels,
        "eegdata": eegdata,
    }


if __name__ == "__main__":
    minimesh = load_minimal_triangular_mesh()
    print(minimesh["trilist"])
    print(minimesh["vertlist"])

    simplemesh = load_simple_triangular_mesh()
    print(simplemesh["trilist"])
    print(simplemesh["vertlist"])

    sepstudy = load_eeg_256_channel_study()
    print(sepstudy["trilist"])
    print(sepstudy["vertlist"])
    print(sepstudy["labellist"])
    print(sepstudy["eegdata"].shape)
