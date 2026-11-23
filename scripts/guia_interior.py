"""Guia interior en espejo, solo lineas, a partir de la piel de oficio.

El dibujo va en espejo, incluida la letra que pertenece a la pieza.
Al voltear la hoja de izquierda a derecha sobre el carton, esa letra se lee
y los tres puntos coinciden con las agujas de la piel. Una franja arriba,
sin espejo, dice que hoja es para poder elegir cuales imprimir.

Uso:
  py -3 scripts/guia_interior.py
"""

import re
from pathlib import Path

from pypdf import PdfReader, PdfWriter
from pypdf.generic import DecodedStreamObject, DictionaryObject, NameObject, NumberObject

ROOT = Path(__file__).resolve().parents[1]
CARPETA = ROOT / "salida" / "jabali" / "100cm_cabeza_carton_30grados_paleta_ceja"
ORIGEN = CARPETA / "mosaico_oficio.pdf"
DESTINO = CARPETA / "mosaico_oficio_interior.pdf"
PT = 72 / 25.4
DIBUJO = re.compile(r"/[^\s/\[\]()<>]+[ \t]+Do\b")


def mm(valor):
    return valor * PT


def pdf_texto(texto):
    return texto.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")


def sin_textura(datos):
    if isinstance(datos, str):
        datos = datos.encode("latin1")
    texto = datos.decode("latin1")
    return DIBUJO.sub("", texto).encode("latin1")


def rotulos():
    lineas = (CARPETA / "MOSAICO.txt").read_text(encoding="utf-8").splitlines()
    corte = lineas.index("")
    return [linea for linea in lineas[corte + 1 :] if linea.strip()]


def fuentes():
    normal = DictionaryObject()
    normal[NameObject("/Type")] = NameObject("/Font")
    normal[NameObject("/Subtype")] = NameObject("/Type1")
    normal[NameObject("/BaseFont")] = NameObject("/Helvetica")
    negrita = DictionaryObject()
    negrita[NameObject("/Type")] = NameObject("/Font")
    negrita[NameObject("/Subtype")] = NameObject("/Type1")
    negrita[NameObject("/BaseFont")] = NameObject("/Helvetica-Bold")
    return normal, negrita


def asegurar_fuentes(pagina, normal, negrita):
    recursos = pagina["/Resources"].get_object()
    if "/Font" not in recursos:
        recursos[NameObject("/Font")] = DictionaryObject()
    fuentes_pagina = recursos["/Font"].get_object()
    fuentes_pagina[NameObject("/F1")] = normal
    fuentes_pagina[NameObject("/F2")] = negrita


def portada(ancho, alto, normal, negrita):
    from pypdf import PageObject

    lado = mm(100)
    x = (ancho - lado) / 2
    y = mm(28)
    lineas = [
        (mm(12), alto - mm(16), 16, "F2", "GUIA INTERIOR"),
        (mm(12), alto - mm(24), 11, "F2", "JABALI100"),
        (mm(12), alto - mm(34), 9, "F1", "Mismo desdoble que la piel, en espejo y solo con lineas."),
        (mm(12), alto - mm(40), 9, "F1", "No trae la textura de color."),
        (mm(12), alto - mm(50), 10, "F2", "COMO PEGARLA"),
        (mm(12), alto - mm(56), 8.5, "F1", "Imprime al 100 % en oficio, sin ajustar a la pagina."),
        (mm(12), alto - mm(61), 8.5, "F1", "Voltea la hoja de izquierda a derecha y pegala en la cara interna."),
        (mm(12), alto - mm(66), 8.5, "F1", "La tinta queda hacia el hueco. Las letras del dibujo se leen."),
        (mm(12), alto - mm(71), 8.5, "F1", "Los tres puntos caen en las agujas de la piel."),
        (mm(12), alto - mm(80), 10, "F2", "QUE IMPRIMIR"),
        (mm(12), alto - mm(86), 8.5, "F1", "La piel exterior se imprime completa."),
        (mm(12), alto - mm(91), 8.5, "F1", "Esta guia es a criterio, hoja por hoja o por pieza."),
        (mm(12), alto - mm(96), 8.5, "F1", "Conviene donde hay dobleces AFUERA."),
        (mm(12), alto - mm(101), 8.5, "F1", "Si una pieza no tiene AFUERA, puedes no imprimir esas hojas."),
        (mm(12), alto - mm(106), 8.5, "F1", "El rotulo de arriba se lee aqui para elegir. El numero de hoja es el de la piel."),
        (mm(12), alto - mm(115), 10, "F2", "CUADRADO"),
        (mm(12), alto - mm(121), 8.5, "F1", "El cuadrado de abajo mide 100 mm por dentro. Misma prueba de escala."),
        (x, y + lado + mm(4), 9, "F2", "Cuadrado de 100 mm. Mide el interior."),
    ]
    comandos = [
        "q 1.15 w 0 0 0 RG 0 0 0 rg",
        f"{x:.2f} {y:.2f} {lado:.2f} {lado:.2f} re S",
    ]
    for px, py, tamano, fuente, cadena in lineas:
        comandos.append(
            f"BT /{fuente} {tamano:.2f} Tf {px:.2f} {py:.2f} Td ({pdf_texto(cadena)}) Tj ET"
        )
    comandos.append("Q")
    pagina = PageObject.create_blank_page(width=ancho, height=alto)
    flujo = DecodedStreamObject()
    flujo.set_data("\n".join(comandos).encode("latin1"))
    pagina[NameObject("/Contents")] = flujo
    fuentes_pagina = DictionaryObject()
    fuentes_pagina[NameObject("/F1")] = normal
    fuentes_pagina[NameObject("/F2")] = negrita
    recursos = DictionaryObject()
    recursos[NameObject("/Font")] = fuentes_pagina
    pagina[NameObject("/Resources")] = recursos
    return pagina


def franja(ancho, alto, rotulo):
    texto = "INTERIOR  " + rotulo
    if len(texto) > 110:
        texto = texto[:107] + "..."
    alto_franja = mm(8)
    y = alto - alto_franja
    return (
        f"q 1 1 1 rg 0 {y:.2f} {ancho:.2f} {alto_franja:.2f} re f "
        f"0 0 0 rg BT /F2 8 Tf {mm(4):.2f} {y + mm(2.4):.2f} Td ({pdf_texto(texto)}) Tj ET Q\n"
    ).encode("latin1")


def main():
    lector = PdfReader(str(ORIGEN))
    nombres = rotulos()
    if len(nombres) != len(lector.pages):
        raise SystemExit(f"MOSAICO.txt tiene {len(nombres)} hojas y el PDF {len(lector.pages)}")
    normal, negrita = fuentes()
    escritor = PdfWriter()
    primera = lector.pages[0]
    ancho = float(primera.mediabox.width)
    alto = float(primera.mediabox.height)
    escritor.add_page(portada(ancho, alto, normal, negrita))
    for indice, pagina in enumerate(lector.pages):
        if indice == 0:
            continue
        datos = sin_textura(pagina.get_contents().get_data())
        ancho = float(pagina.mediabox.width)
        alto = float(pagina.mediabox.height)
        espejo = (
            f"q -1 0 0 1 {ancho:.3f} 0 cm\n".encode("latin1")
            + datos
            + b"\nQ\n"
            + franja(ancho, alto, nombres[indice])
        )
        flujo = DecodedStreamObject()
        flujo.set_data(espejo)
        pagina[NameObject("/Contents")] = flujo
        asegurar_fuentes(pagina, normal, negrita)
        escritor.add_page(pagina)
        print("HOJA", indice + 1, nombres[indice][:90])
    escritor.write(str(DESTINO))
    print("LISTO", DESTINO, "hojas", len(escritor.pages))


if __name__ == "__main__":
    main()
