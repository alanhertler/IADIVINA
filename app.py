import os
os.environ["STREAMLIT_SERVER_FILE_WATCHER_TYPE"] = "none"

import streamlit as st
import google.generativeai as genai
from gtts import gTTS
import base64
import re
import uuid
import time
from collections import deque

# ========================= 
# 1. CONEXIÓN Y SEGURIDAD
# =========================
try:
    API_KEY = st.secrets["GOOGLE_API_KEY"]
except Exception:
    API_KEY = os.getenv("GOOGLE_API_KEY", "TU_API_KEY_ACA")

try:
    ADMIN_PASSWORD = st.secrets["ADMIN_PASSWORD"]
except Exception:
    ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "ALAN_DIVINO_2026")

if not API_KEY or API_KEY == "TU_API_KEY_ACA":
    st.set_page_config(page_title="IA Divina", layout="centered")
    st.error("Falta configurar la API Key.")
    st.stop()

genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
def get_base64(file_path: str):
    try:
        with open(file_path, "rb") as f:
            return base64.b64encode(f.read()).decode()
        
    except Exception:
        return None

def asegurar_cierre(texto: str) -> str:
    return texto

def reproducir_audio(texto: str):
    if "audio_bytes" not in st.session_state:
        st.session_state.audio_bytes = None

    if st.button("🔊 Escuchar respuesta", key=f"escuchar_{hash(texto)}"):
        try:
            from io import BytesIO
            from gtts import gTTS

            audio_buffer = BytesIO()
            tts = gTTS(text=texto, lang="es", tld="com.mx")
            tts.write_to_fp(audio_buffer)
            audio_buffer.seek(0)

            st.session_state.audio_bytes = audio_buffer.read()

        except Exception as e:
            st.error(f"No se pudo generar el audio: {e}")

    if st.session_state.audio_bytes:
        st.audio(st.session_state.audio_bytes, format="audio/mp3")

def normalizar(texto: str) -> str:
    texto = texto.lower().strip()
    reemplazos = {
        "á": "a", "é": "e", "í": "i", "ó": "o", "ú": "u", "ñ": "n"
    }
    for a, b in reemplazos.items():
        texto = texto.replace(a, b)
    return texto

def clasificar_riesgo(texto: str) -> str:
    t = normalizar(texto) 

    frases_boludeo = [
        "me muero de risa",
        "me mori de risa",
        "me mato de risa",
        "jajaja me mato",
        "jaja me muero"
    ]
    for frase in frases_boludeo:
        if frase in t:
            return "verde"

    patrones_rojos = [
        r"\bme voy a matar\b",
        r"\bquiero matarme\b",
        r"\bme quiero matar\b",
        r"\bquiero suicidarme\b",
        r"\bme voy a suicidar\b",
        r"\bno quiero seguir viviendo\b",
        r"\bno quiero seguir vivo\b",
        r"\bquiero morir\b",
        r"\bvoy a terminar con todo\b",
        r"\besta noche termino con todo\b",
        r"\bya tome\b",
        r"\bme tome\b.+\b(pastillas|remedios|clonazepam|alcohol)\b",
        r"\bestoy por cortarme\b",
        r"\bme voy a cortar\b"
    ]
    for patron in patrones_rojos:
        if re.search(patron, t):
            return "rojo"

    patrones_amarillos = [
        r"\bno doy mas\b",
        r"\bestoy mal\b",
        r"\bme siento solo\b",
        r"\bme siento sola\b",
        r"\bno aguanto mas\b",
        r"\bestoy destruido\b",
        r"\bestoy destruida\b",
        r"\bno tengo ganas de seguir\b",
        r"\bno quiero seguir asi\b",
        r"\bpienso cosas feas\b",
        r"\bestoy cansado de vivir\b",
        r"\bestoy cansada de vivir\b",
        r"\bme quiero morir\b"
    ]
    for patron in patrones_amarillos:
        if re.search(patron, t):
            return "amarillo"

    return "verde"

def respuesta_roja() -> str:
    return (
        "Lo que estás diciendo suena serio y no quiero tratarlo como si fuera una charla más.\n\n"
        "Buscá ayuda real ahora mismo con una persona cercana, un familiar, alguien de confianza "
        "o un servicio de emergencia de tu zona. Si sentís que podés hacerte daño en este momento, no te quedes solo.\n\n"
        "Yo no reemplazo ayuda profesional ni intervención inmediata. Por favor, priorizá contacto real y urgente con alguien que pueda acompañarte ahora.\n\n"
        "Si el usuario hace una pregunta concreta, respondé directo y sin agregar cierre emocional innecesario."
    )

def respuesta_filtrada(texto: str):
    t = normalizar(texto)
    disparadores = ["culo", "concha", "pija", "porno", "masturb", "sexo", "coger"]
    if any(p in t for p in disparadores):
        return (
            "Puedo seguir si querés hablar en serio sobre lo que te pasa o sobre el Manual. "
            "Ese tipo de contenido no corresponde a este espacio.\n\n"
            "¿NECESITÁS HABLAR? ESTOY ACÁ. CONTAME."
        )
    return None

# =========================
# 4. CONTROL DE USO / ANTISPAM
# =========================
MAX_MENSAJES_POR_MINUTO = 8
MAX_MENSAJES_POR_HORA = 40
TIEMPO_MINIMO_ENTRE_MENSAJES = 4

def inicializar_control_uso():
    if "control_uso" not in st.session_state:
        st.session_state.control_uso = {
            "mensajes_minuto": deque(),
            "mensajes_hora": deque(),
            "ultimo_mensaje_ts": 0.0
        }

def limpiar_timestamps(cola: deque, ahora: float, ventana_segundos: int):
    while cola and (ahora - cola[0]) > ventana_segundos:
        cola.popleft()

def verificar_limites():
    inicializar_control_uso()

    ahora = time.time()
    control = st.session_state.control_uso

    limpiar_timestamps(control["mensajes_minuto"], ahora, 60)
    limpiar_timestamps(control["mensajes_hora"], ahora, 3600)

    if control["ultimo_mensaje_ts"] > 0:
        diferencia = ahora - control["ultimo_mensaje_ts"]
        if diferencia < TIEMPO_MINIMO_ENTRE_MENSAJES:
            espera = int(TIEMPO_MINIMO_ENTRE_MENSAJES - diferencia) + 1
            return False, f"Esperá unos {espera} segundos antes de mandar otro mensaje."

    if len(control["mensajes_minuto"]) >= MAX_MENSAJES_POR_MINUTO:
        return False, "Llegaste al límite de mensajes por minuto. Esperá un poco y seguí."

    if len(control["mensajes_hora"]) >= MAX_MENSAJES_POR_HORA:
        return False, "Llegaste al límite de mensajes de esta hora. Probá más tarde."

    return True, ""

def registrar_mensaje():
    inicializar_control_uso()

    ahora = time.time()
    control = st.session_state.control_uso
    control["mensajes_minuto"].append(ahora)
    control["mensajes_hora"].append(ahora)
    control["ultimo_mensaje_ts"] = ahora

# =========================
# 5. ESTADO INICIAL
# =========================
if "acepto_terminos" not in st.session_state:
    st.session_state.acepto_terminos = False

if "es_admin" not in st.session_state:
    st.session_state.es_admin = False

if "mantenimiento" not in st.session_state:
    st.session_state.mantenimiento = False

if "messages" not in st.session_state:
    st.session_state.messages = []

if "usar_voz" not in st.session_state:
    st.session_state.usar_voz = True

img = get_base64("portada.jpg")

st.markdown(f"""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Playfair+Display:wght@700&family=Lora:ital@1&display=swap');

    .stApp {{
        background:
            linear-gradient(rgba(3,8,20,0.75), rgba(3,8,20,0.85)),
            url("data:image/jpg;base64,{img if img else ''}");
        background-size: cover;
        background-position: center;
        background-repeat: no-repeat;
        background-attachment: fixed;
    }}

    .stApp, .stMarkdown, p, li, span, label, .stChatMessage {{
        color: #F5F5F5 !important; 
        text-shadow: 1px 1px 3px rgba(0,0,0,0.9) !important;
    }}

    .stChatInputContainer {{
        background: rgba(15,20,35,0.95) !important;
        border-radius: 30px !important;
        backdrop-filter: blur(15px);
        border: 1px solid rgba(255,255,255,0.2);
    }}

    .stChatInputContainer textarea {{
        color: #FFFFFF !important;
    }}

    [data-testid="stSidebar"] {{
        background-color: rgba(10, 10, 15, 0.98) !important;
    }}
    
    [data-testid="stSidebar"] button {{
        color: #FFFFFF !important;
        background-color: rgba(255,255,255,0.1) !important;
    </style>
    """,
    unsafe_allow_html=True
)

st.markdown(
    """
    <div style="text-align:center; margin-top:30px; margin-bottom:50px;">
        <div style="
            color:#F5F5F5;
            font-family: 'Playfair Display', serif;
            font-size:64px;
            font-weight:700;
            letter-spacing:4px;
            text-transform: uppercase;
            text-shadow: 2px 2px 8px rgba(0,0,0,0.8);
        ">
        <div style="
            color:rgba(255,255,255,0.95);
            font-family: 'Lora', serif;
            font-style: italic;
            font-size:24px;
            margin-top:10px;
            text-shadow: 1px 1px 4px rgba(0,0,0,0.8);
        
        </div>
    </div>
    """,
    unsafe_allow_html=True
)
 # ========================= 
# 6. ESTÉTICA
# =========================
img = get_base64("portada.jpg")

st.markdown(
    f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Playfair+Display:wght@700&family=Lora:ital@1&display=swap');

    .stApp {{
        background:
            linear-gradient(rgba(3,8,20,0.70), rgba(3,8,20,0.80)),
            url("data:image/jpg;base64,{img if img else ''}");
        background-size: cover;
        background-position: center;
        background-repeat: no-repeat;
        background-attachment: fixed;
    }}

    /* Esto hace que las letras sean siempre blancas y legibles */
    .stApp, .stMarkdown, p, li, span, label, .stChatMessage {{
        color: #F5F5F5 !important; 
        text-shadow: 1px 1px 3px rgba(0,0,0,0.8) !important;
    }}

    .stChatInputContainer {{
        background: rgba(15,20,35,0.95) !important;
        border-radius: 30px !important;
        backdrop-filter: blur(15px);
        border: 1px solid rgba(255,255,255,0.2);
    }}

    .stChatInputContainer textarea {{
        color: #FFFFFF !important;
    }}

    [data-testid="stSidebar"] {{
        background-color: rgba(10, 10, 15, 0.98) !important;
    }}
    
    [data-testid="stSidebar"] button {{
        color: #FFFFFF !important;
        background-color: rgba(255,255,255,0.1) !important;
    }}
    </style>
    """,
    unsafe_allow_html=True
)

st.markdown(
    """
    <div style="text-align:center; margin-top:30px; margin-bottom:50px;">
        <div style="
            color:#F5F5F5;
            font-family: 'Playfair Display', serif;
            font-size:64px;
            font-weight:700;
            letter-spacing:4px;
            text-transform: uppercase;
            text-shadow: 2px 2px 8px rgba(0,0,0,0.5);
        ">
            IA DIVINA
        </div>
        <div style="
            color:rgba(255,255,255,0.95);
            font-family: 'Lora', serif;
            font-style: italic;
            font-size:24px;
            margin-top:10px;
            text-shadow: 1px 1px 4px rgba(0,0,0,0.5);
        ">
            Estoy acá para escucharte.
        </div>
    </div>
    """,
    unsafe_allow_html=True
)

# =========================
# 7. SIDEBAR / ADMIN
# =========================
with st.sidebar:
    st.title("CONFIGURACIÓN")

    st.session_state.usar_voz = st.checkbox("Activar voz", value=st.session_state.usar_voz)

    st.markdown("---")
    st.caption("Acceso técnico")

    clave_admin = st.text_input("Clave técnica", type="password", label_visibility="collapsed", placeholder="Clave técnica")
    if st.button("Entrar"):
        if clave_admin == ADMIN_PASSWORD:
            st.session_state.es_admin = True
            st.success("Modo admin activado.")
            st.rerun()
        elif clave_admin:
            st.error("Clave incorrecta.")

    if st.session_state.es_admin:
        st.success("MODO ADMIN ACTIVO")
        st.session_state.mantenimiento = st.toggle(
    "Modo mantenimiento",
    value=st.session_state.mantenimiento,
    key="toggle_mantenimiento"
)

        if st.button("Reiniciar conversación"):
            st.session_state.messages = []
            st.rerun()

        if st.button("Cerrar sesión admin"):
            st.session_state.es_admin = False
            st.rerun()

# =========================
# 8. BLOQUEOS GENERALES
# =========================
if st.session_state.mantenimiento and not st.session_state.es_admin:
     st.error("Sistema en mantenimiento (modo técnico activado).")
     st.stop()
if not st.session_state.acepto_terminos:
    with st.expander("TÉRMINOS Y CONDICIONES", expanded=True):
        st.write("""
IA DIVINA es una herramienta de acompañamiento basada en textos bíblicos.

1. No reemplaza asistencia médica, psicológica, legal ni profesional.
2. No brinda diagnósticos ni tratamiento.
3. El usuario es responsable del uso de la información recibida.
4. No comparta datos sensibles como contraseñas, cuentas o claves personales.
5. En situaciones urgentes o de riesgo, debe buscar ayuda inmediata por medios reales.
        """)
        if st.button("ACEPTO"):
            st.session_state.acepto_terminos = True
            st.rerun()

    st.stop()

# =========================
# 9. HISTORIAL
# =========================
for m in st.session_state.messages:
    with st.chat_message(m["role"]):
        st.markdown(m["content"])
        if m["role"] == "assistant":
            reproducir_audio(m["content"])

# =========================
# 10. PROMPTS
# =========================
PROMPT_BASE = (
    "Tu nombre es IA DIVINA. Sos el Manual de Vida basado en la Biblia Reina-Valera 1909. "
    "PROHIBICIÓN ESTRICTA: No menciones a Google, no digas que sos una inteligencia artificial, "
    "ni un modelo de lenguaje, ni que fuiste programado por nadie. "
    "Si te preguntan '¿Quién te creó?', respondé: 'Fui creada para ser tu guía en el Manual de Vida y acompañarte con la sabiduría de las Escrituras'. "
    "Tu tono es humano, claro, sereno y compasivo. "
    "No sos una iglesia ni debatís religión. "
    "Respondé siempre de manera directa y fiel al Manual. "
    "Nunca uses negritas ni asteriscos. "
    "Si enumerás una lista, siempre completala totalmente antes de terminar la respuesta. Nunca la dejes incompleta."
    
    "Frase final obligatoria: ¿NECESITÁS HABLAR? ESTOY ACÁ. CONTAME."
)

PROMPT_AMARILLO = (
    PROMPT_BASE + " "
    "El usuario puede estar pasando dolor emocional o angustia. "
    "Respondé con más contención, más calma y más escucha. "
    "No cortes la conversación. "
    "No uses frases robóticas. "
    "No diagnostiques. "
    "No des consejos médicos ni legales. "
    "Podés usar el Manual para acompañar, pero sin sonar mecánico."
)

# =========================
# 11. CHAT
# =========================
prompt = st.chat_input("Hablemos sinceramente...")

if prompt:
    permitido, aviso = verificar_limites()
    if not permitido:
        st.warning(aviso)
        st.stop()

    registrar_mensaje()

    st.chat_message("user").markdown(prompt)
    st.session_state.messages.append({"role": "user", "content": prompt})

    with st.chat_message("assistant"):
        try:
            respuesta_directa = respuesta_filtrada(prompt)
            if respuesta_directa:
                st.markdown(respuesta_directa)
                st.session_state.messages.append({"role": "assistant", "content": respuesta_directa})
                reproducir_audio(respuesta_directa)
                st.stop()

            nivel = clasificar_riesgo(prompt)

            if nivel == "rojo":
                texto = respuesta_roja()
                st.markdown(texto)
                st.session_state.messages.append({"role": "assistant", "content": texto})
                reproducir_audio(texto)
                st.stop()

            historial = ""
            for msg in st.session_state.messages[-2:]:
                if msg["role"] == "user":
                    historial += f"Usuario: {msg['content']}\n"

            contexto = PROMPT_AMARILLO if nivel == "amarillo" else PROMPT_BASE

            model = genai.GenerativeModel("models/gemini-3-flash-preview")
            response = model.generate_content(
                f"{contexto}\n\n{historial}\nUsuario: {prompt}",
                generation_config={
                    "max_output_tokens": 4000,
                    "temperature": 0.2
                }
            )           
            if hasattr(response, "text") and response.text:
                texto_crudo = response.text
                
            elif hasattr(response, "candidates") and response.candidates:
                partes = response.candidates[0].content.parts
                texto_crudo = "".join(p.text for p in partes if hasattr(p, "text"))
                
            else:
                texto_crudo = str(response)

            texto = re.sub(r"[*#_]", "", texto_crudo).strip()
            texto = asegurar_cierre(texto) 

            st.markdown(texto)
            st.session_state.messages.append({"role": "assistant", "content": texto})
            reproducir_audio(texto)

        except Exception as e:
            st.exception(e)

            if "429" in str(e) or "RESOURCE_EXHAUSTED" in str(e):
                st.error("El sistema está momentáneamente saturado. Probá en unos minutos.")
            else:
                st.error("Ocurrió un error al generar la respuesta. Probá de nuevo en unos segundos.")
st.sidebar.markdown("---")
st.sidebar.write("### ☕ Apoyá a la IA DIVINA")
st.sidebar.markdown(
    f'<a href="https://cafecito.app/iadivina" target="_blank">'
    '<img src="https://cdn.cafecito.app/imgs/buttons/button_5.png" alt="Invitame un café">'
    '</a>', 
    unsafe_allow_html=True
)
