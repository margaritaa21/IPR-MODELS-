"""Tests HU-007 — `babu_odeh` post-auditoría contra Babu & Odeh (1989).

Verifica:
 - CA-1: J ∈ [17, 22] STB/d/psi para el ejemplo PDF p. 30 (referencia
   Helmy-Wattenbarger: 19,98).
 - CA-2: docstring cita Babu & Odeh (1989).
 - CA-3: marca EXPERIMENTAL removida.
 - CA-4: penetración total (L = b_res) — sR = 0, formula colapsa al término
   básico ln(√A/rw_eq) + ln(CH) - 0.75.

Convención del modelo (post-HU-007):
    Pozo a lo largo del eje Y, longitud L ≤ b_res.
    a_res = X-dim (transversa); b_res = Y-dim (along-pozo); h = Z (espesor).
    x_mid, y_0, z_0 = coordenadas del centro del pozo en X, Y, Z.
"""
import os
import sys

import numpy as np
import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from logic.ipr_models import IPRModels  # noqa: E402


# Inputs del ejemplo PDF p. 30 (Pr=Pb=3814,7; caja 2000×2000×100; pozo centrado).
PDF_INPUTS = dict(
    kx=100.0, ky=100.0, kz=10.0, h=100.0,
    a_res=2000.0, b_res=2000.0,
    mu=1.095, bo=1.278, L=1000.0, rw=0.25,
    x_mid=1000.0, y_0=1000.0, z_0=50.0, s_res=0.0,
    p_res=3814.7, steps=400,
)


def _slope_J(q, p):
    """Estima J como -dq/dPwf (constante para tramo lineal monofásico)."""
    return (q[1] - q[0]) / (p[0] - p[1])


# ── CA-1: J en rango [17, 22] ──────────────────────────────────────────────
def test_ca1_babu_odeh_pi_in_target_range():
    """Babu-Odeh post-fix entrega J ∈ [17, 22] para inputs PDF (Helmy=19.98)."""
    q, p = IPRModels.babu_odeh(**PDF_INPUTS)
    J = _slope_J(q, p)
    assert 17.0 <= J <= 22.0, f"J(Babu-Odeh) = {J:.3f} fuera de [17, 22]"
    # Pin: con todos los fixes aplicados, J ≈ 18.29
    assert J == pytest.approx(18.29, abs=0.2)


# ── CA-2: docstring cita el paper original ────────────────────────────────
def test_ca2_docstring_cites_babu_odeh_1989():
    doc = IPRModels.babu_odeh.__doc__ or ""
    assert "Babu" in doc and "1989" in doc, \
        "Docstring de babu_odeh no cita Babu & Odeh (1989)"


# ── CA-3: marca EXPERIMENTAL removida ─────────────────────────────────────
def test_ca3_experimental_label_removed():
    doc = IPRModels.babu_odeh.__doc__ or ""
    assert "EXPERIMENTAL" not in doc, \
        "babu_odeh sigue marcado como EXPERIMENTAL en el docstring"


# ── CA-4: penetración total (L = b_res) — sR = 0 ──────────────────────────
def test_ca4_full_penetration_no_sR():
    """Con L = b_res la skin de penetración parcial s_R = 0; la fórmula colapsa
    al término básico ln(√A/r_w_eq) + ln(C_H) - 0.75 + s_d.
    """
    import math

    inputs = dict(PDF_INPUTS)
    inputs["L"] = inputs["b_res"]  # full penetration
    q, p = IPRModels.babu_odeh(**inputs)
    J = _slope_J(q, p)

    # Cálculo manual sin s_R:
    A = inputs["a_res"] * inputs["h"]
    rw_eq = (inputs["rw"] / 2.0) * (
        (inputs["kz"] / inputs["kx"]) ** 0.25
        + (inputs["kx"] / inputs["kz"]) ** 0.25
    )
    a_over_h_anis = (inputs["a_res"] / inputs["h"]) * math.sqrt(
        inputs["kz"] / inputs["kx"]
    )
    xm_a = inputs["x_mid"] / inputs["a_res"]
    z_h = inputs["z_0"] / inputs["h"]
    ln_CH = (
        6.28 * a_over_h_anis * (1.0 / 3.0 - xm_a + xm_a ** 2)
        - math.log(math.sin(math.pi * z_h))
        - 0.5 * math.log(a_over_h_anis)
        - 1.088
    )
    denom = inputs["mu"] * inputs["bo"] * (
        math.log(math.sqrt(A) / rw_eq) + ln_CH - 0.75
    )
    J_manual = (0.00708 * inputs["b_res"] * math.sqrt(inputs["kx"] * inputs["kz"])) / denom

    assert J == pytest.approx(J_manual, rel=1e-3), \
        f"J(full pen) = {J:.3f} no coincide con cálculo manual {J_manual:.3f}"


# ── Robustez: no NaN/inf y pendiente lineal ────────────────────────────────
def test_no_nan_or_inf_pdf_inputs():
    q, p = IPRModels.babu_odeh(**PDF_INPUTS)
    assert np.all(np.isfinite(q))
    assert np.all(np.isfinite(p))
    assert np.all(q >= 0)


def test_linearity_below_pres():
    """Babu-Odeh entrega IPR monofásica lineal (q = J·(Pr - Pwf))."""
    q, p = IPRModels.babu_odeh(**PDF_INPUTS)
    slope, intercept = np.polyfit(p, q, 1)
    J = -slope
    # AOF predicho = J·Pr; debe coincidir con el primer punto del array (Pwf=0).
    assert q[0] == pytest.approx(J * PDF_INPUTS["p_res"], rel=1e-3)


# ── Sensibilidad al cambio de anisotropía vertical (sanidad física) ───────
def test_pi_decreases_with_lower_kz():
    """Bajar kz (anisotropía vertical aumenta) reduce J de Babu-Odeh."""
    inputs_high_kz = dict(PDF_INPUTS, kz=10.0)
    inputs_low_kz = dict(PDF_INPUTS, kz=1.0)
    J_high = _slope_J(*IPRModels.babu_odeh(**inputs_high_kz))
    J_low = _slope_J(*IPRModels.babu_odeh(**inputs_low_kz))
    assert J_low < J_high, \
        f"J(kz=1)={J_low:.3f} debería ser < J(kz=10)={J_high:.3f}"
