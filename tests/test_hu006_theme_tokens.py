"""Tests HU-006 — paleta extendida y tokens semánticos.

Cobertura:
 - CA-1: tokens semánticos expuestos por `get_colors()` en ambos modos.
 - CA-2: ambos modos (claro y oscuro) tienen valores coherentes.
 - CA-3: `IPR_PALETTE` y `IPR_MODEL_COLORS` accesibles y bien formados.
 - CA-4: contraste texto/fondo ≥ 4,5:1 (WCAG AA) en ambos modos.
"""
import os
import sys
import re

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from ui.styles import VioletTheme, IPR_PALETTE, IPR_MODEL_COLORS  # noqa: E402


REQUIRED_SEMANTIC_TOKENS = [
    "SURFACE", "SURFACE_ALT", "BORDER",
    "TEXT_MUTED", "TEXT_ON_PRIMARY",
    "PRIMARY", "PRIMARY_HOVER", "PRIMARY_SOFT",
    "SECONDARY", "SECONDARY_HOVER",
    "SUCCESS", "WARNING", "DANGER", "INFO",
    "ENTRY_BORDER",
]

# Claves originales que deben seguir presentes para backward-compat.
BACKCOMPAT_TOKENS = [
    "BG_COLOR", "FRAME_BG", "HEADER_COLOR",
    "BTN_COLOR", "BTN_HOVER", "TEXT_COLOR", "ENTRY_BG",
]


def _hex_to_rgb(h):
    h = h.lstrip("#")
    return tuple(int(h[i : i + 2], 16) for i in (0, 2, 4))


def _relative_luminance(rgb):
    def chan(c):
        c /= 255.0
        return c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4
    r, g, b = (chan(c) for c in rgb)
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def _contrast_ratio(hex_a, hex_b):
    la = _relative_luminance(_hex_to_rgb(hex_a))
    lb = _relative_luminance(_hex_to_rgb(hex_b))
    lighter, darker = max(la, lb), min(la, lb)
    return (lighter + 0.05) / (darker + 0.05)


# ── CA-1: tokens semánticos presentes ──────────────────────────────────────
@pytest.mark.parametrize("mode", ["light", "dark"])
def test_ca1_semantic_tokens_present(mode):
    VioletTheme._mode = mode
    c = VioletTheme.get_colors()
    for tok in REQUIRED_SEMANTIC_TOKENS:
        assert tok in c, f"Falta token semántico '{tok}' en modo {mode}"


@pytest.mark.parametrize("mode", ["light", "dark"])
def test_backward_compat_tokens_present(mode):
    """Los tokens originales (BG_COLOR, etc.) deben seguir disponibles."""
    VioletTheme._mode = mode
    c = VioletTheme.get_colors()
    for tok in BACKCOMPAT_TOKENS:
        assert tok in c, f"Token original '{tok}' desaparecido en modo {mode}"


# ── CA-2: ambos modos tienen valores válidos ───────────────────────────────
HEX_RE = re.compile(r"^#[0-9A-Fa-f]{6}$")


@pytest.mark.parametrize("mode", ["light", "dark"])
def test_ca2_all_tokens_are_valid_hex(mode):
    VioletTheme._mode = mode
    c = VioletTheme.get_colors()
    for k, v in c.items():
        assert HEX_RE.match(v), f"Token {k}={v} no es un color hex válido"


# ── CA-3: paleta y mapeo de modelos ────────────────────────────────────────
def test_ca3_ipr_palette_has_at_least_11_distinct_colors():
    """Hay 11 modelos IPR (5 verticales + 6 horizontales) — paleta cubre todos."""
    assert len(IPR_PALETTE) >= 11
    assert len(set(IPR_PALETTE)) == len(IPR_PALETTE), "IPR_PALETTE tiene colores repetidos"


def test_ca3_ipr_model_colors_covers_all_models():
    """`IPR_MODEL_COLORS` mapea cada modelo del Combobox a un color de la paleta."""
    expected_models = {
        "Vogel (Subsaturado)", "Fetkovich-gas", "Wiggins",
        "Darcy (Semi-Estacionario)", "Brown",
        "Joshi Horizontal", "Babu y Odeh", "Vogel Modificado (Kabir)",
        "Economides y Retnanto", "Bendakhlia y Aziz", "Cheng",
    }
    assert set(IPR_MODEL_COLORS) == expected_models, \
        f"IPR_MODEL_COLORS no cubre todos los modelos: {expected_models - set(IPR_MODEL_COLORS)}"
    for model, color in IPR_MODEL_COLORS.items():
        assert color in IPR_PALETTE, f"{model} usa {color} fuera de IPR_PALETTE"


def test_ca3_ipr_model_colors_are_unique():
    """Cada modelo recibe un color distinto para evitar curvas confundidas."""
    colors = list(IPR_MODEL_COLORS.values())
    assert len(set(colors)) == len(colors), \
        f"Colores repetidos en IPR_MODEL_COLORS: {colors}"


# ── CA-4: contraste WCAG AA ≥ 4.5:1 ─────────────────────────────────────────
@pytest.mark.parametrize("mode", ["light", "dark"])
def test_ca4_text_on_bg_contrast_meets_wcag_aa(mode):
    """Texto principal sobre fondo cumple WCAG AA (≥ 4,5:1)."""
    VioletTheme._mode = mode
    c = VioletTheme.get_colors()
    ratio = _contrast_ratio(c["TEXT_COLOR"], c["BG_COLOR"])
    assert ratio >= 4.5, f"Contraste {mode} = {ratio:.2f}:1 < 4.5:1 (WCAG AA)"


@pytest.mark.parametrize("mode", ["light", "dark"])
def test_ca4_text_on_surface_contrast_meets_wcag_aa(mode):
    """Texto sobre SURFACE (popups, cards) cumple WCAG AA."""
    VioletTheme._mode = mode
    c = VioletTheme.get_colors()
    ratio = _contrast_ratio(c["TEXT_COLOR"], c["SURFACE"])
    assert ratio >= 4.5, f"Contraste TEXT_COLOR/SURFACE {mode} = {ratio:.2f}:1 < 4.5:1"


@pytest.mark.parametrize("mode", ["light", "dark"])
def test_ca4_text_on_primary_contrast_meets_wcag_aa(mode):
    """Texto sobre PRIMARY (botones) cumple WCAG AA."""
    VioletTheme._mode = mode
    c = VioletTheme.get_colors()
    ratio = _contrast_ratio(c["TEXT_ON_PRIMARY"], c["PRIMARY"])
    assert ratio >= 4.5, f"Contraste {mode} TEXT_ON_PRIMARY/PRIMARY = {ratio:.2f}:1 < 4.5:1"


# Reset al estado por defecto tras los tests (dark) — evita side-effects globales.
def teardown_module(module):
    VioletTheme._mode = "dark"
