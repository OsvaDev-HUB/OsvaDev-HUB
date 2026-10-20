# Genera assets/lenguajes.svg con los lenguajes mas usados en mis repos publicos.
# Si existe la variable GITHUB_TOKEN (la Action la entrega sola) se usa para tener mas consultas permitidas.
import json
import os
import urllib.request
from html import escape

USUARIO = "OsvaDev-HUB"
TOKEN = os.environ.get("GITHUB_TOKEN")
RUTA_SALIDA = os.path.join(os.path.dirname(__file__), "..", "assets", "lenguajes.svg")
CANTIDAD_LENGUAJES = 5
BLOQUES_POR_BARRA = 20


def pedir_a_github(url):
    cabeceras = {
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
    }
    if TOKEN:
        cabeceras["Authorization"] = f"Bearer {TOKEN}"
    peticion = urllib.request.Request(url, headers=cabeceras)
    with urllib.request.urlopen(peticion) as respuesta:
        return json.load(respuesta)


def obtener_repos():
    """Trae todos mis repos publicos, pagina por pagina."""
    repos = []
    pagina = 1
    while True:
        url = f"https://api.github.com/users/{USUARIO}/repos?type=owner&per_page=100&page={pagina}"
        lote = pedir_a_github(url)
        if not lote:
            break
        repos.extend(lote)
        pagina += 1
    return repos


def sumar_lenguajes(repos):
    """Suma los bytes de cada lenguaje en todos los repos que no son forks."""
    totales = {}
    for repo in repos:
        if repo["fork"]:
            continue
        for lenguaje, cantidad in pedir_a_github(repo["languages_url"]).items():
            totales[lenguaje] = totales.get(lenguaje, 0) + cantidad
    return totales


def esquinas(x, y, ancho, alto, paso):
    """Puntos de un rectangulo con esquinas escalonadas."""
    return (f"{x + paso},{y} {x + ancho - paso},{y} {x + ancho - paso},{y + paso} {x + ancho},{y + paso} "
            f"{x + ancho},{y + alto - paso} {x + ancho - paso},{y + alto - paso} {x + ancho - paso},{y + alto} "
            f"{x + paso},{y + alto} {x + paso},{y + alto - paso} {x},{y + alto - paso} {x},{y + paso} {x + paso},{y + paso}")


def crear_svg(lenguajes):
    ancho, alto = 318, 173
    filas = []
    porcentaje_mayor = lenguajes[0][1]
    for indice, (nombre, porcentaje) in enumerate(lenguajes):
        y = 48 + indice * 24
        # Los nombres largos se cortan para que no tapen la barra
        if len(nombre) > 12:
            nombre = nombre[:11] + "…"
        filas.append(f'<text x="18" y="{y + 11}" fill="#E9D5FF">{escape(nombre)}</text>')
        # Barra de bloques: el lenguaje mas usado llena la barra y los demas se comparan con el
        llenos = max(1, round(porcentaje / porcentaje_mayor * BLOQUES_POR_BARRA))
        for bloque in range(BLOQUES_POR_BARRA):
            color = "#C084FC" if bloque < llenos else "#2A1A52"
            filas.append(f'<rect x="{106 + bloque * 7}" y="{y}" width="5" height="12" fill="{color}"/>')
        filas.append(f'<text x="302" y="{y + 11}" text-anchor="end" fill="#A78BFA">{porcentaje:.1f}%</text>')

    descripcion = escape(", ".join(f"{nombre} {porcentaje:.1f}%" for nombre, porcentaje in lenguajes))
    contenido = "\n    ".join(filas)
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="{ancho + 4}" height="{alto + 4}" viewBox="0 0 {ancho + 4} {alto + 4}" shape-rendering="crispEdges" role="img" aria-label="Lenguajes más usados: {descripcion}">
  <!-- Marco pixelado igual al de los botones -->
  <polygon transform="translate(4 4)" fill="#2E1065" points="{esquinas(0, 0, ancho, alto, 4)}"/>
  <polygon fill="#8B5CF6" points="{esquinas(0, 0, ancho, alto, 4)}"/>
  <polygon fill="#140D26" points="{esquinas(4, 4, ancho - 8, alto - 8, 4)}"/>
  <!-- Barra de pestañas -->
  <rect x="4" y="4" width="{ancho - 8}" height="30" fill="#1E1238"/>
  <rect x="4" y="4" width="130" height="30" fill="#140D26"/>
  <rect x="4" y="4" width="130" height="3" fill="#C084FC"/>
  <g font-family="'JetBrains Mono', SFMono-Regular, Menlo, Consolas, 'Liberation Mono', 'DejaVu Sans Mono', monospace" font-size="12" text-rendering="geometricPrecision">
    <text x="18" y="24" fill="#E9D5FF">lenguajes.json</text>
    {contenido}
  </g>
</svg>
'''


def main():
    repos = obtener_repos()
    totales = sumar_lenguajes(repos)
    suma = sum(totales.values())
    mas_usados = sorted(totales.items(), key=lambda par: par[1], reverse=True)[:CANTIDAD_LENGUAJES]
    lenguajes = [(nombre, cantidad / suma * 100) for nombre, cantidad in mas_usados]

    with open(RUTA_SALIDA, "w", encoding="utf-8") as archivo:
        archivo.write(crear_svg(lenguajes))
    print(f"Listo: {len(lenguajes)} lenguajes guardados en assets/lenguajes.svg")


if __name__ == "__main__":
    main()
