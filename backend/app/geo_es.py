"""
Lugares conocidos para detectar la «geo fuera de briefing»: una keyword que nombra
una zona que no está en el briefing (Madrid, Coslada, Chamberí…) no se queda sin
geo; se marca con la zona y «(fuera de briefing)».

Se han dejado fuera los nombres que son palabras corrientes («Centro», «Ventas»,
«Retiro», «Delicias»…), porque darían falsos positivos.
"""

# Comunidad de Madrid: municipios
MADRID_MUNICIPIOS = """
Madrid, Móstoles, Alcalá de Henares, Fuenlabrada, Leganés, Getafe, Alcorcón,
Torrejón de Ardoz, Parla, Alcobendas, Las Rozas, Las Rozas de Madrid,
San Sebastián de los Reyes, Pozuelo de Alarcón, Rivas-Vaciamadrid, Rivas Vaciamadrid,
Coslada, Valdemoro, Majadahonda, Collado Villalba, Aranjuez, Arganda del Rey,
Boadilla del Monte, Pinto, Colmenar Viejo, Tres Cantos, San Fernando de Henares,
Galapagar, Arroyomolinos, Villaviciosa de Odón, Navalcarnero, Ciempozuelos, Torrelodones,
Paracuellos de Jarama, Mejorada del Campo, Algete, Villanueva de la Cañada,
San Martín de la Vega, Villanueva del Pardillo, Humanes de Madrid, Guadarrama,
El Escorial, San Lorenzo de El Escorial, Meco, Alpedrete, Moralzarzal, Daganzo de Arriba,
Daganzo, Villalbilla, Griñón, Sevilla la Nueva, Moraleja de Enmedio, Cercedilla,
Hoyo de Manzanares, Collado Mediano, Manzanares el Real, Soto del Real, Brunete,
Velilla de San Antonio, Torrejón de la Calzada, Torrejón de Velasco, Casarrubuelos,
Cubas de la Sagra, Serranillos del Valle, Batres, Chinchón, Colmenarejo, Valdemorillo,
Quijorna, Villamanta, Villamantilla, Aldea del Fresno, Navas del Rey, Chapinería,
Pelayos de la Presa, San Martín de Valdeiglesias, Cadalso de los Vidrios, Cenicientos,
Robledo de Chavela, Fresnedillas de la Oliva, Zarzalejo, Santa María de la Alameda,
Becerril de la Sierra, Los Molinos, Navacerrada, Miraflores de la Sierra, Guadalix de la Sierra,
El Molar, Pedrezuela, San Agustín del Guadalix, Talamanca de Jarama, Valdetorres de Jarama,
Fuente el Saz de Jarama, Fuente el Saz, Ribatejada, Valdeolmos-Alalpardo, Cobeña, Ajalvir,
Camarma de Esteruelas, Torres de la Alameda, Loeches, Campo Real, Nuevo Baztán,
Villar del Olmo, Pozuelo del Rey, Valverde de Alcalá, Anchuelo, Santorcaz, Corpa,
Morata de Tajuña, Perales de Tajuña, Tielmes, Carabaña, Valdilecha, Orusco de Tajuña,
Villarejo de Salvanés, Colmenar de Oreja, Belmonte de Tajo, Valdelaguna, Villaconejos,
Titulcia, Estremera, Fuentidueña de Tajo, Buitrago del Lozoya, Lozoyuela,
Torrelaguna, El Boalo, Cerceda, Mataelpino, El Álamo, Villa del Prado, Sevilla la Nueva
"""

# Madrid capital: distritos y barrios con nombre propio
MADRID_BARRIOS = """
Arganzuela, Chamartín, Tetuán, Chamberí, Fuencarral, Fuencarral-El Pardo, El Pardo,
Moncloa, Moncloa-Aravaca, Aravaca, La Latina, Carabanchel, Usera, Puente de Vallecas,
Moratalaz, Ciudad Lineal, Hortaleza, Villaverde, Villa de Vallecas, Vallecas, Vicálvaro,
San Blas, San Blas-Canillejas, Canillejas, Barajas, Aluche, Lavapiés, Malasaña, Chueca,
Argüelles, Sanchinarro, Las Tablas, Montecarmelo, Valdebebas, Mirasierra, Peñagrande,
Tres Olivos, La Moraleja, Arturo Soria, Legazpi, Opañel, Vista Alegre, Abrantes,
Orcasitas, Pradolongo, Almendrales, Entrevías, Palomeras, Portazgo, Santa Eugenia,
Ensanche de Vallecas, Valdebernardo, El Cañaveral, Butarque, Saconia, Ciudad Universitaria,
Puerta del Ángel, Campamento, Cuatro Vientos, Batán, Lucero, Embajadores, Cuatro Caminos,
Ríos Rosas, Vallehermoso, Gaztambide, Trafalgar, Bernabéu, Plaza de Castilla, Pinar de Chamartín
"""

# Capitales de provincia, ciudades grandes y comunidades autónomas
ESPANA = """
Barcelona, Valencia, Sevilla, Zaragoza, Málaga, Murcia, Palma, Palma de Mallorca,
Las Palmas, Las Palmas de Gran Canaria, Bilbao, Alicante, Córdoba, Valladolid, Vigo, Gijón,
L'Hospitalet, Hospitalet de Llobregat, Vitoria, Vitoria-Gasteiz, A Coruña, La Coruña, Granada,
Elche, Oviedo, Badalona, Terrassa, Cartagena, Jerez, Jerez de la Frontera, Sabadell,
Santa Cruz de Tenerife, Tenerife, Pamplona, Almería, San Sebastián, Donostia, Burgos,
Santander, Castellón, Castellón de la Plana, Albacete, Logroño, Badajoz, Salamanca, Huelva,
Marbella, Lleida, Lérida, Tarragona, León, Cádiz, Jaén, Ourense, Orense, Lugo, Girona, Gerona,
Cáceres, Guadalajara, Toledo, Pontevedra, Palencia, Ciudad Real, Zamora, Ávila, Cuenca,
Huesca, Segovia, Soria, Teruel, Ceuta, Melilla, Algeciras, Mataró, Torrevieja, Reus,
Benidorm, Ibiza, Menorca, Mallorca, Talavera de la Reina, Ponferrada, Santiago de Compostela,
Andalucía, Cataluña, Catalunya, Comunidad Valenciana, Galicia, País Vasco, Euskadi, Aragón,
Asturias, Cantabria, Navarra, La Rioja, Extremadura, Castilla y León, Castilla-La Mancha,
Castilla La Mancha, Islas Baleares, Baleares, Canarias, Islas Canarias, Comunidad de Madrid
"""

# Países y capitales de habla hispana (y algunos más que se cuelan en el autocomplete)
PAISES = """
México, Mexico, Argentina, Colombia, Chile, Perú, Venezuela, Ecuador, Uruguay, Paraguay,
España, Bolivia, Guatemala, Honduras, El Salvador, Nicaragua, Costa Rica, Panamá, Cuba,
República Dominicana, Puerto Rico, Estados Unidos, USA, Andorra, Portugal, Francia,
Bogotá, Medellín, Cali, Lima, Santiago de Chile, Buenos Aires, Córdoba Argentina, Rosario,
Ciudad de México, CDMX, Guadalajara Jalisco, Monterrey, Puebla, Quito, Guayaquil, Caracas,
Montevideo, Asunción, La Paz, Santo Domingo, Miami
"""


def _lista(bloque: str):
    return [n.strip() for n in bloque.replace("\n", " ").split(",") if n.strip()]


LUGARES = {}
for _bloque, _tipo in ((MADRID_MUNICIPIOS, "municipio"), (MADRID_BARRIOS, "barrio"),
                       (ESPANA, "España"), (PAISES, "extranjero")):
    for _n in _lista(_bloque):
        LUGARES.setdefault(_n, _tipo)
