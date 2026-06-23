import streamlit as st
import pandas as pd
import numpy as np
from io import BytesIO
import warnings
warnings.filterwarnings('ignore')

# Configuración de página
st.set_page_config(
    page_title="Validador de Materiales",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Estilos CSS personalizados
st.markdown("""
<style>
    .main {
        padding: 2rem;
    }
    .stTabs [data-baseweb="tab-list"] button [data-testid="stMarkdownContainer"] p {
        font-size: 1.1rem;
    }
    .metric-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 20px;
        border-radius: 10px;
        text-align: center;
    }
    .ok-badge {
        background-color: #d4edda;
        color: #155724;
        padding: 5px 10px;
        border-radius: 5px;
        font-weight: bold;
    }
    .warning-badge {
        background-color: #fff3cd;
        color: #856404;
        padding: 5px 10px;
        border-radius: 5px;
        font-weight: bold;
    }
    .error-badge {
        background-color: #f8d7da;
        color: #721c24;
        padding: 5px 10px;
        border-radius: 5px;
        font-weight: bold;
    }
    .info-badge {
        background-color: #d1ecf1;
        color: #0c5460;
        padding: 5px 10px;
        border-radius: 5px;
        font-weight: bold;
    }
</style>
""", unsafe_allow_html=True)

# Título
st.markdown("""
<h1 style="text-align: center; color: #667eea;">
    🔍 Validador de Listas de Materiales
</h1>
<p style="text-align: center; color: #666;">
    Compara SolidWorks vs BBDD y genera consolidado unificado
</p>
""", unsafe_allow_html=True)

st.divider()

# Sidebar
with st.sidebar:
    st.markdown("### 📋 Instrucciones")
    st.markdown("""
    **Paso 1:** Carga tu archivo de SolidWorks
    
    **Paso 2:** Carga tu archivo de BBDD
    
    **Paso 3:** Selecciona las columnas correctas
    
    **Paso 4:** Haz clic en "VALIDAR"
    
    **Paso 5:** Descarga el consolidado
    """)
    
    st.divider()
    st.markdown("### ⚙️ Configuración")
    
    # Opciones de búsqueda
    search_method = st.radio(
        "Criterio de búsqueda:",
        options=["Por Número de Parte", "Por Descripción", "Ambos"],
        help="Cómo comparar elementos entre archivos"
    )

# ============= SECCIÓN 1: CARGAR ARCHIVOS =============
st.markdown("## 📁 Paso 1: Cargar Archivos")

col1, col2 = st.columns(2)

with col1:
    st.markdown("### 📊 SolidWorks")
    sw_file = st.file_uploader(
        "Carga tu archivo de SolidWorks",
        type=["xlsx", "xls", "csv"],
        key="sw_file",
        help="Archivo exportado desde SolidWorks"
    )
    sw_data = None
    sw_columns = None
    
    if sw_file:
        try:
            if sw_file.name.endswith('csv'):
                sw_data = pd.read_csv(sw_file)
            else:
                sw_data = pd.read_excel(sw_file, sheet_name=0)
            
            st.success(f"✅ Cargado: {sw_file.name}")
            st.caption(f"Filas: {len(sw_data)} | Columnas: {len(sw_data.columns)}")
            sw_columns = list(sw_data.columns)
            
        except Exception as e:
            st.error(f"❌ Error al cargar: {str(e)}")
            sw_data = None

with col2:
    st.markdown("### 🗄️ Base de Datos (BBDD)")
    bbdd_file = st.file_uploader(
        "Carga tu archivo de BBDD",
        type=["xlsx", "xls", "csv"],
        key="bbdd_file",
        help="Archivo de tu base de datos"
    )
    bbdd_data = None
    bbdd_columns = None
    
    if bbdd_file:
        try:
            if bbdd_file.name.endswith('csv'):
                bbdd_data = pd.read_csv(bbdd_file)
            else:
                bbdd_data = pd.read_excel(bbdd_file, sheet_name=0)
            
            st.success(f"✅ Cargado: {bbdd_file.name}")
            st.caption(f"Filas: {len(bbdd_data)} | Columnas: {len(bbdd_data.columns)}")
            bbdd_columns = list(bbdd_data.columns)
            
        except Exception as e:
            st.error(f"❌ Error al cargar: {str(e)}")
            bbdd_data = None

# ============= SECCIÓN 2: SELECCIONAR COLUMNAS =============
if sw_data is not None and bbdd_data is not None:
    st.divider()
    st.markdown("## 🎯 Paso 2: Seleccionar Columnas")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### SolidWorks - Columnas")
        sw_col_ref = st.selectbox(
            "Referencia (opcional)",
            options=[None] + sw_columns,
            key="sw_ref"
        )
        sw_col_num = st.selectbox(
            "Número de Parte",
            options=sw_columns,
            key="sw_num"
        )
        sw_col_desc = st.selectbox(
            "Descripción",
            options=sw_columns,
            key="sw_desc"
        )
        sw_col_qty = st.selectbox(
            "Cantidad",
            options=sw_columns,
            key="sw_qty"
        )
    
    with col2:
        st.markdown("### BBDD - Columnas")
        bbdd_col_num = st.selectbox(
            "Número de Parte",
            options=bbdd_columns,
            key="bbdd_num"
        )
        bbdd_col_desc = st.selectbox(
            "Descripción",
            options=bbdd_columns,
            key="bbdd_desc"
        )
        bbdd_col_qty = st.selectbox(
            "Cantidad",
            options=bbdd_columns,
            key="bbdd_qty"
        )
        bbdd_col_ref = st.selectbox(
            "Ref Comercial (opcional)",
            options=[None] + bbdd_columns,
            key="bbdd_ref"
        )
    
    # ============= VALIDAR =============
    st.divider()
    
    if st.button("🚀 VALIDAR MATERIALES", use_container_width=True, type="primary"):
        with st.spinner("⏳ Validando... esto puede tomar un momento"):
            
            # Procesar SolidWorks
            sw_elements = []
            for idx, row in sw_data.iterrows():
                try:
                    num_parte = str(row[sw_col_num]).strip() if pd.notna(row[sw_col_num]) else ""
                    desc = str(row[sw_col_desc]).strip() if pd.notna(row[sw_col_desc]) else ""
                    qty = int(row[sw_col_qty]) if pd.notna(row[sw_col_qty]) else 1
                    ref = str(row[sw_col_ref]).strip() if sw_col_ref and pd.notna(row[sw_col_ref]) else ""
                    
                    if num_parte or desc:
                        sw_elements.append({
                            'referencia': ref,
                            'numero_parte': num_parte,
                            'descripcion': desc,
                            'cantidad': qty,
                            'fuente': 'SolidWorks'
                        })
                except:
                    pass
            
            # Procesar BBDD
            bbdd_elements = []
            for idx, row in bbdd_data.iterrows():
                try:
                    num_parte = str(row[bbdd_col_num]).strip() if pd.notna(row[bbdd_col_num]) else ""
                    desc = str(row[bbdd_col_desc]).strip() if pd.notna(row[bbdd_col_desc]) else ""
                    qty = int(row[bbdd_col_qty]) if pd.notna(row[bbdd_col_qty]) else 0
                    ref = str(row[bbdd_col_ref]).strip() if bbdd_col_ref and pd.notna(row[bbdd_col_ref]) else ""
                    
                    if num_parte or desc:
                        bbdd_elements.append({
                            'numero_parte': num_parte,
                            'descripcion': desc,
                            'cantidad': qty,
                            'ref_comercial': ref,
                            'fuente': 'BBDD'
                        })
                except:
                    pass
            
            # Comparación
            consolidado = []
            discrepancias = []
            
            for sw in sw_elements:
                bbdd_match = None
                
                # Buscar por número de parte
                if search_method in ["Por Número de Parte", "Ambos"]:
                    if sw['numero_parte']:
                        for bb in bbdd_elements:
                            if bb['numero_parte'] and sw['numero_parte'].lower() == bb['numero_parte'].lower():
                                bbdd_match = bb
                                break
                
                # Buscar por descripción
                if not bbdd_match and search_method in ["Por Descripción", "Ambos"]:
                    if sw['descripcion']:
                        for bb in bbdd_elements:
                            if bb['descripcion']:
                                sw_desc_lower = sw['descripcion'].lower()
                                bb_desc_lower = bb['descripcion'].lower()
                                if sw_desc_lower in bb_desc_lower or bb_desc_lower in sw_desc_lower:
                                    bbdd_match = bb
                                    break
                
                # Determinar estado
                if not bbdd_match:
                    estado = "✗ FALTA"
                    severidad = "error"
                    accion = "Crear en BBDD"
                elif sw['cantidad'] != bbdd_match['cantidad']:
                    estado = "⚠ QTY"
                    severidad = "warning"
                    accion = f"BBDD: {bbdd_match['cantidad']} → {sw['cantidad']}"
                    discrepancias.append({
                        'tipo': 'CANTIDAD',
                        'elemento': sw['descripcion'],
                        'sw_qty': sw['cantidad'],
                        'bbdd_qty': bbdd_match['cantidad']
                    })
                else:
                    estado = "✓ OK"
                    severidad = "success"
                    accion = "Sin cambios"
                
                if estado != "✓ OK":
                    discrepancias.append({
                        'tipo': estado.split()[0],
                        'elemento': sw['descripcion'],
                        'numero_parte': sw['numero_parte'],
                        'sw_qty': sw['cantidad'],
                        'bbdd_qty': bbdd_match['cantidad'] if bbdd_match else None
                    })
                
                consolidado.append({
                    'Referencia': sw['referencia'],
                    'Número Parte': sw['numero_parte'],
                    'Descripción': sw['descripcion'],
                    'Qty SolidWorks': sw['cantidad'],
                    'Qty BBDD': bbdd_match['cantidad'] if bbdd_match else 'FALTA',
                    'Estado': estado,
                    'Acción': accion,
                    'Severidad': severidad
                })
            
            # Guardar en session state
            st.session_state.consolidado = consolidado
            st.session_state.discrepancias = discrepancias
            st.session_state.sw_total = len(sw_elements)
            st.session_state.bbdd_total = len(bbdd_elements)
            st.session_state.matched = len([x for x in consolidado if x['Estado'] == "✓ OK"])
            st.session_state.validado = True
    
    # ============= MOSTRAR RESULTADOS =============
    if 'validado' in st.session_state and st.session_state.validado:
        st.divider()
        st.markdown("## 📊 Resultados de Validación")
        
        # Resumen
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("📊 SolidWorks Total", st.session_state.sw_total)
        
        with col2:
            st.metric("🗄️ BBDD Total", st.session_state.bbdd_total)
        
        with col3:
            st.metric("✓ Coincidencias", st.session_state.matched)
            
        with col4:
            discrepancias_count = len(st.session_state.discrepancias)
            st.metric("⚠️ Discrepancias", discrepancias_count)
        
        # Porcentaje
        if st.session_state.sw_total > 0:
            porcentaje = (st.session_state.matched / st.session_state.sw_total * 100)
            col1, col2, col3 = st.columns([1, 2, 1])
            with col2:
                st.markdown(f"### {porcentaje:.1f}% Validación OK")
        
        st.divider()
        
        # Tabs de resultados
        tab1, tab2, tab3 = st.tabs(["📋 Consolidado Completo", "🔴 Discrepancias", "✓ OK Coincidentes"])
        
        with tab1:
            st.markdown("### Consolidado Unificado")
            
            df_display = pd.DataFrame(st.session_state.consolidado)
            
            # Colorear estados
            def color_estado(val):
                if '✓' in str(val):
                    return 'background-color: #d4edda; color: #155724; font-weight: bold'
                elif '⚠' in str(val):
                    return 'background-color: #fff3cd; color: #856404; font-weight: bold'
                elif '✗' in str(val):
                    return 'background-color: #f8d7da; color: #721c24; font-weight: bold'
                return ''
            
            styled_df = df_display.style.applymap(color_estado, subset=['Estado'])
            st.dataframe(styled_df, use_container_width=True, hide_index=True)
            
            # Descargar consolidado
            col1, col2 = st.columns([1, 1])
            with col1:
                # Excel
                output = BytesIO()
                with pd.ExcelWriter(output, engine='openpyxl') as writer:
                    df_display.to_excel(writer, sheet_name='Consolidado', index=False)
                
                st.download_button(
                    label="📥 Descargar como Excel",
                    data=output.getvalue(),
                    file_name="Consolidado_Materiales.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    use_container_width=True
                )
            
            with col2:
                # CSV
                csv = df_display.to_csv(index=False)
                st.download_button(
                    label="📥 Descargar como CSV",
                    data=csv,
                    file_name="Consolidado_Materiales.csv",
                    mime="text/csv",
                    use_container_width=True
                )
        
        with tab2:
            if st.session_state.discrepancias:
                st.markdown(f"### {len(st.session_state.discrepancias)} Discrepancias Encontradas")
                
                # Filtrar por tipo
                tipos = st.multiselect(
                    "Filtrar por tipo:",
                    options=["✗", "⚠"],
                    default=["✗", "⚠"],
                    key="filtro_tipos"
                )
                
                for disc in st.session_state.discrepancias:
                    if any(t in disc['tipo'] for t in tipos):
                        if disc['tipo'] == '✗':
                            with st.container():
                                col1, col2 = st.columns([3, 1])
                                with col1:
                                    st.markdown(f"**🔴 FALTA en BBDD**")
                                    st.write(f"Elemento: {disc['elemento']}")
                                    st.write(f"Número: {disc['numero_parte']}")
                                with col2:
                                    st.markdown(f"**Qty: {disc['sw_qty']}**")
                        else:
                            with st.container():
                                col1, col2 = st.columns([3, 1])
                                with col1:
                                    st.markdown(f"**🟠 Diferencia de Cantidad**")
                                    st.write(f"Elemento: {disc['elemento']}")
                                    st.write(f"Número: {disc['numero_parte']}")
                                with col2:
                                    st.markdown(f"**SW: {disc['sw_qty']} | BBDD: {disc['bbdd_qty']}**")
                        st.divider()
            else:
                st.success("✅ ¡No hay discrepancias! Todo coincide perfectamente.")
        
        with tab3:
            ok_items = [x for x in st.session_state.consolidado if x['Estado'] == "✓ OK"]
            if ok_items:
                st.markdown(f"### {len(ok_items)} Elementos Correctos")
                df_ok = pd.DataFrame(ok_items)
                st.dataframe(df_ok[['Número Parte', 'Descripción', 'Qty SolidWorks']], 
                           use_container_width=True, hide_index=True)
            else:
                st.info("No hay elementos que coincidan perfectamente.")

# Footer
st.divider()
st.markdown("""
<div style="text-align: center; color: #999; padding: 20px;">
    <p>🔍 Validador de Listas de Materiales | Versión 1.0</p>
    <p>Compara SolidWorks vs BBDD y genera consolidado unificado</p>
</div>
""", unsafe_allow_html=True)
