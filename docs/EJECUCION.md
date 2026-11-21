# Ejecución

Hace falta Blender 5.3, en `C:\Program Files\Blender Foundation\Blender 5.3\blender.exe`, y Python 3 del sistema (`py -3`) con `pypdf`. El GLB de origen está en `C:\Users\lexar\Downloads\dodo3d\dodo_block_anim.glb`. Los comandos se lanzan desde la raíz del repositorio.

El generador corre dentro de Blender, porque usa `bpy`. El mosaico corre en el Python del sistema, porque solo reescribe PDF.

## Plantilla recomendada

Desdobla a 30° sobre la lámina de cartón y hornea la paleta:

```
& "C:\Program Files\Blender Foundation\Blender 5.3\blender.exe" --background --python scripts/generar_plantilla_dodo.py -- --carton --angulo 30 --paleta
```

Eso escribe `salida/dodo/carton_30grados_paleta/` y el modelo `modelos/dodo/dodo_1m_30grados_paleta_carton.obj`.

Parte esas láminas en doble carta:

```
py -3 scripts/mosaico_doble.py --origen salida/dodo/carton_30grados_paleta --destino salida/dodo/carton_30grados_paleta/mosaico_doble_carta.pdf
```

El script también reescribe `MOSAICO.txt` junto al PDF. La hoja 1 del mosaico es `00_prueba_100mm.pdf`.

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

`--angulo 0` deja la malla sin disolver. En carta, una arista de más de 150 mm se subdivide para caber en la hoja. En cartón y en doble carta el límite es la diagonal útil de la hoja, al 90 %, para no agregar dobleces de más.

## Protocolo de silueta

```
& "C:\Program Files\Blender Foundation\Blender 5.3\blender.exe" --background --python scripts/protocolo_silueta.py -- --modelo "C:\Users\lexar\Downloads\dodo3d\dodo_block_anim.glb" --alto 1
```

Escribe `salida/dodo/protocolo/informe.txt`. `--modelo` y `--alto` tienen esos valores por defecto.

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
