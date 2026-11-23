"""Acomoda las islas en la hoja pedida, a escala real.

Mision del curado: llenar lo mas posible cada hoja del formato de impresion,
sin cambiar la escala 1:1, para gastar menos papel. La isla que cabe sale
entera y comparte hoja. La que no cabe se parte en mosaico. El trozo que no
llena la hoja se junta con otros trozos en la misma hoja.

Uso:
  py -3 scripts/mosaico_doble.py --origen salida/jabali/40cm_carton_30grados_paleta_ceja
"""

import io
import math
import re
import sys
from pathlib import Path

from PIL import Image
from pypdf import PageObject, PdfReader, PdfWriter, Transformation
from pypdf.generic import DecodedStreamObject, DictionaryObject, NameObject, NumberObject, StreamObject

ROOT = Path(__file__).resolve().parents[1]
HOJA_X_MM = 279.4
HOJA_Y_MM = 431.8
# Oficio mexicano, 8.5 x 13.4 pulgadas.
OFICIO_X_MM = 215.9
OFICIO_Y_MM = 340.4
MARGEN_MM = 10.0
SOLAPE_MM = 15.0
FRANJA_MM = 6.0
SEPARACION_MM = 2.0
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


def limpiar_marca(texto):
    limpio = "".join(caracter for caracter in texto.upper() if caracter.isascii() and caracter.isalnum())
    return limpio[:16]


def marca_de(origen):
    if "--marca" in sys.argv:
        return limpiar_marca(argumento("--marca", ""))
    archivo = Path(origen) / "MARCA.txt"
    if archivo.exists():
        linea = archivo.read_text(encoding="utf-8").strip().split()
        if linea:
            return limpiar_marca(linea[0])
    carpeta = Path(origen)
    animal = limpiar_marca(carpeta.parent.name)
    alto = re.match(r"(\d+)cm_", carpeta.name)
    if animal and alto:
        return f"{animal}{alto.group(1)}"[:16]
    return animal or "PROYECTO"


def referencia_de(origen):
    if "--referencia" in sys.argv:
        return Path(argumento("--referencia", ""))
    archivo = Path(origen) / "referencia.png"
    return archivo if archivo.exists() else None


def marcas(ancho, alto, margen, texto, esquinas=None, proyecto=""):
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
    if proyecto:
        tamano = 14
        ancho_texto = len(proyecto) * tamano * 0.62
        x_palabra = max(margen, ancho - margen - ancho_texto)
        lineas.append(
            f"BT /F2 {tamano} Tf {x_palabra:.2f} {margen:.2f} Td ({pdf_texto(proyecto)}) Tj ET"
        )
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
    negrita = DictionaryObject()
    negrita[NameObject("/Type")] = NameObject("/Font")
    negrita[NameObject("/Subtype")] = NameObject("/Type1")
    negrita[NameObject("/BaseFont")] = NameObject("/Helvetica-Bold")
    recursos = DictionaryObject()
    fuentes = DictionaryObject()
    fuentes[NameObject("/F1")] = fuente
    fuentes[NameObject("/F2")] = negrita
    recursos[NameObject("/Font")] = fuentes
    pagina[NameObject("/Resources")] = recursos
    return pagina


def leer_medidas(origen):
    ruta = Path(origen) / "LEEME.txt"
    area, laminas, coronilla = "?", "?", ""
    if not ruta.exists():
        return area, laminas, coronilla
    texto = ruta.read_text(encoding="utf-8")
    hallado = re.search(r"Area de cartulina: ([0-9.]+) m2", texto)
    if hallado:
        area = hallado.group(1)
    hallado = re.search(r"cerca de ([0-9.]+) laminas", texto)
    if hallado:
        laminas = hallado.group(1)
    hallado = re.search(r"Coronilla: ([^\n]+)", texto)
    if hallado:
        coronilla = hallado.group(1)
    return area, laminas, coronilla


def _linea(x, y, cadena, tamano, fuente):
    return f"BT /{fuente} {tamano:.2f} Tf {x:.2f} {y:.2f} Td ({pdf_texto(cadena)}) Tj ET"


def construir_portada(ancho, alto, origen, proyecto, hojas, figura):
    """Hoja 1: cuadrado centrado, figura armada y la logica de corte y armado."""
    area, laminas, coronilla = leer_medidas(origen)
    papel_m2 = hojas * (ancho / PT) * (alto / PT) / 1e6
    compra = ""
    if laminas != "?":
        compra = f" Compra {int(float(laminas)) + 1}."
    lado = mm(100)
    x_cuadrado = (ancho - lado) / 2
    y_cuadrado = (alto - lado) / 2
    comandos = [
        "q 1.15 w 0 0 0 RG",
        f"{x_cuadrado:.2f} {y_cuadrado:.2f} {lado:.2f} {lado:.2f} re S",
        "Q",
        _linea(
            x_cuadrado,
            y_cuadrado + lado + mm(3.2),
            "Cuadrado de 100 mm, centrado. Mide el interior.",
            9,
            "F2",
        ),
        _linea(
            x_cuadrado,
            y_cuadrado - mm(5),
            "Si no da 100 mm, la impresora esta escalando. Corrigelo antes de seguir.",
            8,
            "F1",
        ),
    ]
    y = alto - mm(11)
    x_texto = mm(8)
    for cadena, tamano, fuente in (
        (proyecto, 13, "F2"),
        ("Plantilla a escala real. Imprimir al 100 %, sin ajustar a la pagina.", 8, "F1"),
        (coronilla or "La figura armada es referencia. No se corta.", 8, "F1"),
        ("La figura de la derecha no se corta.", 8, "F1"),
    ):
        comandos.append(_linea(x_texto, y, cadena, tamano, fuente))
        y -= mm(4.4 if tamano < 12 else 6)

    flujo_imagen = None
    if figura is not None and Path(figura).exists():
        imagen = Image.open(figura).convert("RGBA")
        fondo = Image.new("RGB", imagen.size, (255, 255, 255))
        fondo.paste(imagen, mask=imagen.getchannel("A"))
        imagen = fondo
        buffer = io.BytesIO()
        imagen.thumbnail((900, 700))
        imagen.save(buffer, format="JPEG", quality=80)
        datos = buffer.getvalue()
        flujo_imagen = StreamObject()
        flujo_imagen.set_data(datos)
        flujo_imagen.update(
            {
                NameObject("/Type"): NameObject("/XObject"),
                NameObject("/Subtype"): NameObject("/Image"),
                NameObject("/Width"): NumberObject(imagen.width),
                NameObject("/Height"): NumberObject(imagen.height),
                NameObject("/ColorSpace"): NameObject("/DeviceRGB"),
                NameObject("/BitsPerComponent"): NumberObject(8),
                NameObject("/Filter"): NameObject("/DCTDecode"),
            }
        )
        dibujo_ancho = mm(78)
        dibujo_alto = dibujo_ancho * imagen.height / imagen.width
        dibujo_x = ancho - mm(8) - dibujo_ancho
        dibujo_y = alto - mm(12) - dibujo_alto
        comandos.append(
            f"q {dibujo_ancho:.2f} 0 0 {dibujo_alto:.2f} {dibujo_x:.2f} {dibujo_y:.2f} cm /ImRef Do Q"
        )
        comandos.append(
            _linea(dibujo_x, dibujo_y - mm(4), "Figura armada. No se corta.", 7.5, "F1")
        )

    y = y_cuadrado - mm(12)
    instrucciones = [
        "PAPEL Y CARTON",
        f"Papel: {hojas} hojas, unas {papel_m2:.1f} m2. Si pegas el reverso, imprime este PDF otra vez.",
        f"Carton de las caras: {area} m2. Con solapas, cerca de {laminas} laminas de 1.22 x 2.44 m.{compra}",
        "CORTES Y SENAS",
        "Linea continua: se corta. Es el contorno y los dos lados de la solapa.",
        "AFUERA, raya larga, flecha a un lado: doblez convexo. El canto queda hacia afuera.",
        "La cara impresa hace de lomo.",
        "ADENTRO, puntos, flecha al lado contrario: doblez concavo. El canto queda hacia adentro.",
        "Tres puntos en cada triangulo: clava una aguja en cada uno, atravesando el carton.",
        "Esas agujas calzan la segunda plantilla por el otro lado, si hace falta pegarla.",
        "Por el interior, los puntos marcan el triangulo para cortar y doblar desde ese lado.",
        "ARMADO",
        "El numero se pega con el mismo numero. La solapa es un triangulo de 12 mm y se pega por dentro.",
        "La cara impresa queda afuera. Se dobla hacia el hueco de la pinata.",
        "El solape de 15 mm se pega por el reverso. No se corta. Cada clave se junta con la misma clave.",
        "Cierra cada cascaron y luego junta las piezas por su forma.",
    ]
    for cadena in instrucciones:
        fuente, tamano = ("F2", 8) if cadena.isupper() else ("F1", 7.4)
        comandos.append(_linea(mm(8), y, cadena, tamano, fuente))
        y -= mm(3.15 if fuente == "F1" else 4.0)

    contenido = ("q 0 0 0 rg\n" + "\n".join(comandos) + "\nQ").encode()
    flujo = DecodedStreamObject()
    flujo.set_data(contenido)
    pagina = PageObject.create_blank_page(width=ancho, height=alto)
    pagina[NameObject("/Contents")] = flujo
    fuente = DictionaryObject()
    fuente[NameObject("/Type")] = NameObject("/Font")
    fuente[NameObject("/Subtype")] = NameObject("/Type1")
    fuente[NameObject("/BaseFont")] = NameObject("/Helvetica")
    negrita = DictionaryObject()
    negrita[NameObject("/Type")] = NameObject("/Font")
    negrita[NameObject("/Subtype")] = NameObject("/Type1")
    negrita[NameObject("/BaseFont")] = NameObject("/Helvetica-Bold")
    fuentes = DictionaryObject()
    fuentes[NameObject("/F1")] = fuente
    fuentes[NameObject("/F2")] = negrita
    recursos = DictionaryObject()
    recursos[NameObject("/Font")] = fuentes
    if flujo_imagen is not None:
        imagenes = DictionaryObject()
        imagenes[NameObject("/ImRef")] = flujo_imagen
        recursos[NameObject("/XObject")] = imagenes
    pagina[NameObject("/Resources")] = recursos
    return pagina


def figura_armada(ancho, alto, ruta, proyecto):
    """Coloca la vista del modelo armado encima del cuadrado, sin taparlo."""
    imagen = Image.open(ruta).convert("RGBA")
    fondo = Image.new("RGB", imagen.size, (255, 255, 255))
    fondo.paste(imagen, mask=imagen.getchannel("A"))
    imagen = fondo
    buffer = io.BytesIO()
    imagen.thumbnail((900, 700))
    imagen.save(buffer, format="JPEG", quality=80)
    datos = buffer.getvalue()
    flujo_imagen = StreamObject()
    flujo_imagen.set_data(datos)
    flujo_imagen.update(
        {
            NameObject("/Type"): NameObject("/XObject"),
            NameObject("/Subtype"): NameObject("/Image"),
            NameObject("/Width"): NumberObject(imagen.width),
            NameObject("/Height"): NumberObject(imagen.height),
            NameObject("/ColorSpace"): NameObject("/DeviceRGB"),
            NameObject("/BitsPerComponent"): NumberObject(8),
            NameObject("/Filter"): NameObject("/DCTDecode"),
        }
    )
    carta_alto = mm(279.4)
    x0, x1 = mm(10), ancho - mm(10)
    y0, y1 = carta_alto + mm(14), alto - mm(12)
    proporcion = imagen.width / imagen.height
    caja_ancho, caja_alto = x1 - x0, y1 - y0
    if caja_ancho / caja_alto > proporcion:
        dibujo_alto = caja_alto
        dibujo_ancho = dibujo_alto * proporcion
    else:
        dibujo_ancho = caja_ancho
        dibujo_alto = dibujo_ancho / proporcion
    dibujo_x = x0 + (caja_ancho - dibujo_ancho) / 2
    dibujo_y = y0 + (caja_alto - dibujo_alto) / 2
    leyenda = f"{proyecto}  figura armada, no se corta"
    contenido = (
        f"q {dibujo_ancho:.2f} 0 0 {dibujo_alto:.2f} {dibujo_x:.2f} {dibujo_y:.2f} cm /ImRef Do Q\n"
        f"BT /F1 11 Tf {(ancho - len(leyenda) * 11 * 0.5) / 2:.2f} {carta_alto + mm(3):.2f} Td ({pdf_texto(leyenda)}) Tj ET"
    ).encode()
    flujo = DecodedStreamObject()
    flujo.set_data(contenido)
    pagina = PageObject.create_blank_page(width=ancho, height=alto)
    pagina[NameObject("/Contents")] = flujo
    fuente = DictionaryObject()
    fuente[NameObject("/Type")] = NameObject("/Font")
    fuente[NameObject("/Subtype")] = NameObject("/Type1")
    fuente[NameObject("/BaseFont")] = NameObject("/Helvetica")
    fuentes = DictionaryObject()
    fuentes[NameObject("/F1")] = fuente
    imagenes = DictionaryObject()
    imagenes[NameObject("/ImRef")] = flujo_imagen
    recursos = DictionaryObject()
    recursos[NameObject("/Font")] = fuentes
    recursos[NameObject("/XObject")] = imagenes
    pagina[NameObject("/Resources")] = recursos
    return pagina


def contar(largo, ventana, paso):
    if largo <= ventana + 0.5:
        return 1
    return int(math.ceil((largo - ventana) / paso)) + 1


def rotulo(nombre, isla):
    base = nombre.split("_", 1)[-1].replace("_", " ")
    if nombre.startswith("01_"):
        return f"cuerpo {isla}"
    return base


def interseccion(a, b):
    x0, y0 = max(a[0], b[0]), max(a[1], b[1])
    x1, y1 = min(a[2], b[2]), min(a[3], b[3])
    if x1 - x0 < 1 or y1 - y0 < 1:
        return None
    return x0, y0, x1, y1


def aplicar_recorte(pagina, caja):
    contenido = pagina.get_contents()
    if contenido is None:
        return
    datos = contenido.get_data()
    if isinstance(datos, str):
        datos = datos.encode("latin1")
    x0, y0, x1, y1 = caja
    recorte = f"q {x0:.3f} {y0:.3f} {x1 - x0:.3f} {y1 - y0:.3f} re W n\n".encode()
    flujo = DecodedStreamObject()
    flujo.set_data(recorte + datos + b"\nQ\n")
    pagina.replace_contents(flujo)


def colocar(destino, origen, caja, dest_x, dest_y, gira, visible):
    """Pone una isla en la hoja. El giro es de 90° y no cambia la escala."""
    x0, y0, x1, y1 = caja
    ancho, alto = x1 - x0, y1 - y0
    if gira:
        rect = (dest_x, dest_y, dest_x + alto, dest_y + ancho)
        matriz = Transformation((0, 1, -1, 0, dest_x + y1, dest_y - x0))
    else:
        rect = (dest_x, dest_y, dest_x + ancho, dest_y + alto)
        matriz = Transformation().translate(dest_x - x0, dest_y - y0)
    recorte = interseccion(rect, visible)
    if recorte is None:
        return False
    temporal = PageObject.create_blank_page(
        width=float(destino.mediabox.width),
        height=float(destino.mediabox.height),
    )
    temporal.merge_transformed_page(origen, matriz)
    aplicar_recorte(temporal, recorte)
    destino.merge_page(temporal)
    return True


class Cajon:
    """Empaca recuadros en el área útil. La y crece hacia abajo."""

    def __init__(self, ancho, alto, separacion):
        self.libres = [(0.0, 0.0, ancho, alto)]
        self.separacion = separacion
        self.piezas = []

    def _podar(self, rects):
        salida = []
        for candidato in rects:
            if candidato[2] < 1 or candidato[3] < 1:
                continue
            ax, ay, aw, ah = candidato
            contenido = False
            for otro in rects:
                if candidato is otro:
                    continue
                bx, by, bw, bh = otro
                if (
                    ax >= bx - 0.05
                    and ay >= by - 0.05
                    and ax + aw <= bx + bw + 0.05
                    and ay + ah <= by + bh + 0.05
                    and aw * ah < bw * bh - 0.1
                ):
                    contenido = True
                    break
            if not contenido:
                salida.append(candidato)
        return salida

    def colocar(self, ancho, alto, dato):
        mejor = None
        for x, y, libre_x, libre_y in self.libres:
            if ancho <= libre_x + 0.05 and alto <= libre_y + 0.05:
                puntaje = (min(libre_x - ancho, libre_y - alto), libre_x * libre_y - ancho * alto)
                if mejor is None or puntaje < mejor[0]:
                    mejor = (puntaje, x, y)
        if mejor is None:
            return False
        _, x, y = mejor
        self.piezas.append({**dato, "x": x, "y": y, "pw": ancho, "ph": alto})
        ocupado_x, ocupado_y = ancho + self.separacion, alto + self.separacion
        nuevo = []
        for rx, ry, rw, rh in self.libres:
            if x >= rx + rw or x + ocupado_x <= rx or y >= ry + rh or y + ocupado_y <= ry:
                nuevo.append((rx, ry, rw, rh))
                continue
            if x > rx:
                nuevo.append((rx, ry, x - rx, rh))
            if x + ocupado_x < rx + rw:
                nuevo.append((x + ocupado_x, ry, rx + rw - (x + ocupado_x), rh))
            if y > ry:
                nuevo.append((rx, ry, rw, y - ry))
            if y + ocupado_y < ry + rh:
                nuevo.append((rx, y + ocupado_y, rw, ry + rh - (y + ocupado_y)))
        self.libres = self._podar(nuevo)
        return True


def cabe_en(ancho, alto, ventana_x, ventana_y):
    return ancho <= ventana_x + 0.5 and alto <= ventana_y + 0.5


def empaquetar(islas, ventana_x, ventana_y, separacion):
    cajones = []
    for isla in sorted(islas, key=lambda item: item["w"] * item["h"], reverse=True):
        opciones = []
        if cabe_en(isla["w"], isla["h"], ventana_x, ventana_y):
            opciones.append((isla["w"], isla["h"], False))
        if cabe_en(isla["h"], isla["w"], ventana_x, ventana_y):
            opciones.append((isla["h"], isla["w"], True))
        puesto = False
        for cajon in cajones:
            for ancho, alto, gira in sorted(opciones, key=lambda opcion: (opcion[1], opcion[0])):
                if cajon.colocar(ancho, alto, {**isla, "gira": gira}):
                    puesto = True
                    break
            if puesto:
                break
        if not puesto:
            cajon = Cajon(ventana_x, ventana_y, separacion)
            cajones.append(cajon)
            for ancho, alto, gira in sorted(opciones, key=lambda opcion: (-opcion[0] * opcion[1], opcion[1])):
                if cajon.colocar(ancho, alto, {**isla, "gira": gira}):
                    break
    return cajones


def tamano_celda(pieza, paso_x, paso_y, ventana_x, ventana_y):
    """Ancho y alto reales del trozo, ya girado. El ultimo de la fila o la columna es mas chico."""
    if pieza["gira"]:
        largo_x, largo_y = pieza["h"], pieza["w"]
    else:
        largo_x, largo_y = pieza["w"], pieza["h"]
    ancho = min(ventana_x, largo_x - pieza["columna"] * paso_x)
    alto = min(ventana_y, largo_y - pieza["fila"] * paso_y)
    return max(ancho, 1.0), max(alto, 1.0)


def celda_llena(ancho, alto, ventana_x, ventana_y):
    return ancho >= ventana_x - 1 and alto >= ventana_y - 1


def empaquetar_fijo(piezas, ventana_x, ventana_y, separacion):
    """Mete trozos ya orientados. No los gira: el mosaico ya eligio el giro."""
    cajones = []
    for pieza in sorted(piezas, key=lambda item: item["tw"] * item["th"], reverse=True):
        puesto = False
        for cajon in cajones:
            if cajon.colocar(pieza["tw"], pieza["th"], pieza):
                puesto = True
                break
        if not puesto:
            cajon = Cajon(ventana_x, ventana_y, separacion)
            cajones.append(cajon)
            cajon.colocar(pieza["tw"], pieza["th"], pieza)
    return cajones


def colocar_celda(destino, pieza, px, py, paso_x, paso_y, margen, franja):
    """El trozo que caeria en la ventana de su casilla se pone en (px, py)."""
    dest_x = margen - pieza["columna"] * paso_x + (px - margen)
    dest_y = margen + franja - pieza["fila"] * paso_y + (py - (margen + franja))
    return colocar(
        destino,
        pieza["pagina"],
        (pieza["x0"], pieza["y0"], pieza["x1"], pieza["y1"]),
        dest_x,
        dest_y,
        pieza["gira"],
        (px, py, px + pieza["tw"], py + pieza["th"]),
    )


def claves_en_celda(hoja_x, hoja_y, x, y, ancho, alto, esquinas):
    """La clave va en la esquina del trozo, no en la de la hoja."""
    if not esquinas:
        return []
    t = mm(1.4)
    caja_w, caja_h = mm(14), mm(4.6)
    anclas = {
        "bl": (x + mm(1.2), y + mm(1.2), 1, 1),
        "br": (x + ancho - mm(1.2), y + mm(1.2), -1, 1),
        "tl": (x + mm(1.2), y + alto - mm(1.2), 1, -1),
        "tr": (x + ancho - mm(1.2), y + alto - mm(1.2), -1, -1),
    }
    lineas = []
    for nombre, codigo in esquinas.items():
        if not codigo:
            continue
        bx, by, hacia_x, hacia_y = anclas[nombre]
        cx = bx if hacia_x > 0 else bx - caja_w
        cy = by if hacia_y > 0 else by - caja_h
        lineas.append(f"1 1 1 rg {cx:.2f} {cy:.2f} {caja_w:.2f} {caja_h:.2f} re f")
        lineas.append(
            f"0 0 0 rg BT /F1 8 Tf {cx + mm(0.8):.2f} {cy + mm(1.2):.2f} Td ({pdf_texto(codigo)}) Tj ET"
        )
        lineas.append(
            f"0 0 0 RG {bx:.2f} {by:.2f} m {bx + hacia_x * t:.2f} {by:.2f} l {bx:.2f} {by:.2f} m {bx:.2f} {by + hacia_y * t:.2f} l S"
        )
    if not lineas:
        return []
    contenido = ("q 0.5 w\n" + "\n".join(lineas) + "\nQ").encode()
    flujo = DecodedStreamObject()
    flujo.set_data(contenido)
    pagina = PageObject.create_blank_page(width=hoja_x, height=hoja_y)
    pagina[NameObject("/Contents")] = flujo
    fuente = DictionaryObject()
    fuente[NameObject("/Type")] = NameObject("/Font")
    fuente[NameObject("/Subtype")] = NameObject("/Type1")
    fuente[NameObject("/BaseFont")] = NameObject("/Helvetica")
    fuentes = DictionaryObject()
    fuentes[NameObject("/F1")] = fuente
    recursos = DictionaryObject()
    recursos[NameObject("/Font")] = fuentes
    pagina[NameObject("/Resources")] = recursos
    return pagina


def orientacion(isla, ventana_x, ventana_y, paso_x, paso_y):
    normal = contar(isla["w"], ventana_x, paso_x) * contar(isla["h"], ventana_y, paso_y)
    girada = contar(isla["h"], ventana_x, paso_x) * contar(isla["w"], ventana_y, paso_y)
    gira = girada < normal
    if gira:
        return True, contar(isla["h"], ventana_x, paso_x), contar(isla["w"], ventana_y, paso_y)
    return False, contar(isla["w"], ventana_x, paso_x), contar(isla["h"], ventana_y, paso_y)


def tamano_hoja():
    pedido = argumento("--hoja", "doble").lower()
    if pedido in ("oficio", "oficio-mx", "mexicano"):
        return OFICIO_X_MM, OFICIO_Y_MM, "Oficio mexicano, 216 x 340 mm, a escala real."
    return HOJA_X_MM, HOJA_Y_MM, "Doble carta, 279 x 432 mm, a escala real."


def mosaico(origen, destino):
    origen = Path(origen)
    destino = Path(destino)
    destino.parent.mkdir(parents=True, exist_ok=True)
    hoja_mm_x, hoja_mm_y, titulo_hoja = tamano_hoja()
    hoja_x, hoja_y = mm(hoja_mm_x), mm(hoja_mm_y)
    margen = mm(MARGEN_MM)
    solape = mm(SOLAPE_MM)
    ventana_x = hoja_x - 2 * margen
    ventana_y = hoja_y - 2 * margen - mm(FRANJA_MM)
    paso_x = ventana_x - solape
    paso_y = ventana_y - solape

    escritor = PdfWriter()
    proyecto = marca_de(origen)
    figura = referencia_de(origen)
    indice = ["portada  cuadrado de 100 mm centrado, figura armada e instrucciones"]
    islas = []
    lectores = []
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
                islas.append({
                    "pagina": pagina,
                    "x0": x0,
                    "y0": y0,
                    "x1": x1,
                    "y1": y1,
                    "w": x1 - x0,
                    "h": y1 - y0,
                    "nombre": nombre,
                    "isla": n_isla,
                    "pag": numero,
                })

    enteras = [
        isla for isla in islas
        if cabe_en(isla["w"], isla["h"], ventana_x, ventana_y)
        or cabe_en(isla["h"], isla["w"], ventana_x, ventana_y)
    ]
    grandes = [isla for isla in islas if isla not in enteras]
    cajones = empaquetar(enteras, ventana_x, ventana_y, mm(SEPARACION_MM))
    franja = mm(FRANJA_MM)
    visible = (margen, margen + franja, margen + ventana_x, margen + franja + ventana_y)

    piezas = []
    for isla in grandes:
        gira, columnas, filas = orientacion(isla, ventana_x, ventana_y, paso_x, paso_y)
        for fila_visual in range(filas):
            for columna in range(columnas):
                piezas.append({
                    **isla,
                    "gira": gira,
                    "fila": filas - 1 - fila_visual,
                    "fila_visual": fila_visual,
                    "columna": columna,
                    "filas": filas,
                    "columnas": columnas,
                    "texto": (
                        f"{isla['nombre']} isla {isla['isla']}  "
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

    for pieza in piezas:
        pieza["tw"], pieza["th"] = tamano_celda(pieza, paso_x, paso_y, ventana_x, ventana_y)
    completas = [pieza for pieza in piezas if celda_llena(pieza["tw"], pieza["th"], ventana_x, ventana_y)]
    parciales = [pieza for pieza in piezas if pieza not in completas]
    cajones_parciales = empaquetar_fijo(parciales, ventana_x, ventana_y, mm(SEPARACION_MM))

    hojas = []
    print("HOJA", 1, indice[0])
    for cajon in cajones:
        nueva = PageObject.create_blank_page(width=hoja_x, height=hoja_y)
        nombres = []
        for pieza in sorted(cajon.piezas, key=lambda item: (item["y"], item["x"])):
            dest_x = margen + pieza["x"]
            dest_y = margen + franja + ventana_y - pieza["y"] - pieza["ph"]
            colocar(
                nueva,
                pieza["pagina"],
                (pieza["x0"], pieza["y0"], pieza["x1"], pieza["y1"]),
                dest_x,
                dest_y,
                pieza["gira"],
                visible,
            )
            nombres.append(rotulo(pieza["nombre"], pieza["isla"]))
        texto = " · ".join(nombres)
        nueva.merge_page(marcas(hoja_x, hoja_y, margen, texto, proyecto=proyecto))
        hojas.append(nueva)
        indice.append(f"islas enteras  {texto}")
        print("HOJA", len(indice), indice[-1])

    def publicar_trozo(nueva, pieza, px, py):
        colocar_celda(nueva, pieza, px, py, paso_x, paso_y, margen, franja)
        claves = claves_en_celda(hoja_x, hoja_y, px, py, pieza["tw"], pieza["th"], pieza["esquinas"])
        if claves:
            nueva.merge_page(claves)

    for pieza in completas:
        nueva = PageObject.create_blank_page(width=hoja_x, height=hoja_y)
        publicar_trozo(nueva, pieza, margen, margen + franja)
        nueva.merge_page(marcas(hoja_x, hoja_y, margen, pieza["texto"], proyecto=proyecto))
        hojas.append(nueva)
        marcas_txt = "  ".join(
            f"{nombre.upper()} {pieza['esquinas'][nombre] or '-'}"
            for nombre in ("tl", "tr", "bl", "br")
        )
        linea = pieza["texto"] if pieza["pag"] == 1 else f"{pieza['texto']} pag {pieza['pag']}"
        indice.append(f"mosaico  {linea}   {marcas_txt}")
        print("HOJA", len(indice), indice[-1])
    for cajon in cajones_parciales:
        nueva = PageObject.create_blank_page(width=hoja_x, height=hoja_y)
        nombres = []
        for pieza in sorted(cajon.piezas, key=lambda item: (item["y"], item["x"])):
            px = margen + pieza["x"]
            py = margen + franja + ventana_y - pieza["y"] - pieza["ph"]
            publicar_trozo(nueva, pieza, px, py)
            linea = pieza["texto"] if pieza["pag"] == 1 else f"{pieza['texto']} pag {pieza['pag']}"
            nombres.append(linea)
        texto = " · ".join(rotulo(pieza["nombre"], pieza["isla"]) for pieza in cajon.piezas)
        nueva.merge_page(marcas(hoja_x, hoja_y, margen, texto[:180], proyecto=proyecto))
        hojas.append(nueva)
        indice.append("mosaico compartido  " + " | ".join(nombres))
        print("HOJA", len(indice), indice[-1])

    if len(indice) < 2 and not hojas:
        raise SystemExit(f"No hay PDF en {origen}")
    escritor.add_page(construir_portada(hoja_x, hoja_y, origen, proyecto, len(indice), figura))
    for hoja in hojas:
        escritor.add_page(hoja)
    escritor.write(str(destino))
    guia = destino.with_name("MOSAICO.txt")
    guia.write_text(
        "\n".join(
            [
                titulo_hoja,
                "Imprimir al 100 %, sin ajustar a la pagina.",
                f"Cada hoja lleva la palabra {proyecto}. Identifica este proyecto si las hojas se mezclan o se voltean.",
                "La hoja 1 trae el cuadrado de 100 mm centrado, la figura armada y las instrucciones.",
                "La figura armada no se corta. El interior del cuadrado tiene que medir 100 mm.",
                "Cada triangulo trae tres puntos. Una aguja en cada punto calza la plantilla del reverso.",
                "La hoja marcada como islas enteras trae una o varias islas completas.",
                "Cada una se corta por su contorno. Entre ellas hay 2 mm. Esa separacion no se pega.",
                "La hoja marcada como mosaico es un trozo de una isla que no cupo.",
                "La hoja marcada como mosaico compartido junta varios trozos para no dejar la hoja vacia.",
                f"Solape de {SOLAPE_MM:.0f} mm: la franja repetida se hace coincidir con la hoja vecina.",
                "Esa franja se pega. No se corta.",
                "Se corta solo la linea continua de la pieza. La punteada se dobla.",
                "Cada esquina que se junta con otra hoja lleva una clave de cuatro signos, por ejemplo AA23.",
                "La misma clave esta en la esquina de la hoja vecina. AA23 se junta con AA23.",
                "Las esquinas del borde exterior, y las hojas de islas enteras, quedan sin clave.",
                "En el mosaico, la fila 1 es la de arriba.",
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
