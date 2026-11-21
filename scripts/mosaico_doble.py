"""Parte plantillas grandes en doble carta, a escala real, con solape.

El borde de la hoja no es un corte. El solape se alinea con la hoja vecina
y el corte sigue siendo la linea continua de la isla.

Uso:
  py -3 scripts/mosaico_doble.py --origen salida/dodo/carton_30grados_paleta
"""

import math
import re
import sys
from pathlib import Path

from pypdf import PageObject, PdfReader, PdfWriter, Transformation
from pypdf.generic import DecodedStreamObject, DictionaryObject, NameObject

ROOT = Path(__file__).resolve().parents[1]
HOJA_X_MM = 279.4
HOJA_Y_MM = 431.8
MARGEN_MM = 10.0
SOLAPE_MM = 15.0
FRANJA_MM = 6.0
PT = 72 / 25.4

TOKEN = re.compile(
    r"\((?:\\.|[^\\)])*\)|/[^\s\[\]()<>{}]+|"
    r"[+-]?(?:\d+\.\d*|\.\d+|\d+)(?:[eE][+-]?\d+)?|"
    r"[A-Za-z*]+|\[|\]"
)


def mm(valor):
    return valor * PT


def argumento(nombre, defecto):
    if nombre in sys.argv:
        return sys.argv[sys.argv.index(nombre) + 1]
    return defecto


def tokens(contenido):
    return TOKEN.findall(contenido)


def punto(ctm, x, y):
    a, b, c, d, e, f = ctm
    return a * x + c * y + e, b * x + d * y + f


def cajas_de_islas(pagina):
    contenido = pagina.get_contents()
    if contenido is None:
        return []
    datos = contenido.get_data()
    if isinstance(datos, bytes):
        texto = datos.decode("latin1")
    else:
        texto = "".join(parte.get_data().decode("latin1") for parte in datos)
    islas = []
    actual = None
    pila = []
    ctm = (1, 0, 0, 1, 0, 0)
    pila_numeros = []

    def anotar(x, y):
        if actual is not None:
            actual.append(punto(ctm, x, y))

    for token in tokens(texto):
        if token[:1] in "-+0123456789.":
            pila_numeros.append(float(token))
            continue
        if token == "q":
            pila.append(ctm)
            if len(pila) == 1:
                actual = []
        elif token == "Q" and pila:
            if len(pila) == 1 and actual:
                xs = [p[0] for p in actual]
                ys = [p[1] for p in actual]
                if xs:
                    islas.append((min(xs), min(ys), max(xs), max(ys)))
            ctm = pila.pop()
            if not pila:
                actual = None
        elif token == "cm" and len(pila_numeros) >= 6:
            a, b, c, d, e, f = pila_numeros[-6:]
            ca, cb, cc, cd, ce, cf = ctm
            ctm = (
                ca * a + cc * b,
                cb * a + cd * b,
                ca * c + cc * d,
                cb * c + cd * d,
                ca * e + cc * f + ce,
                cb * e + cd * f + cf,
            )
        elif token in ("m", "l") and len(pila_numeros) >= 2:
            anotar(pila_numeros[-2], pila_numeros[-1])
        elif token == "c" and len(pila_numeros) >= 6:
            for i in (-6, -4, -2):
                anotar(pila_numeros[i], pila_numeros[i + 1])
        elif token == "re" and len(pila_numeros) >= 4:
            x, y, w, h = pila_numeros[-4:]
            for dx, dy in ((0, 0), (w, 0), (0, h), (w, h)):
                anotar(x + dx, y + dy)
        elif token == "Do":
            for dx, dy in ((0, 0), (1, 0), (0, 1), (1, 1)):
                anotar(dx, dy)
        pila_numeros.clear()
    return islas


LETRAS = "ABCDEFGHJKLMNPQRSTUVWXYZ"


def clave(n):
    resto = n + 1
    digito_2 = resto % 10
    resto //= 10
    digito_1 = resto % 10
    resto //= 10
    letra_2 = resto % 24
    resto //= 24
    letra_1 = resto % 24
    return f"{LETRAS[letra_1]}{LETRAS[letra_2]}{digito_1}{digito_2}"


def pdf_texto(texto):
    return texto.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")


def marcas(ancho, alto, margen, texto, esquinas=None):
    x0, y0 = margen, margen + mm(FRANJA_MM)
    x1, y1 = ancho - margen, alto - margen
    t = mm(6)
    esquinas = esquinas or {}
    lineas = [
        f"{x0:.2f} {y0:.2f} m {x0+t:.2f} {y0:.2f} l {x0:.2f} {y0:.2f} m {x0:.2f} {y0+t:.2f} l S",
        f"{x1:.2f} {y0:.2f} m {x1-t:.2f} {y0:.2f} l {x1:.2f} {y0:.2f} m {x1:.2f} {y0+t:.2f} l S",
        f"{x0:.2f} {y1:.2f} m {x0+t:.2f} {y1:.2f} l {x0:.2f} {y1:.2f} m {x0:.2f} {y1-t:.2f} l S",
        f"{x1:.2f} {y1:.2f} m {x1-t:.2f} {y1:.2f} l {x1:.2f} {y1:.2f} m {x1:.2f} {y1-t:.2f} l S",
        f"BT /F1 8 Tf {margen + mm(2):.2f} {margen:.2f} Td ({pdf_texto(texto)}) Tj ET",
    ]
    anclas = {
        "bl": (x0 + mm(7), y0 + mm(1.2), 1, 1),
        "br": (x1 - mm(7), y0 + mm(1.2), -1, 1),
        "tl": (x0 + mm(7), y1 - mm(1.2), 1, -1),
        "tr": (x1 - mm(7), y1 - mm(1.2), -1, -1),
    }
    caja_w, caja_h = mm(15), mm(5)
    for nombre, codigo in esquinas.items():
        if not codigo:
            continue
        x_borde, y_borde, hacia_x, hacia_y = anclas[nombre]
        x = x_borde if hacia_x > 0 else x_borde - caja_w
        y = y_borde if hacia_y > 0 else y_borde - caja_h
        lineas.append(f"1 1 1 rg {x:.2f} {y:.2f} {caja_w:.2f} {caja_h:.2f} re f")
        lineas.append(
            f"0 0 0 rg BT /F1 10 Tf {x + mm(1.1):.2f} {y + mm(1.3):.2f} Td ({pdf_texto(codigo)}) Tj ET"
        )
    contenido = ("q 0.6 w 0 0 0 RG 0 0 0 rg\n" + "\n".join(lineas) + "\nQ").encode()
    flujo = DecodedStreamObject()
    flujo.set_data(contenido)
    pagina = PageObject.create_blank_page(width=ancho, height=alto)
    pagina[NameObject("/Contents")] = flujo
    fuente = DictionaryObject()
    fuente[NameObject("/Type")] = NameObject("/Font")
    fuente[NameObject("/Subtype")] = NameObject("/Type1")
    fuente[NameObject("/BaseFont")] = NameObject("/Helvetica")
    recursos = DictionaryObject()
    fuentes = DictionaryObject()
    fuentes[NameObject("/F1")] = fuente
    recursos[NameObject("/Font")] = fuentes
    pagina[NameObject("/Resources")] = recursos
    return pagina


def contar(largo, ventana, paso):
    if largo <= ventana + 0.5:
        return 1
    return int(math.ceil((largo - ventana) / paso)) + 1


def mosaico(origen, destino):
    origen = Path(origen)
    destino = Path(destino)
    destino.parent.mkdir(parents=True, exist_ok=True)
    hoja_x, hoja_y = mm(HOJA_X_MM), mm(HOJA_Y_MM)
    margen = mm(MARGEN_MM)
    solape = mm(SOLAPE_MM)
    ventana_x = hoja_x - 2 * margen
    ventana_y = hoja_y - 2 * margen - mm(FRANJA_MM)
    paso_x = ventana_x - solape
    paso_y = ventana_y - solape

    escritor = PdfWriter()
    indice = []
    piezas = []
    lectores = []
    prueba = origen / "00_prueba_100mm.pdf"
    if prueba.exists():
        lectores.append(PdfReader(str(prueba)))
        indice.append("00_prueba_100mm  el cuadrado interior mide 100 mm")
    archivos = sorted(
        ruta
        for ruta in origen.glob("*.pdf")
        if not ruta.name.startswith(("00_", "_", "mosaico"))
    )
    for archivo in archivos:
        lector = PdfReader(str(archivo))
        lectores.append(lector)
        for numero, pagina in enumerate(lector.pages, 1):
            cajas = cajas_de_islas(pagina)
            if not cajas:
                cajas = [(
                    float(pagina.mediabox.left),
                    float(pagina.mediabox.bottom),
                    float(pagina.mediabox.right),
                    float(pagina.mediabox.top),
                )]
            nombre = archivo.stem
            for n_isla, caja in enumerate(cajas, 1):
                x0, y0, x1, y1 = caja
                columnas = contar(x1 - x0, ventana_x, paso_x)
                filas = contar(y1 - y0, ventana_y, paso_y)
                for fila_visual in range(filas):
                    for columna in range(columnas):
                        piezas.append({
                            "pagina": pagina,
                            "x0": x0,
                            "y0": y0,
                            "fila": filas - 1 - fila_visual,
                            "fila_visual": fila_visual,
                            "columna": columna,
                            "filas": filas,
                            "columnas": columnas,
                            "nombre": nombre,
                            "isla": n_isla,
                            "pag": numero,
                            "texto": (
                                f"{nombre} isla {n_isla}  "
                                f"{fila_visual + 1}/{filas} x {columna + 1}/{columnas}"
                            ),
                        })

    juntas = {}
    for pieza in piezas:
        for esquina, fila_junta, col_junta in (
            ("tl", pieza["fila_visual"], pieza["columna"]),
            ("tr", pieza["fila_visual"], pieza["columna"] + 1),
            ("bl", pieza["fila_visual"] + 1, pieza["columna"]),
            ("br", pieza["fila_visual"] + 1, pieza["columna"] + 1),
        ):
            clave_junta = (pieza["nombre"], pieza["isla"], pieza["pag"], fila_junta, col_junta)
            juntas.setdefault(clave_junta, []).append((pieza, esquina))
    codigos = {}
    n = 0
    for clave_junta in sorted(juntas):
        if len(juntas[clave_junta]) < 2:
            continue
        codigos[clave_junta] = clave(n)
        n += 1
    for pieza in piezas:
        esquinas = {}
        for esquina, fila_junta, col_junta in (
            ("tl", pieza["fila_visual"], pieza["columna"]),
            ("tr", pieza["fila_visual"], pieza["columna"] + 1),
            ("bl", pieza["fila_visual"] + 1, pieza["columna"]),
            ("br", pieza["fila_visual"] + 1, pieza["columna"] + 1),
        ):
            clave_junta = (pieza["nombre"], pieza["isla"], pieza["pag"], fila_junta, col_junta)
            esquinas[esquina] = codigos.get(clave_junta, "")
        pieza["esquinas"] = esquinas

    if prueba.exists():
        pagina = lectores[0].pages[0]
        nueva = PageObject.create_blank_page(width=hoja_x, height=hoja_y)
        nueva.merge_transformed_page(pagina, Transformation())
        nueva.merge_page(marcas(hoja_x, hoja_y, margen, indice[0]))
        escritor.add_page(nueva)
        print("HOJA", 1, indice[0])
    for pieza in piezas:
        nueva = PageObject.create_blank_page(width=hoja_x, height=hoja_y)
        tx = margen - pieza["x0"] - pieza["columna"] * paso_x
        ty = margen + mm(FRANJA_MM) - pieza["y0"] - pieza["fila"] * paso_y
        nueva.merge_transformed_page(pieza["pagina"], Transformation().translate(tx, ty))
        nueva.merge_page(marcas(hoja_x, hoja_y, margen, pieza["texto"], pieza["esquinas"]))
        escritor.add_page(nueva)
        marcas_txt = "  ".join(
            f"{nombre.upper()} {pieza['esquinas'][nombre] or '-'}"
            for nombre in ("tl", "tr", "bl", "br")
        )
        linea = pieza["texto"] if pieza["pag"] == 1 else f"{pieza['texto']} pag {pieza['pag']}"
        indice.append(f"{linea}   {marcas_txt}")
        print("HOJA", len(indice), indice[-1])

    if not indice:
        raise SystemExit(f"No hay PDF en {origen}")
    escritor.write(str(destino))
    guia = destino.with_name("MOSAICO.txt")
    guia.write_text(
        "\n".join(
            [
                "Mosaico en doble carta, 279 x 432 mm, a escala real.",
                "Imprimir al 100 %, sin ajustar a la pagina.",
                f"Solape de {SOLAPE_MM:.0f} mm: la franja repetida se hace coincidir con la hoja vecina.",
                "Esa franja se pega. No se corta.",
                "Se corta solo la linea continua de la pieza. La punteada se dobla.",
                "Cada esquina que se junta con otra hoja lleva una clave de cuatro signos, por ejemplo AA23.",
                "La misma clave esta en la esquina de la hoja vecina. AA23 se junta con AA23.",
                "Las esquinas del borde exterior quedan sin clave.",
                "El texto de cada hoja dice la parte, la fila y la columna. La fila 1 es la de arriba.",
                "TL es la esquina superior izquierda, TR la superior derecha, BL la inferior izquierda y BR la inferior derecha.",
                "",
                *indice,
                "",
            ]
        ),
        encoding="utf-8",
    )
    print("LISTO", destino, "hojas", len(indice))


if __name__ == "__main__":
    mosaico(
        argumento("--origen", str(ROOT / "salida" / "dodo" / "carton_30grados_paleta")),
        argumento("--destino", str(ROOT / "salida" / "dodo" / "carton_30grados_paleta" / "mosaico_doble_carta.pdf")),
    )
