"""Marca cada doblez con un trazo distinto, una flecha y un texto.

AFUERA es el doblez convexo: el canto queda hacia afuera y la cara
impresa hace de lomo. La flecha apunta hacia un lado de la linea.
ADENTRO es el doblez concavo: el canto queda hacia adentro. La flecha
apunta hacia el lado contrario. Las coordenadas entran en milimetros.
"""


def _disco(cx, cy, radio, rgb):
    k = 0.55191502449 * radio
    return (
        f"{rgb} rg {cx + radio:.3f} {cy:.3f} m "
        f"{cx + radio:.3f} {cy + k:.3f} {cx + k:.3f} {cy + radio:.3f} {cx:.3f} {cy + radio:.3f} c "
        f"{cx - k:.3f} {cy + radio:.3f} {cx - radio:.3f} {cy + k:.3f} {cx - radio:.3f} {cy:.3f} c "
        f"{cx - radio:.3f} {cy - k:.3f} {cx - k:.3f} {cy - radio:.3f} {cx:.3f} {cy - radio:.3f} c "
        f"{cx + k:.3f} {cy - radio:.3f} {cx + radio:.3f} {cy - k:.3f} {cx + radio:.3f} {cy:.3f} c f"
    )


def _area2(a, b, c):
    return abs((b[0] - a[0]) * (c[1] - a[1]) - (c[0] - a[0]) * (b[1] - a[1]))


def puntos_de_cara(vertices):
    """Tres puntos por triangulo, hacia el centro, para clavar una aguja en cada uno."""
    if len(vertices) < 3:
        return ""
    triangulos = (
        [vertices]
        if len(vertices) == 3
        else [(vertices[0], vertices[i], vertices[i + 1]) for i in range(1, len(vertices) - 1)]
    )
    marcas = []
    for a, b, c in triangulos:
        if _area2(a, b, c) < 2:
            continue
        centro = ((a[0] + b[0] + c[0]) / 3, (a[1] + b[1] + c[1]) / 3)
        for vertice in (a, b, c):
            marcas.append((
                vertice[0] + 0.34 * (centro[0] - vertice[0]),
                vertice[1] + 0.34 * (centro[1] - vertice[1]),
            ))
    if not marcas:
        return ""
    lineas = ["q"]
    for x, y in marcas:
        lineas.append(_disco(x, y, 1.7, "1 1 1"))
        lineas.append(_disco(x, y, 0.55, "0 0 0"))
    lineas.append("Q")
    return "\n".join(lineas)


def comandos(x1, y1, x2, y2, afuera):
    dx, dy = x2 - x1, y2 - y1
    largo = (dx * dx + dy * dy) ** 0.5
    if largo < 5:
        return ""
    ux, uy = dx / largo, dy / largo
    if ux < -1e-6 or (abs(ux) < 1e-6 and uy < 0):
        ux, uy = -ux, -uy
    nx, ny = -uy, ux
    mx, my = (x1 + x2) / 2, (y1 + y2) / 2
    if afuera:
        palabra, factor = "AFUERA", 3.95
        flecha = "1.5 0 m 0 2.6 l -1.5 0 l f"
    else:
        palabra, factor = "ADENTRO", 4.73
        flecha = "1.5 0 m 0 -2.6 l -1.5 0 l f"
    alto = 2.4
    if largo < 16:
        palabra = "A" if afuera else "D"
        factor = 0.70
        alto = 2.2
    ancho = alto * factor
    base = 3.3
    return "\n".join(
        [
            f"q {ux:.5f} {uy:.5f} {nx:.5f} {ny:.5f} {mx:.3f} {my:.3f} cm",
            "[ ] 0 d 0 J",
            "0 0 0 rg",
            flecha,
            f"q 1 1 1 rg {-ancho / 2 - 0.5:.2f} {base - 0.45:.2f} {ancho + 1.0:.2f} {alto + 0.7:.2f} re f Q",
            f"BT /F1 {alto:.2f} Tf 0 0 0 rg {-ancho / 2:.2f} {base:.2f} Td ({palabra}) Tj ET",
            "Q",
            "",
        ]
    )
