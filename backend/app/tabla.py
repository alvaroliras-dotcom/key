"""
La tabla única de keywords: todos los módulos vuelcan aquí. Deduplica por clave
normalizada, guarda de qué módulo y semilla salió cada keyword, filtra el ruido
(lista negra del cliente + lista por defecto) y etiqueta intención, geo, servicio
y familia.
"""

import re
from typing import Dict, List, Optional

from .geo_es import LUGARES
from .modelos import Aviso, Briefing, Descartada, Keyword
from .normalizar import clave, limpiar, sin_tildes, tokens

INFO_INICIO = {"como", "que", "cual", "cuales", "cuando", "donde", "quien", "por", "porque", "para"}
INFO = {"cuanto", "cuanta", "guia", "tutorial", "consejo", "truco", "significado",
        "tipo", "idea", "funciona", "sirve", "hacer", "pasos", "paso", "pdf", "libro",
        "ventaja", "desventaja", "definicion", "ejemplo", "concepto", "objetivo", "herramienta",
        "importancia", "caracteristica", "historia", "curso", "tesis", "master", "wikipedia",
        "articulo", "aprender", "manual", "plantilla", "temario", "funcion",
        # Quien estudia el oficio no es cliente
        "carrera", "fp", "grado", "estudiar", "escuela", "universidad", "salida", "sueldo",
        "salario", "bootcamp", "certificacion", "empleo", "trabajo", "practica", "oposicion"}
# Interrogativos con tilde en cualquier posición («seo local qué es») = pregunta
_PREGUNTA = re.compile(r"\b(qué|cómo|cuánto|cuánta|cuál|cuáles|dónde|cuándo|quién)\b")
# …y sin tilde, las fórmulas que delatan pregunta aunque no vayan al principio
_PREGUNTA_SIN_TILDE = re.compile(r"\b(que es|que son|para que|como se|como hacer|como funciona|como crear)\b")
COMPARATIVA = {"mejor", "opinion", "vs", "comparativa", "ranking", "top", "homologado",
               "recomendado", "fiable", "confianza", "resena", "valoracion", "diferencia",
               "alternativa", "versus"}
TRANSACCIONAL = {"urgente", "urgencia", "24h", "24", "hora", "precio", "presupuesto", "barato",
                 "economico", "tarifa", "coste", "costo", "contratar", "reparar", "reparacion",
                 "instalar", "instalacion", "cambiar", "cambio", "abrir", "apertura", "arreglar",
                 "comprar", "oferta", "rapido", "domicilio", "ahora", "hoy", "noche", "festivo",
                 "servicio", "empresa", "tienda", "venta", "alquiler", "negocio", "pyme",
                 "autonomo", "profesional", "contratacion"}
CERCA = {"cerca", "cercano", "cercana", "proximo", "zona"}

ORDEN_INTENCION = {"transaccional": 0, "local": 1, "marca": 2, "comparativa": 3, "informacional": 4}

# Lista negra por defecto (decisión de Nuria, 4 oct 2026). Editable desde el formulario.
# No lleva «online» a secas: «agencia seo online» puede ser cliente.
RUIDO_POR_DEFECTO = {
    "país": ["chile", "méxico", "argentina", "colombia", "perú"],
    "ciudad fuera de alcance": ["barcelona", "valencia", "sevilla"],
    "formación y empleo": ["curso", "carrera", "fp", "máster", "grado", "sueldo", "empleo",
                           "pdf", "libro"],
}
_CATEGORIA_RUIDO = {clave(t): cat for cat, ts in RUIDO_POR_DEFECTO.items() for t in ts}


def ruido_por_defecto() -> List[str]:
    return [t for ts in RUIDO_POR_DEFECTO.values() for t in ts]


def _reglas(lineas: List[str]):
    """«gratis salvo auditoría, sherlock» → (término, tokens, [tokens de excepciones])."""
    out = []
    for linea in lineas:
        termino, _, salvo = linea.partition(" salvo ")
        if termino.strip() and tokens(termino):
            out.append((termino.strip(), tokens(termino),
                        [tokens(e) for e in salvo.split(",") if tokens(e)]))
    return out


class Tabla:
    def __init__(self, briefing: Briefing, avisos: List[Aviso]):
        self.briefing = briefing
        self.avisos = avisos
        self.kws: Dict[str, Keyword] = {}
        self.descartadas: Dict[str, Descartada] = {}

        zonas_claves = {clave(z) for z in briefing.zonas()}
        ruido = ruido_por_defecto() if briefing.ruido is None else briefing.ruido
        # Una zona del briefing nunca es ruido (un cliente de Valencia quiere «valencia»)
        self.ruido_ignorado = [t for t in ruido if clave(t.partition(" salvo ")[0]) in zonas_claves]
        ruido = [t for t in ruido if t not in self.ruido_ignorado]
        self._negra = [("lista negra del cliente", *r) for r in _reglas(briefing.no_ofrece)]
        self._negra += [(f"ruido: {_CATEGORIA_RUIDO.get(clave(r[0]), 'lista por defecto')}", *r)
                        for r in _reglas(ruido)]

        self._zonas = [(z, f" {clave(z)} ") for z in briefing.zonas()]
        # Lugares conocidos que no están en el briefing, los nombres largos primero
        self._fuera = sorted(((n, f" {clave(n)} ") for n in LUGARES if clave(n) not in zonas_claves),
                             key=lambda x: -len(x[1]))
        self._marca = tokens(briefing.marca)

        # Servicios y jerga → tokens, más largos primero para que gane el más específico
        servs = [(s.nombre, tokens(s.nombre)) for s in briefing.servicios]
        for linea in briefing.jerga:
            if "=" in linea:
                termino, serv = (p.strip() for p in linea.split("=", 1))
                servs.append((serv or termino, tokens(termino)))
            elif linea.strip():
                servs.append((f"{linea.strip()} (jerga)", tokens(linea)))
        self._servicios = sorted([s for s in servs if s[1]], key=lambda s: -len(s[1]))

    # ── Alta ────────────────────────────────────────────────────────────────
    def add(self, texto: str, modulo: str, semilla: str = "", posicion: Optional[int] = None) -> bool:
        texto = limpiar(texto)
        if not texto or len(texto) > 120:
            return False
        tk = tokens(texto)
        k = clave(texto)
        for motivo, termino, tneg, excepciones in self._negra:
            if tneg <= tk and not any(e <= tk for e in excepciones):
                d = self.descartadas.get(k)
                if d:
                    d.veces += 1
                else:
                    self.descartadas[k] = Descartada(texto, motivo, termino, modulo, semilla)
                return False
        kw = self.kws.get(k)
        if kw is None:
            kw = self.kws[k] = Keyword(clave=k, semilla_origen=semilla)
        kw.variantes[texto] = kw.variantes.get(texto, 0) + 1
        kw.apariciones += 1
        if modulo not in kw.modulos:
            kw.modulos.append(modulo)
        if posicion is not None and (kw.mejor_posicion is None or posicion < kw.mejor_posicion):
            kw.mejor_posicion = posicion
        return True

    def es_ruido(self, texto: str) -> str:
        """Motivo si el texto cae en la lista negra (sin darlo de alta); «» si está limpio."""
        tk = tokens(limpiar(texto))
        for motivo, termino, tneg, excepciones in self._negra:
            if tneg <= tk and not any(e <= tk for e in excepciones):
                return motivo
        return ""

    def __len__(self):
        return len(self.kws)

    # ── Etiquetado ──────────────────────────────────────────────────────────
    def geo(self, k: str) -> str:
        """Zona del briefing; si no, lugar conocido «(fuera de briefing)»; si no, «cerca de mí»."""
        con_espacios = f" {k} "
        for nombre, patron in self._zonas:
            if patron in con_espacios:
                return nombre
        for nombre, patron in self._fuera:
            if patron in con_espacios:
                return f"{nombre} (fuera de briefing)"
        if CERCA & set(k.split()):
            return "cerca de mí"
        return ""

    def servicio(self, tk: set) -> str:
        for nombre, ts in self._servicios:
            if ts <= tk:
                return nombre
        return ""

    def _tokens_servicio(self, nombre: str) -> set:
        return next((ts for n, ts in self._servicios if n == nombre), set())

    def intencion(self, texto: str, tk: set, geo: str, servicio: str) -> str:
        palabras = sin_tildes(texto).split()
        if ((palabras and palabras[0] in INFO_INICIO) or (INFO & tk) or _PREGUNTA.search(texto)
                or _PREGUNTA_SIN_TILDE.search(" ".join(palabras))):
            return "informacional"
        if COMPARATIVA & tk:
            return "comparativa"
        if self._marca and self._marca <= tk:
            return "marca"
        if TRANSACCIONAL & tk:
            return "transaccional"
        if geo:
            return "local"
        # Término de servicio a secas («diseño web», «agencia seo madrid»): comercial.
        # Una cola larga sin modificador comercial («analítica web para medir
        # resultados de marketing») es de alguien que se informa.
        if servicio and len(tk) <= len(self._tokens_servicio(servicio)) + 1:
            return "transaccional"
        return "informacional"

    @staticmethod
    def familia(servicio: str, geo: str, intencion: str) -> str:
        """Vista de lectura: servicio + geo + intención. Las zonas de fuera se agrupan."""
        if not geo:
            g = "sin zona"
        elif geo.endswith("(fuera de briefing)"):
            g = "otras zonas"
        else:
            g = geo
        return f"{servicio or 'sin servicio'} · {g} · {intencion}"

    def etiquetar(self):
        for kw in self.kws.values():
            texto = kw.texto
            tk = tokens(texto)
            kw.geo = self.geo(kw.clave)
            kw.servicio = self.servicio(tk)
            kw.intencion = self.intencion(texto, tk, kw.geo, kw.servicio)
            kw.familia = self.familia(kw.servicio, kw.geo, kw.intencion)

    def finalizar(self):
        self.etiquetar()
        # Una keyword puede descartarse en un módulo y entrar limpia por otro: manda la tabla
        for k in [k for k in self.descartadas if k in self.kws]:
            self.descartadas.pop(k)
        por_motivo: Dict[str, int] = {}
        for d in self.descartadas.values():
            por_motivo[d.motivo] = por_motivo.get(d.motivo, 0) + 1
        for motivo, n in sorted(por_motivo.items(), key=lambda x: -x[1]):
            self.avisos.append(Aviso("descartadas", motivo,
                                     f"{n} keyword(s) eliminadas; están en la pestaña Descartadas por si hay que rescatar alguna"))
        for t in self.ruido_ignorado:
            self.avisos.append(Aviso("ruido ignorado", t,
                                     "Está en la lista negra por defecto pero es zona del briefing: no se filtra"))

    def ordenadas(self) -> List[Keyword]:
        return sorted(self.kws.values(), key=lambda k: (
            ORDEN_INTENCION.get(k.intencion, 9), -k.apariciones, -(k.volumen or 0), k.texto))
