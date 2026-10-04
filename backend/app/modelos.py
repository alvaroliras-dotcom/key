"""Modelos de entrada (el briefing del proyecto) y estructuras compartidas."""

from dataclasses import dataclass, field
from typing import Dict, List, Literal, Optional

from pydantic import BaseModel, Field, field_validator


class Servicio(BaseModel):
    nombre: str
    prioritario: bool = False


class Briefing(BaseModel):
    # Obligatorios
    dominio: str = Field(..., min_length=3)
    marca: str = Field(..., min_length=2)
    sector: str = Field(..., min_length=2)
    servicios: List[Servicio] = Field(..., min_length=1)
    objetivo: Literal["urgencias", "leads", "marca", "ventas"]
    sede: str = Field(..., min_length=2)
    zona_principal: str = Field(..., min_length=2)
    zonas_secundarias: List[str] = []
    alcance: Literal["local", "provincial", "nacional"]
    web_estado: Literal["nueva", "existente"]

    # Opcionales
    url_web: Optional[str] = None
    sitemap_url: Optional[str] = None
    no_ofrece: List[str] = []              # lista negra del cliente; admite «término salvo excepción»
    # Lista negra por defecto (países, ciudades lejanas, formación). None = la de fábrica;
    # [] = desactivada. Las zonas del briefing nunca se filtran aunque estén aquí.
    ruido: Optional[List[str]] = None
    gsc_csv: Optional[str] = None          # contenido del CSV de Search Console (texto)
    gsc_nombre: Optional[str] = None       # nombre del archivo, para trazabilidad
    planner_csv: Optional[str] = None      # contenido del CSV de Keyword Planner (texto)
    planner_nombre: Optional[str] = None
    competidores: List[str] = []
    jerga: List[str] = []                  # «término» o «término = servicio»
    mercado: str = "es-ES"

    # Modificadores editables por intención. Admiten «{s}» como hueco del servicio;
    # sin hueco se añaden detrás («urgente» → «cerrajero urgente»).
    modificadores: Optional[Dict[str, List[str]]] = None

    # Opciones de la recogida
    segundo_nivel: bool = False
    preguntas: bool = True                 # People Also Ask y relacionadas (DataForSEO)
    volumen_dataforseo: bool = True        # volumen de pago para lo que no tenga GSC ni Planner

    @field_validator("servicios")
    @classmethod
    def _servicios_no_vacios(cls, v):
        v = [s for s in v if s.nombre.strip()]
        if not v:
            raise ValueError("Hace falta al menos un servicio")
        return v

    @field_validator("competidores")
    @classmethod
    def _max_competidores(cls, v):
        v = [c.strip() for c in v if c and c.strip()]
        if len(v) > 5:
            raise ValueError("Máximo 5 competidores")
        return v

    def zonas(self) -> List[str]:
        """Todas las zonas sin repetir, la principal primero."""
        vistas, out = set(), []
        for z in [self.zona_principal, self.sede, *self.zonas_secundarias]:
            z = (z or "").strip()
            if z and z.lower() not in vistas:
                vistas.add(z.lower())
                out.append(z)
        return out


@dataclass
class Semilla:
    texto: str
    servicio: str
    intencion: str
    geo: str = ""
    tipo: str = "base"            # base | variante | marca | jerga
    prioritaria: bool = False
    sugerencias: int = 0          # cuántas sugerencias produjo (cobertura)
    consultas: int = 0
    estado: str = "pendiente"     # pendiente | hecha | parcial | sin consultar


@dataclass
class Aviso:
    tipo: str
    elemento: str
    detalle: str


@dataclass
class PaginaCompetidor:
    dominio: str
    url: str
    title: str = ""
    h1: str = ""
    meta_description: str = ""
    h2: str = ""
    patron: str = ""
    keyword_inferida: str = ""
    # Calculado por el módulo de hueco
    servicio: str = ""
    geo: str = ""
    fiabilidad: str = ""          # fuerte | inferencia débil | sin servicio
    propia: bool = False


@dataclass
class Descartada:
    keyword: str
    motivo: str                   # lista negra del cliente | ruido: país… | ruido: formación…
    termino: str
    modulo: str
    semilla: str
    veces: int = 1


@dataclass
class Pregunta:
    pregunta: str
    tipo: str                     # People Also Ask | búsqueda relacionada
    semilla: str
    servicio: str = ""
    geo: str = ""


@dataclass
class Keyword:
    clave: str
    variantes: Dict[str, int] = field(default_factory=dict)
    semilla_origen: str = ""
    modulos: List[str] = field(default_factory=list)
    apariciones: int = 0
    mejor_posicion: Optional[int] = None
    intencion: str = ""
    geo: str = ""
    servicio: str = ""
    familia: str = ""
    volumen: Optional[float] = None
    volumen_texto: str = ""       # rango del Planner («1K – 10K»); se escribe en lugar del número
    fuente_volumen: str = ""
    marca_estimacion: str = ""
    clics: Optional[float] = None
    posicion_media: Optional[float] = None
    cpc: Optional[float] = None
    hueco: str = ""               # sí | no | — (sin servicio o sin competencia comparable)
    competidores_con_pagina: str = ""
    pagina_propia: str = ""
    fiabilidad_hueco: str = ""

    @property
    def texto(self) -> str:
        # La variante más vista; a igualdad, la que lleva tildes (mejor escrita)
        return max(self.variantes.items(),
                   key=lambda kv: (kv[1], sum(c in "áéíóúü" for c in kv[0]), -len(kv[0])))[0]
