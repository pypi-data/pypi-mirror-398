import re

from unidecode import unidecode

CITY_TO_PROVINCE = {"Madrid": "Madrid"}

POSTCODES = {
    "01": "Álava",
    "02": "Albacete",
    "03": "Alicante",
    "04": "Almería",
    "05": "Ávila",
    "06": "Badajoz",
    "07": "Baleares",
    "08": "Barcelona",
    "09": "Burgos",
    "10": "Cáceres",
    "11": "Cádiz",
    "12": "Castellón",
    "13": "Ciudad Real",
    "14": "Córdoba",
    "15": "La Coruña",
    "16": "Cuenca",
    "17": "Gerona",
    "18": "Granada",
    "19": "Guadalajara",
    "20": "Guipúzcoa",
    "21": "Huelva",
    "22": "Huesca",
    "23": "Jaén",
    "24": "León",
    "25": "Lérida",
    "26": "La Rioja",
    "27": "Lugo",
    "28": "Madrid",
    "29": "Málaga",
    "30": "Murcia",
    "31": "Navarra",
    "32": "Orense",
    "33": "Asturias",
    "34": "Palencia",
    "35": "Las Palmas",
    "36": "Pontevedra",
    "37": "Salamanca",
    "38": "Santa Cruz de Tenerife",
    "39": "Cantabria",
    "40": "Segovia",
    "41": "Sevilla",
    "42": "Soria",
    "43": "Tarragona",
    "44": "Teruel",
    "45": "Toledo",
    "46": "Valencia",
    "47": "Valladolid",
    "48": "Vizcaya",
    "49": "Zamora",
    "50": "Zaragoza",
    "51": "Ceuta",
    "52": "Melilla",
}

# Mapping of normalized names (for comparison) to standardized names (for storing)
# for each corresponding country code
STATES = {
    "es": {
        "andalucia": "Andalucía",
        "aragon": "Aragón",
        "asturias": "Asturias",
        "baleares": "Baleares",
        "canarias": "Canarias",
        "cantabria": "Cantabria",
        "castilla la mancha": "Castilla-La Mancha",
        "castilla y leon": "Castilla y León",
        "cataluna": "Cataluña",
        "ceuta": "Ceuta",
        "comunidad valenciana": "Comunidad Valenciana",
        "extremadura": "Extremadura",
        "galicia": "Galicia",
        "la rioja": "La Rioja",
        "madrid": "Comunidad de Madrid",
        "melilla": "Melilla",
        "murcia": "Murcia",
        "navarra": "Navarra",
        "pais vasco": "País Vasco",
        "euskadi": "País Vasco",  # Alias not caught by rapidfuzz
    }
}

PROVINCES = {
    "es": {
        "alava": "Álava",
        "araba": "Álava",  # Alias not caught by rapidfuzz
        "albacete": "Albacete",
        "alicante": "Alicante",
        "almeria": "Almería",
        "asturias": "Asturias",
        "avila": "Ávila",
        "badajoz": "Badajoz",
        "barcelona": "Barcelona",
        "bizkaia": "Vizcaya",
        "burgos": "Burgos",
        "caceres": "Cáceres",
        "cadiz": "Cádiz",
        "cantabria": "Cantabria",
        "castellon": "Castellón",
        "ceuta": "Ceuta",  # Considered province by opensm and/or geonames
        "ciudad real": "Ciudad Real",
        "cordoba": "Córdoba",
        "cuenca": "Cuenca",
        "gipuzkoa": "Gipuzkoa",
        "gerona": "Gerona",
        "granada": "Granada",
        "guadalajara": "Guadalajara",
        "huelva": "Huelva",
        "huesca": "Huesca",
        "islas baleares": "Islas Baleares",
        "jaen": "Jaén",
        "la coruna": "La Coruña",
        "la rioja": "La Rioja",
        "las palmas": "Las Palmas",
        "leon": "León",
        "lerida": "Lérida",
        "lugo": "Lugo",
        "madrid": "Madrid",
        "malaga": "Málaga",
        "melilla": "Melilla",  # Considered province by opensm and/or geonames
        "murcia": "Murcia",
        "navarra": "Navarra",
        "orense": "Orense",
        "palencia": "Palencia",
        "pontevedra": "Pontevedra",
        "salamanca": "Salamanca",
        "santa cruz de tenerife": "Santa Cruz de Tenerife",
        "segovia": "Segovia",
        "sevilla": "Sevilla",
        "soria": "Soria",
        "tarragona": "Tarragona",
        "teruel": "Teruel",
        "toledo": "Toledo",
        "valencia": "Valencia",
        "valladolid": "Valladolid",
        "zamora": "Zamora",
        "zaragoza": "Zaragoza",
    }
}


PROVINCE_TO_POSTCODE = {
    "es": {
        "A Coruña": "15",
        "Álava": "01",
        "Araba": "01",
        "Alacant": "03",
        "Alicante": "03",
        "Albacete": "02",
        "Almería": "04",
        "Asturias": "33",
        "Ávila": "05",
        "Badajoz": "06",
        "Baleares": "07",
        "Barcelona": "08",
        "Bizkaia": "48",
        "Burgos": "09",
        "Cáceres": "10",
        "Cádiz": "11",
        "Cantabria": "39",
        "Castelló": "12",
        "Castellón": "12",
        "Ceuta": "51",
        "Ciudad Real": "13",
        "Córdoba": "14",
        "Cuenca": "16",
        "Gerona": "17",
        "Gipuzkoa": "20",
        "Girona": "17",
        "Granada": "18",
        "Guadalajara": "19",
        "Guipúzcoa": "20",
        "Huelva": "21",
        "Huesca": "22",
        "Illes Balears": "07",
        "Jaén": "23",
        "La Coruña": "15",
        "La Rioja": "26",
        "Las Palmas": "35",
        "León": "24",
        "Lérida": "25",
        "Lleida": "25",
        "Lugo": "27",
        "Madrid": "28",
        "Málaga": "29",
        "Melilla": "52",
        "Murcia": "30",
        "Navarra": "31",
        "Orense": "32",
        "Ourense": "32",
        "Palencia": "34",
        "Pontevedra": "36",
        "Salamanca": "37",
        "Santa Cruz de Tenerife": "38",
        "Segovia": "40",
        "Sevilla": "41",
        "Soria": "42",
        "Tarragona": "43",
        "Teruel": "44",
        "Toledo": "45",
        "València": "46",
        "Valencia": "46",
        "Valladolid": "47",
        "Vizcaya": "48",
        "Zamora": "49",
        "Zaragoza": "50",
    },
    "pt": {
        "Aveiro": "3",
        "Beja": "7",
        "Braga": "4",
        "Bragança": "5",
        "Castelo Branco": "6",
        "Coimbra": "3",
        "Évora": "7",
        "Faro": "8",
        "Guarda": "6",
        "Leiria": "2",
        "Lisboa": "1",
        "Portalegre": "7",
        "Porto": "4",
        "Santarém": "2",
        "Setúbal": "2",
        "Viana do Castelo": "4",
        "Vila Real": "5",
        "Viseu": "3",
        "Açores": "9",
        "Madeira": "9",
    },
}


POSTCODE_TO_STATES = {
    "es": {
        # Andalucía
        "04": "Andalucía",
        "11": "Andalucía",
        "14": "Andalucía",
        "18": "Andalucía",
        "21": "Andalucía",
        "23": "Andalucía",
        "29": "Andalucía",
        "41": "Andalucía",
        # Aragón
        "22": "Aragón",
        "44": "Aragón",
        "50": "Aragón",
        # Asturias
        "33": "Principado de Asturias",
        # Baleares
        "07": "Islas Baleares",
        # Canarias
        "35": "Canarias",
        "38": "Canarias",
        # Cantabria
        "39": "Cantabria",
        # Castilla y León
        "05": "Castilla y León",
        "09": "Castilla y León",
        "24": "Castilla y León",
        "34": "Castilla y León",
        "37": "Castilla y León",
        "40": "Castilla y León",
        "42": "Castilla y León",
        "47": "Castilla y León",
        "49": "Castilla y León",
        # Castilla-La Mancha
        "02": "Castilla-La Mancha",
        "13": "Castilla-La Mancha",
        "16": "Castilla-La Mancha",
        "19": "Castilla-La Mancha",
        "45": "Castilla-La Mancha",
        # Cataluña
        "08": "Cataluña",
        "17": "Cataluña",
        "25": "Cataluña",
        "43": "Cataluña",
        # Comunidad Valenciana
        "03": "Comunidad Valenciana",
        "12": "Comunidad Valenciana",
        "46": "Comunidad Valenciana",
        # Extremadura
        "06": "Extremadura",
        "10": "Extremadura",
        # Galicia
        "15": "Galicia",
        "27": "Galicia",
        "32": "Galicia",
        "36": "Galicia",
        # Madrid
        "28": "Comunidad de Madrid",
        # Murcia
        "30": "Región de Murcia",
        # Navarra
        "31": "Comunidad Foral de Navarra",
        # País Vasco
        "01": "País Vasco",
        "20": "País Vasco",
        "48": "País Vasco",
        # La Rioja
        "26": "La Rioja",
        # Ciudades Autónomas
        "51": "Ceuta",
        "52": "Melilla",
    },
    "pt": {  # --- NORTE ---
        "40": "Porto",
        "41": "Porto",
        "42": "Porto",
        "43": "Porto",
        "44": "Porto",
        "45": "Aveiro",  # Concelhos do norte de Aveiro, na fronteira com Porto.
        "47": "Braga",
        "48": "Braga",  # Guimarães.
        "49": "Viana do Castelo",
        "50": "Vila Real",
        "51": "Vila Real",
        "52": "Vila Real",
        "53": "Vila Real / Bragança",  # Zona fronteiriça.
        "54": "Bragança",
        # --- CENTRO ---
        "60": "Castelo Branco",
        "61": "Castelo Branco",
        "62": "Castelo Branco",
        "63": "Guarda",
        "30": "Coimbra",
        "31": "Coimbra",
        "32": "Coimbra",
        "33": "Coimbra",
        "34": "Viseu",
        "35": "Viseu",
        "37": "Aveiro",
        "38": "Aveiro",
        "24": "Leiria",
        # --- ÁREA METROPOLITANA DE LISBOA e arredores ---
        "10": "Lisboa",
        "11": "Lisboa",
        "12": "Lisboa",
        "13": "Lisboa",
        "14": "Lisboa",
        "15": "Lisboa",
        "16": "Lisboa",
        "17": "Lisboa",
        "18": "Lisboa",
        "19": "Lisboa",
        "20": "Santarém",
        "21": "Santarém",
        "22": "Santarém",
        "23": "Santarém",  # Tomar e Torres Novas.
        "25": "Lisboa",  # Concelhos como Torres Vedras, Mafra, Alenquer.
        "26": "Lisboa",  # Concelhos como Loures, Amadora, Odivelas.
        "27": "Lisboa",  # Concelhos como Sintra, Cascais, Oeiras.
        "28": "Setúbal",
        "29": "Setúbal",
        # --- ALENTEJO ---
        "70": "Évora",
        "71": "Évora",
        "72": "Évora",
        "73": "Portalegre",
        "74": "Portalegre",
        "75": "Setúbal",  # Litoral Alentejano (Sines, Grândola), administrativamente de Setúbal.
        "76": "Beja",
        "77": "Beja",
        "78": "Beja",
        "79": "Beja",
        # --- ALGARVE ---
        "80": "Faro",
        "81": "Faro",
        "82": "Faro",
        "83": "Faro",
        "84": "Faro",
        "85": "Faro",
        "86": "Faro",
        "87": "Faro",
        "88": "Faro",
        "89": "Faro",
        # --- REGIÕES AUTÓNOMAS ---
        "90": "Madeira",
        "91": "Madeira",
        "92": "Madeira",
        "93": "Madeira",
        "95": "Açores",  # Ilha de São Miguel (Ponta Delgada).
        "96": "Açores",  # Ilha de São Miguel (Ribeira Grande) e Santa Maria.
        "97": "Açores",  # Ilha Terceira (Angra do Heroísmo).
        "98": "Açores",  # Ilhas de São Jorge, Graciosa, Faial, Pico.
        "99": "Açores",  # Ilhas de Flores e Corvo.
    },
}

_NORMALIZED_PROVINCE_CACHE = {}
for country, provinces in PROVINCE_TO_POSTCODE.items():
    # Get the original keys (e.g., "A Coruña", "Álava")
    original_keys = list(provinces.keys())

    # Create the normalized list (e.g., "a coruna", "alava")
    normalized_choices = [unidecode(p).lower() for p in original_keys]

    _NORMALIZED_PROVINCE_CACHE[country] = {
        "choices": normalized_choices,  # The list for rapidfuzz to search in
        "keys": original_keys,  # The list to find the name by index
    }

# Source: https://github.com/ariankoochak/regex-patterns-of-all-countries
COUNTRY_PARSING_RULES = {
    "es": {
        "zip_validate_pattern": re.compile(r"^\d{5}$"),
        "zip_search_pattern": re.compile(r"\b\d{5}\b"),
        "phone_validate_pattern": re.compile(r"^(\+?34)?[67]\d{8}$"),
    },
    "pt": {
        "zip_validate_pattern": re.compile(r"^\d{4}[- ]{0,1}\d{3}$|^\d{4}$"),
        "zip_search_pattern": re.compile(r"\b\d{4}[- ]?\d{3}\b|\b\d{4}\b"),
        "phone_validate_pattern": re.compile(r"^(\+?351)?9[1236]\d{7}$"),
    },
}

MADRID_DISTRICT_DIRECT_PATCH = {
    # Correcciones directas
    "Aravaca": "Moncloa-Aravaca",
    "Puerta de Hierro": "Fuencarral-El Pardo",
    "Palacio": "Centro",
    "Argüelles": "Moncloa-Aravaca",
    "Barrio de La Estación": "Latina",
    "Casa de Campo": "Moncloa-Aravaca",
    "Universidad": "Centro",
    "Valdezarza": "Moncloa-Aravaca",
    "Cortes": "Centro",
    "Barrio de la Latina": "Centro",
    "Ciudad Universitaria": "Moncloa-Aravaca",
    "Embajadores": "Centro",
    "Justicia": "Centro",
    "Sol": "Centro",
    "Barrio de los Austrias": "Centro",
}

MADRID_DISTRICT_QUARTER_PATCH = {
    # Reglas dependientes del quarter
    ("Centro", "Atocha"): "Arganzuela",
    ("Centro", "Gaztambide"): "Chamberí",
    ("Centro", "Imperial"): "Arganzuela",
    ("Centro", "Palos de Moguer"): "Arganzuela",
    ("Arganzuela", "Embajadores"): "Centro",
    ("Salamanca", "La Elipa"): "Ciudad Lineal",
    ("Salamanca", "Ventas"): "Ciudad Lineal",
    ("Tetuán", "La Paz"): "Fuencarral-El Pardo",
    ("Tetuán", "San Cristóbal"): "Villaverde",
    ("Tetuán", "Colonia de San Cristóbal"): "Villaverde",
    ("Tetuán", "Valdezarza"): "Moncloa-Aravaca",
    ("Chamberí", "Ciudad Universitaria"): "Moncloa-Aravaca",
    ("Chamberí", "Justicia"): "Centro",
    ("Chamberí", "Universidad"): "Centro",
    ("Fuencarral-El Pardo", "Castilla"): "Chamartín",
    ("Fuencarral-El Pardo", "Valdeacederas"): "Tetuán",
    ("Fuencarral-El Pardo", "Valdezarza"): "Moncloa-Aravaca",
    ("Moncloa-Aravaca", "Bellas Vistas"): "Tetuán",
    ("Moncloa-Aravaca", "Berruguete"): "Tetuán",
    ("Moncloa-Aravaca", "Campamento"): "Latina",
    ("Moncloa-Aravaca", "Gaztambide"): "Chamberí",
    ("Moncloa-Aravaca", "Lucero"): "Latina",
    ("Moncloa-Aravaca", "Valdeacederas"): "Tetuán",
    ("Moncloa-Aravaca", "Vallehermoso"): "Chamberí",
    ("Latina", "Casa de Campo"): "Moncloa-Aravaca",
    ("Villaverde", "San Fermín"): "Usera",
    ("San Blas - Canillejas", "Concepción"): "Ciudad Lineal",
    ("San Blas - Canillejas", "Quintana"): "Ciudad Lineal",
    ("Barajas", "Palomas"): "Hortaleza",
}

MADRID_QUARTER_DIRECT_PATCH = {
    "Barrio de la Latina": "Palacio",
    "Barrio de las Letras": "Cortes",
    "Barrio de los Austrias": "Palacio",
    "Colonia de San Cristóbal": "San Cristóbal",
    "Encinar de los Reyes": "Valdefuentes",
    "La Elipa": "Ventas",
    "Las Cárcavas - San Antonio": "Valdefuentes",
    "Lavapiés": "Embajadores",
    "Montecarmelo": "El Goloso",
    "Puerta de Hierro": "Ciudad Universitaria",
    "Villaverde Alto, Casco Histórico de Villaverde": "San Andrés",
    "Villaverde Bajo": "Los Rosales",
    "Virgen del Cortijo": "Valdefuentes",
    "Las Acacias": "Acacias",
}

# Cutoff score for rapidfuzz in the name standardization function
STANDARD_THRESHOLD = 40
