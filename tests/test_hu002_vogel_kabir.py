"""Tests para HU-002 — Vogel Modificado (Kabir) horizontal.

Verifica:
 - Partición saturado / subsaturado y continuidad/linealidad arriba de Pb.
 - Reproducción del ejemplo del PDF (sección 3.2.7, pp. 30-33, Tabla 3-5)
   usando el PI de Helmy-Wattenbarger (Ecs. 3-44 a 3-57).
"""
import os
import sys

import numpy as np
import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from logic.ipr_models import IPRModels  # noqa: E402


# ---------------------------------------------------------------------------
# Inputs del ejemplo PDF p. 30 (reservorio 2000×2000×100 ft, pozo centrado,
# L=1000 ft en dirección y, Pr=Pb=3814,7 psi, μ=1,095 cp, Bo=1,278 RB/STB).
# ---------------------------------------------------------------------------
PDF_INPUTS = dict(
    kh=100.0, kv=10.0, h=100.0, mu=1.095, bo=1.278,
    L=1000.0, reh=1128.0, rw=0.25, s=0.0,
    p_res=3814.7, pb=3814.7,
    pi_source="helmy",
    kx=100.0, ky=100.0, kz=10.0,
    a_res=2000.0, b_res=2000.0,
    x_w=1000.0, y_w=1000.0, z_w=50.0,
    steps=400,
)


def _q_at(q_arr, pwf_arr, pwf_target):
    order = np.argsort(pwf_arr)
    return float(np.interp(pwf_target, pwf_arr[order], q_arr[order]))


def test_ca1_pdf_example_with_helmy_within_2pct():
    """CA-1 (variante Helmy): q(Pwf=2214,7) ≈ 26 010 STB/d (PDF Tabla 3-5)."""
    q_arr, pwf_arr = IPRModels.vogel_kabir(**PDF_INPUTS)
    q = _q_at(q_arr, pwf_arr, 2214.7)
    assert q == pytest.approx(26010.3, rel=0.02), (
        f"q(Pwf=2214,7) = {q:.2f}, esperado 26010,3 ±2 %"
    )


def test_helmy_pi_matches_pdf():
    """J calculado por Helmy debe ser ≈ 19,98 (PDF p. 32)."""
    j = IPRModels._pi_helmy_wattenbarger(
        kx=100.0, ky=100.0, kz=10.0, h=100.0,
        a_res=2000.0, b_res=2000.0, L=1000.0, rw=0.25,
        x_w=1000.0, y_w=1000.0, z_w=50.0, mu=1.095, bo=1.278,
    )
    assert j == pytest.approx(19.98, rel=0.01)


def test_ca2_continuity_at_pb_subsaturated():
    """CA-2: con Pr>Pb, q(Pwf=Pb) = J·(Pr - Pb) exacto y curva continua."""
    inputs = dict(
        kh=100.0, kv=10.0, h=100.0, mu=2.0, bo=1.2,
        L=2000.0, reh=1500.0, rw=0.328, s=0.0,
        p_res=4000.0, pb=3000.0, steps=200,
    )
    j = IPRModels._pi_joshi(
        inputs["kh"], inputs["kv"], inputs["h"], inputs["mu"], inputs["bo"],
        inputs["L"], inputs["reh"], inputs["rw"], inputs["s"],
    )
    q_arr, pwf_arr = IPRModels.vogel_kabir(**inputs)
    q_at_pb = _q_at(q_arr, pwf_arr, 3000.0)
    assert q_at_pb == pytest.approx(j * 1000.0, rel=1e-3)


def test_ca3_q_zero_at_pres():
    """CA-3: q(Pwf=Pr) = 0 exacto."""
    inputs = dict(
        kh=100.0, kv=10.0, h=100.0, mu=2.0, bo=1.2,
        L=2000.0, reh=1500.0, rw=0.328, s=0.0,
        p_res=4000.0, pb=3000.0, steps=50,
    )
    q_arr, pwf_arr = IPRModels.vogel_kabir(**inputs)
    # El último punto del array corresponde a Pwf = p_res
    assert pwf_arr[-1] == pytest.approx(4000.0)
    assert q_arr[-1] == pytest.approx(0.0, abs=1e-6)


def test_ca4_linear_above_pb():
    """CA-4: tramo Pwf ≥ Pb es lineal con pendiente -J."""
    inputs = dict(
        kh=100.0, kv=10.0, h=100.0, mu=2.0, bo=1.2,
        L=2000.0, reh=1500.0, rw=0.328, s=0.0,
        p_res=4000.0, pb=3000.0, steps=400,
    )
    j = IPRModels._pi_joshi(
        inputs["kh"], inputs["kv"], inputs["h"], inputs["mu"], inputs["bo"],
        inputs["L"], inputs["reh"], inputs["rw"], inputs["s"],
    )
    q_arr, pwf_arr = IPRModels.vogel_kabir(**inputs)
    # Filtrar tramo monofásico (Pwf ≥ Pb)
    mask = pwf_arr >= inputs["pb"]
    pwf_lin = pwf_arr[mask]
    q_lin = q_arr[mask]
    slope, intercept = np.polyfit(pwf_lin, q_lin, 1)
    assert slope == pytest.approx(-j, rel=1e-3)
    # Coeficiente de determinación ~ 1 (linealidad perfecta)
    fit = slope * pwf_lin + intercept
    ss_res = np.sum((q_lin - fit) ** 2)
    ss_tot = np.sum((q_lin - np.mean(q_lin)) ** 2)
    r2 = 1.0 - ss_res / ss_tot if ss_tot > 0 else 1.0
    assert r2 > 0.9999


def test_saturated_case_joshi_pure_vogel():
    """Cuando Pr=Pb (saturado), la curva colapsa al Vogel puro qomax·(1-0,2r-0,8r²)."""
    inputs = dict(
        kh=100.0, kv=10.0, h=100.0, mu=2.0, bo=1.2,
        L=2000.0, reh=1500.0, rw=0.328, s=0.0,
        p_res=3000.0, pb=3000.0, steps=200,
    )
    j = IPRModels._pi_joshi(
        inputs["kh"], inputs["kv"], inputs["h"], inputs["mu"], inputs["bo"],
        inputs["L"], inputs["reh"], inputs["rw"], inputs["s"],
    )
    qomax = j * inputs["pb"] / 1.8
    q_arr, pwf_arr = IPRModels.vogel_kabir(**inputs)
    # Q at Pwf=0 debe ser qomax
    assert _q_at(q_arr, pwf_arr, 0.0) == pytest.approx(qomax, rel=1e-3)
    # En Pwf=Pb=Pr da 0
    assert _q_at(q_arr, pwf_arr, 3000.0) == pytest.approx(0.0, abs=1e-6)


def test_invalid_inputs_return_zero_array():
    """pb<=0 o p_res<=0 → arrays de ceros sin excepción."""
    q_arr, pwf_arr = IPRModels.vogel_kabir(
        kh=100.0, kv=10.0, h=100.0, mu=2.0, bo=1.2,
        L=2000.0, reh=1500.0, rw=0.328, s=0.0,
        p_res=4000.0, pb=0.0, steps=20,
    )
    assert np.all(q_arr == 0)


def test_ca5_other_horizontal_models_unchanged():
    """CA-5: los demás modelos horizontales siguen calculando sin excepción."""
    j = IPRModels.joshi(kh=100, kv=10, h=100, mu=2.0, bo=1.2, L=2000,
                       reh=1500, rw=0.328, s=0, p_res=3000)
    assert j[0].shape == (20,)
    b = IPRModels.bendakhlia_aziz(kh=100, kv=10, h=100, mu=2.0, bo=1.2, L=2000,
                                  reh=1500, rw=0.328, s=0, p_res=3000, pb=3000, rec_factor=0.05)
    assert b[0].shape == (20,)
    c = IPRModels.cheng(kh=100, kv=10, h=100, mu=2.0, bo=1.2, L=2000,
                        reh=1500, rw=0.328, s=0, p_res=3000, pb=3000, angle=90)
    assert c[0].shape == (20,)
