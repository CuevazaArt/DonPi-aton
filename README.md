# DonPiñaton

Plantilla a escala real para armar una piñata hueca de jabalí, de papel y cartón, a partir de un modelo 3D. La coronilla queda a 1 m del suelo.

La carpeta local se llama DonPiñaton. En GitHub el repositorio quedó como [CuevazaArt/DonPi-aton](https://github.com/CuevazaArt/DonPi-aton): el nombre con eñe no se pudo conservar en la URL y el guion ocupa su lugar.

El flujo es este: la malla ya disuelta a 30° se escala para que la coronilla quede a 1 m, las solapas salen en triángulo, el desdoble va a lámina de cartón a escala 1:1 y el curado llena hojas de oficio mexicano. La isla que cabe sale entera. La que no cabe se parte en mosaico. Un trozo sin dibujo no se imprime, y el que no llena la hoja se junta con otros.

## Para armar

Hay dos PDF, en oficio mexicano (216 × 340 mm), al 100 % y sin ajustar a la página. Tienen el mismo número de hojas.

La piel, a color, se imprime completa:

`salida/jabali/100cm_cabeza_carton_30grados_paleta_ceja/mosaico_oficio.pdf`

La guía interior es el mismo desdoble en espejo y solo con líneas. Se imprime a criterio, hoja por hoja:

`salida/jabali/100cm_cabeza_carton_30grados_paleta_ceja/mosaico_oficio_interior.pdf`

La coronilla queda a 1.00 m. Con la montura el alto es 1.31 m, el largo 1.78 m y el ancho 1.50 m. Cada hoja de la piel dice `JABALI100`. La hoja 1 trae el cuadrado de 100 mm centrado, la figura armada y las instrucciones. El armado está en [el manual](docs/MANUAL.md). Papel y cartón están en [materiales](docs/MATERIALES.md).

El modelo es «boar block anim» por [blam](https://sketchfab.com/Blam577895), [CC BY 4.0](http://creativecommons.org/licenses/by/4.0/). El detalle está en [créditos](docs/CREDITOS.md).

## Documentos

| Documento | Para qué |
| --- | --- |
| [docs/FLUJO.md](docs/FLUJO.md) | De la malla al mosaico en oficio |
| [docs/MANUAL.md](docs/MANUAL.md) | Imprimir, cuadrar, pegar, cortar y armar |
| [docs/EJECUCION.md](docs/EJECUCION.md) | Comandos para volver a generar la plantilla |
| [docs/MATERIALES.md](docs/MATERIALES.md) | Papel, cartón, cinta y pegamento |
| [docs/CREDITOS.md](docs/CREDITOS.md) | Autor, licencia CC BY 4.0 y cambios sobre el modelo |

## Qué hay en el repositorio

- `scripts/jabali_cabeza_1m.py` escala el jabalí ya disuelto para que la coronilla quede a 1 m y lo desdobla.
- `scripts/generar_plantilla_dodo.py` es el desdoblador que usa ese script: paleta, solapa triangular y lámina de cartón.
- `scripts/io_export_paper_model.py` abre la malla a escala 1:1. La flecha de armado queda dentro del corte. El doblez convexo sale como `AFUERA` y el cóncavo como `ADENTRO`.
- `scripts/marcas_doblez.py` dibuja esas señas.
- `scripts/insertar_puntos.py` pone tres puntos en cada triángulo para clavar agujas y calzar el reverso.
- `scripts/mosaico_doble.py` es el curado. Con `--hoja oficio` llena hojas de 216 × 340 mm sin cambiar la escala. Omite el trozo vacío y junta los que no llenan la hoja.
- `scripts/guia_interior.py` saca la guía interior: el mismo PDF en espejo y sin textura, para calzar el reverso.
- `salida/jabali/100cm_cabeza_carton_30grados_paleta_ceja/` es la plantilla.
- `modelos/jabali/` guarda la malla de esa escala.

## Etiqueta

`v0.5.0` es este jabalí: coronilla a 1 m, oficio mexicano, curado que llena la hoja, flechas dentro del corte, dobleces `AFUERA` y `ADENTRO`, y tres puntos por triángulo.

`v0.6.0` separa la guía interior. Es el mismo desdoble en espejo y solo con líneas, hoja por hoja, para imprimir el reverso solo donde hace falta.
