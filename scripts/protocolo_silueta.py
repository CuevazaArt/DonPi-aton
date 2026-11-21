"""Busca el equilibrio entre silueta y manufactura.

Prueba varios niveles de simplificación, por parte, y se queda con la
versión más simple cuya silueta sigue siendo la del original.

Uso:
  blender --background --python scripts/protocolo_silueta.py -- --modelo RUTA --alto 1
"""

import json
import sys
from pathlib import Path

import bmesh
import bpy
from mathutils import Matrix, Vector

ROOT = Path(__file__).resolve().parents[1]
SRC = Path(r"C:\Users\lexar\Downloads\dodo3d\dodo_block_anim.glb")
ALTO_M = 1.0
RESOLUCION = 160
UMBRAL_IOU = 0.93
BANDA_SILUETA = 0.015
TOLERANCIA_CAJA = 0.03
AREA_MINIMA = 0.90
HOJA_UTIL = (0.170, 0.210)
SOLAPA_M = 0.012

NOMBRES = {
    "dodo_body_DodoMat_0": "cuerpo",
    "dodo_head_DodoMat_0": "cabeza",
    "dodo_3_DodoMat_0": "pieza_frontal",
    "dodo_4_DodoMat_0": "pieza_lateral",
    "dodo_1_DodoMat_0": "pata_a_muslo",
    "dodo_11_DodoMat_0": "pata_a_canilla",
    "dodo_111_DodoMat_0": "pata_a_pie",
    "dodo_2_DodoMat_0": "pata_b_muslo",
    "dodo_22_DodoMat_0": "pata_b_canilla",
    "dodo_222_DodoMat_0": "pata_b_pie",
}

PASOS = [
    ("original", None),
    ("disolver_5", ("dissolve", 5)),
    ("disolver_15", ("dissolve", 15)),
    ("disolver_30", ("dissolve", 30)),
    ("disolver_15_y_colapsar_50", ("both", 15, 0.50)),
    ("disolver_15_y_colapsar_25", ("both", 15, 0.25)),
]

VISTAS = {"frente": (0, 2), "lado": (1, 2), "planta": (0, 1)}


def argumento(nombre, defecto):
    if "--" not in sys.argv:
        return defecto
    resto = sys.argv[sys.argv.index("--") + 1 :]
    if nombre in resto:
        return resto[resto.index(nombre) + 1]
    return defecto


def activar(obj):
    if bpy.context.mode != "OBJECT":
        bpy.ops.object.mode_set(mode="OBJECT")
    bpy.ops.object.select_all(action="DESELECT")
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj


def hornear(obj):
    matriz = obj.matrix_world.copy()
    obj.data = obj.data.copy()
    obj.parent = None
    obj.matrix_world = Matrix.Identity(4)
    for vertice in obj.data.vertices:
        vertice.co = matriz @ vertice.co


def cargar(ruta, alto):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.context.scene.unit_settings.system = "METRIC"
    bpy.context.scene.unit_settings.scale_length = 1.0
    bpy.ops.import_scene.gltf(filepath=str(ruta))
    piezas = [obj for obj in bpy.data.objects if obj.type == "MESH"]
    for obj in piezas:
        hornear(obj)
    for obj in list(bpy.data.objects):
        if obj.type != "MESH":
            bpy.data.objects.remove(obj, do_unlink=True)
    coordenadas = [v.co.copy() for obj in piezas for v in obj.data.vertices]
    minimo = Vector((min(v.x for v in coordenadas), min(v.y for v in coordenadas), min(v.z for v in coordenadas)))
    factor = alto / (max(v.z for v in coordenadas) - minimo.z)
    for obj in piezas:
        for vertice in obj.data.vertices:
            vertice.co = (vertice.co - minimo) * factor
        obj.name = NOMBRES.get(obj.name, obj.name)
        obj.data.name = obj.name
    return piezas


def copiar(piezas):
    copias = []
    for obj in piezas:
        nuevo = obj.copy()
        nuevo.data = obj.data.copy()
        nuevo.name = obj.name
        bpy.context.scene.collection.objects.link(nuevo)
        copias.append(nuevo)
    return copias


def borrar(piezas):
    for obj in piezas:
        malla = obj.data
        bpy.data.objects.remove(obj, do_unlink=True)
        if malla.users == 0:
            bpy.data.meshes.remove(malla)


def aplicar_modificador(obj, tipo, grados=0, ratio=1):
    modificador = obj.modifiers.new("simplificar", "DECIMATE")
    modificador.decimate_type = tipo
    if tipo == "DISSOLVE":
        modificador.angle_limit = grados * 3.1415926535 / 180.0
        modificador.use_dissolve_boundaries = False
    else:
        modificador.ratio = ratio
    activar(obj)
    bpy.ops.object.modifier_apply(modifier=modificador.name)


def simplificar(piezas, paso):
    if not paso:
        return
    modo = paso[0]
    for obj in piezas:
        if len(obj.data.polygons) < 6:
            continue
        if modo in ("dissolve", "both"):
            aplicar_modificador(obj, "DISSOLVE", grados=paso[1])
        if modo == "both" and len(obj.data.polygons) >= 8:
            aplicar_modificador(obj, "COLLAPSE", ratio=paso[2])


def caja_total(piezas):
    coordenadas = [v.co for obj in piezas for v in obj.data.vertices]
    return Vector(
        (
            max(v.x for v in coordenadas) - min(v.x for v in coordenadas),
            max(v.y for v in coordenadas) - min(v.y for v in coordenadas),
            max(v.z for v in coordenadas) - min(v.z for v in coordenadas),
        )
    )


def area_total(piezas):
    total = 0.0
    for obj in piezas:
        malla = bmesh.new()
        malla.from_mesh(obj.data)
        total += sum(cara.calc_area() for cara in malla.faces)
        malla.free()
    return total


def caras(piezas):
    return sum(len(obj.data.polygons) for obj in piezas)


def marcos(piezas):
    resultado = {}
    for nombre, (iu, iv) in VISTAS.items():
        us, vs = [], []
        for obj in piezas:
            for vertice in obj.data.vertices:
                coordenada = (vertice.co.x, vertice.co.y, vertice.co.z)
                us.append(coordenada[iu])
                vs.append(coordenada[iv])
        ancho = max(us) - min(us) or 0.01
        alto = max(vs) - min(vs) or 0.01
        resultado[nombre] = (min(us) - ancho * 0.08, max(us) + ancho * 0.08, min(vs) - alto * 0.08, max(vs) + alto * 0.08)
    return resultado


def pintar_triangulo(mascara, res, puntos):
    xs = [p[0] for p in puntos]
    ys = [p[1] for p in puntos]
    minx = max(int(min(xs)), 0)
    maxx = min(int(max(xs)) + 1, res - 1)
    miny = max(int(min(ys)), 0)
    maxy = min(int(max(ys)) + 1, res - 1)
    x0, y0 = puntos[0]
    x1, y1 = puntos[1]
    x2, y2 = puntos[2]
    denominador = (y1 - y2) * (x0 - x2) + (x2 - x1) * (y0 - y2)
    if abs(denominador) < 1e-8:
        return
    for y in range(miny, maxy + 1):
        py = y + 0.5
        fila = y * res
        for x in range(minx, maxx + 1):
            px = x + 0.5
            a = ((y1 - y2) * (px - x2) + (x2 - x1) * (py - y2)) / denominador
            b = ((y2 - y0) * (px - x2) + (x0 - x2) * (py - y2)) / denominador
            c = 1 - a - b
            if a >= -0.02 and b >= -0.02 and c >= -0.02:
                mascara[fila + x] = 1


def silueta(piezas, referencia):
    mascaras = {}
    for nombre, (iu, iv) in VISTAS.items():
        u0, u1, v0, v1 = referencia[nombre]
        mascara = bytearray(RESOLUCION * RESOLUCION)
        for obj in piezas:
            malla = bmesh.new()
            malla.from_mesh(obj.data)
            bmesh.ops.triangulate(malla, faces=malla.faces)
            for cara in malla.faces:
                puntos = []
                for vertice in cara.verts:
                    coordenada = (vertice.co.x, vertice.co.y, vertice.co.z)
                    puntos.append(
                        (
                            (coordenada[iu] - u0) / (u1 - u0) * (RESOLUCION - 1),
                            (coordenada[iv] - v0) / (v1 - v0) * (RESOLUCION - 1),
                        )
                    )
                pintar_triangulo(mascara, RESOLUCION, puntos)
            malla.free()
        mascaras[nombre] = mascara
    return mascaras


def iou(a, b):
    interseccion = sum(1 for izq, der in zip(a, b) if izq and der)
    union = sum(1 for izq, der in zip(a, b) if izq or der)
    if union == 0:
        return 1.0
    return interseccion / union


def extension_de_cara(cara):
    normal = cara.normal
    arista = None
    for loop in cara.loops:
        vector = loop.link_loop_next.vert.co - loop.vert.co
        if vector.length > 1e-8:
            arista = vector.normalized()
            break
    if arista is None:
        return 0.0, 0.0
    bitangente = normal.cross(arista)
    us, vs = [], []
    for vertice in cara.verts:
        us.append(vertice.co.dot(arista))
        vs.append(vertice.co.dot(bitangente))
    return max(us) - min(us), max(vs) - min(vs)


def estimar_hojas(piezas):
    page_w, page_h = HOJA_UTIL
    cajas = []
    for obj in piezas:
        malla = bmesh.new()
        malla.from_mesh(obj.data)
        for cara in malla.faces:
            ancho, alto = extension_de_cara(cara)
            ancho += 2 * SOLAPA_M
            alto += 2 * SOLAPA_M
            if ancho < alto and alto <= page_w and ancho <= page_h:
                ancho, alto = alto, ancho
            elif ancho > page_w and alto <= page_w and ancho <= page_h:
                ancho, alto = alto, ancho
            cajas.append((ancho, alto))
        malla.free()
    hojas = 0
    normales = []
    for ancho, alto in cajas:
        if ancho > page_w or alto > page_h:
            hojas += max(1, int(ancho / page_w + 0.999)) * max(1, int(alto / page_h + 0.999))
        else:
            normales.append((ancho, alto))
    normales.sort(key=lambda caja: -caja[1])
    x = page_w
    y = 0.0
    fila = 0.0
    if normales:
        hojas += 1
    for ancho, alto in normales:
        if x + ancho > page_w + 1e-6:
            y += fila
            x = 0.0
            fila = 0.0
            if y + alto > page_h + 1e-6:
                hojas += 1
                y = 0.0
        x += ancho
        fila = max(fila, alto)
    return hojas


def medir(piezas, base_caja, base_area, base_silueta, referencia):
    actual = caja_total(piezas)
    deltas = [abs(actual[i] - base_caja[i]) / base_caja[i] for i in range(3)]
    actual_silueta = silueta(piezas, referencia)
    vistas = {nombre: round(iou(base_silueta[nombre], actual_silueta[nombre]), 4) for nombre in VISTAS}
    return {
        "caras": caras(piezas),
        "area_m2": round(area_total(piezas), 3),
        "area_ratio": round(area_total(piezas) / base_area, 4),
        "caja_mm": [round(v * 1000) for v in actual],
        "caja_delta_max": round(max(deltas), 4),
        "iou": vistas,
        "iou_min": round(min(vistas.values()), 4),
        "hojas_estimadas": estimar_hojas(piezas),
    }


def elegir(filas):
    viables = [
        fila
        for fila in filas
        if "error" not in fila
        and fila["iou_min"] >= UMBRAL_IOU
        and fila["caja_delta_max"] <= TOLERANCIA_CAJA
        and fila["area_ratio"] >= AREA_MINIMA
    ]
    if not viables:
        return None, []
    mejor = max(fila["iou_min"] for fila in viables)
    banda = [fila for fila in viables if fila["iou_min"] >= mejor - BANDA_SILUETA]
    ganador = min(banda, key=lambda fila: (fila["caras"], fila["hojas_estimadas"], -fila["iou_min"]))
    return ganador, viables


def main():
    ruta = Path(argumento("--modelo", str(SRC)))
    alto = float(argumento("--alto", str(ALTO_M)))
    piezas = cargar(ruta, alto)
    referencia = marcos(piezas)
    base_silueta = silueta(piezas, referencia)
    base_caja = caja_total(piezas)
    base_area = area_total(piezas)
    filas = []
    for nombre, paso in PASOS:
        copias = copiar(piezas)
        try:
            simplificar(copias, paso)
            medida = medir(copias, base_caja, base_area, base_silueta, referencia)
            medida["nombre"] = nombre
        except Exception as exc:
            medida = {"nombre": nombre, "error": str(exc)}
        borrar(copias)
        filas.append(medida)
        print("NIVEL", medida)

    ganador, viables = elegir(filas)
    salida = Path(argumento("--salida", str(ROOT / "salida" / "dodo" / "protocolo")))
    salida.mkdir(parents=True, exist_ok=True)
    informe = {
        "modelo": str(ruta),
        "alto_m": alto,
        "reglas": {
            "silueta_minima": UMBRAL_IOU,
            "banda_de_empate": BANDA_SILUETA,
            "cambio_maximo_de_caja": TOLERANCIA_CAJA,
            "area_minima": AREA_MINIMA,
            "criterio": "Entre las versiones que conservan la silueta, la de menos caras.",
        },
        "niveles": filas,
        "viables": [fila["nombre"] for fila in viables],
        "elegido": None if ganador is None else ganador["nombre"],
    }
    (salida / "informe.json").write_text(json.dumps(informe, indent=2, ensure_ascii=False), encoding="utf-8")
    lineas = [
        "Protocolo de equilibrio silueta / manufactura",
        f"Modelo: {ruta.name}. Altura: {alto:.2f} m.",
        "Cada parte se simplifica sola. La silueta se compara de frente, de lado y desde arriba,",
        "sobre el recuadro del original. Una version es viable si la silueta minima queda",
        f"en {UMBRAL_IOU:.0%} o mas, la caja no cambia mas de {TOLERANCIA_CAJA:.0%} y el area",
        f"no baja de {AREA_MINIMA:.0%}. De esas, se elige la de menos caras que siga dentro",
        f"de {BANDA_SILUETA:.1%} de la mejor silueta.",
        "",
        f"{'nivel':32} {'caras':>6} {'iou':>6} {'caja':>6} {'hojas':>6}",
    ]
    for fila in filas:
        if "error" in fila:
            lineas.append(f"{fila['nombre']:32} ERROR {fila['error']}")
            continue
        lineas.append(
            f"{fila['nombre']:32} {fila['caras']:6} {fila['iou_min']:6.3f} {fila['caja_delta_max']:6.3f} {fila['hojas_estimadas']:6}"
        )
    lineas.append("")
    if ganador is None:
        lineas.append("Ningun nivel cumple la silueta. Se conserva el original.")
    else:
        lineas.append(
            f"Equilibrio: {ganador['nombre']}. Caras {ganador['caras']}. "
            f"Silueta minima {ganador['iou_min']:.3f}. Hojas estimadas {ganador['hojas_estimadas']}."
        )
    texto = "\n".join(lineas) + "\n"
    (salida / "informe.txt").write_text(texto, encoding="utf-8")
    print(texto)


if __name__ == "__main__":
    main()
