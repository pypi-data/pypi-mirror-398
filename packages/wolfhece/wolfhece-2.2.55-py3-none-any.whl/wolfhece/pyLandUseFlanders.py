import numpy as np
import logging
from pathlib import Path
from enum import Enum

from osgeo import gdal, osr

from .wolf_array import WolfArray

class Legend_LU_Flanders_NL(Enum):
    """
    Enum for Legend Land Use Flanders
    """
    HUIZEN_EN_TUINEN = {"color": "#ff0000", "quantity": 1, "label": "Huizen en tuinen"}
    INDUSTRIE = {"color": "#8400a8", "quantity": 2, "label": "Industrie"}
    COMMERCIELE_DOELEINDEN = {"color": "#ff00c5", "quantity": 3, "label": "Commerciële doeleinden"}
    DIENSTEN = {"color": "#002673", "quantity": 4, "label": "Diensten"}
    TRANSPORTINFRASTRUCTUUR = {"color": "#686868", "quantity": 5, "label": "Transportinfrastructuur"}
    RECREATIE = {"color": "#ffaa00", "quantity": 6, "label": "Recreatie"}
    LANDBOUWGEBOUWEN_EN_INFRASTRUCTUUR = {"color": "#a87000", "quantity": 7, "label": "Landbouwgebouwen en -infrastructuur"}
    OVERIGE_BEBOWDE_TERREINEN = {"color": "#cccccc", "quantity": 8, "label": "Overige bebouwde terreinen"}
    OVERIGE_ONBEBOWDE_TERREINEN = {"color": "#828282", "quantity": 9, "label": "Overige onbebouwde terreinen"}
    ACTIEVE_GROEVES = {"color": "#dfe6a9", "quantity": 10, "label": "Actieve groeves"}
    LUCHTHAVENS = {"color": "#df73ff", "quantity": 11, "label": "Luchthavens"}
    BOS = {"color": "#267300", "quantity": 12, "label": "Bos"}
    AKKER = {"color": "#ffffbe", "quantity": 13, "label": "Akker"}
    GRASLAND_IN_LANDBOUWGEBRUIK = {"color": "#a3ff73", "quantity": 14, "label": "Grasland in landbouwgebruik"}
    STRUIKGEWAS = {"color": "#897044", "quantity": 15, "label": "Struikgewas"}
    BRAAKLIGGEND_EN_DUINEN = {"color": "#ffd37f", "quantity": 16, "label": "Braakliggend en duinen"}
    WATER = {"color": "#005ce6", "quantity": 17, "label": "Water"}
    MOERAS = {"color": "#00a884", "quantity": 18, "label": "Moeras"}
    OVERIGE_GRASLANDEN = {"color": "#82ca5b", "quantity": 19, "label": "Overige graslanden"}

class Legend_LU_Flanders_EN(Enum):
    """
    Enum for Legend Land Use Flanders in English
    """
    HOUSES_AND_GARDENS = {"color": "#ff0000", "quantity": 1, "label": "Houses and gardens"}
    INDUSTRY = {"color": "#8400a8", "quantity": 2, "label": "Industry"}
    COMMERCIAL_PURPOSES = {"color": "#ff00c5", "quantity": 3, "label": "Commercial purposes"}
    SERVICES = {"color": "#002673", "quantity": 4, "label": "Services"}
    TRANSPORT_INFRASTRUCTURE = {"color": "#686868", "quantity": 5, "label": "Transport infrastructure"}
    RECREATION = {"color": "#ffaa00", "quantity": 6, "label": "Recreation"}
    AGRICULTURAL_BUILDINGS_AND_INFRASTRUCTURE = {"color": "#a87000", "quantity": 7, "label": "Agricultural buildings and infrastructure"}
    OTHER_BUILT_UP_LAND = {"color": "#cccccc", "quantity": 8, "label": "Other built-up land"}
    OTHER_UNBUILT_LAND = {"color": "#828282", "quantity": 9, "label": "Other unbuilt land"}
    ACTIVE_QUARRIES = {"color": "#dfe6a9", "quantity": 10, "label": "Active quarries"}
    AIRPORTS = {"color": "#df73ff", "quantity": 11, "label": "Airports"}
    FOREST = {"color": "#267300", "quantity": 12, "label": "Forest"}
    CROP_LAND = {"color": "#ffffbe", "quantity": 13, "label": "Crop land"}
    GRASSLAND_IN_AGRICULTURAL_USE = {"color": "#a3ff73", "quantity": 14, "label": "Grassland in agricultural use"}
    SHRUB_LAND = {"color": "#897044", "quantity": 15, "label": "Shrub land"}
    FALLOW_AND_DUNES = {"color": "#ffd37f", "quantity": 16, "label": "Fallow and dunes"}
    WATER = {"color": "#005ce6", "quantity": 17, "label": "Water"}
    MARSHLAND = {"color": "#00a884", "quantity": 18, "label": "Marshland"}
    OTHER_GRASSLANDS = {"color": "#82ca5b", "quantity": 19, "label": "Other grasslands"}

class Legend_LU_Flanders_FR(Enum):
    """ 
    Enum for Legend Land Use Flanders in French
    """
    MAISONS_ET_JARDINS = {"color": "#ff0000", "quantity": 1, "label": "Maisons et jardins"}
    INDUSTRIE = {"color": "#8400a8", "quantity": 2, "label": "Industrie"}
    USAGES_COMMERCIAUX = {"color": "#ff00c5", "quantity": 3, "label": "Usages commerciaux"}
    SERVICES = {"color": "#002673", "quantity": 4, "label": "Services"}
    INFRASTRUCTURE_DE_TRANSPORT = {"color": "#686868", "quantity": 5, "label": "Infrastructure de transport"}
    LOISIRS = {"color": "#ffaa00", "quantity": 6, "label": "Loisirs"}
    BÂTIMENTS_AGRICOLES_ET_INFRASTRUCTURE = {"color": "#a87000", "quantity": 7, "label": "Bâtiments agricoles et infrastructure"}
    AUTRES_TERRAINS_BÂTIS = {"color": "#cccccc", "quantity": 8, "label": "Autres terrains bâtis"}
    AUTRES_TERRAINS_NON_BÂTIS = {"color": "#828282", "quantity": 9, "label": "Autres terrains non bâtis"}
    CARRIÈRES_ACTIVES = {"color": "#dfe6a9", "quantity": 10, "label": "Carrières actives"}
    AÉROPORTS = {"color": "#df73ff", "quantity": 11, "label": "Aéroports"}
    FORÊT = {"color": "#267300", "quantity": 12, "label": "Forêt"}
    CULTURES = {"color": "#ffffbe", "quantity": 13, "label": "Cultures"}
    PRAIRIES_EN_UTILISATION_AGRICOLE = {"color": "#a3ff73", "quantity": 14, "label": "Prairies en utilisation agricole"}
    LANDES_ARBUSTIVES = {"color": "#897044", "quantity": 15, "label": "Landes arbustives"}
    TERRES_EN_FRICHE_ET_DUNES = {"color": "#ffd37f", "quantity": 16, "label": "Terres en friche et dunes"}
    EAU = {"color": "#005ce6", "quantity": 17, "label": "Eau"}
    MARAIS = {"color": "#00a884", "quantity": 18, "label": "Marais"}
    AUTRES_TERRAINS_ENHERBES = {"color": "#82ca5b", "quantity": 19, "label": "Autres terrains enherbés"}

FLANDERS_OCS_COLORMAP = {
    1.: (255,0,0,255), # Maisons et jardins,
    2.: (132,0,168,255), # Industrie
    3.: (255,0,197,255), # Usages commerciaux
    4.: (0,38,115,255), # Services
    5.: (104,104,104,255), # Infrastructure de transport
    6.: (255,170,0,255), # Loisirs
    7.: (168,112,0,255), # Bâtiments agricoles et infrastructure
    8.: (204,204,204,255), # Autres terrains bâtis
    9.: (130,130,130,255), # Autres terrains non bâtis
    10.: (223,230,169,255), # Carrières actives 
    11.: (223,115,255,255), # Aéroports
    12.: (38,115,0,255), # Forêt    
    13.: (255,255,190,255), # Cultures
    14.: (163,255,115,255), # Prairies en utilisation agricole
    15.: (137,112,68,255), # Landes arbustives
    16.: (255,211,127,255), # Terres en friche et dunes
    17.: (0,92,230,255), # Eau
    18.: (0,168,132,255), # Marais
    19.: (130,202,91,255), # Autres terrains enherbés
    }

MAPPING_FLANDERS_TO_WALOUS = {
    1.: 11., # Maisons et jardins -> Construction artificielles hors sol
    2.: 11., # Industrie -> Revêtement artificiels au sol
    3.: 9., # Usages commerciaux -> Revêtement artificiels au sol
    4.: 9., # Services -> Revêtement artificiels au sol
    5.: 10., # Infrastructure de transport -> Réseau ferroviaire
    6.: 9., # Loisirs -> Revêtement artificiels au sol
    7.: 9., # Bâtiments agricoles et infrastructure -> Revêtement artificiels au sol
    8.: 9., # Autres terrains bâtis -> Revêtement artificiels au sol
    9.: 7., # Autres terrains non bâtis -> Sols nus
    10.: 7., # Carrières actives -> Sols nus
    11.: 8., # Aéroports -> Revêtement artificiels au sol
    12.: 4., # Forêt -> Feuillus (> 3m)
    13.: 1., # Cultures -> Couvert herbacé en rotation dans l'année
    14.: 1., # Prairies en utilisation agricole -> Couvert herbacé en rotation dans l'année
    15.: 6., # Landes arbustives -> Feuillus (<= 3m)
    16.: 7., # Terres en friche et dunes -> Sols nus
    17.: 8., # Eau -> Eaux de surface
    18.: 8., # Marais -> Eaux de surface
    19.: 2., # Autres terrains enherbés -> Couvert herbacé toute l'année
}

MAPPING_FLANDERS_TO_HYDROLOGY = {
    1.: 4., # Maisons et jardins -> Pavés/urbain
    2.: 4., # Industrie -> Pavés/urbain
    3.: 4., # Usages commerciaux -> Pavés/urbain
    4.: 4., # Services -> Pavés/urbain
    5.: 4., # Infrastructure de transport -> Pavés/urbain
    6.: 4., # Loisirs -> Pavés/urbain
    7.: 4., # Bâtiments agricoles et infrastructure -> Pavés/urbain
    8.: 4., # Autres terrains bâtis -> Pavés/urbain
    9.: 3., # Autres terrains non bâtis -> Culture
    10.: 3., # Carrières actives -> Culture
    11.: 4., # Aéroports -> Pavés/urbain
    12.: 1., # Forêt -> Forêt
    13.: 3., # Cultures -> Culture
    14.: 3., # Prairies en utilisation agricole -> Culture
    15.: 3., # Landes arbustives -> Culture
    16.: 3., # Terres en friche et dunes -> Culture
    17.: 6., # Eau -> Plan d'eau
    18.: 6., # Marais -> Plan d'eau
    19.: 2., # Autres terrains enherbés -> Prairie
}
