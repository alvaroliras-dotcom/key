"""
Dónde se guardan las recogidas, para que el Excel no se pierda cuando el servidor
se duerme (petición 7 de Nuria).

- Siempre en una carpeta: RECOGIDAS_DIR (por defecto, «recogidas/» en la raíz del
  repo). En el ordenador de Álvaro queda en E:\\015-CREACION DE APPS\\010-THE KEY\\recogidas.
- Opcional, en Supabase Storage, si hay SUPABASE_URL y SUPABASE_SERVICE_KEY: así
  sobrevive a los reinicios de Render.

Cada recogida es una subcarpeta con:
  la-llave-<marca>.xlsx · briefing.json (relanzable) · resumen.json · pestanas.json
"""

import json
import logging
import os
import re
from datetime import datetime
from typing import List, Optional

import httpx

log = logging.getLogger("la-llave")

RAIZ = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
DIR = os.getenv("RECOGIDAS_DIR") or os.path.join(RAIZ, "recogidas")
SUPABASE_URL = os.getenv("SUPABASE_URL", "").rstrip("/")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_KEY", "")
BUCKET = os.getenv("SUPABASE_BUCKET", "la-llave")
os.makedirs(DIR, exist_ok=True)


def supabase_activo() -> bool:
    return bool(SUPABASE_URL and SUPABASE_KEY)


def slug(texto: str) -> str:
    return re.sub(r"[^\w\-]+", "-", texto.lower()).strip("-") or "proyecto"


def carpeta(pid: str, marca: str, inicio: float) -> str:
    return f"{datetime.fromtimestamp(inicio):%Y-%m-%d_%H%M}_{slug(marca)}_{pid}"


def nombre_excel(marca: str) -> str:
    return f"la-llave-{slug(marca)}.xlsx"


def ruta_local(nombre_carpeta: str, archivo: str) -> str:
    return os.path.join(DIR, nombre_carpeta, archivo)


def _cabeceras(tipo: str):
    return {"Authorization": f"Bearer {SUPABASE_KEY}", "apikey": SUPABASE_KEY,
            "Content-Type": tipo, "x-upsert": "true"}


def _subir(ruta_remota: str, contenido: bytes, tipo: str):
    r = httpx.post(f"{SUPABASE_URL}/storage/v1/object/{BUCKET}/{ruta_remota}",
                   content=contenido, headers=_cabeceras(tipo), timeout=60)
    if r.status_code >= 300:
        raise RuntimeError(f"Supabase {r.status_code}: {r.text[:200]}")


def _bajar(ruta_remota: str) -> Optional[bytes]:
    r = httpx.get(f"{SUPABASE_URL}/storage/v1/object/{BUCKET}/{ruta_remota}",
                  headers=_cabeceras("application/octet-stream"), timeout=60)
    return r.content if r.status_code == 200 else None


def guardar(nombre_carpeta: str, archivos: dict) -> List[str]:
    """archivos: {nombre: bytes}. Devuelve los avisos (texto) si algo falla al subir."""
    os.makedirs(os.path.join(DIR, nombre_carpeta), exist_ok=True)
    for nombre, contenido in archivos.items():
        with open(ruta_local(nombre_carpeta, nombre), "wb") as f:
            f.write(contenido)
    _actualizar_indice(nombre_carpeta, json.loads(archivos["resumen.json"]))
    fallos = []
    if supabase_activo():
        for nombre, contenido in archivos.items():
            tipo = ("application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                    if nombre.endswith(".xlsx") else "application/json")
            try:
                _subir(f"{nombre_carpeta}/{nombre}", contenido, tipo)
            except Exception as e:      # no se cae la recogida por esto; se avisa
                fallos.append(f"{nombre}: {e}")
        try:
            _subir("indice.json", json.dumps(leer_indice(), ensure_ascii=False).encode(), "application/json")
        except Exception as e:
            fallos.append(f"indice.json: {e}")
    return fallos


def leer(nombre_carpeta: str, archivo: str) -> Optional[bytes]:
    ruta = ruta_local(nombre_carpeta, archivo)
    if os.path.exists(ruta):
        with open(ruta, "rb") as f:
            return f.read()
    if supabase_activo():
        contenido = _bajar(f"{nombre_carpeta}/{archivo}")
        if contenido is not None:
            os.makedirs(os.path.dirname(ruta), exist_ok=True)
            with open(ruta, "wb") as f:
                f.write(contenido)
        return contenido
    return None


def _ruta_indice() -> str:
    return os.path.join(DIR, "indice.json")


def leer_indice() -> list:
    """Historial de recogidas, la más reciente primero."""
    if os.path.exists(_ruta_indice()):
        with open(_ruta_indice(), encoding="utf-8") as f:
            return json.load(f)
    if supabase_activo():
        contenido = _bajar("indice.json")
        if contenido:
            datos = json.loads(contenido)
            with open(_ruta_indice(), "w", encoding="utf-8") as f:
                json.dump(datos, f, ensure_ascii=False, indent=1)
            return datos
    return []


def _actualizar_indice(nombre_carpeta: str, resumen: dict):
    indice = [e for e in leer_indice() if e.get("carpeta") != nombre_carpeta]
    indice.insert(0, {"carpeta": nombre_carpeta, "id": resumen.get("id"), "marca": resumen.get("marca"),
                      "fecha": resumen.get("fecha"), "keywords": resumen.get("keywords"),
                      "duracion_seg": resumen.get("duracion_seg")})
    with open(_ruta_indice(), "w", encoding="utf-8") as f:
        json.dump(indice, f, ensure_ascii=False, indent=1)


def buscar(pid: str) -> Optional[dict]:
    return next((e for e in leer_indice() if e.get("id") == pid), None)
