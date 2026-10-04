"""
Módulo 5 · Espejo de competidores (por sitemap).

Para cada dominio: busca el sitemap (robots.txt y rutas habituales), lo recorre
y de cada URL saca title, H1, meta description y H2. Si no hay sitemap, lee la
home y sigue los enlaces del menú. Todo fallo queda en Avisos con su URL.
"""

import asyncio
import random
import re
from typing import Callable, List, Optional, Tuple
from urllib.parse import urljoin, urlparse

import httpx
from bs4 import BeautifulSoup

from .autocomplete import USER_AGENTS
from .modelos import Aviso, PaginaCompetidor
from .normalizar import clave, limpiar

RUTAS_SITEMAP = ["/sitemap_index.xml", "/sitemap.xml", "/wp-sitemap.xml",
                 "/sitemap-index.xml", "/page-sitemap.xml"]
MAX_URLS = 150
MAX_SITEMAPS_HIJOS = 12
CONCURRENCIA = 6

_SITEMAP_DESCARTE = re.compile(r"(image|attachment|category|tag|author|product_cat|"
                               r"post_tag|format|video|news-sitemap|portfolio_cat)", re.I)
_URL_DESCARTE = re.compile(r"(\.(jpe?g|png|gif|webp|svg|pdf|zip|docx?|xlsx?|mp4)$|/tag/|/author/|"
                           r"/category/|/feed/?$|/page/\d+|\?|/wp-content/|/wp-json/|#)", re.I)
_LEGAL = re.compile(r"(aviso-legal|legal|privacidad|privacy|cookies|terminos|condiciones|"
                    r"politica|rgpd|lopd)", re.I)
_CONTACTO = re.compile(r"(contacto|contact|donde-estamos|localizacion)", re.I)
_EMPRESA = re.compile(r"(quienes-somos|sobre-nosotros|nosotros|empresa|equipo|about|trabaja)", re.I)
_BLOG = re.compile(r"(/blog/|/noticias/|/articulos?/|/consejos/|/guia|/\d{4}/\d{2}/)", re.I)
_SEPARADORES = re.compile(r"\s+[|–—·•:»\-]\s+")


def _base(url: str) -> str:
    url = url.strip()
    if not re.match(r"^https?://", url, re.I):
        url = "https://" + url
    p = urlparse(url)
    return f"{p.scheme}://{p.netloc}"


def dominio_de(url: str) -> str:
    return urlparse(_base(url)).netloc.lower().removeprefix("www.")


def _headers():
    return {"User-Agent": random.choice(USER_AGENTS),
            "Accept-Language": "es-ES,es;q=0.9"}


def patron_url(url: str, zonas_claves: List[str], es_post: bool) -> str:
    path = urlparse(url).path.strip("/").lower()
    if not path:
        return "home"
    if _LEGAL.search(path):
        return "legal"
    if _CONTACTO.search(path):
        return "contacto"
    if _EMPRESA.search(path) and path.count("/") == 0:
        return "empresa"
    if es_post or _BLOG.search("/" + path + "/"):
        return "blog"
    slug = clave(path.replace("/", " ").replace("-", " ").replace("_", " "))
    con_espacios = f" {slug} "
    if any(f" {z} " in con_espacios for z in zonas_claves if z):
        return "servicio-ciudad"
    if len(path.split("/")[-1].split("-")) >= 7:
        return "blog"
    return "servicio"


def keyword_inferida(title: str, h1: str, marca_dominio: str) -> str:
    """La keyword que parece trabajar la página: el H1 si es razonable, si no el title sin la marca."""
    cand = h1.strip()
    if not cand or len(cand.split()) > 12:
        partes = [p for p in _SEPARADORES.split(title or "") if p.strip()]
        sin_marca = [p for p in partes if marca_dominio not in clave(p).replace(" ", "")]
        cand = (sin_marca or partes or [""])[0]
    cand = limpiar(cand)
    return cand if 1 <= len(cand.split()) <= 12 else ""


class Espejo:
    def __init__(self, avisos: List[Aviso], zonas: List[str],
                 progreso: Callable[[str], None]):
        self.avisos = avisos
        self.zonas_claves = [clave(z) for z in zonas]
        self.progreso = progreso

    async def _get(self, client, url) -> Optional[httpx.Response]:
        try:
            r = await client.get(url, headers=_headers())
            return r if r.status_code == 200 else None
        except httpx.HTTPError:
            return None

    async def _leer_sitemap(self, client, url) -> Tuple[List[str], List[str]]:
        """Devuelve (urls, sitemaps_hijos)."""
        r = await self._get(client, url)
        if r is None or "<" not in r.text[:500]:
            return [], []
        soup = BeautifulSoup(r.content, "xml")
        if soup.find("sitemapindex"):
            return [], [l.get_text(strip=True) for l in soup.find_all("loc")]
        if soup.find("urlset"):
            return [l.get_text(strip=True) for l in soup.select("url > loc")], []
        return [], []

    async def _urls_por_sitemap(self, client, base: str, sitemap_dado: Optional[str]):
        candidatos = []
        if sitemap_dado:
            candidatos.append(sitemap_dado if sitemap_dado.startswith("http") else urljoin(base, sitemap_dado))
        r = await self._get(client, base + "/robots.txt")
        if r is not None:
            candidatos += re.findall(r"(?im)^\s*sitemap:\s*(\S+)", r.text)
        candidatos += [base + p for p in RUTAS_SITEMAP]

        probados = []
        for cand in dict.fromkeys(candidatos):
            probados.append(cand)
            urls, hijos = await self._leer_sitemap(client, cand)
            if hijos:
                # Primero los de páginas/servicios, luego entradas; fuera imágenes, tags…
                hijos = [h for h in hijos if not _SITEMAP_DESCARTE.search(h)]
                hijos.sort(key=lambda h: (0 if re.search(r"page|pagina|servic", h, re.I)
                                          else 2 if re.search(r"post|blog", h, re.I) else 1))
                posts = set()
                for h in hijos[:MAX_SITEMAPS_HIJOS]:
                    u, nietos = await self._leer_sitemap(client, h)
                    for n in nietos[:MAX_SITEMAPS_HIJOS]:
                        u2, _ = await self._leer_sitemap(client, n)
                        u += u2
                    if re.search(r"post|blog", h, re.I):
                        posts.update(u)
                    urls += u
                if urls:
                    return urls, cand, posts, probados
            elif urls:
                return urls, cand, set(), probados
        return [], None, set(), probados

    async def _urls_por_menu(self, client, base: str) -> List[str]:
        r = await self._get(client, base + "/")
        if r is None:
            return []
        soup = BeautifulSoup(r.text, "lxml")
        zonas = soup.select("nav a[href], header a[href], .menu a[href], #menu a[href]") or soup.select("a[href]")
        host = urlparse(base).netloc.lower().removeprefix("www.")
        urls = [base + "/"]
        for a in zonas:
            u = urljoin(base + "/", a["href"]).split("#")[0]
            if urlparse(u).netloc.lower().removeprefix("www.") == host:
                urls.append(u)
        return list(dict.fromkeys(urls))[:60]

    async def _pagina(self, client, dominio, url, posts, marca_dom, sem) -> Optional[PaginaCompetidor]:
        async with sem:
            await asyncio.sleep(random.uniform(0.05, 0.3))
            r = await self._get(client, url)
        if r is None or "html" not in r.headers.get("content-type", "html"):
            self.avisos.append(Aviso("página sin respuesta", url, f"No se pudo leer ({dominio})"))
            return None
        soup = BeautifulSoup(r.text, "lxml")
        title = soup.title.get_text(" ", strip=True) if soup.title else ""
        h1 = soup.find("h1")
        h1 = h1.get_text(" ", strip=True) if h1 else ""
        meta = soup.find("meta", attrs={"name": re.compile("^description$", re.I)})
        meta = (meta.get("content") or "").strip() if meta else ""
        h2s = [h.get_text(" ", strip=True) for h in soup.find_all("h2")]
        h2 = " | ".join([h for h in h2s if h][:6])
        patron = patron_url(url, self.zonas_claves, url in posts)
        kw = "" if patron in ("legal", "contacto", "empresa") else keyword_inferida(title, h1, marca_dom)
        return PaginaCompetidor(dominio=dominio, url=url, title=title, h1=h1,
                                meta_description=meta, h2=h2, patron=patron, keyword_inferida=kw)

    async def leer(self, url_dominio: str, etiqueta: str = "", sitemap_dado: Optional[str] = None) -> List[PaginaCompetidor]:
        base = _base(url_dominio)
        dominio = dominio_de(url_dominio) + (f" {etiqueta}" if etiqueta else "")
        marca_dom = dominio_de(url_dominio).split(".")[0].replace("-", "")
        async with httpx.AsyncClient(timeout=15, follow_redirects=True) as client:
            # La home puede redirigir a otro host (www, https): se usa el definitivo
            r = await self._get(client, base + "/")
            if r is not None:
                base = f"{r.url.scheme}://{r.url.host}"
            self.progreso(f"{dominio}: buscando sitemap")
            urls, sitemap, posts, probados = await self._urls_por_sitemap(client, base, sitemap_dado)
            if not urls:
                self.avisos.append(Aviso("sitemap caído", base,
                                         "Sin sitemap legible. Probados: " + ", ".join(probados)))
                self.progreso(f"{dominio}: sin sitemap, leyendo el menú de la home")
                urls = await self._urls_por_menu(client, base)
                if not urls:
                    self.avisos.append(Aviso("sitemap caído", base + "/",
                                             "Tampoco se pudo leer la home: competidor sin datos"))
                    return []
            urls = [u for u in dict.fromkeys(urls) if not _URL_DESCARTE.search(u)]
            if len(urls) > MAX_URLS:
                # Primero páginas (servicios), luego entradas del blog
                urls.sort(key=lambda u: (u in posts, u.count("/")))
                self.avisos.append(Aviso("límite de URLs", sitemap or base,
                                         f"{len(urls)} URLs en el sitemap; leídas las {MAX_URLS} primeras (páginas antes que blog)"))
                urls = urls[:MAX_URLS]
            self.progreso(f"{dominio}: leyendo {len(urls)} páginas")
            sem = asyncio.Semaphore(CONCURRENCIA)
            paginas = await asyncio.gather(*(self._pagina(client, dominio, u, posts, marca_dom, sem)
                                             for u in urls))
        return [p for p in paginas if p]
