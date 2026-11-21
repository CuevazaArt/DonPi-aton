"""Vistas del original, del equilibrio a 30° y del colapso rechazado."""

import bpy
from mathutils import Matrix, Vector
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = Path(r"C:\Users\lexar\Downloads\dodo3d\dodo_block_anim.glb")
SALIDA = ROOT / "salida" / "dodo" / "protocolo" / "vistas"
ALTO_M = 1.0

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
COLORES = {
    "cuerpo": (0.85, 0.55, 0.20, 1),
    "cabeza": (0.95, 0.80, 0.25, 1),
    "pieza_frontal": (0.75, 0.35, 0.20, 1),
    "pieza_lateral": (0.55, 0.35, 0.70, 1),
    "pata_a_muslo": (0.30, 0.55, 0.85, 1),
    "pata_a_canilla": (0.25, 0.70, 0.75, 1),
    "pata_a_pie": (0.20, 0.45, 0.55, 1),
    "pata_b_muslo": (0.85, 0.35, 0.45, 1),
    "pata_b_canilla": (0.90, 0.55, 0.60, 1),
    "pata_b_pie": (0.60, 0.25, 0.30, 1),
}


def activar(obj):
    if bpy.context.mode != "OBJECT":
        bpy.ops.object.mode_set(mode="OBJECT")
    bpy.ops.object.select_all(action="DESELECT")
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj


def hornear_y_escalar():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    escena = bpy.context.scene
    escena.unit_settings.system = "METRIC"
    escena.unit_settings.scale_length = 1.0
    bpy.ops.import_scene.gltf(filepath=str(SRC))
    piezas = [obj for obj in bpy.data.objects if obj.type == "MESH"]
    for obj in piezas:
        matriz = obj.matrix_world.copy()
        obj.data = obj.data.copy()
        obj.parent = None
        obj.matrix_world = Matrix.Identity(4)
        for vertice in obj.data.vertices:
            vertice.co = matriz @ vertice.co
    for obj in list(bpy.data.objects):
        if obj.type != "MESH":
            bpy.data.objects.remove(obj, do_unlink=True)
    coordenadas = [v.co.copy() for obj in piezas for v in obj.data.vertices]
    minimo = Vector((min(v.x for v in coordenadas), min(v.y for v in coordenadas), min(v.z for v in coordenadas)))
    factor = ALTO_M / (max(v.z for v in coordenadas) - minimo.z)
    for obj in piezas:
        for vertice in obj.data.vertices:
            vertice.co = (vertice.co - minimo) * factor
        obj.name = NOMBRES.get(obj.name, obj.name)
        color = COLORES.get(obj.name, (0.8, 0.8, 0.8, 1))
        obj.color = color
    return piezas


def copiar(piezas, sufijo):
    copias = []
    for obj in piezas:
        nuevo = obj.copy()
        nuevo.data = obj.data.copy()
        nuevo.name = f"{obj.name}{sufijo}"
        nuevo.color = obj.color
        bpy.context.scene.collection.objects.link(nuevo)
        copias.append(nuevo)
    return copias


def disolver(piezas, grados):
    for obj in piezas:
        if len(obj.data.polygons) < 6:
            continue
        modificador = obj.modifiers.new("disolver", "DECIMATE")
        modificador.decimate_type = "DISSOLVE"
        modificador.angle_limit = grados * 3.1415926535 / 180.0
        modificador.use_dissolve_boundaries = False
        activar(obj)
        bpy.ops.object.modifier_apply(modifier=modificador.name)


def colapsar(piezas, ratio):
    for obj in piezas:
        if len(obj.data.polygons) < 8:
            continue
        modificador = obj.modifiers.new("colapsar", "DECIMATE")
        modificador.decimate_type = "COLLAPSE"
        modificador.ratio = ratio
        activar(obj)
        bpy.ops.object.modifier_apply(modifier=modificador.name)


def centro(piezas):
    coordenadas = [v.co for obj in piezas for v in obj.data.vertices]
    return Vector(
        (
            (min(v.x for v in coordenadas) + max(v.x for v in coordenadas)) / 2,
            (min(v.y for v in coordenadas) + max(v.y for v in coordenadas)) / 2,
            (min(v.z for v in coordenadas) + max(v.z for v in coordenadas)) / 2,
        )
    )


def mover(piezas, delta):
    for obj in piezas:
        for vertice in obj.data.vertices:
            vertice.co += delta


def ocultar_todos(grupos, visible):
    visibles = {id(obj) for obj in visible}
    for grupo in grupos:
        for obj in grupo:
            obj.hide_render = id(obj) not in visibles


def camara(nombre, ubicacion, objetivo, escala):
    datos = bpy.data.cameras.new(nombre)
    datos.type = "ORTHO"
    datos.ortho_scale = escala
    obj = bpy.data.objects.new(nombre, datos)
    bpy.context.scene.collection.objects.link(obj)
    obj.location = ubicacion
    seguimiento = obj.constraints.new("TRACK_TO")
    seguimiento.target = objetivo
    seguimiento.track_axis = "TRACK_NEGATIVE_Z"
    seguimiento.up_axis = "UP_Y"
    return obj


def main():
    SALIDA.mkdir(parents=True, exist_ok=True)
    original = hornear_y_escalar()
    equilibrio = copiar(original, "_30")
    disolver(equilibrio, 30)
    rechazado = copiar(original, "_colapso")
    disolver(rechazado, 15)
    colapsar(rechazado, 0.5)

    grupos = [original, equilibrio, rechazado]
    escena = bpy.context.scene
    escena.render.engine = "BLENDER_WORKBENCH"
    escena.display.shading.light = "STUDIO"
    escena.display.shading.color_type = "OBJECT"
    escena.display.shading.show_cavity = True
    escena.render.resolution_x = 900
    escena.render.resolution_y = 1100
    escena.render.image_settings.file_format = "PNG"
    escena.render.film_transparent = False

    ancla = bpy.data.objects.new("ancla", None)
    escena.collection.objects.link(ancla)
    ancla.location = centro(original)

    frente = camara("frente", ancla.location + Vector((0, -4, 0)), ancla, 1.35)
    lado = camara("lado", ancla.location + Vector((-4, 0, 0)), ancla, 1.55)
    tres = camara("tres_cuartos", ancla.location + Vector((-2.4, -3.2, 0.7)), ancla, 1.7)

    tomas = {"frente": frente, "lado": lado, "tres_cuartos": tres}
    versiones = {"original": original, "equilibrio_30": equilibrio, "rechazado": rechazado}
    for vista, cam in tomas.items():
        escena.camera = cam
        for nombre, grupo in versiones.items():
            ocultar_todos(grupos, grupo)
            escena.render.filepath = str(SALIDA / f"{nombre}_{vista}.png")
            bpy.ops.render.render(write_still=True)
            print("FOTO", escena.render.filepath)


if __name__ == "__main__":
    main()
