import os
os.environ["STREAMLIT_SERVER_FILE_WATCHER_TYPE"] = "none"

import streamlit as st
import google.generativeai as genai
from gtts import gTTS
import base64
import re
import time
from collections import deque


# =========================
# 1. CONFIGURACIÓN INICIAL
# =========================
try:
    API_KEY = st.secrets["GOOGLE_API_KEY"]
except Exception:
    API_KEY = os.getenv("GOOGLE_API_KEY", "TU_API_KEY_ACA")

try:
    ADMIN_PASSWORD = st.secrets["ADMIN_PASSWORD"]
except Exception:
    ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "NOmerobesLAPLATA10K")

st.set_page_config(page_title="IA DIVINA", layout="centered")

if not API_KEY or API_KEY == "TU_API_KEY_ACA":
    st.error("Falta configurar la API Key.")
    st.stop()

genai.configure(api_key=API_KEY)


# =========================
# 2. FUNCIONES AUXILIARES
# =========================
def get_base64(file_path: str):
    try:
        with open(file_path, "rb") as f:
            return base64.b64encode(f.read()).decode()
    except Exception:
        return None


def asegurar_cierre(texto: str) -> str:
    return texto.strip()


def normalizar(texto: str) -> str:
    texto = texto.lower().strip()
    reemplazos = {
        "á": "a",
        "é": "e",
        "í": "i",
        "ó": "o",
        "ú": "u",
        "ñ": "n",
    }
    for a, b in reemplazos.items():
        texto = texto.replace(a, b)
    return texto


def reproducir_audio(texto: str):
    if not st.session_state.get("usar_voz", True):
        return

    if "audio_bytes" not in st.session_state:
        st.session_state.audio_bytes = None

    if st.button("🔊 Escuchar respuesta", key=f"escuchar_{hash(texto)}"):
        try:
            from io import BytesIO
            audio_buffer = BytesIO()
            tts = gTTS(text=texto, lang="es", tld="com.mx")
            tts.write_to_fp(audio_buffer)
            audio_buffer.seek(0)
            st.session_state.audio_bytes = audio_buffer.read()
        except Exception as e:
            st.error(f"No se pudo generar el audio: {e}")

    if st.session_state.audio_bytes:
        st.audio(st.session_state.audio_bytes, format="audio/mp3")


# =========================
# 2.1 FUNCIONES VISUALES NUEVAS
# =========================
def construir_historial(messages, limite=15):
    historial = ""
    for msg in messages[-limite:]:
        if msg["role"] == "user":
            historial += f"Usuario: {msg['content']}\n"
        elif msg["role"] == "assistant":
            historial += f"Asistente: {msg['content']}\n"
    return historial.strip()


def stream_text(texto: str, delay: float = 0.012):
    palabras = texto.split()
    for palabra in palabras:
        yield palabra + " "
        time.sleep(delay)


def mostrar_respuesta_suave(texto: str, delay: float = 0.012) -> str:
    resultado = st.write_stream(stream_text(texto, delay=delay))
    if isinstance(resultado, str):
        return resultado
    return texto


# =========================
# 3. CLASIFICACIÓN DE RIESGO
# =========================
def clasificar_riesgo(texto: str) -> str:
    t = normalizar(texto)

    frases_boludeo = [
        "me muero de risa",
        "me mori de risa",
        "me mato de risa",
        "jajaja me mato",
        "jaja me muero",
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
        r"\bvoy a terminar con todo\b",
        r"\ble mataron a\b",
        r"\bse murio mi amiga\b",
        r"\bse murio mi amigo\b",
        r"\bmataron a mi\b",
        r"\bperdi a mi\b",
        r"\besta noche termino con todo\b",
        r"\bya tome pastillas\b",
        r"\bya tome remedios\b",
        r"\bya tome clonazepam\b",
        r"\bya tome alcohol\b",
        r"\bme tome\b.+\b(pastillas|remedios|clonazepam|alcohol)\b",
        r"\bestoy por cortarme\b",
        r"\bme voy a cortar\b",
    ]
    for patron in patrones_rojos:
        if re.search(patron, t):
            return "rojo"

    patrones_abuso = [
        r"\bmi papa me toco\b",
        r"\bmi mama me toco\b",
        r"\bmi padrastro me toco\b",
        r"\bmi tio me toco\b",
        r"\bmi abuelo me toco\b",
        r"\bmi hermano me toco\b",
        r"\bel pastor me toco\b",
        r"\bme toco entre las piernas\b",
        r"\bme tocaron entre las piernas\b",
        r"\bme tocaron\b.+\bpiernas\b",
        r"\bme manosearon\b",
        r"\bme tocaron los senos\b",
        r"\bme tocaron las tetas\b",
        r"\bme tocaron la cola\b",
        r"\bme tocaron el culo\b",
        r"\bme tocaron la vagina\b",
        r"\babusaron de mi\b",
        r"\bme violaron\b",
        r"\bme hicieron cosas\b",
        r"\bme obligaron\b",
        r"\bme acosaron\b",
    ]
    for patron in patrones_abuso:
        if re.search(patron, t):
            return "rojo_abuso"

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
        r"\bme quiero morir\b",
        r"\bquiero morir\b",
    ]
    for patron in patrones_amarillos:
        if re.search(patron, t):
            return "amarillo"

    return "verde"


# =========================
# 4. RESPUESTAS FIJAS
# =========================
def respuesta_roja() -> str:
    return (
        "Lo que estás diciendo suena serio y no quiero tratarlo como si fuera una charla más.\n\n"
        "Buscá ayuda real ahora mismo con una persona cercana, un familiar, alguien de confianza "
        "o un servicio de emergencia de tu zona. Si sentís que podés hacerte daño en este momento, no te quedes solo.\n\n"
        "Si estás en Argentina, podés llamar gratis al 135 (CABA y GBA) o al (011) 5275-1135 desde todo el país. "
        "Hay personas reales del otro lado para escucharte ahora mismo.\n\n"
        "Yo no reemplazo ayuda profesional ni intervención inmediata. Por favor, priorizá contacto real y urgente con alguien que pueda acompañarte ahora.\n\n"
        "¿NECESITÁS HABLAR? ESTOY ACÁ. CONTAME."
    )


def respuesta_abuso() -> str:
    return (
        "Lo que estás diciendo es muy serio. No es tu culpa.\n\n"
        "Si estás en peligro o esto puede volver a pasar, llamá ahora mismo al 911.\n\n"
        "También podés comunicarte en Argentina con el 137 o el 144. "
        "Hay personas que pueden ayudarte ahora mismo.\n\n"
        "Buscá un lugar seguro y alejate de quien te hizo daño. "
        "Contactá a alguien de confianza que pueda acompañarte.\n\n"
        "No tenés que pasar esto sola/o.\n\n"
        "Dios está cerca de los que están heridos. Salmos 34:18.\n\n"
        "¿NECESITÁS HABLAR? ESTOY ACÁ. CONTAME."
    )


def respuesta_filtrada(texto: str):
    t = normalizar(texto)
    disparadores = ["concha", "pija", "porno", "masturb", "sexo", "coger"]
    if any(p in t for p in disparadores):
        return (
            "Puedo seguir si querés hablar en serio sobre lo que te pasa o sobre el Manual. "
            "Ese tipo de contenido no corresponde a este espacio.\n\n"
            "¿NECESITÁS HABLAR? ESTOY ACÁ. CONTAME."
        )
    return None


# =========================
# 5. CONTROL DE USO
# =========================
MAX_MENSAJES_POR_MINUTO = 8
MAX_MENSAJES_POR_HORA = 40
TIEMPO_MINIMO_ENTRE_MENSAJES = 4


def inicializar_control_uso():
    if "control_uso" not in st.session_state:
        st.session_state.control_uso = {
            "mensajes_minuto": deque(),
            "mensajes_hora": deque(),
            "ultimo_mensaje_ts": 0.0,
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
# 6. ESTADO INICIAL
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


# =========================
# 7. ESTILO
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

    .stApp, .stMarkdown, p, li, span, label, .stChatMessage {{
        color: #F5F5F5 !important;
        text-shadow: 1px 1px 3px rgba(0,0,0,1) !important;
        font-size: 18px !important;
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

    .respuesta-cargando {{
        opacity: 0.92;
        font-style: italic;
        padding-top: 4px;
    }}
    </style>
    """,
    unsafe_allow_html=True,
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
            IA DIVINA
        </div>
        <div style="width: 60px; height: 1px; background-color: rgba(255,255,255,0.3); margin: 20px auto;"></div>
        <div style="
            color:rgba(255,255,255,0.95);
            font-family: 'Lora', serif;
            font-style: italic;
            font-size:24px;
            margin-top:10px;
            text-shadow: 1px 1px 4px rgba(0,0,0,0.8);
        ">
            Estoy acá para escucharte.
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)


# =========================
# 8. SIDEBAR / ADMIN
# =========================
with st.sidebar:
    st.title("CONFIGURACIÓN")

    st.session_state.usar_voz = st.checkbox("Activar voz", value=st.session_state.usar_voz)

    st.markdown("---")
    st.caption("Acceso técnico")

    clave_admin = st.text_input(
        "Clave técnica",
        type="password",
        label_visibility="collapsed",
        placeholder="Clave técnica",
    )

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
            key="toggle_mantenimiento",
        )

        if st.button("Reiniciar conversación"):
            st.session_state.messages = []
            st.rerun()

        if st.button("Cerrar sesión admin"):
            st.session_state.es_admin = False
            st.rerun()


# =========================
# 9. BLOQUEOS GENERALES
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
# 10. HISTORIAL
# =========================
for m in st.session_state.messages:
    with st.chat_message(m["role"]):
        st.markdown(m["content"])
        if m["role"] == "assistant":
            reproducir_audio(m["content"])


# =========================
# 11. PROMPTS
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

    # 🔥 ANTI RECITATION
    "IMPORTANTE: Si el usuario pide textos bíblicos muy conocidos o extensos "
    "(como los Diez Mandamientos), NO los recites completos. "
    "En su lugar, explicalos o resumilos con palabras simples. "

    "Podés incluir citas breves, pero evitá bloques largos completos. "

    # 🔥 FLUIDEZ
    "Antes de citar un versículo, introducí brevemente el tema. "
    "Luego el versículo, y después una explicación clara. "

    "Usá párrafos cortos. Evitá bloques largos. "

    # 🔥 FORMATO
    "Siempre que cites, usá formato en palabras: "
    "Éxodo capitulo. 20 versiculo. 3 — No tendrás dioses ajenos delante de mí. "

    "No uses dos puntos (:). "
    "No inventes citas. "

    # 🔥 LISTAS
    "Si enumerás, completá siempre la lista. "

    # 🔥 NATURALIDAD
    "No repitas cierres. Variá el lenguaje."
)

PROMPT_AMARILLO = (
    PROMPT_BASE + " "
    "El usuario puede estar pasando dolor emocional. "
    "Respondé con más contención, calma y cercanía. "
)


# =========================
# 🔐 FUNCIÓN SEGURA (NUEVA)
# =========================
def extraer_texto_seguro(response):
    try:
        if response is None:
            return None, "Respuesta vacía", None

        candidates = getattr(response, "candidates", None)
        if not candidates:
            return None, "Sin candidates", None

        candidate = candidates[0]
        finish_reason = getattr(candidate, "finish_reason", None)
        finish_reason_str = str(finish_reason) if finish_reason else ""

        content = getattr(candidate, "content", None)
        parts = getattr(content, "parts", None) if content else None

        textos = []

        if parts:
            for part in parts:
                texto = getattr(part, "text", None)
                if texto:
                    textos.append(str(texto).strip())

        if textos:
            return "\n\n".join(textos), None, finish_reason_str

        return None, "Sin texto válido", finish_reason_str

    except Exception as e:
        return None, f"Error: {e}", None


# =========================
# 12. CHAT (PARTE CORREGIDA)
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
        respuesta_placeholder = st.empty()

        try:
            nivel = clasificar_riesgo(prompt)

            if nivel == "rojo":
                texto = respuesta_roja()
                respuesta_placeholder.empty()
                texto_final = mostrar_respuesta_suave(texto)
                st.session_state.messages.append({"role": "assistant", "content": texto_final})
                reproducir_audio(texto_final)
                st.stop()

            elif nivel == "rojo_abuso":
                texto = respuesta_abuso()
                respuesta_placeholder.empty()
                texto_final = mostrar_respuesta_suave(texto)
                st.session_state.messages.append({"role": "assistant", "content": texto_final})
                reproducir_audio(texto_final)
                st.stop()

            respuesta_directa = respuesta_filtrada(prompt)
            if respuesta_directa:
                respuesta_placeholder.empty()
                texto_final = mostrar_respuesta_suave(respuesta_directa)
                st.session_state.messages.append({"role": "assistant", "content": texto_final})
                reproducir_audio(texto_final)
                st.stop()

            with respuesta_placeholder.container():
                with st.spinner("Buscando respuesta en el Manual..."):

                    historial = construir_historial(st.session_state.messages, limite=15)
                    contexto = PROMPT_AMARILLO if nivel == "amarillo" else PROMPT_BASE

                    model = genai.GenerativeModel("models/gemini-3-flash-preview")

                    response = model.generate_content(
                        f"{contexto}\n\n{historial}\nUsuario: {prompt}",
                        generation_config={
                            "max_output_tokens": 4000,
                            "temperature": 0.3,
                        },
                    )

                    texto_extraido, error_detalle, finish_reason = extraer_texto_seguro(response)

                    if not texto_extraido:
                        fr = (finish_reason or "").upper()

                        if "RECITATION" in fr or fr == "4":
                            texto_extraido = (
                                "Ese contenido no lo puedo mostrar de forma literal completa, "
                                "pero sí puedo explicártelo:\n\n"
                                "Los Diez Mandamientos enseñan a honrar a Dios, respetar a los padres, "
                                "no matar, no cometer adulterio, no robar, no mentir y no codiciar lo ajeno. "
                                "Son una guía de vida para caminar en rectitud."
                            )
                        else:
                            texto_extraido = "No pude generar una respuesta válida en este momento."

                    texto = re.sub(r"[*#_]", "", texto_extraido).strip()
                    texto = asegurar_cierre(texto)

            respuesta_placeholder.empty()
            texto_final = mostrar_respuesta_suave(texto)

            st.session_state.messages.append({"role": "assistant", "content": texto_final})
            reproducir_audio(texto_final)

        except Exception as e:
            st.exception(e)
            st.error("Error en la generación de respuesta.")

# =========================
# 13. CAFECITO
# =========================
st.sidebar.markdown("---")
st.sidebar.write("### ☕ Apoyá a la IA DIVINA")
st.sidebar.markdown(
    '<a href="https://cafecito.app/iadivina" target="_blank">'
    '<img src="https://cdn.cafecito.app/imgs/buttons/button_5.png" alt="Invitame un café">'
    '</a>',
    unsafe_allow_html=True,
)
