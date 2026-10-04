"""
Módulo 3 · Preguntas: People Also Ask y búsquedas relacionadas (petición 3 de Nuria).

- Con DataForSEO: lee la SERP de las semillas prioritarias (máx. DATAFORSEO_MAX_PREGUNTAS)
  y extrae el bloque PAA y las búsquedas relacionadas. Si una SERP no trae PAA,
  se registra «sin PAA» para esa semilla; nunca se inventa.
- Siempre: las keywords del autocomplete formuladas como pregunta también pasan
  a la pestaña Preguntas (son materia de blog aunque no haya clave de pago).

Las PAA van solo a Preguntas; las búsquedas relacionadas son keywords y entran
además en la tabla (módulo «relacionadas»).
"""

import asyncio
import re
from typing import Callable, List

import httpx

from . import dataforseo
from .modelos import Aviso, Briefing, Pregunta, Semilla
from .normalizar import clave, limpiar, tokens
from .tabla import Tabla

ES_PREGUNTA = re.compile(r"^(c[oó]mo|qu[eé]|cu[aá]nto|cu[aá]nta|cu[aá]l|cu[aá]les|d[oó]nde|cu[aá]ndo|"
                         r"por qu[eé]|para qu[eé]|qui[eé]n)\b|\?$|\b(qu[eé] es|para qu[eé] sirve)\b")
CONCURRENCIA = 3


def semillas_para_preguntas(semillas: List[Semilla], briefing: Briefing) -> List[str]:
    """Prioritarias primero (sin zona, luego con la principal), después el resto de servicios a secas."""
    elegidas = []
    prior = [s for s in semillas if s.prioritaria and s.tipo == "base"]
    for s in sorted(prior, key=lambda s: (bool(s.geo), len(s.texto))):
        elegidas.append(s.texto)
    for serv in briefing.servicios:
        elegidas.append(limpiar(serv.nombre))
    return list(dict.fromkeys(elegidas))[:dataforseo.MAX_SEMILLAS_PREGUNTAS]


def preguntas_del_autocomplete(tabla: Tabla) -> List[Pregunta]:
    out = []
    for kw in tabla.kws.values():
        if "autocomplete" in kw.modulos and ES_PREGUNTA.search(kw.texto):
            out.append(Pregunta(kw.texto, "pregunta del autocomplete", kw.semilla_origen, kw.servicio, kw.geo))
    return out


async def recoger_paa(semillas_texto: List[str], tabla: Tabla, briefing: Briefing, avisos: List[Aviso],
                      progreso: Callable[[str, int, int], None]) -> (List[Pregunta], dataforseo.DataForSEO):
    dfs = dataforseo.DataForSEO(briefing.mercado)
    preguntas: List[Pregunta] = []
    vistas = set()
    hechas = 0
    sem = asyncio.Semaphore(CONCURRENCIA)

    async def una(client, semilla):
        nonlocal hechas
        async with sem:
            try:
                paa, relacionadas = await dfs.preguntas(client, semilla)
            except Exception as e:
                avisos.append(Aviso("preguntas", semilla, f"DataForSEO no respondió: {e}"))
                return
        hechas += 1
        progreso(semilla, hechas, len(semillas_texto))
        if not paa:
            avisos.append(Aviso("sin PAA", semilla, "La SERP no trae bloque «La gente también pregunta»"))
        tk_serv = tabla.servicio(tokens(semilla))
        geo = tabla.geo(clave(semilla))
        for p in paa:
            motivo = tabla.es_ruido(p)
            if motivo or clave(p) in vistas:
                continue
            vistas.add(clave(p))
            preguntas.append(Pregunta(p, "People Also Ask", semilla, tk_serv, geo))
        for r in relacionadas:
            if tabla.add(r, "relacionadas", semilla) and ES_PREGUNTA.search(limpiar(r)) and clave(r) not in vistas:
                vistas.add(clave(r))
                preguntas.append(Pregunta(r, "búsqueda relacionada", semilla, tk_serv, geo))

    async with httpx.AsyncClient() as client:
        await asyncio.gather(*(una(client, s) for s in semillas_texto))
    return preguntas, dfs
