# La Llave (The Key) · keyword research de Nuria · v2

Recoge en una pasada la materia prima de keywords de un proyecto y la entrega en un Excel
con la imagen de GYF, ya filtrada y con la lectura hecha:

- autocomplete en sopa de letras;
- espejo de competidores por sitemap;
- preguntas;
- volumen en cascada, siempre con su fuente.

La arquitectura, la asignación y la anti-canibalización siguen siendo de Nuria.

```
backend/     FastAPI (Python 3.12) → Render. Incluye el conector MCP.
frontend/    React + Vite → Vercel. El formulario del briefing.
docs/        Briefing original y peticiones de Nuria, con una página por versión
             (hecho / descartado / pendiente), más los informes a Nuria.
recogidas/   Cada recogida guardada (Excel, briefing.json, resumen). No se sube al repo.
render.yaml  Configuración de Render (lee la carpeta backend/).
```

## Qué sale en el Excel

| Pestaña | Qué es |
|---|---|
| **Lectura** | Los recuentos del informe, ya hechos: intención, servicio, zona, top de Search Console, familias, huecos y fiabilidad del espejo. |
| **Keywords** | Una fila por keyword: origen, intención, zona, servicio, familia, volumen + fuente, hueco y página propia. |
| **Familias** | Borrador de lectura: servicio + zona + intención. No es clustering. |
| **Preguntas** | People Also Ask y búsquedas relacionadas (con DataForSEO) y preguntas del autocomplete. |
| **Competidores** | Cada página espejada, con su servicio, su zona y la fiabilidad de la inferencia. |
| **Semillas** | Cobertura: cuántas sugerencias dio cada semilla. |
| **Descartadas** | Lo que quitó el filtro de ruido, con su motivo, para rescatar lo que se cuele. |
| **Avisos** | Todo fallo o hueco de datos, con la URL o la semilla exacta. |
| **Briefing** | Copia del formulario. |

## Despliegue

1. **GitHub:** el repo `la-llave` (privado).
2. **Render (backend):**
   - New → Blueprint → elige el repo. Lee `render.yaml` y te pide los secretos:
     - `MCP_RUTA`: una cadena larga y aleatoria, p. ej. `mcp-` + 32 letras y números.
     - `DATAFORSEO_LOGIN` y `DATAFORSEO_PASSWORD`: déjalos vacíos hasta tener cuenta.
     - Supabase: opcional.
   - Comprueba que `https://la-llave-qicn.onrender.com/` responde `{"ok":true,…}`.
3. **Vercel (frontend):** Add New → Project → el mismo repo, Root Directory `frontend`.
   Variable `VITE_API_URL = https://la-llave-qicn.onrender.com`.

Todas las variables están explicadas en [backend/.env.example](backend/.env.example).

## Usarla desde claude.ai (conector MCP)

1. En claude.ai: Configuración → Conectores → Añadir conector personalizado.
2. URL: `https://la-llave-qicn.onrender.com/<MCP_RUTA>` (la ruta secreta que pusiste en Render).
3. Herramientas que aparecen:
   - `lanzar_recogida(briefing)` → devuelve un id;
   - `estado(id)` → progreso y, al terminar, el resumen y la Lectura;
   - `descargar_excel(id)` → enlaces al Excel, al briefing.json y a cada pestaña en CSV;
   - `leer_pestana(id, pestaña)` → lee Keywords, Familias, Preguntas… por tramos.

La ruta secreta es la única protección del conector: no la compartas.

## Ejecutarla en local (en este ordenador)

```bash
cd backend
pip install -r requirements.txt
uvicorn app.main:app --port 8000
```

En otra terminal:

```bash
cd frontend
npm install
npm run dev
```

Las recogidas se guardan en `recogidas/` y no se borran nunca.

## Ajustes (variables de entorno)

| Variable | Por defecto | Para qué |
|---|---|---|
| `AC_PRESUPUESTO_SEG` | 420 | Segundos máximos de autocomplete |
| `AC_CONCURRENCIA` | 2 | Consultas a Google en paralelo (2 = prudente) |
| `DATAFORSEO_MAX_PREGUNTAS` | 15 | Semillas cuya SERP se lee para PAA |
| `DATAFORSEO_MAX_VOLUMEN` | 3000 | Tope de keywords a las que se pide volumen |
| `RECOGIDAS_DIR` | `recogidas/` | Dónde se guardan las recogidas |

Si hubo otra recogida en la última hora, la siguiente va con pausas dobles y lo avisa.
Si Google bloquea, se entrega lo recogido, se avisa en grande y queda en Avisos la última semilla.

## Reglas de honestidad del dato (no se tocan)

- Cada keyword lleva su módulo de origen. Cada volumen lleva su fuente.
- Sin fuente no hay número: celda vacía y «sin dato fiable». **El Excel no se genera si
  aparece un volumen sin fuente.**
- Los rangos del Keyword Planner se escriben como rango, nunca como un número inventado.
- La familia es una vista de lectura, marcada como borrador; nunca un entregable.
