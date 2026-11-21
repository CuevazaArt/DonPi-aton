# DonPiñaton

Plantillas a escala real para armar piñatas huecas de papel y cartón, a partir de un modelo 3D. El primer objeto es un dodo de 1 m de alto.

La carpeta local se llama DonPiñaton. En GitHub el repositorio quedó como [CuevazaArt/DonPi-aton](https://github.com/CuevazaArt/DonPi-aton): el nombre con eñe no se pudo conservar en la URL y el guion ocupa su lugar. El trabajo vive en las dos rutas.

## Para armar el dodo

Imprime este archivo al 100 %, en doble carta (279 × 432 mm):

`salida/dodo/carton_30grados_paleta/mosaico_doble_carta.pdf`

Son 74 hojas y 17 piezas de corte. La primera hoja trae un cuadrado cuyo interior tiene que medir 100 mm. El armado está en [el manual](docs/MANUAL.md). Papel, cartón y pegamento están en [materiales](docs/MATERIALES.md).

## Ejemplo

El ave de origen, a 1 m, con un color plano por pieza para la inspección. A la derecha, la misma silueta tras disolver aristas a 30°. Abajo, el atlas recoloreado que se hornea en la plantilla.

| Original | Disolución a 30° |
| --- | --- |
| ![Dodo original en tres cuartos](salida/dodo/protocolo/vistas/original_tres_cuartos.png) | ![Dodo tras disolver a 30 grados](salida/dodo/protocolo/vistas/equilibrio_30_tres_cuartos.png) |

![Atlas del dodo con la paleta turquesa, magenta y verde lima](salida/dodo/carta_30grados_paleta/textura_paleta.png)

«dodo block anim» por [blam](https://sketchfab.com/Blam577895), bajo [CC BY 4.0](http://creativecommons.org/licenses/by/4.0/). Obra original en [Sketchfab](https://sketchfab.com/3d-models/dodo-block-anim-6b63321a76f241a3899193f129e92f7d). DonPiñaton la modificó: escala de 1 m, simplificación, paleta y plantilla de papel. blam y Sketchfab no patrocinan este repositorio. El detalle está en [créditos](docs/CREDITOS.md).

## Documentos

| Documento | Para qué |
| --- | --- |
| [docs/FLUJO.md](docs/FLUJO.md) | Cómo se atacó cada complicación, de la malla al mosaico |
| [docs/MANUAL.md](docs/MANUAL.md) | Imprimir, cuadrar, pegar, cortar y armar |
| [docs/EJECUCION.md](docs/EJECUCION.md) | Comandos para volver a generar una plantilla |
| [docs/MATERIALES.md](docs/MATERIALES.md) | Papel, cartón, cinta y pegamento |
| [docs/CREDITOS.md](docs/CREDITOS.md) | Autor, licencia CC BY 4.0 y cambios sobre el modelo |

## Qué hay en el repositorio

- `scripts/generar_plantilla_dodo.py` escala el modelo, simplifica la malla y desdobla las piezas.
- `scripts/io_export_paper_model.py` es el desdoblador. Pepakura Designer 6.3.9 está instalado para revisar a mano; este complemento hace el desdoble por script, a escala 1:1.
- `scripts/mosaico_doble.py` parte las láminas grandes en doble carta, con solape y claves de esquina.
- `scripts/protocolo_silueta.py` compara siluetas y elige hasta dónde se puede simplificar.
- `salida/dodo/` guarda las plantillas ya generadas. Cada carpeta trae su `LEEME.txt`.
- `modelos/dodo/` guarda la malla de 1 m en OBJ y Blend, ya horneada en metros.

El GLB de origen no está en el repositorio. En esta computadora vive en `C:\Users\lexar\Downloads\dodo3d\dodo_block_anim.glb`.

## Etiqueta

`v0.1.0` es el dodo de 30°, con paleta, desdoblado en lámina de cartón y mosaicado a doble carta.
