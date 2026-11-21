# Flujo de trabajo

El dodo entra como un GLB animado de diez cascarones y sale como un PDF que una impresora doméstica puede imprimir a 1 m de alto. Cada paso existe porque el anterior chocaba con un límite real.

## De dónde sale la malla

Blender 5.3 importa `dodo_block_anim.glb`, hornea la posición de cada pieza al mundo y escala el conjunto hasta 1.00 m de alto. La unidad de Blender es el metro. El desdoble escribe milímetros reales en el PDF: la primera matriz del archivo es 2.834646, que convierte milímetros a puntos tipográficos.

Las diez piezas conservan su nombre de archivo:

| PDF | Malla de origen |
| --- | --- |
| 01_cuerpo | dodo_body |
| 02_cabeza | dodo_head |
| 03_pieza_frontal | dodo_3 |
| 04_pieza_lateral | dodo_4 |
| 05 a 07, pata A | dodo_1, dodo_11, dodo_111, lado X positivo |
| 08 a 10, pata B | dodo_2 y su cadena, lado X negativo |

Son cascarones cerrados. Se unen entre sí por la posición del modelo. El número de una arista pega con el mismo número dentro de la misma pieza.

## Por qué no se imprime el modelo tal cual

Una carta útil, ya con 10 mm de margen de impresora y 12 mm de solapa, no admite una arista larga. El generador parte esas aristas y el desdoblador vuelve a cortar cada isla para que quepa en la hoja. El dodo original, de 646 caras, se volvió unas 155 hojas carta. El corte era el trabajo pesado, no el dibujo.

`scripts/protocolo_silueta.py` compara frente, lado y planta a 160 px. Una versión sigue siendo el dodo si la silueta mínima queda en 0.93 o más, la caja cambia 3 % o menos y el área no baja de 90 %. Entre las que pasan, se queda la de menos caras que siga a 1.5 % de la mejor silueta. El informe está en `salida/dodo/protocolo/informe.txt`.

| Nivel | Caras | Silueta mínima | Qué pasó |
| --- | --- | --- | --- |
| Original | 646 | 1.000 | Demasiados cortes al partir en carta |
| Disolver 30° | 342 | 0.998 | Silueta intacta. Es la plantilla de armar |
| Disolver 45° y unir vértices a 8 mm | 113 | Sigue leyéndose el ave | 55 hojas doble carta y 60 islas. Menos dobleces, más plano |
| Colapsar | 190 y menos | 0.856 o peor | Abre huecos y deforma la caja. Quedó en `salida/dodo/inspeccion/03_rechazado_colapso` |

Disolver por encima de 60° aplana los escalones del modelo de bloques. A 90° el ave deja de leerse. Unir vértices entre 4 y 12 mm produjo la misma malla; 8 mm es el valor usado en la variante doble carta.

La cifra de «hojas estimadas» del protocolo es un empaque de estantería. La cuenta real es la de cada `LEEME.txt`.

## La hoja grande y el mosaico

Desdoblar sobre una lámina de 1.22 × 2.44 m evita partir cada cara para que quepa en carta. Con disolución de 30° salen 17 islas: el cuerpo en 4, la cabeza en 5 y el resto en una isla cada una. Esas láminas están en `salida/dodo/carton_30grados_paleta/`. No caben en una impresora doméstica.

`scripts/mosaico_doble.py` toma cada isla y la reparte en doble carta, 279.4 × 431.8 mm, que es el formato más grande de esa impresora. La escala sigue en 1:1. Hay 15 mm de solape para alinear, y el borde de la hoja se pega. El corte sigue siendo la línea continua de la isla.

PosteRazor y Rasterbator convierten el plano en una foto y la línea de corte se suaviza. El mosaico de este repositorio conserva vectores, imagen y milímetros. LibreOffice Draw también puede mosaicar, con el riesgo de cambiar la escala al imprimir. El PDF ya trae el mosaico hecho.

Cada esquina que toca otra hoja lleva una clave de cuatro signos, por ejemplo AA18. La hoja vecina repite esa clave en la esquina que se junta. Donde se cruzan cuatro hojas, las cuatro esquinas dicen lo mismo. La esquina del borde exterior queda sin clave. El índice completo está en `salida/dodo/carton_30grados_paleta/MOSAICO.txt`.

## Textura

El atlas original mide 512 px, así que subir los puntos por pulgada no agrega detalle. El horneado usa Cycles, pase de color difuso, una muestra, por isla. En carta va a 150 ppp. En lámina de cartón va a 110 ppp.

`--textura` deja la paleta original. `--paleta` la reescribe antes de hornear: el cuerpo pasa a turquesa, el pico y las patas a magenta, la cara a verde lima, y el ojo negro se conserva. Las solapas quedan grises para que se lean el corte, el doblez y el número. El cuadrado de 100 mm se exporta sin imagen.

## Las tres plantillas que valen

| Carpeta | Qué es |
| --- | --- |
| `salida/dodo/carton_30grados_paleta/mosaico_doble_carta.pdf` | La de armar. 30°, paleta, 74 hojas doble carta, 17 cortes |
| `salida/dodo/doble_45grados/plantilla.pdf` | Menos dobleces. 45° y fusión de 8 mm, 55 hojas, 60 islas, solo líneas. El ave mide 99 × 58 × 107 cm |
| `salida/dodo/carta_30grados_paleta/` | La misma geometría de 30° partida directo en carta, unas 151 hojas |

El resto de `salida/dodo/` son ensayos: carta con líneas, carta con el atlas original, láminas de cartón sin textura y las vistas del protocolo.
