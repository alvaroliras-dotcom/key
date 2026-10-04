"""
Módulo 6 · Volumen en cascada.

Orden: Search Console → Keyword Planner → DataForSEO → sin dato. Cada keyword se
queda con la primera fuente que responda. La herramienta nunca rellena huecos:
sin fuente, la celda va vacía y marcada «sin dato fiable».

- Search Console: impresiones, clics y posición media (dato real).
- Keyword Planner: búsquedas mensuales; en cuentas sin gasto llega como rango
  («1 mil – 10 mil») y se escribe tal cual, sin convertirlo en un número.
- DataForSEO: búsquedas mensuales medias de Google Ads (dato real, de pago).
"""

import csv
import io
import re
from dataclasses import dataclass
from typing import Dict, List, Optional

from . import dataforseo
from .modelos import Aviso
from .normalizar import clave, sin_tildes
from .tabla import Tabla

FUENTE_GSC = "Search Console (impresiones)"
FUENTE_PLANNER = "Keyword Planner (búsquedas/mes)"
FUENTE_PLANNER_RANGO = "Keyword Planner (rango)"
SIN_DATO = "sin dato fiable"

COL_CONSULTA = {"consultas principales", "consulta", "consultas", "top queries", "query", "queries"}
COL_IMPRESIONES = {"impresiones", "impressions"}
COL_CLICS = {"clics", "clicks"}
COL_POSICION = {"posicion", "position", "posicion media", "average position"}

COL_PLANNER_KW = {"keyword", "palabra clave", "palabras clave"}
COL_PLANNER_VOL = {"avg. monthly searches", "promedio de busquedas mensuales", "busquedas mensuales medias",
                   "media de busquedas mensuales", "avg monthly searches"}


def cascada() -> List[dict]:
    return [
        {"fuente": "Search Console", "como": "CSV subido (Consultas.csv)", "disponible": "v1"},
        {"fuente": "Keyword Planner", "como": "CSV subido (ideas de palabras clave)", "disponible": "v2"},
        {"fuente": "DataForSEO", "como": "API de pago, solo lo que falte",
         "disponible": "activa" if dataforseo.activo() else "sin clave en el servidor"},
        {"fuente": "Sin dato", "como": "celda vacía + «sin dato fiable»", "disponible": "siempre"},
    ]


@dataclass
class FilaGSC:
    impresiones: float = 0
    clics: float = 0
    pos_ponderada: float = 0       # posición × impresiones, para la media


def _num(v: str) -> Optional[float]:
    v = (v or "").strip().replace("%", "").replace(" ", "").replace(" ", "")
    if not v:
        return None
    if "," in v and "." in v:                 # 1.234,5
        v = v.replace(".", "").replace(",", ".")
    elif "," in v:                            # 3,5
        v = v.replace(",", ".")
    try:
        return float(v)
    except ValueError:
        return None


def _filas(texto: str) -> List[List[str]]:
    texto = texto.lstrip("﻿")
    lineas = texto.splitlines()
    muestra = "\n".join(lineas[:5])
    delim = "\t" if muestra.count("\t") > muestra.count(",") else (
        ";" if muestra.count(";") > muestra.count(",") else ",")
    return list(csv.reader(io.StringIO(texto), delimiter=delim))


def leer_gsc(texto: str, avisos: List[Aviso], nombre: str = "CSV Search Console") -> Dict[str, Dict]:
    """Devuelve {clave: {texto, impresiones, clics, posicion}}. Registra en Avisos si no lo entiende."""
    filas = _filas(texto)
    if not filas:
        avisos.append(Aviso("sin volumen", nombre, "El CSV de Search Console está vacío"))
        return {}

    cab = [sin_tildes(c.strip().lower()) for c in filas[0]]

    def idx(nombres):
        return next((i for i, c in enumerate(cab) if c in nombres), None)

    iq, ii, ic, ip = idx(COL_CONSULTA), idx(COL_IMPRESIONES), idx(COL_CLICS), idx(COL_POSICION)
    if iq is None or ii is None:
        avisos.append(Aviso("sin volumen", nombre,
                            "No encuentro las columnas de consulta e impresiones. ¿Es el export de "
                            f"«Consultas»? Cabecera leída: {', '.join(filas[0])}"))
        return {}

    acumulado: Dict[str, FilaGSC] = {}
    textos: Dict[str, str] = {}
    for fila in filas[1:]:
        if len(fila) <= max(iq, ii):
            continue
        q = fila[iq].strip()
        imp = _num(fila[ii])
        if not q or imp is None:
            continue
        k = clave(q)
        a = acumulado.setdefault(k, FilaGSC())
        textos.setdefault(k, q)
        a.impresiones += imp
        a.clics += (_num(fila[ic]) or 0) if ic is not None else 0
        pos = _num(fila[ip]) if ip is not None else None
        if pos is not None:
            a.pos_ponderada += pos * imp
    return {k: {"texto": textos[k], "impresiones": a.impresiones, "clics": a.clics,
                "posicion": round(a.pos_ponderada / a.impresiones, 1) if a.impresiones and a.pos_ponderada else None}
            for k, a in acumulado.items()}


def leer_planner(texto: str, avisos: List[Aviso], nombre: str = "CSV Keyword Planner") -> Dict[str, Dict]:
    """
    Devuelve {clave: {texto, volumen (número o None), rango (texto)}}.
    El export del Planner trae dos líneas de título antes de la cabecera: se busca la cabecera.
    """
    filas = _filas(texto)
    ik = iv = None
    inicio = 0
    for n, fila in enumerate(filas[:10]):
        cab = [sin_tildes(c.strip().lower()) for c in fila]
        ik = next((i for i, c in enumerate(cab) if c in COL_PLANNER_KW), None)
        iv = next((i for i, c in enumerate(cab) if c in COL_PLANNER_VOL), None)
        if ik is not None and iv is not None:
            inicio = n + 1
            break
    if ik is None or iv is None:
        avisos.append(Aviso("sin volumen", nombre,
                            "No encuentro las columnas «Palabra clave» y «Promedio de búsquedas mensuales». "
                            "¿Es el CSV de «Descargar ideas de palabras clave»?"))
        return {}
    out = {}
    for fila in filas[inicio:]:
        if len(fila) <= max(ik, iv) or not fila[ik].strip():
            continue
        q, bruto = fila[ik].strip(), fila[iv].strip()
        if not bruto:
            continue
        numero = _num(bruto) if re.fullmatch(r"[\d.,\s ]+", bruto) else None
        out[clave(q)] = {"texto": q, "volumen": numero, "rango": "" if numero is not None else bruto}
    return out


def aplicar_volumen(tabla: Tabla, gsc: Dict[str, Dict], planner: Dict[str, Dict],
                    dfs: Dict[str, Dict], avisos: List[Aviso], fuentes: List[str]) -> Dict[str, int]:
    cuenta = {"Search Console": 0, "Keyword Planner": 0, "DataForSEO": 0, "sin dato": 0}
    for kw in tabla.kws.values():
        kw.volumen, kw.volumen_texto, kw.fuente_volumen, kw.marca_estimacion = None, "", SIN_DATO, ""
        if kw.clave in gsc:
            d = gsc[kw.clave]
            kw.volumen, kw.clics, kw.posicion_media = d["impresiones"], d["clics"], d["posicion"]
            kw.fuente_volumen, kw.marca_estimacion = FUENTE_GSC, "dato real"
            cuenta["Search Console"] += 1
        elif kw.clave in planner:
            d = planner[kw.clave]
            if d["volumen"] is not None:
                kw.volumen, kw.fuente_volumen = d["volumen"], FUENTE_PLANNER
            else:
                kw.volumen_texto, kw.fuente_volumen = d["rango"], FUENTE_PLANNER_RANGO
            kw.marca_estimacion = "dato real" if d["volumen"] is not None else "dato real en rango"
            cuenta["Keyword Planner"] += 1
        elif kw.clave in dfs:
            d = dfs[kw.clave]
            kw.volumen, kw.cpc = d["search_volume"], d.get("cpc")
            kw.fuente_volumen, kw.marca_estimacion = dataforseo.FUENTE_VOLUMEN, "dato real"
            cuenta["DataForSEO"] += 1
        else:
            cuenta["sin dato"] += 1
    if cuenta["sin dato"]:
        avisos.append(Aviso("sin volumen", f"{cuenta['sin dato']} keywords",
                            f"Sin volumen en ninguna fuente activa ({', '.join(fuentes) or 'ninguna'}). "
                            "Celda vacía, nunca una cifra inventada."))
    return cuenta


def comprobar_honestidad(tabla: Tabla):
    """Regla dura: no puede existir un volumen (número o rango) sin fuente."""
    for kw in tabla.kws.values():
        tiene = kw.volumen is not None or bool(kw.volumen_texto)
        if tiene and (not kw.fuente_volumen or kw.fuente_volumen == SIN_DATO):
            raise AssertionError(f"Volumen sin fuente en «{kw.texto}»")
