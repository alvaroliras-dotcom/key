# La Llave v2: lo que se ha hecho con tus peticiones

Nuria:

Esto responde a tus instrucciones del 4 de octubre y al PDF *La Llave, segunda vuelta*. Te cuento qué se ha hecho, qué se ha descartado y por qué, y qué sale de verdad cuando se lanza.

La regla que pediste no tocar sigue intacta: **el Excel no se genera si hay un volumen sin fuente.**

Una aclaración antes de empezar. Pediste los números de la prueba con **Marcos Cerrajeros**, pero no tenemos su briefing. La prueba se ha hecho otra vez con **El Gordo y el Flaco**: es la web de Álvaro, tenemos su Search Console y sirve para comparar con la primera recogida. En cuanto llegue el briefing de Marcos, se lanza igual.

> **Actualización, 4 de octubre (mañana):** Álvaro ha decidido **no contratar DataForSEO** (50 $ de entrada sin saber cuánto mejora los proyectos). Su código queda dentro y apagado. Sin DataForSEO:
> - el volumen sale de Search Console y del CSV del Keyword Planner (gratis con una cuenta de Google Ads, aunque dé rangos);
> - las preguntas, del autocomplete.
>
> Además, la web y el motor ya están publicados y conectados, y **el conector «La Llave» ya está dado de alta en claude.ai**: puedes usarlo desde hoy. Lanzar una recogida pide aprobación; leer el estado, el Excel y las pestañas, no. Una prueba real desde el servidor de Render confirmó que **Google bloquea el autocomplete hacia las 570 consultas** (desde el ordenador de Álvaro, 1.418 sin bloqueo). Aun así entregó unas 1.800 keywords con el aviso de bloqueo. Por eso: **una recogida por hora**.

---

## 1. En una frase

El Excel te llega **sin ruido, agrupado para leer y con la oportunidad marcada**. Además, puedes lanzar La Llave desde claude.ai sin pasar por el formulario.

---

## 2. Tus siete peticiones, una por una

### 1 · Filtro de ruido: hecho

- **Lista negra por defecto**, editable desde el formulario. Lleva tus 17 términos: chile, méxico, argentina, colombia, perú, barcelona, valencia, sevilla, curso, carrera, fp, máster, grado, sueldo, empleo, pdf y libro. **No lleva «online»**, como pediste: «agencia seo online» sigue dentro.
- **Una zona del briefing nunca se filtra.** Si mañana el cliente es de Valencia, «valencia» no se elimina, y queda registrado en Avisos.
- **Pestaña Descartadas.** Cada keyword eliminada aparece con su motivo («ruido: país», «ruido: ciudad fuera de alcance», «ruido: formación y empleo», «lista negra del cliente»), el término que la tumbó, el módulo y la semilla. Así puedes rescatar lo que se cuele.
- **Geo fuera de briefing.** La Llave conoce unos 300 lugares: los municipios de la Comunidad de Madrid, los distritos y barrios de Madrid capital, las capitales de provincia, las comunidades autónomas y los países de habla hispana. Lo que no está en el briefing ya no se queda sin zona: sale como «Coslada (fuera de briefing)». En la pestaña Lectura tienes las zonas de fuera más nombradas, con la pregunta «¿añadir al briefing?».

### 2 · Familias: hecho

Hay una columna «familia (borrador)» en Keywords y una pestaña **Familias**. Cada familia agrupa servicio + zona + intención. En las familias, las zonas de fuera se juntan en «otras zonas», para no multiplicar grupos.

Cada familia trae:
- número de keywords;
- impresiones de Search Console;
- búsquedas del Planner o de DataForSEO;
- cuántas keywords tienen hueco y con qué competidores;
- tu página propia, si la hay;
- cinco ejemplos.

Va marcada en el propio Excel como **«VISTA DE LECTURA · BORRADOR. No es clustering ni decide páginas»**.

### 3 · People Also Ask y búsquedas relacionadas: hecho, a falta de la clave

- **Con DataForSEO:** se lee la página de resultados de Google de hasta 15 semillas prioritarias y se sacan el bloque PAA y las búsquedas relacionadas. Las PAA van a la pestaña **Preguntas**. Las relacionadas entran además como keywords (módulo «relacionadas»). Si una búsqueda no trae PAA, queda en Avisos como «sin PAA»; no se inventa nada.
- **Siempre, aunque no haya clave:** las keywords del autocomplete formuladas como pregunta también pasan a Preguntas. En la prueba han salido 108.
- **Pendiente:** Álvaro todavía no tiene cuenta de DataForSEO, así que esta parte solo está probada con respuestas simuladas.

### 4 · Hueco frente a la competencia: hecho y probado

Columnas nuevas en Keywords:
- **hueco**: sí / no / —;
- **competidores con página**;
- **página propia**;
- **fiabilidad del hueco**.

Pediste que probara primero si la keyword inferida del competidor era fiable. Lo he hecho:

1. **Cada página espejada se etiqueta** con el mismo servicio y la misma zona que las keywords. Esa etiqueta tiene tres grados de fiabilidad:
   - **fuerte**: el servicio sale del H1 o de la keyword inferida;
   - **inferencia débil**: solo sale del title o de la URL (H1 vacío o de eslogan);
   - **sin servicio**: la página no corresponde a ningún servicio del briefing. Pasa con entradas del blog, «agencia de comunicación» o un «cupón de descuento».
2. **Fiabilidad real por web, en tu recogida:**

| Web | Páginas | Fuerte | Débil | Sin servicio |
|---|---|---|---|---|
| elestudiodemilo.es | 149 | 78 | 1 | 70 |
| softdream.es | 87 | 27 | — | 60 |
| idealweb.es | 47 | 13 | 15 | 19 |
| grupodreamsoft.com | 1 | — | 1 | — |
| elgordoyelflaco.es (propia) | 18 | 18 | — | — |

   **Lo que dice el dato:** tenías razón con **Milo**, que es muy fiable. Con **Idealweb**, no tanto: es la web más floja del espejo. Muchas de sus landings de barrio (Arganzuela, Moncloa) no tienen H1, así que solo se reconocen por la URL. Por eso existe la columna de fiabilidad.

3. **Corregí la regla de cobertura.** La primera versión comparaba zona con zona y salían 457 huecos, de los que 310 eran falsos. Tus páginas dicen «Diseño web **en Alcorcón**», y por eso no contaban como página para «diseño web barato». La regla buena para negocio local es:
   - una keyword **sin zona** la cubre cualquier página de ese servicio;
   - una keyword **con zona** («diseño web móstoles») solo la cubre una página de ese servicio en esa zona.

   Con la regla corregida quedan **147 huecos, y 145 son de inferencia fuerte**.

### 5 · Volumen para webs nuevas: hecho, a falta de la clave

- **Cascada:** Search Console → Keyword Planner → DataForSEO → sin dato. Cada keyword se queda con la primera fuente que responde.
- **Keyword Planner:** se lee el CSV de «Descargar ideas de palabras clave», que llega en UTF-16 con dos líneas de título; las dos cosas están resueltas. **Si el dato viene en rango («1 mil – 10 mil»), se escribe el rango tal cual**, con la marca «dato real en rango». Nunca se convierte en un número inventado.
- **DataForSEO:** volumen mensual medio y CPC de Google Ads, **solo para lo que no tenga Search Console ni Planner**, con un tope configurable. El coste de cada recogida aparece en la pestaña Lectura.
- **Pendiente:** la clave. Probado con respuestas simuladas: la cascada, los rangos, el CPC y la regla de honestidad funcionan juntos hasta el Excel.

### 6 · Pestaña Lectura: hecho

Es la primera pestaña del Excel. Trae los recuentos del informe ya hechos:
- ficha de la recogida;
- reparto por intención, servicio, zona y módulo de origen;
- zonas de fuera más nombradas;
- volumen por fuente;
- top 20 de Search Console, sin marca;
- familias más grandes;
- huecos más claros;
- fiabilidad del espejo por web;
- descartadas por motivo;
- avisos por tipo.

### 7 · Operativa: hecho

- **Briefing relanzable:** botones «Guardar briefing» y «Cargar briefing». El fichero `briefing.json` lleva también los CSV de Search Console y del Planner. Probado: al cargarlo vuelven todos los campos, las prioridades y el CSV.
- **El Excel ya no se pierde:** cada recogida se guarda en su propia carpeta, con el Excel, el briefing relanzable, un resumen y las pestañas. El formulario enseña el historial y permite volver a descargar cualquier recogida. Supabase queda preparado como opción, pero Álvaro eligió carpeta.
- **Ritmo prudente:** 2 consultas en paralelo como máximo. Si hubo otra recogida en la última hora, la siguiente va con pausas dobles y el formulario lo avisa antes de lanzar.
- **Bloqueo de Google:** si ocurre, sale un aviso grande en pantalla y en el conector, con la última semilla consultada; se entrega lo recogido.

---

## 3. El conector MCP (tu petición nueva)

La Llave se puede usar desde claude.ai. Tiene cuatro herramientas:

| Herramienta | Qué hace |
|---|---|
| `lanzar_recogida(briefing)` | Lanza una recogida y devuelve un id. El briefing tiene los mismos campos que el formulario. |
| `estado(id)` | Progreso por módulo. Al terminar trae el resumen y la pestaña **Lectura** completa. |
| `descargar_excel(id)` | Enlaces al Excel, al briefing.json y a cada pestaña en CSV. |
| `leer_pestana(id, pestaña)` | **Añadida:** lee cualquier pestaña (Keywords, Familias, Preguntas…) por tramos de hasta 300 filas, sin descargar nada. |

Añadí la cuarta porque desde claude.ai es más cómodo leer las familias directamente que descargar un archivo.

**La recogida de prueba se lanzó desde el propio conector**, igual que lo harás tú. El conector se protege con una ruta secreta: solo funciona quien tiene la dirección completa.

---

## 4. Resultados: El Gordo y el Flaco, 4 de octubre, 06:10

Briefing con tus prioridades: **agencia SEO, SEO local y diseño web** como prioritarios; diseño gráfico normal; analítica web secundaria. Lista negra del cliente: «gratis salvo auditoría, sherlock». Lista negra por defecto: la tuya.

### La prueba de aceptación

| Criterio | Pedido | Obtenido |
|---|---|---|
| Tiempo | menos de 10 min | **7 min 1 s** |
| Keywords únicas | más de 300 | **1.693** |
| Competidores con sitemap leído | al menos 2 | **4 de 4** y la web propia (353 páginas) |
| Volumen sin fuente | ninguno | **ninguno** |
| Bloqueo de Google | — | ninguno |

### Comparación con la primera recogida

| | v1 (3 oct) | v2 (4 oct) |
|---|---|---|
| Keywords | 3.410 | **1.693** |
| Consultas al autocomplete | 1.757 (bloqueada) | 1.418 (sin bloqueo) |
| Consultas en paralelo | 3 | 2 |
| Ruido dentro de la tabla | sí | **no: 139 en Descartadas** |
| Familias | — | **108** |
| Keywords con hueco | — | **147** |
| Preguntas | — | **108** |

**Hay la mitad de keywords, y es lo esperado.** Con 2 consultas en paralelo entran menos en el mismo tiempo, pero no hay bloqueo. El ruido ya no está en la tabla. Y las prioridades han cambiado: la sopa de letras completa se la llevan agencia SEO, SEO local y diseño web, que traen menos «analítica web avinash kaushik pdf». Si quieres más volumen, se sube el tiempo de recogida en Render (`AC_PRESUPUESTO_SEG`), siempre por debajo de 10 minutos.

### Reparto

| Intención | Keywords |
|---|---|
| Informacional | 660 (38 %) |
| Transaccional | 542 (32 %) |
| Local | 366 (21 %) |
| Comparativa | 65 |
| Marca | 60 |

| Servicio | Keywords |
|---|---|
| Diseño web | 397 |
| SEO local | 296 |
| Agencia SEO | 293 |
| Diseño gráfico | 88 |
| Google Ads | 79 |
| Analítica web | 16 |
| Auditoría SEO | 12 |
| Redacción SEO | 10 |
| Sin servicio | 502 |

**Zonas.**
- **Del briefing:** Alcorcón 62, Móstoles 16, Getafe 14, Fuenlabrada 11 y Leganés 10.
- **De fuera:** 293 keywords. Las más nombradas son **Madrid (49)**, España (11) y Zaragoza (8). Madrid merece pensarlo: ¿la añadimos al briefing de El Gordo y el Flaco?

### Descartadas: 139

| Motivo | Keywords | Ejemplos |
|---|---|---|
| Ruido: país | 53 | «agencias seo argentina», «cuanto cuesta google ads argentina» |
| Ruido: ciudad fuera de alcance | 47 | «agencia seo barcelona», «agencia de marketing online en barcelona» |
| Ruido: formación y empleo | 30 | «diseño grafico carrera», «diseño gráfico carrera nota de corte» |
| Lista negra del cliente (gratis) | 9 | «diseño gráfico online gratis», «curso redacción seo gratis» |

«Auditoría seo gratis» se queda dentro, porque es el cebo de Sherlock.

### Los huecos más claros (145 de 147 con inferencia fuerte)

- **Diseño web en tu zona:** Milo y Softdream tienen landings de diseño web en **Móstoles, Getafe, Leganés y Fuenlabrada**. Milo además en **Majadahonda y Pozuelo**. Tus landings de municipio son de agencia SEO; de diseño web no tienes ninguna.
- **Diseño gráfico en Alcorcón:** Softdream tiene «diseño gráfico en Alcorcón». Tu página de diseño gráfico no nombra Alcorcón.
- **Google Ads en Getafe:** Milo tiene página.
- **Blog:** 46 keywords informacionales de diseño web y 11 de Google Ads para las que Milo, Idealweb o Softdream tienen entrada y tú no. Es lo que decías del blog: Softdream tiene 50 entradas, Milo 33 y tú 0.
- **Madrid y sus barrios:** Milo e Idealweb trabajan landings de barrio (Chamberí, Arganzuela, Chamartín…). Si Madrid no entra en el briefing, son huecos que no te interesan.

### Top de Search Console (sin marca)

| Keyword | Impresiones | Posición |
|---|---|---|
| agencia seo alcorcón | 847 | 25,4 |
| seo alcorcón | 516 | 42,7 |
| diseño web alcorcón | 386 | 20,7 |
| diseño web para negocios locales | 370 | 16,9 |
| consultor seo alcorcón | 316 | 60,3 |
| agencia de seo alcorcón | 292 | 25,1 |
| gráfica para empresas | 262 | 35,3 |
| optimizar ficha google my business | 241 | 70,5 |
| agencia google ads alcorcón | 183 | 33,2 |

La lectura de la primera vuelta se confirma: **hay demanda en Alcorcón y la web está en segunda o tercera página para lo que importa.**

---

## 5. Lo que se descartó y por qué

1. **Leer directamente la página de resultados de Google para las PAA.** Google bloquea las consultas desde servidores compartidos como Render. Se hace con DataForSEO, que es fiable y cuesta céntimos.
2. **Supabase como almacén obligatorio.** Álvaro eligió guardar en carpeta. Supabase queda como opción, activable con dos variables.
3. **«online» en la lista negra.** Decisión tuya.
4. **La primera regla del hueco.** Ver el punto 4 del apartado 2: daba 310 huecos falsos.

## 6. Lo que queda pendiente

1. **La clave de DataForSEO.** Álvaro crea la cuenta y la pone en Render. Hasta entonces, sin PAA ni volumen de pago; todo lo demás funciona.
2. **Terminar el despliegue.** La web ya está en Vercel y el motor se está instalando en Render. Faltan tres cosas: unirlos, fijar la dirección pública del motor y dar de alta el conector en claude.ai.
3. **La prueba con Marcos Cerrajeros**, en cuanto llegue su briefing.
4. **Detección automática de competidores** (del briefing original; no entró en esta vuelta).
5. **v3:** Google Trends, histórico en Supabase y borrador de clustering automático.

## 7. Dónde está cada cosa

- **Repositorio:** `github.com/alvaroliras-dotcom/key`. En `docs/` están tu briefing, tu PDF de peticiones (ya con la página de la v2, «hecho / descartado / pendiente») y este informe.
- **El Excel de esta prueba:** `la-llave-el-gordo-y-el-flaco.xlsx`, junto a este informe.

---

*La Llave · El Gordo y el Flaco Marketing Online · 4 de octubre de 2026 · recogida 7ff042d43b6b.*
