import streamlit as st
import pandas as pd
from io import BytesIO
import requests
import warnings
warnings.filterwarnings('ignore')

st.set_page_config(page_title="Validador", page_icon="🔍", layout="wide")

st.markdown("""
<h1 style="text-align: center; color: #667eea;">
    🔍 Validador de Materiales
</h1>
<p style="text-align: center; color: #666;">
    Valida contra BBDD Estática + BBDD Proyecto (fusionadas)
</p>
""", unsafe_allow_html=True)

st.divider()

# ============= CARGAR SOLIDWORKS =============
st.markdown("## 📊 1. SolidWorks")
sw_file = st.file_uploader("Carga SolidWorks (2601.xls)", type=["xlsx", "xls", "csv"], key="sw")
sw_data = None

if sw_file:
    try:
        sw_data = pd.read_excel(sw_file) if not sw_file.name.endswith('.csv') else pd.read_csv(sw_file)
        st.success(f"✅ {len(sw_data)} filas cargadas")
    except Exception as e:
        st.error(f"Error: {e}")

# ============= DESCARGAR BBDD ESTÁTICA =============
st.divider()
st.markdown("## 🗄️ 2. BBDD Estática (desde GitHub)")

bbdd_estatica = None
try:
    GITHUB_USER = "sebasmpaura"
    REPO_NAME = "validador-materiales"
    
    url = f"https://raw.githubusercontent.com/{GITHUB_USER}/{REPO_NAME}/main/ProyectosXConjArt.xlsx"
    
    response = requests.get(url)
    if response.status_code == 200:
        bbdd_estatica = pd.read_excel(BytesIO(response.content))
        st.success(f"✅ BBDD Estática descargada ({len(bbdd_estatica)} filas)")
    else:
        st.warning(f"⚠️ No se pudo descargar BBDD Estática (código {response.status_code})")
        
except Exception as e:
    st.warning(f"⚠️ Error descargando BBDD Estática: {e}")

# ============= CARGAR BBDD PROYECTO =============
st.divider()
st.markdown("## 📁 3. BBDD Proyecto (cargada actualmente)")
bbdd_proyecto = st.file_uploader("Carga BBDD del Proyecto actual", type=["xlsx", "xls", "csv"], key="bbdd_proyecto")
bbdd_proyecto_data = None

if bbdd_proyecto:
    try:
        bbdd_proyecto_data = pd.read_excel(bbdd_proyecto) if not bbdd_proyecto.name.endswith('.csv') else pd.read_csv(bbdd_proyecto)
        st.success(f"✅ BBDD Proyecto cargada ({len(bbdd_proyecto_data)} filas)")
    except Exception as e:
        st.error(f"Error: {e}")

# ============= VALIDAR =============
if sw_data is not None and (bbdd_estatica is not None or bbdd_proyecto_data is not None):
    st.divider()
    st.markdown("## 🚀 Validación")
    
    sw_cols = list(sw_data.columns)
    
    if len(sw_cols) < 2:
        st.error("❌ SolidWorks necesita al menos 2 columnas")
    else:
        col_numero_sw = sw_cols[1]
        
        # Contar bases de datos disponibles
        bbdd_count = 0
        bbdd_info = ""
        if bbdd_estatica is not None:
            bbdd_count += 1
            bbdd_info += f"✓ BBDD Estática ({len(bbdd_estatica)} filas)\n"
        if bbdd_proyecto_data is not None:
            bbdd_count += 1
            bbdd_info += f"✓ BBDD Proyecto ({len(bbdd_proyecto_data)} filas)"
        
        st.info(f"""
        📊 **SolidWorks:** {len(sw_data)} filas, referencias de columna 2 → **{col_numero_sw}**
        
        🗄️  **BBDD Fusionada:**
        {bbdd_info}
        
        📍 Se buscarán en AMBAS y se mostrarán como: ELEMENTO / ARTÍCULO / AMBOS
        """)
        
        st.divider()
        
        if st.button("🔍 VALIDAR", use_container_width=True, type="primary"):
            with st.spinner("Validando contra BBDD fusionada..."):
                
                # PASO 1: Extraer referencias de SolidWorks
                referencias_sw = {}
                for idx, row in sw_data.iterrows():
                    try:
                        ref = row[col_numero_sw]
                        if pd.notna(ref):
                            try:
                                ref_num = int(float(str(ref).strip()))
                                if ref_num not in referencias_sw:
                                    referencias_sw[ref_num] = True
                            except:
                                pass
                    except:
                        pass
                
                st.info(f"✅ Leídas {len(referencias_sw)} referencias de SolidWorks")
                
                # PASO 2: Clasificar referencias en BBDD (AMBAS fusionadas)
                referencias_clasificadas = {}
                
                for ref_sw in referencias_sw.keys():
                    referencias_clasificadas[ref_sw] = {
                        'es_elemento': False,
                        'es_articulo': False
                    }
                
                # Buscar en Elementos.ref_empresa (AMBAS BBDD)
                for bbdd in [bbdd_estatica, bbdd_proyecto_data]:
                    if bbdd is not None and 'Elementos.ref_empresa' in bbdd.columns:
                        for val in bbdd['Elementos.ref_empresa']:
                            try:
                                if pd.notna(val):
                                    ref_num = int(float(str(val).strip()))
                                    if ref_num in referencias_clasificadas:
                                        referencias_clasificadas[ref_num]['es_elemento'] = True
                            except:
                                pass
                
                # Buscar en Proyectos.ref_empresa (AMBAS BBDD)
                for bbdd in [bbdd_estatica, bbdd_proyecto_data]:
                    if bbdd is not None and 'Proyectos.ref_empresa' in bbdd.columns:
                        for val in bbdd['Proyectos.ref_empresa']:
                            try:
                                if pd.notna(val):
                                    ref_num = int(float(str(val).strip()))
                                    if ref_num in referencias_clasificadas:
                                        referencias_clasificadas[ref_num]['es_articulo'] = True
                            except:
                                pass
                
                st.info(f"✅ Clasificación completada contra BBDD fusionada")
                
                # PASO 3: Crear resultado
                resultado = []
                hay_count = 0
                elemento_count = 0
                articulo_count = 0
                ambos_count = 0
                no_hay_count = 0
                
                for ref_sw in sorted(referencias_clasificadas.keys()):
                    data = referencias_clasificadas[ref_sw]
                    
                    if data['es_elemento'] and data['es_articulo']:
                        estado = "✓ HAY"
                        tipo = "AMBOS"
                        ambos_count += 1
                        hay_count += 1
                    elif data['es_elemento']:
                        estado = "✓ HAY"
                        tipo = "ELEMENTO"
                        elemento_count += 1
                        hay_count += 1
                    elif data['es_articulo']:
                        estado = "✓ HAY"
                        tipo = "ARTÍCULO"
                        articulo_count += 1
                        hay_count += 1
                    else:
                        estado = "✗ NO HAY"
                        tipo = "NO EXISTE"
                        no_hay_count += 1
                    
                    resultado.append({
                        'Referencia': ref_sw,
                        'Estado': estado,
                        'Tipo': tipo
                    })
                
                st.session_state.resultado = resultado
                st.session_state.hay_count = hay_count
                st.session_state.no_hay_count = no_hay_count
                st.session_state.elemento_count = elemento_count
                st.session_state.articulo_count = articulo_count
                st.session_state.ambos_count = ambos_count
                st.session_state.validado = True
        
        # ============= MOSTRAR RESULTADOS =============
        if 'validado' in st.session_state:
            st.divider()
            st.markdown("## 📊 RESULTADOS")
            
            col1, col2, col3, col4, col5 = st.columns(5)
            col1.metric("📊 Total", len(st.session_state.resultado))
            col2.metric("✓ HAY", st.session_state.hay_count)
            col3.metric("📦 Elementos", st.session_state.elemento_count)
            col4.metric("🏷️ Artículos", st.session_state.articulo_count)
            col5.metric("🔗 Ambos", st.session_state.ambos_count)
            
            st.divider()
            st.metric("✗ NO HAY", st.session_state.no_hay_count)
            
            st.divider()
            
            df = pd.DataFrame(st.session_state.resultado)
            
            tab1, tab2, tab3, tab4, tab5 = st.tabs(
                ["📋 TODAS", "✓ HAY", "📦 ELEMENTOS", "🏷️ ARTÍCULOS", "✗ NO HAY"]
            )
            
            with tab1:
                st.markdown("### Validación Completa")
                
                for idx, row in df.iterrows():
                    if row['Estado'] == "✓ HAY":
                        if row['Tipo'] == "ELEMENTO":
                            st.success(f"✓ **{row['Referencia']}** → 📦 ELEMENTO")
                        elif row['Tipo'] == "ARTÍCULO":
                            st.success(f"✓ **{row['Referencia']}** → 🏷️ ARTÍCULO")
                        else:
                            st.success(f"✓ **{row['Referencia']}** → 🔗 AMBOS")
                    else:
                        st.error(f"✗ **{row['Referencia']}** → NO HAY en BBDD")
                
                st.divider()
                
                col1, col2 = st.columns(2)
                with col1:
                    output = BytesIO()
                    with pd.ExcelWriter(output, engine='openpyxl') as writer:
                        df.to_excel(writer, sheet_name='Validacion', index=False)
                    st.download_button(
                        "📥 Descargar Excel",
                        output.getvalue(),
                        "Validacion_Completa.xlsx",
                        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                        use_container_width=True
                    )
                with col2:
                    st.download_button(
                        "📥 Descargar CSV",
                        df.to_csv(index=False),
                        "Validacion_Completa.csv",
                        "text/csv",
                        use_container_width=True
                    )
            
            with tab2:
                df_hay = df[df['Estado'] == "✓ HAY"]
                if len(df_hay) > 0:
                    st.markdown(f"### ✓ {len(df_hay)} Referencias encontradas en BBDD")
                    for idx, row in df_hay.iterrows():
                        if row['Tipo'] == "ELEMENTO":
                            st.success(f"✓ **{row['Referencia']}** → 📦 ELEMENTO")
                        elif row['Tipo'] == "ARTÍCULO":
                            st.success(f"✓ **{row['Referencia']}** → 🏷️ ARTÍCULO")
                        else:
                            st.success(f"✓ **{row['Referencia']}** → 🔗 AMBOS")
                else:
                    st.info("No hay referencias encontradas")
            
            with tab3:
                df_elementos = df[df['Tipo'] == "ELEMENTO"]
                if len(df_elementos) > 0:
                    st.markdown(f"### 📦 {len(df_elementos)} Elementos en BBDD")
                    for idx, row in df_elementos.iterrows():
                        st.success(f"📦 **{row['Referencia']}**")
                else:
                    st.info("No hay elementos")
            
            with tab4:
                df_articulos = df[df['Tipo'] == "ARTÍCULO"]
                if len(df_articulos) > 0:
                    st.markdown(f"### 🏷️ {len(df_articulos)} Artículos en BBDD")
                    for idx, row in df_articulos.iterrows():
                        st.success(f"🏷️ **{row['Referencia']}**")
                else:
                    st.info("No hay artículos")
            
            with tab5:
                df_no_hay = df[df['Estado'] == "✗ NO HAY"]
                if len(df_no_hay) > 0:
                    st.markdown(f"### ✗ {len(df_no_hay)} Referencias NO en BBDD")
                    st.error("**FALTA CARGAR EN BBDD:**")
                    
                    for idx, row in df_no_hay.iterrows():
                        st.error(f"✗ **{row['Referencia']}**")
                    
                    csv_faltantes = df_no_hay[['Referencia']].to_csv(index=False)
                    st.download_button(
                        "📥 Descargar Faltantes (CSV)",
                        csv_faltantes,
                        "Referencias_Faltantes.csv",
                        "text/csv",
                        use_container_width=True
                    )
                else:
                    st.success("✅ ¡Todas las referencias están en la BBDD!")

else:
    st.warning("⏳ Carga SolidWorks y al menos una BBDD (Estática o Proyecto)")

st.divider()
st.markdown("<p style='text-align: center; color: #999;'>🔍 Validador FINAL | BBDD Estática + Proyecto Fusionadas</p>", unsafe_allow_html=True)
