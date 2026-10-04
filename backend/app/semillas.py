"""
Módulo 1 · Generador de semillas.

Combina servicio × modificador de intención × geo. Las semillas «base» pasan por
el autocomplete; las «variante» (plural, sin tilde) solo se consultan solas,
porque Google ya sugiere casi lo mismo para ambas formas.
"""

from typing import Dict, List, Tuple

from .modelos import Briefing, Semilla
from .normalizar import limpiar, pluralizar_frase, sin_tildes

MODIFICADORES_POR_DEFECTO: Dict[str, List[str]] = {
    "transaccional": [
        "urgente", "24 horas", "24h", "precio", "presupuesto", "barato",
        "económico", "reparar {s}", "instalar {s}",
    ],
    "local": ["cerca de mí", "a domicilio"],
    "informacional": ["cómo {s}", "qué {s}", "cuánto cuesta {s}"],
    "comparativa": ["mejor {s}", "opiniones", "homologado", "de confianza"],
}

# Qué modificadores pesan más según el objetivo del briefing: esas semillas
# pasan la sopa de letras completa en la zona principal.
PESO_OBJETIVO = {
    "urgencias": {"urgente", "24 horas", "24h"},
    "leads": {"precio", "presupuesto"},
    "ventas": {"precio", "barato", "económico"},
    "marca": set(),
}


def _aplicar(mod: str, servicio: str) -> str:
    return limpiar(mod.replace("{s}", servicio) if "{s}" in mod else f"{servicio} {mod}")


def _jerga(briefing: Briefing) -> List[Tuple[str, str]]:
    """Devuelve (término, servicio al que equivale) por cada línea de jerga."""
    out = []
    for linea in briefing.jerga:
        if not linea.strip():
            continue
        if "=" in linea:
            termino, serv = (p.strip() for p in linea.split("=", 1))
        else:
            termino, serv = linea.strip(), ""
        if termino:
            out.append((limpiar(termino), serv))
    return out


def generar_semillas(briefing: Briefing) -> List[Semilla]:
    mods = briefing.modificadores or MODIFICADORES_POR_DEFECTO
    con_geo = briefing.alcance != "nacional"
    zonas = briefing.zonas() if con_geo else []
    principal = briefing.zona_principal.strip() if con_geo else ""
    algun_prioritario = any(s.prioritario for s in briefing.servicios)
    pesan = PESO_OBJETIVO.get(briefing.objetivo, set())

    semillas: List[Semilla] = []
    vistas = set()

    def add(texto, servicio, intencion, geo="", tipo="base", prioritaria=False):
        texto = limpiar(texto)
        # Se deduplica por texto exacto, no por clave: el plural y la forma sin
        # tilde comparten clave con la base y aquí sí queremos consultarlas.
        if not texto or texto in vistas:
            return
        vistas.add(texto)
        semillas.append(Semilla(texto=texto, servicio=servicio, intencion=intencion,
                                geo=geo, tipo=tipo, prioritaria=prioritaria))

    for serv in briefing.servicios:
        s = limpiar(serv.nombre)
        manda = serv.prioritario or not algun_prioritario

        # Servicio solo: es la semilla que más rinde en la sopa de letras
        # («cerrajero a» ya devuelve «cerrajero alcorcón»…), así que va primera.
        add(s, serv.nombre, "transaccional", prioritaria=manda)

        # Servicio × modificador (sin geo)
        for intencion, lista in mods.items():
            for mod in lista:
                add(_aplicar(mod, s), serv.nombre, intencion, prioritaria=manda and mod in pesan)

        if con_geo:
            # Servicio × zona (todas las zonas)
            for z in zonas:
                es_principal = z == principal
                add(f"{s} {z}", serv.nombre, "local", geo=z, prioritaria=manda and es_principal)
                add(f"{s} en {z}", serv.nombre, "local", geo=z, prioritaria=manda and es_principal)
            # Servicio × modificador transaccional × zona principal
            for mod in mods.get("transaccional", []):
                add(f"{_aplicar(mod, s)} {principal}", serv.nombre, "transaccional",
                    geo=principal, prioritaria=manda and mod in pesan)

        # Variantes: plural y sin tilde del servicio solo y con cada zona
        bases = [s] + [f"{s} {z}" for z in zonas]
        for b in bases:
            geo = next((z for z in zonas if b.endswith(limpiar(z))), "")
            add(pluralizar_frase(b), serv.nombre, "local" if geo else "transaccional",
                geo=geo, tipo="variante")
            if sin_tildes(b) != b:
                add(sin_tildes(b), serv.nombre, "local" if geo else "transaccional",
                    geo=geo, tipo="variante")

    # Marca
    marca = limpiar(briefing.marca)
    add(marca, "(marca)", "marca", tipo="marca", prioritaria=briefing.objetivo == "marca")
    if principal:
        add(f"{marca} {principal}", "(marca)", "marca", geo=principal, tipo="marca")
    add(f"{marca} opiniones", "(marca)", "marca", tipo="marca")

    # Jerga del público: término solo y con la zona principal
    for termino, serv in _jerga(briefing):
        add(termino, serv or "(jerga)", "transaccional", tipo="jerga")
        if principal:
            add(f"{termino} {principal}", serv or "(jerga)", "local", geo=principal, tipo="jerga")

    # Categoría del sector, por si los servicios no la nombran
    add(limpiar(briefing.sector), "(sector)", "transaccional")
    if principal:
        add(f"{limpiar(briefing.sector)} {principal}", "(sector)", "local", geo=principal)

    return semillas
