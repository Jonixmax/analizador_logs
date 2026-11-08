# 🔍 Analizador de Logs en Python

Script que lee un archivo de texto con eventos de una aplicación, clasifica cada línea y muestra en consola un resumen claro: total de eventos, cantidad por nivel de severidad y líneas mal formateadas o incompletas.

> **Actividad:** IA como Herramienta, no como Autor: Desarrollo Guiado y Validado de un Script en Python
> **Curso:** AI for Developers Jr. 4 · KODIGO Academy · Semana 3
> **Autor:** Jonathan Alberto
> **IA de apoyo:** Claude (Anthropic)

El documento de reflexión técnica está en [`REFLEXION_TECNICA.md`](REFLEXION_TECNICA.md).

---

## 📋 Contenido

1. [Qué hace](#-qué-hace)
2. [Ejecución](#-ejecución)
3. [Estructura del proyecto](#-estructura-del-proyecto)
4. [Reglas de validación y quién decidió cada una](#-reglas-de-validación-y-quién-decidió-cada-una)
5. [Cómo está organizado el código](#-cómo-está-organizado-el-código)
6. [Casos borde: cuáles se manejan y cuáles no](#-casos-borde-cuáles-se-manejan-y-cuáles-no)
7. [Evidencia de pruebas](#-evidencia-de-pruebas)

---

## 🎯 Qué hace

Cada línea del log tiene este formato:

```
[NIVEL] AAAA-MM-DD mensaje
```

El script identifica el nivel (`INFO`, `WARNING` o `ERROR`), comprueba si la fecha existe y es válida, y genera un resumen con:

- Total de eventos.
- Cantidad de eventos por tipo.
- Número de líneas mal formateadas o incompletas, con su número de línea y el motivo.

**Ejemplo de salida:**

```
================================================================
 ANÁLISIS DE LOGS
================================================================
 Archivo: logs_prueba/log_con_errores.txt
 Líneas leídas: 13   (vacías ignoradas: 1)

 RESUMEN
   Total de eventos ............. 5
     INFO     ................. 2
     WARNING  ................. 2
     ERROR    ................. 1
   Eventos sin fecha ............ 1
   Líneas mal formateadas ....... 8   (1 de ellas también cuenta como evento)

 LÍNEAS MAL FORMATEADAS
   Línea   3: sin fecha
              [WARNING] Invalid password attempt
   Línea   4: nivel no válido: [DEBUG]
              [DEBUG] 2025-01-10 Cache warmed
   ...
```

---

## 🚀 Ejecución

**Requisitos:** Python 3.8 o superior (desarrollado y probado con Python 3.12). No necesita instalar librerías: usa solo la librería estándar.

```bash
# Con selector de archivos (abre una ventana para elegir el log)
python analizador_logs.py

# Indicando la ruta directamente
python analizador_logs.py logs_prueba/log_bueno.txt

# Ejecutar las pruebas automáticas
python -m unittest -v
```

Si el equipo no tiene entorno gráfico, el script pide la ruta por consola. Si el archivo no existe, es una carpeta, no se puede leer o está vacío, muestra un mensaje claro en lugar de fallar.

---

## 📁 Estructura del proyecto

```
analizador_logs/
├── analizador_logs.py       # Script principal
├── test_analizador.py       # Pruebas automáticas (16)
├── README.md                # Este documento
├── REFLEXION_TECNICA.md     # Documento de reflexión técnica
└── logs_prueba/             # Archivos de prueba
    ├── log_bueno.txt        # Todas las líneas bien formadas
    ├── log_con_errores.txt  # Mezcla de líneas válidas e inválidas
    ├── log_casos_borde.txt  # Casos límite (BOM, fechas imposibles, versiones...)
    └── log_vacio.txt        # Archivo vacío
```

---

## ⚖️ Reglas de validación y quién decidió cada una

La consigna indica que la IA **no debe definir por sí sola qué se considera una línea inválida**. Estas son las reglas del script y el origen de cada una:

| # | Regla | Origen |
|---|---|---|
| 1 | Nivel válido pero **sin fecha**: cuenta como evento **y** como mal formateada | **Decisión mía** |
| 2 | **Sin nivel válido** (sin corchetes o nivel distinto de INFO/WARNING/ERROR, como `[DEBUG]`): mal formateada y **no** cuenta como evento | **Decisión mía** |
| 3 | **Fecha incorrecta o imposible** (como `2025-13-45`): toda la línea es mal formateada y no cuenta como evento | **Decisión mía** (la IA propuso la interpretación de que no cuenta como evento; la confirmé) |
| 4 | Nivel y fecha válidos pero **sin mensaje**: mal formateada y no cuenta como evento | Propuesta de la IA, **confirmada por mí** |
| 5 | Los niveles distinguen **mayúsculas**: `[info]` es inválido | Propuesta de la IA, **confirmada por mí** |
| 6 | Las **líneas vacías** se ignoran: no son eventos ni errores | Propuesta de la IA, **confirmada por mí** |
| 7 | Solo se acepta fecha estricta **AAAA-MM-DD** | Propuesta de la IA, **confirmada por mí** |
| 8 | Algo "parece una fecha" solo si tiene un **año de 4 dígitos** (así `1.2.3` o una IP no se confunden con fechas) | **Decisión mía**, tomada al corregir una sugerencia mejorable de la IA (ver la reflexión técnica) |

Cada regla está marcada en los comentarios del código como `DECISIÓN DEL ESTUDIANTE`, y las constantes `COUNT_EVENT_IF_NO_DATE`, `COUNT_EVENT_IF_INVALID_DATE` y `COUNT_EVENT_IF_NO_MESSAGE` permiten cambiar el comportamiento sin reescribir la lógica.

---

## 🧩 Cómo está organizado el código

| Función | Para qué sirve |
|---|---|
| `choose_file()` | Obtiene la ruta del archivo: por argumento, con selector gráfico o escribiéndola |
| `read_lines(path)` | Lee el archivo (elimina la marca BOM y no falla por caracteres extraños) |
| `parse_line(number, raw)` | Analiza una línea: nivel, estado de la fecha, mensaje y problemas encontrados |
| `is_valid_date(token)` | Comprueba que la fecha tenga formato AAAA-MM-DD **y** exista en el calendario |
| `analyze(lines)` | Recorre todas las líneas y arma el resumen |
| `print_report(path, summary)` | Muestra el resultado en consola |
| `main()` | Orquesta el flujo y maneja errores de archivo |

---

## 🧪 Casos borde: cuáles se manejan y cuáles no

**Se manejan:**

- Líneas vacías o con solo espacios.
- Líneas con sangría o espacios sobrantes.
- Archivo con marca BOM al inicio.
- Fechas con formato correcto pero imposibles (`2025-02-30`, `2025-13-45`) y años bisiestos válidos (`2024-02-29`).
- Fechas con separadores o formato distintos (`2025/01/10`, `10-01-2025`, `2025-03-04T10:30:00`).
- Niveles en minúscula, vacíos (`[]`) o desconocidos (`[DEBUG]`).
- Mensajes con tildes, ñ y corchetes internos.
- Archivo inexistente, carpeta en lugar de archivo, sin permisos y archivo vacío.

**No se manejan (limitaciones conocidas):**

- **Eventos de varias líneas**, como un *stack trace*: cada línea se analiza de forma independiente.
- **La hora no se valida.** En `[INFO] 2025-03-04 10:30:00 mensaje`, la hora queda como parte del mensaje, por lo que `99:99:99` pasaría sin error.
- **Archivos muy grandes:** `read_lines` carga todo el archivo en memoria con `readlines()`.
- **Otros niveles** como `CRITICAL` o `DEBUG` se consideran inválidos; no hay una lista configurable desde fuera del código.
- **Archivos binarios:** no se detectan; el script intenta leerlos como texto.

---

## ✅ Evidencia de pruebas

Los resultados esperados se calcularon **a mano**, leyendo cada archivo y aplicando las reglas, **antes** de ejecutar el script. Luego se compararon con lo obtenido.

### Archivo 1: `log_bueno.txt` (bien formado)

10 líneas, todas con la forma `[NIVEL] AAAA-MM-DD mensaje`.

| Métrica | Esperado | Obtenido |
|---|---|---|
| Total de eventos | 10 | 10 |
| INFO / WARNING / ERROR | 5 / 2 / 3 | 5 / 2 / 3 |
| Líneas mal formateadas | 0 | 0 |

### Archivo 2: `log_con_errores.txt` (con errores e inconsistencias)

13 líneas, una de ellas vacía, con distintos tipos de error.

| Métrica | Esperado | Obtenido |
|---|---|---|
| Líneas leídas / vacías ignoradas | 13 / 1 | 13 / 1 |
| Total de eventos | 5 | 5 |
| INFO / WARNING / ERROR | 2 / 2 / 1 | 2 / 2 / 1 |
| Líneas mal formateadas | 8 | 8 |
| Mal formateadas que también cuentan como evento | 1 | 1 |

Detalle de las líneas mal formateadas:

| Línea | Contenido | Motivo detectado |
|---|---|---|
| 3 | `[WARNING] Invalid password attempt` | Sin fecha (cuenta también como evento) |
| 4 | `[DEBUG] 2025-01-10 Cache warmed` | Nivel no válido |
| 6 | `Texto suelto sin ningun formato` | Sin nivel entre corchetes |
| 7 | `[INFO] 2025-13-45 Date out of range` | Fecha inválida (mes 13) |
| 8 | `[ERROR] 2025/01/10 Wrong date separators` | Fecha inválida (separadores) |
| 9 | `[INFO] 2025-01-11` | Sin mensaje |
| 11 | `[error] 2025-01-11 Lowercase level` | Nivel no válido (minúscula) |
| 12 | `[ERROR]` | Sin fecha y sin mensaje |

### Archivo 3: `log_casos_borde.txt` (casos límite)

14 líneas con casos límite: BOM, sangría, `2025-02-30`, año bisiesto, tildes, versión `1.2.3`, número `404`, falta de espacio tras el corchete, nivel vacío, fecha con `T` y hora después de la fecha.

| Métrica | Esperado | Obtenido |
|---|---|---|
| Líneas leídas / vacías ignoradas | 14 / 1 | 14 / 1 |
| Total de eventos | 10 | 10 |
| INFO / WARNING / ERROR | 6 / 1 / 3 | 6 / 1 / 3 |
| Líneas mal formateadas | 5 (líneas 3, 6, 7, 11, 13) | 5 (líneas 3, 6, 7, 11, 13) |
| Mal formateadas que también cuentan como evento | 2 | 2 |

> **Nota sobre la corrección:** la primera versión del script daba 9 eventos en este archivo, porque descartaba `[INFO] 1.2.3 released` como "fecha inválida". Tras la decisión 8, se actualizó el resultado esperado a 10 eventos y el script pasó a cumplirlo. Está explicado en la reflexión técnica.

### Archivo 4: `log_vacio.txt` y errores de entrada

| Prueba | Esperado | Obtenido |
|---|---|---|
| Archivo vacío | Aviso de que no hay nada que analizar | "El archivo ... está vacío: no hay nada que analizar." |
| Archivo inexistente | Mensaje de error, sin colapsar | "Error: no existe el archivo ..." |
| Ruta que es una carpeta | Mensaje de error, sin colapsar | Mensaje de error y código de salida 1 |

### Pruebas automáticas

`test_analizador.py` contiene **16 pruebas** (`python -m unittest -v`) que verifican los tres logs, cada regla de validación, las líneas vacías y los errores de archivo. Resultado: **16 pruebas, todas correctas**.

### Pruebas manuales
- [x] Ejecuté el script sin argumentos y el selector de archivos se abrió.
- [x] Analicé los tres logs de `logs_prueba/` y los resultados coinciden con las tablas.
- [x] Creé un log propio con al menos tres líneas inventadas y revisé que el resultado tuviera sentido.
- [x] Probé una ruta inexistente y comprobé el mensaje de error.

---

*Desarrollado con IA como herramienta de apoyo · KODIGO Academy*
