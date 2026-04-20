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
    if m2 <= 15: return "BOOTH"
    elif m2 <= 36: return "MINI"
    elif m2 <= 56: return "MINI 2"
    elif m2 <= 77: return "MEDIA"
    elif m2 <= 98: return "MEDIA 2"
    elif m2 <= 117: return "REGULAR"
    elif m2 <= 135: return "MÍNIMO 2"
    elif m2 <= 154: return "ÓPTIMO"
    elif m2 <= 170: return "ÓPTIMO 2"
    elif m2 <= 250: return "MÁXIMO"
    else: return "MEGA"

def colisiona(x, y, w, h, lista_obstaculos):
    margen = 0.05
    for (ox, oy, ow, oh, nombre) in lista_obstaculos:
        if not (x + w <= ox + margen or x >= ox + ow - margen or y + h <= oy + margen or y >= oy + oh - margen):
            return True, nombre
    return False, ""

def normalizar_rotacion(r):
    return (r % 360)

def to_iso(x, y):
    ang = math.radians(30)
    iso_x = (x - y) * math.cos(ang)
    iso_y = (x + y) * math.sin(ang)
    return iso_x, iso_y

# --- MOTOR DE BLOQUES (V30.0) ---
def dibujar_layout_oxxo_v30(conf):
    W, L = conf['ancho'], conf['largo']
    vista_iso = conf.get('modo_iso', False)

    fig, ax = plt.subplots(figsize=(16, 12))
    
    # DIBUJO DE REJILLA Y EJES
    if vista_iso:
        ax.axis('off')
        # Lineas y Numeración
        for ix in range(int(W)+1):
            x1, y1 = to_iso(ix, 0); x2, y2 = to_iso(ix, L)
            ax.plot([x1, x2], [y1, y2], color='#E5E7E9', lw=0.5, zorder=0)
            tx, ty = to_iso(ix, -0.4)
            ax.text(tx, ty, str(ix), ha='center', va='center', fontsize=6, color='gray')
        for iy in range(int(L)+1):
            x1, y1 = to_iso(0, iy); x2, y2 = to_iso(W, iy)
            ax.plot([x1, x2], [y1, y2], color='#E5E7E9', lw=0.5, zorder=0)
            tx, ty = to_iso(-0.4, iy)
            ax.text(tx, ty, str(iy), ha='center', va='center', fontsize=6, color='gray')
        
        # Etiquetas de Ejes
        tx, ty = to_iso(W/2, -1.2)
        ax.text(tx, ty, "EJE X (Ancho)", ha='center', va='center', fontsize=9, weight='bold', color='#2E4053')
        tx, ty = to_iso(-1.2, L/2)
        ax.text(tx, ty, "EJE Y (Profundidad)", ha='center', va='center', fontsize=9, weight='bold', color='#2E4053')

        ax.set_xlim(-L*0.9, W*0.9)
        ax.set_ylim(-1.5, (W+L)*0.6)
    else:
        ax.set_xlim(0, W)
        ax.set_ylim(0, L)
        ax.xaxis.set_major_locator(MultipleLocator(1))
        ax.yaxis.set_major_locator(MultipleLocator(1))
        ax.grid(which='major', color='#E5E7E9', linestyle='-', linewidth=0.5, zorder=0)
        ax.set_xlabel("EJE X (Ancho)", fontsize=10, weight='bold', color='#2E4053')
        ax.set_ylabel("EJE Y (Profundidad)", fontsize=10, weight='bold', color='#2E4053')

    obs_fisicos = []  
    obs_pasillos = [] 
    errores = []
    log_imagenes = []
    area_exh = 0
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    
    def registrar_bloque(x, y, w, h, color, texto="", rot_text=0, tipo="Fisico", name="Objeto", img_name_full=None, draw_fallback=True):
        choca = False
        obj_chocado = ""
        ec = 'black' if color != 'none' else 'none'
        lw = 1 if color != 'none' else 0

        z_calc = 1000 - int((x + y) * 10) if tipo in ["Fisico", "Visual"] else 2

        if (x < -0.05 or y < -0.05 or x + w > W + 0.05 or y + h > L + 0.05) and tipo != "Visual":
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

            if choca and obj_chocado and tipo != "Visual": 
                errores.append(f"{name} choca con {obj_chocado}.")
                ec, lw = 'red', 2
                z_calc = 2000 
            elif not choca:
                if tipo == "Fisico": obs_fisicos.append((x, y, w, h, name))
                elif tipo == "Pasillo": obs_pasillos.append((x, y, w, h, name))

        dibujado_imagen = False
        # SEGURO DE MINÚSCULAS PARA NOMBRES DE ARCHIVO
        if conf.get('modo_render', False) and img_name_full and not choca:
            nombre_archivo = f"{img_name_full.lower()}.png"
            ruta_img = os.path.join(BASE_DIR, "assets", nombre_archivo)
            
            if os.path.exists(ruta_img):
                try:
                    img = mpimg.imread(ruta_img)
                    overlap = 0.02 
                    
                    if vista_iso:
                        img_h, img_w = img.shape[:2]
                        aspect = img_w / img_h
                        scale = math.hypot(w, h) * 1.0
                        ext_w = scale + overlap
                        ext_h = (scale / aspect) + overlap
                        
                        icx, icy = to_iso(x + w/2, y + h/2)
                        icy += ext_h * 0.15 
                        ax.imshow(img, extent=[icx - ext_w/2, icx + ext_w/2, icy - ext_h/2, icy + ext_h/2], zorder=z_calc)
                    else:
                        ax.imshow(img, extent=[x - overlap, x + w + overlap, y - overlap, y + h + overlap], zorder=z_calc)
                    
                    dibujado_imagen = True
                    if f"✅ OK: {nombre_archivo}" not in log_imagenes: log_imagenes.append(f"✅ OK: {nombre_archivo}")
                except Exception as e:
                    log_imagenes.append(f"❌ Error: {nombre_archivo}")
            else:
                if f"⚠️ Falta: {nombre_archivo}" not in log_imagenes: log_imagenes.append(f"⚠️ Falta: {nombre_archivo}")

        if not dibujado_imagen and draw_fallback and color != 'none':
            if vista_iso:
                pts = [to_iso(x, y), to_iso(x+w, y), to_iso(x+w, y+h), to_iso(x, y+h)]
                ax.add_patch(patches.Polygon(pts, closed=True, color=color, ec=ec, lw=lw, alpha=0.8, zorder=z_calc))
                if texto:
                    icx, icy = to_iso(x + w/2, y + h/2)
                    ax.text(icx, icy, texto, ha='center', va='center', fontsize=5, color='black', weight='bold', zorder=z_calc+1)
            else:
                ax.add_patch(patches.Rectangle((x, y), w, h, color=color, ec=ec, lw=lw, alpha=0.8, zorder=z_calc))
                if texto:
                    rot_visual = rot_text % 360
                    if 90 < rot_visual < 270: rot_visual -= 180
                    ax.text(x + w/2, y + h/2, texto, ha='center', va='center', rotation=rot_visual, fontsize=5, color='black', weight='bold', zorder=z_calc+1)
        
        return w, h, dibujado_imagen

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
        registrar_bloque(xb, yb, w_b, h_b, '#D2B48C', f"BODEGA\n({a_op:.1f}m²)", name="Bodega")
        
        # Pasillo y Racks Internos Visuales
        registrar_bloque(xb + 0.5, yb + 0.5, w_b - 1.0, h_b - 1.0, '#E59866', "Int. Bodega", tipo="Pasillo", name="Interior Bodega")
        
        # Puerta Bodega
        pos_pb = conf['pos_puerta_bod']
        if conf['muro_puerta_bod'] == 'Sur': registrar_bloque(xb + pos_pb, yb, 0.9, 0.2, 'brown', tipo="Visual")
        elif conf['muro_puerta_bod'] == 'Norte': registrar_bloque(xb + pos_pb, yb + h_b - 0.2, 0.9, 0.2, 'brown', tipo="Visual")
        elif conf['muro_puerta_bod'] == 'Oeste': registrar_bloque(xb, yb + pos_pb, 0.2, 0.9, 'brown', tipo="Visual")
        elif conf['muro_puerta_bod'] == 'Este': registrar_bloque(xb + w_b - 0.2, yb + pos_pb, 0.2, 0.9, 'brown', tipo="Visual")

    area_comercial = area_total - a_op

    # ==========================================
    # 2. ACCESO Y PASILLOS DE PODER
    # ==========================================
    if conf['t_puerta']:
        pw = 0.9 if conf['tipo_puerta'] == '1 Puerta (90cm)' else 1.80
        xp, yp = conf['pos_puerta_x'], conf['pos_puerta_y']
        w_p = pw if conf['muro_puerta'] in ['Sur', 'Norte'] else 0.2
        h_p = 0.2 if conf['muro_puerta'] in ['Sur', 'Norte'] else pw
        registrar_bloque(xp, yp, w_p, h_p, 'red', "ACCESO", name="Acceso")

        # Zona de Descompresión (Círculo Isométrico)
        if vista_iso:
            cx, cy = xp + w_p/2, yp + h_p/2
            pts = []
            for angle in range(0, 360, 10):
                rad = math.radians(angle)
                pts.append(to_iso(cx + 2.0 * math.cos(rad), cy + 2.0 * math.sin(rad)))
            ax.add_patch(patches.Polygon(pts, closed=True, color='#85C1E9', alpha=0.2, zorder=1))
        else:
            ax.add_patch(patches.Circle((xp + w_p/2, yp + h_p/2), 2.0, color='#85C1E9', alpha=0.2, zorder=1))

        if conf['t_pasillos']:
            wpod = conf['pas_poder']
            if conf['muro_puerta'] == 'Sur': registrar_bloque(xp - (wpod-pw)/2, yp, wpod, L - yp, '#EBF5FB', "P. PODER", rot_text=90, tipo="Pasillo", name="Pasillo Poder")
            elif conf['muro_puerta'] == 'Norte': registrar_bloque(xp - (wpod-pw)/2, 0, wpod, yp, '#EBF5FB', "P. PODER", rot_text=90, tipo="Pasillo", name="Pasillo Poder")
            elif conf['muro_puerta'] == 'Este': registrar_bloque(0, yp - (wpod-pw)/2, xp, wpod, '#EBF5FB', "P. PODER", tipo="Pasillo", name="Pasillo Poder")
            elif conf['muro_puerta'] == 'Oeste': registrar_bloque(xp, yp - (wpod-pw)/2, W - xp, wpod, '#EBF5FB', "P. PODER", tipo="Pasillo", name="Pasillo Poder")

    # ==========================================
    # 3. CHECKOUT
    # ==========================================
    if conf['t_check']:
        mods = conf['cant_check']
        xc, yc = conf['pos_chk_x'], conf['pos_chk_y']
        rot = conf['rot_check']
        w_b = mods * MOD_2FT
        h_b = PROF_CONTRA + PROF_CAJERO + PROF_CHECK
        nombre_img = f"checkout_{mods}_modulo_{rot}"

        if rot == 0: registrar_bloque(xc, yc, w_b, h_b, '#ABEBC6', f"CHECKOUT\n{mods} Mods", rot_text=0, name="Checkout", img_name_full=nombre_img)
        elif rot == 90: registrar_bloque(xc, yc, h_b, w_b, '#ABEBC6', f"CHECKOUT\n{mods} Mods", rot_text=90, name="Checkout", img_name_full=nombre_img)
        elif rot == 180: registrar_bloque(xc, yc, w_b, h_b, '#ABEBC6', f"CHECKOUT\n{mods} Mods", rot_text=180, name="Checkout", img_name_full=nombre_img)
        elif rot == 270: registrar_bloque(xc, yc, h_b, w_b, '#ABEBC6', f"CHECKOUT\n{mods} Mods", rot_text=270, name="Checkout", img_name_full=nombre_img)
        area_exh += (w_b * PROF_CHECK)

    # ==========================================
    # 4. CUARTO FRÍO (Lineal y Escuadra)
    # ==========================================
    if conf['t_frio']:
        xf, yf = conf['pos_frio_x'], conf['pos_frio_y']
        rot = conf['rot_frio']
        forma = conf['forma_frio']
        
        if forma == 'Lineal':
            ptas = conf['cant_frio']
            largo_f = ptas * MOD_2FT
            nombre_img = f"cuarto_frio_lineal_{ptas}_puertas_{rot}"
            
            bw = largo_f if rot in [0, 180] else PROF_FRIO
            bh = PROF_FRIO if rot in [0, 180] else largo_f
            
            _, _, img_ok = registrar_bloque(xf, yf, bw, bh, '#AED6F1', f"FRÍO\n{ptas} Pts", rot_text=rot, name="Frio", img_name_full=nombre_img)
            
            # Dibujar Puertas Visuales si no hay Render
            if not img_ok:
                for p in range(ptas):
                    if rot == 0: registrar_bloque(xf + p*MOD_2FT, yf, MOD_2FT, 0.15, '#2874A6', tipo="Visual")
                    elif rot == 90: registrar_bloque(xf + PROF_FRIO - 0.15, yf + p*MOD_2FT, 0.15, MOD_2FT, '#2874A6', tipo="Visual")
                    elif rot == 180: registrar_bloque(xf + p*MOD_2FT, yf + PROF_FRIO - 0.15, MOD_2FT, 0.15, '#2874A6', tipo="Visual")
                    elif rot == 270: registrar_bloque(xf, yf + p*MOD_2FT, 0.15, MOD_2FT, '#2874A6', tipo="Visual")
            area_exh += (largo_f * PROF_FRIO)

        elif forma == 'Escuadra':
            p1, p2 = conf['ptas_frio_1'], conf['ptas_frio_2']
            w1, w2 = p1 * MOD_2FT, p2 * MOD_2FT
            nombre_img = f"cuarto_frio_escuadra_{p1}x{p2}_{rot}"

            # Bounding Box de la Escuadra
            if rot == 0: bb_x, bb_y, bb_w, bb_h = xf, yf, PROF_FRIO + w1, PROF_FRIO + w2
            elif rot == 90: bb_x, bb_y, bb_w, bb_h = xf - w2, yf, PROF_FRIO + w2, PROF_FRIO + w1
            elif rot == 180: bb_x, bb_y, bb_w, bb_h = xf - w1, yf - w2, PROF_FRIO + w1, PROF_FRIO + w2
            elif rot == 270: bb_x, bb_y, bb_w, bb_h = xf, yf - w1, PROF_FRIO + w2, PROF_FRIO + w1

            # Intentar Render Completo (Solo visual para no bloquear espacio vacío)
            _, _, img_ok = registrar_bloque(bb_x, bb_y, bb_w, bb_h, 'none', name="Frio_IMG", img_name_full=nombre_img, tipo="Visual")

            # Registrar Bloques Físicos de Colisión (y dibujarlos si no hay render)
            registrar_bloque(xf, yf, PROF_FRIO, PROF_FRIO, '#AED6F1', "PIV", rot_text=rot, name="Frio Pivote", draw_fallback=not img_ok)
            
            if rot == 0:
                registrar_bloque(xf + PROF_FRIO, yf, w1, PROF_FRIO, '#AED6F1', f"L1\n{p1}p", rot_text=0, name="Frio L1", draw_fallback=not img_ok)
                if not img_ok: [registrar_bloque(xf + PROF_FRIO + p*MOD_2FT, yf, MOD_2FT, 0.15, '#2874A6', tipo="Visual") for p in range(p1)]
                registrar_bloque(xf, yf + PROF_FRIO, PROF_FRIO, w2, '#AED6F1', f"L2\n{p2}p", rot_text=90, name="Frio L2", draw_fallback=not img_ok)
                if not img_ok: [registrar_bloque(xf + PROF_FRIO - 0.15, yf + PROF_FRIO + p*MOD_2FT, 0.15, MOD_2FT, '#2874A6', tipo="Visual") for p in range(p2)]
            
            elif rot == 90:
                registrar_bloque(xf, yf + PROF_FRIO, PROF_FRIO, w1, '#AED6F1', f"L1\n{p1}p", rot_text=90, name="Frio L1", draw_fallback=not img_ok)
                if not img_ok: [registrar_bloque(xf + PROF_FRIO - 0.15, yf + PROF_FRIO + p*MOD_2FT, 0.15, MOD_2FT, '#2874A6', tipo="Visual") for p in range(p1)]
                registrar_bloque(xf - w2, yf, w2, PROF_FRIO, '#AED6F1', f"L2\n{p2}p", rot_text=0, name="Frio L2", draw_fallback=not img_ok)
                if not img_ok: [registrar_bloque(xf - (p+1)*MOD_2FT, yf + PROF_FRIO - 0.15, MOD_2FT, 0.15, '#2874A6', tipo="Visual") for p in range(p2)]
            
            elif rot == 180:
                registrar_bloque(xf - w1, yf, w1, PROF_FRIO, '#AED6F1', f"L1\n{p1}p", rot_text=0, name="Frio L1", draw_fallback=not img_ok)
                if not img_ok: [registrar_bloque(xf - (p+1)*MOD_2FT, yf + PROF_FRIO - 0.15, MOD_2FT, 0.15, '#2874A6', tipo="Visual") for p in range(p1)]
                registrar_bloque(xf, yf - w2, PROF_FRIO, w2, '#AED6F1', f"L2\n{p2}p", rot_text=90, name="Frio L2", draw_fallback=not img_ok)
                if not img_ok: [registrar_bloque(xf, yf - (p+1)*MOD_2FT, 0.15, MOD_2FT, '#2874A6', tipo="Visual") for p in range(p2)]
            
            elif rot == 270:
                registrar_bloque(xf, yf - w1, PROF_FRIO, w1, '#AED6F1', f"L1\n{p1}p", rot_text=90, name="Frio L1", draw_fallback=not img_ok)
                if not img_ok: [registrar_bloque(xf, yf - (p+1)*MOD_2FT, 0.15, MOD_2FT, '#2874A6', tipo="Visual") for p in range(p1)]
                registrar_bloque(xf + PROF_FRIO, yf, w2, PROF_FRIO, '#AED6F1', f"L2\n{p2}p", rot_text=0, name="Frio L2", draw_fallback=not img_ok)
                if not img_ok: [registrar_bloque(xf + PROF_FRIO + p*MOD_2FT, yf, MOD_2FT, 0.15, '#2874A6', tipo="Visual") for p in range(p2)]
            
            area_exh += (PROF_FRIO*PROF_FRIO) + ((p1+p2)*MOD_2FT*PROF_FRIO)

    # ==========================================
    # 5. GÓNDOLAS CENTRALES
    # ==========================================
    if conf['t_gondolas']:
        xg, yg = conf['pos_gon_x'], conf['pos_gon_y']
        rot = conf['rot_gon'] 
        tramos = conf['cant_tramos']
        largo_g = (tramos * MOD_3FT) + (CABECERA_PROF * 2)
        nombre_img = f"gondola_central_{tramos}_tramo_{rot}"
        
        for i in range(conf['cant_trenes']):
            if rot == 0 or rot == 180: 
                registrar_bloque(xg, yg, GONDOLA_PROF, largo_g, '#ABB2B9', f"GÓNDOLA\n{tramos} Tr", rot_text=rot, name=f"Gondola {i+1}", img_name_full=nombre_img)
                xg += GONDOLA_PROF + conf['pas_gon']
            elif rot == 90 or rot == 270: 
                registrar_bloque(xg, yg, largo_g, GONDOLA_PROF, '#ABB2B9', f"GÓNDOLA\n{tramos} Tr", rot_text=rot, name=f"Gondola {i+1}", img_name_full=nombre_img)
                yg += GONDOLA_PROF + conf['pas_gon']
            area_exh += (GONDOLA_PROF * largo_g)

    # ==========================================
    # 6. FOODVENIENCE (Lineal y Escuadra)
    # ==========================================
    if conf['t_cafe']:
        xc, yc = conf['pos_cafe_x'], conf['pos_cafe_y']
        rot = conf['rot_cafe']
        forma = conf['forma_cafe']
        
        if forma == 'Lineal':
            mods = conf['cant_cafe']
            largo_c = mods * MOD_2FT
            nombre_img = f"cafe_lineal_{mods}_modulo_{rot}"

            bw = largo_c if rot in [0, 180] else PROF_CAFE
            bh = PROF_CAFE if rot in [0, 180] else largo_c
            
            _, _, img_ok = registrar_bloque(xc, yc, bw, bh, '#FAD7A0', f"CAFÉ\n{mods} Mod", rot_text=rot, name="Cafe", img_name_full=nombre_img)
            
            # Divisiones visuales
            if not img_ok:
                for p in range(mods):
                    if rot == 0: registrar_bloque(xc + p*MOD_2FT, yc, 0.05, PROF_CAFE, '#E59866', tipo="Visual")
                    elif rot == 90: registrar_bloque(xc, yc + p*MOD_2FT, PROF_CAFE, 0.05, '#E59866', tipo="Visual")
                    elif rot == 180: registrar_bloque(xc + p*MOD_2FT, yc, 0.05, PROF_CAFE, '#E59866', tipo="Visual")
                    elif rot == 270: registrar_bloque(xc, yc + p*MOD_2FT, PROF_CAFE, 0.05, '#E59866', tipo="Visual")
            area_exh += (largo_c * PROF_CAFE)

        elif forma == 'Escuadra':
            p1, p2 = conf['mods_cafe_1'], conf['mods_cafe_2']
            w1, w2 = p1 * MOD_2FT, p2 * MOD_2FT
            nombre_img = f"cafe_escuadra_{p1}x{p2}_{rot}"

            if rot == 0: bb_x, bb_y, bb_w, bb_h = xc, yc, PROF_CAFE + w1, PROF_CAFE + w2
            elif rot == 90: bb_x, bb_y, bb_w, bb_h = xc - w2, yc, PROF_CAFE + w2, PROF_CAFE + w1
            elif rot == 180: bb_x, bb_y, bb_w, bb_h = xc - w1, yc - w2, PROF_CAFE + w1, PROF_CAFE + w2
            elif rot == 270: bb_x, bb_y, bb_w, bb_h = xc, yc - w1, PROF_CAFE + w2, PROF_CAFE + w1

            _, _, img_ok = registrar_bloque(bb_x, bb_y, bb_w, bb_h, 'none', name="Cafe_IMG", img_name_full=nombre_img, tipo="Visual")

            registrar_bloque(xc, yc, PROF_CAFE, PROF_CAFE, '#FAD7A0', "PIV", rot_text=rot, name="Cafe Pivote", draw_fallback=not img_ok)
            
            if rot == 0:
                registrar_bloque(xc + PROF_CAFE, yc, w1, PROF_CAFE, '#FAD7A0', f"L1\n{p1}m", rot_text=0, name="Cafe L1", draw_fallback=not img_ok)
                registrar_bloque(xc, yc + PROF_CAFE, PROF_CAFE, w2, '#FAD7A0', f"L2\n{p2}m", rot_text=90, name="Cafe L2", draw_fallback=not img_ok)
            elif rot == 90:
                registrar_bloque(xc, yc + PROF_CAFE, PROF_CAFE, w1, '#FAD7A0', f"L1\n{p1}m", rot_text=90, name="Cafe L1", draw_fallback=not img_ok)
                registrar_bloque(xc - w2, yc, w2, PROF_CAFE, '#FAD7A0', f"L2\n{p2}m", rot_text=0, name="Cafe L2", draw_fallback=not img_ok)
            elif rot == 180:
                registrar_bloque(xc - w1, yc, w1, PROF_CAFE, '#FAD7A0', f"L1\n{p1}m", rot_text=0, name="Cafe L1", draw_fallback=not img_ok)
                registrar_bloque(xc, yc - w2, PROF_CAFE, w2, '#FAD7A0', f"L2\n{p2}m", rot_text=90, name="Cafe L2", draw_fallback=not img_ok)
            elif rot == 270:
                registrar_bloque(xc, yc - w1, PROF_CAFE, w1, '#FAD7A0', f"L1\n{p1}m", rot_text=90, name="Cafe L1", draw_fallback=not img_ok)
                registrar_bloque(xc + PROF_CAFE, yc, w2, PROF_CAFE, '#FAD7A0', f"L2\n{p2}m", rot_text=0, name="Cafe L2", draw_fallback=not img_ok)
            
            area_exh += (PROF_CAFE*PROF_CAFE) + ((p1+p2)*MOD_2FT*PROF_CAFE)

    # ==========================================
    # 7. PERIMETRALES Y PASILLOS (UI Restoration)
    # ==========================================
    if conf['t_perimetral']:
        w_p = conf['pas_peri']
        if conf['peri_izq']: 
            for i in range(conf['tramos_izq']): registrar_bloque(0, conf['pos_izq_y'] + (i*MOD_1FT), PROF_PERIMETRO, MOD_1FT, '#D5DBDB', "P", rot_text=90, name=f"PIzq{i}")
            if conf['t_pasillos']: registrar_bloque(PROF_PERIMETRO, 0, w_p, L, '#FCF3CF', "P. PERI", rot_text=90, tipo="Pasillo", name="Pas Izq")
            area_exh += (conf['tramos_izq'] * MOD_1FT * PROF_PERIMETRO)
            
        if conf['peri_der']: 
            for i in range(conf['tramos_der']): registrar_bloque(W - PROF_PERIMETRO, conf['pos_der_y'] + (i*MOD_1FT), PROF_PERIMETRO, MOD_1FT, '#D5DBDB', "P", rot_text=90, name=f"PDer{i}")
            if conf['t_pasillos']: registrar_bloque(W - PROF_PERIMETRO - w_p, 0, w_p, L, '#FCF3CF', "P. PERI", rot_text=90, tipo="Pasillo", name="Pas Der")
            area_exh += (conf['tramos_der'] * MOD_1FT * PROF_PERIMETRO)
            
        if conf['peri_frente']: 
            for i in range(conf['tramos_frente']): registrar_bloque(conf['pos_fre_x'] + (i*MOD_1FT), 0, MOD_1FT, PROF_PERIMETRO, '#D5DBDB', "P", name=f"PFre{i}")
            if conf['t_pasillos']: registrar_bloque(0, PROF_PERIMETRO, W, w_p, '#FCF3CF', "P. PERI", tipo="Pasillo", name="Pas Fre")
            area_exh += (conf['tramos_frente'] * MOD_1FT * PROF_PERIMETRO)
            
        if conf['peri_fondo']: 
            for i in range(conf['tramos_fondo']): registrar_bloque(conf['pos_fon_x'] + (i*MOD_1FT), L - PROF_PERIMETRO, MOD_1FT, PROF_PERIMETRO, '#D5DBDB', "P", name=f"PFon{i}")
            if conf['t_pasillos']: registrar_bloque(0, L - PROF_PERIMETRO - w_p, W, w_p, '#FCF3CF', "P. PERI", tipo="Pasillo", name="Pas Fon")
            area_exh += (conf['tramos_fondo'] * MOD_1FT * PROF_PERIMETRO)

    # ==========================================
    # 8. ISLAS INDIVIDUALES
    # ==========================================
    if conf['t_islas']:
        for i in range(conf['cant_islas']):
            ix, iy = conf[f'isla_x_{i}'], conf[f'isla_y_{i}']
            nombre_img = f"isla_1_racks_0"
            registrar_bloque(ix, iy, ISLA_DIM, ISLA_DIM, '#F4D03F', f"ISLA {i+1}", rot_text=0, name=f"Isla {i+1}", img_name_full=nombre_img)
            area_exh += (ISLA_DIM * ISLA_DIM)

    pct_exh = (area_exh / area_comercial) * 100 if area_comercial > 0 else 0
    pct_nav = 100 - pct_exh
    
    ax.set_aspect('equal')
    return fig, errores, log_imagenes, pct_exh, pct_nav, area_total, area_comercial, a_op

# --- INTERFAZ STREAMLIT ---
st.set_page_config(layout="wide", page_title="Store Planning OXXO")
conf = {}

with st.sidebar:
    st.image("https://upload.wikimedia.org/wikipedia/commons/thumb/a/a2/Logo_OXXO.svg/1200px-Logo_OXXO.svg.png", width=150)
    st.title("Store Planning")
    
    st.markdown("### 🎨 Motor Render 3D/2.5D")
    col_t1, col_t2 = st.columns(2)
    conf['modo_render'] = col_t1.toggle("Imágenes PNG", value=False)
    conf['modo_iso'] = col_t2.toggle("Isométrico (30°)", value=False)
    
    st.markdown("---")
    st.markdown("### 📐 Dimensiones Base")
    nombre_tienda = st.text_input("Nombre Tienda", "OXXO Nueva Creación")
    ancho = st.number_input("Ancho (m)", 5.0, 20.0, 12.0, 0.5)
    largo = st.number_input("Profundidad (m)", 5.0, 20.0, 15.0, 0.5)
    
    st.markdown("---")
    st.write("🕹️ **Mobiliario Paramétrico**")

    with st.expander("🚪 Acceso y Puertas", expanded=False):
        t_puerta = st.checkbox("Habilitar Acceso", value=False)
        tipo_puerta = st.selectbox("Tipo", ['1 Puerta (90cm)', '2 Puertas (180cm)'], index=1)
        muro_puerta = st.selectbox("Muro", ['Sur', 'Norte', 'Este', 'Oeste'])
        pos_puerta_x = st.number_input("Posición X", 0.0, 100.0, 5.0, 0.1)
        pos_puerta_y = st.number_input("Posición Y (Si Este/Oeste)", 0.0, 100.0, 0.0, 0.1)

    with st.expander("📦 Bodega Operativa", expanded=False):
        t_bodega = st.checkbox("Habilitar Bodega", value=False)
        col_bx, col_by = st.columns(2)
        x_bodega = col_bx.number_input("Pos X Bodega", 0.0, 100.0, 0.0, 0.1)
        y_bodega = col_by.number_input("Pos Y Bodega", 0.0, 100.0, 12.0, 0.1)
        col_w, col_h = st.columns(2)
        w_bodega = col_w.number_input("Ancho Bod", 1.0, 100.0, 12.0, 0.1)
        h_bodega = col_h.number_input("Largo Bod", 1.0, 100.0, 3.0, 0.1)
        muro_puerta_bod = st.selectbox("Muro Pta Bodega", ['Sur', 'Norte', 'Este', 'Oeste'])
        pos_puerta_bod = st.slider("Posición Pta Bodega", 0.0, 10.0, 1.0)

    with st.expander("💳 Checkout", expanded=False):
        t_check = st.checkbox("Habilitar Checkout", value=False)
        cant_check = st.slider("Módulos", 2, 7, 3)
        rot_check = st.selectbox("Giro Checkout (°)", [0, 90, 180, 270])
        pos_chk_x = st.number_input("Check Pos X", 0.0, 100.0, 8.0, 0.1)
        pos_chk_y = st.number_input("Check Pos Y", 0.0, 100.0, 0.0, 0.1)

    with st.expander("❄️ Cuarto Frío", expanded=False):
        t_frio = st.checkbox("Habilitar Cuarto Frío", value=False)
        forma_frio = st.radio("Formato Frío", ['Lineal', 'Escuadra'])
        rot_frio = st.selectbox("Giro Frío (°)", [0, 90, 180, 270])
        pos_frio_x = st.number_input("Frío Pos X", 0.0, 100.0, 0.0, 0.1)
        pos_frio_y = st.number_input("Frío Pos Y", 0.0, 100.0, 10.0, 0.1)
        if forma_frio == 'Lineal':
            cant_frio = st.slider("Puertas", 2, 20, 8)
        else:
            col_f1, col_f2 = st.columns(2)
            ptas_frio_1 = col_f1.number_input("Puertas L1", 1, 15, 5)
            ptas_frio_2 = col_f2.number_input("Puertas L2", 1, 15, 3)

    with st.expander("🛒 Góndolas Centrales", expanded=False):
        t_gondolas = st.checkbox("Habilitar Góndolas", value=False)
        rot_gon = st.selectbox("Giro Góndolas (°)", [0, 90, 180, 270])
        cant_trenes = st.slider("Trenes", 1, 6, 2)
        cant_tramos = st.slider("Tramos por Tren", 1, 8, 3)
        pos_gon_x = st.number_input("Góndola Pos X", 0.0, 100.0, 4.0, 0.1)
        pos_gon_y = st.number_input("Góndola Pos Y", 0.0, 100.0, 4.0, 0.1)

    with st.expander("☕ Foodvenience (Café)", expanded=False):
        t_cafe = st.checkbox("Habilitar Café", value=False)
        forma_cafe = st.radio("Formato Café", ['Lineal', 'Escuadra'])
        rot_cafe = st.selectbox("Giro Café (°)", [0, 90, 180, 270])
        pos_cafe_x = st.number_input("Café Pos X", 0.0, 100.0, 0.0, 0.1)
        pos_cafe_y = st.number_input("Café Pos Y", 0.0, 100.0, 0.0, 0.1)
        if forma_cafe == 'Lineal':
            cant_cafe = st.slider("Módulos Café", 2, 10, 4)
        else:
            col_c1, col_c2 = st.columns(2)
            mods_cafe_1 = col_c1.number_input("Café L1", 1, 10, 2)
            mods_cafe_2 = col_c2.number_input("Café L2", 1, 10, 2)

    with st.expander("🛡️ Zonas Perimetrales y Pasillos", expanded=False):
        t_pasillos = st.checkbox("Habilitar Blindaje de Pasillos", value=False)
        pas_poder = st.slider("Ancho Pasillo Poder", 0.9, 2.5, 1.8)
        pas_peri = st.slider("Ancho Pasillos Perimetrales", 0.9, 1.5, 1.2)
        pas_gon = st.slider("Ancho Pasillos Góndolas", 0.9, 1.5, 1.2)
        st.markdown("---")
        t_perimetral = st.checkbox("Habilitar Perimetrales Auto", value=False)
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

    with st.expander("🏝️ Islas Individuales", expanded=False):
        t_islas = st.checkbox("Habilitar Islas", value=False)
        cant_islas = st.slider("Cantidad de Islas", 1, 10, 3)
        for i in range(cant_islas):
            c1, c2 = st.columns(2)
            conf[f'isla_x_{i}'] = c1.number_input(f"Isla {i+1} X", 0.0, 100.0, 2.0 + (i*1.0), 0.1)
            conf[f'isla_y_{i}'] = c2.number_input(f"Isla {i+1} Y", 0.0, 100.0, 2.0, 0.1)

conf.update({
    'nombre_tienda': nombre_tienda, 'ancho': ancho, 'largo': largo, 
    't_puerta': t_puerta, 'tipo_puerta': tipo_puerta, 'muro_puerta': muro_puerta, 'pos_puerta_x': pos_puerta_x, 'pos_puerta_y': pos_puerta_y,
    't_bodega': t_bodega, 'x_bodega': x_bodega if 'x_bodega' in locals() else 0, 'y_bodega': y_bodega if 'y_bodega' in locals() else 0, 'w_bodega': w_bodega if 'w_bodega' in locals() else 0, 'h_bodega': h_bodega if 'h_bodega' in locals() else 0, 'muro_puerta_bod': muro_puerta_bod if 'muro_puerta_bod' in locals() else 'Sur', 'pos_puerta_bod': pos_puerta_bod if 'pos_puerta_bod' in locals() else 0,
    't_check': t_check, 'rot_check': rot_check, 'cant_check': cant_check, 'pos_chk_x': pos_chk_x, 'pos_chk_y': pos_chk_y,
    't_frio': t_frio, 'forma_frio': forma_frio if 'forma_frio' in locals() else 'Lineal', 'rot_frio': rot_frio, 'cant_frio': cant_frio if 'cant_frio' in locals() else 0, 'ptas_frio_1': ptas_frio_1 if 'ptas_frio_1' in locals() else 0, 'ptas_frio_2': ptas_frio_2 if 'ptas_frio_2' in locals() else 0, 'pos_frio_x': pos_frio_x, 'pos_frio_y': pos_frio_y,
    't_gondolas': t_gondolas, 'rot_gon': rot_gon, 'cant_trenes': cant_trenes, 'cant_tramos': cant_tramos, 'pas_gon': pas_gon if 'pas_gon' in locals() else 1.2, 'pos_gon_x': pos_gon_x, 'pos_gon_y': pos_gon_y,
    't_cafe': t_cafe, 'forma_cafe': forma_cafe if 'forma_cafe' in locals() else 'Lineal', 'rot_cafe': rot_cafe, 'cant_cafe': cant_cafe if 'cant_cafe' in locals() else 0, 'mods_cafe_1': mods_cafe_1 if 'mods_cafe_1' in locals() else 0, 'mods_cafe_2': mods_cafe_2 if 'mods_cafe_2' in locals() else 0, 'pos_cafe_x': pos_cafe_x, 'pos_cafe_y': pos_cafe_y,
    't_perimetral': t_perimetral if 't_perimetral' in locals() else False, 'peri_izq': peri_izq if 'peri_izq' in locals() else False, 'tramos_izq': tramos_izq if 'tramos_izq' in locals() else 0, 'pos_izq_y': pos_izq_y if 'pos_izq_y' in locals() else 0, 'peri_der': peri_der if 'peri_der' in locals() else False, 'tramos_der': tramos_der if 'tramos_der' in locals() else 0, 'pos_der_y': pos_der_y if 'pos_der_y' in locals() else 0, 'peri_frente': peri_frente if 'peri_frente' in locals() else False, 'tramos_frente': tramos_frente if 'tramos_frente' in locals() else 0, 'pos_fre_x': pos_fre_x if 'pos_fre_x' in locals() else 0, 'peri_fondo': peri_fondo if 'peri_fondo' in locals() else False, 'tramos_fondo': tramos_fondo if 'tramos_fondo' in locals() else 0, 'pos_fon_x': pos_fon_x if 'pos_fon_x' in locals() else 0, 'pas_peri': pas_peri if 'pas_peri' in locals() else 1.2,
    't_islas': t_islas, 'cant_islas': cant_islas,
    't_pasillos': t_pasillos if 't_pasillos' in locals() else False, 'pas_poder': pas_poder if 'pas_poder' in locals() else 1.8
})

st.markdown(f"## 🏬 {nombre_tienda}")
area_tot = ancho * largo
fig, errores, log_imgs, pct_exh, pct_nav, a_tot, a_com, a_op_real = dibujar_layout_oxxo_v30(conf)

kpi1, kpi2, kpi3, kpi4 = st.columns(4)
kpi1.metric("Área Total", f"{area_tot:.1f} m²", clasificar_formato(area_tot))
pct_op = (a_op_real / a_tot) * 100 if a_tot > 0 else 0
kpi2.metric("Área Operativa (Bodega)", f"{pct_op:.1f}%", "✅ Meta" if 18 <= pct_op <= 22 else ("🔻 Baja" if pct_op < 18 else "🔺 Excede"))
kpi3.metric("Área Exhibición (Comercial)", f"{pct_exh:.1f}%", "✅ Optima" if 30 <= pct_exh <= 40 else "⚠️ Revisar")
kpi4.metric("Área Navegación (Comercial)", f"{pct_nav:.1f}%", "✅ Optima" if 60 <= pct_nav <= 70 else "⚠️ Revisar")

st.markdown("---")
st.pyplot(fig, use_container_width=True)

col_pdf, col_svg = st.columns(2)
buf_pdf = io.BytesIO()
fig.savefig(buf_pdf, format="pdf", bbox_inches='tight')
col_pdf.download_button("📥 Exportar PDF Plano Técnico", data=buf_pdf.getvalue(), file_name=f"{nombre_tienda}.pdf", mime="application/pdf", use_container_width=True)

buf_svg = io.BytesIO()
fig.savefig(buf_svg, format="svg", bbox_inches='tight')
col_svg.download_button("📐 Exportar Vectorial (SVG)", data=buf_svg.getvalue(), file_name=f"{nombre_tienda}.svg", mime="image/svg+xml", use_container_width=True)

if conf.get('modo_render') and log_imgs:
    with st.expander("🔍 Consola de Motor de Archivos 3D", expanded=True):
        for msg in set(log_imgs):
            if "✅" in msg: st.success(msg)
            elif "⚠️" in msg: st.warning(msg)
            else: st.error(msg)

if errores:
    st.error("🚨 **Colisiones Detectadas:**")
    for err in errores: st.warning(f"• {err}")