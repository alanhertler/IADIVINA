import os
os.environ["STREAMLIT_SERVER_FILE_WATCHER_TYPE"] = "none"

import json
import streamlit as st
# =========================
# BIBLIA LOCAL (RV1909)
# =========================
def cargar_biblia():
    try:
        with open("data/biblia_rv1909_completa.json", "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print("Error cargando Biblia:", e)
        return None

biblia = cargar_biblia()


def buscar_versiculo(libro, capitulo, versiculo):
    if not biblia:
        return None

    alias_libros = {
        "genesis": "Genesis",
        "gen": "Genesis",
        "exodo": "Exodus",
        "éxodo": "Exodus",
        "levitico": "Leviticus",
        "levítico": "Leviticus",
        "numeros": "Numbers",
        "números": "Numbers",
        "deuteronomio": "Deuteronomy",
        "josue": "Joshua",
        "josué": "Joshua",
        "jueces": "Judges",
        "rut": "Ruth",
        "1 samuel": "1 Samuel",
        "2 samuel": "2 Samuel",
        "1 reyes": "1 Kings",
        "2 reyes": "2 Kings",
        "1 cronicas": "1 Chronicles",
        "1 crónicas": "1 Chronicles",
        "2 cronicas": "2 Chronicles",
        "2 crónicas": "2 Chronicles",
        "esdras": "Ezra",
        "nehemias": "Nehemiah",
        "nehemías": "Nehemiah",
        "ester": "Esther",
        "job": "Job",
        "salmo": "Psalms",
        "salmos": "Psalms",
        "proverbios": "Proverbs",
        "eclesiastes": "Ecclesiastes",
        "eclesiastés": "Ecclesiastes",
        "cantares": "Song of Solomon",
        "cantar de los cantares": "Song of Solomon",
        "isaias": "Isaiah",
        "isaías": "Isaiah",
        "jeremias": "Jeremiah",
        "jeremías": "Jeremiah",
        "lamentaciones": "Lamentations",
        "ezequiel": "Ezekiel",
        "daniel": "Daniel",
        "oseas": "Hosea",
        "joel": "Joel",
        "amos": "Amos",
        "abdias": "Obadiah",
        "abdías": "Obadiah",
        "jonas": "Jonah",
        "jonás": "Jonah",
        "miqueas": "Micah",
        "nahum": "Nahum",
        "habacuc": "Habakkuk",
        "sofonias": "Zephaniah",
        "sofonías": "Zephaniah",
        "hageo": "Haggai",
        "zacarias": "Zechariah",
        "zacarías": "Zechariah",
        "malaquias": "Malachi",
        "malaquías": "Malachi",
        "mateo": "Matthew",
        "marcos": "Mark",
        "lucas": "Luke",
        "juan": "John",
        "san juan": "John",
        "jn": "John",
        "hechos": "Acts",
        "romanos": "Romans",
        "1 corintios": "1 Corinthians",
        "2 corintios": "2 Corinthians",
        "galatas": "Galatians",
        "gálatas": "Galatians",
        "efesios": "Ephesians",
        "filipenses": "Philippians",
        "colosenses": "Colossians",
        "1 tesalonicenses": "1 Thessalonians",
        "2 tesalonicenses": "2 Thessalonians",
        "1 timoteo": "1 Timothy",
        "2 timoteo": "2 Timothy",
        "tito": "Titus",
        "filemon": "Philemon",
        "filémon": "Philemon",
        "hebreos": "Hebrews",
        "santiago": "James",
        "1 pedro": "1 Peter",
        "2 pedro": "2 Peter",
        "1 juan": "1 John",
        "2 juan": "2 John",
        "3 juan": "3 John",
        "judas": "Jude",
        "apocalipsis": "Revelation",
        "revelacion": "Revelation",
        "revelación": "Revelation",
    }

    libro_normalizado = normalizar(libro)
    libro_json = alias_libros.get(libro_normalizado, libro)

    for book in biblia["books"]:
        if book["name"].lower() == libro_json.lower():
            for chap in book["chapters"]:
                if chap["chapter"] == capitulo:
                    for verse in chap["verses"]:
                        if verse["verse"] == versiculo:
                            return verse["text"]

    return None
import google.genai as genai
from gtts import gTTS
import base64
import re
import time
import io
from pathlib import Path
from collections import deque


def normalizar(texto):
    texto = str(texto).lower().strip()

    reemplazos = {
        "4": "a",
        "3": "e",
        "1": "i",
        "0": "o",
        "5": "s",
        "@": "a",
    }
    for k, v in reemplazos.items():
        texto = texto.replace(k, v)

    reemplazos_directos = {
        "kiero": "quiero",
        "qiero": "quiero",
        "mor1r": "morir",
        "m4tar": "matar",
        "m4t4r": "matar",
        "su1cid": "suicid",
        "mat4r": "matar",
        "ki3ro": "quiero",
        "xq": "porque",
    }
    for k, v in reemplazos_directos.items():
        texto = texto.replace(k, v)

    for a, b in {
        "á": "a", "é": "e", "í": "i", "ó": "o", "ú": "u", "ñ": "n"
    }.items():
        texto = texto.replace(a, b)

    texto = re.sub(r"[_\-]+", " ", texto)
    texto = re.sub(r"[^\w\s]", " ", texto)
    texto = re.sub(r"\s+", " ", texto).strip()
    return texto


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
client = None

if API_DISPONIBLE:
    client = genai.Client(api_key=API_KEY)


# =========================
# 1.1 MOTOR LOCAL BÍBLICO
# =========================
BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"

BIBLIA_FILE = DATA_DIR / "biblia_rv1909_completa.json"
RESPUESTAS_FILE = DATA_DIR / "respuestas.json"
TEMAS_FILE = DATA_DIR / "temas.json"

BIBLIA_DEMO = []

RESPUESTAS_DEMO = {
    "saludo": "Estoy acá para escucharte. Podés contarme qué te pasa, pedir un versículo o escribir un capítulo como Juan 1 o Salmo 91.",
    "ayuda": "Podés escribir cosas como Juan capitulo 3 versiculo 16, Salmo 91, Marcos 1 o dame un versículo sobre paz.",
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
    "miedo": [{"libro": "Isaias", "capitulo": 41, "versiculo": 10}],
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
        {"libro": "Isaias", "capitulo": 41, "versiculo": 10},
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

    if not RESPUESTAS_FILE.exists():
        guardar_json(RESPUESTAS_FILE, RESPUESTAS_DEMO)

    if not TEMAS_FILE.exists():
        guardar_json(TEMAS_FILE, TEMAS_DEMO)

    if not BIBLIA_FILE.exists():
        guardar_json(BIBLIA_FILE, BIBLIA_DEMO)


def cargar_datos_locales():
    return cargar_json(BIBLIA_FILE), cargar_json(RESPUESTAS_FILE), cargar_json(TEMAS_FILE)


def normalizar_local(texto: str) -> str:
    texto = str(texto).lower().strip()
    reemplazos = {
        "á": "a", "é": "e", "í": "i", "ó": "o", "ú": "u", "ñ": "n"
    }
    for a, b in reemplazos.items():
        texto = texto.replace(a, b)
    texto = re.sub(r"[^\w\s]", " ", texto)
    texto = re.sub(r"\s+", " ", texto).strip()
    return texto


def canon_libro(nombre: str):
    n = normalizar_local(nombre)
    alias = {
        "salmo": "Salmos",
        "salmos": "Salmos",
        "sal": "Salmos",
        "psalmo": "Salmos",
        "mateo": "Mateo",
        "san mateo": "Mateo",
        "evangelio de mateo": "Mateo",
        "marcos": "Marcos",
        "san marcos": "Marcos",
        "evangelio de marcos": "Marcos",
        "lucas": "Lucas",
        "san lucas": "Lucas",
        "san luca": "Lucas",
        "evangelio de lucas": "Lucas",
        "juan": "Juan",
        "san juan": "Juan",
        "evangelio de juan": "Juan",
        "romanos": "Romanos",
        "filipenses": "Filipenses",
        "isaias": "Isaias",
        "isaias": "Isaias",
        "exodo": "Exodo",
    }
    return alias.get(n)


def extraer_referencia_local(consulta: str):
    q = normalizar_local(consulta)
    patrones = [
        r"^([a-z\s]+?)\s+capitulo\s+(\d+)\s+versiculo\s+(\d+)$",
        r"^([a-z\s]+?)\s+(\d+)\s+(\d+)$",
        r"^([a-z\s]+?)\s+(\d+)[:](\d+)$",
    ]

    for patron in patrones:
        m = re.match(patron, q)
        if m:
            libro = canon_libro(m.group(1))
            if libro:
                return {
                    "libro": libro,
                    "capitulo": int(m.group(2)),
                    "versiculo": int(m.group(3)),
                }
    return None


def extraer_capitulo_local(consulta: str):
    q = normalizar_local(consulta)
    patrones = [
        r"^([a-z\s]+?)\s+capitulo\s+(\d+)$",
        r"^([a-z\s]+?)\s+(\d+)$",
    ]

    for patron in patrones:
        m = re.match(patron, q)
        if m:
            libro = canon_libro(m.group(1))
            if libro:
                return {
                    "libro": libro,
                    "capitulo": int(m.group(2)),
                }
    return None


def buscar_por_referencia_local(biblia, libro, capitulo, versiculo=None):
    if not biblia or "books" not in biblia:
        return None

    alias_libros = {
        "genesis": "Genesis",
        "gen": "Genesis",
        "exodo": "Exodus",
        "éxodo": "Exodus",
        "levitico": "Leviticus",
        "levítico": "Leviticus",
        "numeros": "Numbers",
        "números": "Numbers",
        "deuteronomio": "Deuteronomy",
        "josue": "Joshua",
        "josué": "Joshua",
        "jueces": "Judges",
        "rut": "Ruth",
        "1 samuel": "1 Samuel",
        "2 samuel": "2 Samuel",
        "1 reyes": "1 Kings",
        "2 reyes": "2 Kings",
        "1 cronicas": "1 Chronicles",
        "1 crónicas": "1 Chronicles",
        "2 cronicas": "2 Chronicles",
        "2 crónicas": "2 Chronicles",
        "esdras": "Ezra",
        "nehemias": "Nehemiah",
        "nehemías": "Nehemiah",
        "ester": "Esther",
        "job": "Job",
        "salmo": "Psalms",
        "salmos": "Psalms",
        "proverbios": "Proverbs",
        "eclesiastes": "Ecclesiastes",
        "eclesiastés": "Ecclesiastes",
        "cantares": "Song of Solomon",
        "cantar de los cantares": "Song of Solomon",
        "isaias": "Isaiah",
        "isaías": "Isaiah",
        "jeremias": "Jeremiah",
        "jeremías": "Jeremiah",
        "lamentaciones": "Lamentations",
        "ezequiel": "Ezekiel",
        "daniel": "Daniel",
        "oseas": "Hosea",
        "joel": "Joel",
        "amos": "Amos",
        "abdias": "Obadiah",
        "abdías": "Obadiah",
        "jonas": "Jonah",
        "jonás": "Jonah",
        "miqueas": "Micah",
        "nahum": "Nahum",
        "habacuc": "Habakkuk",
        "sofonias": "Zephaniah",
        "sofonías": "Zephaniah",
        "hageo": "Haggai",
        "zacarias": "Zechariah",
        "zacarías": "Zechariah",
        "malaquias": "Malachi",
        "malaquías": "Malachi",
        "mateo": "Matthew",
        "san mateo": "Matthew",
        "mate": "Matthew",
        "san mate": "Matthew",
        "marcos": "Mark",
        "san marcos": "Mark",
        "lucas": "Luke",
        "san lucas": "Luke",
        "juan": "John",
        "san juan": "John",
        "jn": "John",
        "hechos": "Acts",
        "romanos": "Romans",
        "1 corintios": "1 Corinthians",
        "2 corintios": "2 Corinthians",
        "galatas": "Galatians",
        "gálatas": "Galatians",
        "efesios": "Ephesians",
        "filipenses": "Philippians",
        "colosenses": "Colossians",
        "1 tesalonicenses": "1 Thessalonians",
        "2 tesalonicenses": "2 Thessalonians",
        "1 timoteo": "1 Timothy",
        "2 timoteo": "2 Timothy",
        "tito": "Titus",
        "filemon": "Philemon",
        "filémon": "Philemon",
        "hebreos": "Hebrews",
        "santiago": "James",
        "1 pedro": "1 Peter",
        "2 pedro": "2 Peter",
        "1 juan": "1 John",
        "2 juan": "2 John",
        "3 juan": "3 John",
        "judas": "Jude",
        "apocalipsis": "Revelation",
        "revelacion": "Revelation",
        "revelación": "Revelation",
    }

    libro_norm = normalizar_local(libro)
    libro_json = alias_libros.get(libro_norm, libro)

    for book in biblia["books"]:
        if normalizar_local(book.get("name", "")) == normalizar_local(libro_json):
            for chap in book.get("chapters", []):
                if chap.get("chapter") == capitulo:
                    if versiculo is None:
                        versos = []
                        for v in chap.get("verses", []):
                            n = v.get("verse")
                            t = v.get("text", "").strip()
                            versos.append(f"Versiculo {n}. {t}")
                        return f"{libro.title()} {capitulo}\n\n" + " ".join(versos)

                    for v in chap.get("verses", []):
                        if v.get("verse") == versiculo:
                            texto = v.get("text", "").strip()
                            return f"{libro.title()} capitulo {capitulo} versiculo {versiculo}. {texto}"

    return None

def buscar_capitulo_local(biblia, libro, capitulo):
    if not biblia or "books" not in biblia:
        return None

    alias_libros = {
        "mateo": "Matthew",
        "san mateo": "Matthew",
        "mate": "Matthew",
        "san mate": "Matthew",
        "marcos": "Mark",
        "san marcos": "Mark",
        "lucas": "Luke",
        "san lucas": "Luke",
        "juan": "John",
        "san juan": "John",
        "genesis": "Genesis",
        "salmo": "Psalms",
        "salmos": "Psalms",
        "apocalipsis": "Revelation",
    }

    libro_norm = normalizar_local(libro)
    libro_json = alias_libros.get(libro_norm, libro)

    for book in biblia["books"]:
        if normalizar_local(book.get("name", "")) == normalizar_local(libro_json):
            for chap in book.get("chapters", []):
                if chap.get("chapter") == capitulo:
                    versos = []
                    for v in chap.get("verses", []):
                        n = v.get("verse")
                        t = v.get("text", "").strip()
                        versos.append(f"Versiculo {n}. {t}")

                    return f"{libro.title()} {capitulo}\n\n" + " ".join(versos)

    return None

    if not versiculos:
        return None

    versiculos.sort(key=lambda x: x.get("versiculo", 0))

    partes = [f"{libro} {capitulo}", ""]
    for v in versiculos:
        partes.append(f'Versiculo {v["versiculo"]}\n{v["texto"]}')
        partes.append("")
    return "\n".join(partes).strip()


def detectar_tema_local(consulta: str):    
    t = normalizar_local(consulta)
    mapa = {
        "consuelo": ["consuelo", "dolor", "quebrantado", "solo", "sola", "triste", "tristeza", "duelo"],
        "paz": ["paz", "calma", "tranquilidad", "descanso"],
        "miedo": ["miedo", "temor", "asustado", "asustada", "desesperado", "desesperada"],
        "fe": ["fe", "creer", "esperanza", "confianza"],
        "ansiedad": ["ansiedad", "ansioso", "ansiosa", "angustia", "angustiado", "angustiada"],
    }
    for tema, palabras in mapa.items():
        for palabra in palabras:
            if palabra in t:
                return tema
    return None


def buscar_versiculos_por_tema_local(biblia, temas, tema):
    resultado = []
    for ref in temas.get(tema, []):
        v = buscar_por_referencia_local(biblia, ref["libro"], ref["capitulo"], ref["versiculo"])
        if v:
            resultado.append(v)
    return resultado


def formatear_versiculo_local(item):
    return (
        f'{item["libro"]} capitulo {item["capitulo"]} versiculo {item["versiculo"]}\n'
        f'{item["texto"]}'
    )


def responder_local_si_aplica(consulta: str, biblia, respuestas, temas):
    consulta_norm = normalizar_local(consulta)

    if any(k in consulta_norm for k in ["10 mandamientos", "diez mandamientos", "mandamientos", "madamientos"]):
        return """LOS DIEZ MANDAMIENTOS

Base bíblica: EXODO capitulo 20 versiculos 3 al 17
Versión: Reina-Valera 1909

1. EXODO capitulo 20 versiculo 3
No tendrás dioses ajenos delante de mí

2. EXODO capitulo 20 versiculos 4 al 5
No te harás imagen, ni ninguna semejanza de cosa que esté arriba en el cielo, ni abajo en la tierra, ni en las aguas debajo de la tierra. No te inclinarás á ellas, ni las honrarás

3. EXODO capitulo 20 versiculo 7
No tomarás el nombre de Jehová tu Dios en vano

4. EXODO capitulo 20 versiculos 8 al 11
Acordarte has del día del reposo, para santificarlo

5. EXODO capitulo 20 versiculo 12
Honra á tu padre y á tu madre

6. EXODO capitulo 20 versiculo 13
No matarás

7. EXODO capitulo 20 versiculo 14
No adulterarás

8. EXODO capitulo 20 versiculo 15
No hurtarás

9. EXODO capitulo 20 versiculo 16
No hablarás contra tu prójimo falso testimonio

10. EXODO capitulo 20 versiculo 17
No codiciarás la casa de tu prójimo, no codiciarás la mujer de tu prójimo, ni su siervo, ni su criada, ni su buey, ni su asno, ni cosa alguna de tu prójimo"""

    if consulta_norm in ["hola", "buenas", "buen dia", "buenas tardes", "buenas noches"]:
        return respuestas["saludo"]

    if consulta_norm in ["ayuda", "menu", "como funciona"]:
        return respuestas["ayuda"]

    capitulo = extraer_capitulo_local(consulta)
    if capitulo:
        encontrado = buscar_capitulo_local(biblia, capitulo["libro"], capitulo["capitulo"])
        if encontrado and encontrado.count("Versiculo") >= 3:
            return encontrado

    referencia = extraer_referencia_local(consulta)
    if referencia:
        encontrado = buscar_por_referencia_local(
            biblia,
            referencia["libro"],
            referencia["capitulo"],
            referencia["versiculo"]
        )
        return encontrado if encontrado else "No encontré esa referencia en la base local actual."

    tema = detectar_tema_local(consulta)
    if tema:
        versiculos = buscar_versiculos_por_tema_local(biblia, temas, tema)
        if versiculos:
            encabezados = {
                "consuelo": respuestas.get("consuelo_base", "Te comparto una palabra:"),
                "paz": respuestas.get("paz_base", "Te comparto una palabra:"),
                "miedo": respuestas.get("miedo_base", "Te comparto una palabra:"),
                "fe": respuestas.get("fe_base", "Te comparto una palabra:"),
                "ansiedad": respuestas.get("consuelo_base", "Te comparto una palabra:"),
            }
            partes = [encabezados.get(tema, "Te comparto una palabra:")]
            for v in versiculos[:2]:
                partes.append("")
                partes.append(v)
            return "\n".join(partes)


asegurar_estructura_local()
# =========================
# 2.2 VOZ — gTTS
# =========================
def _generar_audio_gtts(texto):
    tts = gTTS(text=texto, lang="es")
    buffer = io.BytesIO()
    tts.write_to_fp(buffer)
    buffer.seek(0)
    return buffer


def reproducir_audio(texto: str):
    if not st.session_state.get("usar_voz", True):
        return

    try:
        texto_audio = texto.replace("\n", ". ").strip()
        if not texto_audio:
            return

        audio_bytes = _generar_audio_gtts(texto_audio)
        st.audio(audio_bytes, format="audio/mp3")
    except Exception as e:
        st.error(f"Error de sonido: {e}")


def mostrar_boton_audio(texto: str, clave_extra: str = ""):
    if not st.session_state.get("usar_voz", True):
        return

    clave_base = re.sub(r"[^a-zA-Z0-9_]+", "_", texto[:40])
    clave_audio = f"audio_{clave_extra}_{clave_base}"

    if st.button("🔊 Escuchar", key=clave_audio):
        reproducir_audio(texto)


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


def asegurar_cierre(texto: str) -> str:
    return str(texto).strip()


# =========================
# 3. CLASIFICACIÓN DE RIESGO
# =========================
def clasificar_riesgo(texto: str) -> str:
    t = normalizar(texto)

    if len(t.strip()) < 3:
        return "verde"

    for frase in [
        "me muero de risa", "me mori de risa", "me mato de risa",
        "jajaja me mato", "jaja me muero", "me parto de risa", "me caigo de risa"
    ]:
        if frase in t:
            return "verde"         
    
    patrones_rojos = [
        r"\bme voy a matar\b",
        r"\bme .* matar\b",
        r"\bquiero matarme\b",
        r"\bme quiero matar\b",
        r"\bquiero suicidarme\b",
        r"\bme voy a suicidar\b",
        r"\bno quiero seguir viviendo\b",
        r"\bno quiero seguir vivo\b",
        r"\bvoy a terminar con todo\b",
        r"\besta noche termino con todo\b",
        r"\bya tome pastillas\b",
        r"\bya tome remedios\b",
        r"\bya tome clonazepam\b",
        r"\bya tome alcohol\b",
        r"\bme tome\b.+\b(pastillas|remedios|clonazepam|alcohol)\b",
        r"\bestoy por cortarme\b",
        r"\bme voy a cortar\b",
        r"\ble mataron a\b",
        r"\bse murio mi amiga\b",
        r"\bse murio mi amigo\b",
        r"\bmataron a mi\b",
        r"\bperdi a mi\b",
        r"\bme quiero borrar\b",
        r"\bya no quiero estar\b",
        r"\bquiero desaparecer\b",
        r"\bdesearia no haber nacido\b",
        r"\bdeseo no haber nacido\b",
        r"\bno deberia haber nacido\b",
        r"\bno debi nacer\b",
        r"\bnadie me va a extrañar\b",
        r"\bnadie me extrañaria\b",
        r"\btodos estarian mejor sin mi\b",
        r"\btodos estarian mejor sin mí\b",
        r"\bsoy una carga\b",
        r"\bsoy un estorbo\b",
        r"\bme voy a tirar\b",
        r"\bme voy a aventar\b",
        r"\bquiero saltar\b",
        r"\bpienso en hacerme dano\b",
        r"\bpienso en hacerme daño\b",
        r"\bvoy a hacerme dano\b",
        r"\bvoy a hacerme daño\b",
        r"\bme lastime\b",
        r"\bme hice dano\b",
        r"\bme hice daño\b",
        r"\bquiero .* morir\b",
        r"\bno quiero vivir\b",
        r"\bme quiero ir\b",
        r"\bme quiero ir de aca\b",
        r"\bme quiero ir de aqui\b",
        r"\bya fue todo\b",
        r"\bno tiene sentido\b",
        r"\bestoy cansado de todo\b",
        r"\bestoy cansada de todo\b",
        r"\bno aguanto vivir\b",
        r"\bya no puedo mas con esto\b",
        r"\bno quiero estar aca\b",
        r"\bno quiero estar aqui\b",
        r"\bquiero dormirme y no despertar\b",
        r"\bseria mejor desaparecer\b",
        r"\bquiero dejar de existir\b",
        r"\bme quiero morir\b",
        r"\bquiero morir\b",
        r"\bme quiero dormir para siempre\b",
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
        r"\bme hizo cosas raras\b",
        r"\bme toco de manera rara\b",
        r"\bme toco de forma rara\b",
        r"\bme dejo tocar\b",
        r"\bme obligo a tocarlo\b",
        r"\bme obligo a tocarla\b",
        r"\bme saco fotos\b",
        r"\bme grabo sin ropa\b",
        r"\bme mando fotos\b",
        r"\bme pidio fotos\b",
        r"\bme pidió fotos\b",
        r"\bme piden fotos\b",
        r"\bun adulto me\b.+\bfotos\b",
        r"\bme groomea\b",
        r"\bme esta groomeando\b",
        r"\bme está groomeando\b",
        r"\bun mayor me pide\b",
        r"\bun chico mayor me\b",
        r"\bme amenaza para mandar fotos\b",
        r"\bme obliga a mandar fotos\b",
        r"\bme pide fotos sin ropa\b",
        r"\bme pidio fotos sin ropa\b",
        r"\bme toca cuando nadie ve\b",
        r"\bme toca a escondidas\b",
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
        r"\bno sirvo para nada\b",
        r"\bsoy un fracaso\b",
        r"\bnadie me entiende\b",
        r"\bnadie me quiere\b",
        r"\bme harte de todo\b",
        r"\bme tiene harto\b",
        r"\bme tiene harta\b",
        r"\bestoy harto de vivir\b",
        r"\bestoy harta de vivir\b",
        r"\bme siento invisible\b",
        r"\bme siento roto\b",
        r"\bme siento rota\b",
        r"\bme siento vacio\b",
        r"\bme siento vacia\b",
        r"\bno le importo a nadie\b",
        r"\bsoy una carga para todos\b",
        r"\btodo me sale mal\b",
        r"\bya no puedo mas\b",
        r"\bestoy agotado\b",
        r"\bestoy agotada\b",
        r"\bme siento muy triste\b",
        r"\bno puedo con esto\b",
        r"\bestoy cansado\b",
        r"\bestoy cansada\b",
        r"\bme siento para atras\b",
        r"\bquiero desaparecer un rato\b",
        r"\bno se que hacer con mi vida\b",
    ]
    for patron in patrones_amarillos:
        if re.search(patron, t):
            return "amarillo"

    return "verde"
# =========================
# DETECCIÓN DE INTENCIÓN
# =========================
def detectar_intencion(texto: str) -> str:
    t = normalizar(texto)

    palabras_tecnicas = [
        "diferencia", "version", "versiones", "traduccion",
        "que es", "como funciona", "porque", "historia",
        "cuando", "quien", "explicame", "explica"
    ]

    for palabra in palabras_tecnicas:
        if palabra in t:
            return "tecnica"

    return "espiritual"

# =========================
# 4. RESPUESTAS FIJAS
# =========================
def respuesta_roja() -> str:
    return (
        "Lo que estás diciendo es serio y necesito priorizar tu seguridad ahora mismo.\n\n"
        "Si sentís que podés lastimarte o que estás en peligro, llamá al 911 ahora.\n\n"
        "Si estás en Argentina, también podés llamar gratis al 135 desde CABA y GBA, "
        "o al 11 5275 1135 desde todo el país.\n\n"
        "Buscá a una persona real de confianza ya mismo y no te quedes sola o solo.\n\n"
        "Dios ve tu dolor aun en este momento. Salmos capitulo 34 versiculo 18.\n\n"
        "NECESITÁS HABLAR? ESTOY ACÁ. CONTAME."
    )


def respuesta_abuso() -> str:
    return (
        "Lo que te pasó es grave. No es tu culpa.\n\n"
        "Si estás en peligro ahora mismo, llamá al 911 de inmediato.\n\n"
        "Si estás en Argentina, también podés llamar al 137 para abuso sexual o violencia familiar. "
        "Si sos mujer y necesitás orientación, también podés comunicarte con el 144.\n\n"
        "Alejate de la persona que te hizo daño y buscá un adulto o una persona de confianza que pueda protegerte ahora.\n\n"
        "Si tenés dolor físico, sangrado o te lastimaron, buscá atención médica urgente.\n\n"
        "Dios está cerca de los quebrantados. Salmos capitulo 34 versiculo 18.\n\n"
        "NECESITÁS HABLAR? ESTOY ACÁ. CONTAME."
    )


def respuesta_filtrada(texto: str):
    t = normalizar(texto)
    if any(p in t for p in ["concha", "pija", "porno", "masturb", "sexo", "coger"]):
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


def get_base64(file_path: str):
    try:
        with open(file_path, "rb") as f:
            return base64.b64encode(f.read()).decode()
    except Exception:
        return None


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
            font-size: 18px !important; line-height: 1.85 !important;
        }}
        .stChatInputContainer textarea {{ font-size: 18px !important; }}
    }}
        .stChatInputContainer textarea {{ font-size: clamp(16px, 4vw, 18px) !important; }}
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
for i, m in enumerate(st.session_state.messages):
    avatar = "✝️" if m["role"] == "assistant" else "❤️"
    with st.chat_message(m["role"], avatar=avatar):
        st.markdown(m["content"].replace("\n", "  \n"))

        if m["role"] == "assistant":
            mostrar_boton_audio(m["content"], clave_extra=f"hist_{i}")


# =========================
# 11. PROMPTS
# =========================
PROMPT_BASE = (
    "Tu nombre es IA DIVINA. Sos el Manual de Vida basado en la Biblia Reina-Valera 1909. "

    "PROHIBICIÓN ESTRICTA: "
    "No menciones a Google, no digas que sos inteligencia artificial, modelo, sistema o programa. "
    "Si te preguntan quién te creó, respondé: "
    "Fui creada para acompañarte con la sabiduría del Manual de Vida. "

    "IDENTIDAD: "
    "Sos una guía espiritual cercana, humana, paciente y compasiva. "
    "No sos una iglesia ni debatís religión. "
    "Respondé de forma clara, directa y humana. "

    "SEGURIDAD CRÍTICA: "
    "Si el mensaje implica abuso, peligro, violencia, autolesión o riesgo inmediato, priorizá SIEMPRE la seguridad antes que la reflexión. "
    "Primero indicá acciones concretas y urgentes. "
    "Decí que busque ayuda real inmediata, que se aleje del peligro y que contacte autoridades, emergencias o una persona adulta de confianza según corresponda. "
    "No minimices ni espiritualices antes de la acción. "

    "ORDEN OBLIGATORIO: "
    "1 validar brevemente lo que pasa. "
    "2 indicar acción concreta si hay riesgo. "
    "3 dar contención breve. "
    "4 recién después, si suma, incluir un versículo corto. "

    "ESTILO: "
    "Usá respuestas cortas, claras y útiles. "
    "No hagas sermones largos. "
    "No repitas ideas. "
    "Usá párrafos breves. "

    "FORMATO GENERAL: "
    "Nunca uses negritas ni asteriscos. "
    "No uses símbolos innecesarios. "

    "CONSULTAS BÍBLICAS DIRECTAS: "
    "Si el usuario pide un salmo, capítulo o texto completo y ese contenido está en la base local, no des explicación previa ni introducción. "
    "Respondé directamente con el texto solicitado. "
    "Solo explicá si el usuario lo pide después. "
    "Si el capítulo completo está disponible en la base local, mostralo íntegro. "
    "Si no está en la base local, podés citarlo desde tu conocimiento bíblico "
    "siempre que sea fiel a la Reina-Valera 1909. "
    "Nunca inventes versículos ni números que no existan. "

    "FORMATO BÍBLICO COMPLETO: "
    "Para capítulos completos, mostrá solo el título una vez, por ejemplo Salmos 91 o Juan 1. "
    "Luego escribí los versículos como Versiculo 1, Versiculo 2, Versiculo 3. "
    "No repitas el nombre del libro en cada línea. "
    "No mezcles formatos. "

    "FORMATO COMPATIBLE CON VOZ: "
    "Nunca uses dos puntos en referencias bíblicas cuando redactes. "
    "No uses formatos como Juan 3:16. "
    "Siempre escribí las referencias en palabras, por ejemplo Juan capitulo 3 versiculo 16. "

    "CITAS BÍBLICAS: "
    "Si usás un versículo individual, escribilo completo y en palabras. "
    "Ejemplo: Salmos capitulo 34 versiculo 18. "
    "No uses dos puntos. "
    "No inventes citas. "
    "No es obligatorio incluir versículo si no aporta. "

    "INTEGRIDAD DEL TEXTO: "
    "Cuando muestres un versículo individual, debe estar completo. "
    "No cortes frases ni dejes ideas incompletas. "
    "No resumas un versículo. "
    "No inventes el resto de un versículo. "

    "VARIACIONES DEL USUARIO: "
    "Reconocé distintas formas de pedir lo mismo. "
    "Ejemplos válidos: salmo 91, salmos 91, sal 91, san juan 1, juan 1, san lucas 1, marcos 1, mateo 5, juan capitulo 3 versiculo 16, juan 3 16. "
    "Interpretá correctamente aunque esté mal escrito. "

    "INSULTOS O AGRESIÓN VERBAL: "
    "Si el usuario insulta, respondé breve, con calma, sin sermón largo, y redirigí la conversación. "

    "IDIOMA Y CONTROL DE RESPUESTA: "
    "Respondé siempre en español. "
    "Nunca uses inglés. "
    "No muestres pensamientos internos. "
    "No escribas frases como wait, I should, checking. "
    "No expliques lo que estás haciendo. "
    "Respondé directamente con la respuesta final. "
)

PROMPT_BASE_AHORRO = (
    "Tu nombre es IA DIVINA. Sos el Manual de Vida basado en la Biblia Reina-Valera 1909. "
    "No menciones a Google ni digas que sos IA. "
    "Tu tono es humano, claro, sereno y compasivo. "
    "No sos una iglesia ni debatís religión. "
    "Respondé siempre de manera directa y fiel al Manual. "
    "Nunca uses negritas ni asteriscos. "
    "Usá formato en palabras: Exodo capitulo 20 versiculo 3. No uses dos puntos. "
    "No inventes citas. Usá párrafos cortos. "
    "Si hay peligro o abuso, priorizá seguridad inmediata y acciones concretas antes que cualquier reflexión. "
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
                mostrar_boton_audio(texto_final, clave_extra="nuevo_rojo")
                st.stop()

            elif nivel == "rojo_abuso":
                texto = respuesta_abuso()
                respuesta_placeholder.empty()
                texto_final = mostrar_respuesta_suave(texto)
                st.session_state.messages.append({"role": "assistant", "content": texto_final})
                mostrar_boton_audio(texto_final, clave_extra="nuevo_abuso")
                st.stop()

            respuesta_directa = respuesta_filtrada(prompt)
            if respuesta_directa:
                respuesta_placeholder.empty()
                texto_final = mostrar_respuesta_suave(respuesta_directa)
                st.session_state.messages.append({"role": "assistant", "content": texto_final})
                mostrar_boton_audio(texto_final, clave_extra="nuevo_filtrado")
                st.stop()

            biblia_local, respuestas_locales, temas_locales = cargar_datos_locales()
            respuesta_local = responder_local_si_aplica(prompt, biblia_local, respuestas_locales, temas_locales)

            if respuesta_local:
                respuesta_placeholder.empty()
                texto_final = mostrar_respuesta_suave(respuesta_local)
                st.session_state.messages.append({"role": "assistant", "content": texto_final})
                mostrar_boton_audio(texto_final, clave_extra="nuevo_local")
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
                mostrar_boton_audio(texto_final, clave_extra="nuevo_sin_api")
                st.stop()

            with respuesta_placeholder.container():
                with st.spinner("Buscando respuesta en el Manual..."):
                    historial = construir_historial(st.session_state.messages, limite=15)
                    intencion = detectar_intencion(prompt)

                    if intencion == "tecnica":
                        contexto = (
                            "Responde en español de forma clara y directa.\n"
                            "Esta es una pregunta técnica o informativa.\n"
                            "NO uses versículos bíblicos.\n"
                            "NO hagas reflexión espiritual.\n"
                            "NO incluyas contenido religioso.\n"
                            "Solo responde con información clara y concreta.\n"
                        )
                    else:
                        contexto = PROMPT_AMARILLO if nivel == "amarillo" else PROMPT_BASE
            
                    response = client.models.generate_content(
                        model="gemini-2.5-flash",
                        contents=f"{contexto}\n\n{historial}\nUsuario: {prompt}",
                        config={
                            "max_output_tokens": 2000,
                            "temperature": 0.45,
                        },
                    )
                    texto_extraido, error_detalle, finish_reason = extraer_texto_seguro(response)

                    if not texto_extraido:
                        fr = (finish_reason or "").upper()
                        if "RECITATION" in fr or fr == "4":
                            texto_extraido = (
                                "Ese contenido no lo puedo mostrar de forma literal completa, "
                                "pero sí puedo explicártelo.\n\n"
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
                mostrar_boton_audio(texto_final, clave_extra="nuevo_fallback")
                st.stop()
            else:
                st.exception(e)
                st.error("Error en la generación de respuesta.")
                st.stop()

        respuesta_placeholder.empty()
        texto_final = mostrar_respuesta_suave(texto)
        st.session_state.messages.append({"role": "assistant", "content": texto_final})
        mostrar_boton_audio(texto_final, clave_extra="nuevo_modelo")
        
# =========================
# 13. CAFECITO
# =========================
st.sidebar.markdown("---")
st.sidebar.write("### ☕ Apoyá a la IA DIVINA")
st.sidebar.markdown(
    '<a href="https://cafecito.app/iadivina" target="_blank"><img src="https://cdn.cafecito.app/imgs/buttons/button_5.png" alt="Invitame un café"></a>',
    unsafe_allow_html=True
)




