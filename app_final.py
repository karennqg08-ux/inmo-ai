import hashlib
import base64
from urllib.parse import urlencode
import streamlit as st
import google.generativeai as genai
from supabase import create_client, Client

# ---------------------------------------------------------
# 1. CONFIGURACIÓN DE PÁGINA Y ESTILOS
# ---------------------------------------------------------
st.set_page_config(
    page_title="InmoAI - Plataforma Profesional",
    page_icon="🏢",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
    /* Ocultamos el menú estándar de Streamlit y el pie de página */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    
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
    .paywall-box {
        background-color: #FEF2F2;
        border: 2px solid #EF4444;
        border-radius: 12px;
        padding: 2rem;
        text-align: center;
        margin-top: 1rem;
    }
    .admin-box {
        background-color: #F0FDF4;
        border: 1px solid #22C55E;
        padding: 1rem;
        border-radius: 8px;
        margin-bottom: 1rem;
    }
</style>
""", unsafe_allow_html=True)

# ---------------------------------------------------------
# 2. CONEXIÓN CON SUPABASE Y GEMINI API
# ---------------------------------------------------------
raw_key = st.secrets.get("GEMINI_API_KEY", "")
api_key = raw_key.strip().strip('"').strip("'")

supabase_url = st.secrets.get("SUPABASE_URL", "").strip().rstrip('/')
supabase_key = st.secrets.get("SUPABASE_KEY", "").strip().strip('"').strip("'")

# Correo del Administrador
ADMIN_EMAIL = st.secrets.get("ADMIN_EMAIL", "admin@tuinmoai.com").strip().lower()

# Enlace de pago (Mercado Pago / Wompi / WhatsApp)
PAYMENT_LINK = st.secrets.get(
    "PAYMENT_LINK", 
    "https://wa.me/573000000000?text=Hola,%20quiero%20activar%20mi%20suscripcion%20InmoAI%20Pro"
).strip()

supabase: Client = None
if supabase_url and supabase_key:
    try:
        supabase = create_client(supabase_url, supabase_key)
    except Exception as e:
        st.error(f"Error al inicializar cliente de Supabase: {e}")

modelos_candidatos = []
if api_key:
    try:
        genai.configure(api_key=api_key)
        for m in genai.list_models():
            if 'generateContent' in m.supported_generation_methods:
                modelos_candidatos.append(m.name)
    except Exception as e:
        st.error(f"Error al conectar con Google AI: {e}")

# ---------------------------------------------------------
# 3. CONSTRUCCIÓN DE LLAVE DE SEGURIDAD PKCE (OAUTH)
# ---------------------------------------------------------
FIXED_PKCE_VERIFIER = "InmoAIStudioPKCECodeVerifierKey2026SecureConstantStringForStreamlit123456"

def get_pkce_challenge(verifier: str) -> str:
    digest = hashlib.sha256(verifier.encode('ascii')).digest()
    return base64.urlsafe_b64encode(digest).decode('ascii').rstrip('=')

FIXED_PKCE_CHALLENGE = get_pkce_challenge(FIXED_PKCE_VERIFIER)

if "usuario" not in st.session_state:
    st.session_state["usuario"] = None

# Procesar retorno desde Google OAuth
params = st.query_params
if "code" in params and supabase:
    code = params["code"]
    try:
        res_auth = supabase.auth.exchange_code_for_session({
            "auth_code": code,
            "code_verifier": FIXED_PKCE_VERIFIER
        })
        
        if res_auth and res_auth.user:
            email_google = res_auth.user.email.lower()
            existente = supabase.table("usuarios").select("*").eq("email", email_google).execute()
            
            if existente.data:
                st.session_state["usuario"] = existente.data[0]
            else:
                nuevo_user = {
                    "email": email_google,
                    "password": "oauth_google_login",
                    "generaciones": 0,
                    "suscrito": False
                }
                insert_res = supabase.table("usuarios").insert(nuevo_user).execute()
                if insert_res.data:
                    st.session_state["usuario"] = insert_res.data[0]
            
            st.query_params.clear()
            st.rerun()
    except Exception:
        st.query_params.clear()
        st.error("Ocurrió un inconveniente al validar la sesión. Por favor, haz clic en 'Continuar con Google' para ingresar.")

# Generar enlace de autenticación directo con parámetro PKCE manual
google_login_url = None
if supabase_url:
    app_redirect_url = st.secrets.get("APP_URL", "https://share.streamlit.io").strip().rstrip('/')
    oauth_params = {
        "provider": "google",
        "redirect_to": app_redirect_url,
        "code_challenge": FIXED_PKCE_CHALLENGE,
        "code_challenge_method": "s256"
    }
    google_login_url = f"{supabase_url}/auth/v1/authorize?{urlencode(oauth_params)}"

# ---------------------------------------------------------
# 4. PANTALLA DE INICIO DE SESIÓN / REGISTRO
# ---------------------------------------------------------
if not st.session_state["usuario"]:
    st.markdown("""
    <div class="main-header" style="text-align: center;">
        <h1>🏢 Bienvenido a InmoAI Studio</h1>
        <p>Crea tu cuenta gratuita y genera tus primeros 3 anuncios inmobiliarios de alto impacto.</p>
    </div>
    """, unsafe_allow_html=True)

    col_center1, col_center2, col_center3 = st.columns([1, 2, 1])
    
    with col_center2:
        tab_login, tab_registro = st.tabs(["🔑 Iniciar Sesión", "📝 Crear Cuenta Gratis"])
        
        # TAB LOGIN
        with tab_login:
            st.subheader("Ingresa a tu cuenta")
            
            if google_login_url:
                st.link_button("🌐 Continuar con Google", google_login_url, use_container_width=True)
                st.markdown("<p style='text-align: center; color: #6B7280; font-size: 0.9rem;'>— o con tu correo —</p>", unsafe_allow_html=True)
            
            email_login = st.text_input("Correo Electrónico", key="login_email")
            pass_login = st.text_input("Contraseña", type="password", key="login_pass")
            
            if st.button("Iniciar Sesión", type="primary", use_container_width=True):
                if email_login and pass_login:
                    try:
                        res = supabase.table("usuarios").select("*").eq("email", email_login.strip().lower()).eq("password", pass_login).execute()
                        if res.data:
                            st.session_state["usuario"] = res.data[0]
                            st.success("¡Bienvenido de nuevo!")
                            st.rerun()
                        else:
                            st.error("Correo o contraseña incorrectos.")
                    except Exception as err:
                        st.error(f"Error de conexión: {err}")
                else:
                    st.warning("Completa todos los campos.")

        # TAB REGISTRO
        with tab_registro:
            st.subheader("Regístrate en 5 segundos")
            
            if google_login_url:
                st.link_button("🌐 Regístrate rápido con Google", google_login_url, use_container_width=True)
                st.markdown("<p style='text-align: center; color: #6B7280; font-size: 0.9rem;'>— o crea una cuenta manual —</p>", unsafe_allow_html=True)

            email_reg = st.text_input("Correo Electrónico", key="reg_email")
            pass_reg = st.text_input("Contraseña", type="password", key="reg_pass")
            
            if st.button("Crear Cuenta Gratis", type="primary", use_container_width=True):
                if email_reg and pass_reg:
                    try:
                        existe = supabase.table("usuarios").select("*").eq("email", email_reg.strip().lower()).execute()
                        if existe.data:
                            st.warning("Este correo ya está registrado. Ve a Iniciar Sesión.")
                        else:
                            nuevo = {
                                "email": email_reg.strip().lower(),
                                "password": pass_reg,
                                "generaciones": 0,
                                "suscrito": False
                            }
                            insert_res = supabase.table("usuarios").insert(nuevo).execute()
                            if insert_res.data:
                                st.session_state["usuario"] = insert_res.data[0]
                                st.success("¡Cuenta creada exitosamente! Tienes 3 anuncios gratis.")
                                st.rerun()
                            else:
                                st.error("No se pudo insertar el usuario.")
                    except Exception as err:
                        st.error(f"Error en el registro: {err}")
                else:
                    st.warning("Completa todos los campos.")

    st.stop()

# ---------------------------------------------------------
# 5. APLICACIÓN PRINCIPAL (USUARIO LOGUEADO)
# ---------------------------------------------------------
user = st.session_state["usuario"]
generaciones_usadas = user.get("generaciones", 0)
es_suscrito = user.get("suscrito", False)
user_email = user.get("email", "").strip().lower()

# BARRA LATERAL
with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/602/602275.png", width=60)
    st.title("InmoAI Pro")
    st.caption(f"👤 `{user_email}`")
    st.markdown("---")
    
    if es_suscrito:
        st.success("💎 Plan Pro Activo (Ilimitado)")
    else:
        restantes = max(0, 3 - generaciones_usadas)
        st.info(f"📊 **Prueba Gratuita:**\nTe quedan **{restantes} de 3** anuncios.")
        st.progress(min(1.0, generaciones_usadas / 3))
    
    st.markdown("---")
    
    # PANEL DE ADMINISTRADOR (Visible solo para el dueño)
    if user_email == ADMIN_EMAIL:
        st.subheader("👑 Panel de Administración")
        with st.expander("Gestionar Suscripciones"):
            target_email = st.text_input("Correo del usuario", placeholder="ejemplo@correo.com", key="admin_target")
            action = st.radio("Estado del Plan Pro", ["Activar (Suscrito)", "Desactivar (Free)"])
            
            if st.button("Guardar Cambios de Usuario", type="primary"):
                if target_email and supabase:
                    is_sub = (action == "Activar (Suscrito)")
                    res = supabase.table("usuarios").update({"suscrito": is_sub}).eq("email", target_email.strip().lower()).execute()
                    if res.data:
                        st.success(f"¡Usuario `{target_email}` actualizado a {'Suscrito' if is_sub else 'Gratuito'}!")
                        if target_email.strip().lower() == user_email:
                            st.session_state["usuario"]["suscrito"] = is_sub
                            st.rerun()
                    else:
                        st.error("No se encontró ningún usuario con ese correo.")
                else:
                    st.warning("Escribe un correo válido.")
        st.markdown("---")

    if st.button("🚪 Cerrar Sesión", use_container_width=True):
        st.session_state["usuario"] = None
        st.rerun()

# ENCABEZADO PRINCIPAL
st.markdown("""
<div class="main-header">
    <h1>🏢 InmoAI Studio</h1>
    <p>Plataforma de IA especializada en Copywriting Inmobiliario de Alto Impacto.</p>
</div>
""", unsafe_allow_html=True)

# VERIFICACIÓN DE LÍMITE (PAYWALL)
alcanzo_limite = (not es_suscrito) and (generaciones_usadas >= 3)

if alcanzo_limite:
    st.markdown("""
    <div class="paywall-box">
        <h2 style="color: #991B1B;">🔒 Has agotado tus 3 anuncios de prueba gratuita</h2>
        <p style="color: #7F1D1D; font-size: 1.1rem;">
            ¡Esperamos que hayas disfrutado de InmoAI! Para seguir generando anuncios ilimitados para todas tus propiedades, activa tu suscripción mensual.
        </p>
        <hr style="border-top: 1px solid #FECACA; margin: 1.5rem 0;">
        <h3 style="color: #991B1B;">🚀 Plan InmoAI Pro - Acceso Ilimitado</h3>
        <p style="font-size: 1.5rem; font-weight: bold; color: #1E293B;">$49,000 COP / mes</p>
        <p>✅ Generaciones ilimitadas • ✅ Todos los formatos • ✅ PSE / Nequi / Tarjetas</p>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("<br>", unsafe_allow_html=True)
    st.link_button("💳 Activar Suscripción Pro Ahora ($49,000 COP)", PAYMENT_LINK, type="primary", use_container_width=True)

else:
    # FORMULARIO DE GENERACIÓN DE ANUNCIOS
    with st.form("formulario_propiedad_completo"):
        col1, col2 = st.columns(2)

        with col1:
            st.subheader("📍 Ubicación y Datos Clave")
            tipo_negocio = st.selectbox(
                "Tipo de operación",
                ["Venta", "Arriendo Mensual", "Arriendo Amoblado / Temporal", "Cesión de Derechos / Proyecto"]
            )
            direccion = st.text_input("Dirección / Zona", placeholder="Ej: Calle 79 sur #58-66, Envigado")
            tipo_propiedad = st.selectbox(
                "Tipo de propiedad",
                ["Apartamento", "Casa", "Casa Campestre", "Penthouse", "Oficina", "Local Comercial", "Lote / Terreno"]
            )
            precio = st.text_input("Precio de oferta", placeholder="Ej: $267,000,000 COP o $2,500,000 COP/mes")
            
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
            - Tipo de operación: {tipo_negocio}
            - Tipo de propiedad: {tipo_propiedad}
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

            Luego de escribir esa marca, presenta inmediatamente las opciones adaptadas específicamente para la operación de {tipo_negocio}:
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
                        
                        MARCA = "===RESULTADO_FINAL==="
                        if MARCA in texto_bruto:
                            texto_limpio = texto_bruto.split(MARCA)[-1].strip()
                        else:
                            texto_limpio = texto_bruto.strip()

                        st.success("¡Anuncio generado exitosamente!")
                        st.subheader("📄 Resultado Generado")
                        st.code(texto_limpio, language="markdown")
                        
                        # ACTUALIZAR CONTADOR DE GENERACIONES EN SUPABASE
                        nuevas_generaciones = generaciones_usadas + 1
                        try:
                            supabase.table("usuarios").update({"generaciones": nuevas_generaciones}).eq("id", user["id"]).execute()
                            st.session_state["usuario"]["generaciones"] = nuevas_generaciones
                        except Exception as update_err:
                            st.warning(f"Nota: No se pudo actualizar el contador: {update_err}")

                        exito = True
                        break
                    except Exception:
                        continue
            
            if not exito:
                st.error("❌ No se pudo conectar con los servidores de Google. Inténtalo de nuevo.")
