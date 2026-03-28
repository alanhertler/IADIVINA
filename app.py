import os
os.environ["STREAMLIT_SERVER_FILE_WATCHER_TYPE"] = "none"

import json
import streamlit as st
import google.generativeai as genai
import base64
import re
import time
import io
import requests
from pathlib import Path
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

API_DISPONIBLE = bool(API_KEY and API_KEY != "TU_API_KEY_ACA")
if API_DISPONIBLE:
    genai.configure(api_key=API_KEY)


# =========================
# 1.1 MOTOR LOCAL BÍBLICO
# =========================
BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"

BIBLIA_FILE = DATA_DIR / "biblia_rv1909_demo.json"
RESPUESTAS_FILE = DATA_DIR / "respuestas.json"
TEMAS_FILE = DATA_DIR / "temas.json"

BIBLIA_DEMO = [
    {"libro": "Salmos", "capitulo": 34, "versiculo": 18,
     "texto": "Cercano está Jehová á los quebrantados de corazón; y salvará á los contritos de espíritu."},
    {"libro": "Salmos", "capitulo": 23, "versiculo": 1,
     "texto": "Jehová es mi pastor; nada me faltará."},
    {"libro": "Juan", "capitulo": 3, "versiculo": 16,
     "texto": "Porque de tal manera amó Dios al mundo, que ha dado á su Hijo unigénito, para que todo aquel que en él cree, no se pierda, mas tenga vida eterna."},
    {"libro": "Mateo", "capitulo": 11, "versiculo": 28,
     "texto": "Venid á mí todos los que estáis trabajados y cargados, que yo os haré descansar."},
    {"libro": "Filipenses", "capitulo": 4, "versiculo": 7,
     "texto": "Y la paz de Dios, que sobrepuja todo entendimiento, guardará vuestros corazones y vuestros entendimientos en Cristo Jesús."},
    {"libro": "Isaías", "capitulo": 41, "versiculo": 10,
     "texto": "No temas, porque yo soy contigo; no desmayes, porque yo soy tu Dios que te esfuerzo; siempre te ayudaré, siempre te sustentaré con la diestra de mi justicia."},
    {"libro": "Romanos", "capitulo": 8, "versiculo": 28,
     "texto": "Y sabemos que á los que á Dios aman, todas las cosas les ayudan á bien, es á saber, á los que conforme al propósito son llamados."},
    {"libro": "Exodo", "capitulo": 20, "versiculo": 3, "texto": "No tendrás dioses ajenos delante de mí."},
    {"libro": "Exodo", "capitulo": 20, "versiculo": 4,
     "texto": "No te harás imagen, ni ninguna semejanza de cosa que esté arriba en el cielo, ni abajo en la tierra, ni en las aguas debajo de la tierra."},
    {"libro": "Exodo", "capitulo": 20, "versiculo": 5,
     "texto": "No te inclinarás á ellas, ni las honrarás; porque yo soy Jehová tu Dios, fuerte, celoso."},
    {"libro": "Exodo", "capitulo": 20, "versiculo": 7,
     "texto": "No tomarás el nombre de Jehová tu Dios en vano; porque no dará por inocente Jehová al que tomare su nombre en vano."},
    {"libro": "Exodo", "capitulo": 20, "versiculo": 8,
     "texto": "Acordarte has del día del reposo, para santificarlo."},
    {"libro": "Exodo", "capitulo": 20, "versiculo": 12,
     "texto": "Honra á tu padre y á tu madre, porque tus días se alarguen en la tierra que Jehová tu Dios te da."},
    {"libro": "Exodo", "capitulo": 20, "versiculo": 13, "texto": "No matarás."},
    {"libro": "Exodo", "capitulo": 20, "versiculo": 14, "texto": "No adulterarás."},
    {"libro": "Exodo", "capitulo": 20, "versiculo": 15, "texto": "No hurtarás."},
    {"libro": "Exodo", "capitulo": 20, "versiculo": 16, "texto": "No hablarás contra tu prójimo falso testimonio."},
    {"libro": "Exodo", "capitulo": 20, "versiculo": 17,
     "texto": "No codiciarás la casa de tu prójimo, no codiciarás la mujer de tu prójimo, ni su siervo, ni su criada, ni su buey, ni su asno, ni cosa alguna de tu prójimo."},
]

RESPUESTAS_DEMO = {
    "saludo": "Estoy acá para escucharte. Si querés, podés contarme qué te pasa o pedirme un versículo por tema o referencia.",
    "ayuda": "Podés escribir cosas como: 'Juan 3:16', 'dame un versículo sobre paz', 'estoy triste', 'tengo miedo'.",
    "fallback": "No encontré una respuesta local exacta.",
    "consuelo_base": "Te comparto una palabra que puede traer consuelo:",
    "paz_base": "Te comparto una palabra sobre la paz:",
    "miedo_base": "Te comparto una palabra para el temor:",
    "fe_base": "Te comparto una palabra para fortalecer la fe:",
}

TEMAS_DEMO = {
    "consuelo": [
        {"libro": "Salmos", "capitulo": 34, "versiculo": 18},
        {"libro": "Mateo", "capitulo": 11, "versiculo": 28},
    ],
    "paz": [
        {"libro": "Filipenses", "capitulo": 4, "versiculo": 7},
        {"libro": "Salmos", "capitulo": 23, "versiculo": 1},
    ],
    "miedo": [{"libro": "Isaías", "capitulo": 41, "versiculo": 10}],
    "fe": [
        {"libro": "Juan", "capitulo": 3, "versiculo": 16},
        {"libro": "Romanos", "capitulo": 8, "versiculo": 28},
    ],
    "tristeza": [
        {"libro": "Salmos", "capitulo": 34, "versiculo": 18},
        {"libro": "Mateo", "capitulo": 11, "versiculo": 28},
    ],
    "ansiedad": [
        {"libro": "Filipenses", "capitulo": 4, "versiculo": 7},
        {"libro": "Isaías", "capitulo": 41, "versiculo": 10},
    ],
}


def guardar_json(ruta: Path, data):
    with open(ruta, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def cargar_json(ruta: Path):
    with open(ruta, "r", encoding="utf-8") as f:
        return json.load(f)


def asegurar_estructura_local():
    DATA_DIR.mkdir(exist_ok=True)
    if not BIBLIA_FILE.exists():
        guardar_json(BIBLIA_FILE, BIBLIA_DEMO)
    else:
        try:
            biblia_actual = cargar_json(BIBLIA_FILE)
            claves = {
                (str(x.get("libro", "")).lower(), x.get("capitulo"), x.get("versiculo"))
                for x in biblia_actual if isinstance(x, dict)
            }
            agregados = 0
            for item in BIBLIA_DEMO:
                clave = (str(item.get("libro", "")).lower(), item.get("capitulo"), item.get("versiculo"))
                if clave not in claves:
                    biblia_actual.append(item)
                    claves.add(clave)
                    agregados += 1
            if agregados:
                guardar_json(BIBLIA_FILE, biblia_actual)
        except Exception:
            guardar_json(BIBLIA_FILE, BIBLIA_DEMO)
    if not RESPUESTAS_FILE.exists():
        guardar_json(RESPUESTAS_FILE, RESPUESTAS_DEMO)
    if not TEMAS_FILE.exists():
        guardar_json(TEMAS_FILE, TEMAS_DEMO)
    else:
        try:
            temas_actuales = cargar_json(TEMAS_FILE)
            cambios = False
            alias_mandamientos = {
                "10 mandamientos": [{"libro": "Exodo", "capitulo": 20, "versiculo": i} for i in range(2, 18)],
                "diez mandamientos": [{"libro": "Exodo", "capitulo": 20, "versiculo": 2}],
                "mandamientos": [{"libro": "Exodo", "capitulo": 20, "versiculo": 2}],
                "madamientos": [{"libro": "Exodo", "capitulo": 20, "versiculo": 2}],
            }
            for clave, valor in alias_mandamientos.items():
                if clave not in temas_actuales:
                    temas_actuales[clave] = valor
                    cambios = True
            if cambios:
                guardar_json(TEMAS_FILE, temas_actuales)
        except Exception:
            guardar_json(TEMAS_FILE, TEMAS_DEMO)


def cargar_datos_locales():
    return cargar_json(BIBLIA_FILE), cargar_json(RESPUESTAS_FILE), cargar_json(TEMAS_FILE)


def normalizar_local(texto: str) -> str:
    texto = texto.lower().strip()
    for a, b in {"á":"a","é":"e","í":"i","ó":"o","ú":"u","ñ":"n"}.items():
        texto = texto.replace(a, b)
    return re.sub(r"\s+", " ", texto)


def extraer_referencia_local(consulta: str):
    match = re.match(r"^\s*([A-Za-zÁÉÍÓÚáéíóúÑñ]+)\s+(\d+)\s*:\s*(\d+)\s*$", consulta.strip())
    if not match:
        return None
    return {"libro": match.group(1), "capitulo": int(match.group(2)), "versiculo": int(match.group(3))}


def buscar_por_referencia_local(biblia, libro, capitulo, versiculo):
    libro_norm = normalizar_local(libro)
    for item in biblia:
        if normalizar_local(item["libro"]) == libro_norm and item["capitulo"] == capitulo and item["versiculo"] == versiculo:
            return item
    return None


def detectar_tema_local(consulta: str):
    t = normalizar_local(consulta)
    mapa = {
        "consuelo": ["consuelo","dolor","quebrantado","solo","sola","triste","tristeza","duelo"],
        "paz": ["paz","calma","tranquilidad","descanso"],
        "miedo": ["miedo","temor","asustado","asustada","desesperado","desesperada"],
        "fe": ["fe","creer","esperanza","confianza"],
        "ansiedad": ["ansiedad","ansioso","ansiosa","angustia","angustiado","angustiada"],
    }
    for tema, palabras in mapa.items():
        for palabra in palabras:
            if palabra in t:
                return tema
    return None


def buscar_versiculos_por_tema_local(biblia, temas, tema):
    return [v for ref in temas.get(tema, [])
            if (v := buscar_por_referencia_local(biblia, ref["libro"], ref["capitulo"], ref["versiculo"]))]


def formatear_versiculo_local(item):
    return f'{item["libro"]} {item["capitulo"]}:{item["versiculo"]} — {item["texto"]}'


def responder_local_si_aplica(consulta: str, biblia, respuestas, temas):
    consulta_norm = normalizar_local(consulta)
    if any(k in consulta_norm for k in ["10 mandamientos","diez mandamientos","mandamientos","madamientos"]):
        return """LOS DIEZ MANDAMIENTOS

Base bíblica: EXODO capitulo 20. versiculos 2 al 17
Versión: Reina-Valera 1909

EXODO capitulo 20. versiculo 2
Yo soy Jehová tu Dios, que te saqué de la tierra de Egipto, de casa de siervos

1. EXODO capitulo 20. versiculo 3
No tendrás dioses ajenos delante de mí

2. EXODO capitulo 20. versiculos 4 al 5
No te harás imagen, ni ninguna semejanza de cosa que esté arriba en el cielo, ni abajo en la tierra, ni en las aguas debajo de la tierra. No te inclinarás á ellas, ni las honrarás

3. EXODO capitulo 20. versiculo 7
No tomarás el nombre de Jehová tu Dios en vano

4. EXODO capitulo 20. versiculos 8 al 11
Acordarte has del día del reposo, para santificarlo

5. EXODO capitulo 20. versiculo 12
Honra á tu padre y á tu madre

6. EXODO capitulo 20. versiculo 13
No matarás

7. EXODO capitulo 20. versiculo 14
No adulterarás

8. EXODO capitulo 20. versiculo 15
No hurtarás

9. EXODO capitulo 20. versiculo 16
No hablarás contra tu prójimo falso testimonio

10. EXODO capitulo 20. versiculo 17
No codiciarás la casa de tu prójimo, no codiciarás la mujer de tu prójimo, ni su siervo, ni su criada, ni su buey, ni su asno, ni cosa alguna de tu prójimo"""

    if consulta_norm in ["hola","buenas","buen dia","buen día","buenas tardes","buenas noches"]:
        return respuestas["saludo"]
    if consulta_norm in ["ayuda","menu","menú","como funciona","cómo funciona"]:
        return respuestas["ayuda"]
    referencia = extraer_referencia_local(consulta)
    if referencia:
        encontrado = buscar_por_referencia_local(biblia, referencia["libro"], referencia["capitulo"], referencia["versiculo"])
        return formatear_versiculo_local(encontrado) if encontrado else "No encontré esa referencia en la base local actual."
    tema = detectar_tema_local(consulta)
    if tema:
        versiculos = buscar_versiculos_por_tema_local(biblia, temas, tema)
        if versiculos:
            encabezados = {"consuelo": respuestas.get("consuelo_base","Te comparto una palabra:"),
                           "paz": respuestas.get("paz_base","Te comparto una palabra:"),
                           "miedo": respuestas.get("miedo_base","Te comparto una palabra:"),
                           "fe": respuestas.get("fe_base","Te comparto una palabra:"),
                           "ansiedad": respuestas.get("consuelo_base","Te comparto una palabra:")}
            return "\n\n".join([encabezados.get(tema,"Te comparto una palabra:")] + [formatear_versiculo_local(v) for v in versiculos[:2]])
    return None


asegurar_estructura_local()


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
    for a, b in {"á":"a","é":"e","í":"i","ó":"o","ú":"u","ñ":"n"}.items():
        texto = texto.replace(a, b)
    return texto


# =========================
# 2.2 VOZ — Google Cloud TTS Neural2
# Voz masculina español latino — es-US-Neural2-B
# Usa la misma GOOGLE_API_KEY del proyecto Gemini
# Si falla, cae silenciosamente sin romper la app
# Alternativas masculinas:
#   es-US-Neural2-C (tono más suave)
#   es-ES-Neural2-B (español España)
# =========================
def _generar_audio_cloud_tts(texto: str):
    if not API_KEY or API_KEY == "TU_API_KEY_ACA":
        return None
    url = f"https://texttospeech.googleapis.com/v1/text:synthesize?key={st.secrets['GOOGLE_API_KEY']}"
    texto_audio = texto[:4500].replace("\n", ". ").strip()
    payload = {
        "input": {"text": texto_audio},
        "voice": {
            "languageCode": "es-US",
            "name": "es-US-Neural2-B",
            "ssmlGender": "MALE",
        },
        "audioConfig": {
            "audioEncoding": "MP3",
            "speakingRate": 1.0,
            "pitch": 0.0,
        }
    }
    try:
        resp = requests.post(url, json=payload, timeout=15)
        if resp.status_code == 200:
            audio_b64 = resp.json().get("audioContent", "")
            if audio_b64:
                return base64.b64decode(audio_b64)
        return None
    except Exception:
        return None


def reproducir_audio(texto: str):
    if not st.session_state.get("usar_voz", True):
        return
    boton_id = f"btn_audio_{abs(hash(texto[:80]))}"
    if st.button("🔊 Escuchar Manual", key=boton_id):
        try:
            audio_bytes = _generar_audio_cloud_tts(texto)
            if audio_bytes:
                st.audio(audio_bytes, format="audio/mp3")
            else:
                st.warning("La voz no está disponible en este momento.")
        except Exception as e:
            st.error(f"Error de sonido: {e}")


# =========================
# 2.1 FUNCIONES VISUALES
# =========================
def construir_historial(messages, limite=15):
    historial = ""
    for msg in messages[-limite:]:
        if msg["role"] == "user":
            historial += f"Usuario: {msg['content']}\n"
        elif msg["role"] == "assistant":
            historial += f"Asistente: {msg['content']}\n"
    return historial.strip()


def stream_text(texto: str, delay: float = 0.02):
    texto = texto.replace("\r\n", "\n")
    for parte in re.split(r"(\s+)", texto):
        yield parte
        time.sleep(delay)


def mostrar_respuesta_suave(texto: str, delay: float = 0.02) -> str:
    resultado = st.write_stream(stream_text(texto, delay=delay))
    return resultado if isinstance(resultado, str) else texto


# =========================
# 3. CLASIFICACIÓN DE RIESGO
# =========================
def clasificar_riesgo(texto: str) -> str:
    t = normalizar(texto)

    for frase in ["me muero de risa","me mori de risa","me mato de risa","jajaja me mato","jaja me muero","me parto de risa","me caigo de risa"]:
        if frase in t:
            return "verde"

    patrones_rojos = [
        r"\bme voy a matar\b",r"\bquiero matarme\b",r"\bme quiero matar\b",
        r"\bquiero suicidarme\b",r"\bme voy a suicidar\b",
        r"\bno quiero seguir viviendo\b",r"\bno quiero seguir vivo\b",
        r"\bvoy a terminar con todo\b",r"\besta noche termino con todo\b",
        r"\bya tome pastillas\b",r"\bya tome remedios\b",r"\bya tome clonazepam\b",r"\bya tome alcohol\b",
        r"\bme tome\b.+\b(pastillas|remedios|clonazepam|alcohol)\b",
        r"\bestoy por cortarme\b",r"\bme voy a cortar\b",
        r"\ble mataron a\b",r"\bse murio mi amiga\b",r"\bse murio mi amigo\b",r"\bmataron a mi\b",r"\bperdi a mi\b",
        r"\bme quiero borrar\b",r"\bya no quiero estar\b",r"\bquiero desaparecer\b",
        r"\bdesearía no haber nacido\b",r"\bdeseo no haber nacido\b",
        r"\bno deberia haber nacido\b",r"\bno debí nacer\b",
        r"\bnadie me va a extrañar\b",r"\bnadie me extrañaria\b",
        r"\btodos estarian mejor sin mi\b",r"\btodos estarian mejor sin mí\b",
        r"\bsoy una carga\b",r"\bsoy un estorbo\b",
        r"\bme voy a tirar\b",r"\bme voy a aventar\b",r"\bquiero saltar\b",
        r"\bpienso en hacerme dano\b",r"\bpienso en hacerme daño\b",
        r"\bvoy a hacerme dano\b",r"\bvoy a hacerme daño\b",
        r"\bme lastimé\b",r"\bme lastime\b",r"\bme hice dano\b",r"\bme hice daño\b",
    ]
    for patron in patrones_rojos:
        if re.search(patron, t):
            return "rojo"

    patrones_abuso = [
        r"\bmi papa me toco\b",r"\bmi mama me toco\b",r"\bmi padrastro me toco\b",
        r"\bmi tio me toco\b",r"\bmi abuelo me toco\b",r"\bmi hermano me toco\b",
        r"\bel pastor me toco\b",r"\bme toco entre las piernas\b",
        r"\bme tocaron entre las piernas\b",r"\bme tocaron\b.+\bpiernas\b",
        r"\bme manosearon\b",r"\bme tocaron los senos\b",r"\bme tocaron las tetas\b",
        r"\bme tocaron la cola\b",r"\bme tocaron el culo\b",r"\bme tocaron la vagina\b",
        r"\babusaron de mi\b",r"\bme violaron\b",r"\bme hicieron cosas\b",r"\bme obligaron\b",r"\bme acosaron\b",
        r"\bme hizo cosas raras\b",r"\bme toco de manera rara\b",r"\bme toco de forma rara\b",
        r"\bme dejo tocar\b",r"\bme obligo a tocarlo\b",r"\bme obligo a tocarla\b",
        r"\bme saco fotos\b",r"\bme grabo sin ropa\b",r"\bme mando fotos\b",
        r"\bme pidio fotos\b",r"\bme pidió fotos\b",r"\bme piden fotos\b",
        r"\bun adulto me\b.+\bfotos\b",r"\bme groomea\b",r"\bme está groomeando\b",
        r"\bun mayor me pide\b",r"\bun chico mayor me\b",
    ]
    for patron in patrones_abuso:
        if re.search(patron, t):
            return "rojo_abuso"

    patrones_amarillos = [
        r"\bno doy mas\b",r"\bestoy mal\b",r"\bme siento solo\b",r"\bme siento sola\b",
        r"\bno aguanto mas\b",r"\bestoy destruido\b",r"\bestoy destruida\b",
        r"\bno tengo ganas de seguir\b",r"\bno quiero seguir asi\b",r"\bpienso cosas feas\b",
        r"\bestoy cansado de vivir\b",r"\bestoy cansada de vivir\b",
        r"\bme quiero morir\b",r"\bquiero morir\b",
        r"\bno sirvo para nada\b",r"\bsoy un fracaso\b",
        r"\bnadie me entiende\b",r"\bnadie me quiere\b",
        r"\bme harté de todo\b",r"\bme harte de todo\b",r"\bme tiene harto\b",r"\bme tiene harta\b",
        r"\bestoy harto de vivir\b",r"\bestoy harta de vivir\b",
        r"\bme siento invisible\b",r"\bme siento roto\b",r"\bme siento rota\b",
        r"\bme siento vacio\b",r"\bme siento vacía\b",r"\bme siento vacío\b",
        r"\bno le importo a nadie\b",r"\bsoy una carga para todos\b",r"\btodo me sale mal\b",
        r"\bya no puedo más\b",r"\bya no puedo mas\b",r"\bestoy agotado\b",r"\bestoy agotada\b",
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
        "NECESITÁS HABLAR? ESTOY ACÁ. CONTAME."
    )


def respuesta_abuso() -> str:
    return (
        "Lo que estás diciendo es muy serio. No es tu culpa.\n\n"
        "Si estás en peligro o esto puede volver a pasar, llamá ahora mismo al 911.\n\n"
        "También podés comunicarte en Argentina con el 137 o el 144. "
        "Hay personas que pueden ayudarte ahora mismo.\n\n"
        "Buscá un lugar seguro y alejate de quien te hizo daño. "
        "Contactá a alguien de confianza que pueda acompañarte.\n\n"
        "No tenés que pasar esto sola o solo.\n\n"
        "Dios está cerca de los que están heridos. Salmos capitulo 34 versiculo 18.\n\n"
        "NECESITÁS HABLAR? ESTOY ACÁ. CONTAME."
    )


def respuesta_filtrada(texto: str):
    t = normalizar(texto)
    if any(p in t for p in ["concha","pija","porno","masturb","sexo","coger"]):
        return (
            "Puedo seguir si querés hablar en serio sobre lo que te pasa o sobre el Manual. "
            "Ese tipo de contenido no corresponde a este espacio.\n\n"
            "NECESITÁS HABLAR? ESTOY ACÁ. CONTAME."
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


def limpiar_timestamps(cola, ahora, ventana_segundos):
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
            return False, f"Esperá unos {int(TIEMPO_MINIMO_ENTRE_MENSAJES - diferencia) + 1} segundos antes de mandar otro mensaje."
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

st.markdown(f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Playfair+Display:wght@700&family=Lora:ital@1&display=swap');
    .stApp {{
        background: linear-gradient(rgba(3,8,20,0.70), rgba(3,8,20,0.80)), url("data:image/jpg;base64,{img if img else ''}");
        background-size: cover; background-position: center; background-repeat: no-repeat; background-attachment: fixed;
    }}
    .stApp, .stMarkdown, p, li, span, label, .stChatMessage {{
        color: #F5F5F5 !important; text-shadow: 1px 1px 3px rgba(0,0,0,1) !important;
        font-size: clamp(15px, 3.5vw, 18px) !important; line-height: 1.75 !important;
    }}
    [data-testid="stChatMessageContent"], [data-testid="stMarkdownContainer"],
    [data-testid="stChatMessageContent"] p, [data-testid="stChatMessageContent"] li,
    [data-testid="stChatMessageContent"] div {{
        font-size: clamp(15px, 3.8vw, 19px) !important; line-height: 1.75 !important;
    }}
    @media (max-width: 768px) {{
        .stApp, .stMarkdown, p, li, span, label, .stChatMessage,
        [data-testid="stChatMessageContent"], [data-testid="stMarkdownContainer"],
        [data-testid="stChatMessageContent"] p, [data-testid="stChatMessageContent"] li,
        [data-testid="stChatMessageContent"] div {{
            font-size: clamp(15px, 4vw, 17px) !important; line-height: 1.75 !important;
        }}
        .stChatInputContainer textarea {{ font-size: clamp(15px, 4vw, 17px) !important; }}
    }}
    .stChatInputContainer {{
        background: rgba(15,20,35,0.95) !important; border-radius: 30px !important;
        backdrop-filter: blur(15px); border: 1px solid rgba(255,255,255,0.2);
    }}
    .stChatInputContainer textarea {{ color: #FFFFFF !important; }}
    [data-testid="stSidebar"] {{ background-color: rgba(10, 10, 15, 0.98) !important; }}
    </style>
""", unsafe_allow_html=True)

st.markdown("""
    <style>
    @keyframes smokeReveal {
        0%   { opacity: 0; filter: blur(30px) brightness(0.3); transform: scale(1.08); }
        40%  { opacity: 0.6; filter: blur(12px) brightness(0.7); transform: scale(1.03); }
        100% { opacity: 1; filter: blur(0px) brightness(1); transform: scale(1); }
    }
    @keyframes fadeInSubtitle { 0% { opacity:0; transform:translateY(12px); } 100% { opacity:1; transform:translateY(0); } }
    @keyframes fadeInDivider { 0% { opacity:0; width:0px; } 100% { opacity:1; width:60px; } }
    .hero-title {
        color: #F5F5F5; font-family: 'Playfair Display', serif;
        font-size: clamp(44px, 10vw, 64px); font-weight: 700; letter-spacing: 4px;
        text-transform: uppercase; text-shadow: 2px 2px 12px rgba(0,0,0,0.9), 0 0 40px rgba(255,220,150,0.15);
        animation: smokeReveal 2.2s ease-out forwards; opacity: 0;
    }
    .hero-divider {
        height: 1px; background-color: rgba(255,255,255,0.3); margin: 20px auto;
        animation: fadeInDivider 0.8s ease-out 2.4s forwards; opacity: 0; width: 0px;
    }
    .hero-subtitle {
        color: rgba(255,255,255,0.95); font-family: 'Lora', serif; font-style: italic;
        font-size: clamp(18px, 5vw, 24px); text-shadow: 1px 1px 4px rgba(0,0,0,0.8);
        animation: fadeInSubtitle 1s ease-out 2.8s forwards; opacity: 0;
    }
    </style>
    <div style="text-align:center; margin-top:30px; margin-bottom:50px;">
        <div class="hero-title">IA DIVINA</div>
        <div class="hero-divider"></div>
        <div class="hero-subtitle">Estoy acá para escucharte.</div>
    </div>
""", unsafe_allow_html=True)


# =========================
# 8. SIDEBAR / ADMIN
# =========================
with st.sidebar:
    st.title("CONFIGURACIÓN")
    st.session_state.usar_voz = st.checkbox("Activar voz", value=st.session_state.usar_voz)
    st.markdown("---")
    st.caption("Acceso técnico")
    if API_DISPONIBLE:
        st.success("API IA conectada")
    else:
        st.warning("Sin API: funciona solo el motor local")
    st.caption(f"Base local: {BIBLIA_FILE.name}")
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
        st.session_state.mantenimiento = st.toggle("Modo mantenimiento", value=st.session_state.mantenimiento, key="toggle_mantenimiento")
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
    st.markdown("""
    <style>
    @keyframes slideDown { 0% { opacity:0; max-height:0px; transform:translateY(-10px); } 100% { opacity:1; max-height:600px; transform:translateY(0); } }
    @keyframes pingAppear { 0% { opacity:0; transform:scale(0.7); } 60% { opacity:1; transform:scale(1.08); } 80% { transform:scale(0.96); } 100% { opacity:1; transform:scale(1); } }
    .terminos-box {
        background: rgba(10,12,25,0.82); border: 1px solid rgba(255,255,255,0.15);
        border-radius: 14px; padding: 24px 28px; margin: 10px 0 24px 0;
        overflow: hidden; animation: slideDown 1.8s ease-out 3.6s forwards; opacity: 0; max-height: 0px;
    }
    .terminos-box p, .terminos-box li {
        font-family: 'EB Garamond', Georgia, serif !important; font-size: clamp(15px,3.8vw,18px) !important;
        line-height: 1.75 !important; color: #e8ddd0 !important; margin-bottom: 0.5em !important;
    }
    .terminos-titulo {
        font-family: 'Cinzel', serif !important; font-size: clamp(13px,3.5vw,15px) !important;
        letter-spacing: 3px !important; color: rgba(212,175,122,0.85) !important;
        margin-bottom: 16px !important; text-align: center !important;
    }
    .acepto-wrapper { text-align:center; animation: pingAppear 0.6s cubic-bezier(0.34,1.56,0.64,1) 5.6s forwards; opacity:0; margin-top:10px; }
    </style>
    <div class="terminos-box">
        <div class="terminos-titulo">TÉRMINOS Y CONDICIONES</div>
        <p>IA DIVINA es una herramienta de acompañamiento basada en textos bíblicos.</p>
        <ol>
            <li>No reemplaza asistencia médica, psicológica, legal ni profesional.</li>
            <li>No brinda diagnósticos ni tratamiento.</li>
            <li>El usuario es responsable del uso de la información recibida.</li>
            <li>No comparta datos sensibles como contraseñas, cuentas o claves personales.</li>
            <li>En situaciones urgentes o de riesgo, debe buscar ayuda inmediata por medios reales.</li>
        </ol>
    </div>
    <div class="acepto-wrapper" id="acepto-btn-hint"></div>
    """, unsafe_allow_html=True)
    if st.button("✦  ACEPTO  ✦", key="btn_acepto", use_container_width=False):
        st.session_state.acepto_terminos = True
        st.rerun()
    st.stop()


# =========================
# 10. HISTORIAL
# =========================
for m in st.session_state.messages:
    avatar = "✝️" if m["role"] == "assistant" else "❤️"
    with st.chat_message(m["role"], avatar=avatar):
        st.markdown(m["content"].replace("\n", "  \n"))
        if m["role"] == "assistant":
            reproducir_audio(m["content"])


# =========================
# 11. PROMPTS
# Para volver al modo ahorro: reemplazá PROMPT_BASE por PROMPT_BASE_AHORRO
# =========================
PROMPT_BASE = (
    "Tu nombre es IA DIVINA. Sos el Manual de Vida basado en la Biblia Reina-Valera 1909. "
    "PROHIBICIÓN ESTRICTA: No menciones a Google, no digas que sos una inteligencia artificial, "
    "ni un modelo de lenguaje, ni que fuiste programado por nadie. "
    "Si te preguntan quien te creó, respondé: "
    "Fui creada para ser tu guía en el Manual de Vida y acompañarte con la sabiduría de las Escrituras. "
    "TONO Y PERSONALIDAD: "
    "Sos una guía espiritual cercana, paciente y reconfortante. "
    "Hablás como alguien que escucha de verdad, no como un buscador de información. "
    "Tu lenguaje es humano, cálido, sereno y compasivo. "
    "No sos una iglesia ni debatís religión. "
    "Respondé siempre de manera directa y fiel al Manual. "
    "EMPATÍA ACTIVA — MUY IMPORTANTE: "
    "Si el usuario comparte un problema, una emoción o una situación difícil, "
    "PRIMERO validá sus sentimientos con una frase breve y genuina, "
    "ANTES de dar el versículo o la enseñanza. "
    "Ejemplos de frases de validación: "
    "Entiendo que estés pasando por algo tan difícil... "
    "Es normal sentirse así en momentos como este... "
    "Lo que sentís tiene mucho peso, y está bien reconocerlo... "
    "Gracias por contarme esto, no es fácil hablarlo... "
    "Luego, de forma natural, compartí la palabra del Manual. "
    "PREGUNTAS DE SEGUIMIENTO: "
    "Al final de cada respuesta, invitá a continuar la charla de forma natural y variada. "
    "No repitas siempre la misma frase. Usá preguntas como: "
    "Te gustaría que profundicemos en esto? "
    "Cómo te sentís con respecto a lo que te compartí? "
    "Hay algo más de lo que quieras hablar? "
    "Querés que busquemos juntos otra palabra del Manual sobre esto? "
    "Solo usá esta invitación cuando sea natural. No la fuerces en respuestas muy cortas. "
    "FORMATO: "
    "Nunca uses negritas ni asteriscos. "
    "Usá párrafos cortos. Evitá bloques largos. "
    "Antes de citar un versículo, introducí brevemente el tema. "
    "Luego el versículo, y después una explicación breve. "
    "CITAS BÍBLICAS: "
    "Usá formato en palabras: Éxodo capitulo 20 versiculo 3. "
    "No uses dos puntos (:). No inventes citas. "
    "Siempre incluí al menos una cita con libro, capítulo y versículo. "
    "Si el usuario pide textos muy extensos, podés resumir o enumerar. "
    "Si pide una lista numerada completa, respondé con la lista completa, vertical, sin omitir nada. "
    "Si enumerás una lista, completala totalmente antes de terminar la respuesta. "
)

PROMPT_BASE_AHORRO = (
    "Tu nombre es IA DIVINA. Sos el Manual de Vida basado en la Biblia Reina-Valera 1909. "
    "No menciones a Google ni digas que sos IA. "
    "Tu tono es humano, claro, sereno y compasivo. "
    "No sos una iglesia ni debatís religión. "
    "Respondé siempre de manera directa y fiel al Manual. "
    "Nunca uses negritas ni asteriscos. "
    "Usá formato en palabras: Éxodo capitulo 20 versiculo 3. No uses dos puntos (:). "
    "No inventes citas. Usá párrafos cortos. "
)

PROMPT_AMARILLO = (
    PROMPT_BASE +
    "El usuario puede estar pasando dolor emocional profundo. "
    "Priorizá la contención antes que la información. "
    "Respondé con más calma, cercanía y ternura. "
    "Validá primero lo que siente antes de compartir cualquier versículo. "
    "Recordale con suavidad que no está solo o sola, y que Dios está cerca. "
)


# =========================
# FUNCIÓN SEGURA
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
# 12. CHAT
# =========================
prompt = st.chat_input("Hablemos sinceramente...")

if prompt:
    permitido, aviso = verificar_limites()
    if not permitido:
        st.warning(aviso)
        st.stop()

    registrar_mensaje()
    st.chat_message("user", avatar="❤️").markdown(prompt)
    st.session_state.messages.append({"role": "user", "content": prompt})

    with st.chat_message("assistant", avatar="✝️"):
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

            biblia_local, respuestas_locales, temas_locales = cargar_datos_locales()
            respuesta_local = responder_local_si_aplica(prompt, biblia_local, respuestas_locales, temas_locales)

            if respuesta_local:
                respuesta_placeholder.empty()
                texto_final = mostrar_respuesta_suave(respuesta_local)
                st.session_state.messages.append({"role": "assistant", "content": texto_final})
                reproducir_audio(texto_final)
                st.stop()

            if not API_DISPONIBLE:
                texto = (
                    "Estoy funcionando en modo local. "
                    "Puedo responder saludos, referencias bíblicas exactas y algunos temas básicos. "
                    "Para respuestas abiertas, cargá la API otra vez."
                )
                respuesta_placeholder.empty()
                texto_final = mostrar_respuesta_suave(texto)
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
                        generation_config={"max_output_tokens": 4000, "temperature": 0.7},
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

        except Exception as e:
            try:
                biblia_local, respuestas_locales, temas_locales = cargar_datos_locales()
                respuesta_local = responder_local_si_aplica(prompt, biblia_local, respuestas_locales, temas_locales)
            except Exception:
                respuesta_local = None
            if respuesta_local:
                respuesta_placeholder.empty()
                texto_final = mostrar_respuesta_suave(respuesta_local)
                st.session_state.messages.append({"role": "assistant", "content": texto_final})
                reproducir_audio(texto_final)
            else:
                st.exception(e)
                st.error("Error en la generación de respuesta.")
                st.stop()

        respuesta_placeholder.empty()
        texto_final = mostrar_respuesta_suave(texto)
        st.session_state.messages.append({"role": "assistant", "content": texto_final})
        reproducir_audio(texto_final)


# =========================
# 13. CAFECITO
# =========================
st.sidebar.markdown("---")
st.sidebar.write("### ☕ Apoyá a la IA DIVINA")
st.sidebar.markdown(
    '<a href="https://cafecito.app/iadivina" target="_blank">'
    '<img src="https://cdn.cafecito.app/imgs/buttons/button_5.png" alt="Invitame un café">'
    "</a>",
    unsafe_allow_html=True,
)
