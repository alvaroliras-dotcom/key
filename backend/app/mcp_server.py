"""
Conector MCP de La Llave (petición 4 de Nuria): para invocarla desde claude.ai sin
pasar por el formulario. Va en el mismo backend, en la ruta /{MCP_RUTA}.

Herramientas:
  lanzar_recogida(briefing) → id
  estado(id)                → progreso por módulo; al terminar, el resumen y la Lectura
  descargar_excel(id)       → enlaces al Excel, al briefing y a cada pestaña en CSV
  leer_pestana(id, pestana) → filas de una pestaña, por tramos (para leerla desde claude.ai)

Seguridad: el conector no tiene usuario ni contraseña. Lo protege una ruta secreta:
pon en MCP_RUTA algo largo e imposible de adivinar (p. ej. «mcp-7f3c9e…») y comparte
la URL solo con quien deba usarla.
"""

import os

from mcp.server.mcpserver import MCPServer
from mcp.server.transport_security import TransportSecuritySettings

from .modelos import Briefing

MCP_RUTA = os.getenv("MCP_RUTA", "mcp").strip("/")
URL_PUBLICA = os.getenv("PUBLIC_URL", "http://localhost:8000").rstrip("/")
MAX_FILAS = 300

INSTRUCCIONES = """La Llave recoge la materia prima de keywords de un proyecto (autocomplete en sopa de
letras, espejo de competidores por sitemap, preguntas, volumen con fuente) y la entrega en un Excel.
No decide arquitectura ni asigna keywords: eso es de Nuria.
Flujo: lanzar_recogida(briefing) → estado(id) cada minuto hasta «terminado» (tarda 7-9 min) →
descargar_excel(id) o leer_pestana(id, "Lectura" / "Familias" / "Keywords"…).
Regla: todo volumen lleva fuente; una celda de volumen vacía significa «sin dato fiable», nunca cero."""


def opciones_http() -> dict:
    # El servidor es público (Render): la protección anti DNS-rebinding es para servidores
    # locales y aquí rechazaría el Host de Render. La protección real es la ruta secreta.
    return {"streamable_http_path": f"/{MCP_RUTA}", "stateless_http": True, "json_response": True,
            "host": "0.0.0.0",
            "transport_security": TransportSecuritySettings(enable_dns_rebinding_protection=False)}


def _enlaces(pid: str) -> dict:
    from . import main
    pestanas = list(main.pestanas_de(pid).keys())
    return {"excel": f"{URL_PUBLICA}/proyectos/{pid}/excel",
            "briefing_json": f"{URL_PUBLICA}/proyectos/{pid}/briefing",
            "csv": {p: f"{URL_PUBLICA}/proyectos/{pid}/csv/{p}" for p in pestanas}}


def crear_mcp() -> MCPServer:
    mcp = MCPServer("La Llave", title="La Llave · keyword research de GYF", instructions=INSTRUCCIONES)

    @mcp.tool()
    async def lanzar_recogida(briefing: Briefing) -> dict:
        """Lanza una recogida de keywords con el briefing del proyecto. Devuelve el id para
        consultar el estado. Servicios prioritarios: prioritario=true. Lista negra del cliente:
        no_ofrece (admite «gratis salvo auditoría»). ruido=null usa la lista negra por defecto.
        gsc_csv / planner_csv: el texto del CSV, si se tiene."""
        from . import main
        est = main.lanzar(briefing)
        return {"id": est["id"], "estado": "corriendo",
                "siguiente": "Consulta estado(id) cada minuto; tarda 7-9 minutos."}

    @mcp.tool()
    def estado(id: str) -> dict:
        """Progreso de una recogida por módulo. Al terminar incluye el resumen y la pestaña
        Lectura (recuentos por intención, servicio, zona, top Search Console, huecos…)."""
        from . import main
        try:
            est = main.estado_publico(id)
        except KeyError:
            return {"error": f"No existe la recogida {id}"}
        out = {"id": id, "estado": est["estado"], "segundos": est.get("segundos"),
               "modulos": {m: f"{v['estado']} · {v['detalle']}".strip(" ·")
                           for m, v in est["modulos"].items()},
               "bloqueo": est.get("bloqueo"), "error": est.get("error")}
        if est["estado"] == "terminado":
            out["resumen"] = est["resumen"]
            cols, filas, _, _ = main.pestanas_de(id)["Lectura"]
            out["lectura"] = [dict(zip(cols, f)) for f in filas]
        return out

    @mcp.tool()
    def descargar_excel(id: str) -> dict:
        """Enlaces de descarga de una recogida terminada: el Excel con identidad GYF, el
        briefing en JSON (para relanzar) y cada pestaña en CSV."""
        from . import main
        try:
            if main.estado_publico(id)["estado"] != "terminado":
                return {"error": "La recogida todavía no ha terminado"}
            return _enlaces(id)
        except KeyError:
            return {"error": f"No existe la recogida {id}"}

    @mcp.tool()
    def leer_pestana(id: str, pestana: str, desde: int = 0, cuantas: int = 200) -> dict:
        """Lee filas de una pestaña de una recogida terminada (Lectura, Keywords, Familias,
        Preguntas, Competidores, Semillas, Descartadas, Avisos, Briefing), por tramos de
        hasta 300 filas. Devuelve columnas, filas y el total."""
        from . import main
        try:
            pestanas = main.pestanas_de(id)
        except Exception:
            return {"error": f"No hay datos de la recogida {id} (¿ha terminado?)"}
        nombre = next((n for n in pestanas if n.lower() == pestana.lower()), None)
        if not nombre:
            return {"error": f"Pestaña desconocida. Disponibles: {', '.join(pestanas)}"}
        cols, filas, _, nota = pestanas[nombre]
        cuantas = max(1, min(cuantas, MAX_FILAS))
        return {"pestana": nombre, "nota": nota, "columnas": cols, "total": len(filas),
                "desde": desde, "filas": filas[desde:desde + cuantas]}

    return mcp
