"""
La Llave (The Key) · API de keyword research de Nuria (v2).

REST (lo usa el formulario web):
  POST /proyectos                    → lanza la recogida con el briefing; devuelve un id
  GET  /proyectos/{id}               → progreso por módulo y, al acabar, el resumen
  GET  /proyectos/{id}/excel         → el Excel con identidad GYF
  GET  /proyectos/{id}/csv/{pestaña} → una pestaña como CSV plano
  GET  /proyectos/{id}/briefing      → el briefing en JSON, para relanzar
  GET  /recogidas                    → historial de recogidas guardadas
  GET  /cascada                      → cascada de volumen, fuentes activas y valores por defecto

MCP (lo usa Nuria desde claude.ai): en /{MCP_RUTA}, ver mcp_server.py.
"""

import asyncio
import json
import logging
import os
import re
import time
import uuid
from contextlib import asynccontextmanager
from typing import Dict, List

import httpx
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response

from . import almacen, dataforseo
from .autocomplete import PRESUPUESTO_SEG, Autocomplete
from .competidores import Espejo, dominio_de
from .excel import a_json, construir_pestanas, de_json, generar_csv, generar_excel
from .hueco import calcular_hueco, etiquetar_paginas
from .mcp_server import crear_mcp, opciones_http
from .modelos import Aviso, Briefing, PaginaCompetidor, Pregunta
from .preguntas import preguntas_del_autocomplete, recoger_paa, semillas_para_preguntas
from .semillas import MODIFICADORES_POR_DEFECTO, generar_semillas
from .tabla import Tabla, ruido_por_defecto
from .volumen import aplicar_volumen, cascada, comprobar_honestidad, leer_gsc, leer_planner

logging.basicConfig(level=logging.INFO)
log = logging.getLogger("la-llave")

VERSION = "v2"
MODULOS = ["semillas", "autocomplete", "competidores", "preguntas", "volumen", "deduplicado",
           "hueco", "excel"]
MARGEN_IP_SEG = 3600          # otra recogida en la última hora → ritmo más prudente
XLSX = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"

PROYECTOS: Dict[str, dict] = {}
_tareas = set()
_ultima_recogida = {"fin": 0.0}


def _nuevo_estado(briefing: Briefing) -> dict:
    inicio = time.time()
    pid = uuid.uuid4().hex[:12]
    return {
        "id": pid,
        "marca": briefing.marca,
        "carpeta": almacen.carpeta(pid, briefing.marca, inicio),
        "estado": "corriendo",
        "inicio": inicio,
        "fin": None,
        "modulos": {m: {"estado": "pendiente", "detalle": "", "hechas": 0, "total": 0} for m in MODULOS},
        "presupuesto_seg": PRESUPUESTO_SEG,
        "resumen": None,
        "error": None,
        "bloqueo": None,
    }


async def _recoger(briefing: Briefing, est: dict):
    mod = est["modulos"]

    def marcar(m, estado, detalle="", hechas=None, total=None):
        mod[m]["estado"] = estado
        if detalle:
            mod[m]["detalle"] = detalle
        if hechas is not None:
            mod[m]["hechas"] = hechas
        if total is not None:
            mod[m]["total"] = total

    avisos: List[Aviso] = []
    tabla = Tabla(briefing, avisos)

    # 1 · Semillas
    marcar("semillas", "corriendo")
    semillas = generar_semillas(briefing)
    n_prior = sum(s.prioritaria for s in semillas)
    marcar("semillas", "hecho", f"{len(semillas)} semillas ({n_prior} prioritarias)",
           len(semillas), len(semillas))

    # Otra recogida reciente desde la misma IP: pausas dobles y aviso
    factor = 1.0
    hace = time.time() - _ultima_recogida["fin"]
    if hace < MARGEN_IP_SEG:
        factor = 2.0
        avisos.append(Aviso("ritmo prudente", "autocomplete",
                            f"Hubo otra recogida hace {int(hace // 60)} min desde este servidor: "
                            "pausas dobles para que Google no bloquee"))

    # 2, 3 y 5 · Autocomplete, preguntas y competidores en paralelo (servidores distintos)
    ac = Autocomplete(tabla, avisos, briefing.mercado,
                      lambda d, h, t: marcar("autocomplete", "corriendo", d, h, t), factor)

    async def correr_autocomplete():
        marcar("autocomplete", "corriendo")
        await ac.ejecutar(semillas, briefing.segundo_nivel)
        estado = "hecho" if not ac.parado else ("parcial" if ac.parado == "tiempo" else "bloqueado")
        if estado == "bloqueado":
            est["bloqueo"] = (f"Google bloqueó el autocomplete tras {ac.hechas} consultas "
                              f"(última semilla: «{ac.ultima_semilla}»). Se entrega lo recogido; "
                              "espera una hora antes de otra recogida.")
        marcar("autocomplete", estado, f"{ac.hechas} consultas · {len(tabla)} keywords únicas hasta ahora")

    paginas: List[PaginaCompetidor] = []

    async def correr_competidores():
        objetivos = [(c, "", None) for c in briefing.competidores]
        if briefing.web_estado == "existente" and briefing.url_web:
            objetivos.append((briefing.url_web, "(propia)", briefing.sitemap_url))
        if not briefing.competidores:
            avisos.append(Aviso("sin competidores", "briefing",
                                "No se dieron competidores: sin espejo ni hueco"))
        if not objetivos:
            marcar("competidores", "omitido", "Sin competidores en el briefing")
            return
        marcar("competidores", "corriendo", total=len(objetivos))
        espejo = Espejo(avisos, briefing.zonas(), lambda d: marcar("competidores", "corriendo", d))
        resultados = await asyncio.gather(*(espejo.leer(u, et, sm) for u, et, sm in objetivos),
                                          return_exceptions=True)
        leidos = 0
        for (u, et, _), res in zip(objetivos, resultados):
            if isinstance(res, Exception):
                avisos.append(Aviso("sitemap caído", u, f"Error inesperado: {type(res).__name__}: {res}"))
                continue
            if res:
                leidos += 1
            for p in res:
                p.propia = bool(et)
            paginas.extend(res)
            modulo = "web propia" if et else "competidores"
            for p in res:
                if p.keyword_inferida and p.patron in ("servicio", "servicio-ciudad", "blog", "home"):
                    tabla.add(p.keyword_inferida, modulo, dominio_de(u))
        marcar("competidores", "hecho", f"{leidos} de {len(objetivos)} dominios leídos · {len(paginas)} páginas",
               leidos, len(objetivos))

    preguntas: List[Pregunta] = []
    dfs_coste = 0.0
    estado_preguntas = ""

    async def correr_preguntas():
        nonlocal dfs_coste, estado_preguntas
        if not briefing.preguntas:
            estado_preguntas = "desactivado en el briefing"
        elif not dataforseo.activo():
            estado_preguntas = "sin clave de DataForSEO en el servidor"
            avisos.append(Aviso("módulo desactivado", "People Also Ask",
                                "Falta DATAFORSEO_LOGIN / DATAFORSEO_PASSWORD en Render. "
                                "La pestaña Preguntas solo trae las del autocomplete."))
        else:
            marcar("preguntas", "corriendo")
            elegidas = semillas_para_preguntas(semillas, briefing)
            encontradas, dfs = await recoger_paa(
                elegidas, tabla, briefing, avisos,
                lambda d, h, t: marcar("preguntas", "corriendo", f"SERP de «{d}»", h, t))
            preguntas.extend(encontradas)
            dfs_coste += dfs.coste
            estado_preguntas = f"{len(encontradas)} de {len(elegidas)} SERP (DataForSEO)"
        marcar("preguntas", "omitido" if "sin clave" in estado_preguntas or "desactivado" in estado_preguntas
               else "hecho", estado_preguntas)

    await asyncio.gather(correr_autocomplete(), correr_competidores(), correr_preguntas())

    # 6 · Volumen en cascada: Search Console → Planner → DataForSEO → sin dato
    marcar("volumen", "corriendo")
    fuentes = []
    gsc, planner, dfs_vol = {}, {}, {}
    if briefing.gsc_csv:
        gsc = leer_gsc(briefing.gsc_csv, avisos, briefing.gsc_nombre or "CSV Search Console")
        for d in gsc.values():
            tabla.add(d["texto"], "search console", "—")
        fuentes.append("Search Console")
    if briefing.planner_csv:
        planner = leer_planner(briefing.planner_csv, avisos, briefing.planner_nombre or "CSV Keyword Planner")
        for d in planner.values():
            tabla.add(d["texto"], "keyword planner", "—")
        fuentes.append("Keyword Planner")

    marcar("deduplicado", "corriendo")
    tabla.finalizar()
    marcar("deduplicado", "hecho", f"{len(tabla)} keywords únicas · {len(tabla.descartadas)} descartadas")

    if briefing.volumen_dataforseo and dataforseo.activo():
        pendientes = [k.texto for k in tabla.ordenadas()
                      if k.clave not in gsc and k.clave not in planner and dataforseo.apta_para_ads(k.texto)]
        pendientes = pendientes[:dataforseo.MAX_KEYWORDS_VOLUMEN]
        marcar("volumen", "corriendo", f"DataForSEO: {len(pendientes)} keywords")
        cliente = dataforseo.DataForSEO(briefing.mercado)
        try:
            async with httpx.AsyncClient() as client:
                dfs_vol = await cliente.volumen(client, pendientes)
            fuentes.append("DataForSEO")
        except Exception as e:
            avisos.append(Aviso("sin volumen", "DataForSEO", f"No respondió: {e}"))
        dfs_coste += cliente.coste
    elif briefing.volumen_dataforseo:
        avisos.append(Aviso("módulo desactivado", "DataForSEO (volumen)",
                            "Sin clave en el servidor: el volumen solo sale de los CSV subidos"))
    por_fuente = aplicar_volumen(tabla, gsc, planner, dfs_vol, avisos, fuentes)
    comprobar_honestidad(tabla)
    con_vol = sum(v for k, v in por_fuente.items() if k != "sin dato")
    marcar("volumen", "hecho", " · ".join(f"{k}: {v}" for k, v in por_fuente.items()))

    # Hueco frente a la competencia
    marcar("hueco", "corriendo")
    etiquetar_paginas(tabla, paginas)
    cuenta_hueco = calcular_hueco(list(tabla.kws.values()), paginas)
    marcar("hueco", "hecho" if paginas else "omitido",
           f"{cuenta_hueco['sí']} keywords con hueco" if paginas else "Sin páginas espejadas")

    preguntas.extend(p for p in preguntas_del_autocomplete(tabla)
                     if p.pregunta not in {q.pregunta for q in preguntas})

    # Excel y guardado
    marcar("excel", "corriendo")
    duracion = round(time.time() - est["inicio"])
    fecha = almacen.hora_madrid(est["inicio"]).strftime("%d/%m/%Y %H:%M")
    extra = {
        "fecha": fecha, "duracion_seg": duracion, "consultas": ac.hechas,
        "parado": {None: "", "tiempo": "parado por tiempo"}.get(ac.parado, f"bloqueado: {ac.parado}"),
        "preguntas_estado": estado_preguntas, "coste_dfs": dataforseo.coste_legible(dfs_coste),
        "volumen_por_fuente": por_fuente,
    }
    por_intencion: Dict[str, int] = {}
    for k in tabla.kws.values():
        por_intencion[k.intencion] = por_intencion.get(k.intencion, 0) + 1
    dominios_leidos = sorted({p.dominio for p in paginas})
    resumen = {
        "id": est["id"], "marca": briefing.marca, "fecha": fecha, "version": VERSION,
        "keywords": len(tabla), "descartadas": len(tabla.descartadas),
        "por_intencion": por_intencion, "semillas": len(semillas),
        "consultas_autocomplete": ac.hechas, "autocomplete_parado": ac.parado,
        "dominios_leidos": dominios_leidos, "paginas_competidores": len(paginas),
        "con_volumen": con_vol, "volumen_por_fuente": por_fuente,
        "preguntas": len(preguntas), "hueco": cuenta_hueco,
        "familias": len({k.familia for k in tabla.kws.values()}),
        "coste_dataforseo": round(dfs_coste, 4), "avisos": len(avisos), "duracion_seg": duracion,
    }
    texto_resumen = (f"{len(tabla)} keywords únicas · {len(semillas)} semillas · "
                     f"{len(dominios_leidos)} dominios espejados · {fecha}")
    pestanas = construir_pestanas(briefing, tabla, semillas, paginas, avisos, preguntas, extra)

    ruta_tmp = almacen.ruta_local(est["carpeta"], almacen.nombre_excel(briefing.marca))
    os.makedirs(os.path.dirname(ruta_tmp), exist_ok=True)
    generar_excel(ruta_tmp, briefing, pestanas, texto_resumen)
    with open(ruta_tmp, "rb") as f:
        xlsx = f.read()
    archivos = {
        almacen.nombre_excel(briefing.marca): xlsx,
        "briefing.json": briefing.model_dump_json(indent=1).encode("utf-8"),
        "resumen.json": json.dumps(resumen, ensure_ascii=False, indent=1).encode("utf-8"),
        "pestanas.json": json.dumps(a_json(pestanas), ensure_ascii=False).encode("utf-8"),
    }
    fallos = await asyncio.to_thread(almacen.guardar, est["carpeta"], archivos)
    for f in fallos:
        log.warning("No se pudo subir a Supabase: %s", f)
    est["pestanas"] = pestanas
    marcar("excel", "hecho", "Guardado y listo para descargar")
    est["resumen"] = resumen


async def _lanzar(briefing: Briefing, est: dict):
    try:
        await _recoger(briefing, est)
        est["estado"] = "terminado"
    except Exception as e:                      # se entrega el error, no se esconde
        log.exception("Fallo en la recogida")
        est["estado"] = "error"
        est["error"] = f"{type(e).__name__}: {e}"
    finally:
        est["fin"] = time.time()
        _ultima_recogida["fin"] = est["fin"]


def lanzar(briefing: Briefing) -> dict:
    """Crea la recogida y la arranca en segundo plano (lo usan la API y el MCP)."""
    est = _nuevo_estado(briefing)
    PROYECTOS[est["id"]] = est
    tarea = asyncio.create_task(_lanzar(briefing, est))
    _tareas.add(tarea)
    tarea.add_done_callback(_tareas.discard)
    return est


def estado_publico(pid: str) -> dict:
    """Estado en memoria; si el servidor se reinició, el resumen guardado."""
    if not re.fullmatch(r"[0-9a-f]{12}", pid):
        raise KeyError(pid)
    est = PROYECTOS.get(pid)
    if est:
        fin = est["fin"] or time.time()
        return {k: v for k, v in est.items() if k != "pestanas"} | {"segundos": round(fin - est["inicio"])}
    entrada = almacen.buscar(pid)
    if not entrada:
        raise KeyError(pid)
    resumen = json.loads(almacen.leer(entrada["carpeta"], "resumen.json") or b"{}")
    return {"id": pid, "marca": entrada["marca"], "carpeta": entrada["carpeta"], "estado": "terminado",
            "segundos": resumen.get("duracion_seg", 0), "presupuesto_seg": PRESUPUESTO_SEG,
            "modulos": {m: {"estado": "hecho", "detalle": "", "hechas": 0, "total": 0} for m in MODULOS},
            "resumen": resumen, "error": None, "bloqueo": None}


def _carpeta(pid: str) -> str:
    try:
        est = estado_publico(pid)
    except KeyError:
        raise HTTPException(404, "Recogida no encontrada")
    if est["estado"] != "terminado":
        raise HTTPException(409, "La recogida todavía no ha terminado")
    return est["carpeta"]


def pestanas_de(pid: str):
    est = PROYECTOS.get(pid)
    if est and est.get("pestanas"):
        return est["pestanas"]
    contenido = almacen.leer(_carpeta(pid), "pestanas.json")
    if not contenido:
        raise HTTPException(404, "No están guardadas las pestañas de esa recogida")
    return de_json(json.loads(contenido))


# ── App ─────────────────────────────────────────────────────────────────────
mcp = crear_mcp()
mcp_http = mcp.streamable_http_app(**opciones_http())   # crea también el gestor de sesiones


@asynccontextmanager
async def lifespan(_app):
    async with mcp.session_manager.run():
        yield


app = FastAPI(title="La Llave · Keyword Research API", version=VERSION, lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def raiz():
    return {"ok": True, "servicio": "la-llave", "version": VERSION}


@app.get("/cascada")
def get_cascada():
    return {"cascada": cascada(),
            "modificadores_por_defecto": MODIFICADORES_POR_DEFECTO,
            "ruido_por_defecto": ruido_por_defecto(),
            "dataforseo": dataforseo.activo(),
            "supabase": almacen.supabase_activo(),
            "recogida_reciente_min": (int((time.time() - _ultima_recogida["fin"]) // 60)
                                      if time.time() - _ultima_recogida["fin"] < MARGEN_IP_SEG else None)}


@app.post("/proyectos")
async def crear(briefing: Briefing):
    return {"id": lanzar(briefing)["id"]}


@app.get("/proyectos/{pid}")
def estado(pid: str):
    try:
        return estado_publico(pid)
    except KeyError:
        raise HTTPException(404, "Recogida no encontrada")


@app.get("/proyectos/{pid}/excel")
def excel(pid: str):
    carpeta = _carpeta(pid)
    marca = estado_publico(pid)["marca"]
    contenido = almacen.leer(carpeta, almacen.nombre_excel(marca))
    if contenido is None:
        raise HTTPException(404, "El Excel no está guardado")
    return Response(contenido, media_type=XLSX,
                    headers={"Content-Disposition": f'attachment; filename="{almacen.nombre_excel(marca)}"'})


@app.get("/proyectos/{pid}/briefing")
def briefing_json(pid: str):
    contenido = almacen.leer(_carpeta(pid), "briefing.json")
    if contenido is None:
        raise HTTPException(404, "Briefing no guardado")
    return Response(contenido, media_type="application/json",
                    headers={"Content-Disposition": 'attachment; filename="briefing.json"'})


@app.get("/proyectos/{pid}/csv/{pestana}")
def csv_pestana(pid: str, pestana: str):
    pestanas = pestanas_de(pid)
    nombre = next((n for n in pestanas if n.lower() == pestana.lower()), None)
    if not nombre:
        raise HTTPException(404, f"Pestaña desconocida. Disponibles: {', '.join(pestanas)}")
    return Response(generar_csv(pestanas, nombre), media_type="text/csv; charset=utf-8",
                    headers={"Content-Disposition": f'attachment; filename="{nombre.lower()}.csv"'})


@app.get("/recogidas")
def recogidas():
    return {"recogidas": almacen.leer_indice()[:50]}


# El servidor MCP va al final: atiende solo su ruta; todo lo demás ya lo ha atendido FastAPI
app.mount("/", mcp_http)
