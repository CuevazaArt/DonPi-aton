"""Exporta original, equilibrio a 30° y colapso rechazado para abrirlos."""

from pathlib import Path

import bpy
from mathutils import Matrix, Vector

ROOT = Path(__file__).resolve().parents[1]
SRC = Path(r"C:\Users\lexar\Downloads\dodo3d\dodo_block_anim.glb")
SALIDA = ROOT / "salida" / "dodo" / "inspeccion"
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


def seleccionar(piezas):
    if bpy.context.mode != "OBJECT":
        bpy.ops.object.mode_set(mode="OBJECT")
    bpy.ops.object.select_all(action="DESELECT")
    for obj in piezas:
        obj.select_set(True)
    bpy.context.view_layer.objects.active = piezas[0]


def cargar():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.context.scene.unit_settings.system = "METRIC"
    bpy.context.scene.unit_settings.scale_length = 1.0
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
        base = NOMBRES.get(obj.name, obj.name)
        obj.name = base
        obj.data.name = base
        color = COLORES.get(base, (0.8, 0.8, 0.8, 1))
        obj.color = color
        material = bpy.data.materials.new(base)
        material.diffuse_color = color
        obj.data.materials.clear()
        obj.data.materials.append(material)
    return piezas


def copiar(piezas, sufijo):
    copias = []
    for obj in piezas:
        nuevo = obj.copy()
        nuevo.data = obj.data.copy()
        nuevo.name = f"{obj.name}{sufijo}"
        nuevo.data.name = nuevo.name
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


def exportar(piezas, carpeta):
    carpeta.mkdir(parents=True, exist_ok=True)
    seleccionar(piezas)
    bpy.ops.wm.obj_export(
        filepath=str(carpeta / "modelo.obj"),
        export_selected_objects=True,
        forward_axis="NEGATIVE_Y",
        up_axis="Z",
        global_scale=1000.0,
        export_materials=True,
        apply_modifiers=True,
    )
    bpy.ops.export_scene.gltf(
        filepath=str(carpeta / "modelo.glb"),
        export_format="GLB",
        use_selection=True,
        export_apply=True,
    )


def desplazar(piezas, distancia):
    for obj in piezas:
        for vertice in obj.data.vertices:
            vertice.co.x += distancia


def main():
    SALIDA.mkdir(parents=True, exist_ok=True)
    original = cargar()
    equilibrio = copiar(original, "")
    for obj in equilibrio:
        obj.name = obj.name.replace(".001", "")
    disolver(equilibrio, 30)
    rechazado = copiar(original, "")
    disolver(rechazado, 15)
    colapsar(rechazado, 0.5)

    exportar(original, SALIDA / "01_original")
    exportar(equilibrio, SALIDA / "02_equilibrio_30")
    exportar(rechazado, SALIDA / "03_rechazado_colapso")

    desplazar(equilibrio, 1.4)
    desplazar(rechazado, 2.8)
    seleccionar(original + equilibrio + rechazado)
    bpy.ops.wm.save_as_mainfile(filepath=str(SALIDA / "comparacion.blend"))
    print("LISTO", SALIDA)


if __name__ == "__main__":
    main()
