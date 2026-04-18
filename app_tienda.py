import streamlit as st
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from matplotlib.ticker import MultipleLocator
import matplotlib.image as mpimg
import os
import io

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

# --- CLASIFICADOR DE MATRIZ DE FORMATOS OXXO ---
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
    r = r % 360
    if 90 < r < 270: r -= 180
    return r

def dibujar_layout_oxxo_v25(conf):
    W, L = conf['ancho'], conf['largo']

    fig, ax = plt.subplots(figsize=(12, 12))
    ax.set_xlim(0, W)
    ax.set_ylim(0, L)
    
    # Cuadrícula
    ax.xaxis.set_major_locator(MultipleLocator(1))
    ax.yaxis.set_major_locator(MultipleLocator(1))
    ax.grid(which='major', color='#E5E7E9', linestyle='-', linewidth=0.5, zorder=0)

    obs_fisicos = []  
    obs_pasillos = [] 
    errores = []
    area_exh = 0
    
    # MOTOR HÍBRIDO (Imágenes + Z-Sorting)
    def registrar_obj(x, y, w, h, color, texto="", rot_text=0, alpha=1.0, font=6, tipo="Fisico", name="Objeto", txt_col='black', weight='normal', img_base=None):
        choca = False
        obj_chocado = ""
        ec = 'black'
        lw = 1

        # Z-Sorting automático: Mientras menor sea 'y' (más abajo), mayor es el zorder (se dibuja encima)
        z_calc = 1000 - int(y * 10) if tipo == "Fisico" else 2

        if x < -0.05 or y < -0.05 or x + w > W + 0.05 or y + h > L + 0.05:
            errores.append(f"Mobiliario fuera de layout: {name}")
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
                errores.append(f"{name} colisiona o bloquea a {obj_chocado}.")
                ec, lw = 'red', 2
                z_calc = 2000 # Traer al frente si hay error para que se note
            elif not choca:
                if tipo == "Fisico": obs_fisicos.append((x, y, w, h, name))
                elif tipo == "Pasillo": obs_pasillos.append((x, y, w, h, name))

        # Intentar cargar imagen si el modo render está activo
        dibujado_imagen = False
        if conf.get('modo_render', False) and img_base and tipo == "Fisico" and not choca:
            rot_norm = int(rot_text % 360)
            ruta_img = f"assets/{img_base}_{rot_norm}.png"
            if os.path.exists(ruta_img):
                try:
                    img = mpimg.imread(ruta_img)
                    # extent = [left, right, bottom, top]
                    ax.imshow(img, extent=[x, x+w, y, y+h], zorder=z_calc)
                    dibujado_imagen = True
                except Exception as e:
                    pass

        # Si no hay imagen o hubo error, pintar el cuadro clásico
        if not dibujado_imagen:
            ax.add_patch(patches.Rectangle((x, y), w, h, color=color, ec=ec, lw=lw, alpha=alpha, zorder=z_calc))
            if texto:
                ax.text(x + w/2, y + h/2, texto, ha='center', va='center', rotation=normalizar_rotacion(rot_text), fontsize=font, color=txt_col, weight=weight, zorder=z_calc+1)
        
        return w, h

    # Lienzo Base
    ax.add_patch(patches.Rectangle((0, 0), W, L, fill=False, ec='black', lw=4, zorder=10000)) # Muro siempre arriba
    area_total = W * L

    # ==========================================
    # 1. BODEGA PARAMÉTRICA
    # ==========================================
    a_op = 0
    if conf['t_bodega']:
        w_b, h_b = conf['w_bodega'], conf['h_bodega']
        xb, yb = conf['x_bodega'], conf['y_bodega']
        a_op = w_b * h_b
        registrar_obj(xb, yb, w_b, h_b, '#D2B48C', f"BODEGA ({a_op:.1f} m²)", font=8, weight='bold', name="Bodega")
        pb = conf['pas_bod']
        registrar_obj(xb + 0.5, yb + 0.5, w_b - 1.0, h_b - 1.0, '#E59866', f"Pasillo {pb}m\nRacks 50cm", alpha=0.3, tipo="Pasillo", txt_col='white', name="Interior Bodega")
        
        pos_pb = conf['pos_puerta_bod']
        muro_pb = conf['muro_puerta_bod']
        if muro_pb == 'Sur': registrar_obj(xb + pos_pb, yb, 0.9, 0.2, 'brown', name="Pta Bodega")
        elif muro_pb == 'Norte': registrar_obj(xb + pos_pb, yb + h_b - 0.2, 0.9, 0.2, 'brown', name="Pta Bodega")
        elif muro_pb == 'Oeste': registrar_obj(xb, yb + pos_pb, 0.2, 0.9, 'brown', name="Pta Bodega")
        elif muro_pb == 'Este': registrar_obj(xb + w_b - 0.2, yb + pos_pb, 0.2, 0.9, 'brown', name="Pta Bodega")

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
        ax.add_patch(patches.Circle((xp + w_puerta/2, yp + h_puerta/2), 2.0, color='#85C1E9', alpha=0.2, zorder=1))

        if conf['t_pasillos']:
            wpod = conf['pas_poder']
            if conf['muro_puerta'] == 'Sur': registrar_obj(xp - (wpod-pw)/2, yp, wpod, L - yp, '#EBF5FB', "PASILLO DE PODER", rot_text=90, alpha=0.6, tipo="Pasillo", txt_col='#154360', weight='bold', name="Pasillo de Poder")
            elif conf['muro_puerta'] == 'Norte': registrar_obj(xp - (wpod-pw)/2, 0, wpod, yp, '#EBF5FB', "PASILLO DE PODER", rot_text=90, alpha=0.6, tipo="Pasillo", txt_col='#154360', weight='bold', name="Pasillo de Poder")
            elif conf['muro_puerta'] == 'Este': registrar_obj(0, yp - (wpod-pw)/2, xp, wpod, '#EBF5FB', "PASILLO DE PODER", alpha=0.6, tipo="Pasillo", txt_col='#154360', weight='bold', name="Pasillo de Poder")
            elif conf['muro_puerta'] == 'Oeste': registrar_obj(xp, yp - (wpod-pw)/2, W - xp, wpod, '#EBF5FB', "PASILLO DE PODER", alpha=0.6, tipo="Pasillo", txt_col='#154360', weight='bold', name="Pasillo de Poder")

    # ==========================================
    # 3. CHECKOUT
    # ==========================================
    if conf['t_check']:
        mods_chk = conf['cant_check']
        xc, yc = conf['pos_chk_x'], conf['pos_chk_y']
        rot_c = conf['rot_check']
        w_chk = mods_chk * MOD_2FT
        
        if rot_c == 0: 
            registrar_obj(xc, yc, w_chk, PROF_CONTRA, '#82E0AA', "C.CAJA", name="Contracaja", img_base="contracaja")
            registrar_obj(xc, yc + PROF_CONTRA, w_chk, PROF_CAJERO, '#EAEDED', "P. CAJERO", tipo="Pasillo", name="Pasillo Cajero")
            for i in range(mods_chk): registrar_obj(xc + (i*MOD_2FT), yc + PROF_CONTRA + PROF_CAJERO, MOD_2FT, PROF_CHECK, '#ABEBC6', f"CHK{i+1}", font=5, name=f"CHK{i+1}", img_base="checkout")
            if conf['t_pasillos']: registrar_obj(xc, yc + PROF_CONTRA + PROF_CAJERO + PROF_CHECK, w_chk, PASILLO_STD, '#D5F5E3', "PASILLO COBRO", alpha=0.5, tipo="Pasillo", name="Pasillo Cobro")
            area_exh += (w_chk * PROF_CHECK)
        elif rot_c == 90: 
            registrar_obj(xc + PROF_CHECK + PROF_CAJERO, yc, PROF_CONTRA, w_chk, '#82E0AA', "C.CAJA", rot_text=90, name="Contracaja", img_base="contracaja")
            registrar_obj(xc + PROF_CHECK, yc, PROF_CAJERO, w_chk, '#EAEDED', "P. CAJERO", rot_text=90, tipo="Pasillo", name="Pasillo Cajero")
            for i in range(mods_chk): registrar_obj(xc, yc + (i*MOD_2FT), PROF_CHECK, MOD_2FT, '#ABEBC6', f"CHK{i+1}", font=5, rot_text=90, name=f"CHK{i+1}", img_base="checkout")
            if conf['t_pasillos']: registrar_obj(xc - PASILLO_STD, yc, PASILLO_STD, w_chk, '#D5F5E3', "PASILLO COBRO", rot_text=90, alpha=0.5, tipo="Pasillo", name="Pasillo Cobro")
            area_exh += (w_chk * PROF_CHECK)
        elif rot_c == 180: 
            if conf['t_pasillos']: registrar_obj(xc, yc - PASILLO_STD, w_chk, PASILLO_STD, '#D5F5E3', "PASILLO COBRO", alpha=0.5, tipo="Pasillo", name="Pasillo Cobro")
            for i in range(mods_chk): registrar_obj(xc + (i*MOD_2FT), yc, MOD_2FT, PROF_CHECK, '#ABEBC6', f"CHK{i+1}", font=5, name=f"CHK{i+1}", img_base="checkout")
            registrar_obj(xc, yc + PROF_CHECK, w_chk, PROF_CAJERO, '#EAEDED', "P. CAJERO", tipo="Pasillo", name="Pasillo Cajero")
            registrar_obj(xc, yc + PROF_CHECK + PROF_CAJERO, w_chk, PROF_CONTRA, '#82E0AA', "C.CAJA", name="Contracaja", img_base="contracaja")
            area_exh += (w_chk * PROF_CHECK)
        elif rot_c == 270: 
            registrar_obj(xc, yc, PROF_CONTRA, w_chk, '#82E0AA', "C.CAJA", rot_text=90, name="Contracaja", img_base="contracaja")
            registrar_obj(xc + PROF_CONTRA, yc, PROF_CAJERO, w_chk, '#EAEDED', "P. CAJERO", rot_text=90, tipo="Pasillo", name="Pasillo Cajero")
            for i in range(mods_chk): registrar_obj(xc + PROF_CONTRA + PROF_CAJERO, yc + (i*MOD_2FT), PROF_CHECK, MOD_2FT, '#ABEBC6', f"CHK{i+1}", font=5, rot_text=90, name=f"CHK{i+1}", img_base="checkout")
            if conf['t_pasillos']: registrar_obj(xc + PROF_CONTRA + PROF_CAJERO + PROF_CHECK, yc, PASILLO_STD, w_chk, '#D5F5E3', "PASILLO COBRO", rot_text=90, alpha=0.5, tipo="Pasillo", name="Pasillo Cobro")
            area_exh += (w_chk * PROF_CHECK)

    # ==========================================
    # 4. CUARTO FRÍO
    # ==========================================
    if conf['t_frio']:
        xf, yf = conf['pos_frio_x'], conf['pos_frio_y']
        rot_f = conf['rot_frio']
        
        if conf['forma_frio'] == 'Lineal':
            ptas = conf['cant_frio']
            wf = ptas * MOD_2FT
            if rot_f == 0: 
                registrar_obj(xf, yf, wf, PROF_FRIO, '#AED6F1', "CUARTO FRÍO", weight='bold', name="Frio", img_base="frio")
                for i in range(ptas): registrar_obj(xf + i*MOD_2FT, yf, MOD_2FT, 0.15, '#2874A6', f"P{i+1}", font=4, txt_col='white', name=f"Pta {i+1}")
                if conf['t_pasillos']: registrar_obj(xf, yf - PASILLO_STD, wf, PASILLO_STD, '#FCF3CF', "PASILLO FRÍO", alpha=0.6, tipo="Pasillo", name="Pasillo Frio", txt_col='#9A7D0A')
            elif rot_f == 90:
                registrar_obj(xf, yf, PROF_FRIO, wf, '#AED6F1', "CUARTO FRÍO", rot_text=90, weight='bold', name="Frio", img_base="frio")
                for i in range(ptas): registrar_obj(xf + PROF_FRIO - 0.15, yf + i*MOD_2FT, 0.15, MOD_2FT, '#2874A6', f"P{i+1}", rot_text=90, font=4, txt_col='white', name=f"Pta {i+1}")
                if conf['t_pasillos']: registrar_obj(xf + PROF_FRIO, yf, PASILLO_STD, wf, '#FCF3CF', "PASILLO FRÍO", rot_text=90, alpha=0.6, tipo="Pasillo", name="Pasillo Frio", txt_col='#9A7D0A')
            elif rot_f == 180:
                registrar_obj(xf, yf, wf, PROF_FRIO, '#AED6F1', "CUARTO FRÍO", weight='bold', name="Frio", img_base="frio")
                for i in range(ptas): registrar_obj(xf + i*MOD_2FT, yf + PROF_FRIO - 0.15, MOD_2FT, 0.15, '#2874A6', f"P{i+1}", font=4, txt_col='white', name=f"Pta {i+1}")
                if conf['t_pasillos']: registrar_obj(xf, yf + PROF_FRIO, wf, PASILLO_STD, '#FCF3CF', "PASILLO FRÍO", alpha=0.6, tipo="Pasillo", name="Pasillo Frio", txt_col='#9A7D0A')
            elif rot_f == 270:
                registrar_obj(xf, yf, PROF_FRIO, wf, '#AED6F1', "CUARTO FRÍO", rot_text=90, weight='bold', name="Frio", img_base="frio")
                for i in range(ptas): registrar_obj(xf, yf + i*MOD_2FT, 0.15, MOD_2FT, '#2874A6', f"P{i+1}", rot_text=90, font=4, txt_col='white', name=f"Pta {i+1}")
                if conf['t_pasillos']: registrar_obj(xf - PASILLO_STD, yf, PASILLO_STD, wf, '#FCF3CF', "PASILLO FRÍO", rot_text=90, alpha=0.6, tipo="Pasillo", name="Pasillo Frio", txt_col='#9A7D0A')
            area_exh += (wf * PROF_FRIO)

    # ==========================================
    # 5. GÓNDOLAS CENTRALES (Con llamada a imagen 'gondola')
    # ==========================================
    if conf['t_gondolas']:
        xg, yg = conf['pos_gon_x'], conf['pos_gon_y']
        tramos = conf['cant_tramos']
        largo_g = tramos * MOD_3FT
        
        for i in range(conf['cant_trenes']):
            # Asignamos la rotación correspondiente a la imagen base
            rot_img = 0 if conf['rot_gon'] == 'Vertical' else 90
            
            # Dibujamos el tren completo como un solo bloque para facilitar la imagen
            # NOTA: Si pones la imagen, tapará los cuadritos individuales, lo cual es ideal.
            if conf['rot_gon'] == 'Vertical':
                registrar_obj(xg, yg, GONDOLA_PROF, largo_g + CABECERA_PROF*2, '#ABB2B9', "GÓNDOLA", rot_text=0, font=8, name=f"Tren {i+1}", img_base="gondola")
                if conf['t_pasillos']: registrar_obj(xg + GONDOLA_PROF, yg, conf['pas_gon'], largo_g + CABECERA_PROF*2, '#EBEDEF', "", rot_text=90, alpha=0.6, tipo="Pasillo", name=f"Pasillo Gon {i+1}")
                xg += GONDOLA_PROF + conf['pas_gon']
            else: 
                registrar_obj(xg, yg, largo_g + CABECERA_PROF*2, GONDOLA_PROF, '#ABB2B9', "GÓNDOLA", rot_text=90, font=8, name=f"Tren {i+1}", img_base="gondola")
                if conf['t_pasillos']: registrar_obj(xg, yg + GONDOLA_PROF, largo_g + CABECERA_PROF*2, conf['pas_gon'], '#EBEDEF', "", alpha=0.6, tipo="Pasillo", name=f"Pasillo Gon {i+1}")
                yg += GONDOLA_PROF + conf['pas_gon']
            area_exh += GONDOLA_PROF * (largo_g + CABECERA_PROF*2)

    # ==========================================
    # 6. ISLAS INDIVIDUALES
    # ==========================================
    if conf['t_islas']:
        for i in range(conf['cant_islas']):
            ix, iy = conf[f'isla_x_{i}'], conf[f'isla_y_{i}']
            registrar_obj(ix, iy, ISLA_DIM, ISLA_DIM, '#F4D03F', f"E{i+1}", font=6, name=f"Isla {i+1}", img_base="isla")
            area_exh += (ISLA_DIM * ISLA_DIM)

    pct_exh = (area_exh / area_comercial) * 100 if area_comercial > 0 else 0
    pct_nav = 100 - pct_exh
    
    ax.set_aspect('equal')
    plt.title(f"Store Planning: {conf['nombre_tienda']} | Formato: {clasificar_formato(area_total)}")
    return fig, errores, pct_exh, pct_nav, area_total, area_comercial, a_op

# --- INTERFAZ STREAMLIT ---
st.set_page_config(layout="wide", page_title="Store Planning OXXO")

conf = {}

with st.sidebar:
    st.title("🏬 Store Planning OXXO")
    
    st.markdown("### 🎨 Motor Gráfico")
    modo_render = st.toggle("Activar Modo Render (Imágenes PNG)", value=False)
    conf['modo_render'] = modo_render
    if modo_render:
        st.success("Buscando imágenes en la carpeta 'assets/'...")
        
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

col_info, col_plot = st.columns([1.5, 2.5])

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
        rot_gon = st.radio("Orientación", ['Vertical', 'Horizontal'])
        sep_cab = st.checkbox("Separar cabeceras para islas")
        cant_trenes = st.slider("Trenes", 1, 6, 2)
        cant_tramos = st.slider("Tramos por Tren", 1, 8, 3)
        pas_gon = st.slider("Pasillo entre góndolas", 0.9, 1.5, 1.2)
        pos_gon_x = st.number_input("Góndola Pos X", 0.0, 100.0, 4.0, 0.1)
        pos_gon_y = st.number_input("Góndola Pos Y", 0.0, 100.0, 4.0, 0.1)

    with st.expander("6. Islas Individuales", expanded=False):
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
    't_islas': t_islas, 'cant_islas': cant_islas,
    't_cafe': False, 't_perimetral': False # Ocultos por brevedad en la prueba
})

with col_plot:
    fig, errores, pct_exh, pct_nav, a_tot, a_com, a_op_real = dibujar_layout_oxxo_v25(conf)
    st.pyplot(fig)
    
    if errores:
        st.error("🚨 **Motor de Colisiones Activo:**")
        for err in errores: st.warning(f"• {err}")

# Update Dashboard KPIs
pct_op = (a_op_real / a_tot) * 100 if a_tot > 0 else 0
if 18 <= pct_op <= 22: kpi_bod.success(f"Bodega: {pct_op:.1f}% (Meta 20%)")
else: kpi_bod.error(f"Bodega: {pct_op:.1f}% (Meta 20%)")

kpi_exh.metric("Rentabilidad (30-40%)", f"{pct_exh:.1f}%", "Aceptado" if 30 <= pct_exh <= 40 else "Revisar")
kpi_nav.metric("Experiencia (60-70%)", f"{pct_nav:.1f}%", "Aceptado" if 60 <= pct_nav <= 70 else "Revisar")