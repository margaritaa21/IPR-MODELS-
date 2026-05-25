import warnings

import numpy as np

class IPRModels:
    """
    Generación de curvas IPR (Inflow Performance Relationship).
    Retorna tuplas (caudales, presiones) para graficar.
    """

    # El modelo Vogel clásico se eliminó según petición (se mantiene solo Vogel Subsaturado)

    @staticmethod
    def darcy(k, h, mu, bo, re, rw, s, p_res, steps=20):
        """Darcy radial — estado pseudo-estable (Pr constante).

        Ec. 2-14 (MODULO II p. 9):
            q = 0.00708·k·h·(P_R - P_wf) / [μ·B·(ln(0.472·re/rw) + s)]
        Implementación equivalente: ln(0.472·re/rw) = ln(re/rw) + ln(0.472)
        ≈ ln(re/rw) - 0.7507. Por convención de campo se aproxima como
        ``ln(re/rw) - 0.75 + s``.

        Inputs:
            k (md), h (ft), μ (cp), Bo (rb/STB), re (ft), rw (ft),
            s (skin adimensional), Pr (psi).

        Ref: DOCS/MODULO II - DESEMPEÑO DEL YACIMIENTO_unlocked.pdf, pp. 8-9.
        """
        pwf_values = np.linspace(0, p_res, steps)
        q_values = []
        
        # Validación básica para evitar división por cero
        if mu <= 0 or bo <= 0 or re <= rw:
            return np.zeros(steps), pwf_values
        
        # Constante J (Índice de Productividad)
        # Q = J * (Pr - Pwf)
        # J = (0.00708 * k * h) / (mu * Bo * (ln(re/rw) - 0.75 + S))
        
        try:
            denom = mu * bo * (np.log(re/rw) - 0.75 + s)
            if denom == 0: denom = 1e-6
            j_index = (0.00708 * k * h) / denom
        except Exception:
            j_index = 0

        for pwf in pwf_values:
            q = j_index * (p_res - pwf)
            q_values.append(max(0, q))
            
        return np.array(q_values), pwf_values

    @staticmethod
    def fetkovich(C, n, p_res, steps=20):
        """Fetkovich (1973) — IPR de pozos de gas / aceite con efecto de turbulencia.

        Ec. 2-54 (MODULO II p. 56):
            q = C · (Pr² - Pwf²)^n
        ``n`` varía entre 0.5 y 1; ``C`` en unidades de campo Mscf/d/psi²ⁿ
        (gas) o STB/d/psi²ⁿ (aceite).

        Ref: DOCS/MODULO II - DESEMPEÑO DEL YACIMIENTO_unlocked.pdf, pp. 55-58.
        """
        pwf_values = np.linspace(0, p_res, steps)
        q_values = []
        
        for pwf in pwf_values:
            term = (p_res ** 2) - (pwf ** 2)
            if term < 0: term = 0
            q = C * (term ** n)
            q_values.append(q)
            
        return np.array(q_values), pwf_values

    @staticmethod
    def wiggins(p_res, pb, j_index, steps=20):
        """Wiggins (1994) — IPR bifásico para crudos volátiles, generalizado a Pr > Pb.

        - Tramo monofásico (Pwf ≥ Pb): q = J·(Pr - Pwf).
        - Tramo bifásico (Pwf < Pb):   q = qb + (J·Pb/1.48)·(1 - 0.52·r - 0.48·r²),
          con r = Pwf/Pb y qb = J·(Pr - Pb).

        El qomax bifásico (J·Pb/1.48) y la pendiente continua en Pb se derivan
        igualando dq/dPwf|_(Pwf=Pb) = -J (mismo procedimiento que Vogel-Sub).

        Wiggins (1994) NO aparece en MODULO II ni MODULO III; referencia
        original: Wiggins, M. L., *"Generalized Inflow Performance Relationships
        for Three-Phase Flow"*, SPE Reservoir Engineering, Aug 1994.
        """
        pwf_values = np.linspace(0, p_res, steps)
        q_values = []
        qb = j_index * (p_res - pb) if p_res > pb else 0
        for pwf in pwf_values:
            if pwf >= pb:
                q = j_index * (p_res - pwf)
            else:
                ratio = pwf / pb if pb > 0 else 0
                q = qb + (j_index * pb / 1.48) * (1 - 0.52 * ratio - 0.48 * (ratio**2))
            q_values.append(max(0, q))
        return np.array(q_values), pwf_values

    # ================= NUEVOS MODELOS VERTICALES =================

    @staticmethod
    def economides_retnanto(q_max, p_res, pb, steps=20):
        """Correlación de Retnanto y Economides (1998) para IPR bifásico en pozos horizontales.

        Ec. 3-33: qo/qo,max = 1 - 0.25*(Pwf/Pr) - 0.75*(Pwf/Pr)^n
        Ec. 3-34: n = (-0.27 + 1.46*(Pr/Pb) - 0.96*(Pr/Pb)^2) * (4 + 1.66e-3*Pb)

        Ref: DOCS/MODULO III - IPR DE POZOS HORIZONTALES, pp. 21-24
        (Tabla 3-3 y Figura 3-8 acotan el rango físico de n).

        Emite ``warnings.UserWarning`` si los inputs caen fuera del rango
        del modelo (Pr > Pb subsaturado, o n < 1).
        """
        pwf_values = np.linspace(0, p_res, steps)

        if pb <= 0 or p_res <= 0 or q_max <= 0:
            warnings.warn(
                "Economides–Retnanto requiere Pr, Pb y q_max estrictamente positivos.",
                UserWarning, stacklevel=2,
            )
            return np.zeros(steps), pwf_values

        ratio_rb = p_res / pb
        n_param = (-0.27 + 1.46 * ratio_rb - 0.96 * (ratio_rb ** 2)) \
                  * (4.0 + 1.66e-3 * pb)

        if p_res > pb:
            warnings.warn(
                "Economides–Retnanto está formulado para reservorios saturados "
                "(Pr ≤ Pb). El resultado puede no ser físico "
                "(MODULO III, sec. 3.2.4).",
                UserWarning, stacklevel=2,
            )
        if n_param < 1.0:
            warnings.warn(
                f"Economides–Retnanto: n = {n_param:.3f} < 1 — fuera del rango "
                "de validez del modelo (Tabla 3-3 / Figura 3-8 del MODULO III).",
                UserWarning, stacklevel=2,
            )

        q_values = []
        for pwf in pwf_values:
            r = pwf / p_res
            # Evita 0**(n<0) = inf cuando la curva parte de Pwf = 0.
            if n_param < 0 and r == 0.0:
                r_n = 0.0
            else:
                r_n = r ** n_param
            q = q_max * (1.0 - 0.25 * r - 0.75 * r_n)
            q_values.append(max(0.0, q))
        return np.array(q_values), pwf_values

    @staticmethod
    def vogel_subsaturado(p_res, pb, j_index, steps=20):
        """Vogel generalizado para reservorios subsaturados (Pr ≥ Pb).

        Ec. 2-35 (MODULO II p. 39):
        - Pwf ≥ Pb (monofásico):  q = J·(Pr - Pwf).
        - Pwf < Pb (bifásico):    q = qb + (J·Pb/1.8)·(1 - 0.2·(Pwf/Pb) - 0.8·(Pwf/Pb)²)
          con qb = J·(Pr - Pb).

        Caso saturado (Pr = Pb): qb = 0, formula colapsa al Vogel original
        (Ec. 2-33 con qomax = J·Pb/1.8).

        Ref: DOCS/MODULO II - DESEMPEÑO DEL YACIMIENTO_unlocked.pdf, pp. 33-40
        (Ec. 2-33, 2-35).
        """
        pwf_values = np.linspace(0, p_res, steps)
        q_values = []
        qb = j_index * (p_res - pb) if p_res > pb else 0
        for pwf in pwf_values:
            if pwf >= pb:
                q = j_index * (p_res - pwf)
            else:
                ratio = pwf / pb if pb > 0 else 0
                q = qb + (j_index * pb / 1.8) * (1 - 0.2 * ratio - 0.8 * (ratio**2))
            q_values.append(max(0, q))
        return np.array(q_values), pwf_values

    @staticmethod
    def brown(q_max_o, p_res, w_cut, steps=20):
        """Brown — IPR de aceite + agua con corte de agua constante.

        Aceite por Vogel saturado: qo = q_max_o·(1 - 0.2·(Pwf/Pr) - 0.8·(Pwf/Pr)²).
        Agua proporcional al corte: qw = (WC/(100-WC))·qo  → qt = qo + qw.

        Asunción: el corte de agua se asume **constante** en toda la curva
        (simplificación; en realidad WC varía con la presión). Para WC=20 %
        cada punto cumple qt = qo·1.25.

        Brown's Method no aparece en MODULO II ni MODULO III; modelo
        propio del proyecto basado en la generalización clásica de Vogel
        con WOR constante.
        """
        pwf_values = np.linspace(0, p_res, steps)
        q_values = []
        for pwf in pwf_values:
            ratio = pwf / p_res
            qo = q_max_o * (1 - 0.2 * ratio - 0.8 * (ratio ** 2))
            # Aproximación lineal para el agua basada en el water cut a Qmax
            qw = (w_cut / (100 - w_cut)) * qo if w_cut < 100 else 0
            q_values.append(max(0, qo + qw))
        return np.array(q_values), pwf_values

    # ================= NUEVOS MODELOS HORIZONTALES =================

    @staticmethod
    def cheng(q_max, p_res, angle, steps=20):
        """Cheng (1990) — IPR para pozo desviado u horizontal (sec. 3.2.3).

        Ec. 3-32:  qo/qo,max = a0 + a1·(Pwf/Pr) - a2·(Pwf/Pr)²
        con a0, a1, a2 interpolados de la Tabla 3-1 según el ángulo de
        inclinación (0° = vertical, 90° = horizontal).

        Ref: DOCS/MODULO III - IPR DE POZOS HORIZONTALES, pp. 18-21
        (Tabla 3-1). Nota: el ejemplo del PDF p. 34 contiene una incoherencia
        interna (sustituye a1 con signo invertido y entrega un resultado
        numérico no reproducible por la propia fórmula); esta implementación
        respeta la Ec. 3-32 canónica con los signos de Tabla 3-1.
        """
        pwf_values = np.linspace(0, p_res, steps)
        q_values = []

        # Tabla 3-1: Constantes de Cheng
        angles = np.array([0, 15, 30, 45, 60, 75, 85, 90])
        a0_vals = np.array([1, 0.9998, 0.9969, 0.9946, 0.9926, 0.9915, 0.9915, 0.9885])
        a1_vals = np.array([0.2, 0.221, 0.1254, 0.0221, -0.0549, -0.1002, -0.112, -0.2055])
        a2_vals = np.array([0.8, 0.7783, 0.8582, 0.9663, 1.0395, 1.0829, 1.0942, 1.1818])
        
        a0 = np.interp(angle, angles, a0_vals)
        a1 = np.interp(angle, angles, a1_vals)
        a2 = np.interp(angle, angles, a2_vals)
        
        for pwf in pwf_values:
            ratio = pwf / p_res if p_res > 0 else 0
            q = q_max * (a0 + a1 * ratio - a2 * (ratio ** 2))
            q_values.append(max(0, q))
        return np.array(q_values), pwf_values

    @staticmethod
    def joshi(kh, kv, h, mu, bo, L, reh, rw, s, p_res, steps=20):
        """Pozo horizontal monofásico — correlación de Joshi (1991).

        Ec. 3-43 (forma para drenaje elíptico):
            J = 0.00708·kh·h / [μ·B · (ln((a + √(a²-(L/2)²))/(L/2))
                                       + (I_ani·h/L)·ln(I_ani·h/(rw·(I_ani+1))) + s)]
        con a = (L/2)·√(0.5 + √(0.25 + (2·r_eH/L)⁴))  y  I_ani = √(kh/kv).

        Ref: DOCS/MODULO III - IPR DE POZOS HORIZONTALES, pp. 25-26.
        Devuelve la recta IPR (q, Pwf). Para los inputs del ejemplo p. 30 entrega
        J ≈ 15,26 STB/d/psi (Helmy-Wattenbarger en el PDF da 19,98; las dos
        correlaciones difieren naturalmente — ver `_pi_helmy_wattenbarger`).
        """
        pwf_values = np.linspace(0, p_res, steps)
        q_values = []
        try:
            iani = np.sqrt(kh / kv) if kv > 0 else 1.0
            a = (L / 2) * np.sqrt(0.5 + np.sqrt(0.25 + (reh / (L / 2))**4))
            term1 = np.log((a + np.sqrt(a**2 - (L/2)**2)) / (L/2))
            term2 = (iani * h / L) * np.log((iani * h) / (rw * (iani + 1)))
            denom = mu * bo * (term1 + term2 + s)
            j_index = (0.00708 * kh * h) / denom if denom > 0 else 0
        except Exception:
            j_index = 0

        for pwf in pwf_values:
            q = j_index * (p_res - pwf)
            q_values.append(max(0, q))
        return np.array(q_values), pwf_values

    @staticmethod
    def babu_odeh(kx, ky, kz, h, a_res, b_res, mu, bo, L, rw, x_mid, y_0, z_0, s_res, p_res, steps=20):
        """Babu y Odeh (1989) — IPR de pozo horizontal en caja rectangular delimitada.

        Convención: el pozo corre a lo largo del eje **Y** con longitud L (≤ b_res).
            a_res = dimensión X (transversa al pozo)
            b_res = dimensión Y (dirección del pozo)
            h     = espesor (Z)
            x_mid = posición X del centro del pozo (= a_res/2 para centrado)
            y_0   = posición Y del centro del pozo (= b_res/2 para centrado)
            z_0   = posición Z del centro del pozo (= h/2  para centrado)

        Fórmula:
            J = (0.00708·b·√(kx·kz)) / [μ·B·(ln(√A/r_w_eq) + ln(C_H) - 0.75 + s_R + s_d)]
        con A = a·h, r_w_eq = (r_w/2)·[(kz/kx)^¼ + (kx/kz)^¼], y
        ln(C_H) = 6.28·(a/h)·√(kz/kx)·[⅓ - x_mid/a + (x_mid/a)²]
                  - ln(sin(π·z_0/h)) - 0.5·ln[(a/h)·√(kz/kx)] - 1.088.

        s_R (skin de penetración parcial) se aplica sólo si L < b_res y se
        selecciona entre dos regímenes según `a/√ky` vs `0.75·b/√kx`
        (Babu-Odeh 1989, eqs. (24)-(31)).

        Ref: Babu, D. K., & Odeh, A. S. (1989), "Productivity of a Horizontal
        Well", SPE Reservoir Engineering, Nov 1989. Reproducción didáctica en
        Joshi & Economides, "Petroleum Production Systems", Cap. 8.

        Auditoría (HU-007, 2026-05-25): se corrigieron 4 bugs respecto a la
        implementación previa: (i) `r_w` desnudo → `r_w_eq` con anisotropía
        vertical en denominador principal; (ii) `√(ky·kz)` → `√(kx·kz)` en
        el numerador (kx ⊥ pozo en plano horizontal); (iii) `I_ani = √(kx/ky)`
        → `√(kx/kz)` en P_xy' (anisotropía vertical relevante para penetración
        parcial); (iv) confusión de ejes y_0↔x_mid en términos C_H, P_y, P_xy.
        """
        pwf_values = np.linspace(0, p_res, steps)
        q_values = []
        try:
            A = a_res * h

            # Radio equivalente del pozo en plano X-Z (anisotropía vertical).
            rw_eq = (rw / 2.0) * ((kz / kx) ** 0.25 + (kx / kz) ** 0.25)

            # Factor de forma C_H (pozo perpendicular a X y Z; depende de x_mid y z_0).
            a_over_h_anis = (a_res / h) * np.sqrt(kz / kx)
            xm_over_a = x_mid / a_res
            z_over_h = z_0 / h
            ln_CH = (
                6.28 * a_over_h_anis * (1.0 / 3.0 - xm_over_a + xm_over_a ** 2)
                - np.log(np.sin(np.pi * z_over_h))
                - 0.5 * np.log(a_over_h_anis)
                - 1.088
            )

            # Skin de penetración parcial (sólo si L < b_res).
            s_R = 0.0
            if L < b_res:
                def F(x):
                    if x <= 1:
                        return -x * (0.145 + np.log(x) - 0.137 * x ** 2)
                    else:
                        return (2.0 - x) * (
                            0.145 + np.log(2.0 - x) - 0.137 * (2.0 - x) ** 2
                        )

                L_2b = L / (2.0 * b_res)
                # Los extremos del pozo en dirección Y normalizados por b_res.
                y0_plus = (4.0 * y_0 + L) / (2.0 * b_res)
                y0_minus = (4.0 * y_0 - L) / (2.0 * b_res)

                P_xyz = (b_res / L - 1.0) * (
                    np.log(h / rw * np.sqrt(ky / kz))
                    + 0.25 * np.log(ky / kz)
                    - np.log(np.sin(np.pi * z_over_h))
                    - 1.84
                )

                # Anisotropía vertical (k_x⊥pozo vs k_z) — afecta a la convergencia
                # del flujo en el plano transverso X-Z hacia el extremo del pozo.
                I_ani_xz = np.sqrt(kx / kz)
                P_xy_prime = (2.0 * b_res ** 2 / (I_ani_xz * L * h)) * (
                    F(L_2b) + 0.5 * (F(y0_plus) - F(y0_minus))
                )

                # P_y: posición en dirección del pozo (Y) sobre dimensión Y.
                yw_over_b = y_0 / b_res
                P_y = (6.28 * b_res ** 2 * np.sqrt(ky * kz) / (a_res * h * kx)) * (
                    1.0 / 3.0 - yw_over_b + yw_over_b ** 2
                    + (L / (24.0 * b_res)) * (L / b_res - 3.0)
                )

                # P_xy: posición transversa (X) sobre dimensión X.
                P_xy = (b_res / L - 1.0) * (6.28 * a_res / h * np.sqrt(kz / ky)) * (
                    1.0 / 3.0 - xm_over_a + xm_over_a ** 2
                )

                # Selección de régimen según relación de dimensiones equivalentes.
                if a_res / np.sqrt(ky) >= 0.75 * b_res / np.sqrt(kx):
                    s_R = P_xyz + P_xy_prime
                else:
                    s_R = P_xyz + P_y + P_xy

            denom = mu * bo * (
                np.log(np.sqrt(A) / rw_eq) + ln_CH - 0.75 + s_R + s_res
            )
            # Numerador con √(kx·kz): kx y kz son las dos perms perpendiculares al pozo.
            j_index = (0.00708 * b_res * np.sqrt(kx * kz)) / denom if denom > 0 else 0
        except Exception:
            j_index = 0

        for pwf in pwf_values:
            q = j_index * (p_res - pwf)
            q_values.append(max(0, q))
        return np.array(q_values), pwf_values

    @staticmethod
    def _pi_joshi(kh, kv, h, mu, bo, L, reh, rw, s):
        """PI horizontal por Joshi 1991. Devuelve J en STB/d/psi o 0 si inputs inválidos."""
        if mu <= 0 or bo <= 0 or L <= 0 or kh <= 0 or kv <= 0 or reh <= (L / 2.0):
            return 0.0
        try:
            iani = np.sqrt(kh / kv)
            a = (L / 2.0) * np.sqrt(0.5 + np.sqrt(0.25 + (reh / (L / 2.0)) ** 4))
            term1 = np.log((a + np.sqrt(a ** 2 - (L / 2.0) ** 2)) / (L / 2.0))
            term2 = (iani * h / L) * np.log((iani * h) / (rw * (iani + 1)))
            denom = mu * bo * (term1 + term2 + s)
            return (0.00708 * kh * h) / denom if denom > 0 else 0.0
        except Exception:
            return 0.0

    @staticmethod
    def _pi_helmy_wattenbarger(kx, ky, kz, h, a_res, b_res, L,
                               rw, x_w, y_w, z_w, mu, bo):
        """PI horizontal por Helmy & Wattenbarger 1998, condición de presión constante.

        Implementa Ecs. 3-44 a 3-57 del MODULO III, pp. 26-28.
        Devuelve J en STB/d/psi o 0 si inputs inválidos.
        γ = 1.781 (parámetro de la formulación).
        """
        gamma = 1.781
        if min(kx, ky, kz, h, a_res, b_res, L, rw, mu, bo) <= 0:
            return 0.0
        try:
            # Ecs. 3-48 a 3-57: dimensiones equivalentes
            k_eq = (kx * ky * kz) ** (1.0 / 3.0)
            a_eq = a_res * np.sqrt(k_eq / ky)
            b_eq = b_res * np.sqrt(k_eq / kx)
            h_eq = h * np.sqrt(k_eq / kz)
            L_eq = L * np.sqrt(k_eq / ky)
            A_eq = a_eq * h_eq
            rw_eq = (rw / 2.0) * ((kz / kx) ** 0.25 + (kx / kz) ** 0.25)
            x_w_eq = x_w * np.sqrt(k_eq / kx)
            y_w_eq = y_w * np.sqrt(k_eq / ky)
            z_w_eq = z_w * np.sqrt(k_eq / kz)

            xa = x_w_eq / a_eq
            ah = a_eq / h_eq
            zh = z_w_eq / h_eq
            yb = y_w_eq / b_eq
            Lb = L_eq / b_eq
            ab = a_eq / b_eq

            # Ec. 3-45: ln(C_ACP)
            inner = 4.74 - 10.353 * xa ** 1.115 + 9.165 * xa ** 2.838
            lnC_ACP = (
                2.607
                - inner * ah ** 1.011
                + 1.810 * np.log(np.sin(np.pi * zh))
                + 2.056 * np.log(ah)
            )

            # Ec. 3-47: AA (factor de forma para s_PCP)
            num = (0.388
                   - 1.278 * yb + 0.715 * yb ** 2
                   + 1.278 * Lb - 1.215 * Lb ** 2)
            den = (h_eq / a_eq) * ab ** 1.711
            AA = num / den

            # Ec. 3-46: s_PCP (skin por penetración parcial)
            bL = b_eq / L_eq
            s_PCP = (bL ** 1.233 - 1.0) * (
                2.897 + 0.003 * lnC_ACP - 0.453 * np.log(h_eq / a_eq) + AA
            )

            # Ec. 3-44: J_CP
            denom = 141.2 * mu * bo * (
                0.5 * np.log(4.0 * A_eq / (gamma * rw_eq ** 2))
                - 0.5 * lnC_ACP + s_PCP
            )
            return (k_eq * b_eq) / denom if denom > 0 else 0.0
        except Exception:
            return 0.0

    @staticmethod
    def vogel_kabir(kh, kv, h, mu, bo, L, reh, rw, s, p_res, pb,
                    pi_source="joshi",
                    kx=None, ky=None, kz=None,
                    a_res=None, b_res=None,
                    x_w=None, y_w=None, z_w=None,
                    steps=20):
        """Vogel Modificado (Kabir 1992) para pozos horizontales con partición saturado/subsaturado.

        - Si Pwf ≥ Pb (tramo monofásico): q = J·(Pr - Pwf)            (Ec. 3-43 análoga).
        - Si Pwf < Pb (tramo bifásico):  q = qb + (J·Pb/1.8)·(1 - 0.2·r - 0.8·r²),
          con r = Pwf/Pb, qb = J·(Pr - Pb)                            (Ecs. 3-30 y 3-41).

        ``pi_source``:
          * ``"joshi"`` (default): J por Joshi 1991 con kh, kv, L, reh, rw, s.
          * ``"helmy"``: J por Helmy-Wattenbarger 1998 (Ecs. 3-44 a 3-57) — requiere
            kx, ky, kz, a_res, b_res, x_w, y_w, z_w. Si alguno es None se infiere
            del par horizontal: kx=ky=kh, kz=kv, a_res=b_res=2·reh, pozo centrado.

        Ref: DOCS/MODULO III - IPR DE POZOS HORIZONTALES, pp. 24-32
        (secciones 3.2.5 y 3.2.6, Ec. 3-30, 3-41, 3-43, 3-44 a 3-57).
        """
        pwf_values = np.linspace(0, p_res, steps)
        q_values = []

        if pb <= 0 or p_res <= 0:
            return np.zeros(steps), pwf_values

        if pi_source == "helmy":
            kx_ = kh if kx is None else kx
            ky_ = kh if ky is None else ky
            kz_ = kv if kz is None else kz
            a_ = (2.0 * reh) if a_res is None else a_res
            b_ = (2.0 * reh) if b_res is None else b_res
            x_w_ = (b_ / 2.0) if x_w is None else x_w
            y_w_ = (a_ / 2.0) if y_w is None else y_w
            z_w_ = (h / 2.0) if z_w is None else z_w
            j_index = IPRModels._pi_helmy_wattenbarger(
                kx_, ky_, kz_, h, a_, b_, L, rw, x_w_, y_w_, z_w_, mu, bo
            )
        else:
            j_index = IPRModels._pi_joshi(kh, kv, h, mu, bo, L, reh, rw, s)

        if j_index <= 0:
            return np.zeros(steps), pwf_values

        qo_max_below_pb = (j_index * pb) / 1.8           # Ec. 3-41
        qb = j_index * (p_res - pb) if p_res > pb else 0.0

        for pwf in pwf_values:
            if pwf >= pb:
                q = j_index * (p_res - pwf)              # tramo lineal monofásico
            else:
                r = pwf / pb
                q = qb + qo_max_below_pb * (1.0 - 0.2 * r - 0.8 * r ** 2)
            q_values.append(max(0.0, q))

        return np.array(q_values), pwf_values

    # Se eliminaron Economides Horizontal, Butler y Furui de los modelos horizontales

    @staticmethod
    def bendakhlia_aziz(q_max, p_res, rec_factor, steps=20):
        """Bendakhlia y Aziz — IPR bifásico horizontal con factor de recobro.

        Ec. 3-31:  qo/qo,max = [1 - V·(Pwf/Pr) - (1-V)·(Pwf/Pr)²]^n
        V y n son funciones empíricas del factor de recobro (Fig. 3-6,
        ajustadas por regresión polinómica al rango x ∈ [0, 0.14]).

        Ref: DOCS/MODULO III - IPR DE POZOS HORIZONTALES, pp. 16-19
        (Ec. 3-31, Fig. 3-6). Para rec_factor=0.05 reproduce el ejemplo
        PDF p. 33 con error < 1 % (q≈27 823 STB/d vs 27 580 STB/d).
        """
        pwf_values = np.linspace(0, p_res, steps)
        q_values = []

        # Calcular n y V a partir del factor de recobro
        x = rec_factor
        n = 98.395 * (x**2) - 13.587 * x + 1.35
        # Se utilizan coeficientes precisos en lugar de la etiqueta truncada de Excel (6E+06) para evitar el colapso < 0
        v = 355651 * (x**6) - 297459 * (x**5) + 91175 * (x**4) - 12584 * (x**3) + 837.55 * (x**2) - 25.12 * x + 0.378
        v = max(0.01, v) # Clamping de seguridad absoluto
        
        for pwf in pwf_values:
            ratio = pwf / p_res if p_res > 0 else 0
            
            # Qo / Qo_max = (1 - V*(Pwf/Pr) - (1-V)*(Pwf/Pr)^2)^n
            base = 1 - v * ratio - (1 - v) * (ratio ** 2)
            if base < 0: base = 0
            
            q = q_max * (base ** n)
            q_values.append(max(0, q))
            
        return np.array(q_values), pwf_values