import math
from .pvt_correlations import PVTCorrelations as PVT

class VLPModels:
    """
    Algoritmo iterativo de gradiente de presión (Outflow) - Metodología Estricta 31 Pasos.
    Referencia: PDF "SISTEMAS DE PRODUCCIÓN MIO 1ER PARCIAL".
    """

    @staticmethod
    def calculate_pwf_31_steps(length_ft, tubing_id_in, p_wh, temp_wh_f, temp_bh_f, q_liq_bpd, gor, bsw, api, gas_sg, water_sg, bw):
        """
        Ejecuta el algoritmo de 31 pasos iterando sobre Delta P hasta que Delta H ≈ Longitud.
        Retorna: (Pwf, Diccionario con las 31 variables)
        """
        
        # --- Inicialización Iterativa ---
        # Objetivo: Encontrar un Delta P tal que la altura calculada (Delta H) sea igual a la longitud del tubing.
        
        delta_p = 100.0 # Valor semilla inicial (psi)
        tolerance = 1.0 # Tolerancia en pies (ft)
        max_iter = 200
        
        # Variables de resultado final
        final_pwf = 0.0
        pasos = {}
        
        converged = False

        for iteration in range(max_iter):
            # Paso 1: Presión promedio
            p_avg = p_wh + delta_p / 2.0
            t_avg = (temp_wh_f + temp_bh_f) / 2.0 # Asumiendo perfil lineal simple para T promedio
            
            # Paso 2: Presión de burbuja (Standing)
            pb = PVT.calculate_pb_standing(gor, gas_sg, api, t_avg)
            
            # Paso 3: Relación gas disuelto (Rs)
            if p_avg < pb:
                rs = PVT.calculate_rs_standing(p_avg, gas_sg, api, t_avg)
            else:
                rs = gor
            
            # Paso 4: Calcular F (Variable intermedia Standing)
            gamma_o = 141.5 / (131.5 + api)
            f_factor = rs * ((gas_sg / gamma_o)**0.5) + 1.25 * t_avg
            
            # Paso 5: Factor volumétrico del petróleo (Bo)
            # Fórmula PDF: Bo = 0.972 + 0.000147 * F^1.175
            bo = 0.972 + 0.000147 * (f_factor ** 1.175)
            
            # Paso 6: Densidad del gas disuelto (gamma_gd)
            # Fórmula PDF: ygd = 0.25 + 0.02*API + 10^-6 * (0.6874 - 3.5864*API) * Rs
            gamma_gd = 0.25 + 0.02 * api + 1e-6 * (0.6874 - 3.5864 * api) * rs
            
            # Paso 7: Densidad del petróleo (rho_o)
            # Fórmula PDF: rho_o = (62.4 * yo + 0.01362 * Rs * ygd) / Bo
            rho_o = (62.4 * gamma_o + 0.01362 * rs * gamma_gd) / bo
            
            # Paso 8: Viscosidad del petróleo (mu_o) - Beggs & Robinson
            # Calculamos variables intermedias Z, Y, X
            z_val = 3.0324 - 0.02023 * api
            y_val = 10 ** z_val
            x_val = y_val * (t_avg ** -1.163)
            mu_om = (10 ** x_val) - 1 # Viscosidad petróleo muerto
            
            a_val = 10.715 * ((rs + 100) ** -0.515)
            b_val = 5.44 * ((rs + 150) ** -0.338)
            mu_o = a_val * (mu_om ** b_val)
            
            # Paso 9: Gravedad específica del gas libre (gamma_gl)
            if (gor - rs) > 0:
                gamma_gl = (gor * gas_sg - rs * gamma_gd) / (gor - rs)
            else:
                gamma_gl = gas_sg # Si no hay gas libre o indeterminado
            
            # Paso 10: Factor Z (Dranchuk-Abou-Kassem)
            p_pc = 756.8 - 131.0 * gas_sg
            t_pc = 169.2 + 349.5 * gas_sg
            ppr = p_avg / p_pc
            tpr = (t_avg + 460) / t_pc
            z = PVT.calculate_z_factor_dak(ppr, tpr)
            
            # Paso 11: Factor volumétrico del gas (Bg)
            # Bg = 0.02825 * Z * (T+460) / P
            bg = 0.02825 * z * (t_avg + 460) / p_avg
            
            # Paso 12: Densidad del gas (rho_g)
            # rho_g = 0.0764 * ygl / Bg
            rho_g = (0.0764 * gamma_gl) / bg if bg > 0 else 0
            
            # Paso 13: Viscosidad del gas (mu_g) - Lee et al.
            mu_g = PVT.calculate_gas_viscosity_lee(t_avg, rho_g, 28.96 * gamma_gl)
            
            # Paso 14: Volumen de agua producido (Qw)
            # Nota: El PDF usa una formula derivada del BSW.
            # Qw = (100 * Qo / (100 - BSW)) - Qo  (Si Qo es input neto)
            # Pero usualmente el input es Qliq total.
            # Asumiremos Qliq como dato de entrada.
            # Qw = Qliq * (BSW/100)
            # Qo = Qliq * (1 - BSW/100)
            qw = q_liq_bpd * (bsw / 100.0)
            qo = q_liq_bpd - qw
            
            # Paso 18: WOR (Calculado antes para usar en fórmulas siguientes)
            wor = qw / qo if qo > 0 else 0
            
            # Paso 15: Fracción volumétrica de líquido (Lambda - Colgamiento sin resbalamiento)
            # Lambda = 1 / (1 + [Qo(GOR-Rs)Bg] / [5.615 * (QoBo + QwBw)])
            term_gas = qo * (gor - rs) * bg
            term_liq = 5.615 * (qo * bo + qw * bw)
            if term_liq + term_gas == 0:
                lam = 1.0
            else:
                lam = term_liq / (term_liq + term_gas * 5.615 / 5.615) # Ajuste unidades, usando forma simplificada
                # Usando fórmula exacta PDF:
                # Numerador parece ser 1 según PDF o VolLiq / VolTotal?
                # PDF: Lambda = QL / (QL + QG). QL en condiciones yacimiento.
                # QL_yac = Qo*Bo + Qw*Bw. QG_yac = Qo*(GOR-Rs)*Bg
                # lambda = (Qo*Bo + Qw*Bw) / ((Qo*Bo + Qw*Bw) + (Qo*(GOR-Rs)*Bg)/5.615?)
                # Nota: Bg en ft3/scf. Qo en STB/d.
                # Vamos a usar balance volumétrico estándar consistente.
                q_liq_res_bbl = qo * bo + qw * bw
                q_gas_res_bbl = (qo * (gor - rs) * bg) / 5.615 # Convertir ft3 a bbl
                lam = q_liq_res_bbl / (q_liq_res_bbl + q_gas_res_bbl)

            # Paso 16: VSL (ft/s)
            # VSL = 0.01191 * (QoBo + QwBw) / ID^2
            vsl = 0.01191 * (qo * bo + qw * bw) / (tubing_id_in ** 2)
            
            # Paso 17: VSG (ft/s)
            # VSG = 0.002122 * Qo * (GOR - Rs) * Bg / ID^2
            vsg = 0.002122 * qo * (gor - rs) * bg / (tubing_id_in ** 2)
            
            # Paso 19: Fracción volumétrica de petróleo (fo)
            # fo = Bo / (Bo + WOR * Bw)
            fo = bo / (bo + wor * bw)
            
            # Paso 20: Densidad del agua (rho_w)
            rho_w = 62.4 * water_sg
            
            # Paso 21: Densidad del líquido (rho_l)
            # rho_l = rho_o * fo + rho_w * (1 - fo)
            rho_l = rho_o * fo + rho_w * (1 - fo)
            
            # Paso 22: Densidad de la mezcla 1 (rho_m)
            # rho_m = rho_l * lambda + rho_g * (1 - lambda)
            rho_m = rho_l * lam + rho_g * (1 - lam)
            
            # Paso 23: Densidad equivalente (rho_mes2) - Fórmula compleja PDF
            # rho_mes2 = [350.5 * (141.5/(131.5+API) + Yw*WOR) + 0.0764*GOR*Yg] / [5.615*(Bo + Bw*WOR) + (GOR-Rs)*Bg]
            num_p23 = 350.5 * (gamma_o + water_sg * wor) + 0.0764 * gor * gas_sg
            den_p23 = 5.615 * (bo + bw * wor) + (gor - rs) * bg
            rho_mes2 = num_p23 / den_p23 if den_p23 > 0 else rho_m
            
            # Paso 24: Viscosidad del líquido (mu_l)
            # mu_l = mu_o * fo + mu_w * (1 - fo)
            # Asumimos mu_w = 0.5 cp si no hay correlación
            mu_w = 0.5 
            mu_l = mu_o * fo + mu_w * (1 - fo)
            
            # Paso 25: Viscosidad de la mezcla (mu_m)
            # mu_m = mu_l * lambda + mu_g * (1 - lambda)
            mu_m = mu_l * lam + mu_g * (1 - lam)
            
            # Paso 26: Masa volumétrica total (M)
            # M = 350.5 * gamma_o + 0.0764 * GOR * Yg + 350.5 * Yw * WOR
            # Nota: el PDF pone gamma_o como la fracción (141.5/...)
            mass_m = 350.5 * gamma_o + 0.0764 * gor * gas_sg + 350.5 * water_sg * wor
            
            # Paso 27: Factor A
            # A = (ID * 10^6) / (Qo * M)
            if qo * mass_m > 0:
                factor_a = (tubing_id_in * 1e6) / (qo * mass_m)
            else:
                factor_a = 999999 # Valor alto para evitar error
            
            # Paso 28: Factor FTP (Polinomio)
            # FTP = 0.005415 - 0.0005723*A + 0.0001848*A^2 + 3.5843e-6*A^3
            # Nota: El PDF tiene un error tipográfico probable en los signos o coeficientes si A es muy grande.
            # Usaremos la fórmula tal cual. Si A es muy grande (>10), FTP explota. 
            # Asumiremos rango valido.
            ftp = 0.005415 - 0.0005723 * factor_a + 0.0001848 * (factor_a**2) + 3.5843e-6 * (factor_a**3)
            if ftp < 0.001: ftp = 0.005 # Limite físico
            
            # Paso 29: Gradiente de presión
            # Gradiente = (1/144) * (rho_mes2 + [FTP * (Qo * M)^2] / [2.979e5 * rho_mes2 * ID^5])
            term_fric = (ftp * ((qo * mass_m) ** 2)) / (2.979e5 * rho_mes2 * (tubing_id_in ** 5))
            gradient = (1.0 / 144.0) * (rho_mes2 + term_fric)
            
            # Paso 30: Altura equivalente (Delta H)
            # Delta H = Delta P / Gradient
            if gradient <= 0: gradient = 0.001
            delta_h_calc = delta_p / gradient
            
            # Verificación de Condición: Delta H >= Longitud?
            diff = delta_h_calc - length_ft
            
            # Almacenamos los 31 pasos para retornar
            current_steps = {
                "Paso 1 (P_avg)": p_avg, "Paso 2 (Pb)": pb, "Paso 3 (Rs)": rs, "Paso 4 (F)": f_factor,
                "Paso 5 (Bo)": bo, "Paso 6 (Ygd)": gamma_gd, "Paso 7 (Rho_o)": rho_o, "Paso 8 (Mu_o)": mu_o,
                "Paso 9 (Ygl)": gamma_gl, "Paso 10 (Z)": z, "Paso 11 (Bg)": bg, "Paso 12 (Rho_g)": rho_g,
                "Paso 13 (Mu_g)": mu_g, "Paso 14 (Qw)": qw, "Paso 15 (Lambda)": lam, "Paso 16 (VSL)": vsl,
                "Paso 17 (VSG)": vsg, "Paso 18 (WOR)": wor, "Paso 19 (fo)": fo, "Paso 20 (Rho_w)": rho_w,
                "Paso 21 (Rho_l)": rho_l, "Paso 22 (Rho_m)": rho_m, "Paso 23 (Rho_eq)": rho_mes2,
                "Paso 24 (Mu_l)": mu_l, "Paso 25 (Mu_m)": mu_m, "Paso 26 (Masa M)": mass_m,
                "Paso 27 (Factor A)": factor_a, "Paso 28 (FTP)": ftp, "Paso 29 (Gradiente)": gradient,
                "Paso 30 (Delta H)": delta_h_calc, "Paso 31 (Pwf)": p_wh + delta_p
            }

            if abs(diff) <= tolerance:
                # Convergencia alcanzada
                final_pwf = p_wh + delta_p
                pasos = current_steps
                converged = True
                break
            else:
                # Ajuste de Delta P para siguiente iteración
                # Método Newton simple o Sustitución directa
                # Nueva Delta P = Gradient_calc * Length
                new_delta_p = gradient * length_ft
                
                # Amortiguamiento para evitar oscilaciones
                delta_p = 0.5 * delta_p + 0.5 * new_delta_p
        
        if not converged:
            # Si no converge, devolvemos el último estimado
            final_pwf = p_wh + delta_p
            pasos = current_steps
            
        return final_pwf, pasos