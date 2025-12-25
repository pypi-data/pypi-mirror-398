# results.py
from dataclasses import dataclass
import numpy as np
from typing import Any


@dataclass
class AnalysisResults:
    """
    Reiner Datencontainer für Analyse-Ergebnisse.
    KEINE Berechnungen, KEIN Plotting.
    """

    # Input (Geometrie, Materialien, Knoten, Stäbe)
    Inp: Any

    # Globale Ergebnisse
    u_ges: np.ndarray
    GesMat: np.ndarray
    FGes: np.ndarray

    # Elementweise Matrizen
    TransMats: np.ndarray
    K_el_i_store: np.ndarray
    u_el: np.ndarray
    s_el: np.ndarray

    # Schnittgrößen an den Elementenden
    N_el_i_store: np.ndarray
    VY_el_i_store: np.ndarray
    VZ_el_i_store: np.ndarray
    MX_el_i_store: np.ndarray
    MY_el_i_store: np.ndarray
    MZ_el_i_store: np.ndarray

    # Zusatzinfos
    member_length: np.ndarray
