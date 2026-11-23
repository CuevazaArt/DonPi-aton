"""Desdobla el jabali para que la coronilla quede a 1 m del suelo.

Parte del modelo ya disuelto a 30 grados y 0.50 m de alto total.
La coronilla es el punto mas alto del cuerpo en el 30 % delantero,
desde el hocico. La montura puede quedar por encima de ese metro.
Las solapas salen en triangulo y la escala del dibujo es 1:1.

Uso:
  blender --background --python scripts/jabali_cabeza_1m.py
"""

import sys
from pathlib import Path

import bmesh
import bpy
from mathutils import Vector

sys.path.insert(0, str(Path(__file__).resolve().parent))
import generar_plantilla_dodo as gen

ROOT = Path(__file__).resolve().parents[1]
BLEND = ROOT / "modelos" / "jabali" / "jabali_50cm_30grados_paleta_ceja_carton.blend"
OUT = ROOT / "salida" / "jabali" / "100cm_cabeza_carton_30grados_paleta_ceja"
MODELOS = ROOT / "modelos" / "jabali"
ALTO_CABEZA_M = 1.0
FRENTE = 0.30


def piezas_del_modelo():
    return [
        obj
        for obj in bpy.data.objects
        if obj.type == "MESH" and not obj.name.startswith("00_")
    ]


def coronilla(cuerpo):
    """Punto mas alto del hocico y el craneo, sin la espalda ni la montura."""
    ys = [vertice.co.y for vertice in cuerpo.data.vertices]
    ymin, ymax = min(ys), max(ys)
    corte = ymin + (ymax - ymin) * FRENTE
    frente = [vertice.co for vertice in cuerpo.data.vertices if vertice.co.y <= corte]
    return max(punto.z for punto in frente), ymin, ymax, corte


def escalar(piezas, factor):
    for obj in piezas:
        for vertice in obj.data.vertices:
            vertice.co *= factor
        obj.data.update()


def main():
    sys.argv = [
        sys.argv[0],
        "--",
        "--carton",
        "--paleta",
        "--ceja-triangular",
        "--angulo",
        "30",
    ]
    OUT.mkdir(parents=True, exist_ok=True)
    bpy.ops.wm.open_mainfile(filepath=str(BLEND))
    gen.activar_desdoblador()
    gen.activar_ceja_triangular()

    for imagen in bpy.data.images:
        print("IMAGEN", imagen.name, tuple(imagen.size), imagen.filepath)

    piezas = piezas_del_modelo()
    for obj in piezas:
        gen.hornear_al_mundo(obj)

    cuerpo = next(obj for obj in piezas if obj.name == "01_cuerpo")
    alto_cabeza, ymin, ymax, corte = coronilla(cuerpo)
    factor = ALTO_CABEZA_M / alto_cabeza
    print(
        f"CABEZA antes {alto_cabeza:.4f} m  hocico Y {ymin:.4f}  "
        f"cola Y {ymax:.4f}  corte {corte:.4f}  factor {factor:.4f}"
    )
    escalar(piezas, factor)
    alto_cabeza, ymin, ymax, corte = coronilla(cuerpo)

    coordenadas = [vertice.co.copy() for obj in piezas for vertice in obj.data.vertices]
    minimo = Vector(
        (
            min(punto.x for punto in coordenadas),
            min(punto.y for punto in coordenadas),
            min(punto.z for punto in coordenadas),
        )
    )
    maximo = Vector(
        (
            max(punto.x for punto in coordenadas),
            max(punto.y for punto in coordenadas),
            max(punto.z for punto in coordenadas),
        )
    )
    medida = maximo - minimo
    print(
        f"CABEZA {alto_cabeza:.3f} m  "
        f"caja {medida.x:.3f} x {medida.y:.3f} x {medida.z:.3f} m"
    )

    lineas = []
    area_total = 0.0
    for obj in sorted(piezas, key=lambda item: item.name):
        lo, hi = gen.caja(obj)
        tamano = hi - lo
        superficie = gen.area(obj)
        area_total += superficie
        arista = 0.0
        malla = bmesh.new()
        malla.from_mesh(obj.data)
        for arista_malla in malla.edges:
            arista = max(arista, arista_malla.calc_length())
        malla.free()
        pdf = OUT / f"{obj.name}.pdf"
        estado = gen.desdoblar(obj, pdf)
        islas = gen.islas_de(pdf) if pdf.exists() else 0
        linea = (
            f"{obj.name}: {islas} islas {estado}; "
            f"{len(obj.data.polygons)} caras; "
            f"caja {tamano.x*1000:.0f} x {tamano.y*1000:.0f} x {tamano.z*1000:.0f} mm; "
            f"arista maxima {arista*1000:.0f} mm; "
            f"area {superficie:.3f} m2"
        )
        lineas.append(linea)
        print("PIEZA", linea)

    marca = "JABALI100"
    (OUT / "MARCA.txt").write_text(marca + "\n", encoding="utf-8")
    gen.guardar_referencia(piezas, OUT / "referencia.png")

    plano = bpy.data.objects.new("00_prueba_100mm", bpy.data.meshes.new("regla"))
    bpy.context.scene.collection.objects.link(plano)
    malla = bmesh.new()
    bmesh.ops.create_grid(malla, x_segments=1, y_segments=1, size=0.05)
    malla.to_mesh(plano.data)
    malla.free()
    estado = gen.desdoblar(plano, OUT / "00_prueba_100mm.pdf", textura=False, hoja=(gen.CARTA_X, gen.CARTA_Y))
    print("REGLA", estado, (OUT / "00_prueba_100mm.pdf").exists())

    for obj in piezas:
        gen.activar(obj)
    bpy.ops.object.select_all(action="DESELECT")
    for obj in piezas:
        obj.select_set(True)
    bpy.context.view_layer.objects.active = piezas[0]
    bpy.ops.wm.obj_export(
        filepath=str(MODELOS / "jabali_100cm_cabeza_30grados_paleta_ceja_carton.obj"),
        export_selected_objects=True,
        forward_axis="NEGATIVE_Y",
        up_axis="Z",
        global_scale=1000.0,
        export_materials=True,
        apply_modifiers=True,
    )
    bpy.ops.wm.save_as_mainfile(
        filepath=str(MODELOS / "jabali_100cm_cabeza_30grados_paleta_ceja_carton.blend")
    )

    cartulina = 1.22 * 2.44
    hojas_carton = area_total * 1.45 / cartulina
    credito = "\n".join(
        [
            'Obra derivada de "boar block  anim" por blam, CC BY 4.0.',
            "https://sketchfab.com/Blam577895",
            "https://sketchfab.com/3d-models/boar-block-anim-a294b1f7ea2241c6bf5245e7a4923366",
            "http://creativecommons.org/licenses/by/4.0/",
            "La licencia incluye un descargo de garantias: https://creativecommons.org/licenses/by/4.0/legalcode",
            "Cambios: escala para que la coronilla quede a 1.00 m, disolucion, paleta y plantilla de papel.",
            "blam y Sketchfab no patrocinan este proyecto.",
            "",
        ]
    )
    texto = "\n".join(
        [
            credito.rstrip(),
            "Jabali con la coronilla a 1.00 m del suelo, plantilla a escala real. Disolucion: 30 grados.",
            "La altura se mide en el cuerpo, en el 30 % delantero desde el hocico. La montura puede superar ese metro.",
            f"Coronilla: {alto_cabeza:.2f} m. Caja total: {medida.x:.2f} m de ancho, {medida.y:.2f} m de largo, {medida.z:.2f} m de alto.",
            "Las solapas de pegado pasan de trapecio a triangulo: se quita el lado corto exterior y la base sigue siendo el doblez. La malla conserva la disolucion.",
            f"Cada hoja de impresion lleva la palabra {marca}. Distingue este proyecto si las hojas se mezclan o se voltean.",
            "La hoja del cuadrado de 100 mm trae la figura armada. Esa imagen es referencia y no se corta.",
            "Cada PDF suelto es una lamina de carton de 1.22 x 2.44 m, a escala real.",
            "Para la impresora domestica usa mosaico_oficio.pdf, en oficio mexicano de 216 x 340 mm, al 100 %.",
            "La palabra JABALI100 va abajo a la derecha de cada hoja.",
            "La hoja 1 trae el cuadrado de 100 mm y, arriba, la figura armada. Esa imagen no se corta.",
            "La isla que cabe sale entera. La que no cabe se parte en mosaico, con 15 mm de solape.",
            "La lista hoja por hoja queda en MOSAICO.txt despues de correr scripts/mosaico_doble.py.",
            "El corte es el contorno de cada isla. El borde de la lamina no se recorta si no hay linea.",
            "Dentro de la isla, la linea continua se corta. La flecha con numero queda dentro de la cara, junto a la arista que nombra, para que el recorte no se la lleve.",
            "La raya larga, con la palabra AFUERA, es un doblez convexo: el canto queda hacia afuera y la cara impresa hace de lomo.",
            "Los puntos, con la palabra ADENTRO, son un doblez concavo: el canto queda hacia adentro.",
            "La flecha chica junto a esa palabra marca el sentido. AFUERA y ADENTRO apuntan a lados contrarios de la linea.",
            "Cada triangulo trae tres puntos. Una aguja en cada punto calza la plantilla del reverso y guia el corte y el doblez por el interior.",
            "En los dos casos la cara impresa queda afuera del volumen.",
            "00_prueba_100mm.pdf sigue siendo carta: el cuadrado interior tiene que medir 100 mm.",
            "Cada cara lleva la paleta alternativa del proyecto: grises a turquesa, tonos calidos a magenta, amarillos a verde lima. El negro se conserva.",
            "Las solapas quedan sin imagen para que se lean el corte, el doblez y el numero.",
            "Primero imprime 00_prueba_100mm.pdf y mide el cuadrado: tiene que dar 100 mm.",
            "Las solapas miden 12 mm. El numero de una arista se pega con el mismo numero.",
            "Recorta cada isla por su contorno, dobla las lineas punteadas y pega las solapas con el mismo numero.",
            "Las piezas son cascarones cerrados. Se unen entre si por la posicion del modelo.",
            f"Area de cartulina: {area_total:.2f} m2.",
            f"Con solapas y recorte, cerca de {hojas_carton:.1f} laminas de 1.22 x 2.44 m.",
            "La cola queda hacia +Y y el hocico hacia -Y. Las patas 1 y 3 estan del lado del hocico: la 1 en +X y la 3 en -X. Las patas 2 y 4 estan del lado de la cola.",
            "",
            *lineas,
            "",
        ]
    )
    (OUT / "CREDITOS.txt").write_text(credito, encoding="utf-8")
    (OUT / "LEEME.txt").write_text(texto, encoding="utf-8")
    print("LISTO", OUT)


if __name__ == "__main__":
    main()
