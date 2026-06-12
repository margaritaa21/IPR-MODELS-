"""Tests para HU-001 — Economides–Retnanto.

Verifica la fórmula corregida contra el ejemplo del PDF
``DOCS/MODULO III - IPR DE POZOS HORIZONTALES_unlocked.pdf``,
sección 3.2.7, pp. 30-33 (Tabla 3-5).
"""
import os
import sys
import warnings

import numpy as np
import pytest

# Permite ejecutar `pytest` desde la raíz del proyecto sin instalar el paquete.
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from logic.ipr_models import IPRModels  # noqa: E402


def _q_at_pwf(q_arr, pwf_arr, pwf_target):
    """Interpola q en un Pwf objetivo a partir de los arrays retornados."""
    order = np.argsort(pwf_arr)
    return float(np.interp(pwf_target, pwf_arr[order], q_arr[order]))


def test_ca1_pdf_reference_case_within_2pct():
    """CA-1: Pr=Pb=3814,7 ; Pwf=2214,7 ; qmax=42345,7 → q≈27473,9 STB/d."""
    q_arr, pwf_arr = IPRModels.economides_retnanto(
        kh=100.0, kv=10.0, h=100.0, mu=1.095, bo=1.278,
        L=1000.0, reh=1128.0, rw=0.25, s=0.0,
        p_res=3814.7, pb=3814.7, pi_source="helmy",
        kx=100.0, ky=100.0, kz=10.0,
        a_res=2000.0, b_res=2000.0,
        x_w=1000.0, y_w=1000.0, z_w=50.0,
        steps=400,
    )
    q_at_pwf = _q_at_pwf(q_arr, pwf_arr, 2214.7)
    assert q_at_pwf == pytest.approx(27473.9, rel=0.02), (
        f"q(Pwf=2214,7) = {q_at_pwf:.2f}, esperado 27473.9 ±2 %"
    )


def test_ca1_n_param_matches_pdf():
    """n calculado para Pr=Pb=3814,7 debe ser ≈ 2,376 (PDF p. 33)."""
    pr = pb = 3814.7
    ratio_rb = pr / pb
    n_param = (-0.27 + 1.46 * ratio_rb - 0.96 * (ratio_rb ** 2)) \
              * (4.0 + 1.66e-3 * pb)
    assert n_param == pytest.approx(2.376, abs=0.01)


def test_ca2_curve_between_vogel_and_bendakhlia():
    """CA-2: A Pwf = 2214,7, q_Economides ∈ [q_Vogel, q_Bendakhlia]
    para los inputs saturados del ejemplo PDF."""
    qmax_inputs = dict(
        kh=100.0, kv=10.0, h=100.0, mu=1.095, bo=1.278,
        L=1000.0, reh=1128.0, rw=0.25, s=0.0,
        p_res=3814.7, pb=3814.7, pi_source="helmy",
        kx=100.0, ky=100.0, kz=10.0,
        a_res=2000.0, b_res=2000.0,
        x_w=1000.0, y_w=1000.0, z_w=50.0,
        steps=400
    )

    q_er, pwf_er = IPRModels.economides_retnanto(**qmax_inputs)
    q_ba, pwf_ba = IPRModels.bendakhlia_aziz(rec_factor=0.05, **qmax_inputs)
    q_er_v = _q_at_pwf(q_er, pwf_er, 2214.7)
    q_ba_v = _q_at_pwf(q_ba, pwf_ba, 2214.7)

    # Vogel modificado bifásico: qo/qo_max = 1 - 0,2·r - 0,8·r²
    r = 2214.7 / 3814.7
    q_vogel = 42345.7 * (1 - 0.2 * r - 0.8 * r * r)

    assert q_vogel < q_er_v < q_ba_v + 1e-6, (
        f"Esperado q_Vogel ({q_vogel:.1f}) < q_ER ({q_er_v:.1f}) ≤ "
        f"q_Bendakhlia ({q_ba_v:.1f})"
    )


def test_ca3_warning_out_of_range_when_pr_gt_pb():
    """CA-3: Pr > Pb produce n<1 → debe emitirse UserWarning y NO crashear."""
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always", UserWarning)
        q_arr, pwf_arr = IPRModels.economides_retnanto(
            kh=100.0, kv=10.0, h=100.0, mu=2.0, bo=1.2, L=2000.0,
            reh=1500.0, rw=0.328, s=0.0, p_res=4000.0, pb=3000.0, steps=20,
        )

    messages = [str(w.message) for w in caught
                if issubclass(w.category, UserWarning)]
    assert any("n =" in m and "< 1" in m for m in messages), (
        f"Esperado warning de n<1, recibidos: {messages}"
    )
    assert q_arr.shape == (20,) and pwf_arr.shape == (20,)


def test_ca4_default_ui_inputs_no_nan_no_inf():
    """CA-4: Defaults de UI (Pr=4000, Pb=3000) → sin NaN/inf."""
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        q_arr, pwf_arr = IPRModels.economides_retnanto(
            kh=100.0, kv=10.0, h=100.0, mu=2.0, bo=1.2, L=2000.0,
            reh=1500.0, rw=0.328, s=0.0, p_res=4000.0, pb=3000.0, steps=50,
        )
    assert not np.any(np.isnan(q_arr)), "La curva contiene NaN"
    assert not np.any(np.isinf(q_arr)), "La curva contiene inf"
    assert np.all(q_arr >= 0), "La curva tiene valores negativos sin clampear"


def test_invalid_inputs_return_zero_array():
    """pb<=0 / J<=0 / p_res<=0 → arrays cero + warning."""
    for kwargs in [
        dict(kh=100.0, kv=10.0, h=100.0, mu=2.0, bo=1.2, L=2000.0, reh=1500.0, rw=0.328, s=0.0, p_res=4000.0, pb=0.0),
        dict(kh=0.0, kv=10.0, h=100.0, mu=2.0, bo=1.2, L=2000.0, reh=1500.0, rw=0.328, s=0.0, p_res=4000.0, pb=3000.0),
        dict(kh=100.0, kv=10.0, h=100.0, mu=2.0, bo=1.2, L=2000.0, reh=1500.0, rw=0.328, s=0.0, p_res=0.0, pb=3000.0),
    ]:
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always", UserWarning)
            q_arr, pwf_arr = IPRModels.economides_retnanto(steps=10, **kwargs)
        assert np.all(q_arr == 0), f"Esperado ceros para inputs {kwargs}"
        assert any(issubclass(w.category, UserWarning) for w in caught), \
            f"Esperado warning para inputs {kwargs}"

