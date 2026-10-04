# La Llave: lo que estamos construyendo con tu briefing

Nuria:

Esto es la respuesta a tu briefing de octubre, *Herramienta de keyword research*. Te cuento qué está hecho, cómo funciona por dentro, qué he cambiado respecto a lo que pediste y por qué, y qué sale de verdad cuando se lanza. Al final hay dos decisiones que son tuyas.

La herramienta se llama **La Llave** (en inglés, *The Key*). El nombre lo puso Álvaro.

---

## 1. En una frase

Hace el trabajo mecánico que hoy te come el 80 % del tiempo y te entrega la materia prima limpia en un Excel. **No toca tu criterio**: el clustering, la arquitectura de URLs, la asignación de keyword principal y secundarias, la anti-canibalización y las fases siguen siendo tuyas. La Llave no te propone ninguna página.

---

## 2. Dónde encaja

```
Sabueso → Sherlock → LA LLAVE → Nuria → Matías → Merche · Jean Paul
                     recoge      piensa
```

Tú rellenas el briefing en un formulario web, pulsas un botón y en 7-8 minutos descargas el Excel. De cada pestaña hay también un CSV plano, que es lo que me dijiste que mejor lees cuando se pega en una conversación.

---

## 3. Qué hay construido (la v1)

### 3.1 El formulario de entrada

Es tu plantilla, campo a campo. Si falta un obligatorio, no arranca.

| Campo | Cómo se rellena | Para qué lo usa |
|---|---|---|
| Dominio y marca * | texto | semillas de marca y lectura de la web propia |
| Sector * | texto | semilla de categoría («agencia de marketing online», «agencia de marketing online alcorcón») |
| Servicios * | uno por línea; **un asterisco delante = prioritario** | eje de las semillas; los prioritarios pasan la sopa de letras completa primero |
| Lo que NO ofrece | uno por línea; **admite excepciones**: `gratis salvo auditoría, sherlock` | lista negra: elimina las keywords que lo contengan, salvo las excepciones |
| Objetivo * | urgencias / leads / marca / ventas | decide qué modificadores pesan más (urgencias → «urgente», «24 horas»; leads → «precio», «presupuesto»; ventas → «precio», «barato») |
| Sede, zona principal, zonas secundarias * | texto | eje geo de las semillas |
| Alcance * | local / provincial / nacional | en nacional no se cruza con geo |
| Web * | nueva / existente (+ URL y sitemap opcional) | con web existente se lee su arquitectura igual que la de un competidor |
| CSV de Search Console | archivo `Consultas.csv` del ZIP | primera fuente de volumen |
| Competidores | hasta 5 URL (tú pediste 1-3; Álvaro quiso 4) | espejo por sitemap |
| Jerga del público | uno por línea; admite `término = servicio` (`posicionamiento web = agencia seo`) | semillas coloquiales y detección del servicio |
| Idioma / mercado | España por defecto (también Latinoamérica y catalán) | fija el Google y el idioma del autocomplete |
| Modificadores | editables, por intención | ver 3.2 |

Antes de lanzar, la pantalla enseña **el orden de la cascada de volumen** y qué fuentes están activas, como pediste.

### 3.2 Módulo 1: generador de semillas

Combina **servicio × modificador × zona** con tu lista de modificadores por defecto (editable desde el formulario):

- **Transaccional:** urgente, 24 horas, 24h, precio, presupuesto, barato, económico, reparar…, instalar…
- **Local:** cerca de mí, a domicilio, más cada zona («servicio zona» y «servicio en zona»).
- **Informacional:** cómo…, qué…, cuánto cuesta…
- **Comparativa / confianza:** mejor…, opiniones, homologado, de confianza.

Reglas de cruce:
- Servicio solo y servicio × cada modificador, sin zona.
- Servicio × cada zona.
- Servicio × modificador transaccional × **solo la zona principal**, para no multiplicar sin sentido.
- Variantes en plural y sin tilde del servicio y del servicio + zona.
- Marca, marca + zona principal y marca + opiniones.
- La jerga, sola y con la zona principal.
- El sector, solo y con la zona principal.

Con El Gordo y el Flaco (8 servicios, 11 zonas) salieron **581 semillas**. En la pestaña Semillas ves cuántas sugerencias produjo cada una: es tu mapa de cobertura.

### 3.3 Módulo 2: autocomplete en sopa de letras

Para cada semilla consulta el autocomplete de Google (google.es, español) con la semilla sola y con la semilla + cada letra a-z, la ñ y 0-9: **38 consultas por semilla**. Guarda cada sugerencia con su semilla de origen y su posición en la lista.

Hacer la sopa completa de 581 semillas serían 22.000 consultas, y eso no cabe en 10 minutos ni Google lo aguanta. Así que La Llave reparte el tiempo (7 minutos) por orden de rendimiento:

1. **Sopa completa de las prioritarias**, primero las que no llevan zona.
2. **Consulta simple** (semilla sola) de todas las demás.
3. **Sopa completa del resto**, mientras quede tiempo.
4. Opcional: segundo nivel, la sopa sobre las 20 sugerencias más repetidas.

Ritmo: 3 consultas en paralelo, pausas aleatorias de 0,25 a 0,8 s y 8 navegadores distintos que se van rotando.

### 3.4 Módulo 5: espejo de competidores

Para cada competidor (y para la web propia, si existe):

1. Busca el sitemap: primero el `robots.txt`, después `sitemap_index.xml`, `sitemap.xml`, `wp-sitemap.xml` y otros. Recorre los sitemaps hijos. Descarta imágenes, etiquetas, autores y categorías.
2. Si no hay sitemap, lee la home y sigue los enlaces del menú.
3. De cada URL saca el **title, el H1, la meta description y los 6 primeros H2**.
4. **Clasifica el patrón de URL:** home, servicio, servicio-ciudad, blog, empresa, contacto o legal.
5. **Infiere la keyword** que parece trabajar la página: el H1 si es razonable; si no, el title sin la marca.

Lee hasta 150 páginas por dominio, primero las de servicio y luego las del blog. Si hay más, lo avisa.

### 3.5 Módulo 6: volumen en cascada (en la v1, solo Search Console)

Cruza cada keyword con el CSV de Search Console y suma las variantes («agencia seo alcorcón» + «agencia seo alcorcon»). Guarda **impresiones, clics y posición media** (ponderada por impresiones).

Si una keyword no aparece en el CSV: volumen vacío, fuente «sin dato fiable». **Nunca un número inventado.** El Excel ni siquiera se genera si alguna celda tiene número y no tiene fuente: es una comprobación del código, no una promesa.

### 3.6 Deduplicado, normalización y etiquetas

- **Una keyword = una fila.** Se agrupan minúsculas, tildes, singular/plural y espacios: «Cerrajeros Alcorcón» y «cerrajero alcorcon» son la misma. Se muestra la forma más buscada.
- **Lista negra** aplicada al entrar, con el recuento en Avisos.
- **Etiquetas automáticas:**
  - geo detectada (de tus zonas, más «cerca de mí»);
  - servicio detectado (incluida la jerga);
  - intención: transaccional / local / comparativa / informacional / marca.

La **intención es una etiqueta de lectura, no un clustering**. Sale de reglas sobre el texto:

| Intención | Cuándo |
|---|---|
| Informacional | qué, cómo, cuánto, para qué, pdf, curso, carrera, fp, sueldo, empleo… |
| Comparativa | mejor, opiniones, vs, homologado… |
| Marca | lleva el nombre de la marca |
| Transaccional | precio, presupuesto, urgente, empresa, negocio… |
| Local | lleva zona sin modificador comercial |
| Servicio a secas | transaccional; si es una cola larga sin modificador comercial, informacional |

Añadí **marca** a tus cuatro intenciones porque sin ella las búsquedas de marca se mezclaban con las demás.

### 3.7 El Excel de salida

Lleva cabecera fucsia y logo GYF, filas alternas, filtros y la primera fila congelada. Tiene las cinco pestañas de tu v1:

| Pestaña | Contenido | Columnas |
|---|---|---|
| **Keywords** | una fila por keyword única | keyword · semilla origen · módulo · intención · geo · servicio · volumen · fuente del volumen · marca de estimación · nº de apariciones · clics (GSC) · posición media (GSC) |
| **Competidores** | cada página de cada competidor y de la web propia | dominio · URL · title · H1 · meta description · H2 · patrón de URL · keyword inferida |
| **Semillas** | todas las semillas y su rendimiento | semilla · servicio · intención · geo · tipo · prioritaria · nº de sugerencias · consultas · estado |
| **Avisos** | todo lo que falló o quedó sin dato | tipo · elemento afectado · detalle |
| **Briefing** | copia del formulario, para trazabilidad | campo · valor |

La pestaña Keywords viene **ordenada como tú empiezas a leer**: primero transaccional; después local, marca, comparativa e informacional; y dentro de cada una, por número de apariciones.

Añadí dos columnas que no pediste, **clics y posición media de Search Console**, porque el dato ya venía en el CSV y te sirve para ver dónde hay impresiones sin clic.

---

## 4. Cómo está construido

- **Backend:** Python con FastAPI, en **Render** (no en Railway como decía tu briefing: Sherlock ya vive en Render y Álvaro prefirió no tener dos proveedores).
- **Frontend:** React en Vercel.
- **Sin base de datos:** cada proyecto es un formulario y un Excel, como pediste.
- **Librerías:** httpx y BeautifulSoup para leer webs y sitemaps; openpyxl para el Excel.

La recogida corre en segundo plano y la web enseña una barra de progreso por módulo. El autocomplete y el espejo de competidores van **a la vez**, porque consultan servidores distintos, y eso ahorra tiempo.

**Qué pasa cuando Google bloquea.** Cada consulta fallida se reintenta como máximo dos veces, con espera. Con cuatro bloqueos seguidos el módulo se para, **entrega lo que tiene** y deja en Avisos hasta qué semilla llegó y cuántas consultas hizo. Nunca reintenta en silencio.

---

## 5. Lo que cambié respecto a tu briefing, y por qué

1. **El orden de la sopa de letras.** Tu briefing ponía como prioritarias «servicio × zona principal». En la prueba real, «cerrajero alcorcón + letra» devuelve casi cero sugerencias. En cambio, «cerrajero + a» ya devuelve «cerrajero alcorcón», «cerrajero aluche»… Con 40 segundos de prueba, tu orden sacó **27 keywords** y el nuevo **1.107**. Ahora las prioritarias sin zona van primero.
2. **Semillas que Google no reconoce.** Si la semilla sola no da ninguna sugerencia («reparar seo local», «instalar diseño gráfico»), no se gastan en ella las 37 consultas de las letras. Su estado queda como «sin sugerencias».
3. **La lista negra admite excepciones.** Álvaro solo regala la auditoría (el cebo de Sherlock): `gratis salvo auditoría, sherlock`.
4. **Hasta 5 competidores**, en lugar de 3.
5. **La web propia también se espeja**, así ves tu arquitectura al lado de la de los competidores.
6. **La intención «marca»**, como te expliqué en 3.6.

---

## 6. Resultados reales: El Gordo y el Flaco

Probé con la web de Álvaro porque tenemos todos los datos: su Search Console (456 consultas, últimos 16 meses) y cuatro competidores que él eligió.

**Briefing usado:**
- **Servicios:** agencia seo, seo local, diseño web, google ads, auditoría seo, **\*diseño gráfico**, redacción seo, **\*analítica web** (prioritarios los dos marcados, por decisión de Álvaro).
- **Zonas:** Alcorcón y las 10 de sus landings (Getafe, Móstoles, Leganés, Fuenlabrada, Majadahonda, Boadilla del Monte, Arroyomolinos, Villaviciosa de Odón, Pozuelo de Alarcón y Brunete).
- **Objetivo:** leads.
- **Lista negra:** gratis, salvo auditoría y Sherlock.
- **Competidores:** softdream.es, idealweb.es, grupodreamsoft.com, elestudiodemilo.es.
- **Jerga:** posicionamiento web, posicionamiento en google y agencia de marketing (= agencia seo); ficha de google y google maps (= seo local); página web (= diseño web).

### La prueba de aceptación

| Criterio de tu briefing | Pedido | Obtenido |
|---|---|---|
| Tiempo | < 10 min | **6 min 38 s** |
| Keywords únicas | > 300 | **3.410** |
| Competidores con sitemap leído | ≥ 2 | **4 de 4**, más la web propia (353 páginas) |
| Volumen sin fuente | ninguno | **ninguno** (430 con dato real de Search Console; el resto, vacío y marcado) |

### De dónde salen las keywords

| Módulo | Keywords |
|---|---|
| Autocomplete | 2.711 |
| Search Console | 430 |
| Competidores (keyword inferida) | 275 |
| Web propia | 18 |

Algunas keywords salen de varios módulos a la vez.

### Por intención

| Intención | Keywords |
|---|---|
| Transaccional | 1.620 |
| Informacional | 975 |
| Local | 641 |
| Comparativa | 112 |
| Marca | 62 |

### Por servicio detectado

| Servicio | Keywords |
|---|---|
| SEO local | 1.184 |
| Agencia SEO | 765 |
| Diseño gráfico | 439 |
| Diseño web | 226 |
| Google Ads | 126 |
| Auditoría SEO | 66 |
| Analítica web | 64 |
| Redacción SEO | 13 |
| Sin servicio | 527 (marca, términos sueltos, otras zonas) |

### Por zona

| Zona | Keywords |
|---|---|
| Leganés | 187 |
| Fuenlabrada | 162 |
| Alcorcón | 121 |
| Móstoles | 114 |
| «Cerca de mí» | 68 |
| Getafe | 57 |
| Pozuelo de Alarcón | 20 |
| Villaviciosa de Odón | 20 |
| Majadahonda | 13 |
| Boadilla del Monte | 13 |
| Arroyomolinos | 9 |
| Brunete | 9 |
| Sin zona | 2.617 |

### Lo que más impresiones tiene de verdad (Search Console, sin contar marca)

| Keyword | Impresiones | Posición media |
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

Lectura rápida para ti: **hay demanda real en Alcorcón y la web está en segunda o tercera página para todo lo que importa.** Ahí tienes material para las fases.

### El espejo de la competencia

| Dominio | Páginas | Servicio | Servicio-ciudad | Blog |
|---|---|---|---|---|
| elestudiodemilo.es | 150 de 170 | 87 | 28 | 33 |
| softdream.es | 94 | 25 | 11 | 50 |
| idealweb.es | 82 | 27 | 1 (en realidad, más) | 18 |
| grupodreamsoft.com | 4 | 0 | 0 | 0 |
| elgordoyelflaco.es (propia) | 23 | 7 | 10 | 0 |

- **elestudiodemilo.es:** landings de municipio como las nuestras (diseño web en Getafe, en Leganés, en Coslada; posicionamiento web en Villaviciosa de Odón…).
- **softdream.es:** también tiene landings de municipio (diseño web en Leganés, en Fuenlabrada) y un blog grande.
- **idealweb.es:** trabaja barrios de Madrid (Chamberí, Arganzuela, Vallecas, Moncloa) que no están en el briefing, por eso salen como «servicio». Ver limitaciones.
- **grupodreamsoft.com:** su sitemap solo tiene la home y las legales. No hay más que leer.

### Avisos registrados

- elestudiodemilo.es tiene 170 URLs; se leyeron las 150 primeras.
- Google bloqueó el autocomplete a las 1.757 consultas. Era la tercera recogida grande desde la misma IP en una hora. Se paró, entregó lo que tenía y dejó apuntada la última semilla.
- 32 keywords eliminadas por «gratis».
- 2.980 keywords sin volumen: no están en Search Console y en la v1 no hay otra fuente.

---

## 7. Limitaciones que debes conocer

1. **Las zonas que no están en el briefing no se detectan** (Madrid, Coslada, Chamberí…). Esas keywords salen sin geo y las landings de esos barrios se clasifican como «servicio» en lugar de «servicio-ciudad». Si te interesan, añade esas zonas al briefing.
2. **La intención es por reglas.** Acierta en lo claro y falla en algún caso raro: «analítica web para empresas arte ingenio y anticipación» es el título de un libro y sale transaccional porque lleva «empresas».
3. **Entra ruido de otros mercados y de estudiantes:** «agencia seo chile», «agencia seo méxico», «diseño gráfico curso»… Se filtra con la lista negra (ver decisiones).
4. **Search Console trae ruido de marca:** «flaco», «el gordo», «ines ingenieros». Son datos reales y no se tocan.
5. **Bloqueos de Google.** Una recogida por proyecto va bien. Varias seguidas desde el mismo servidor, no. Si en Avisos aparecen bloqueos, se baja la velocidad desde Render.
6. **Render gratuito** tarda unos 50 s en despertar la primera vez y borra los Excel al dormirse: hay que descargarlo al terminar.

---

## 8. Lo que viene

- **v2:** People Also Ask y búsquedas relacionadas, pestaña Preguntas, CSV del Keyword Planner como segunda fuente de volumen y detección automática de competidores.
- **v3:** DataForSEO, Google Trends (solo como tendencia, nunca mezclado con el volumen), histórico en Supabase y un borrador de clustering. Será siempre un borrador, nunca tu entregable.

---

## 9. Dos decisiones que son tuyas

**1. Ampliar la lista negra.** Han entrado búsquedas de otros mercados («agencia seo chile», «agencia seo méxico», «agencia seo barcelona») y de formación («diseño gráfico online», «diseño gráfico curso / carrera / fp»). Las de formación ya salen como informacionales, pero siguen en la tabla. Si no traen clientes, añádelas a «Lo que NO ofrece» y desaparecen en la próxima recogida. Por ejemplo: `chile`, `méxico`, `argentina`, `colombia`, `curso`, `carrera`, `fp`, `máster`, `empleo`. ¿Cuáles entran?

**2. Las prioridades.** Con diseño gráfico y analítica web como prioritarios, la cabeza del Excel es de esos dos servicios. Pero «analítica web» atrae sobre todo a gente que estudia (libros, PDF de Avinash Kaushik, «ventajas y desventajas»), no a clientes. Los datos de Search Console dicen que la demanda real está en **agencia SEO / SEO local y diseño web en Alcorcón**. Si el objetivo es leads, quizá convenga priorizar esos. ¿Mantienes las prioridades o las cambias?

---

*La Llave · El Gordo y el Flaco Marketing Online · octubre 2026.*
