"""
Hueco frente a la competencia (petición 4 de Nuria).

1. Cada página espejada (competidores y web propia) se etiqueta con el mismo
   servicio y la misma zona que usan las keywords, a partir de su H1, su keyword
   inferida y su URL.
2. Fiabilidad de esa etiqueta:
   - «fuerte»: el servicio sale del H1 o de la keyword inferida.
   - «inferencia débil»: solo sale del title o del slug (H1 vacío, genérico o de eslogan).
   - «sin servicio»: no se reconoce ningún servicio del briefing.
3. Una keyword tiene hueco si algún competidor tiene una página de su mismo
   servicio y zona (o, si es informacional, una entrada de blog que trate lo mismo)
   y la web propia no.

No decide páginas: marca dónde mirar.
"""

from collections import defaultdict
from typing import Dict, List, Tuple

from .modelos import Keyword, PaginaCompetidor
from .normalizar import clave, tokens
from .tabla import Tabla

PATRONES_COMERCIALES = {"servicio", "servicio-ciudad", "home"}
SOLAPE_MINIMO_BLOG = 0.5


def _slug(url: str) -> str:
    return url.split("://", 1)[-1].split("/", 1)[-1].replace("/", " ").replace("-", " ").replace("_", " ")


def _geo_comparable(geo: str) -> str:
    # «cerca de mí» no es una zona: compara con las páginas genéricas
    return "" if geo == "cerca de mí" else geo


def etiquetar_paginas(tabla: Tabla, paginas: List[PaginaCompetidor]):
    for p in paginas:
        if p.patron in ("legal", "contacto", "empresa"):
            p.fiabilidad = "no aplica"
            continue
        principal = f"{p.h1} {p.keyword_inferida}"
        p.servicio = tabla.servicio(tokens(principal))
        if p.servicio:
            p.fiabilidad = "fuerte"
        else:
            p.servicio = tabla.servicio(tokens(f"{p.title} {_slug(p.url)}"))
            p.fiabilidad = "inferencia débil" if p.servicio else "sin servicio"
        # La zona, del slug y del H1: el title suele repetir la sede en todas las páginas
        p.geo = _geo_comparable(tabla.geo(clave(f"{_slug(p.url)} {p.h1}")))


def calcular_hueco(kws: List[Keyword], paginas: List[PaginaCompetidor]) -> Dict[str, int]:
    """
    Regla de cobertura (pensada para negocio local):
    - keyword sin zona («diseño web barato») → la cubre cualquier página de ese servicio,
      lleve zona o no («Diseño web en Alcorcón» la cubre);
    - keyword con zona («diseño web móstoles») → solo la cubre una página de ese servicio
      y esa zona.
    """
    por_servicio: Dict[str, List[PaginaCompetidor]] = defaultdict(list)
    comerciales: Dict[Tuple[str, str], List[PaginaCompetidor]] = defaultdict(list)
    blog: Dict[str, List[PaginaCompetidor]] = defaultdict(list)
    for p in paginas:
        if not p.servicio:
            continue
        if p.patron in PATRONES_COMERCIALES:
            comerciales[(p.servicio, p.geo)].append(p)
            por_servicio[p.servicio].append(p)
        elif p.patron == "blog":
            blog[p.servicio].append(p)
    tokens_pagina = {id(p): tokens(f"{p.title} {p.h1} {p.keyword_inferida}") for p in paginas}

    cuenta = {"sí": 0, "no": 0, "—": 0}
    for kw in kws:
        candidatas: List[PaginaCompetidor] = []
        if kw.servicio and kw.intencion != "marca":
            if kw.intencion == "informacional":
                tk = tokens(kw.texto)
                resto = tk - tokens(kw.servicio)
                for p in blog.get(kw.servicio, []):
                    if not resto or len(resto & tokens_pagina[id(p)]) / len(resto) >= SOLAPE_MINIMO_BLOG:
                        candidatas.append(p)
            elif _geo_comparable(kw.geo):
                candidatas = comerciales.get((kw.servicio, _geo_comparable(kw.geo)), [])
            else:
                candidatas = por_servicio.get(kw.servicio, [])
        propias = [p for p in candidatas if p.propia]
        ajenas = [p for p in candidatas if not p.propia]
        if not ajenas and not propias:
            kw.hueco = "—"
        elif propias:
            kw.hueco = "no"
        else:
            kw.hueco = "sí"
        if ajenas:
            kw.competidores_con_pagina = ", ".join(sorted({p.dominio for p in ajenas}))
            kw.fiabilidad_hueco = ("fuerte" if any(p.fiabilidad == "fuerte" for p in ajenas)
                                   else "inferencia débil")
        if propias:
            kw.pagina_propia = propias[0].url
        cuenta[kw.hueco] += 1
    return cuenta


def fiabilidad_por_dominio(paginas: List[PaginaCompetidor]) -> Dict[str, Dict[str, int]]:
    """Recuento para la Lectura y el informe: ¿se puede fiar uno del espejo de cada web?"""
    out: Dict[str, Dict[str, int]] = defaultdict(lambda: defaultdict(int))
    for p in paginas:
        if p.fiabilidad != "no aplica":
            out[p.dominio][p.fiabilidad] += 1
    return {d: dict(v) for d, v in out.items()}
