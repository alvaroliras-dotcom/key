export const API_URL = (import.meta.env.VITE_API_URL ?? "http://localhost:8000").replace(/\/$/, "");

export interface Servicio {
  nombre: string;
  prioritario: boolean;
}

/** Igual que el modelo Briefing del backend: es también el formato del fichero relanzable. */
export interface Briefing {
  dominio: string;
  marca: string;
  sector: string;
  servicios: Servicio[];
  objetivo: "urgencias" | "leads" | "marca" | "ventas";
  sede: string;
  zona_principal: string;
  zonas_secundarias: string[];
  alcance: "local" | "provincial" | "nacional";
  web_estado: "nueva" | "existente";
  url_web?: string | null;
  sitemap_url?: string | null;
  no_ofrece: string[];
  ruido?: string[] | null;
  gsc_csv?: string | null;
  gsc_nombre?: string | null;
  planner_csv?: string | null;
  planner_nombre?: string | null;
  competidores: string[];
  jerga: string[];
  mercado: string;
  modificadores?: Record<string, string[]> | null;
  segundo_nivel: boolean;
  preguntas: boolean;
  volumen_dataforseo: boolean;
}

export interface Modulo {
  estado: "pendiente" | "corriendo" | "hecho" | "parcial" | "bloqueado" | "omitido";
  detalle: string;
  hechas: number;
  total: number;
}

export interface Resumen {
  keywords: number;
  descartadas: number;
  por_intencion: Record<string, number>;
  semillas: number;
  consultas_autocomplete: number;
  autocomplete_parado: string | null;
  dominios_leidos: string[];
  paginas_competidores: number;
  con_volumen: number;
  volumen_por_fuente: Record<string, number>;
  preguntas: number;
  hueco: Record<string, number>;
  familias: number;
  coste_dataforseo: number;
  avisos: number;
  duracion_seg: number;
}

export interface Estado {
  id: string;
  marca: string;
  estado: "corriendo" | "terminado" | "error";
  segundos: number;
  presupuesto_seg: number;
  modulos: Record<string, Modulo>;
  resumen: Resumen | null;
  error: string | null;
  bloqueo: string | null;
}

export interface Cascada {
  cascada: { fuente: string; como: string; disponible: string }[];
  modificadores_por_defecto: Record<string, string[]>;
  ruido_por_defecto: string[];
  dataforseo: boolean;
  supabase: boolean;
  recogida_reciente_min: number | null;
}

export interface Recogida {
  carpeta: string;
  id: string;
  marca: string;
  fecha: string;
  keywords: number;
  duracion_seg: number;
}

async function json<T>(res: Response): Promise<T> {
  if (!res.ok) {
    let msg = `Error ${res.status}`;
    try {
      const d = await res.json();
      if (typeof d?.detail === "string") msg = d.detail;
      else if (Array.isArray(d?.detail))
        msg = d.detail.map((e: { loc?: string[]; msg: string }) => `${e.loc?.slice(1).join(".")}: ${e.msg}`).join(" · ");
    } catch {
      // sin cuerpo JSON
    }
    throw new Error(msg);
  }
  return res.json() as Promise<T>;
}

export const getCascada = () => fetch(`${API_URL}/cascada`).then((r) => json<Cascada>(r));

export const getRecogidas = () =>
  fetch(`${API_URL}/recogidas`).then((r) => json<{ recogidas: Recogida[] }>(r));

export const crearProyecto = (b: Briefing) =>
  fetch(`${API_URL}/proyectos`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(b),
  }).then((r) => json<{ id: string }>(r));

export const getEstado = (id: string) => fetch(`${API_URL}/proyectos/${id}`).then((r) => json<Estado>(r));

export const urlExcel = (id: string) => `${API_URL}/proyectos/${id}/excel`;
export const urlBriefing = (id: string) => `${API_URL}/proyectos/${id}/briefing`;
export const urlCsv = (id: string, pestana: string) => `${API_URL}/proyectos/${id}/csv/${pestana}`;

/** Lee un CSV respetando su codificación: el Keyword Planner exporta en UTF-16. */
export async function leerCsv(file: File): Promise<string> {
  const buf = new Uint8Array(await file.arrayBuffer());
  if (buf[0] === 0xff && buf[1] === 0xfe) return new TextDecoder("utf-16le").decode(buf.subarray(2));
  if (buf[0] === 0xfe && buf[1] === 0xff) return new TextDecoder("utf-16be").decode(buf.subarray(2));
  return new TextDecoder("utf-8").decode(buf).replace(/^﻿/, "");
}
