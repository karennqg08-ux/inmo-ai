import streamlit as st
import google.generativeai as genai

# ---------------------------------------------------------
# 1. CONFIGURACIÓN DE PÁGINA Y ESTILOS CORPORATIVOS
# ---------------------------------------------------------
st.set_page_config(
    page_title="InmoAI - Generador Profesional de Anuncios",
    page_icon="🏢",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    .stApp { background-color: #F8FAFC; }
    .main-header {
        background: linear-gradient(135deg, #1E293B 0%, #0F172A 100%);
        padding: 2rem;
        border-radius: 12px;
        color: white;
        margin-bottom: 2rem;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
    }
    .main-header h1 { color: #F8FAFC !important; font-weight: 700; margin-bottom: 0.5rem; }
    .main-header p { color: #94A3B8; font-size: 1.1rem; }
    .stButton>button { border-radius: 8px; font-weight: 600; }
</style>
""", unsafe_allow_html=True)

# ---------------------------------------------------------
# 2. CONEXIÓN AUTOMÁTICA Y LISTA DE MODELOS
# ---------------------------------------------------------
raw_key = st.secrets.get("GEMINI_API_KEY", "")
api_key = raw_key.strip().strip('"').strip("'")
modelos_candidatos = []

if api_key:
    try:
        genai.configure(api_key=api_key)
        for m in genai.list_models():
            if 'generateContent' in m.supported_generation_methods:
                modelos_candidatos.append(m.name)
    except Exception as e:
        st.error(f"Error al conectar con la API: {e}")

# ---------------------------------------------------------
# 3. BARRA LATERAL
# ---------------------------------------------------------
with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/602/602275.png", width=60)
    st.title("InmoAI Pro")
    st.caption("v1.5 • Delimitador Secreto Activo")
    st.markdown("---")
    
    if modelos_candidatos:
        st.success("🟢 Sistema Activo & Listo")
    elif api_key:
        st.warning("⚠️ Validando conexión con Google...")
    else:
        st.error("🔴 Falta configurar GEMINI_API_KEY en Secrets.")
        
    st.markdown("---")
    st.info("💡 **Estado del Servicio:**\nAcceso Comercial Activo.")

# ---------------------------------------------------------
# 4. ENCABEZADO
# ---------------------------------------------------------
st.markdown("""
<div class="main-header">
    <h1>🏢 InmoAI Studio</h1>
    <p>Plataforma de IA especializada en Copywriting Inmobiliario de Alto Impacto.</p>
</div>
""", unsafe_allow_html=True)

tab1, tab2 = st.tabs(["✨ Generador de Anuncios", "ℹ️ Guía & Soporte"])

# ---------------------------------------------------------
# 5. FORMULARIO Y GENERACIÓN DE CONTENIDO
# ---------------------------------------------------------
with tab1:
    with st.form("formulario_propiedad_completo"):
        col1, col2 = st.columns(2)

        with col1:
            st.subheader("📍 Ubicación y Datos Clave")
            direccion = st.text_input("Dirección / Zona", placeholder="Ej: Calle 79 sur #58-66, Envigado")
            tipo_propiedad = st.selectbox(
                "Tipo de propiedad",
                ["Apartamento", "Casa", "Casa Campestre", "Penthouse", "Oficina", "Local Comercial", "Lote / Terreno"]
            )
            precio = st.text_input("Precio de oferta", placeholder="Ej: $267,000,000 COP")
            
            st.subheader("📐 Dimensiones")
            col_a1, col_a2 = st.columns(2)
            with col_a1:
                area_privada = st.text_input("Área privada", placeholder="Ej: 75 m²")
            with col_a2:
                area_construida = st.text_input("Área construida", placeholder="Ej: 82 m²")

        with col2:
            st.subheader("🛋️ Distribución Interna")
            col_sub1, col_sub2, col_sub3 = st.columns(3)
            with col_sub1:
                habitaciones = st.number_input("Habitaciones", min_value=0, value=3)
            with col_sub2:
                banos = st.number_input("Baños", min_value=0, value=2)
            with col_sub3:
                parqueaderos = st.number_input("Parqueaderos", min_value=0, value=1)

            st.subheader("🎯 Estrategia Comercial")
            tono = st.selectbox(
                "Tono del mensaje", 
                [
                    "Familiar (Cálido, emotivo y enfocado en momentos)", 
                    "Sofisticado / Lujo (Elegante, exclusivo y de alto nivel)", 
                    "Inversionista (Rentabilidad, números y oportunidad)", 
                    "Joven / Moderno (Dinámico, fresco y directo)"
                ]
            )
            plataforma = st.selectbox(
                "Canal de difusión", 
                [
                    "Instagram / Facebook (Corto, emojis, hashtags y alto impacto)", 
                    "Portal Inmobiliario (Largo, detallado y descriptivo)", 
                    "WhatsApp (Directo, profesional y listo para enviar)"
                ]
            )

        st.markdown("---")
        col3, col4 = st.columns(2)
        with col3:
            notas = st.text_area(
                "Características destacadas & Amenidades", 
                placeholder="Ej: Piscina, zona BBQ, cerca a colegios, vista panorámica, cocina remodelada...",
                height=100
            )
        with col4:
            cta = st.text_input(
                "📞 Datos de Contacto / Llamado a la Acción", 
                placeholder="Ej: Escribe a Carlos al 300 754 8766",
                value=""
            )

        submit_button = st.form_submit_button("🚀 Generar Anuncio Profesional", type="primary", use_container_width=True)

    if submit_button:
        if not api_key:
            st.error("⚠️ La aplicación no tiene una API Key configurada en el servidor.")
        elif not modelos_candidatos:
            st.error("⚠️ No se encontraron modelos de IA disponibles para esta clave API.")
        elif not direccion or not precio:
            st.warning("⚠️ Debes completar al menos los campos de Dirección y Precio.")
        else:
            prompt_usuario = f"""
            Redacta propuestas de anuncios inmobiliarios profesionales en español.

            DATOS DE LA PROPIEDAD:
            - Tipo: {tipo_propiedad}
            - Ubicación: {direccion}
            - Precio: {precio}
            - Área privada: {area_privada if area_privada else 'No especificada'}
            - Área construida: {area_construida if area_construida else 'No especificada'}
            - Habitaciones: {habitaciones} | Baños: {banos} | Parqueaderos: {parqueaderos}
            - Amenidades: {notas}
            - Tono comercial: {tono}
            - Canal: {plataforma}
            - Contacto: {cta}

            INSTRUCCIÓN CRÍTICA DE MARCA:
            Antes de comenzar a escribir las opciones en español, DEBES escribir exactamente esta marca en una línea propia:
            ===RESULTADO_FINAL===

            Luego de escribir esa marca, presenta inmediatamente las opciones:
            **Opción 1:** (Enfoque principal)
            **Opción 2:** (Enfoque alternativo)
            💡 **Consejos de publicación**
            """
            
            exito = False
            
            with st.spinner("Redactando propuesta publicitaria... ✍️"):
                for mod_name in modelos_candidatos:
                    try:
                        modelo = genai.GenerativeModel(mod_name)
                        respuesta = modelo.generate_content(prompt_usuario)
                        texto_bruto = respuesta.text
                        
                        # CORTADOR PERFECTO: EXTRAE SOLO LO QUE ESTÁ DESPUÉS DE LA MARCA
                        MARCA = "===RESULTADO_FINAL==="
                        if MARCA in texto_bruto:
                            texto_limpio = texto_bruto.split(MARCA)[-1].strip()
                        else:
                            # Si por algún motivo la IA no imprimió la marca, usa el texto original
                            texto_limpio = texto_bruto.strip()

                        st.success("¡Anuncio generado exitosamente!")
                        st.subheader("📄 Resultado Generado")
                        st.markdown("Copia el texto haciendo clic en el botón de la esquina superior derecha del recuadro:")
                        st.code(texto_limpio, language="markdown")
                        
                        exito = True
                        break
                    except Exception:
                        continue
            
            if not exito:
                st.error("❌ No se pudo conectar con los servidores de Google. Verifica la API Key.")

# ---------------------------------------------------------
# 6. PESTAÑA SECUNDARIA
# ---------------------------------------------------------
with tab2:
    st.subheader("💡 ¿Cómo sacar el máximo provecho a InmoAI?")
    st.markdown("""
    * **Sé específico en las notas:** Entre más amenidades describas, mejor será el gancho comercial.
    * **Prueba varios tonos:** Para propiedades lujosas usa el tono *Sofisticado*, para familias jóvenes usa *Moderno*.
    * **Copia rápida:** Usa el botón flotante de copia en el recuadro gris de resultados para pegar directamente en tu red social o WhatsApp.
    """)
