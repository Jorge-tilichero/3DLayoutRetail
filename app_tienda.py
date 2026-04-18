import streamlit as st
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from matplotlib.ticker import MultipleLocator
import matplotlib.image as mpimg
import os
import io
import math

# --- CONSTANTES DE MODULACIÓN EXACTA ---
MOD_1FT = 0.30
MOD_2FT = 0.61        
MOD_3FT = 0.91        
PROF_CAFE = 0.75      
PROF_CHECK = 0.60     
PROF_CAJERO = 1.00    
PROF_CONTRA = 0.45    
PROF_FRIO = 2.00      
PROF_PERIMETRO = 0.45 
GONDOLA_PROF = 0.90   
CABECERA_PROF = 0.45  
PUERTA_ANCHO = 1.80   
PASILLO_STD = 1.20    
ISLA_DIM = 0.60

# --- CLASIFICADOR ---
def clasificar_formato(m2):
    if m2 <= 15: return "BOOTH (Compacto)"
    elif m2 <= 36: return "MINI (Reducido)"
    elif m2 <= 56: return "MINI 2 (Reducido)"
    elif m2 <= 77: return "MEDIA (Ordinario)"
    elif m2 <= 98: return "MEDIA 2 (Ordinario)"
    elif m2 <= 117: return "REGULAR (Ordinario)"
    elif m2 <= 135: return "MÍNIMO 2 (Ordinario)"
    elif m2 <= 154: return "ÓPTIMO (Ordinario)"
    elif m2 <= 170: return "ÓPTIMO 2 (Ordinario)"
    elif m2 <= 250: return "MÁXIMO (Extra Ordinario)"
    else: return "MEGA (Extra Ordinario)"

def colisiona(x, y, w, h, lista_obstaculos):
    margen = 0.05
    for (ox, oy, ow, oh, nombre) in lista_obstaculos:
        if not (x + w <= ox + margen or x >= ox + ow - margen or y + h <= oy + margen or y >= oy + oh - margen):
            return True, nombre
    return False, ""

def normalizar_rotacion(r):
    return (r % 360)

# MATRIZ ISOMÉTRICA (30 GRADOS)
def to_iso(x, y):
    ang = math.radians(30)
    iso_x = (x - y) * math.cos(ang)
    iso_y = (x + y) * math.sin(ang)
    return iso_x, iso_y

def dibujar_layout_oxxo_v27(conf):
    W, L = conf['ancho'], conf['largo']
    vista_iso = conf.get('modo_iso', False)

    fig, ax = plt.subplots(figsize=(14, 14))
    
    if vista_iso:
        ax.axis('off')
        for ix in range(int(W)+1):
            x1, y1 = to_iso(ix, 0)
            x2, y2 = to_iso(ix, L)
            ax.plot([x1, x2], [y1, y2], color='#E5E7E9', lw=0.5, zorder=0)
        for iy in range(int(L)+1):
            x1, y1 = to_iso(0, iy)
            x2, y2 = to_iso(W, iy)
            ax.plot([x1, x2], [y1, y2], color='#E5E7E9', lw=0.5, zorder=0)
        ax.set_xlim(-L*0.9, W*0.9)
        ax.set_ylim(0, (W+L)*0.6)
    else:
        ax.set_xlim(0, W)
        ax.set_ylim(0, L)
        ax.xaxis.set_major_locator(MultipleLocator(1))
        ax.yaxis.set_major_locator(MultipleLocator(1))
        ax.grid(which='major', color='#E5E7E9', linestyle='-', linewidth=0.5, zorder=0)

    obs_fisicos = []  
    obs_pasillos = [] 
    errores = []
    log_imagenes = []
    area_exh = 0
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    
    def registrar_obj(x, y, w, h, color, texto="", rot_text=0, alpha=1.0, font=6, tipo="Fisico", name="Objeto", txt_col='black', weight='normal', img_base=None):
        choca = False
        obj_chocado = ""
        ec = 'black'
        lw = 1

        z_calc = 1000 - int((x + y) * 10) if tipo == "Fisico" else 2

        if x < -0.05 or y < -0.05 or x + w > W + 0.05 or y + h > L + 0.05:
            errores.append(f"Fuera de layout: {name}")
            ec, lw = 'red', 2
            choca = True
        else:
            if tipo == "Fisico":
                c1, n1 = colisiona(x, y, w, h, obs_fisicos)
                c2, n2 = colisiona(x, y, w, h, obs_pasillos)
                if c1: choca, obj_chocado = True, n1
                elif c2: choca, obj_chocado = True, n2
            elif tipo == "Pasillo":
                choca, obj_chocado = colisiona(x, y, w, h, obs_fisicos)
                ec, lw = 'none', 0

            if choca and obj_chocado: 
                errores.append(f"{name} choca con {obj_chocado}.")
                ec, lw = 'red', 2
                z_calc = 2000 
            elif not choca:
                if tipo == "Fisico": obs_fisicos.append((x, y, w, h, name))
                elif tipo == "Pasillo": obs_pasillos.append((x, y, w, h, name))

        dibujado_imagen = False
        if conf.get('modo_render', False) and img_base and tipo == "Fisico" and not choca:
            rot_norm = int(rot_text % 360)
            nombre_archivo = f"{img_base}_{rot_norm}.png"
            ruta_img = os.path.join(BASE_DIR, "assets", nombre_archivo)
            
            if os.path.exists(ruta_img):
                try:
                    img = mpimg.imread(ruta_img)
                    if vista_iso:
                        img_h, img_w = img.shape[:2]
                        aspect = img_w / img_h
                        scale = math.hypot(w, h) * 1.0
                        ext_w = scale
                        ext_h = scale / aspect
                        
                        icx, icy = to_iso(x + w/2, y + h/2)
                        icy += ext_h * 0.15 
                        ax.imshow(img, extent=[icx - ext_w/2, icx + ext_w/2, icy - ext_h/2, icy + ext_h/2], zorder=z_calc)
                    else:
                        ax.imshow(img, extent=[x, x+w, y, y+h], zorder=z_calc)
                    
                    dibujado_imagen = True
                    if f"✅ OK: {nombre_archivo}" not in log_imagenes: log_imagenes.append(f"✅ OK: {nombre_archivo}")
                except Exception as e:
                    log_imagenes.append(f"❌ Error: {nombre_archivo}")
            else:
                if f"⚠️ Falta: {nombre_archivo}" not in log_imagenes: log_imagenes.append(f"⚠️ Falta: {nombre_archivo}")

        if not dibujado_imagen:
            if vista_iso:
                pts = [to_iso(x, y), to_iso(x+w, y), to_iso(x+w, y+h), to_iso(x, y+h)]
                ax.add_patch(patches.Polygon(pts, closed=True, color=color, ec=ec, lw=lw, alpha=alpha, zorder=z_calc))
                if texto:
                    icx, icy = to_iso(x + w/2, y + h/2)
                    ax.text(icx, icy, texto, ha='center', va='center', fontsize=font, color=txt_col, weight=weight, zorder=z_calc+1)
            else:
                ax.add_patch(patches.Rectangle((x, y), w, h, color=color, ec=ec, lw=lw, alpha=alpha, zorder=z_calc))
                if texto:
                    rot_visual = rot_text % 360
                    if 90 < rot_visual < 270: rot_visual -= 180
                    ax.text(x + w/2, y + h/2, texto, ha='center', va='center', rotation=rot_visual, fontsize=font, color=txt_col, weight=weight, zorder=z_calc+1)
        return w, h

    if vista_iso:
        pts_piso = [to_iso(0,0), to_iso(W,0), to_iso(W,L), to_iso(0,L)]
        ax.add_patch(patches.Polygon(pts_piso, closed=True, fill=False, ec='black', lw=4, zorder=0))
    else:
        ax.add_patch(patches.Rectangle((0, 0), W, L, fill=False, ec='black', lw=4, zorder=0))
    
    area_total = W * L

    # ==========================================
    # 1. BODEGA
    # ==========================================
    a_op = 0
    if conf['t_bodega']:
        w_b, h_b = conf['w_bodega'], conf['h_bodega']
        xb, yb = conf['x_bodega'], conf['y_bodega']
        a_op = w_b * h_b
        registrar_obj(xb, yb, w_b, h_b, '#D2B48C', f"BODEGA ({a_op:.1f}m²)", font=8, weight='bold', name="Bodega")
        registrar_obj(xb + 0.5, yb + 0.5, w_b - 1.0, h_b - 1.0, '#E59866', "Int. Bodega", alpha=0.3, tipo="Pasillo", name="Interior Bodega")
        
        pos_pb = conf['pos_puerta_bod']
        if conf['muro_puerta_bod'] == 'Sur': registrar_obj(xb + pos_pb, yb, 0.9, 0.2, 'brown', name="Pta Bodega")
        elif conf['muro_puerta_bod'] == 'Norte': registrar_obj(xb + pos_pb, yb + h_b - 0.2, 0.9, 0.2, 'brown', name="Pta Bodega")
        elif conf['muro_puerta_bod'] == 'Oeste': registrar_obj(xb, yb + pos_pb, 0.2, 0.9, 'brown', name="Pta Bodega")
        elif conf['muro_puerta_bod'] == 'Este': registrar_obj(xb + w_b - 0.2, yb + pos_pb, 0.2, 0.9, 'brown', name="Pta Bodega")

    area_comercial = area_total - a_op

    # ==========================================
    # 2. ACCESO Y PASILLO DE PODER
    # ==========================================
    if conf['t_puerta']:
        pw = 0.9 if conf['tipo_puerta'] == '1 Puerta (90cm)' else 1.80
        xp, yp = conf['pos_puerta_x'], conf['pos_puerta_y']
        
        w_puerta = pw if conf['muro_puerta'] in ['Sur', 'Norte'] else 0.2
        h_puerta = 0.2 if conf['muro_puerta'] in ['Sur', 'Norte'] else pw
        registrar_obj(xp, yp, w_puerta, h_puerta, 'red', "ACCESO", font=5, txt_col='white', weight='bold', name="Acceso")

        if conf['t_pasillos']:
            wpod = conf['pas_poder']
            if conf['muro_puerta'] == 'Sur': registrar_obj(xp - (wpod-pw)/2, yp, wpod, L - yp, '#EBF5FB', "PASILLO DE PODER", rot_text=90, alpha=0.6, tipo="Pasillo", name="Pasillo Poder")
            elif conf['muro_puerta'] == 'Norte': registrar_obj(xp - (wpod-pw)/2, 0, wpod, yp, '#EBF5FB', "PASILLO DE PODER", rot_text=90, alpha=0.6, tipo="Pasillo", name="Pasillo Poder")
            elif conf['muro_puerta'] == 'Este': registrar_obj(0, yp - (wpod-pw)/2, xp, wpod, '#EBF5FB', "PASILLO DE PODER", alpha=0.6, tipo="Pasillo", name="Pasillo Poder")
            elif conf['muro_puerta'] == 'Oeste': registrar_obj(xp, yp - (wpod-pw)/2, W - xp, wpod, '#EBF5FB', "PASILLO DE PODER", alpha=0.6, tipo="Pasillo", name="Pasillo Poder")

    # ==========================================
    # 3. CHECKOUT
    # ==========================================
    if conf['t_check']:
        mods_chk = conf['cant_check']
        xc, yc = conf['pos_chk_x'], conf['pos_chk_y']
        rot_c = conf['rot_check']
        w_chk = mods_chk * MOD_2FT
        
        if rot_c == 0: 
            registrar_obj(xc, yc, w_chk, PROF_CONTRA, '#82E0AA', "C.CAJA", name="Contracaja", img_base="contracaja", rot_text=0)
            registrar_obj(xc, yc + PROF_CONTRA, w_chk, PROF_CAJERO, '#EAEDED', "P. CAJERO", tipo="Pasillo", name="Pasillo Cajero")
            for i in range(mods_chk): registrar_obj(xc + (i*MOD_2FT), yc + PROF_CONTRA + PROF_CAJERO, MOD_2FT, PROF_CHECK, '#ABEBC6', f"CHK{i+1}", font=5, name=f"CHK{i+1}", img_base="checkout", rot_text=0)
            if conf['t_pasillos']: registrar_obj(xc, yc + PROF_CONTRA + PROF_CAJERO + PROF_CHECK, w_chk, PASILLO_STD, '#D5F5E3', "P. COBRO", alpha=0.5, tipo="Pasillo", name="Pasillo Cobro")
            area_exh += (w_chk * PROF_CHECK)
        elif rot_c == 90: 
            registrar_obj(xc + PROF_CHECK + PROF_CAJERO, yc, PROF_CONTRA, w_chk, '#82E0AA', "C.CAJA", rot_text=90, name="Contracaja", img_base="contracaja")
            registrar_obj(xc + PROF_CHECK, yc, PROF_CAJERO, w_chk, '#EAEDED', "P. CAJERO", rot_text=90, tipo="Pasillo", name="Pasillo Cajero")
            for i in range(mods_chk): registrar_obj(xc, yc + (i*MOD_2FT), PROF_CHECK, MOD_2FT, '#ABEBC6', f"CHK{i+1}", font=5, rot_text=90, name=f"CHK{i+1}", img_base="checkout")
            if conf['t_pasillos']: registrar_obj(xc - PASILLO_STD, yc, PASILLO_STD, w_chk, '#D5F5E3', "P. COBRO", rot_text=90, alpha=0.5, tipo="Pasillo", name="Pasillo Cobro")
            area_exh += (w_chk * PROF_CHECK)
        elif rot_c == 180: 
            if conf['t_pasillos']: registrar_obj(xc, yc - PASILLO_STD, w_chk, PASILLO_STD, '#D5F5E3', "P. COBRO", alpha=0.5, tipo="Pasillo", name="Pasillo Cobro")
            for i in range(mods_chk): registrar_obj(xc + (i*MOD_2FT), yc, MOD_2FT, PROF_CHECK, '#ABEBC6', f"CHK{i+1}", font=5, name=f"CHK{i+1}", img_base="checkout", rot_text=180)
            registrar_obj(xc, yc + PROF_CHECK, w_chk, PROF_CAJERO, '#EAEDED', "P. CAJERO", tipo="Pasillo", name="Pasillo Cajero")
            registrar_obj(xc, yc + PROF_CHECK + PROF_CAJERO, w_chk, PROF_CONTRA, '#82E0AA', "C.CAJA", name="Contracaja", img_base="contracaja", rot_text=180)
            area_exh += (w_chk * PROF_CHECK)
        elif rot_c == 270: 
            registrar_obj(xc, yc, PROF_CONTRA, w_chk, '#82E0AA', "C.CAJA", rot_text=270, name="Contracaja", img_base="contracaja")
            registrar_obj(xc + PROF_CONTRA, yc, PROF_CAJERO, w_chk, '#EAEDED', "P. CAJERO", rot_text=90, tipo="Pasillo", name="Pasillo Cajero")
            for i in range(mods_chk): registrar_obj(xc + PROF_CONTRA + PROF_CAJERO, yc + (i*MOD_2FT), PROF_CHECK, MOD_2FT, '#ABEBC6', f"CHK{i+1}", font=5, rot_text=270, name=f"CHK{i+1}", img_base="checkout")
            if conf['t_pasillos']: registrar_obj(xc + PROF_CONTRA + PROF_CAJERO + PROF_CHECK, yc, PASILLO_STD, w_chk, '#D5F5E3', "P. COBRO", rot_text=90, alpha=0.5, tipo="Pasillo", name="Pasillo Cobro")
            area_exh += (w_chk * PROF_CHECK)

    # ==========================================
    # 4. CUARTO FRÍO (Módulos individuales)
    # ==========================================
    if conf['t_frio']:
        xf, yf = conf['pos_frio_x'], conf['pos_frio_y']
        rot_f = conf['rot_frio']
        ptas = conf['cant_frio']
        
        for p in range(ptas):
            if rot_f == 0: registrar_obj(xf + p*MOD_2FT, yf, MOD_2FT, PROF_FRIO, '#AED6F1', f"F{p+1}", weight='bold', rot_text=0, name=f"Frio {p}", img_base="frio")
            elif rot_f == 90: registrar_obj(xf, yf + p*MOD_2FT, PROF_FRIO, MOD_2FT, '#AED6F1', f"F{p+1}", rot_text=90, weight='bold', name=f"Frio {p}", img_base="frio")
            elif rot_f == 180: registrar_obj(xf - (p+1)*MOD_2FT, yf - PROF_FRIO, MOD_2FT, PROF_FRIO, '#AED6F1', f"F{p+1}", weight='bold', rot_text=180, name=f"Frio {p}", img_base="frio")
            elif rot_f == 270: registrar_obj(xf - PROF_FRIO, yf - (p+1)*MOD_2FT, PROF_FRIO, MOD_2FT, '#AED6F1', f"F{p+1}", rot_text=270, weight='bold', name=f"Frio {p}", img_base="frio")
        
        # Pasillo General
        wf = ptas * MOD_2FT
        if conf['t_pasillos']:
            if rot_f == 0: registrar_obj(xf, yf - PASILLO_STD, wf, PASILLO_STD, '#FCF3CF', "P. FRÍO", alpha=0.6, tipo="Pasillo", name="Pas Frio")
            elif rot_f == 90: registrar_obj(xf + PROF_FRIO, yf, PASILLO_STD, wf, '#FCF3CF', "P. FRÍO", rot_text=90, alpha=0.6, tipo="Pasillo", name="Pas Frio")
            elif rot_f == 180: registrar_obj(xf - wf, yf, wf, PASILLO_STD, '#FCF3CF', "P. FRÍO", alpha=0.6, tipo="Pasillo", name="Pas Frio")
            elif rot_f == 270: registrar_obj(xf - PASILLO_STD - PROF_FRIO, yf - wf, PASILLO_STD, wf, '#FCF3CF', "P. FRÍO", rot_text=90, alpha=0.6, tipo="Pasillo", name="Pas Frio")
        area_exh += (wf * PROF_FRIO)

    # ==========================================
    # 5. GÓNDOLAS CENTRALES (Módulos individuales)
    # ==========================================
    if conf['t_gondolas']:
        xg, yg = conf['pos_gon_x'], conf['pos_gon_y']
        rot_g = conf['rot_gon'] 
        tramos = conf['cant_tramos']
        largo_g = tramos * MOD_3FT
        
        for i in range(conf['cant_trenes']):
            if rot_g == 0: 
                registrar_obj(xg, yg, GONDOLA_PROF, CABECERA_PROF, '#E74C3C', "CAB", rot_text=0, font=5, name=f"Cab Sur {i+1}", img_base="gondola_cab")
                for t in range(tramos): registrar_obj(xg, yg + CABECERA_PROF + t*MOD_3FT, GONDOLA_PROF, MOD_3FT, '#ABB2B9', f"Tr{t+1}", rot_text=0, font=6, name=f"Tr{t+1} Tren{i+1}", img_base="gondola_tramo")
                registrar_obj(xg, yg + CABECERA_PROF + largo_g, GONDOLA_PROF, CABECERA_PROF, '#E74C3C', "CAB", rot_text=0, font=5, name=f"Cab Norte {i+1}", img_base="gondola_cab")
                if conf['t_pasillos']: registrar_obj(xg + GONDOLA_PROF, yg, conf['pas_gon'], largo_g + CABECERA_PROF*2, '#EBEDEF', "", rot_text=90, alpha=0.6, tipo="Pasillo", name=f"Pas Gon {i+1}")
                xg += GONDOLA_PROF + conf['pas_gon']
            elif rot_g == 90:
                registrar_obj(xg, yg, CABECERA_PROF, GONDOLA_PROF, '#E74C3C', "CAB", rot_text=90, font=5, name=f"Cab Oeste {i+1}", img_base="gondola_cab")
                for t in range(tramos): registrar_obj(xg + CABECERA_PROF + t*MOD_3FT, yg, MOD_3FT, GONDOLA_PROF, '#ABB2B9', f"Tr{t+1}", rot_text=90, font=6, name=f"Tr{t+1} Tren{i+1}", img_base="gondola_tramo")
                registrar_obj(xg + CABECERA_PROF + largo_g, yg, CABECERA_PROF, GONDOLA_PROF, '#E74C3C', "CAB", rot_text=90, font=5, name=f"Cab Este {i+1}", img_base="gondola_cab")
                if conf['t_pasillos']: registrar_obj(xg, yg + GONDOLA_PROF, largo_g + CABECERA_PROF*2, conf['pas_gon'], '#EBEDEF', "", alpha=0.6, tipo="Pasillo", name=f"Pas Gon {i+1}")
                yg += GONDOLA_PROF + conf['pas_gon']
            elif rot_g == 180:
                registrar_obj(xg - GONDOLA_PROF, yg - CABECERA_PROF, GONDOLA_PROF, CABECERA_PROF, '#E74C3C', "CAB", rot_text=180, font=5, name=f"Cab Norte {i+1}", img_base="gondola_cab")
                for t in range(tramos): registrar_obj(xg - GONDOLA_PROF, yg - CABECERA_PROF - (t+1)*MOD_3FT, GONDOLA_PROF, MOD_3FT, '#ABB2B9', f"Tr{t+1}", rot_text=180, font=6, name=f"Tr{t+1} Tren{i+1}", img_base="gondola_tramo")
                registrar_obj(xg - GONDOLA_PROF, yg - CABECERA_PROF*2 - largo_g, GONDOLA_PROF, CABECERA_PROF, '#E74C3C', "CAB", rot_text=180, font=5, name=f"Cab Sur {i+1}", img_base="gondola_cab")
                if conf['t_pasillos']: registrar_obj(xg - GONDOLA_PROF - conf['pas_gon'], yg - largo_g - CABECERA_PROF*2, conf['pas_gon'], largo_g + CABECERA_PROF*2, '#EBEDEF', "", rot_text=90, alpha=0.6, tipo="Pasillo", name=f"Pas Gon {i+1}")
                xg -= (GONDOLA_PROF + conf['pas_gon'])
            elif rot_g == 270:
                registrar_obj(xg - CABECERA_PROF, yg - GONDOLA_PROF, CABECERA_PROF, GONDOLA_PROF, '#E74C3C', "CAB", rot_text=270, font=5, name=f"Cab Este {i+1}", img_base="gondola_cab")
                for t in range(tramos): registrar_obj(xg - CABECERA_PROF - (t+1)*MOD_3FT, yg - GONDOLA_PROF, MOD_3FT, GONDOLA_PROF, '#ABB2B9', f"Tr{t+1}", rot_text=270, font=6, name=f"Tr{t+1} Tren{i+1}", img_base="gondola_tramo")
                registrar_obj(xg - CABECERA_PROF*2 - largo_g, yg - GONDOLA_PROF, CABECERA_PROF, GONDOLA_PROF, '#E74C3C', "CAB", rot_text=270, font=5, name=f"Cab Oeste {i+1}", img_base="gondola_cab")
                if conf['t_pasillos']: registrar_obj(xg - largo_g - CABECERA_PROF*2, yg - GONDOLA_PROF - conf['pas_gon'], largo_g + CABECERA_PROF*2, conf['pas_gon'], '#EBEDEF', "", alpha=0.6, tipo="Pasillo", name=f"Pas Gon {i+1}")
                yg -= (GONDOLA_PROF + conf['pas_gon'])

            area_exh += GONDOLA_PROF * (largo_g + CABECERA_PROF*2)

    # ==========================================
    # 6. FOODVENIENCE (Módulos Individuales)
    # ==========================================
    if conf['t_cafe']:
        xc, yc = conf['pos_cafe_x'], conf['pos_cafe_y']
        rot_c = conf['rot_cafe']
        mods = conf['cant_cafe']
        
        for m in range(mods):
            if rot_c == 0: registrar_obj(xc + m*MOD_2FT, yc, MOD_2FT, PROF_CAFE, '#FAD7A0', f"C{m+1}", rot_text=0, name=f"Cafe {m}", img_base="cafe")
            elif rot_c == 90: registrar_obj(xc, yc + m*MOD_2FT, PROF_CAFE, MOD_2FT, '#FAD7A0', f"C{m+1}", rot_text=90, name=f"Cafe {m}", img_base="cafe")
            elif rot_c == 180: registrar_obj(xc - (m+1)*MOD_2FT, yc - PROF_CAFE, MOD_2FT, PROF_CAFE, '#FAD7A0', f"C{m+1}", rot_text=180, name=f"Cafe {m}", img_base="cafe")
            elif rot_c == 270: registrar_obj(xc - PROF_CAFE, yc - (m+1)*MOD_2FT, PROF_CAFE, MOD_2FT, '#FAD7A0', f"C{m+1}", rot_text=270, name=f"Cafe {m}", img_base="cafe")
        
        wf = mods * MOD_2FT
        if conf['t_pasillos']:
            if rot_c == 0: registrar_obj(xc, yc + PROF_CAFE, wf, PASILLO_STD, '#FADBD8', "P. CAFE", alpha=0.5, tipo="Pasillo", name="Pas Cafe")
            elif rot_c == 90: registrar_obj(xc + PROF_CAFE, yc, PASILLO_STD, wf, '#FADBD8', "P. CAFE", rot_text=90, alpha=0.5, tipo="Pasillo", name="Pas Cafe")
            elif rot_c == 180: registrar_obj(xc - wf, yc - PASILLO_STD - PROF_CAFE, wf, PASILLO_STD, '#FADBD8', "P. CAFE", alpha=0.5, tipo="Pasillo", name="Pas Cafe")
            elif rot_c == 270: registrar_obj(xc - PASILLO_STD - PROF_CAFE, yc - wf, PASILLO_STD, wf, '#FADBD8', "P. CAFE", rot_text=90, alpha=0.5, tipo="Pasillo", name="Pas Cafe")
        area_exh += (wf * PROF_CAFE)

    # ==========================================
    # 7. PERIMETRALES
    # ==========================================
    if conf['t_perimetral']:
        w_p = conf['pas_peri']
        if conf['peri_izq']: 
            for i in range(conf['tramos_izq']): registrar_obj(0, conf['pos_izq_y'] + (i*MOD_1FT), PROF_PERIMETRO, MOD_1FT, '#D5DBDB', "P", rot_text=90, font=4, name=f"PIzq{i}")
            if conf['t_pasillos']: registrar_obj(PROF_PERIMETRO, 0, w_p, L, '#FCF3CF', "P. PERI", rot_text=90, alpha=0.3, tipo="Pasillo", name="Pas Izq")
            area_exh += (conf['tramos_izq'] * MOD_1FT * PROF_PERIMETRO)
            
        if conf['peri_der']: 
            for i in range(conf['tramos_der']): registrar_obj(W - PROF_PERIMETRO, conf['pos_der_y'] + (i*MOD_1FT), PROF_PERIMETRO, MOD_1FT, '#D5DBDB', "P", rot_text=90, font=4, name=f"PDer{i}")
            if conf['t_pasillos']: registrar_obj(W - PROF_PERIMETRO - w_p, 0, w_p, L, '#FCF3CF', "P. PERI", rot_text=90, alpha=0.3, tipo="Pasillo", name="Pas Der")
            area_exh += (conf['tramos_der'] * MOD_1FT * PROF_PERIMETRO)
            
        if conf['peri_frente']: 
            for i in range(conf['tramos_frente']): registrar_obj(conf['pos_fre_x'] + (i*MOD_1FT), 0, MOD_1FT, PROF_PERIMETRO, '#D5DBDB', "P", font=4, name=f"PFre{i}")
            if conf['t_pasillos']: registrar_obj(0, PROF_PERIMETRO, W, w_p, '#FCF3CF', "P. PERI", alpha=0.3, tipo="Pasillo", name="Pas Fre")
            area_exh += (conf['tramos_frente'] * MOD_1FT * PROF_PERIMETRO)
            
        if conf['peri_fondo']: 
            for i in range(conf['tramos_fondo']): registrar_obj(conf['pos_fon_x'] + (i*MOD_1FT), L - PROF_PERIMETRO, MOD_1FT, PROF_PERIMETRO, '#D5DBDB', "P", font=4, name=f"PFon{i}")
            if conf['t_pasillos']: registrar_obj(0, L - PROF_PERIMETRO - w_p, W, w_p, '#FCF3CF', "P. PERI", alpha=0.3, tipo="Pasillo", name="Pas Fon")
            area_exh += (conf['tramos_fondo'] * MOD_1FT * PROF_PERIMETRO)

    # ==========================================
    # 8. ISLAS INDIVIDUALES
    # ==========================================
    if conf['t_islas']:
        for i in range(conf['cant_islas']):
            ix, iy = conf[f'isla_x_{i}'], conf[f'isla_y_{i}']
            registrar_obj(ix, iy, ISLA_DIM, ISLA_DIM, '#F4D03F', f"E{i+1}", font=6, name=f"Isla {i+1}", img_base="isla", rot_text=0)
            area_exh += (ISLA_DIM * ISLA_DIM)

    pct_exh = (area_exh / area_comercial) * 100 if area_comercial > 0 else 0
    pct_nav = 100 - pct_exh
    
    ax.set_aspect('equal')
    plt.title(f"Store Planning: {conf['nombre_tienda']} | Formato: {clasificar_formato(area_total)} {'(Vista 30°)' if vista_iso else ''}")
    return fig, errores, log_imagenes, pct_exh, pct_nav, area_total, area_comercial, a_op

# --- INTERFAZ STREAMLIT ---
st.set_page_config(layout="wide", page_title="Store Planning OXXO")

conf = {}

with st.sidebar:
    st.title("🏬 Store Planning OXXO")
    
    st.markdown("### 🎨 Motor Gráfico")
    col_t1, col_t2 = st.columns(2)
    conf['modo_render'] = col_t1.toggle("Imágenes PNG", value=False)
    conf['modo_iso'] = col_t2.toggle("Isométrico (30°)", value=False)
    
    nombre_tienda = st.text_input("Nombre de la Tienda", "OXXO Nueva Creación")
    
    st.markdown("### 📊 Auditoría Oficial M2")
    ancho = st.number_input("Ancho (m)", 5.0, 20.0, 12.0, 0.5)
    largo = st.number_input("Profundidad (m)", 5.0, 20.0, 15.0, 0.5)
    
    area_tot = ancho * largo
    st.write(f"**Total:** {area_tot:.1f} m² | `{clasificar_formato(area_tot)}`")
    
    kpi_bod = st.empty()
    kpi_exh = st.empty()
    kpi_nav = st.empty()
    
    st.markdown("---")
    st.write("🕹️ **Panel de Control Paramétrico**")

col_info, col_plot = st.columns([1.2, 2.8])

with col_info:
    with st.expander("1. Acceso y Puertas", expanded=False):
        t_puerta = st.checkbox("Habilitar Acceso", value=False)
        tipo_puerta = st.selectbox("Tipo", ['1 Puerta (90cm)', '2 Puertas (180cm)'], index=1)
        muro_puerta = st.selectbox("Muro", ['Sur', 'Norte', 'Este', 'Oeste'])
        pos_puerta_x = st.number_input("Posición X", 0.0, 100.0, 5.0, 0.1)
        pos_puerta_y = st.number_input("Posición Y (Si Este/Oeste)", 0.0, 100.0, 0.0, 0.1)

    with st.expander("2. Bodega Operativa", expanded=False):
        t_bodega = st.checkbox("Habilitar Bodega", value=False)
        col_bx, col_by = st.columns(2)
        x_bodega = col_bx.number_input("Posición Bodega X", 0.0, 100.0, 0.0, 0.1)
        y_bodega = col_by.number_input("Posición Bodega Y", 0.0, 100.0, 12.0, 0.1)
        col_w, col_h = st.columns(2)
        w_bodega = col_w.number_input("Ancho Bodega", 1.0, 100.0, 12.0, 0.1)
        h_bodega = col_h.number_input("Largo Bodega", 1.0, 100.0, 3.0, 0.1)
        muro_puerta_bod = st.selectbox("Muro Puerta Bodega", ['Sur', 'Norte', 'Este', 'Oeste'])
        pos_puerta_bod = st.slider("Posición Puerta Bodega", 0.0, 10.0, 1.0)
        pas_bod = st.slider("Ancho Pasillo Bodega", 0.8, 1.5, 1.0)

    with st.expander("3. Checkout", expanded=False):
        t_check = st.checkbox("Habilitar Checkout", value=False)
        cant_check = st.slider("Módulos", 2, 7, 3)
        rot_check = st.selectbox("Rotación Checkout (°)", [0, 90, 180, 270])
        pos_chk_x = st.number_input("Check Pos X", 0.0, 100.0, 8.0, 0.1)
        pos_chk_y = st.number_input("Check Pos Y", 0.0, 100.0, 0.0, 0.1)

    with st.expander("4. Cuarto Frío", expanded=False):
        t_frio = st.checkbox("Habilitar Cuarto Frío", value=False)
        forma_frio = st.radio("Formato Frío", ['Lineal'], index=0)
        rot_frio = st.selectbox("Rotación Frío (°)", [0, 90, 180, 270])
        pos_frio_x = st.number_input("Frío Pos X", 0.0, 100.0, 0.0, 0.1)
        pos_frio_y = st.number_input("Frío Pos Y", 0.0, 100.0, 10.0, 0.1)
        cant_frio = st.slider("Puertas", 2, 20, 8)

    with st.expander("5. Góndolas Centrales", expanded=False):
        t_gondolas = st.checkbox("Habilitar Góndolas", value=False)
        rot_gon = st.selectbox("Rotación Góndolas (°)", [0, 90, 180, 270])
        sep_cab = st.checkbox("Separar cabeceras para islas")
        cant_trenes = st.slider("Trenes", 1, 6, 2)
        cant_tramos = st.slider("Tramos por Tren", 1, 8, 3)
        pas_gon = st.slider("Pasillo entre góndolas", 0.9, 1.5, 1.2)
        pos_gon_x = st.number_input("Góndola Pos X", 0.0, 100.0, 4.0, 0.1)
        pos_gon_y = st.number_input("Góndola Pos Y", 0.0, 100.0, 4.0, 0.1)

    with st.expander("6. Foodvenience", expanded=False):
        t_cafe = st.checkbox("Habilitar Foodvenience", value=False)
        forma_cafe = st.radio("Formato Café", ['Lineal'])
        rot_cafe = st.selectbox("Rotación Café (°)", [0, 90, 180, 270])
        pos_cafe_x = st.number_input("Café Pos X", 0.0, 100.0, 0.0, 0.1)
        pos_cafe_y = st.number_input("Café Pos Y", 0.0, 100.0, 0.0, 0.1)
        cant_cafe = st.slider("Módulos Café", 2, 10, 4)

    with st.expander("7. Góndola Perimetral", expanded=False):
        t_perimetral = st.checkbox("Habilitar Perimetrales Manual", value=False)
        col_m1, col_m2 = st.columns(2)
        peri_izq = col_m1.checkbox("Muro Izquierdo", value=False)
        tramos_izq = col_m1.number_input("Tramos Izq", 0, 30, 10)
        pos_izq_y = col_m1.number_input("Inicio Y Izq", 0.0, 100.0, 0.0, 0.1)
        peri_der = col_m2.checkbox("Muro Derecho", value=False)
        tramos_der = col_m2.number_input("Tramos Der", 0, 30, 10)
        pos_der_y = col_m2.number_input("Inicio Y Der", 0.0, 100.0, 0.0, 0.1)
        peri_frente = col_m1.checkbox("Muro Frente", value=False)
        tramos_frente = col_m1.number_input("Tramos Fre", 0, 30, 5)
        pos_fre_x = col_m1.number_input("Inicio X Fre", 0.0, 100.0, 0.0, 0.1)
        peri_fondo = col_m2.checkbox("Muro Fondo", value=False)
        tramos_fondo = col_m2.number_input("Tramos Fon", 0, 30, 5)
        pos_fon_x = col_m2.number_input("Inicio X Fon", 0.0, 100.0, 0.0, 0.1)

    with st.expander("8. Islas Individuales", expanded=False):
        t_islas = st.checkbox("Habilitar Islas Libres", value=False)
        cant_islas = st.slider("Cantidad de Islas", 1, 10, 3)
        for i in range(cant_islas):
            c1, c2 = st.columns(2)
            conf[f'isla_x_{i}'] = c1.number_input(f"Isla {i+1} X", 0.0, 100.0, 2.0 + (i*1.0), 0.1)
            conf[f'isla_y_{i}'] = c2.number_input(f"Isla {i+1} Y", 0.0, 100.0, 2.0, 0.1)
            
    with st.expander("⚙️ Configuraciones Globales", expanded=False):
        t_pasillos = st.checkbox("Habilitar Blindaje de Pasillos", value=False)
        pas_poder = st.slider("Ancho Pasillo Poder", 0.9, 2.5, 1.8)

# Compilación Final
conf.update({
    'nombre_tienda': nombre_tienda,
    'ancho': ancho, 'largo': largo, 
    't_puerta': t_puerta, 'tipo_puerta': tipo_puerta, 'muro_puerta': muro_puerta, 'pos_puerta_x': pos_puerta_x, 'pos_puerta_y': pos_puerta_y,
    't_bodega': t_bodega, 'x_bodega': x_bodega, 'y_bodega': y_bodega, 'w_bodega': w_bodega, 'h_bodega': h_bodega, 'pas_bod': pas_bod, 'muro_puerta_bod': muro_puerta_bod, 'pos_puerta_bod': pos_puerta_bod,
    't_pasillos': t_pasillos, 'pas_poder': pas_poder,
    't_check': t_check, 'rot_check': rot_check, 'cant_check': cant_check, 'pos_chk_x': pos_chk_x, 'pos_chk_y': pos_chk_y,
    't_frio': t_frio, 'forma_frio': forma_frio, 'rot_frio': rot_frio, 'cant_frio': cant_frio, 'pos_frio_x': pos_frio_x, 'pos_frio_y': pos_frio_y,
    't_gondolas': t_gondolas, 'rot_gon': rot_gon, 'sep_cab': sep_cab, 'cant_trenes': cant_trenes, 'cant_tramos': cant_tramos, 'pas_gon': pas_gon, 'pos_gon_x': pos_gon_x, 'pos_gon_y': pos_gon_y,
    't_cafe': t_cafe, 'forma_cafe': forma_cafe, 'rot_cafe': rot_cafe, 'cant_cafe': cant_cafe, 'pos_cafe_x': pos_cafe_x, 'pos_cafe_y': pos_cafe_y,
    't_perimetral': t_perimetral, 'peri_izq': peri_izq, 'tramos_izq': tramos_izq, 'pos_izq_y': pos_izq_y, 'peri_der': peri_der, 'tramos_der': tramos_der, 'pos_der_y': pos_der_y, 'peri_frente': peri_frente, 'tramos_frente': tramos_frente, 'pos_fre_x': pos_fre_x, 'peri_fondo': peri_fondo, 'tramos_fondo': tramos_fondo, 'pos_fon_x': pos_fon_x,
    't_islas': t_islas, 'cant_islas': cant_islas
})

with col_plot:
    fig, errores, log_imgs, pct_exh, pct_nav, a_tot, a_com, a_op_real = dibujar_layout_oxxo_v27(conf)
    st.pyplot(fig)
    
    col_pdf, col_svg = st.columns(2)
    buf_pdf = io.BytesIO()
    fig.savefig(buf_pdf, format="pdf", bbox_inches='tight')
    col_pdf.download_button("📥 Descargar Plano PDF", data=buf_pdf.getvalue(), file_name=f"{nombre_tienda}.pdf", mime="application/pdf", use_container_width=True)
    
    buf_svg = io.BytesIO()
    fig.savefig(buf_svg, format="svg", bbox_inches='tight')
    col_svg.download_button("📐 Descargar Vectorial (SVG)", data=buf_svg.getvalue(), file_name=f"{nombre_tienda}.svg", mime="image/svg+xml", use_container_width=True)

    if conf.get('modo_render') and log_imgs:
        with st.expander("🔍 Consola de Motor de Imágenes", expanded=True):
            for msg in set(log_imgs):
                if "✅" in msg: st.success(msg)
                elif "⚠️" in msg: st.warning(msg)
                else: st.error(msg)
    
    if errores:
        st.error("🚨 **Motor de Colisiones Activo:**")
        for err in errores: st.warning(f"• {err}")

pct_op = (a_op_real / a_tot) * 100 if a_tot > 0 else 0
if 18 <= pct_op <= 22: kpi_bod.success(f"Bodega: {pct_op:.1f}% (Meta 20%)")
else: kpi_bod.error(f"Bodega: {pct_op:.1f}% (Meta 20%)")

kpi_exh.metric("Rentabilidad (30-40%)", f"{pct_exh:.1f}%", "Aceptado" if 30 <= pct_exh <= 40 else "Revisar")
kpi_nav.metric("Experiencia (60-70%)", f"{pct_nav:.1f}%", "Aceptado" if 60 <= pct_nav <= 70 else "Revisar")