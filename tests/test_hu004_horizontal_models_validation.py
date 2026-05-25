"""Tests HU-004 — Validación numérica de los 4 modelos horizontales contra el
ejemplo del MODULO III sec. 3.2.7 (pp. 30-34, Tabla 3-5).

Decisiones de tolerancia (revisadas con el usuario en sesión 2026-05-25):
 - **Joshi**: aceptado como 15,26 STB/d/psi para los inputs PDF; rango ampliado
   a [15, 24] respecto a la HU original ([17, 24]). El gap vs Helmy-Wattenbarger
   (19,98) es propio de las dos correlaciones, no un bug — ver HU-002 para PI
   Helmy alternativo.
 - **Babu-Odeh**: marcado EXPERIMENTAL en docstring; se verifica que ejecuta sin
   excepciones pero no se exige el rango [17, 24]. Auditoría profunda en HU-007.
 - **Cheng**: valida contra Ec. 3-32 canónica con coeficientes de Tabla 3-1
   directamente. La PDF Tabla 3-5 fila Cheng presenta inconsistencia interna
   (resultado 17 857 STB/d no es reproducible por la fórmula sustituida en p.34).
 - **Bendakhlia-Aziz**: ±5 % vs Tabla 3-5 — pasa nativamente con < 1 % error.
"""
import os
import sys

import numpy as np
import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from logic.ipr_models import IPRModels  # noqa: E402


# Inputs comunes del ejemplo PDF p. 30
PR = 3814.7
PB = 3814.7
PWF_TEST = 2214.7
QOMAX_PDF = 42345.7


def _q_at(q, p, target):
    order = np.argsort(p)
    return float(np.interp(target, p[order], q[order]))


# ── CA-2 — Joshi ────────────────────────────────────────────────────────────
def test_ca2_joshi_pi_within_widened_range():
    """Joshi 1991 con inputs PDF entrega J ∈ [15, 24]."""
    q, p = IPRModels.joshi(
        kh=100, kv=10, h=100, mu=1.095, bo=1.278,
        L=1000, reh=1128, rw=0.25, s=0, p_res=PR, steps=400,
    )
    j = (q[1] - q[0]) / (p[0] - p[1])
    assert 15.0 <= j <= 24.0, f"J(Joshi) = {j:.3f} fuera de [15, 24]"
    # Pin: Joshi puro para los inputs PDF entrega 15,26 ± 0,1
    assert j == pytest.approx(15.26, abs=0.10)


# ── CA-3 — Babu-Odeh (auditado en HU-007: ya no es experimental) ──────────
def test_ca3_babu_odeh_runs_without_exception():
    """Babu-Odeh ejecuta sin excepciones para los inputs PDF.

    Nota: tras HU-007 la implementación fue auditada y la etiqueta EXPERIMENTAL
    fue removida; el test específico de [17, 22] está en
    `tests/test_hu007_babu_odeh.py::test_ca1_babu_odeh_pi_in_target_range`.
    """
    q, p = IPRModels.babu_odeh(
        kx=100, ky=100, kz=10, h=100, a_res=2000, b_res=2000,
        mu=1.095, bo=1.278, L=1000, rw=0.25,
        x_mid=1000, y_0=1000, z_0=50, s_res=0, p_res=PR, steps=20,
    )
    assert q.shape == (20,)
    assert np.all(np.isfinite(q))


# ── CA-4 — Cheng validado contra Ec. 3-32 canónica ──────────────────────────
def test_ca4_cheng_matches_canonical_equation():
    """Cheng @ 90° reproduce Ec. 3-32 con coeficientes Tabla 3-1 byte-a-byte."""
    q, p = IPRModels.cheng(q_max=QOMAX_PDF, p_res=PR, angle=90, steps=400)
    q_code = _q_at(q, p, PWF_TEST)

    # Fórmula canónica Ec. 3-32 + Tabla 3-1 fila 90° (a0=0,9885, a1=-0,2055, a2=1,1818)
    r = PWF_TEST / PR
    expected_canonical = QOMAX_PDF * (0.9885 - 0.2055 * r - 1.1818 * r ** 2)
    assert q_code == pytest.approx(expected_canonical, rel=1e-4), (
        f"q={q_code:.2f}, esperado canónico {expected_canonical:.2f}"
    )

    # PDF Tabla 3-5 dice 17 857 — registrado como inconsistencia del PDF:
    # la fórmula 0,9885 + (-0,2055)·0,58057 - 1,1818·0,58057² = 0,4709 → 19 938,6
    # cualquier permutación de signos da 0,7095 o 0,4709, nunca 0,4217.
    # Por ello validamos contra la fórmula canónica, no contra Tabla 3-5.
    assert q_code == pytest.approx(19938.6, abs=2.0), \
        f"Resultado canónico esperado ≈ 19 938,6; obtenido {q_code:.2f}"


# ── CA-5 — Bendakhlia-Aziz ─────────────────────────────────────────────────
def test_ca5_bendakhlia_aziz_within_5pct_of_pdf():
    """Bendakhlia-Aziz con rec_factor=0,05 entrega q(Pwf=2214,7) ≈ 27 580 STB/d (±5 %)."""
    q, p = IPRModels.bendakhlia_aziz(
        q_max=QOMAX_PDF, p_res=PR, rec_factor=0.05, steps=400,
    )
    q_code = _q_at(q, p, PWF_TEST)
    assert q_code == pytest.approx(27579.8, rel=0.05), (
        f"q(Pwf=2214,7) = {q_code:.2f}, esperado 27 579,8 ±5 %"
    )


# ── Coverage adicional: que los docstrings citen documentación ─────────────
def test_docstrings_cite_documentation_reference():
    """Los 4 modelos horizontales tienen referencia documental en su docstring.

    Joshi, Cheng y Bendakhlia-Aziz citan MODULO III; Babu-Odeh (tras la auditoría
    de HU-007) cita el paper original Babu & Odeh 1989 directamente.
    """
    for fn in [IPRModels.joshi, IPRModels.cheng, IPRModels.bendakhlia_aziz]:
        assert "MODULO III" in (fn.__doc__ or ""), f"{fn.__name__} sin ref MODULO III"
    bo_doc = IPRModels.babu_odeh.__doc__ or ""
    assert "Babu" in bo_doc and "1989" in bo_doc, \
        "babu_odeh sin ref al paper original Babu & Odeh 1989"


# ── Cheng — verificación adicional contra Tabla 3-1 fila por fila ──────────
@pytest.mark.parametrize("angle, a0, a1, a2", [
    (0,  1.0,    0.2,    0.8),
    (15, 0.9998, 0.221,  0.7783),
    (30, 0.9969, 0.1254, 0.8582),
    (45, 0.9946, 0.0221, 0.9663),
    (60, 0.9926, -0.0549, 1.0395),
    (75, 0.9915, -0.1002, 1.0829),
    (85, 0.9915, -0.112,  1.0942),
    (90, 0.9885, -0.2055, 1.1818),
])
def test_cheng_table_3_1_coefficients(angle, a0, a1, a2):
    """Tabla 3-1 (Cheng) bien transcrita: q(Pwf=Pr/2) coincide con cálculo manual."""
    q, p = IPRModels.cheng(q_max=1000.0, p_res=3000.0, angle=angle, steps=400)
    pwf = 1500.0
    q_at_pwf = _q_at(q, p, pwf)
    r = 0.5
    expected = 1000.0 * (a0 + a1 * r - a2 * r ** 2)
    assert q_at_pwf == pytest.approx(expected, rel=1e-3)
