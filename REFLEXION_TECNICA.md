# Reflexión técnica: IA como herramienta, no como autor

**Actividad:** Desarrollo guiado y validado de un script en Python (analizador de logs)
**Autor:** Jonathan Alberto · **Curso:** AI for Developers Jr. 4 · **IA de apoyo:** Claude (Anthropic)

---

## 1. Qué partes fueron sugeridas o apoyadas por la IA

La IA escribió el código del script a partir de las reglas que yo definí, y me apoyó en lo siguiente:

- **Expresiones regulares.** Propuso tres: una que separa el nivel entre corchetes del resto de la línea, una que detecta si algo "parece una fecha" y una que exige el formato estricto `AAAA-MM-DD`.
- **Estructura del código.** Sugirió dividirlo en funciones con una sola tarea cada una (`parse_line`, `analyze`, `print_report`, `read_lines`, `choose_file`) y usar dataclasses para representar una línea analizada y el resumen.
- **Selección del archivo.** Propuso aceptar la ruta por argumento, abrir un selector gráfico y, si no hay entorno gráfico, pedirla por consola.
- **Validación de fechas.** Sugirió apoyarse en `datetime.strptime` para rechazar fechas imposibles como `2025-02-30`.
- **Archivos y pruebas.** Generó los archivos de log de prueba y las 16 pruebas automáticas.
- **Manejo de errores de archivo** y el formato del reporte en consola.

## 2. Qué partes fueron decisión mía

La consigna pide que la IA no defina las reglas de validación, así que esas decisiones las tomé yo:

- **Línea sin fecha pero con nivel válido:** cuenta como evento **y** como mal formateada.
- **Línea sin nivel válido** (sin corchetes o con un nivel como `[DEBUG]`): mal formateada y **no** cuenta como evento.
- **Fecha incorrecta o imposible:** toda la línea se considera mal formateada.
- **Cuatro casos que yo no había definido** y para los que la IA propuso un valor por defecto, que revisé y confirmé: líneas sin mensaje (mal formateadas), niveles sensibles a mayúsculas, líneas vacías ignoradas y fecha estricta `AAAA-MM-DD`.
- **La corrección de la regla de fechas** (ver sección 3).
- **Qué casos borde manejar y cuáles no.** Decidimos manejar los comunes (líneas vacías, fechas imposibles, archivo inexistente) y dejar fuera los eventos de varias líneas y la validación de la hora, y los documenté como limitaciones.
- **Revisión y prueba del resultado** con logs propios.

En el código, cada regla está marcada como `DECISIÓN DEL ESTUDIANTE`, y los casos donde la IA propuso el valor figuran como "propuesta de la IA, confirmada".

## 3. Ejemplo concreto: una sugerencia mejorable y su corrección

**La sugerencia.** Para distinguir entre "no hay fecha" y "hay una fecha mal escrita", la IA propuso esta expresión regular: tres grupos numéricos separados por `-`, `/` o `.`.

```python
# Versión original 
DATE_LIKE_RE = re.compile(r"^\d{1,4}[-/.]\d{1,2}[-/.]\d{1,4}")
```

**El problema.** La regla era demasiado amplia. Una línea como `[INFO] 1.2.3 released`, que anuncia una versión de software y no tiene fecha, cumplía esa forma: el script la trataba como "fecha inválida" y la **descartaba** sin contarla como evento. En cambio, `[INFO] 404 pages not found` (que tampoco tiene fecha) se trataba bien: contaba como evento y como mal formateada, según mi regla 1. Dos líneas con el mismo defecto recibían tratamientos distintos.

**Cómo se detectó.** La propia IA señaló esta limitación cuando me presentó el script, y yo la comprobé ejecutando el programa sobre esa línea y sobre casos vecinos (una IP como `192.168.1.1`, el número `404`, fechas mal escritas). Es importante decirlo con claridad: **no fui yo quien la descubrió primero**; mi contribución fue entender por qué ocurría, decidir cómo resolverlo y validarlo.

**La decisión.** La IA me presentó tres caminos: hacer la regla más estricta, dejarlo como limitación documentada, o aceptar solo `AAAA-MM-DD` y tratar todo lo demás como "sin fecha". Elegí el primero, porque mantiene mi regla 3 (una fecha mal escrita convierte la línea en mal formateada) y a la vez corrige la inconsistencia.

**La corrección.** Exigir un año de 4 dígitos, al inicio o al final:

```python
# Versión corregida
DATE_LIKE_RE = re.compile(
    r"^(?:\d{4}[-/.]\d{1,2}[-/.]\d{1,2}|\d{1,2}[-/.]\d{1,2}[-/.]\d{4})(?!\d)"
)
```

**La validación.** Primero actualicé las pruebas con el comportamiento que quería y comprobé que **fallaban** (2 fallos), lo que confirmaba que el problema existía. Después cambié la expresión y las 16 pruebas pasaron. Ahora `1.2.3` y las IPs se tratan como "sin fecha", mientras que `2025-13-45` o `10-01-2025` siguen siendo fechas mal escritas. En el archivo `log_casos_borde.txt`, el resultado esperado pasó de 9 a 10 eventos.

## 4. Qué aprendí sobre usar la IA como herramienta y no como reemplazo


Aprendí que la IA es muy buena para producir código rápido, pero el código que produce tiene supuestos escondidos: las decisiones sobre qué es una línea válida son de negocio, no técnicas, y solo yo podía tomarlas. Si le hubiera pedido "hazme un analizador de logs" sin definir las reglas, habría decidido por mí cosas como si `[info]` es válido o si una línea sin fecha cuenta como evento, y yo habría entregado un código que no entiendo.

También aprendí que una sugerencia puede funcionar en los casos obvios y fallar en los límites, como con `1.2.3`. Por eso conviene probar con datos incómodos, no solo con ejemplos bonitos, y escribir las pruebas con el resultado que yo espero antes de ejecutar el código.

Por último, entendí que mi responsabilidad no es escribir cada línea, sino definir las reglas, revisar lo que se genera, probarlo y poder explicar por qué el código se comporta como lo hace.
