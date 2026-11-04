import streamlit as st
import pandas as pd
import re
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from io import BytesIO

# Configuración de página
st.set_page_config(page_title="Columna Estratigráfica Pro", layout="wide")

# Diccionario de litologías con colores y tramas (hatch) para Matplotlib
LITOLOGIAS = {
    "ignimbrita": {"color": "#D8BFD8", "hatch": "x", "label": "Ignimbrita"},
    "escoria": {"color": "#2F4F4F", "hatch": "O", "label": "Escoria"},
    "pómez": {"color": "#F5F5DC", "hatch": "o", "label": "Pómez"},
    "brecha": {"color": "#8FBC8F", "hatch": "^", "label": "Brecha"},
    "paleosuelo": {"color": "#5C4033", "hatch": "", "label": "Paleosuelo"},
    "lava": {"color": "#696969", "hatch": "+", "label": "Lava"},
    "arcilla": {"color": "#BDB76B", "hatch": "-", "label": "Arcilla"},
    "lapilli": {"color": "#D2B48C", "hatch": ".", "label": "Lapilli"},
    "ceniza": {"color": "#A9A9A9", "hatch": "//", "label": "Ceniza"},
    "suelo": {"color": "#8B5A2B", "hatch": "", "label": "Suelo"}
}

def parsear_libreta(texto):
    datos = []
    lineas = texto.split('\n')
    
    for linea in lineas:
        linea = linea.strip()
        if not linea:
            continue
        
        match = re.search(r'(\d+(?:\.\d+)?)\s*cms?', linea.lower())
        if not match:
            continue
        grosor = float(match.group(1))
        
        desc_principal = re.split(r'\b(con|esporádic[oa]s?|algun[oa]s?|pequeños?)\b', linea.lower())[0]
        
        litologia = "Estrato"
        for clave, props in LITOLOGIAS.items():
            if clave in desc_principal:
                litologia = props["label"]
                break
                
        granulometria = "media"
        if "fina" in linea.lower() or "arcilla" in linea.lower():
            granulometria = "fina"
        elif "gruesa" in linea.lower() or "lapilli" in linea.lower():
            granulometria = "gruesa"
        
        oxidacion = "Sí" if "oxidación" in linea.lower() or "ox" in linea.lower() else "No"
        
        simbolos = []
        if "fiamme" in linea.lower():
            simbolos.append("Fiamme")
        if "bomba" in linea.lower():
            simbolos.append("Bomba")
        if "lodo" in linea.lower():
            simbolos.append("Lodo")
        
        datos.append({
            "Grosor (cm)": grosor,
            "Litología": litologia,
            "Granulometría": granulometria,
            "Oxidación": oxidacion,
            "Símbolos": ", ".join(simbolos),
            "Descripción Original": linea
        })
        
    return pd.DataFrame(datos)

def dibujar_columna(df, cota_inicial, zoom):
    profundidad_total = df['Grosor (cm)'].sum()
    if profundidad_total == 0:
        return None
    
    alto_figura = max(6, (profundidad_total / 20) * zoom)
    fig, ax = plt.subplots(figsize=(6 * zoom, alto_figura))
    
    ax.invert_yaxis()
    y_actual = 0
    
    for idx, row in df.iterrows():
        grosor = row['Grosor (cm)']
        lit = row['Litología'].lower()
        gran = row['Granulometría']
        ox = row['Oxidación']
        
        w = 0.75
        if gran == 'fina':
            w = 0.5
        elif gran == 'gruesa':
            w = 1.0
        
        props = LITOLOGIAS.get(lit, {"color": "#FFFFFF", "hatch": ""})
        
        rect = patches.Rectangle((0, y_actual), w, grosor, 
                                 facecolor=props["color"], 
                                 hatch=props["hatch"], 
                                 edgecolor='black', 
                                 linewidth=1.5)
        ax.add_patch(rect)
        
        if ox == 'Sí':
            ax.plot([0, w], [y_actual + grosor, y_actual + grosor], color='red', linewidth=3.5)
            
        texto_label = f"{row['Litología']}\n({grosor} cm)"
        if row['Símbolos']:
            texto_label += f"\n[{row['Símbolos']}]"
            
        ax.text(w + 0.1, y_actual + (grosor / 2), texto_label, 
                va='center', fontsize=9 * zoom, color='#333333', weight='bold')
        
        y_actual += grosor
        
    ax.set_xlim(0, 3)
    ax.set_ylim(profundidad_total, 0)
    ax.set_ylabel("Profundidad Acumulada (cm)", fontsize=11 * zoom, weight='bold')
    ax.tick_params(axis='y', labelsize=9 * zoom)
    
    ax.xaxis.set_visible(False)
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.spines['bottom'].set_visible(False)
    
    if cota_inicial is not None:
        ax2 = ax.twinx()
        cota_fin = cota_inicial - (profundidad_total / 100)
        ax2.set_ylim(cota_fin, cota_inicial)
        ax2.set_ylabel("Cota (msnm)", color='#1E90FF', fontsize=11 * zoom, weight='bold')
        ax2.tick_params(axis='y', labelcolor='#1E90FF', labelsize=9 * zoom)
        ax2.spines['right'].set_color('#1E90FF')
        
    fig.tight_layout()
    return fig

# --- INTERFAZ STREAMLIT ---

st.title("🪨 Generador de Columnas Estratigráficas Pro")

col1, col2 = st.columns([1, 1])

with col1:
    st.subheader("1. Detalles y Cotas")
    nombre_columna = st.text_input("Nombre de la Columna / Locación", "ML 81 - Carretera Río Negro")
    cota_input = st.number_input("Cota Inicial (msnm) - Opcional", value=None, placeholder="Ej: 3850")
    
    st.subheader("2. Libreta de Campo")
    notas = st.text_area(
        "Pega aquí tus descripciones (arrastra la esquina inferior derecha para ampliar):",
        height=500,
        value="""80 cms de suelo actual.
34 cms de lapilli alterado ocre con cristales.
20 cms transicional ceniza media café clara.
16 cms de escoria negra porfiritica con bombas.
20 cms ceniza media café claro. A la base nivel de oxidación.
14 cms ignimbrita con fiammes.
98 cms de brecha. Suelo."""
    )
    
    if st.button("Extraer y Validar Datos", type="primary"):
        df_extraido = parsear_libreta(notas)
        st.session_state['df'] = df_extraido

    if 'df' in st.session_state and not st.session_state['df'].empty:
        st.subheader("3. Tabla de Validación")
        st.info("Edita cualquier celda directamente si el parser necesita corrección antes de dibujar.")
        df_editado = st.data_editor(st.session_state['df'], num_rows="dynamic", use_container_width=True)
        st.session_state['df_editado'] = df_editado

with col2:
    if 'df_editado' in st.session_state and not st.session_state['df_editado'].empty:
        st.subheader("Visualización y Exportación")
        
        zoom = st.slider("Zoom Gráfico", min_value=0.5, max_value=3.0, value=1.2, step=0.1)
        
        fig = dibujar_columna(st.session_state['df_editado'], cota_input, zoom)
        
        if fig:
            st.pyplot(fig)
            
            buf = BytesIO()
            fig.savefig(buf, format="png", dpi=300, bbox_inches='tight')
            buf.seek(0)
            
            csv = st.session_state['df_editado'].to_csv(index=False).encode('utf-8')
            
            c_btn1, c_btn2 = st.columns(2)
            with c_btn1:
                st.download_button(
                    label="🖼️ Descargar PNG (Alta Res)", 
                    data=buf, 
                    file_name=f"{nombre_columna.replace(' ', '_')}.png", 
                    mime="image/png",
                    use_container_width=True
                )
            with c_btn2:
                st.download_button(
                    label="📊 Exportar CSV", 
                    data=csv, 
                    file_name=f"{nombre_columna.replace(' ', '_')}_datos.csv", 
                    mime="text/csv",
                    use_container_width=True
                )
