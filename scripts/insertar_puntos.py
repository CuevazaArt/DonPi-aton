"""Pone tres puntos de aguja en cada triangulo de las plantillas ya desdobladas."""

import math
import re
from collections import defaultdict
from pathlib import Path

from pypdf import PdfReader, PdfWriter
from pypdf.generic import DecodedStreamObject, NameObject

from marcas_doblez import puntos_de_cara

PLIEGUE = re.compile(r"([0-9.]+) ([0-9.]+) m ([0-9.]+) ([0-9.]+) l S")
BORDE = re.compile(r"((?:[0-9.]+ [0-9.]+ m |[0-9.]+ [0-9.]+ l )+)s")


def clave(x, y):
    return (round(float(x), 3), round(float(y), 3))


def grafo(texto):
    aristas = set()
    for a, b, c, d in PLIEGUE.findall(texto):
        p, q = clave(a, b), clave(c, d)
        if p != q:
            aristas.add(tuple(sorted((p, q))))
    extremos = {punto for arista in aristas for punto in arista}
    for path in BORDE.findall(texto)[:1]:
        puntos = [clave(x, y) for x, y in re.findall(r"([0-9.]+) ([0-9.]+)", path)]
        limpio = []
        for punto in puntos:
            if punto in extremos and (not limpio or limpio[-1] != punto):
                limpio.append(punto)
        for a, b in zip(limpio, limpio[1:] + limpio[:1]):
            if a != b:
                aristas.add(tuple(sorted((a, b))))
    vecinos = defaultdict(set)
    for a, b in aristas:
        vecinos[a].add(b)
        vecinos[b].add(a)
    return aristas, vecinos


def caras_de(texto):
    aristas, vecinos = grafo(texto)

    def une(a, b):
        return tuple(sorted((a, b))) in aristas

    triangulos = set()
    for a, bs in vecinos.items():
        lista = sorted(bs)
        for i, b in enumerate(lista):
            for c in lista[i + 1 :]:
                if une(b, c):
                    triangulos.add(tuple(sorted((a, b, c))))
    quads = set()
    for a, b in aristas:
        for c in vecinos[a]:
            if c == b:
                continue
            for d in vecinos[b]:
                if d in (a, c) or not une(c, d):
                    continue
                if une(a, d) or une(b, c):
                    continue
                quads.add(tuple(sorted((a, b, c, d))))
    caras = [list(tri) for tri in triangulos]
    for a, b, c, d in quads:
        caras.append([a, b, c, d])
    return caras


def _cerrar_isla(texto, inicio):
    profundidad = 0
    for hallado in re.finditer(r"\bq\b|\bQ\b", texto[inicio:]):
        if hallado.group() == "q":
            profundidad += 1
        else:
            profundidad -= 1
            if profundidad == 0:
                return inicio + hallado.start()
    return -1


def marcar(texto):
    piezas = list(re.finditer(r"q 1 0 0 1 ", texto))
    if not piezas:
        return texto, 0
    total = 0
    salida = []
    cursor = 0
    for pieza in piezas:
        fin = _cerrar_isla(texto, pieza.start())
        if fin < 0:
            continue
        isla = texto[pieza.start() : fin]
        caras = caras_de(isla)
        marcas = []
        for cara in caras:
            if len(cara) > 3:
                cx = sum(p[0] for p in cara) / len(cara)
                cy = sum(p[1] for p in cara) / len(cara)
                cara = sorted(cara, key=lambda p: math.atan2(p[1] - cy, p[0] - cx))
            if len(cara) == 3:
                grupos = [cara]
            else:
                grupos = [(cara[0], cara[i], cara[i + 1]) for i in range(1, len(cara) - 1)]
            for grupo in grupos:
                marcas.append(puntos_de_cara(grupo))
                total += 1
        bloque = "\n".join(marca for marca in marcas if marca)
        salida.append(texto[cursor:fin])
        if bloque:
            salida.append("\n" + bloque + "\n")
        cursor = fin
    salida.append(texto[cursor:])
    return "".join(salida), total


def procesar(pdf):
    lector = PdfReader(str(pdf))
    escritor = PdfWriter()
    total = 0
    for pagina in lector.pages:
        contenido = pagina.get_contents()
        if contenido is None:
            escritor.add_page(pagina)
            continue
        nuevo, cuenta = marcar(contenido.get_data().decode("latin1"))
        total += cuenta
        if cuenta:
            flujo = DecodedStreamObject()
            flujo.set_data(nuevo.encode("latin1"))
            pagina[NameObject("/Contents")] = flujo
        escritor.add_page(pagina)
    if total:
        escritor.write(str(pdf))
    return total


def main():
    raiz = Path(__file__).resolve().parents[1] / "salida" / "jabali" / "100cm_cabeza_carton_30grados_paleta_ceja"
    total = 0
    for pdf in sorted(raiz.glob("*.pdf")):
        if pdf.name.startswith(("00_", "mosaico")):
            continue
        cuenta = procesar(pdf)
        total += cuenta
        print(f"{pdf.name}: {cuenta} triangulos")
    print("TOTAL", total)


if __name__ == "__main__":
    main()
