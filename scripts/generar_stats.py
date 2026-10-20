# Genera assets/stats.svg con mis estadisticas de GitHub y los lenguajes mas usados en mis repos publicos.
# Necesita la variable GITHUB_TOKEN (la Action la entrega sola) porque la API GraphQL de GitHub pide un token.
# En local se puede probar con: GITHUB_TOKEN=$(gh auth token) python3 scripts/generar_stats.py
import json
import os
import urllib.request
from datetime import date, timedelta
from html import escape

USUARIO = "OsvaDev-HUB"
TOKEN = os.environ["GITHUB_TOKEN"]
RUTA_SALIDA = os.path.join(os.path.dirname(__file__), "..", "assets", "stats.svg")
CANTIDAD_LENGUAJES = 5
BLOQUES_POR_BARRA = 20
MESES = ["ene", "feb", "mar", "abr", "may", "jun", "jul", "ago", "sep", "oct", "nov", "dic"]

CABECERAS = {
    "Authorization": f"Bearer {TOKEN}",
    "Accept": "application/vnd.github+json",
    "X-GitHub-Api-Version": "2022-11-28",
}


def pedir_a_github(url):
    peticion = urllib.request.Request(url, headers=CABECERAS)
    with urllib.request.urlopen(peticion) as respuesta:
        return json.load(respuesta)


def consulta_graphql(consulta, variables):
    datos = json.dumps({"query": consulta, "variables": variables}).encode()
    peticion = urllib.request.Request("https://api.github.com/graphql", data=datos, headers=CABECERAS)
    with urllib.request.urlopen(peticion) as respuesta:
        return json.load(respuesta)["data"]


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


def obtener_contribuciones():
    """Devuelve un diccionario {fecha: cantidad} con todos los dias que tengo en GitHub."""
    anios = consulta_graphql(
        "query($login: String!) { user(login: $login) { contributionsCollection { contributionYears } } }",
        {"login": USUARIO},
    )["user"]["contributionsCollection"]["contributionYears"]

    dias = {}
    for anio in anios:
        datos = consulta_graphql(
            """query($login: String!, $desde: DateTime!, $hasta: DateTime!) {
                 user(login: $login) {
                   contributionsCollection(from: $desde, to: $hasta) {
                     contributionCalendar { weeks { contributionDays { date contributionCount } } }
                   }
                 }
               }""",
            {"login": USUARIO, "desde": f"{anio}-01-01T00:00:00Z", "hasta": f"{anio}-12-31T23:59:59Z"},
        )
        semanas = datos["user"]["contributionsCollection"]["contributionCalendar"]["weeks"]
        for semana in semanas:
            for dia in semana["contributionDays"]:
                dias[dia["date"]] = dia["contributionCount"]
    return dias


def racha_mas_larga(dias):
    """Cuenta la mayor cantidad de dias seguidos con al menos una contribucion."""
    mejor = 0
    actual = 0
    dia_anterior = None
    for texto in sorted(dias):
        fecha = date.fromisoformat(texto)
        if dias[texto] > 0:
            seguido = dia_anterior is not None and fecha - dia_anterior == timedelta(days=1)
            actual = actual + 1 if seguido else 1
            dia_anterior = fecha
            mejor = max(mejor, actual)
        else:
            actual = 0
            dia_anterior = None
    return mejor


def esquinas(x, y, ancho, alto, paso):
    """Puntos de un rectangulo con esquinas escalonadas."""
    return (f"{x + paso},{y} {x + ancho - paso},{y} {x + ancho - paso},{y + paso} {x + ancho},{y + paso} "
            f"{x + ancho},{y + alto - paso} {x + ancho - paso},{y + alto - paso} {x + ancho - paso},{y + alto} "
            f"{x + paso},{y + alto} {x + paso},{y + alto - paso} {x},{y + alto - paso} {x},{y + paso} {x + paso},{y + paso}")


# Octocat en pixel-art: "#" es el circulo y "N" es el gato (se pinta con el color de fondo)
OCTOCAT = [
    ".....####.....",
    "...########...",
    "..##########..",
    ".###N####N###.",
    ".###NN##NN###.",
    "####NNNNNN####",
    "###NNNNNNNN###",
    "###NNNNNNNN###",
    "####NNNNNN####",
    ".#N##NNNN####.",
    ".##N#NNNN####.",
    "..##NNNNNN##..",
    "...#NN##NN#...",
    ".....####.....",
]


def dibujar_octocat(x, y, tam=3):
    rectangulos = []
    for fila, linea in enumerate(OCTOCAT):
        for columna, letra in enumerate(linea):
            if letra == ".":
                continue
            color = "#C084FC" if letra == "#" else "#140D26"
            rectangulos.append(f'<rect x="{x + columna * tam}" y="{y + fila * tam}" width="{tam}" height="{tam}" fill="{color}"/>')
    return "\n    ".join(rectangulos)


def crear_svg(ficha, lenguajes):
    ancho, alto = 772, 244
    partes = []

    # Ficha de la izquierda: etiqueta, puntos guia y valor
    for indice, (etiqueta, valor) in enumerate(ficha):
        y = 127 + indice * 24
        partes.append(f'<text x="24" y="{y}" fill="#E9D5FF">{escape(etiqueta)}</text>')
        partes.append(f'<line x1="{24 + len(etiqueta) * 8 + 8}" y1="{y - 4}" x2="{352 - len(valor) * 8 - 8}" y2="{y - 4}" stroke="#3B2A66" stroke-width="2" stroke-dasharray="2 4"/>')
        partes.append(f'<text x="352" y="{y}" text-anchor="end" font-weight="700" fill="#C084FC">{escape(valor)}</text>')

    # Barras de lenguajes a la derecha: el mas usado llena la barra y los demas se comparan con el
    porcentaje_mayor = lenguajes[0][1]
    for indice, (nombre, porcentaje) in enumerate(lenguajes):
        y = 116 + indice * 24
        if len(nombre) > 12:
            nombre = nombre[:11] + "…"
        partes.append(f'<text x="412" y="{y + 11}" fill="#E9D5FF">{escape(nombre)}</text>')
        llenos = max(1, round(porcentaje / porcentaje_mayor * BLOQUES_POR_BARRA))
        for bloque in range(BLOQUES_POR_BARRA):
            color = "#C084FC" if bloque < llenos else "#2A1A52"
            partes.append(f'<rect x="{514 + bloque * 9}" y="{y}" width="7" height="12" fill="{color}"/>')
        partes.append(f'<text x="752" y="{y + 11}" text-anchor="end" fill="#A78BFA">{porcentaje:.1f}%</text>')

    descripcion = escape("Stats de GitHub: " + ", ".join(f"{e} {v}" for e, v in ficha)
                         + ". Lenguajes más usados: " + ", ".join(f"{n} {p:.1f}%" for n, p in lenguajes))
    contenido = "\n    ".join(partes)
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="{ancho + 4}" height="{alto + 4}" viewBox="0 0 {ancho + 4} {alto + 4}" shape-rendering="crispEdges" role="img" aria-label="{descripcion}">
  <!-- Marco pixelado igual al de los botones -->
  <polygon transform="translate(4 4)" fill="#2E1065" points="{esquinas(0, 0, ancho, alto, 4)}"/>
  <polygon fill="#8B5CF6" points="{esquinas(0, 0, ancho, alto, 4)}"/>
  <polygon fill="#140D26" points="{esquinas(4, 4, ancho - 8, alto - 8, 4)}"/>
  <!-- Barra de pestañas -->
  <rect x="4" y="4" width="{ancho - 8}" height="30" fill="#1E1238"/>
  <rect x="4" y="4" width="160" height="30" fill="#140D26"/>
  <rect x="4" y="4" width="160" height="3" fill="#C084FC"/>
  <!-- Linea punteada que separa la ficha de los lenguajes -->
  <line x1="384" y1="52" x2="384" y2="228" stroke="#3B2A66" stroke-width="2" stroke-dasharray="4 4"/>
  <!-- Logo de GitHub -->
  <g>
    {dibujar_octocat(24, 48)}
  </g>
  <g font-family="'JetBrains Mono', SFMono-Regular, Menlo, Consolas, 'Liberation Mono', 'DejaVu Sans Mono', monospace" text-rendering="geometricPrecision">
    <text x="18" y="24" font-size="12" fill="#E9D5FF">github-stats.json</text>
    <text x="80" y="68" font-size="18" font-weight="700" fill="#F3E8FF">Stats de GitHub</text>
    <text x="80" y="86" font-size="12" fill="#A78BFA">@{USUARIO}</text>
    <text x="412" y="68" font-size="14" font-weight="700" fill="#F3E8FF">Lenguajes más usados</text>
    <text x="412" y="86" font-size="12" fill="#A78BFA">en repos públicos</text>
    <g font-size="13">
    {contenido}
    </g>
  </g>
</svg>
'''


def main():
    perfil = pedir_a_github(f"https://api.github.com/users/{USUARIO}")
    repos = obtener_repos()
    dias = obtener_contribuciones()

    totales = sumar_lenguajes(repos)
    suma = sum(totales.values())
    mas_usados = sorted(totales.items(), key=lambda par: par[1], reverse=True)[:CANTIDAD_LENGUAJES]
    lenguajes = [(nombre, cantidad / suma * 100) for nombre, cantidad in mas_usados]

    creado = date.fromisoformat(perfil["created_at"][:10])
    ficha = [
        ("contribuciones", str(sum(dias.values()))),
        ("racha más larga", f"{racha_mas_larga(dias)} días"),
        ("repos públicos", str(perfil["public_repos"])),
        ("seguidores", str(perfil["followers"])),
        ("en GitHub desde", f"{MESES[creado.month - 1]} {creado.year}"),
    ]

    with open(RUTA_SALIDA, "w", encoding="utf-8") as archivo:
        archivo.write(crear_svg(ficha, lenguajes))
    print("Listo: assets/stats.svg actualizado")


if __name__ == "__main__":
    main()
