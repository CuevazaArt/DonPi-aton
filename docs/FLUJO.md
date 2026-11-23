# Flujo de trabajo

La malla y la textura son «boar block anim» por [blam](https://sketchfab.com/Blam577895), [CC BY 4.0](http://creativecommons.org/licenses/by/4.0/). La acreditación completa está en [créditos](CREDITOS.md).

El jabalí entra como la malla ya disuelta a 30°, con la coronilla a 1 m, y sale como un PDF de oficio mexicano. Cada paso existe porque el anterior chocaba con un límite real.

## Orden

1. La altura se mide en el cuerpo, en el 30 % delantero desde el hocico. Ese punto queda a 1.00 m. La montura no entra en esa medida y el alto total queda en 1.31 m.
2. La paleta reescribe el atlas: grises a turquesa, tonos cálidos a magenta, amarillos a verde lima, y el negro se conserva.
3. El desdoble va a una lámina de cartón de 1.22 × 2.44 m, a escala 1:1, con margen de 10 mm.
4. Cada solapa de pegado sale en triángulo. Se quita el lado corto exterior. La base sigue siendo el doblez. La malla no se toca.
5. La flecha con número queda dentro de la cara, para que el corte no se la lleve. El doblez convexo se imprime `AFUERA`, en raya larga. El cóncavo se imprime `ADENTRO`, en puntos. Cada triángulo trae tres puntos para clavar agujas.
6. `scripts/mosaico_doble.py` es el curado. Su misión es llenar lo más posible cada hoja de oficio, 216 × 340 mm, sin cambiar la escala 1:1. Si un trozo de la cuadrícula no tiene dibujo, no se imprime. Si el dibujo no llena la hoja, se junta con otros trozos. El solape de los trozos que sí se tocan sigue siendo 15 mm.

La plantilla es `salida/jabali/100cm_cabeza_carton_30grados_paleta_ceja/mosaico_oficio.pdf`. La cola queda hacia +Y y el hocico hacia −Y. Las patas 1 y 3 están del lado del hocico; la 2 y la 4, del lado de la cola. La montura es la malla Sedlo.

## La palabra y la figura

Cada hoja lleva `JABALI100`, abajo a la derecha. Distingue esta entrega si las hojas se mezclan o se voltean.

`referencia.png` es la vista de tres cuartos del modelo ya armado. El mosaico la pone en la hoja 1, junto al cuadrado de 100 mm centrado, con el texto «figura armada, no se corta». Esa hoja también trae el papel, el cartón y la lógica de cortes.

## Textura

El atlas original mide 512 px. El horneado usa Cycles, pase de color difuso, una muestra, por isla, a 110 ppp en la lámina de cartón. Las solapas quedan sin imagen para que se lean el corte, el doblez y el número.
