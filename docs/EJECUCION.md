# Ejecución

Hace falta Blender 5.3, en `C:\Program Files\Blender Foundation\Blender 5.3\blender.exe`, y Python 3 del sistema (`py -3`) con `pypdf`. El GLB de origen está en `C:\Users\lexar\Downloads\dodo3d\dodo_block_anim.glb`. Los comandos se lanzan desde la raíz del repositorio.

El generador corre dentro de Blender, porque usa `bpy`. El mosaico corre en el Python del sistema, porque solo reescribe PDF.

## Plantilla del flujo común

La malla se disuelve al ángulo que aprobó el protocolo. `--ceja-triangular` solo cambia las solapas de pegado: cada trapecio pasa a triángulo y la base queda como doblez.

Jabalí a 50 cm:

```
& "C:\Program Files\Blender Foundation\Blender 5.3\blender.exe" --background --python scripts/generar_plantilla_dodo.py -- --animal jabali --modelo "C:\Users\lexar\Downloads\jabali\boar_block__anim.glb" --alto 0.5 --carton --angulo 30 --paleta --ceja-triangular
```

El generador escribe el modelo `modelos/jabali/jabali_50cm_30grados_paleta_ceja_carton.obj`. El GLB de origen está en `C:\Users\lexar\Downloads\jabali\boar_block__anim.glb`. El PDF de 57 hojas ya está en `salida/jabali/carton_30grados_paleta_ceja/mosaico_doble_carta.pdf`, partido con una isla por hoja. Volver a lanzar el mosaico sobre esa carpeta lo reescribiría con el acomodo.

El jabalí de 40 cm, con textura y ya acomodado para imprimir:

```
py -3 scripts/mosaico_doble.py --origen salida/jabali/40cm_carton_30grados_paleta_ceja --destino salida/jabali/40cm_carton_30grados_paleta_ceja/mosaico_doble_carta.pdf
```

Son 26 hojas. La isla que cabe sale entera y puede compartir la hoja, con 2 mm entre recuadros. La que no cabe sale en mosaico, girada si así usa menos hojas, con 15 mm de solape. `MOSAICO.txt` lista cada hoja.

El mismo flujo para el dodo de 1 m, con solapas triangulares:

```
& "C:\Program Files\Blender Foundation\Blender 5.3\blender.exe" --background --python scripts/generar_plantilla_dodo.py -- --animal dodo --modelo "C:\Users\lexar\Downloads\dodo3d\dodo_block_anim.glb" --alto 1 --carton --angulo 30 --paleta --ceja-triangular
```

```
py -3 scripts/mosaico_doble.py --origen salida/dodo/carton_30grados_paleta_ceja --destino salida/dodo/carton_30grados_paleta_ceja/mosaico_doble_carta.pdf
```

El mosaico del dodo que ya está en `salida/dodo/carton_30grados_paleta/` se generó sin `--ceja-triangular`. Sus solapas siguen en trapecio.

El script del mosaico también reescribe `MOSAICO.txt` junto al PDF. La hoja 1 es `00_prueba_100mm.pdf`.

Si falta pypdf:

```
py -3 -m pip install --user pypdf
```

## Otras salidas del generador

Los argumentos van después de `--`, que es lo que Blender entrega al script.

| Comando extra | Carpeta |
| --- | --- |
| sin argumentos | `salida/dodo/carta`, líneas, geometría original |
| `--angulo 30` | `salida/dodo/carta_30grados` |
| `--angulo 30 --textura` | `salida/dodo/carta_30grados_textura`, atlas original |
| `--angulo 30 --paleta` | `salida/dodo/carta_30grados_paleta` |
| `--carton --angulo 30` | `salida/dodo/carton_30grados`, láminas sin imagen |
| `--doble` | `salida/dodo/doble_45grados`, 45° y fusión de 8 mm si no se piden otros valores |
| `--doble --angulo 30 --fusion 0` | doble carta, 30°, sin unir vértices |
| `--fusion 8` | une vértices a menos de 8 mm; con `--doble` ese valor ya es el predeterminado |
| `--animal jabali` | nombres, carpeta `salida/jabali/` y crédito del jabalí |
| `--modelo RUTA` y `--alto 0.5` | GLB de origen y altura en metros |
| `--ceja-triangular` | solapas de pegado en triángulo; la malla no cambia |
| `--salida RUTA` en el protocolo | carpeta del informe; por defecto `salida/dodo/protocolo` |

`--angulo 0` deja la malla sin disolver. En carta, una arista de más de 150 mm se subdivide para caber en la hoja. En cartón y en doble carta el límite es la diagonal útil de la hoja, al 90 %, para no agregar dobleces de más.

## Protocolo de silueta

```
& "C:\Program Files\Blender Foundation\Blender 5.3\blender.exe" --background --python scripts/protocolo_silueta.py -- --modelo "C:\Users\lexar\Downloads\dodo3d\dodo_block_anim.glb" --alto 1
```

Escribe `salida/dodo/protocolo/informe.txt`. `--modelo` y `--alto` tienen esos valores por defecto. Para el jabalí se usó `--salida salida/jabali/protocolo` y `--alto 0.5`.

Las vistas comparadas salen con:

```
& "C:\Program Files\Blender Foundation\Blender 5.3\blender.exe" --background --python scripts/vista_equilibrio.py
```

Los OBJ de inspección, incluido el colapso rechazado, salen con:

```
& "C:\Program Files\Blender Foundation\Blender 5.3\blender.exe" --background --python scripts/exportar_inspeccion.py
```

## Qué revisar al terminar

Abre el PDF y confirma que la primera página mide el cuadrado en 100 mm al imprimirla. En una página del cuerpo tienen que verse la imagen, la línea continua, la línea punteada y la clave de esquina. `MOSAICO.txt` y el texto de cada hoja tienen que coincidir.
