"""Tests HU-005 — Validación numérica de los 5 modelos verticales.

Cobertura:
 - Vogel Subsaturado (Ec. 2-33 / 2-35, MODULO II pp. 33-40)
 - Darcy (Ec. 2-14, MODULO II p. 9)
 - Fetkovich (Ec. 2-54, MODULO II p. 56)
 - Wiggins (1994, generalizado a Pr > Pb)
 - Brown (Vogel + WOR constante)

Nota sobre CA-2 de la HU original:
La HU expone "Darcy con k=50, h=30, μ=1.5, Bo=1.2, re=1000, rw=0.328, s=0,
Pr=3000 entrega J ≈ 0,206 STB/d/psi". Ese valor es **erróneo** — un factor
de 4 abajo. La Ec. 2-14 con esos inputs entrega J ≈ 0,811 STB/d/psi
(0.00708·50·30 / (1.5·1.2·ln(0.472·1000/0.328)) = 10.62 / 13.09 = 0.811).
Documentado en la bitácora de PROGRESO.md.
"""
import math
import os
import sys

import numpy as np
import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from logic.ipr_models import IPRModels  # noqa: E402


def _q_at(q, p, target):
    order = np.argsort(p)
    return float(np.interp(target, p[order], q[order]))


# ── CA-1: Vogel Subsaturado caso saturado simple ──────────────────────────
def test_ca1_vogel_subsaturado_saturated_case():
    """Pr=Pb=3000, J=1,5, Pwf=1500 → q = (J·Pb/1.8)·(1 - 0.1 - 0.2) = 1750 STB/d."""
    q, p = IPRModels.vogel_subsaturado(p_res=3000, pb=3000, j_index=1.5, steps=400)
    q_at_1500 = _q_at(q, p, 1500)
    assert q_at_1500 == pytest.approx(1750.0, rel=1e-3)


def test_vogel_subsaturado_example_2_2_modulo_ii():
    """Ejemplo 2-2 MODULO II p. 39: Pr=Pb=2085, J tal que AOF=1097 → q(Pwf=1485) ≈ 496."""
    # qomax_PDF = 1097 STB/d → J = 1097·1.8/2085 = 0,9474
    j = 1097.0 * 1.8 / 2085.0
    q, p = IPRModels.vogel_subsaturado(p_res=2085, pb=2085, j_index=j, steps=400)
    q_at_1485 = _q_at(q, p, 1485)
    assert q_at_1485 == pytest.approx(496.0, abs=1.0), \
        f"q={q_at_1485:.2f}, esperado 496 (PDF Tabla 2-4)"


def test_vogel_subsaturado_continuity_at_pb():
    """Continuidad en Pwf=Pb para caso subsaturado: q debe coincidir con J·(Pr-Pb)."""
    q, p = IPRModels.vogel_subsaturado(p_res=4000, pb=3000, j_index=1.5, steps=400)
    q_at_pb = _q_at(q, p, 3000)
    assert q_at_pb == pytest.approx(1.5 * 1000.0, rel=1e-3)


# ── CA-2: Darcy ────────────────────────────────────────────────────────────
def test_ca2_darcy_pi_matches_eq_2_14():
    """Darcy con k=50, h=30, μ=1.5, B=1.2, re=1000, rw=0.328, s=0
    entrega J = 0.811 STB/d/psi (Ec. 2-14 MODULO II p. 9).
    """
    q, p = IPRModels.darcy(
        k=50, h=30, mu=1.5, bo=1.2, re=1000, rw=0.328, s=0, p_res=3000, steps=400,
    )
    J_code = (q[1] - q[0]) / (p[0] - p[1])
    # Cálculo manual Ec. 2-14:
    J_manual = 0.00708 * 50 * 30 / (1.5 * 1.2 * math.log(0.472 * 1000 / 0.328))
    assert J_code == pytest.approx(J_manual, rel=1e-3)
    assert 0.80 < J_code < 0.82, \
        f"J(Darcy) = {J_code:.4f} fuera de [0.80, 0.82] esperado por Ec. 2-14"


# ── CA-3: Brown ────────────────────────────────────────────────────────────
def test_ca3_brown_wc20_equals_qo_times_1_25():
    """Brown con WC=20 % cumple qt = qo·(1 + 20/80) = qo·1.25 en cada punto."""
    q, p = IPRModels.brown(p_res=3000, pb=3000, j_index=0.9, w_cut=20, steps=400)
    # qo de Vogel saturado con qmax=1500
    r = p / 3000.0
    qo_pure = 1500.0 * (1 - 0.2 * r - 0.8 * r ** 2)
    qt_expected = np.maximum(qo_pure * 1.25, 0.0)
    np.testing.assert_allclose(q, qt_expected, atol=1e-6)
    # AOF a Pwf=0: 1875 STB/d
    assert _q_at(q, p, 0) == pytest.approx(1875.0, rel=1e-3)


def test_brown_zero_water_cut_equals_vogel():
    """Brown con WC=0 reduce a Vogel saturado puro."""
    q_brown, p = IPRModels.brown(p_res=3000, pb=3000, j_index=0.9, w_cut=0, steps=400)
    r = p / 3000.0
    q_vogel = np.maximum(1500.0 * (1 - 0.2 * r - 0.8 * r ** 2), 0.0)
    np.testing.assert_allclose(q_brown, q_vogel, atol=1e-6)


# ── CA-4: sin NaN/inf en rangos físicos ────────────────────────────────────
@pytest.mark.parametrize("name, qp", [
    ("Fetkovich",  lambda: IPRModels.fetkovich(C=0.5, n=1.0, p_res=3000, steps=200)),
    ("Wiggins",    lambda: IPRModels.wiggins(p_res=4000, pb=3000, j_index=1.5, steps=200)),
    ("Darcy",      lambda: IPRModels.darcy(k=50, h=30, mu=1.5, bo=1.2, re=1000, rw=0.328, s=0, p_res=3000, steps=200)),
    ("VogelSub",   lambda: IPRModels.vogel_subsaturado(p_res=4000, pb=3000, j_index=1.5, steps=200)),
    ("Brown",      lambda: IPRModels.brown(p_res=3000, pb=3000, j_index=0.9, w_cut=20, steps=200)),
])
def test_ca4_no_nan_or_inf(name, qp):
    """Los 5 modelos verticales no producen NaN/inf con inputs por defecto del UI."""
    q, p = qp()
    assert np.all(np.isfinite(q)), f"{name} contiene NaN/inf en el array de caudales"
    assert np.all(np.isfinite(p)), f"{name} contiene NaN/inf en el array de presiones"
    assert np.all(q >= 0), f"{name} contiene caudales negativos sin clampear"


# ── CA-5: docstrings con referencia documental ─────────────────────────────
def test_ca5_docstrings_cite_documentation():
    """Los 5 modelos verticales tienen docstring con ref. MODULO II o Wiggins/Brown explícito."""
    for fn in [IPRModels.darcy, IPRModels.fetkovich, IPRModels.vogel_subsaturado]:
        assert "MODULO II" in (fn.__doc__ or ""), f"{fn.__name__} sin ref MODULO II"
    for fn in [IPRModels.wiggins, IPRModels.brown]:
        # Wiggins y Brown no están en MODULO II — documentan su origen
        doc = fn.__doc__ or ""
        assert "MODULO II" in doc or "Wiggins" in doc or "Brown" in doc, \
            f"{fn.__name__} sin referencia documental"


# ── Wiggins — continuidad y derivada ───────────────────────────────────────
def test_wiggins_continuity_at_pb_subsaturated():
    """Wiggins en Pwf=Pb (subsaturado): q debe coincidir con J·(Pr-Pb)."""
    q, p = IPRModels.wiggins(p_res=4000, pb=3000, j_index=1.5, steps=400)
    q_at_pb = _q_at(q, p, 3000)
    assert q_at_pb == pytest.approx(1.5 * 1000.0, rel=1e-3)


# ── Fetkovich — caso lineal n=1 ────────────────────────────────────────────
def test_fetkovich_n_equals_1():
    """Fetkovich con n=1 da q = C·(Pr² - Pwf²) — verificación analítica."""
    q, p = IPRModels.fetkovich(C=0.5, n=1.0, p_res=3000, steps=400)
    q_at_0 = _q_at(q, p, 0)
    # AOF = C·Pr² = 0.5·9_000_000 = 4_500_000
    assert q_at_0 == pytest.approx(4_500_000.0, rel=1e-3)
