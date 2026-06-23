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

# Estilos CSS
st.markdown("""
<style>
    .main {
        padding: 2rem;
    }
</style>
""", unsafe_allow_html=True)

# Título
st.markdown("""
<h1 style="text-align: center; color: #667eea;">
    🔍 Validador de Listas de Materiales
</h1>
<p style="text-align: center; color: #666;">
    Compara: SolidWorks Col2 vs BBDD (Proyectos.ref_empresa + Elementos.ref_empresa)
</p>
""", unsafe_allow_html=True)

st.divider()

# Sidebar
with st.sidebar:
    st.markdown("### 📋 Instrucciones")
    st.markdown("""
    **Paso 1:** Carga SolidWorks
    
    **Paso 2:** Carga BBDD
    
    **Paso 3:** Click VALIDAR
    
    **Paso 4:** Descarga consolidado
    """)
    
    st.divider()
    st.markdown("### ⚙️ Configuración")
    
    busqueda = st.radio(
        "Método de búsqueda:",
        options=[
            "Exacto (igual)",
            "Parcial (contiene)",
            "Ambos"
        ],
        help="Cómo comparar las referencias"
    )

# ============= SECCIÓN 1: CARGAR ARCHIVOS =============
st.markdown("## 📁 Paso 1: Cargar Archivos")

col1, col2 = st.columns(2)

with col1:
    st.markdown("### 📊 SolidWorks")
    st.caption("Columna 2 = Ref a comparar")
    sw_file = st.file_uploader(
        "Carga tu SolidWorks (2601.xls)",
        type=["xlsx", "xls", "csv"],
        key="sw_file"
    )
    sw_data = None
    
    if sw_file:
        try:
            if sw_file.name.endswith('csv'):
                sw_data = pd.read_csv(sw_file)
            else:
                sw_data = pd.read_excel(sw_file, sheet_name=0)
            
            st.success(f"✅ {sw_file.name}")
            st.caption(f"Filas: {len(sw_data)} | Columnas: {len(sw_data.columns)}")
            
            with st.expander("Ver primeras filas"):
                st.dataframe(sw_data.head(3), use_container_width=True)
            
        except Exception as e:
            st.error(f"❌ Error: {str(e)}")
            sw_data = None

with col2:
    st.markdown("### 🗄️ Base de Datos (BBDD)")
    st.caption("Busca en: Proyectos.ref_empresa + Elementos.ref_empresa")
    bbdd_file = st.file_uploader(
        "Carga tu BBDD (ProyectosXConjArt.xlsx)",
        type=["xlsx", "xls", "csv"],
        key="bbdd_file"
    )
    bbdd_data = None
    
    if bbdd_file:
        try:
            if bbdd_file.name.endswith('csv'):
                bbdd_data = pd.read_csv(bbdd_file)
            else:
                bbdd_data = pd.read_excel(bbdd_file, sheet_name=0)
            
            st.success(f"✅ {bbdd_file.name}")
            st.caption(f"Filas: {len(bbdd_data)} | Columnas: {len(bbdd_data.columns)}")
            
            with st.expander("Ver primeras filas"):
                st.dataframe(bbdd_data.head(3), use_container_width=True)
            
        except Exception as e:
            st.error(f"❌ Error: {str(e)}")
            bbdd_data = None

# ============= VALIDAR =============
if sw_data is not None and bbdd_data is not None:
    st.divider()
    st.markdown("## 🚀 Paso 2: Validar")
    
    # Verificar columnas
    sw_cols = list(sw_data.columns)
    bbdd_cols = list(bbdd_data.columns)
    
    col1, col2 = st.columns([1, 1])
    
    with col1:
        if len(sw_cols) >= 2:
            sw_col_ref = sw_cols[1]  # Columna 2
            st.info(f"📊 SolidWorks: Columna 2 → **{sw_col_ref}**")
        else:
            st.error("❌ SolidWorks no tiene 2 columnas")
            sw_data = None
    
    with col2:
        # Buscar columnas de BBDD
        proyectos_col = None
        elementos_col = None
        
        for col in bbdd_cols:
            col_lower = str(col).lower()
            if 'proyectos' in col_lower and 'ref_empresa' in col_lower:
                proyectos_col = col
            if 'elementos' in col_lower and 'ref_empresa' in col_lower:
                elementos_col = col
        
        info_text = "🗄️ BBDD buscará en:"
        if proyectos_col:
            info_text += f"\n  1️⃣ **{proyectos_col}**"
        else:
            info_text += f"\n  1️⃣ (No encontrada: Proyectos.ref_empresa)"
        
        if elementos_col:
            info_text += f"\n  2️⃣ **{elementos_col}**"
        else:
            info_text += f"\n  2️⃣ (No encontrada: Elementos.ref_empresa)"
        
        st.info(info_text)
    
    st.divider()
    
    if st.button("🚀 VALIDAR MATERIALES", use_container_width=True, type="primary"):
        
        with st.spinner("⏳ Validando... procesando datos"):
            
            # Procesar SolidWorks
            sw_elements = []
            for idx, row in sw_data.iterrows():
                try:
                    ref = str(row[sw_col_ref]).strip() if pd.notna(row[sw_col_ref]) else ""
                    
                    # Obtener otras columnas para referencia
                    cols_list = list(row.index)
                    col1_val = str(row[cols_list[0]]).strip() if len(cols_list) > 0 and pd.notna(row[cols_list[0]]) else ""
                    col3_val = str(row[cols_list[2]]).strip() if len(cols_list) > 2 and pd.notna(row[cols_list[2]]) else ""
                    col4_val = int(row[cols_list[3]]) if len(cols_list) > 3 and pd.notna(row[cols_list[3]]) else 1
                    
                    if ref:
                        sw_elements.append({
                            'col1': col1_val,
                            'ref_empresa': ref,
                            'descripcion': col3_val,
                            'cantidad': col4_val,
                            'fuente': 'SolidWorks'
                        })
                except:
                    pass
            
            # Procesar BBDD
            bbdd_elements = []
            for idx, row in bbdd_data.iterrows():
                try:
                    # Obtener referencias de ambas columnas
                    ref_proyectos = str(row[proyectos_col]).strip() if proyectos_col and pd.notna(row[proyectos_col]) else ""
                    ref_elementos = str(row[elementos_col]).strip() if elementos_col and pd.notna(row[elementos_col]) else ""
                    
                    # Usar la que tenga valor, o ambas si ambas tienen
                    refs = []
                    if ref_proyectos:
                        refs.append(ref_proyectos)
                    if ref_elementos:
                        refs.append(ref_elementos)
                    
                    if not refs:
                        continue
                    
                    # Obtener cantidad
                    cantidad = 0
                    for col in bbdd_data.columns:
                        if 'cant' in str(col).lower():
                            cantidad = int(row[col]) if pd.notna(row[col]) else 0
                            break
                    
                    # Obtener descripción
                    descripcion = ""
                    for col in bbdd_data.columns:
                        if 'descripcion' in str(col).lower() or 'elemento' in str(col).lower():
                            descripcion = str(row[col]).strip() if pd.notna(row[col]) else ""
                            break
                    
                    # Agregar entrada por cada referencia
                    for ref in refs:
                        if ref:
                            bbdd_elements.append({
                                'ref_empresa': ref,
                                'descripcion': descripcion,
                                'cantidad': cantidad,
                                'fuente': 'BBDD'
                            })
                except:
                    pass
            
            st.info(f"✅ Procesados: {len(sw_elements)} SolidWorks, {len(bbdd_elements)} BBDD")
            
            # Comparación
            consolidado = []
            discrepancias = []
            
            for sw in sw_elements:
                bbdd_match = None
                sw_ref = sw['ref_empresa'].lower()
                
                # BÚSQUEDA EXACTA
                if busqueda in ["Exacto (igual)", "Ambos"]:
                    for bb in bbdd_elements:
                        if sw_ref == bb['ref_empresa'].lower():
                            bbdd_match = bb
                            break
                
                # BÚSQUEDA PARCIAL
                if not bbdd_match and busqueda in ["Parcial (contiene)", "Ambos"]:
                    for bb in bbdd_elements:
                        if sw_ref in bb['ref_empresa'].lower() or bb['ref_empresa'].lower() in sw_ref:
                            bbdd_match = bb
                            break
                
                # Determinar estado
                if not bbdd_match:
                    estado = "✗ FALTA"
                    accion = "Crear en BBDD"
                    severidad = "error"
                elif sw['cantidad'] != bbdd_match['cantidad']:
                    estado = "⚠ QTY"
                    accion = f"BBDD: {bbdd_match['cantidad']} → SW: {sw['cantidad']}"
                    severidad = "warning"
                    discrepancias.append({
                        'ref': sw['ref_empresa'],
                        'descripcion': sw['descripcion'],
                        'sw_qty': sw['cantidad'],
                        'bbdd_qty': bbdd_match['cantidad'],
                        'tipo': 'CANTIDAD'
                    })
                else:
                    estado = "✓ OK"
                    accion = "Correcto"
                    severidad = "success"
                
                if estado == "✗ FALTA":
                    discrepancias.append({
                        'ref': sw['ref_empresa'],
                        'descripcion': sw['descripcion'],
                        'sw_qty': sw['cantidad'],
                        'bbdd_qty': None,
                        'tipo': 'FALTA'
                    })
                
                consolidado.append({
                    'Col1': sw['col1'],
                    'Ref Empresa': sw['ref_empresa'],
                    'Descripción': sw['descripcion'],
                    'Qty SolidWorks': sw['cantidad'],
                    'Qty BBDD': bbdd_match['cantidad'] if bbdd_match else 'FALTA',
                    'Estado': estado,
                    'Acción': accion,
                    'Severidad': severidad
                })
            
            # Guardar en session
            st.session_state.consolidado = consolidado
            st.session_state.discrepancias = discrepancias
            st.session_state.sw_total = len(sw_elements)
            st.session_state.bbdd_total = len(bbdd_elements)
            st.session_state.matched = len([x for x in consolidado if x['Estado'] == "✓ OK"])
            st.session_state.validado = True
    
    # ============= RESULTADOS =============
    if 'validado' in st.session_state and st.session_state.validado:
        st.divider()
        st.markdown("## 📊 Resultados de Validación")
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("📊 SolidWorks", st.session_state.sw_total)
        
        with col2:
            st.metric("🗄️ BBDD", st.session_state.bbdd_total)
        
        with col3:
            st.metric("✓ OK", st.session_state.matched)
        
        with col4:
            st.metric("⚠️ Problemas", len(st.session_state.discrepancias))
        
        if st.session_state.sw_total > 0:
            porcentaje = (st.session_state.matched / st.session_state.sw_total * 100)
            st.markdown(f"### {porcentaje:.1f}% Validación Correcta")
        
        st.divider()
        
        # Tabs
        tab1, tab2, tab3 = st.tabs(["📋 Consolidado Completo", "🔴 Problemas Encontrados", "✓ Elementos OK"])
        
        with tab1:
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
            
            # Descargar
            col1, col2 = st.columns([1, 1])
            
            with col1:
                output = BytesIO()
                with pd.ExcelWriter(output, engine='openpyxl') as writer:
                    df_display[['Col1', 'Ref Empresa', 'Descripción', 'Qty SolidWorks', 'Qty BBDD', 'Estado', 'Acción']].to_excel(
                        writer, sheet_name='Consolidado', index=False
                    )
                st.download_button(
                    label="📥 Descargar Excel",
                    data=output.getvalue(),
                    file_name="Consolidado_Validacion.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    use_container_width=True
                )
            
            with col2:
                csv = df_display[['Col1', 'Ref Empresa', 'Descripción', 'Qty SolidWorks', 'Qty BBDD', 'Estado', 'Acción']].to_csv(index=False)
                st.download_button(
                    label="📥 Descargar CSV",
                    data=csv,
                    file_name="Consolidado_Validacion.csv",
                    mime="text/csv",
                    use_container_width=True
                )
        
        with tab2:
            if st.session_state.discrepancias:
                st.markdown(f"### {len(st.session_state.discrepancias)} Problemas Detectados")
                
                # Contar por tipo
                faltas = len([x for x in st.session_state.discrepancias if x['tipo'] == 'FALTA'])
                cantidades = len([x for x in st.session_state.discrepancias if x['tipo'] == 'CANTIDAD'])
                
                col1, col2 = st.columns(2)
                with col1:
                    st.metric("❌ Faltan en BBDD", faltas)
                with col2:
                    st.metric("⚠️ Cantidad Incorrecta", cantidades)
                
                st.divider()
                
                # Mostrar detalles
                for disc in st.session_state.discrepancias:
                    if disc['tipo'] == 'FALTA':
                        with st.container():
                            st.error(f"**❌ FALTA en BBDD**")
                            st.write(f"  Ref: `{disc['ref']}`")
                            st.write(f"  Descripción: {disc['descripcion']}")
                            st.write(f"  Cantidad SolidWorks: {disc['sw_qty']}")
                    else:
                        with st.container():
                            st.warning(f"**⚠️ CANTIDAD INCORRECTA**")
                            st.write(f"  Ref: `{disc['ref']}`")
                            st.write(f"  Descripción: {disc['descripcion']}")
                            st.write(f"  SolidWorks: {disc['sw_qty']} | BBDD: {disc['bbdd_qty']}")
                    st.divider()
            else:
                st.success("✅ ¡SIN PROBLEMAS! Todas las referencias coinciden")
        
        with tab3:
            ok_items = [x for x in st.session_state.consolidado if x['Estado'] == "✓ OK"]
            if ok_items:
                st.markdown(f"### {len(ok_items)} Elementos Correctos")
                df_ok = pd.DataFrame(ok_items)
                st.dataframe(
                    df_ok[['Ref Empresa', 'Descripción', 'Qty SolidWorks', 'Qty BBDD']], 
                    use_container_width=True, 
                    hide_index=True
                )
            else:
                st.info("No hay elementos perfectamente correctos")

st.divider()
st.markdown("""
<div style="text-align: center; color: #999;">
    <p>🔍 Validador de Materiales | v3.0 - Busca en Proyectos.ref_empresa + Elementos.ref_empresa</p>
</div>
""", unsafe_allow_html=True)
