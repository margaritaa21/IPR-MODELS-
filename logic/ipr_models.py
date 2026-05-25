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
        """
        Método de Darcy (Flujo semi-estacionario).
        Inputs: 
        k (md), h (ft), mu (cp), bo (rb/stb), 
        re (ft), rw (ft), s (adimensional), Pr (psi)
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
        """
        Método de Fetkovich.
        Q = C * (Pr^2 - Pwf^2)^n
        Inputs: C (coeficiente), n (exponente de turbulencia), Pr
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
        """
        Método de Wiggins adaptado para flujo subsaturado con Pb.
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

    @staticmethod
    def joshi(kh, h, mu, bo, a, L, iani, rw, s, p_res, steps=20):
        import math
        pwf_values = np.linspace(0, p_res, steps)
        q_values = []
        
        if mu <= 0 or bo <= 0 or L <= 0 or a <= (L/2):
            return np.zeros(steps), pwf_values
            
        try:
            term1 = math.log((a + math.sqrt(a**2 - (L/2)**2)) / (L/2))
            term2 = (iani * h / L) * math.log((iani * h) / (rw * (iani + 1)))
            denom = mu * bo * (term1 + term2 + s)
            
            if denom <= 0: denom = 1e-6
            j_index = (0.00708 * kh * h) / denom
        except Exception:
            j_index = 0
            
        for pwf in pwf_values:
            q = j_index * (p_res - pwf)
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
        pwf_values = np.linspace(0, p_res, steps)
        q_values = []
        for pwf in pwf_values:
            ratio = pwf / p_res
            qo = q_max_o * (1 - 0.2 * ratio - 0.8 * (ratio ** 2))
            # Aproximación lineal para el agua basada en el water cut a Qmax
            qw = (w_cut / (100 - w_cut)) * qo if w_cut < 100 else 0
            q_values.append(max(0, qo + qw))
        return np.array(q_values), pwf_values

    @staticmethod
    def cheng(q_max, p_res, angle, steps=20):
        pwf_values = np.linspace(0, p_res, steps)
        q_values = []
        import math
        # Factores empíricos simplificados basados en inclinación
        rad = math.radians(angle)
        v1 = 0.2 * math.cos(rad)
        v2 = 1.0 - v1
        for pwf in pwf_values:
            ratio = pwf / p_res
    # Se eliminaron Couto y Xie Xingli de los modelos verticales

    # ================= NUEVOS MODELOS HORIZONTALES =================

    @staticmethod
    def cheng(q_max, p_res, angle, steps=20):
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
        pwf_values = np.linspace(0, p_res, steps)
        q_values = []
        try:
            # Babu and Odeh rigorous calculation
            # a_res is dimension along x-axis, b_res is dimension along y-axis (well direction is y)
            A = a_res * h
            
            # Form factor CH
            term_ch1 = 6.28 * (a_res / h) * np.sqrt(kz / kx)
            term_ch2 = (1/3) - (y_0 / a_res) + (y_0 / a_res)**2
            term_ch3 = np.log(np.sin(np.pi * z_0 / h))
            term_ch4 = 0.5 * np.log(a_res / h * np.sqrt(kz / kx))
            ln_CH = term_ch1 * term_ch2 - term_ch3 - term_ch4 - 1.088
            
            # Partial penetration skin SR
            s_R = 0
            if L < b_res:
                # Simplified skin logic if partially penetrated
                def F(x, b_L_ratio):
                    if x <= 1:
                        return -x * (0.145 + np.log(x) - 0.137 * x**2)
                    else:
                        return (2 - x) * (0.145 + np.log(2 - x) - 0.137 * (2 - x)**2)
                
                L_2b = L / (2 * b_res)
                xmid_L_2b_plus = (4 * x_mid + L) / (2 * b_res)
                xmid_L_2b_minus = (4 * x_mid - L) / (2 * b_res)
                
                P_xyz = (b_res / L - 1) * (np.log(h / rw * np.sqrt(ky / kz)) + 0.25 * np.log(ky / kz) - np.log(np.sin(np.pi * z_0 / h)) - 1.84)
                
                I_ani_y_x = np.sqrt(kx / ky)
                P_xy_prime = (2 * b_res**2 / (I_ani_y_x * L * h)) * (F(L_2b, b_res) + 0.5 * (F(xmid_L_2b_plus, b_res) - F(xmid_L_2b_minus, b_res)))
                P_y = (6.28 * b_res**2 * np.sqrt(ky * kz) / (a_res * h * kx)) * (1/3 - x_mid/b_res + (x_mid/b_res)**2 + (L/(24*b_res)) * (L/b_res - 3))
                P_xy = (b_res / L - 1) * (6.28 * a_res / h * np.sqrt(kz / ky)) * (1/3 - y_0/a_res + (y_0/a_res)**2)
                
                # Condition simplified for s_R assignment
                if a_res / np.sqrt(ky) >= 0.75 * b_res / np.sqrt(kx):
                    s_R = P_xyz + P_xy_prime
                else:
                    s_R = P_xyz + P_y + P_xy
            
            denom = mu * bo * (np.log(np.sqrt(A) / rw) + ln_CH - 0.75 + s_R + s_res)
            j_index = (0.00708 * b_res * np.sqrt(ky * kz)) / denom if denom > 0 else 0
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