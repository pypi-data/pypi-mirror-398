import numpy as np
from numba import njit, prange
from daemonflux import Flux

import numpy as np

# Muon rest mass (PDG 2022-ish)
M_MU_GEV = 0.105658375  # GeV


def p_to_E_total(p_GeV, m_GeV=M_MU_GEV):
    """
    Convert muon momentum -> TOTAL energy (E = sqrt(p^2 + m^2)).

    Parameters
    ----------
    p_GeV : float or array-like
        Muon momentum in GeV/c.
    m_GeV : float, optional
        Muon mass in GeV. Default is M_MU_GEV.

    Returns
    -------
    E_GeV : float or np.ndarray
        Total energy in GeV.
    """
    p = np.asarray(p_GeV, dtype=float)
    return np.sqrt(p**2 + m_GeV**2)


def p_to_T_kin(p_GeV, m_GeV=M_MU_GEV):
    """
    Convert muon momentum -> KINETIC energy (T = E - m).

    Parameters
    ----------
    p_GeV : float or array-like
        Muon momentum in GeV/c.
    m_GeV : float, optional
        Muon mass in GeV. Default is M_MU_GEV.

    Returns
    -------
    T_GeV : float or np.ndarray
        Kinetic energy in GeV.
    """
    E = p_to_E_total(p_GeV, m_GeV=m_GeV)
    return E - m_GeV


def E_total_to_p(E_GeV, m_GeV=M_MU_GEV):
    """
    Convert TOTAL energy -> momentum (p = sqrt(E^2 - m^2)).

    Parameters
    ----------
    E_GeV : float or array-like
        Total energy in GeV.
    m_GeV : float, optional
        Muon mass in GeV. Default is M_MU_GEV.

    Returns
    -------
    p_GeV : float or np.ndarray
        Momentum in GeV/c.
    """
    E = np.asarray(E_GeV, dtype=float)
    inside = np.maximum(E**2 - m_GeV**2, 0.0)  # clamp tiny negatives
    return np.sqrt(inside)


def T_kin_to_p(T_GeV, m_GeV=M_MU_GEV):
    """
    Convert KINETIC energy -> momentum.

    Parameters
    ----------
    T_GeV : float or array-like
        Kinetic energy in GeV.
    m_GeV : float, optional
        Muon mass in GeV. Default is M_MU_GEV.

    Returns
    -------
    p_GeV : float or np.ndarray
        Momentum in GeV/c.
    """
    T = np.asarray(T_GeV, dtype=float)
    E = T + m_GeV
    inside = np.maximum(E**2 - m_GeV**2, 0.0)
    return np.sqrt(inside)


fl = Flux(location="generic", use_calibration=True)


CM2_TO_M2 = 10000  # cm^2 to m^2

P1, P2, P3, P4, P5 = 0.102573, -0.068287, 0.958633, 0.0407253, 0.817285

@njit(cache=True, fastmath=True)
def _cos_theta_star(theta_rad):
    c = np.cos(theta_rad)
    if c > 1.0: c = 1.0
    elif c < -1.0: c = -1.0
    num = c*c + P1*P1 + P2*(c**P3) + P4*(c**P5)
    den = 1.0 + P1*P1 + P2 + P4
    val = num / den
    if val < 0.0: val = 0.0
    return np.sqrt(val)

@njit(cache=True, fastmath=True)
def _dphi0_dE(theta_rad, E_GeV):
    if E_GeV <= 0.0: return 0.0
    cst   = _cos_theta_star(theta_rad)
    x     = E_GeV
    core  = x * (1.0 + 3.64 / (x * (cst**1.29)))
    spec  = 0.14 * (core ** (-2.7))
    dem_pi = 1.0 + 1.1 * x * cst / 115.0
    dem_K  = 1.0 + 1.1 * x * cst / 850.0
    return (spec * ((1.0 / dem_pi) + 0.054 / dem_K)) * CM2_TO_M2

def differential_flux(theta_rad_array, E_GeV):
    egrid = np.array([E_GeV])
    angle = np.clip(np.degrees(theta_rad_array.flatten()), 0, 90)
    argsort = np.argsort(angle)
    sorted_angle = angle[argsort]
    sorted_flux = fl.flux(p_to_T_kin(egrid), sorted_angle, "muflux")
    flux_array = np.zeros_like(sorted_flux)
    flux_array[argsort] = sorted_flux
    
    flux_array = flux_array / E_GeV**3 * CM2_TO_M2
    return flux_array.reshape(theta_rad_array.shape)
    
# @njit(cache=True, parallel=True, fastmath=True)
# def differential_flux(theta_rad_array, E_GeV):
#     shape = theta_rad_array.shape
#     theta_rad_array = theta_rad_array.flatten()
#     flux_array = np.zeros_like(theta_rad_array)
#     for i in prange(theta_rad_array.shape[0]):
#         if theta_rad_array[i] < 0.0 or theta_rad_array[i] > np.pi / 2:
#             flux_array[i] = 0.0
#         else:
#             flux_array[i] = _dphi0_dE(theta_rad_array[i], E_GeV)
# 
#     flux_array = flux_array.reshape(shape)
#     return flux_array

