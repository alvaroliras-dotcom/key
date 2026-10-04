"""
Módulo 2 · Autocomplete (sopa de letras).

Orden de trabajo, para que un bloqueo o el límite de tiempo pillen lo importante
ya hecho:
  1. Sopa completa (semilla sola + a-z + 0-9) de las semillas prioritarias.
  2. Consulta simple (semilla sola) de todas las demás.
  3. Sopa completa del resto, mientras quede tiempo.
  4. (Opcional) Segundo nivel: sopa sobre las 20 sugerencias más repetidas.

Si Google corta, se reintenta como mucho dos veces con espera; con varios
bloqueos seguidos el módulo se para y entrega lo que tiene.
"""

import asyncio
import json
import os
import random
import string
import time
from typing import Callable, List, Optional

import httpx

from .modelos import Aviso, Semilla
from .tabla import Tabla

URL = "https://suggestqueries.google.com/complete/search"
LETRAS = list(string.ascii_lowercase) + ["ñ"] + list(string.digits)

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:131.0) Gecko/20100101 Firefox/131.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_6) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.6 Safari/605.1.15",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0.0.0 Safari/537.36 Edg/129.0.0.0",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 17_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.6 Mobile/15E148 Safari/604.1",
    "Mozilla/5.0 (Linux; Android 14; Pixel 8) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0.0.0 Mobile Safari/537.36",
]

MERCADOS = {
    "es-ES": ("es", "es"), "es-MX": ("es", "mx"), "es-AR": ("es", "ar"),
    "es-CO": ("es", "co"), "es-CL": ("es", "cl"), "es-PE": ("es", "pe"),
    "es-US": ("es", "us"), "ca-ES": ("ca", "es"),
}

CONCURRENCIA = int(os.getenv("AC_CONCURRENCIA", "2"))
PAUSA_MIN = float(os.getenv("AC_PAUSA_MIN", "0.25"))
PAUSA_MAX = float(os.getenv("AC_PAUSA_MAX", "0.8"))
PRESUPUESTO_SEG = int(os.getenv("AC_PRESUPUESTO_SEG", "420"))
BLOQUEOS_PARA_PARAR = 4
SEGUNDO_NIVEL_TOP = 20


class Bloqueado(Exception):
    pass


class Autocomplete:
    def __init__(self, tabla: Tabla, avisos: List[Aviso], mercado: str,
                 progreso: Callable[[str, int, int], None], factor_pausa: float = 1.0):
        self.tabla = tabla
        self.avisos = avisos
        self.hl, self.gl = MERCADOS.get(mercado, ("es", "es"))
        self.progreso = progreso
        self.hechas = 0
        self.total = 0
        self.bloqueos_seguidos = 0
        self.parado: Optional[str] = None     # motivo si se paró antes de acabar
        self.ultima_semilla = ""
        self._limite = 0.0
        # Con otra recogida reciente desde la misma IP, pausas más largas
        self.factor_pausa = factor_pausa

    async def _consultar(self, client: httpx.AsyncClient, q: str) -> List[str]:
        params = {"client": "firefox", "hl": self.hl, "gl": self.gl, "q": q,
                  "ie": "utf-8", "oe": "utf-8"}
        for intento in range(3):              # 1 intento + 2 reintentos, no más
            await asyncio.sleep(random.uniform(PAUSA_MIN, PAUSA_MAX) * self.factor_pausa)
            try:
                r = await client.get(URL, params=params,
                                     headers={"User-Agent": random.choice(USER_AGENTS),
                                              "Accept-Language": f"{self.hl}-{self.gl.upper()},{self.hl};q=0.9"})
            except httpx.HTTPError as e:
                err = f"error de red: {type(e).__name__}"
            else:
                if r.status_code == 200:
                    try:
                        datos = json.loads(r.content.decode("utf-8"))
                    except (UnicodeDecodeError, json.JSONDecodeError):
                        try:
                            datos = json.loads(r.content.decode("latin-1"))
                        except json.JSONDecodeError:
                            datos = None
                    if isinstance(datos, list) and len(datos) > 1 and isinstance(datos[1], list):
                        self.bloqueos_seguidos = 0
                        return [s for s in datos[1] if isinstance(s, str)]
                    err = "respuesta no reconocible (posible captcha)"
                else:
                    err = f"HTTP {r.status_code}"
            if intento < 2:
                await asyncio.sleep(4 * (intento + 1) + random.uniform(0, 2))
        self.bloqueos_seguidos += 1
        self.avisos.append(Aviso("bloqueo", q, f"Autocomplete sin respuesta tras 2 reintentos ({err})"))
        if self.bloqueos_seguidos >= BLOQUEOS_PARA_PARAR:
            raise Bloqueado(err)
        return []

    async def _semilla(self, client, sem: Semilla, sopa: bool, ya_hecha_sola: bool = False):
        consultas = ([] if ya_hecha_sola else [sem.texto])
        if sopa:
            consultas += [f"{sem.texto} {l}" for l in LETRAS]
        for q in consultas:
            if self.parado:
                sem.estado = "parcial"
                return
            if time.monotonic() > self._limite:
                self.parado = self.parado or "tiempo"
                sem.estado = "parcial"
                return
            try:
                sugerencias = await self._consultar(client, q)
            except Bloqueado as e:
                self.parado = f"bloqueo ({e})"
                sem.estado = "parcial"
                return
            sem.consultas += 1
            self.hechas += 1
            self.ultima_semilla = sem.texto
            for pos, s in enumerate(sugerencias, 1):
                if self.tabla.add(s, "autocomplete", sem.texto, pos):
                    sem.sugerencias += 1
            if q == sem.texto and not sugerencias and sopa:
                # Google no reconoce la semilla: las letras no van a sacar nada
                self.total -= len(LETRAS)
                sem.estado = "sin sugerencias"
                return
            self.progreso(f"{sem.texto!r} · {q[len(sem.texto):].strip() or '(sola)'}",
                          self.hechas, self.total)
        sem.estado = "hecha" if sopa else "solo semilla"

    async def _en_paralelo(self, client, trabajos):
        cola: asyncio.Queue = asyncio.Queue()
        for t in trabajos:
            cola.put_nowait(t)

        async def worker():
            while not cola.empty() and not self.parado:
                sem, sopa, sola_hecha = cola.get_nowait()
                await self._semilla(client, sem, sopa, sola_hecha)

        await asyncio.gather(*(worker() for _ in range(CONCURRENCIA)))

    async def ejecutar(self, semillas: List[Semilla], segundo_nivel: bool):
        self._limite = time.monotonic() + PRESUPUESTO_SEG
        # Sin geo primero: rinden mucho más que «servicio + zona + letra»
        prioritarias = sorted((s for s in semillas if s.prioritaria), key=lambda s: bool(s.geo))
        resto = [s for s in semillas if not s.prioritaria]
        resto_sopa = [s for s in resto if s.tipo == "base"]
        n_letras = len(LETRAS) + 1
        self.total = len(prioritarias) * n_letras + len(resto) + len(resto_sopa) * (n_letras - 1)

        async with httpx.AsyncClient(timeout=10, follow_redirects=True) as client:
            # 1 · Sopa de las prioritarias
            await self._en_paralelo(client, [(s, True, False) for s in prioritarias])
            # 2 · Consulta simple del resto
            await self._en_paralelo(client, [(s, False, False) for s in resto])
            # 3 · Sopa del resto mientras quede tiempo. Si la semilla sola no dio
            # ninguna sugerencia, Google no la reconoce: no se gastan 37 consultas en ella.
            vacias = [s for s in resto_sopa if s.consultas and s.sugerencias == 0]
            for s in vacias:
                s.estado = "sin sugerencias"
            self.total -= len(vacias) * (n_letras - 1)
            await self._en_paralelo(client, [(s, True, True) for s in resto_sopa if s not in vacias])
            # 4 · Segundo nivel opcional
            if segundo_nivel and not self.parado:
                textos_semilla = {s.texto for s in semillas}
                top = [kw.texto for kw in sorted(self.tabla.kws.values(), key=lambda k: -k.apariciones)
                       if kw.texto not in textos_semilla][:SEGUNDO_NIVEL_TOP]
                extra = [Semilla(texto=t, servicio="(segundo nivel)", intencion="", tipo="segundo nivel")
                         for t in top]
                self.total += len(extra) * (n_letras - 1)
                await self._en_paralelo(client, [(s, True, True) for s in extra])
                semillas.extend(extra)

        for s in semillas:
            if s.consultas == 0:
                s.estado = "sin consultar"

        if self.parado:
            motivo = ("se agotó el tiempo asignado" if self.parado == "tiempo"
                      else f"Google bloqueó la recogida: {self.parado}")
            sin = sum(1 for s in semillas if s.consultas == 0)
            self.avisos.append(Aviso(
                "bloqueo" if self.parado != "tiempo" else "presupuesto de tiempo",
                self.ultima_semilla or "(ninguna)",
                f"Autocomplete parado: {motivo}. Última semilla consultada: «{self.ultima_semilla}». "
                f"Consultas hechas: {self.hechas}. Semillas sin consultar: {sin}."))
