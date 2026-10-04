"""
Cliente mínimo de DataForSEO (de pago, por consulta).

- Preguntas: SERP de Google (organic/live/advanced) → bloques «People Also Ask» y
  «búsquedas relacionadas» de las semillas prioritarias.
- Volumen: Google Ads search_volume/live → volumen mensual medio, CPC y competencia,
  solo para las keywords que no tengan dato de Search Console ni del Planner.

Credenciales SOLO en variables de entorno (DATAFORSEO_LOGIN / DATAFORSEO_PASSWORD).
Sin credenciales, los dos módulos se desactivan y lo dicen en Avisos.
"""

import os
from typing import Dict, List, Optional, Tuple

import httpx

from .normalizar import clave

API = "https://api.dataforseo.com/v3"
def _credencial(nombre: str) -> str:
    """Vacío si no hay valor o si es de relleno («-», «x», «none»…), para no llamar a la API con basura."""
    v = os.getenv(nombre, "").strip()
    return "" if len(v) < 4 or v.lower() in {"none", "null", "vacio", "vacío"} else v


LOGIN = _credencial("DATAFORSEO_LOGIN")
PASSWORD = _credencial("DATAFORSEO_PASSWORD")
MAX_SEMILLAS_PREGUNTAS = int(os.getenv("DATAFORSEO_MAX_PREGUNTAS", "15"))
MAX_KEYWORDS_VOLUMEN = int(os.getenv("DATAFORSEO_MAX_VOLUMEN", "3000"))
LOTE_VOLUMEN = 1000                       # máximo de keywords por tarea de Google Ads

# location_code de DataForSEO por mercado del briefing
LOCALIZACION = {
    "es-ES": (2724, "es"), "ca-ES": (2724, "ca"), "es-MX": (2484, "es"), "es-AR": (2032, "es"),
    "es-CO": (2170, "es"), "es-CL": (2152, "es"), "es-PE": (2604, "es"), "es-US": (2840, "es"),
}

FUENTE_VOLUMEN = "DataForSEO (Google Ads, búsquedas/mes)"


def activo() -> bool:
    return bool(LOGIN and PASSWORD)


class ErrorDataForSEO(Exception):
    pass


class DataForSEO:
    def __init__(self, mercado: str):
        self.location_code, self.language_code = LOCALIZACION.get(mercado, (2724, "es"))
        self.coste = 0.0

    async def _post(self, client: httpx.AsyncClient, ruta: str, cuerpo: list) -> list:
        r = await client.post(f"{API}/{ruta}", json=cuerpo, auth=(LOGIN, PASSWORD), timeout=120)
        if r.status_code != 200:
            raise ErrorDataForSEO(f"HTTP {r.status_code}: {r.text[:200]}")
        datos = r.json()
        if datos.get("status_code") != 20000:
            raise ErrorDataForSEO(f"{datos.get('status_code')}: {datos.get('status_message')}")
        self.coste += float(datos.get("cost") or 0)
        tareas = datos.get("tasks") or []
        for t in tareas:
            if t.get("status_code") != 20000:
                raise ErrorDataForSEO(f"tarea {t.get('status_code')}: {t.get('status_message')}")
        return tareas

    # ── Preguntas ─────────────────────────────────────────────────────────
    async def preguntas(self, client: httpx.AsyncClient, keyword: str) -> Tuple[List[str], List[str]]:
        """Devuelve (people_also_ask, búsquedas_relacionadas) de la SERP de esa keyword."""
        tareas = await self._post(client, "serp/google/organic/live/advanced", [{
            "keyword": keyword, "location_code": self.location_code,
            "language_code": self.language_code, "device": "desktop", "depth": 10,
        }])
        return extraer_preguntas(tareas)

    # ── Volumen ───────────────────────────────────────────────────────────
    async def volumen(self, client: httpx.AsyncClient, keywords: List[str]) -> Dict[str, dict]:
        """{clave: {search_volume, cpc, competition}} para las keywords que Google Ads reconoce."""
        out: Dict[str, dict] = {}
        for i in range(0, len(keywords), LOTE_VOLUMEN):
            lote = keywords[i:i + LOTE_VOLUMEN]
            tareas = await self._post(client, "keywords_data/google_ads/search_volume/live", [{
                "keywords": lote, "location_code": self.location_code,
                "language_code": self.language_code,
            }])
            out.update(extraer_volumen(tareas))
        return out


def extraer_preguntas(tareas: list) -> Tuple[List[str], List[str]]:
    paa, relacionadas = [], []
    for t in tareas:
        for res in t.get("result") or []:
            for item in res.get("items") or []:
                tipo = item.get("type")
                if tipo == "people_also_ask":
                    for sub in item.get("items") or []:
                        if sub.get("title"):
                            paa.append(sub["title"])
                elif tipo in ("related_searches", "people_also_search"):
                    for sub in item.get("items") or []:
                        texto = sub if isinstance(sub, str) else (sub or {}).get("title")
                        if texto:
                            relacionadas.append(texto)
    return paa, relacionadas


def extraer_volumen(tareas: list) -> Dict[str, dict]:
    out = {}
    for t in tareas:
        for res in t.get("result") or []:
            kw = res.get("keyword")
            if kw and res.get("search_volume") is not None:
                out[clave(kw)] = {"search_volume": res["search_volume"], "cpc": res.get("cpc"),
                                  "competition": res.get("competition")}
    return out


def apta_para_ads(keyword: str) -> bool:
    """Google Ads rechaza keywords de más de 80 caracteres o 10 palabras, y ciertos símbolos."""
    return len(keyword) <= 80 and len(keyword.split()) <= 10 and not any(c in keyword for c in "!@%,*")


def coste_legible(coste: Optional[float]) -> str:
    return f"{coste:.3f} $" if coste else "0 $"
