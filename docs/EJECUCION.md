# Ejecución

Hace falta Blender 5.3, en `C:\Program Files\Blender Foundation\Blender 5.3\blender.exe`, y Python 3 del sistema (`py -3`) con `pypdf` y `pillow`. Los comandos se lanzan desde la raíz del repositorio.

El desdoble corre dentro de Blender. El mosaico corre en el Python del sistema.

## Plantilla

Vuelve a desdoblar la malla de coronilla a 1 m:

```
& "C:\Program Files\Blender Foundation\Blender 5.3\blender.exe" --background --python scripts/jabali_cabeza_1m.py
```

```
py -3 scripts/insertar_puntos.py
```

```
py -3 scripts/mosaico_doble.py --origen salida/jabali/100cm_cabeza_carton_30grados_paleta_ceja --destino salida/jabali/100cm_cabeza_carton_30grados_paleta_ceja/mosaico_oficio.pdf --hoja oficio
```

```
py -3 scripts/guia_interior.py
```

El curado usa oficio mexicano, 216 × 340 mm. Omite el trozo de cuadrícula que no tiene dibujo y junta en una hoja los que no la llenan. `MOSAICO.txt` lista cada hoja. La hoja 1 es la portada: cuadrado de 100 mm centrado, figura armada e instrucciones. `guia_interior.py` escribe `mosaico_oficio_interior.pdf` con las mismas hojas, en espejo y sin textura.

Si falta una librería:

```
py -3 -m pip install --user pypdf pillow
```

## Qué revisar al terminar

Abre el PDF y confirma que la primera página mide el cuadrado en 100 mm al imprimirla. En una página del cuerpo tienen que verse la imagen, la línea continua, `AFUERA` o `ADENTRO`, los tres puntos del triángulo y la clave de esquina. Una hoja no debe salir en blanco. `MOSAICO.txt` y el texto de cada hoja tienen que coincidir.
