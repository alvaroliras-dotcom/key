"""
Normalización de keywords: minúsculas, sin tildes, espacios limpios y
singular/plural plegados, para que «cerrajeros alcorcón» y «cerrajero alcorcon»
cuenten como la misma keyword.
"""

import re
import unicodedata

STOPWORDS = {
    "de", "del", "la", "las", "el", "los", "en", "a", "al", "y", "o", "para",
    "por", "con", "un", "una", "unos", "unas", "mi", "tu", "su", "que", "se",
}

# Palabras que acaban en -s y no son plurales (no se pliegan)
_NO_PLURAL = {"mas", "tres", "seis", "dos", "crisis", "bus", "gas", "lunes",
              "martes", "miercoles", "jueves", "viernes", "pais", "mes", "vs",
              "ves", "atlas", "gratis", "abrelatas", "parabrisas", "anis"}


def sin_tildes(texto: str) -> str:
    nfkd = unicodedata.normalize("NFKD", texto)
    # La ñ se conserva: «año» y «ano» no son lo mismo
    out = []
    for ch in nfkd:
        if unicodedata.combining(ch):
            if ch == "̃" and out and out[-1] in "nN":
                out[-1] = "ñ" if out[-1] == "n" else "Ñ"
            continue
        out.append(ch)
    return "".join(out)


def limpiar(texto: str) -> str:
    """Forma legible: minúsculas, sin signos raros, espacios simples. Conserva tildes."""
    t = texto.lower().strip()
    t = re.sub(r"[¿?¡!\"'“”«»()\[\]{}:;,.]+", " ", t)
    t = re.sub(r"\s+", " ", t)
    return t.strip()


def singular(palabra: str) -> str:
    if len(palabra) <= 3 or palabra in _NO_PLURAL or palabra.isdigit():
        return palabra
    if palabra.endswith("ces") and len(palabra) > 4:          # luces → luz
        return palabra[:-3] + "z"
    if palabra.endswith("es") and len(palabra) > 4 and palabra[-3] in "lrndjy":
        return palabra[:-2]                                     # motores → motor
    if palabra.endswith("s") and palabra[-2] in "aeiou":
        return palabra[:-1]                                     # llaves → llave
    return palabra


def clave(texto: str) -> str:
    """Clave de deduplicado: sin tildes y en singular palabra a palabra."""
    t = sin_tildes(limpiar(texto))
    return " ".join(singular(p) for p in t.split())


def tokens(texto: str) -> set:
    """Tokens significativos (sin stopwords) ya plegados."""
    return {p for p in clave(texto).split() if p not in STOPWORDS}


def plural(palabra: str) -> str:
    if not palabra or palabra[-1] == "s":
        return palabra
    if palabra[-1] in "aeiouáéó":
        return palabra + "s"
    if palabra[-1] == "z":
        return palabra[:-1] + "ces"
    return palabra + "es"


def pluralizar_frase(frase: str) -> str:
    """Pluraliza el primer sustantivo de la frase (la cabeza): «cerrajero urgente» → «cerrajeros urgente»."""
    partes = frase.split()
    if not partes:
        return frase
    partes[0] = plural(partes[0])
    return " ".join(partes)
