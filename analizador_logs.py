"""
Analizador de logs
------------------
Lee un archivo de texto con eventos de una aplicación, clasifica cada línea y
muestra un resumen en consola.

Formato esperado de una línea bien formada:
    [NIVEL] AAAA-MM-DD mensaje            ej.  [ERROR] 2025-01-10 Failed to connect

Uso:
    python analizador_logs.py                      -> abre un selector de archivos
    python analizador_logs.py logs_prueba/log_bueno.txt

IMPORTANTE (consigna de la actividad): las REGLAS DE VALIDACIÓN las define el
estudiante. En este archivo cada regla está marcada como:
    DECISIÓN DEL ESTUDIANTE ................ regla elegida directamente por el estudiante
    DECISIÓN DEL ESTUDIANTE (propuesta de la IA, confirmada) ... la IA propuso un valor
        por defecto para un caso que el estudiante no había definido; el estudiante lo
        revisó y lo confirmó como suyo. La IA solo propuso: la decisión final es humana.
"""
from __future__ import annotations   # permite 'str | None' en Python 3.8+

import re
import sys
from dataclasses import dataclass, field
from datetime import datetime

# ==========================================================================
# REGLAS DE VALIDACIÓN
# ==========================================================================
VALID_LEVELS = ("INFO", "WARNING", "ERROR")
DATE_FORMAT = "%Y-%m-%d"

# DECISIÓN DEL ESTUDIANTE 1: nivel válido pero SIN fecha
#   -> la línea cuenta como evento Y TAMBIÉN como mal formateada.
COUNT_EVENT_IF_NO_DATE = True

# DECISIÓN DEL ESTUDIANTE 2: línea sin nivel válido (sin corchetes, o nivel
#   distinto de INFO/WARNING/ERROR, p. ej. [DEBUG])
#   -> mal formateada y NO cuenta como evento. (Se aplica en parse_line: una línea
#   sin nivel válido nunca es evento, porque no se sabría en qué tipo contarla.)

# DECISIÓN DEL ESTUDIANTE 3: fecha con formato incorrecto o imposible
#   (p. ej. 2025-13-45) -> toda la línea es mal formateada.
# (Interpretación propuesta por la IA y confirmada por el estudiante: "toda la línea
#   mal formateada" significa que NO cuenta como evento, igual que la decisión 2.
#   Cambiar a True si algún día debe contar como evento.)
COUNT_EVENT_IF_INVALID_DATE = False

# DECISIÓN DEL ESTUDIANTE 4 (propuesta de la IA, confirmada): nivel y fecha válidos pero
#   SIN mensaje (línea incompleta)
#   -> mal formateada y NO cuenta como evento.
COUNT_EVENT_IF_NO_MESSAGE = False

# DECISIÓN DEL ESTUDIANTE 5 (propuesta de la IA, confirmada): los niveles distinguen mayúsculas ("[info]" es inválido).
# DECISIÓN DEL ESTUDIANTE 6 (propuesta de la IA, confirmada): las líneas vacías o solo con espacios se ignoran y no se
#   cuentan ni como evento ni como mal formateadas.
# DECISIÓN DEL ESTUDIANTE 7 (propuesta de la IA, confirmada): solo se acepta fecha estricta AAAA-MM-DD. "2025/01/10",
#   "10-01-2025" o "2025-01-10T10:00:00" se consideran fecha inválida.

# --------------------------------------------------------------------------
# Expresiones regulares (propuestas con apoyo de IA, revisadas por el estudiante)
# --------------------------------------------------------------------------
# Captura el contenido entre el primer par de corchetes y todo lo que sigue.
LINE_RE = re.compile(r"^\[(?P<level>[^\]]*)\]\s*(?P<rest>.*)$")
# "Parece una fecha": tres grupos numéricos separados por - / o . Y con un año de
# 4 dígitos al inicio (2025-01-10) o al final (10-01-2025). Sirve para distinguir
# "fecha mal escrita" de "no hay fecha".
# DECISIÓN DEL ESTUDIANTE 8 (corrección tras detectar un caso mejorable): la primera
#   versión de esta regla (propuesta por la IA) aceptaba cualquier "\d.\d.\d", así que
#   un número de versión como "[INFO] 1.2.3 released" se descartaba como "fecha inválida"
#   aunque simplemente NO tenía fecha. Con el año de 4 dígitos obligatorio, "1.2.3" o una
#   IP como "192.168.1.1" ya no parecen fecha y se tratan como "sin fecha" (decisión 1).
DATE_LIKE_RE = re.compile(
    r"^(?:\d{4}[-/.]\d{1,2}[-/.]\d{1,2}|\d{1,2}[-/.]\d{1,2}[-/.]\d{4})(?!\d)"
)
# Fecha estricta. strptime por sí solo acepta "2025-1-5", por eso se exige esto antes.
STRICT_DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")


# ==========================================================================
# MODELO DE DATOS
# ==========================================================================
@dataclass
class ParsedLine:
    number: int                      # número de línea en el archivo (desde 1)
    raw: str                         # texto original (sin salto de línea)
    level: str | None = None         # INFO / WARNING / ERROR, o None si no es válido
    date_status: str = "n/a"         # "valid" | "missing" | "invalid" | "n/a"
    message: str = ""
    problems: list = field(default_factory=list)   # motivos por los que está mal
    is_event: bool = False           # ¿cuenta en el total de eventos?

    @property
    def is_malformed(self):
        return len(self.problems) > 0


@dataclass
class Summary:
    blank_lines: int = 0
    lines_read: int = 0
    events: int = 0
    by_level: dict = field(default_factory=lambda: {lvl: 0 for lvl in VALID_LEVELS})
    events_without_date: int = 0
    malformed: list = field(default_factory=list)   # lista de ParsedLine

    @property
    def malformed_and_event(self):
        return sum(1 for p in self.malformed if p.is_event)


# ==========================================================================
# ANÁLISIS
# ==========================================================================
def is_valid_date(token):
    """True si token es una fecha estricta AAAA-MM-DD que existe en el calendario."""
    if not STRICT_DATE_RE.match(token):
        return False
    try:
        datetime.strptime(token, DATE_FORMAT)   # rechaza 2025-13-45 y 2025-02-30
        return True
    except ValueError:
        return False


def parse_line(number, raw):
    """Analiza una línea. Devuelve None si está vacía (se ignora)."""
    text = raw.strip()
    if not text:
        return None

    parsed = ParsedLine(number=number, raw=text)

    match = LINE_RE.match(text)
    if not match:
        parsed.problems.append("sin nivel entre corchetes")
        return parsed                                   # DECISIÓN 2: no es evento

    level = match.group("level")
    if level not in VALID_LEVELS:
        parsed.problems.append(f"nivel no válido: [{level}]")
        return parsed                                   # DECISIÓN 2: no es evento
    parsed.level = level

    rest = match.group("rest").strip()
    tokens = rest.split(None, 1)                        # [primera palabra, resto]
    first = tokens[0] if tokens else ""

    if first and DATE_LIKE_RE.match(first):
        # Hay algo que parece fecha: validar formato y existencia.
        parsed.message = tokens[1].strip() if len(tokens) > 1 else ""
        if is_valid_date(first):
            parsed.date_status = "valid"
        else:
            parsed.date_status = "invalid"
            parsed.problems.append(f"fecha inválida: {first}")
    else:
        parsed.date_status = "missing"
        parsed.message = rest
        parsed.problems.append("sin fecha")

    if not parsed.message:
        parsed.problems.append("sin mensaje")

    # ¿Cuenta como evento? Se aplican las reglas configurables de arriba.
    parsed.is_event = True
    if parsed.date_status == "missing" and not COUNT_EVENT_IF_NO_DATE:
        parsed.is_event = False
    if parsed.date_status == "invalid" and not COUNT_EVENT_IF_INVALID_DATE:
        parsed.is_event = False
    if not parsed.message and not COUNT_EVENT_IF_NO_MESSAGE:
        parsed.is_event = False
    return parsed


def analyze(lines):
    """Recorre las líneas y arma el resumen."""
    summary = Summary()
    for number, raw in enumerate(lines, start=1):
        summary.lines_read += 1
        parsed = parse_line(number, raw.rstrip("\r\n"))
        if parsed is None:
            summary.blank_lines += 1
            continue
        if parsed.is_event:
            summary.events += 1
            summary.by_level[parsed.level] += 1
            if parsed.date_status == "missing":
                summary.events_without_date += 1
        if parsed.is_malformed:
            summary.malformed.append(parsed)
    return summary


# ==========================================================================
# ENTRADA / SALIDA
# ==========================================================================
def choose_file():
    """Ruta por argumento; si no, selector gráfico; si no hay entorno gráfico, input()."""
    if len(sys.argv) > 1:
        return sys.argv[1]
    try:
        import tkinter as tk
        from tkinter import filedialog
        root = tk.Tk()
        root.withdraw()
        root.attributes("-topmost", True)
        path = filedialog.askopenfilename(
            title="Selecciona el archivo de log",
            filetypes=[("Archivos de texto", "*.txt *.log"), ("Todos los archivos", "*.*")],
        )
        root.destroy()
        if path:
            return path
        print("No se seleccionó ningún archivo en la ventana.")
    except Exception:
        pass   # sin tkinter o sin pantalla: se pide la ruta por consola
    return input("Escribe la ruta del archivo de log: ").strip().strip('"')


def read_lines(path):
    # utf-8-sig elimina la marca BOM si el archivo la tiene; errors="replace" evita
    # que un carácter extraño haga fallar todo el análisis.
    with open(path, encoding="utf-8-sig", errors="replace") as f:
        return f.readlines()


def short(text, width=62):
    return text if len(text) <= width else text[: width - 3] + "..."


def print_report(path, s, max_malformed=15):
    line = "=" * 64
    print(line)
    print(" ANÁLISIS DE LOGS")
    print(line)
    print(f" Archivo: {path}")
    print(f" Líneas leídas: {s.lines_read}   (vacías ignoradas: {s.blank_lines})")
    print()
    print(" RESUMEN")
    print(f"   Total de eventos ............. {s.events}")
    for lvl in VALID_LEVELS:
        print(f"     {lvl:<8} ................. {s.by_level[lvl]}")
    print(f"   Eventos sin fecha ............ {s.events_without_date}")
    n = s.malformed_and_event
    verbo = "cuenta" if n == 1 else "cuentan"
    print(f"   Líneas mal formateadas ....... {len(s.malformed)}"
          f"   ({n} de ellas también {verbo} como evento)")
    if s.malformed:
        print()
        print(" LÍNEAS MAL FORMATEADAS")
        for p in s.malformed[:max_malformed]:
            print(f"   Línea {p.number:>3}: {', '.join(p.problems)}")
            print(f"              {short(p.raw)}")
        if len(s.malformed) > max_malformed:
            print(f"   ... y {len(s.malformed) - max_malformed} más")
    print(line)


def main():
    path = choose_file()
    try:
        lines = read_lines(path)
    except FileNotFoundError:
        print(f"Error: no existe el archivo '{path}'.")
        return 1
    except IsADirectoryError:
        print(f"Error: '{path}' es una carpeta, no un archivo.")
        return 1
    except PermissionError:
        print(f"Error: no tienes permiso para leer '{path}'.")
        return 1
    except OSError as e:
        print(f"Error al abrir '{path}': {e}")
        return 1

    if not lines:
        print(f"El archivo '{path}' está vacío: no hay nada que analizar.")
        return 0

    print_report(path, analyze(lines))
    return 0


if __name__ == "__main__":
    sys.exit(main())
