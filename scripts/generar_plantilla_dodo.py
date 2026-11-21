"""Escala el dodo a 1 m de alto y desdobla cada pieza en hojas carta.

Uso:
  blender --background --python scripts/generar_plantilla_dodo.py
"""

import importlib.util
import sys
import zlib
from pathlib import Path

import bmesh
import bpy
from mathutils import Matrix, Vector

ROOT = Path(__file__).resolve().parents[1]
SRC = Path(r"C:\Users\lexar\Downloads\dodo3d\dodo_block_anim.glb")
ADDON = Path(__file__).resolve().parent / "io_export_paper_model.py"
OUT = ROOT / "salida" / "dodo" / "carta"
MODELOS = ROOT / "modelos" / "dodo"
ALTO_M = 1.0
# Una arista tiene que caber en el área útil de la carta, ya con margen y solapa.
CORTE_ARISTA_M = 0.15
CARTA_X = 0.2159
CARTA_Y = 0.2794
# Doble carta, 11 x 17 pulgadas.
DOBLE_X = 0.2794
DOBLE_Y = 0.4318
CARTON_X = 1.22
CARTON_Y = 2.44
MARGEN_M = 0.010
SOLAPA_M = 0.012

JABALI_NOMBRES = {
    "hog_body_HogMAt_0": "01_cuerpo",
    "hog_tail_HogMAt_0": "02_cola",
    "Sedlo_SedloMat_0": "03_montura",
    "hog_1_HogMAt_0": "04_pata_1_muslo",
    "hog_11_HogMAt_0": "05_pata_1_canilla",
    "hog_111_HogMAt_0": "06_pata_1_pie",
    "hog_3_HogMAt_0": "07_pata_3_muslo",
    "hog_33_HogMAt_0": "08_pata_3_canilla",
    "hog_333_HogMAt_0": "09_pata_3_pie",
    "hog_2_HogMAt_0": "10_pata_2_muslo",
    "hog_22_HogMAt_0": "11_pata_2_canilla",
    "hog_222_HogMAt_0": "12_pata_2_pie",
    "hog_4_HogMAt_0": "13_pata_4_muslo",
    "hog_44_HogMAt_0": "14_pata_4_canilla",
    "hog_444_HogMAt_0": "15_pata_4_pie",
}

NOMBRES = {
    "dodo_body_DodoMat_0": "01_cuerpo",
    "dodo_head_DodoMat_0": "02_cabeza",
    "dodo_3_DodoMat_0": "03_pieza_frontal",
    "dodo_4_DodoMat_0": "04_pieza_lateral",
    "dodo_1_DodoMat_0": "05_pata_a_muslo",
    "dodo_11_DodoMat_0": "06_pata_a_canilla",
    "dodo_111_DodoMat_0": "07_pata_a_pie",
    "dodo_2_DodoMat_0": "08_pata_b_muslo",
    "dodo_22_DodoMat_0": "09_pata_b_canilla",
    "dodo_222_DodoMat_0": "10_pata_b_pie",
}

COLORES = {
    "01_cuerpo": (0.85, 0.55, 0.20, 1),
    "02_cabeza": (0.95, 0.80, 0.25, 1),
    "03_pieza_frontal": (0.75, 0.35, 0.20, 1),
    "04_pieza_lateral": (0.55, 0.35, 0.70, 1),
    "05_pata_a_muslo": (0.30, 0.55, 0.85, 1),
    "06_pata_a_canilla": (0.25, 0.70, 0.75, 1),
    "07_pata_a_pie": (0.20, 0.45, 0.55, 1),
    "08_pata_b_muslo": (0.85, 0.35, 0.45, 1),
    "09_pata_b_canilla": (0.90, 0.55, 0.60, 1),
    "10_pata_b_pie": (0.60, 0.25, 0.30, 1),
}


def activar_desdoblador():
    spec = importlib.util.spec_from_file_location("io_export_paper_model", ADDON)
    mod = importlib.util.module_from_spec(spec)
    sys.modules["io_export_paper_model"] = mod
    spec.loader.exec_module(mod)
    for cls in mod.module_classes:
        bpy.utils.register_class(cls)
    bpy.types.Scene.paper_model = bpy.props.PointerProperty(
        name="Paper Model", type=mod.PaperModelSettings, options={"SKIP_SAVE"}
    )
    bpy.types.Mesh.paper_island_list = bpy.props.CollectionProperty(type=mod.IslandList)
    bpy.types.Mesh.paper_island_index = bpy.props.IntProperty(
        name="Island List Index",
        default=-1,
        min=-1,
        options={"SKIP_SAVE"},
        update=mod.island_index_changed,
    )

    def etiquetar_islas(self):
        objeto = bpy.context.active_object
        for numero, isla in enumerate(self.islands, 1):
            isla.number = numero
            cara = next(iter(isla.faces))
            nombre = "pieza"
            if objeto and cara.material_index < len(objeto.material_slots):
                material = objeto.material_slots[cara.material_index].material
                if material:
                    nombre = material.name
            isla.generate_label(label=nombre, abbreviation=str(numero))

    mod.Mesh.enumerate_islands = etiquetar_islas


def activar(obj):
    if bpy.context.mode != "OBJECT":
        bpy.ops.object.mode_set(mode="OBJECT")
    bpy.ops.object.select_all(action="DESELECT")
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj


def hornear_al_mundo(obj):
    matriz = obj.matrix_world.copy()
    obj.data = obj.data.copy()
    obj.parent = None
    obj.matrix_world = Matrix.Identity(4)
    for vertice in obj.data.vertices:
        vertice.co = matriz @ vertice.co


def partir_aristas_largas(obj, limite):
    malla = bmesh.new()
    malla.from_mesh(obj.data)
    bmesh.ops.remove_doubles(malla, verts=malla.verts, dist=1e-5)
    for _ in range(6):
        largas = [arista for arista in malla.edges if arista.calc_length() > limite]
        if not largas:
            break
        bmesh.ops.subdivide_edges(malla, edges=largas, cuts=1)
    def torcida(cara):
        if len(cara.verts) <= 3:
            return False
        centro = cara.calc_center_median()
        plano = centro.dot(cara.normal)
        diametro = max((centro - vertice.co).length for vertice in cara.verts)
        limite = max(1e-4, 0.01 * diametro)
        return any(abs(vertice.co.dot(cara.normal) - plano) > limite for vertice in cara.verts)

    irregular = [cara for cara in malla.faces if len(cara.verts) > 4 or torcida(cara)]
    if irregular:
        bmesh.ops.triangulate(malla, faces=irregular)
    bmesh.ops.recalc_face_normals(malla, faces=malla.faces)
    malla.to_mesh(obj.data)
    obj.data.update()
    malla.free()


def caja(obj):
    coordenadas = [vertice.co for vertice in obj.data.vertices]
    minimo = Vector(
        (
            min(v.x for v in coordenadas),
            min(v.y for v in coordenadas),
            min(v.z for v in coordenadas),
        )
    )
    maximo = Vector(
        (
            max(v.x for v in coordenadas),
            max(v.y for v in coordenadas),
            max(v.z for v in coordenadas),
        )
    )
    return minimo, maximo


def area(obj):
    total = 0.0
    malla = bmesh.new()
    malla.from_mesh(obj.data)
    for cara in malla.faces:
        total += cara.calc_area()
    malla.free()
    return total


def disolver_planos(obj, grados):
    antes = len(obj.data.polygons)
    if grados <= 0:
        return antes, antes
    modificador = obj.modifiers.new("disolver", "DECIMATE")
    modificador.decimate_type = "DISSOLVE"
    modificador.angle_limit = grados * 3.1415926535 / 180.0
    modificador.use_dissolve_boundaries = False
    activar(obj)
    bpy.ops.object.modifier_apply(modifier=modificador.name)
    return antes, len(obj.data.polygons)


def ceja_triangular_pedida():
    return "--ceja-triangular" in resto_argv()


def activar_ceja_triangular():
    sys.modules["io_export_paper_model"].CEJA_TRIANGULAR = ceja_triangular_pedida()


def resto_argv():
    if "--" not in sys.argv:
        return []
    return sys.argv[sys.argv.index("--") + 1 :]


def argumento(nombre, defecto):
    resto = resto_argv()
    if nombre in resto:
        return resto[resto.index(nombre) + 1]
    return defecto


def angulo_pedido():
    resto = resto_argv()
    if "--angulo" in resto:
        return float(resto[resto.index("--angulo") + 1])
    if hoja_doble():
        return 45.0
    return 0.0


def fusion_m():
    resto = resto_argv()
    if "--fusion" in resto:
        return float(resto[resto.index("--fusion") + 1]) / 1000.0
    if hoja_doble():
        return 0.008
    return 0.0


def fusionar(obj, distancia):
    malla = bmesh.new()
    malla.from_mesh(obj.data)
    bmesh.ops.remove_doubles(malla, verts=malla.verts, dist=distancia)
    malla.to_mesh(obj.data)
    obj.data.update()
    malla.free()


def con_textura():
    return "--textura" in resto_argv() or "--paleta" in resto_argv()


def paleta_pedida():
    return "--paleta" in resto_argv()


def hoja_carton():
    return "--carton" in resto_argv()


def hoja_doble():
    return "--doble" in resto_argv()


def tamano_hoja():
    if hoja_carton():
        return CARTON_X, CARTON_Y
    if hoja_doble():
        return DOBLE_X, DOBLE_Y
    return CARTA_X, CARTA_Y


def limite_arista():
    if hoja_carton() or hoja_doble():
        ancho, alto = tamano_hoja()
        util_x = ancho - 2 * MARGEN_M - 2 * SOLAPA_M
        util_y = alto - 2 * MARGEN_M - 2 * SOLAPA_M - 0.016
        return (util_x ** 2 + util_y ** 2) ** 0.5 * 0.90
    return CORTE_ARISTA_M


def paginas_de(pdf):
    datos = Path(pdf).read_bytes()
    indice = datos.find(b"/Count ")
    if indice < 0:
        return 0
    fin = indice + len(b"/Count ")
    digitos = []
    while fin < len(datos) and 48 <= datos[fin] <= 57:
        digitos.append(chr(datos[fin]))
        fin += 1
    return int("".join(digitos) or "0")


def islas_de(pdf):
    datos = Path(pdf).read_bytes()
    total = 0
    posicion = 0
    while True:
        inicio = datos.find(b"stream\n", posicion)
        if inicio < 0:
            break
        inicio += len(b"stream\n")
        fin = datos.find(b"\nendstream", inicio)
        if fin < 0:
            break
        posicion = fin + len(b"\nendstream")
        try:
            texto = zlib.decompress(datos[inicio:fin]).decode("latin1")
        except zlib.error:
            continue
        total += texto.count("q 1 0 0 1")
    return total


def hsv_a_rgb(tono, saturacion, valor):
    tono = (tono % 1.0) * 6.0
    sector = int(tono)
    fraccion = tono - sector
    p = valor * (1.0 - saturacion)
    q = valor * (1.0 - fraccion * saturacion)
    t = valor * (1.0 - (1.0 - fraccion) * saturacion)
    return (
        (valor, t, p),
        (q, valor, p),
        (p, valor, t),
        (p, q, valor),
        (t, p, valor),
        (valor, p, q),
    )[sector % 6]


def color_paleta(rojo, verde, azul):
    """Cuerpo turquesa, pico y patas magenta, cara verde lima. El negro del ojo se conserva."""
    mayor = max(rojo, verde, azul)
    menor = min(rojo, verde, azul)
    if mayor < 0.14:
        return 0.0, 0.0, 0.0
    croma = mayor - menor
    if croma < 22 / 255 and mayor > 0.90:
        return rojo, verde, azul
    if croma < 28 / 255:
        return hsv_a_rgb(0.50, 0.62, mayor)
    if azul > rojo + 10 / 255 and azul >= verde - 8 / 255:
        return hsv_a_rgb(0.62, 0.55, mayor)
    if verde > rojo * 0.78 and rojo > 160 / 255 and azul < 170 / 255:
        return hsv_a_rgb(0.24, 0.82, min(1.0, mayor))
    return hsv_a_rgb(0.86, 0.72, min(1.0, mayor))


def aplicar_paleta():
    for imagen in bpy.data.images:
        if imagen.size[0] == 0:
            continue
        pixeles = list(imagen.pixels)
        for indice in range(0, len(pixeles), 4):
            rojo, verde, azul = color_paleta(pixeles[indice], pixeles[indice + 1], pixeles[indice + 2])
            pixeles[indice] = rojo
            pixeles[indice + 1] = verde
            pixeles[indice + 2] = azul
        imagen.pixels.foreach_set(pixeles)
        imagen.update()
        print("PALETA", imagen.name, tuple(imagen.size))


def pintar(obj, color):
    material = bpy.data.materials.new(obj.name)
    material.diffuse_color = color
    material.use_nodes = True
    nodo = material.node_tree.nodes.get("Principled BSDF")
    if nodo:
        nodo.inputs["Base Color"].default_value = color
    obj.data.materials.clear()
    obj.data.materials.append(material)


def desdoblar(obj, destino, textura=None, hoja=None):
    if textura is None:
        textura = con_textura()
    if hoja is None:
        hoja = tamano_hoja()
    ancho, alto = hoja
    activar(obj)
    escena = bpy.context.scene
    papel = escena.paper_model
    papel.limit_by_page = True
    papel.use_auto_scale = False
    papel.scale = 1
    # Cada isla cabe en la hoja, ya descontados el margen y la solapa.
    papel.output_size_x = ancho - 2 * MARGEN_M - 2 * SOLAPA_M
    papel.output_size_y = alto - 2 * MARGEN_M - 2 * SOLAPA_M - 0.016
    resultado = bpy.ops.export_mesh.paper_model(
        filepath=str(destino),
        page_size_preset="USER",
        output_size_x=ancho,
        output_size_y=alto,
        output_margin=MARGEN_M,
        output_type="TEXTURE" if textura else "NONE",
        output_dpi=110 if textura and max(ancho, alto) > 0.5 else 150,
        do_create_stickers=True,
        do_create_numbers=True,
        sticker_width=SOLAPA_M,
        file_format="PDF",
        scale=1.0,
    )
    return set(resultado)


def unir(objetos):
    activo = objetos[0]
    activar(activo)
    for obj in objetos:
        obj.select_set(True)
    bpy.ops.object.join()
    return bpy.context.view_layer.objects.active


def main():
    global OUT, MODELOS
    animal = argumento("--animal", "dodo")
    alto_pedido = float(argumento("--alto", str(ALTO_M)))
    origen = Path(argumento("--modelo", str(SRC)))
    nombres = JABALI_NOMBRES if animal == "jabali" else NOMBRES
    angulo = angulo_pedido()
    sufijo = f"_{int(angulo)}grados" if angulo else ""
    if paleta_pedida():
        sufijo += "_paleta"
    elif con_textura():
        sufijo += "_textura"
    if ceja_triangular_pedida():
        sufijo += "_ceja"
    if hoja_carton():
        carpeta = "carton"
        sufijo += "_carton"
    elif hoja_doble():
        carpeta = "doble"
        sufijo += "_doble"
    else:
        carpeta = "carta"
    OUT = ROOT / "salida" / animal / f"{carpeta}{sufijo.replace('_carton', '').replace('_doble', '')}"
    MODELOS = ROOT / "modelos" / animal
    OUT.mkdir(parents=True, exist_ok=True)
    MODELOS.mkdir(parents=True, exist_ok=True)
    activar_desdoblador()
    activar_ceja_triangular()

    bpy.ops.wm.read_factory_settings(use_empty=True)
    escena = bpy.context.scene
    escena.unit_settings.system = "METRIC"
    escena.unit_settings.scale_length = 1.0
    bpy.ops.import_scene.gltf(filepath=str(origen))
    if paleta_pedida():
        aplicar_paleta()

    piezas = [obj for obj in bpy.data.objects if obj.type == "MESH"]
    for obj in piezas:
        hornear_al_mundo(obj)
    for obj in list(bpy.data.objects):
        if obj.type != "MESH":
            bpy.data.objects.remove(obj, do_unlink=True)

    coordenadas = [v.co.copy() for obj in piezas for v in obj.data.vertices]
    minimo = Vector(
        (
            min(v.x for v in coordenadas),
            min(v.y for v in coordenadas),
            min(v.z for v in coordenadas),
        )
    )
    alto = max(v.z for v in coordenadas) - minimo.z
    factor = alto_pedido / alto
    for obj in piezas:
        for vertice in obj.data.vertices:
            vertice.co = (vertice.co - minimo) * factor

    caras_antes = 0
    caras_despues = 0
    for obj in piezas:
        if fusion_m() > 0:
            fusionar(obj, fusion_m())
        antes, despues = disolver_planos(obj, angulo)
        caras_antes += antes
        caras_despues += despues
        print(f"DISUELTO {obj.name}: {antes} -> {despues}")
        partir_aristas_largas(obj, limite_arista())
        nombre = nombres.get(obj.name, obj.name)
        obj.name = nombre
        obj.data.name = nombre
        if not con_textura():
            pintar(obj, COLORES.get(nombre, (0.8, 0.8, 0.8, 1)))
        else:
            print(
                "TEXTURA",
                obj.name,
                "uv",
                len(obj.data.uv_layers),
                "material",
                [slot.material.name for slot in obj.material_slots if slot.material],
            )

    lineas = []
    area_total = 0.0
    for obj in sorted(piezas, key=lambda item: item.name):
        lo, hi = caja(obj)
        medida = hi - lo
        superficie = area(obj)
        area_total += superficie
        arista = 0.0
        for edge in obj.data.edges:
            a = obj.data.vertices[edge.vertices[0]].co
            b = obj.data.vertices[edge.vertices[1]].co
            arista = max(arista, (a - b).length)
        if hoja_doble():
            lineas.append(
                f"{obj.name}: {len(obj.data.polygons)} caras; "
                f"caja {medida.x*1000:.0f} x {medida.y*1000:.0f} x {medida.z*1000:.0f} mm; "
                f"arista maxima {arista*1000:.0f} mm; "
                f"area {superficie:.3f} m2"
            )
        else:
            pdf = OUT / f"{obj.name}.pdf"
            estado = desdoblar(obj, pdf)
            islas = islas_de(pdf) if pdf.exists() else 0
            lineas.append(
                f"{obj.name}: {islas} islas {estado}; "
                f"{len(obj.data.polygons)} caras; "
                f"caja {medida.x*1000:.0f} x {medida.y*1000:.0f} x {medida.z*1000:.0f} mm; "
                f"arista maxima {arista*1000:.0f} mm; "
                f"area {superficie:.3f} m2"
            )
        print("PIEZA", lineas[-1])

    plano = bpy.data.objects.new("00_prueba_100mm", bpy.data.meshes.new("regla"))
    escena.collection.objects.link(plano)
    malla = bmesh.new()
    bmesh.ops.create_grid(malla, x_segments=1, y_segments=1, size=0.05)
    malla.to_mesh(plano.data)
    malla.free()
    if hoja_doble():
        pintar(plano, (0.92, 0.92, 0.92, 1))
        piezas.append(plano)
        unido = unir(piezas)
        pdf = OUT / "plantilla.pdf"
        estado = desdoblar(unido, pdf, textura=False)
        islas = islas_de(pdf) if pdf.exists() else 0
        paginas = paginas_de(pdf) if pdf.exists() else 0
        lineas.insert(0, f"plantilla.pdf: {paginas} hojas doble carta, {islas} islas {estado}.")
        print("PLANTILLA", lineas[0])
        piezas = [unido]
    else:
        estado = desdoblar(plano, OUT / "00_prueba_100mm.pdf", textura=False, hoja=(CARTA_X, CARTA_Y))
        print("REGLA", estado, (OUT / "00_prueba_100mm.pdf").exists())

    for obj in piezas:
        activar(obj)
    bpy.ops.object.select_all(action="DESELECT")
    for obj in piezas:
        obj.select_set(True)
    bpy.context.view_layer.objects.active = piezas[0]
    bpy.ops.wm.obj_export(
        filepath=str(MODELOS / f"{animal}_{int(round(alto_pedido * 100))}cm{sufijo}.obj"),
        export_selected_objects=True,
        forward_axis="NEGATIVE_Y",
        up_axis="Z",
        global_scale=1000.0,
        export_materials=True,
        apply_modifiers=True,
    )
    bpy.ops.wm.save_as_mainfile(filepath=str(MODELOS / f"{animal}_{int(round(alto_pedido * 100))}cm{sufijo}.blend"))

    cartulina = 1.22 * 2.44
    hojas_carton = area_total * 1.45 / cartulina
    texto = OUT / "LEEME.txt" if angulo else OUT.parent / "LEEME.txt"
    texto.write_text(
        "\n".join(
            [
                f"{'Jabali' if animal == 'jabali' else 'Dodo'} a {alto_pedido:.2f} m de alto, plantilla a escala real. Disolucion: {angulo:.0f} grados.",
                *(
                    [
                        "Las solapas de pegado pasan de trapecio a triangulo: se quita el lado corto exterior y la base sigue siendo el doblez. La malla conserva la disolucion.",
                    ]
                    if ceja_triangular_pedida()
                    else []
                ),
                *(
                    [
                        f"Vertices a menos de {fusion_m()*1000:.0f} mm se unen antes de disolver, para quitar escalones pequenos.",
                    ]
                    if fusion_m() > 0
                    else []
                ),
                f"Caras antes de disolver: {caras_antes}. Despues: {caras_despues}.",
                (
                    "Cada PDF es una lamina de carton de 1.22 x 2.44 m, a escala real."
                    if hoja_carton()
                    else "Imprimir en doble carta, 279 x 432 mm, al 100 %, sin ajustar a la pagina."
                    if hoja_doble()
                    else "Imprimir en hoja carta, calidad media, al 100 %, sin ajustar a la pagina."
                ),
                *(
                    [
                        "Las islas grandes ocupan una hoja. Las piezas chicas, incluida la prueba de 100 mm, comparten hoja.",
                        "El titulo de cada isla nombra la parte: 01_cuerpo, 02_cabeza, las patas y 00_prueba_100mm.",
                        "El cuadrado de 00_prueba_100mm tiene que medir 100 mm por dentro.",
                    ]
                    if hoja_doble()
                    else []
                ),
                *(
                    [
                        "El corte es el contorno de cada isla. El borde de la lamina no se recorta si no hay linea.",
                        "Dentro de la isla, la linea continua se corta y la punteada se dobla.",
                        "00_prueba_100mm.pdf sigue siendo carta: el cuadrado interior tiene que medir 100 mm.",
                    ]
                    if hoja_carton()
                    else []
                ),
                *(
                    [
                        (
                            (
                                "Cada cara lleva la paleta alternativa del proyecto: grises a turquesa, tonos calidos a magenta, amarillos a verde lima. El negro se conserva."
                                if animal == "jabali"
                                else "Cada cara lleva una paleta alternativa: cuerpo turquesa, pico y patas magenta, cara verde lima."
                            )
                            if paleta_pedida()
                            else "Cada cara lleva la textura original del modelo, horneada a 150 ppp."
                        ),
                        "Las solapas quedan sin imagen para que se lean el corte, el doblez y el numero.",
                    ]
                    if con_textura()
                    else []
                ),
                (
                    "Antes de recortar el dodo, mide el cuadrado de prueba en plantilla.pdf."
                    if hoja_doble()
                    else "Primero imprime 00_prueba_100mm.pdf y mide el cuadrado: tiene que dar 100 mm."
                ),
                "Las solapas miden 12 mm. El numero de una arista se pega con el mismo numero.",
                (
                    "Recorta cada isla por su contorno, dobla las lineas punteadas y pega las solapas con el mismo numero."
                    if hoja_carton()
                    else "Recorta cada pieza, pegala sobre el carton de 1.22 x 2.44 m y corta el carton."
                ),
                "Las piezas son cascarones cerrados. Se unen entre si por la posicion del modelo.",
                f"Area de cartulina: {area_total:.2f} m2.",
                f"Con solapas y recorte, cerca de {hojas_carton:.1f} laminas de 1.22 x 2.44 m.",
                (
                    "La cola queda hacia +Y y el hocico hacia -Y. Las patas 1 y 3 estan del lado del hocico: la 1 en +X y la 3 en -X. Las patas 2 y 4 estan del lado de la cola."
                    if animal == "jabali"
                    else "Pata A es el lado X positivo del archivo. Pata B es el lado X negativo."
                ),
                "",
                *lineas,
            ]
        ),
        encoding="utf-8",
    )
    if animal == "jabali":
        credito = OUT / "CREDITOS.txt"
        credito.write_text(
            "\n".join(
                [
                    'Obra derivada de "boar block  anim" por blam, CC BY 4.0.',
                    "https://sketchfab.com/Blam577895",
                    "https://sketchfab.com/3d-models/boar-block-anim-a294b1f7ea2241c6bf5245e7a4923366",
                    "http://creativecommons.org/licenses/by/4.0/",
                    "La licencia incluye un descargo de garantias: https://creativecommons.org/licenses/by/4.0/legalcode",
                    f"Cambios: escala a {alto_pedido:.2f} m de alto, disolucion, paleta y plantilla de papel.",
                    "blam y Sketchfab no patrocinan este proyecto.",
                    "",
                ]
            ),
            encoding="utf-8",
        )
        texto.write_text(credito.read_text(encoding="utf-8") + texto.read_text(encoding="utf-8"), encoding="utf-8")
    print("LISTO", texto)


if __name__ == "__main__":
    main()
