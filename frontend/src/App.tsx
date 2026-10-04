import { useEffect, useRef, useState } from "react";
import {
  type Briefing,
  type Cascada,
  type Estado,
  type Recogida,
  crearProyecto,
  getCascada,
  getEstado,
  getRecogidas,
  leerCsv,
  urlBriefing,
  urlCsv,
  urlExcel,
} from "./api";

// ── Estado del formulario (todo texto; se convierte a Briefing al lanzar) ──
interface Form {
  dominio: string;
  marca: string;
  sector: string;
  servicios: string;
  no_ofrece: string;
  ruido: string | null; // null = aún sin la lista por defecto del servidor
  objetivo: Briefing["objetivo"];
  sede: string;
  zona_principal: string;
  zonas_secundarias: string;
  alcance: Briefing["alcance"];
  web_estado: Briefing["web_estado"];
  url_web: string;
  sitemap_url: string;
  competidores: string[];
  jerga: string;
  mercado: string;
  segundo_nivel: boolean;
  preguntas: boolean;
  volumen_dataforseo: boolean;
  modificadores: Record<string, string>;
}

interface Archivo {
  nombre: string;
  texto: string;
}

const VACIO: Form = {
  dominio: "",
  marca: "",
  sector: "",
  servicios: "",
  no_ofrece: "",
  ruido: null,
  objetivo: "leads",
  sede: "",
  zona_principal: "",
  zonas_secundarias: "",
  alcance: "local",
  web_estado: "nueva",
  url_web: "",
  sitemap_url: "",
  competidores: ["", "", "", "", ""],
  jerga: "",
  mercado: "es-ES",
  segundo_nivel: false,
  preguntas: true,
  volumen_dataforseo: true,
  modificadores: {},
};

const BORRADOR = "la-llave-briefing-borrador";
const MODULOS: [string, string][] = [
  ["semillas", "Generador de semillas"],
  ["autocomplete", "Autocomplete (sopa de letras)"],
  ["competidores", "Espejo de competidores"],
  ["preguntas", "Preguntas (PAA y relacionadas)"],
  ["volumen", "Volumen en cascada"],
  ["deduplicado", "Filtro de ruido y deduplicado"],
  ["hueco", "Hueco frente a la competencia"],
  ["excel", "Excel GYF y guardado"],
];
const PESTANAS = ["Lectura", "Keywords", "Familias", "Preguntas", "Competidores", "Semillas", "Descartadas", "Avisos", "Briefing"];

const lineas = (t: string) =>
  t
    .split(/\n|;/)
    .map((s) => s.trim())
    .filter(Boolean);

const cinco = (xs: string[]) => [...xs, "", "", "", "", ""].slice(0, 5);

function leerBorrador(): Form {
  try {
    const raw = localStorage.getItem(BORRADOR);
    if (raw) {
      const f = { ...VACIO, ...JSON.parse(raw) };
      f.competidores = cinco(f.competidores);
      return f;
    }
  } catch {
    // sin almacenamiento: formulario vacío
  }
  return VACIO;
}

function aBriefing(f: Form, gsc: Archivo | null, planner: Archivo | null): Briefing {
  const mods = Object.fromEntries(
    Object.entries(f.modificadores).map(([k, v]) => [k, v.split(",").map((s) => s.trim()).filter(Boolean)]),
  );
  return {
    dominio: f.dominio.trim(),
    marca: f.marca.trim(),
    sector: f.sector.trim(),
    servicios: lineas(f.servicios).map((s) => ({
      nombre: s.replace(/^\*\s*|\s*\*$/g, ""),
      prioritario: /^\*|\*$/.test(s),
    })),
    no_ofrece: lineas(f.no_ofrece),
    ruido: f.ruido === null ? null : f.ruido.split(",").map((s) => s.trim()).filter(Boolean),
    objetivo: f.objetivo,
    sede: f.sede.trim(),
    zona_principal: f.zona_principal.trim(),
    zonas_secundarias: lineas(f.zonas_secundarias.replace(/,/g, "\n")),
    alcance: f.alcance,
    web_estado: f.web_estado,
    url_web: f.web_estado === "existente" ? f.url_web.trim() || f.dominio.trim() : null,
    sitemap_url: f.sitemap_url.trim() || null,
    competidores: f.competidores.map((c) => c.trim()).filter(Boolean),
    jerga: lineas(f.jerga),
    mercado: f.mercado,
    modificadores: Object.keys(mods).length ? mods : null,
    segundo_nivel: f.segundo_nivel,
    preguntas: f.preguntas,
    volumen_dataforseo: f.volumen_dataforseo,
    gsc_csv: gsc?.texto ?? null,
    gsc_nombre: gsc?.nombre ?? null,
    planner_csv: planner?.texto ?? null,
    planner_nombre: planner?.nombre ?? null,
  };
}

/** El fichero relanzable (briefing.json) vuelve a ser formulario. */
function deBriefing(b: Briefing): { form: Form; gsc: Archivo | null; planner: Archivo | null } {
  return {
    form: {
      ...VACIO,
      dominio: b.dominio,
      marca: b.marca,
      sector: b.sector,
      servicios: b.servicios.map((s) => (s.prioritario ? "*" : "") + s.nombre).join("\n"),
      no_ofrece: (b.no_ofrece ?? []).join("\n"),
      ruido: b.ruido == null ? null : b.ruido.join(", "),
      objetivo: b.objetivo,
      sede: b.sede,
      zona_principal: b.zona_principal,
      zonas_secundarias: (b.zonas_secundarias ?? []).join(", "),
      alcance: b.alcance,
      web_estado: b.web_estado,
      url_web: b.url_web ?? "",
      sitemap_url: b.sitemap_url ?? "",
      competidores: cinco(b.competidores ?? []),
      jerga: (b.jerga ?? []).join("\n"),
      mercado: b.mercado ?? "es-ES",
      segundo_nivel: !!b.segundo_nivel,
      preguntas: b.preguntas ?? true,
      volumen_dataforseo: b.volumen_dataforseo ?? true,
      modificadores: Object.fromEntries(Object.entries(b.modificadores ?? {}).map(([k, v]) => [k, v.join(", ")])),
    },
    gsc: b.gsc_csv ? { nombre: b.gsc_nombre ?? "Search Console", texto: b.gsc_csv } : null,
    planner: b.planner_csv ? { nombre: b.planner_nombre ?? "Keyword Planner", texto: b.planner_csv } : null,
  };
}

function faltan(f: Form): string[] {
  const out: string[] = [];
  if (!f.dominio.trim()) out.push("dominio");
  if (!f.marca.trim()) out.push("marca");
  if (!f.sector.trim()) out.push("sector");
  if (!lineas(f.servicios).length) out.push("servicios");
  if (!f.sede.trim()) out.push("sede");
  if (!f.zona_principal.trim()) out.push("zona principal");
  return out;
}

function descargar(nombre: string, contenido: string) {
  const url = URL.createObjectURL(new Blob([contenido], { type: "application/json" }));
  const a = document.createElement("a");
  a.href = url;
  a.download = nombre;
  a.click();
  URL.revokeObjectURL(url);
}

const mmss = (s: number) => `${Math.floor(s / 60)}:${String(s % 60).padStart(2, "0")}`;
const slug = (t: string) => t.toLowerCase().normalize("NFD").replace(/[̀-ͯ]/g, "").replace(/[^\w]+/g, "-").replace(/^-|-$/g, "");

export default function App() {
  const [f, setF] = useState<Form>(leerBorrador);
  const [gsc, setGsc] = useState<Archivo | null>(null);
  const [planner, setPlanner] = useState<Archivo | null>(null);
  const [cascada, setCascada] = useState<Cascada | null>(null);
  const [historial, setHistorial] = useState<Recogida[]>([]);
  const [conexion, setConexion] = useState<"conectando" | "ok" | "error">("conectando");
  const [estado, setEstado] = useState<Estado | null>(null);
  const [error, setError] = useState("");
  const [enviando, setEnviando] = useState(false);
  const poll = useRef<number>();

  // El servidor gratuito de Render duerme: la primera llamada lo despierta (~50 s)
  useEffect(() => {
    getCascada()
      .then((c) => {
        setCascada(c);
        setConexion("ok");
        setF((prev) => ({
          ...prev,
          ruido: prev.ruido ?? c.ruido_por_defecto.join(", "),
          modificadores: Object.keys(prev.modificadores).length
            ? prev.modificadores
            : Object.fromEntries(Object.entries(c.modificadores_por_defecto).map(([k, v]) => [k, v.join(", ")])),
        }));
      })
      .catch(() => setConexion("error"));
    getRecogidas()
      .then((r) => setHistorial(r.recogidas))
      .catch(() => setHistorial([]));
  }, []);

  useEffect(() => {
    try {
      localStorage.setItem(BORRADOR, JSON.stringify(f));
    } catch {
      // sin almacenamiento: no se guarda el borrador
    }
  }, [f]);

  useEffect(() => () => window.clearInterval(poll.current), []);

  const set = <K extends keyof Form>(k: K, v: Form[K]) => setF((p) => ({ ...p, [k]: v }));

  function seguir(id: string) {
    window.clearInterval(poll.current);
    const tick = async () => {
      try {
        const e = await getEstado(id);
        setEstado(e);
        if (e.estado !== "corriendo") window.clearInterval(poll.current);
      } catch (err) {
        setError((err as Error).message);
        window.clearInterval(poll.current);
      }
    };
    tick();
    poll.current = window.setInterval(tick, 2000);
  }

  async function lanzar() {
    setError("");
    const huecos = faltan(f);
    if (huecos.length) {
      setError(`Faltan campos obligatorios: ${huecos.join(", ")}. La herramienta no arranca sin ellos.`);
      return;
    }
    setEnviando(true);
    try {
      const { id } = await crearProyecto(aBriefing(f, gsc, planner));
      seguir(id);
    } catch (err) {
      setError((err as Error).message);
    } finally {
      setEnviando(false);
    }
  }

  function nueva() {
    window.clearInterval(poll.current);
    setEstado(null);
    setError("");
    getRecogidas()
      .then((r) => setHistorial(r.recogidas))
      .catch(() => undefined);
  }

  async function cargarBriefing(file: File | undefined) {
    if (!file) return;
    try {
      const b = JSON.parse(await file.text()) as Briefing;
      const { form, gsc: g, planner: p } = deBriefing(b);
      setF({ ...form, ruido: form.ruido ?? cascada?.ruido_por_defecto.join(", ") ?? null });
      setGsc(g);
      setPlanner(p);
      setError("");
    } catch {
      setError("Ese archivo no es un briefing de La Llave (briefing.json).");
    }
  }

  const prioritarios = lineas(f.servicios).filter((s) => /^\*|\*$/.test(s)).length;
  const dfs = !!cascada?.dataforseo;

  return (
    <div className="app">
      <header className="top">
        <img src="/logo_gyf.png" alt="El Gordo y el Flaco" className="logo" />
        <div className="top-txt">
          <span className="eyebrow">Keyword research · v2 · The Key</span>
          <h1>La Llave</h1>
        </div>
        <span className={`conexion ${conexion}`}>
          {conexion === "ok" ? "Servidor listo" : conexion === "error" ? "Sin conexión con el servidor" : "Despertando el servidor…"}
        </span>
      </header>

      {!estado ? (
        <main className="grid">
          <section className="card full fichero">
            <div>
              <h2>Briefing</h2>
              <p className="ayuda">Guárdalo como fichero para relanzar el proyecto sin reescribirlo (incluye los CSV subidos).</p>
            </div>
            <div className="fichero-botones">
              <button type="button" className="sec" onClick={() => descargar(`briefing-${slug(f.marca) || "proyecto"}.json`, JSON.stringify(aBriefing(f, gsc, planner), null, 1))}>
                Guardar briefing
              </button>
              <label className="sec subir">
                Cargar briefing
                <input type="file" accept=".json,application/json" onChange={(e) => cargarBriefing(e.target.files?.[0])} />
              </label>
            </div>
          </section>

          <section className="card">
            <h2>Proyecto</h2>
            <div className="row2">
              <Campo label="Dominio" req>
                <input value={f.dominio} onChange={(e) => set("dominio", e.target.value)} placeholder="marcoscerrajeros.es" />
              </Campo>
              <Campo label="Marca" req>
                <input value={f.marca} onChange={(e) => set("marca", e.target.value)} placeholder="Marcos Cerrajeros" />
              </Campo>
            </div>
            <Campo label="Sector / categoría" req>
              <input value={f.sector} onChange={(e) => set("sector", e.target.value)} placeholder="cerrajería" />
            </Campo>
            <Campo label="Servicios núcleo" req ayuda="Uno por línea. Marca con * los prioritarios: mandan en la sopa de letras y en las preguntas.">
              <textarea rows={6} value={f.servicios} onChange={(e) => set("servicios", e.target.value)} placeholder={"*cerrajero\n*apertura de puertas\ncambio de cerradura\npuertas blindadas"} />
            </Campo>
            {lineas(f.servicios).length > 0 && (
              <p className="nota">
                {lineas(f.servicios).length} servicios · {prioritarios || "ninguno marcado → todos cuentan como"} prioritario{prioritarios === 1 ? "" : "s"}
              </p>
            )}
            <Campo label="Lo que NO ofrece" ayuda="Lista negra del cliente, uno por línea. Admite excepciones: «gratis salvo auditoría, sherlock».">
              <textarea rows={3} value={f.no_ofrece} onChange={(e) => set("no_ofrece", e.target.value)} placeholder={"gratis salvo auditoría\ncajas fuertes"} />
            </Campo>
            <Campo label="Lista negra por defecto (ruido)" ayuda="Separada por comas. Lo eliminado va a la pestaña Descartadas con su motivo. Las zonas del briefing nunca se filtran.">
              <textarea rows={3} value={f.ruido ?? ""} onChange={(e) => set("ruido", e.target.value)} />
            </Campo>
            <Campo label="Objetivo" req ayuda="Decide qué modificadores pasan la sopa de letras completa.">
              <Opciones
                valor={f.objetivo}
                set={(v) => set("objetivo", v as Form["objetivo"])}
                opciones={[["urgencias", "Urgencias"], ["leads", "Leads"], ["marca", "Marca"], ["ventas", "Ventas"]]}
              />
            </Campo>
          </section>

          <section className="card">
            <h2>Geografía y web</h2>
            <div className="row2">
              <Campo label="Sede" req>
                <input value={f.sede} onChange={(e) => set("sede", e.target.value)} placeholder="Alcorcón" />
              </Campo>
              <Campo label="Zona principal" req>
                <input value={f.zona_principal} onChange={(e) => set("zona_principal", e.target.value)} placeholder="Alcorcón" />
              </Campo>
            </div>
            <Campo label="Zonas secundarias" ayuda="Una por línea o separadas por comas. Las zonas que no estén aquí se marcan «fuera de briefing».">
              <textarea rows={3} value={f.zonas_secundarias} onChange={(e) => set("zonas_secundarias", e.target.value)} placeholder={"Móstoles, Leganés, Fuenlabrada"} />
            </Campo>
            <Campo label="Alcance" req ayuda={f.alcance === "nacional" ? "En nacional las semillas no se cruzan con geo." : undefined}>
              <Opciones
                valor={f.alcance}
                set={(v) => set("alcance", v as Form["alcance"])}
                opciones={[["local", "Local"], ["provincial", "Provincial"], ["nacional", "Nacional"]]}
              />
            </Campo>
            <Campo label="Web" req ayuda={f.web_estado === "nueva" ? "Web nueva: todo lo que la competencia tenga y tú no saldrá como hueco." : undefined}>
              <Opciones
                valor={f.web_estado}
                set={(v) => set("web_estado", v as Form["web_estado"])}
                opciones={[["nueva", "Nueva"], ["existente", "Existente"]]}
              />
            </Campo>
            {f.web_estado === "existente" && (
              <div className="row2">
                <Campo label="URL de la web" ayuda="Si se deja vacío, se usa el dominio.">
                  <input value={f.url_web} onChange={(e) => set("url_web", e.target.value)} placeholder="https://…" />
                </Campo>
                <Campo label="Sitemap" ayuda="Opcional; si no, se busca solo.">
                  <input value={f.sitemap_url} onChange={(e) => set("sitemap_url", e.target.value)} placeholder="/sitemap_index.xml" />
                </Campo>
              </div>
            )}
            <Campo label="Competidores de referencia" ayuda="Hasta 5. Son la base del espejo y de la columna «hueco».">
              {f.competidores.map((c, i) => (
                <input
                  key={i}
                  className="stack"
                  value={c}
                  placeholder={`competidor${i + 1}.es`}
                  onChange={(e) => {
                    const n = [...f.competidores];
                    n[i] = e.target.value;
                    set("competidores", n);
                  }}
                />
              ))}
            </Campo>
          </section>

          <section className="card">
            <h2>Datos de volumen</h2>
            <Campo label="Export de Search Console (CSV)" ayuda="El «Consultas.csv» del ZIP de exportación.">
              <input type="file" accept=".csv,text/csv" onChange={async (e) => {
                const file = e.target.files?.[0];
                setGsc(file ? { nombre: file.name, texto: await leerCsv(file) } : null);
              }} />
            </Campo>
            {gsc && <p className="nota">Cargado: {gsc.nombre}</p>}
            <Campo label="Export de Keyword Planner (CSV)" ayuda="«Descargar ideas de palabras clave». Si llega en rangos, se escribe el rango tal cual.">
              <input type="file" accept=".csv,text/csv" onChange={async (e) => {
                const file = e.target.files?.[0];
                setPlanner(file ? { nombre: file.name, texto: await leerCsv(file) } : null);
              }} />
            </Campo>
            {planner && <p className="nota">Cargado: {planner.nombre}</p>}
            <label className={`check ${dfs ? "" : "apagado"}`}>
              <input type="checkbox" checked={f.volumen_dataforseo} disabled={!dfs} onChange={(e) => set("volumen_dataforseo", e.target.checked)} />
              Volumen con DataForSEO para lo que no tenga Search Console ni Planner (de pago, céntimos por proyecto)
            </label>
            <label className={`check ${dfs ? "" : "apagado"}`}>
              <input type="checkbox" checked={f.preguntas} disabled={!dfs} onChange={(e) => set("preguntas", e.target.checked)} />
              Preguntas: People Also Ask y búsquedas relacionadas de las semillas prioritarias (DataForSEO)
            </label>
            {!dfs && <p className="ayuda">DataForSEO no está configurado en el servidor: sin PAA ni volumen de pago. La pestaña Preguntas traerá las del autocomplete.</p>}
          </section>

          <section className="card">
            <h2>Afinado</h2>
            <Campo label="Jerga del público" ayuda="Una por línea. Admite «término = servicio» (p. ej. bombín = cambio de cerradura).">
              <textarea rows={3} value={f.jerga} onChange={(e) => set("jerga", e.target.value)} />
            </Campo>
            <Campo label="Idioma / mercado">
              <select value={f.mercado} onChange={(e) => set("mercado", e.target.value)}>
                <option value="es-ES">Español · España</option>
                <option value="ca-ES">Catalán · España</option>
                <option value="es-MX">Español · México</option>
                <option value="es-AR">Español · Argentina</option>
                <option value="es-CO">Español · Colombia</option>
                <option value="es-CL">Español · Chile</option>
                <option value="es-PE">Español · Perú</option>
                <option value="es-US">Español · EE. UU.</option>
              </select>
            </Campo>
            <label className="check">
              <input type="checkbox" checked={f.segundo_nivel} onChange={(e) => set("segundo_nivel", e.target.checked)} />
              Segundo nivel: sopa de letras también sobre las 20 sugerencias más repetidas (si queda tiempo)
            </label>
            <details className="mods">
              <summary>Modificadores por intención</summary>
              <p className="ayuda">Separados por comas. «{"{s}"}» marca dónde va el servicio; sin él, el modificador va detrás.</p>
              {Object.entries(f.modificadores).map(([k, v]) => (
                <Campo key={k} label={k}>
                  <textarea rows={2} value={v} onChange={(e) => set("modificadores", { ...f.modificadores, [k]: e.target.value })} />
                </Campo>
              ))}
            </details>
          </section>

          <section className="card full lanzar">
            <h2>Volumen: orden de la cascada</h2>
            <ol className="cascada">
              {(cascada?.cascada ?? []).map((c) => {
                const activa =
                  (c.fuente === "Search Console" && !!gsc) ||
                  (c.fuente === "Keyword Planner" && !!planner) ||
                  (c.fuente === "DataForSEO" && dfs && f.volumen_dataforseo) ||
                  c.fuente === "Sin dato";
                const etiqueta =
                  c.fuente === "Search Console" ? (gsc ? "activa" : "sin CSV")
                  : c.fuente === "Keyword Planner" ? (planner ? "activa" : "sin CSV")
                  : c.fuente === "DataForSEO" ? (dfs ? (f.volumen_dataforseo ? "activa" : "desactivada") : "sin clave")
                  : "siempre";
                return (
                  <li key={c.fuente} className={activa ? "activa" : "futura"}>
                    <strong>{c.fuente}</strong> <span>{c.como}</span>
                    <em>{etiqueta}</em>
                  </li>
                );
              })}
            </ol>
            <p className="ayuda">Sin fuente no hay número: la celda queda vacía con «sin dato fiable».</p>
            {cascada?.recogida_reciente_min != null && (
              <p className="aviso">
                Hubo otra recogida hace {cascada.recogida_reciente_min} min: esta irá a ritmo prudente (pausas dobles) para que Google no bloquee.
              </p>
            )}
            {error && <p className="error">{error}</p>}
            <button className="cta" onClick={lanzar} disabled={enviando || conexion !== "ok"}>
              {enviando ? "Lanzando…" : "Lanzar la recogida"}
            </button>
            <p className="ayuda">Tarda unos 8-10 minutos. Al terminar se guarda sola: puedes volver a descargarla desde el historial.</p>
          </section>

          {historial.length > 0 && (
            <section className="card full">
              <h2>Recogidas guardadas</h2>
              <ul className="historial">
                {historial.map((r) => (
                  <li key={r.carpeta}>
                    <span className="h-marca">{r.marca}</span>
                    <span className="h-meta">
                      {r.fecha} · {r.keywords?.toLocaleString("es-ES")} keywords
                    </span>
                    <a href={urlExcel(r.id)}>Excel</a>
                    <a href={urlBriefing(r.id)}>Briefing</a>
                    <button type="button" className="link" onClick={() => seguir(r.id)}>
                      Ver
                    </button>
                  </li>
                ))}
              </ul>
            </section>
          )}
        </main>
      ) : (
        <Progreso estado={estado} error={error} nueva={nueva} />
      )}
    </div>
  );
}

function Progreso({ estado, error, nueva }: { estado: Estado; error: string; nueva: () => void }) {
  const r = estado.resumen;
  return (
    <main className="progreso">
      <section className="card">
        <div className="prog-head">
          <h2>{estado.marca}</h2>
          <span className="reloj">{mmss(estado.segundos)}</span>
        </div>
        {estado.bloqueo && <p className="bloqueo">{estado.bloqueo}</p>}
        <ul className="modulos">
          {MODULOS.map(([k, nombre]) => {
            const m = estado.modulos[k];
            if (!m) return null;
            const pct =
              k === "autocomplete" && m.estado === "corriendo"
                ? Math.min(98, (estado.segundos / estado.presupuesto_seg) * 100)
                : m.estado === "corriendo"
                  ? m.total
                    ? (m.hechas / m.total) * 100
                    : 50
                  : m.estado === "pendiente"
                    ? 0
                    : 100;
            return (
              <li key={k} className={`mod ${m.estado}`}>
                <div className="mod-top">
                  <span>{nombre}</span>
                  <span className="mod-estado">{m.estado}</span>
                </div>
                <div className="bar">
                  <div style={{ width: `${pct}%` }} />
                </div>
                <p className="mod-det">
                  {k === "autocomplete" && m.hechas > 0 ? `${m.hechas} consultas · ` : ""}
                  {m.detalle}
                </p>
              </li>
            );
          })}
        </ul>
        {estado.estado === "error" && <p className="error">La recogida falló: {estado.error}</p>}
        {error && <p className="error">{error}</p>}
      </section>

      {r && (
        <section className="card">
          <h2>Resultado</h2>
          <div className="stats">
            <Stat n={r.keywords} t="keywords únicas" />
            <Stat n={r.familias} t="familias (borrador)" />
            <Stat n={r.hueco?.["sí"] ?? 0} t="con hueco" />
            <Stat n={r.preguntas} t="preguntas" />
            <Stat n={r.con_volumen} t="con volumen real" />
            <Stat n={r.descartadas} t="descartadas" />
            <Stat n={r.dominios_leidos.length} t="dominios espejados" />
            <Stat n={r.avisos} t="avisos" />
          </div>
          <p className="nota">
            {Object.entries(r.por_intencion)
              .sort((a, b) => b[1] - a[1])
              .map(([k, v]) => `${k}: ${v}`)
              .join(" · ")}
          </p>
          {r.autocomplete_parado && r.autocomplete_parado !== "tiempo" && (
            <p className="aviso">El autocomplete se paró por bloqueo. Lo recogido está en el Excel; el detalle, en Avisos.</p>
          )}
          <a className="cta" href={urlExcel(estado.id)}>
            Descargar Excel
          </a>
          <div className="csvs">
            {PESTANAS.map((p) => (
              <a key={p} href={urlCsv(estado.id, p)}>
                {p}.csv
              </a>
            ))}
            <a href={urlBriefing(estado.id)}>briefing.json</a>
          </div>
          <p className="ayuda">Guardada en el historial de recogidas.</p>
          <button className="sec" onClick={nueva}>
            Nueva recogida
          </button>
        </section>
      )}
      {estado.estado === "error" && (
        <button className="sec" onClick={nueva}>
          Volver al briefing
        </button>
      )}
    </main>
  );
}

function Stat({ n, t }: { n: number; t: string }) {
  return (
    <div className="stat">
      <strong>{(n ?? 0).toLocaleString("es-ES")}</strong>
      <span>{t}</span>
    </div>
  );
}

function Campo({ label, req, ayuda, children }: { label: string; req?: boolean; ayuda?: string; children: React.ReactNode }) {
  return (
    <div className="campo">
      <span className="lbl">
        {label}
        {req && <b>*</b>}
      </span>
      {children}
      {ayuda && <span className="ayuda">{ayuda}</span>}
    </div>
  );
}

function Opciones({ valor, set, opciones }: { valor: string; set: (v: string) => void; opciones: [string, string][] }) {
  return (
    <div className="seg">
      {opciones.map(([v, t]) => (
        <button type="button" key={v} className={valor === v ? "on" : ""} onClick={() => set(v)}>
          {t}
        </button>
      ))}
    </div>
  );
}
