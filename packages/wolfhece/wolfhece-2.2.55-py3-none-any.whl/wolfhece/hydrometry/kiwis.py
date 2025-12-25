"""
Author: HECE - University of Liege, Pierre Archambeau
Date: 2024

Copyright (c) 2024 University of Liege. All rights reserved.

This script and its content are protected by copyright law. Unauthorized
copying or distribution of this file, via any medium, is strictly prohibited.
"""

from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
import requests
import pandas as pd
import logging
from os.path import join,exists
from os import mkdir
# from osgeo import ogr
# from osgeo import osr
import json
import numpy as np
from enum import Enum
from typing import Literal
import urllib.parse
from pathlib import Path

import matplotlib.pyplot as plt

"""
KIWIS WebServices command :
    getrequestinfo retrieves all available commands

    getGroupList	retrieves a list of object groups
    getSiteList	retrieves a list of sites with metadata
    getStationList	retrieves a list of stations with metadata
    getParameterList	retrieves a list of parameters available at sites and/or stations
    getParameterTypeList	retrieves the system defined parameter type list
    getCatchmentList	retrieves a list of catchments with metadata
    getCatchmentHierarchy	retrieves a hierarchical list of catchments with metadata and parent catchments
    getRiverList	retrieves a list of rivers and water objects with metadata
    getStandardRemarkTypeList	retrieves a hierarchical list of standard remark types
    getRatingCurveList	retrieves a list of rating curves
    getTimeseriesList	retrieves a list of timeseries with metadata
    getTimeseriesTypeList	retrieves a timeseries type list
    getTimeseriesValues	retrieves timeseries data
    getTimeseriesValueLayer	retrieves timeseries data as layer
    getGraphTemplateList	retrieves a list of available graph templates
    getGraph	retrieves a graph image of timeseries data
    getStationGraph	retrieves a graph image of timeseries data based on stations
    getColorClassifications	retrieves a list of WISKI color classifications
    getQualityCodes	retrieves the list of WISKI quality codes
    getReleaseStateClasses	retrieves the list of WISKI release state classes
    getTimeseriesReleaseStateList	retrieves a list of timeseries release states
    getTimeseriesEnsembleValues	retrieves a list of timeseries ensembles with values for one or more timeseries
    getTimeseriesChanges	retrieves a list of changes for a timeseries
    getTimeseriesComments	retrieves object comments/remarks
    checkValueLimit	checks value limitations for time range value requests
"""

TIMEOUT = 5

URL_SERVICE = 'https://hydrometrie.wallonie.be/services'
URL_SERVICE_WATERINFO = 'https://download.waterinfo.be/tsmdownload'
URL_SERVICE_HICWS = 'https://hicws.vlaanderen.be'

URL_SPW   = URL_SERVICE + '/KiWIS/KiWIS'
URL_WATERINFO = URL_SERVICE_WATERINFO + '/KiWIS/KiWIS'
URL_HICWS = URL_SERVICE_HICWS + '/KiWIS/KiWIS'

URL_TOKEN = URL_SERVICE + '/auth/token/'

# See : https://hicws.vlaanderen.be/Manual_for_the_use_of_webservices_HIC.pdf
class HICWS_GroupID(Enum):
    FlowRate_daily = ('Afvoer_dag', 156169)
    FlowRate_hig_res = ('Afvoer_hoge resolutie', 156170)
    FlowRate_hourly = ('Afvoer_uur', 156171)
    Astronomic_predictions_Scheldt_and_coastal_area = ('Astronomische voorspellingen reeksen Schelde en kust (LAT)', 512458)
    Astronomic_predictions_Scheldt_and_coastal_area_high_res = ('AstroAstronomische voorspellingen reeksen Schelde en kust (mTAW)', 354718)
    Astronomic_predictions_Scheldt_and_coastal_area_high_low = ('Astronomische voorspellingen Hoog-en laagwaters Schelde en kust (LAT)', 515316)
    Astronomic_predictions_Scheldt_and_coastal_area_high_low_highres = ('Astronomische voorspellingen Hoog-en laagwaters Schelde en kust (mTAW)', 350099)
    Calculated_Discharge_important = ('Berekende afvoeren sleutellocaties waterwegen', 260592)
    Calculated_Area_Precipitation = ('Berekende gebiedsneerslagen belangrijke meetlocaties HIC', 156159)
    Chlorophyl_high_res = ('Chlorofyl_hoge resolutie', 156172)
    Conductivity_high_res = ('Conductiviteit_hoge resolutie', 156173)
    Precipitation_daily = ('Neerslag_dag', 156166)
    Precipitation_high_res = ('Neerslag_hoge resolutie', 156167)
    Precipitation_yearly = ('Neerslag_jaar', 156191)
    Precipitation_monthly = ('Neerslag_maand', 156190)
    Precipitation_hourly = ('Neerslag_uur', 156168)
    Salinity_high_res = ('Saliniteit_hoge resolutie', 421208)
    Sediment_Concentration = ('Sedimentconcentratie_hoge resolutie', 156188)
    Flow_Direction_high_res = ('Stroomrichting_hoge resolutie', 156158)
    Flow_Velocity = ('Stroomsnelheid_hoge resolutie', 156199)
    Turbidity = ('Turbiditeit_hoge resolutie', 156202)
    Tidal_Previsions_Scheldt_ensemble = ('Verwachtingen Tijgebied Schelde (HWLW)', 432821)
    Forecast_Discharge_shortterm_48h = ('Voorspellingen afvoer korte termijn (48u)', 506057)
    Forecast_Discharge_longterm_10d = ('Voorspellingen afvoer lange termijn (10 dagen)', 506059)
    Forecast_area_48h = ('Voorspellingen berekende gebiedsneerslagen belangrijke meetlocaties HIC korte termijn (48u)', 506060)
    Forecast_area_10d = ('Voorspellingen berekende gebiedsneerslagen belangrijke meetlocaties HIC lange termijn (10 dagen)', 506061)
    Forecast_waterlevel_48h = ('Voorspellingen waterstand korte termijn (48u)', 506056)
    Forecast_waterlevel_10d = ('Voorspellingen waterstand lange termijn (10 dagen)', 506058)
    Water_Level_daily = ('Waterstand_dag', 156162)
    Water_Level_high_res = ('Waterstand_hoge resolutie', 156163)
    High_Low_water_Scheldt = ('Waterstand_Hoog-en laagwaters tijgebied Schelde', 156165)
    Scheldt_High_Water = ('Waterstand_Hoogwaters tijgebied', 510205)
    Scheldt_Low_Water = ('Waterstand_Laagwaters tijgebied', 510207)
    Water_Level_hourly = ('Waterstand_uur', 156164)
    Water_Temperature = ('Watertemperatuur_hoge resolutie', 156200)
    Oxygen_Concentration = ('Zuurstofgehalte_hoge resolutie', 156207)
    Oxygen_Saturation = ('Zuurstofverzadiging_hoge resolutie', 156208)
    pH = ('Zuurtegraad_hoge resolutie', 156197)

#See : https://waterinfo.vlaanderen.be/download/9f5ee0c9-dafa-46de-958b-7cac46eb8c23?dl=0
class WaterInfo_GroupdID(Enum):
    Flowrate_15m = ('Afvoer_15m', 192786)
    Flowrate_daily = ('Afvoer_dag', 192893)
    Flowrate_yearly = ('Afvoer_jaar', 192895)
    Flowrate_monthly = ('Afvoer_maand', 192894)
    Flowrate_hourly = ('Afvoer_uur', 192892)
    Ground_Saturation = ('Bodemverzadiging_15m', 192929)
    Ground_Humidity = ('Bodemvocht_15m', 192928)
    Dew_Point_Temparature = ('Dauwpunttemperatuur_15m', 192923)
    Salinity = ('EC verziltingsmeetnet', 383065)
    projectmetingen = ('EC projectmetingen', 381863)
    Ground_Temperature = ('Grondtemperatuur_15m', 192924)
    Ground_Heat = ('Grondwarmte_15m', 192916)
    Radiation = ('Instraling_15m', 192920)
    Atmospheric_Pressure = ('Luchtdruk_15m', 192918)
    Atmospheric_Temperature = ('Luchttemperatuur175cm_15m', 192922)
    Rain_15m = ('Neerslag_15m', 192896)
    Rain_1m = ('Neerslag_1m', 199792)
    Rain_daily = ('Neerslag_dag', 192898)
    Rain_yearly = ('Neerslag_jaar', 192900)
    Rain_monthly = ('Neerslag_maand', 192899)
    Rain_hourly = ('Neerslag_uur', 192897)
    Relative_Humidity = ('RelatVocht_15m', 192919)
    Evaporation_Monteih_15m = ('VerdampingMonteith_15m', 192927)
    Evaporation_Monteih_daily = ('VerdampingMonteith_dag', 295480)
    Evaporation_Monteih_yearly = ('VerdampingMonteith_jaar', 295483)
    Evaporation_Monteih_monthly = ('VerdampingMonteith_maand', 295482)
    Evaporation_Penman_15m = ('VerdampingPenman_15m', 204341)
    Evaporation_Penman_daily = ('VerdampingPenman_dag', 295474)
    Evaporation_Penman_yearly = ('VerdampingPenman_jaar', 295479)
    Evaporation_Penman_monthly = ('VerdampingPenman_maand', 295475)
    Water_speed_15m = ('Watersnelheid_15m', 192901)
    Water_speed_daily = ('Watersnelheid_dag', 192903)
    Water_speed_yearly = ('Watersnelheid_jaar', 192905)
    Water_speed_monthly = ('Watersnelheid_maand', 192904)
    Water_speed_hourly = ('Watersnelheid_uur', 192902)
    Water_Level_15m = ('Waterstand_15m', 192780)
    Water_Level_daily = ('Waterstand_dag', 192782)
    Water_Level_yearly = ('Waterstand_jaar', 192784)
    Water_Level_monthly = ('Waterstand_maand', 192783)
    Water_Level_hourly = ('Waterstand_uur', 192785)
    Water_Temperature = ('Watertemperatuur_15m', 325066)
    Wind_Direction = ('Windrichting_15m', 192926)
    Wind_Speed = ('Windsnelheid_15m', 192925)

class kiwis_command(Enum):
    getrequestinfo = "getrequestinfo"
    getGroupList = "getGroupList"
    getSiteList = "getSiteList"
    getStationList = "getStationList"
    getParameterList = "getParameterList"
    getParameterTypeList = "getParameterTypeList"
    getCatchmentList = "getCatchmentList"
    getCatchmentHierarchy = "getCatchmentHierarchy"
    getRiverList = "getRiverList"
    getStandardRemarkTypeList = "getStandardRemarkTypeList"
    getRatingCurveList = "getRatingCurveList"
    getTimeseriesList = "getTimeseriesList"
    getTimeseriesTypeList = "getTimeseriesTypeList"
    getTimeseriesValues = "getTimeseriesValues"
    getTimeseriesValueLayer = "getTimeseriesValueLayer"
    getGraphTemplateList = "getGraphTemplateList"
    getGraph = "getGraph"
    getStationGraph = "getStationGraph"
    getColorClassifications = "getColorClassifications"
    getQualityCodes = "getQualityCodes"
    getReleaseStateClasses = "getReleaseStateClasses"
    getTimeseriesReleaseStateList = "getTimeseriesReleaseStateList"
    getTimeseriesEnsembleValues = "getTimeseriesEnsembleValues"
    getTimeseriesChanges = "getTimeseriesChanges"
    getTimeseriesComments = "getTimeseriesComments"
    checkValueLimit = "checkValueLimit"

class kiwis_request_info(Enum):
    Request = "Request"
    Description = "Description"
    QueryFields = "QueryFields"
    Formats = "Formats"
    Returnfields = "Returnfields"
    OptionalFields = "Optionalfields"
    Subdescription = "Subdescription"
    Dateformats = "Dateformats"
    Transformations= "Transformations"

class kiwis_token(Enum):
    ACCESS_TOKEN_KEY = 'access_token'
    TOKEN_TYPE = 'token_type'
    EXPIRES_IN = 'expires_in'

class kiwis_maintainers(Enum):
    DGH = 'DGH'
    DCENN = 'DCENN'
    EUPEN = 'EUP'

class kiwis_site_fields(Enum):
    site_no = 'site_no'
    site_name = 'site_name'
    site_id = 'site_id'

KIWIS_GROUP_TS = {'rain': \
                    {'highres': {'name': 'DGH-TS-Export-Pluie5min', 'id': 1332286 }, \
                    '5min': {'name': 'DGH-TS-Export-Pluie5min', 'id': 1332286 }, \
                    '1h': {'name': 'DGH-TS-Export-PluieHoraire', 'id': 5716546 }, \
                    '1d': {'name': 'DGH-TS-Export-PluieJourn', 'id': 5728245 }, \
                    '1m': {'name': 'DGH-TS-Export-PluieMensuelle', 'id': 7254396 }}, \
               'flowrate': \
                    {'highres': {'name': 'SPW-WS-DebitHR', 'id': 7256917 }, \
                    '5or10min': {'name': 'SPW-WS-DebitHR', 'id': 7256917 }, \
                    '1h': {'name': 'SPW-WS-DebitHoraire', 'id': 7256918 }, \
                    '1d': {'name': 'SPW-WS-DebitJourn', 'id': 7256919 }, \
                    '1m': {'name': 'SPW-WS-DebitMensuel', 'id': 7256920 }}, \
               'waterdepth': \
                    {'highres': {'name': 'SPW-WS-HauteurHR', 'id': 7255523 }, \
                    '5or10min': {'name': 'SPW-WS-HauteurHR', 'id': 7255523 }, \
                    '1h': {'name': 'SPW-WS-HauteurHoraire', 'id': 7255522 }, \
                    '1d': {'name': 'SPW-WS-HauteurJourn', 'id': 7255151 }, \
                    '1m': {'name': 'SPW-WS-HauteurMensuelle', 'id': 7255524 }} \
                }

KIWIS_GROUP_TS_WATERINFO = {'rain': \
                    {'highres': {'name': WaterInfo_GroupdID.Rain_1m.name, 'id': WaterInfo_GroupdID.Rain_1m.value[1] }, \
                    '1min': {'name': WaterInfo_GroupdID.Rain_1m.name, 'id': WaterInfo_GroupdID.Rain_1m.value[1] }, \
                    '15min': {'name': WaterInfo_GroupdID.Rain_15m.name, 'id': WaterInfo_GroupdID.Rain_15m.value[1] }, \
                    '1h': {'name': WaterInfo_GroupdID.Rain_hourly.name, 'id': WaterInfo_GroupdID.Rain_hourly.value[1] }, \
                    '1d': {'name': WaterInfo_GroupdID.Rain_daily.name, 'id': WaterInfo_GroupdID.Rain_daily.value[1] }, \
                    '1m': {'name': WaterInfo_GroupdID.Rain_monthly.name, 'id': WaterInfo_GroupdID.Rain_monthly.value[1] }}, \
               'flowrate': \
                    {'highres': {'name': WaterInfo_GroupdID.Flowrate_15m.name, 'id': WaterInfo_GroupdID.Flowrate_15m.value[1] }, \
                    '15min': {'name': WaterInfo_GroupdID.Flowrate_15m.name, 'id': WaterInfo_GroupdID.Flowrate_15m.value[1] }, \
                    '1h': {'name': WaterInfo_GroupdID.Flowrate_hourly.name, 'id': WaterInfo_GroupdID.Flowrate_hourly.value[1] }, \
                    '1d': {'name': WaterInfo_GroupdID.Flowrate_daily.name, 'id': WaterInfo_GroupdID.Flowrate_daily.value[1] }, \
                    '1m': {'name': WaterInfo_GroupdID.Flowrate_monthly.name, 'id': WaterInfo_GroupdID.Flowrate_monthly.value[1] }}, \
               'waterdepth': \
                    {'highres': {'name': WaterInfo_GroupdID.Water_Level_15m.name, 'id': WaterInfo_GroupdID.Water_Level_15m.value[1] }, \
                    '15min': {'name': WaterInfo_GroupdID.Water_Level_15m.name, 'id': WaterInfo_GroupdID.Water_Level_15m.value[1] }, \
                    '1h': {'name': WaterInfo_GroupdID.Water_Level_hourly.name, 'id': WaterInfo_GroupdID.Water_Level_hourly.value[1] }, \
                    '1d': {'name': WaterInfo_GroupdID.Water_Level_daily.name, 'id': WaterInfo_GroupdID.Water_Level_daily.value[1] }, \
                    '1m': {'name': WaterInfo_GroupdID.Water_Level_monthly.name, 'id': WaterInfo_GroupdID.Water_Level_monthly.value[1] }} \
                }

KIWIS_GROUP_TS_HIC = {'rain': \
                    {'highres': {'name': HICWS_GroupID.Precipitation_high_res.name, 'id': HICWS_GroupID.Precipitation_high_res.value[1] }, \
                    '1h': {'name': HICWS_GroupID.Precipitation_hourly.name, 'id': HICWS_GroupID.Precipitation_hourly.value[1] }, \
                    '1m': {'name': HICWS_GroupID.Precipitation_monthly.name, 'id': HICWS_GroupID.Precipitation_monthly.value[1] }}, \
               'flowrate': \
                    {'highres': {'name': HICWS_GroupID.FlowRate_hig_res.name, 'id': HICWS_GroupID.FlowRate_hig_res.value[1] }, \
                    '1h': {'name': HICWS_GroupID.FlowRate_hourly.name, 'id': HICWS_GroupID.FlowRate_hourly.value[1] }, \
                    '1d': {'name': HICWS_GroupID.FlowRate_daily.name, 'id': HICWS_GroupID.FlowRate_daily.value[1] }}, \
               'waterdepth': \
                    {'highres': {'name': HICWS_GroupID.Water_Level_high_res.name, 'id': HICWS_GroupID.Water_Level_high_res.value[1] }, \
                    '1h': {'name': HICWS_GroupID.Water_Level_hourly.name, 'id': HICWS_GroupID.Water_Level_hourly.value[1] }, \
                    '1d': {'name': HICWS_GroupID.Water_Level_daily.name, 'id': HICWS_GroupID.Water_Level_daily.value[1] }} \
                }


class kiwis_keywords_horq(Enum):
    V5_10MIN    = 'complet'
    V1H         = '1h.moyen'
    VDAY        = 'jour.moyen'
    VMONTH      = 'mois.moyen'
    VMAXAN      = 'an.maximum'
    VMAXANHYD   = 'anHydro.maximum'
    VMINANHYD   = 'anHydro.minimum'

class kiwis_keywords_rain(Enum):
    V5_10MIN    = 'production'
    V1H         = '1h.total'
    VDAY        = 'jour.total'
    VMONTH      = 'mois.total'
    VMAXAN      = 'an.maximum'
    VMAXANHYD   = 'anHydro.maximum'
    VMINANHYD   = 'AnHydro.minimum'

class kiwis_default_q(Enum):
    Q_FULL      = '05-Debit.Complet'
    Q_1H        = '10-Debit.1h.Moyen'
    Q_1H_Ultra  = '10-Debit ultrason.1h.Moyen'

    def __str__(self):
        return self.value

class kiwis_default_h(Enum):
    H_FULL      = '05-Hauteur.Complet'
    H_1H        = '10-Hauteur.1h.Moyen'
    H_1J        = '20-Hauteur.Jour.Moyen'
    Z_1H        = '10-Hauteur_absolue.1h.Moyen'

    def __str__(self):
        return self.value

class kiwis_default_rain(Enum):
    R_FULL      = '05-Precipitation.Complete'
    R_PROD      = '02b-Precipitation.5min.Production'
    R_1H        = '10-Precipitation.1h.Total'
    R_1J        = '20-Precipitation.Jour.Total'
    R_1M        = '40-Precipitation.Mois.Total'

    def __str__(self):
        return self.value

class kiwis_default_rain_Waterinfo(Enum):
    R_FULL      = 'P.1'
    R_10        = 'P.10'
    R_5         = 'P.5'
    R_15        = 'P.15'
    R_1H        = 'P.60'
    R_1J        = 'DagTotaal'
    R_1M        = 'MaandTotaal'

    def __str__(self):
        return self.value

class kiwis_default_rain_HIC(Enum):
    R_FULL      = 'Base'
    R_15        = '15Tot'
    R_1H        = '60Tot'
    R_1J        = 'DagTot'
    R_1M        = 'MaandTot'

    def __str__(self):
        return self.value


"""
Code qualité    Validation  Qualité
40              Oui         Mesure ou calcul de qualité standard
80              Oui         Données estimées / corrigées : données fausses ou
                            manquantes qui ont pu être corrigées ou complétées de
                            manière satisfaisante.
120             Oui         Données estimées / corrigées : données fausses ou
                            manquantes qui ont été corrigées ou complétées mais
                            restent suspectes ou de faible qualité.
160             Oui         Données suspectes ou de faible qualité mais non modifiées.
200             Non         Données brutes
205/210         Non         Données de qualité suspecte (contrôle automatique) ou en
                            cours d'analyse à à ne pas utiliser
255 / -1 -                  Données manquantes
"""
class quality_code(Enum):
    # Validated
    STANDARD        = (40, 'blue', '')
    ESTIMATED_OK    = (80, 'green', '+')
    ESTIMATED_DOUBT = (120, 'orange', '>')
    # Not validated
    DOUBT           = (160, 'orange', '*')
    RAW             = (200, 'gray', '.')
    BAD             = (205, 'red', 'o')
    BAD2            = (210, 'red', 'x')
    VOID            = (255, 'black', '.')
    VOID2           = (-1, 'black', '.')

class station_fields(Enum):
    STATION_ID = 'station_id'
    STATION_NO = 'station_no'
    STATION_NAME = 'station_name'
    STATION_LOCAL_X = 'station_local_x'
    STATION_LOCAL_Y = 'station_local_y'
    STATION_LATITUDE = 'station_latitude'
    STATION_LONGITUDE = 'station_longitude'
    RIVER_NAME = 'river_name'

class timeseries_fields(Enum):
    TS_ID = 'ts_id'
    TS_NAME = 'ts_name'
    TS_UNITNAME = 'ts_unitname'
    TS_UNITSYMBOL ='ts_unitsymbol'

class hydrometry():

    def __init__(self, url:str=URL_SPW, urltoken:str=URL_TOKEN, credential ='', dir='') -> None:
        """Initialisation sur base d'un URL de service KIWIS
        et recherche des sites et stations disponibles
        """
        self.url = url
        self.urltoken = urltoken
        self.dir = dir
        self.credential = credential

        self.groups = None
        self.stations = None
        self.sites = None
        self.requests = None

        self.idx = 'hydrometry'
        self.plotted = False

        self.mystations = None # only for HECE

        if url=='':
            self.url=URL_SPW

            # check if url is responding
            try:
                requests.get(self.url, timeout=TIMEOUT)
            except requests.exceptions.RequestException as e:
                logging.error(f"Error connecting to {self.url}: {e}")
                return

        if urltoken=='':
            self.urltoken=URL_TOKEN

        try:
            self.daily_token()
        except Exception as e:
            logging.warning('No token available or Error in hydrometry init :', e)

        try:
            self.get_requests()
            self.get_sites()
            self.get_stations()
            self.get_groups()
            self.save_struct()
        except Exception as e:
            logging.error('Error in hydrometry init :', e)
            self.realstations = None
            pass

    def __str__(self) -> str:
        ret='Columns in stations :\n'
        for curcol in self.realstations.columns:
            ret+=curcol+'\n'
        return ret

    def _get_commandstr(self, which:str, format='json'):
        """ Construction de la commande à envoyer au serveur KIWIS """

        datasource = ''
        if self.url == URL_WATERINFO:
            datasource = '&datasource=1'
        elif self.url == URL_HICWS:
            datasource = '&datasource=4'

        return self.url+'?request='+which.value+'&format='+format + datasource

    def daily_token(self, timeout:int =5):
        """
        Get daily token to be identified on hydrometry website

        #FIXME: better manage error as response
        """

        if self.credential == '':
            self._header = None
            return

        today = 'token_'+datetime.now().strftime('%Y%m%d')+'.json'

        if exists(today):
            with open(today, 'r') as f:
                self.token = json.load(f)
        else:
            headers = {'Authorization' : 'Basic {}'.format(self.credential)}
            data = {'grant_type' :'client_credentials'}

            try:
                self.token = requests.post(self.urltoken,
                                           data=data,
                                           headers=headers,
                                           timeout=timeout).json()

                if 'error' in self.token:
                    self.token = None
                    self._header = {'Authorization': 'Bearer '}
                    return

                with open(today, 'w') as f:
                    json.dump(self.token, f)
            except:
                self._header = {'Authorization': 'Bearer '}
                self.token = {'access_token': 0}
                with open(today, 'w') as f:
                    json.dump(self.token, f)
                return

        try:
            self._header = {'Authorization': 'Bearer {}'.format(self.token['access_token'])}
        except Exception as e:
            logging.error('Error in daily_token :', e)
            self._header = None

    def check_plot(self):
        """ Instance is checked in mapviewer """
        self.plotted = True

    def uncheck_plot(self):
        """ Instance is unchecked in mapviewer """
        self.plotted = False

    def get_path(self, dir:Path, filename:str):
        """ Get path of instance """
        return Path(dir) / (self.url.replace('/','_').replace('https:','') + filename)

    def save_struct(self, dir=''):
        """Sauvegarde des structures dans un répertoire

        :param dir: répertoire de sauvegarde
        """

        if dir=='':
            if self.dir:
                dir = self.dir
            else:
                logging.warning('No directory to save structure')
                return

        dir = Path(dir)
        dir.mkdir(parents=True, exist_ok=True)

        self.sites.to_csv(self.get_path(dir, 'sites.csv'))
        self.stations.to_csv(self.get_path(dir, 'stations.csv'))
        self.groups.to_csv(self.get_path(dir, 'groups.csv'))
        self.requests.to_csv(self.get_path(dir, 'requests.csv'))

    def _get_stations_pythonlist(self, site_no:str|int, onlyreal:bool= True, return_only_name:bool=False):
        """ Obtention des stations pour le site en liste python

        :param site_no: numéro du site
        :param onlyreal: ne prendre que les stations réelles, pas les calculées
        """

        if onlyreal:
            stations = self.realstations[self.realstations[kiwis_site_fields.site_no.value]==site_no]
        else:
            stations = self.stations[self.stations[kiwis_site_fields.site_no.value]==site_no]

        if return_only_name:
            return [curname for curname in stations[station_fields.STATION_NAME.value].values]

        else:
            list_name_code = [curname+' --- '+curno   for curname,curno in zip(stations[station_fields.STATION_NAME.value].values,stations[station_fields.STATION_NO.value].values)]
            list_code_name = [curno  +' --- '+curname for curname,curno in zip(stations[station_fields.STATION_NAME.value].values,stations[station_fields.STATION_NO.value].values)]

            return list_name_code, list_code_name

    def _get_sites_pythonlist(self):
        """ Obtention des sites en liste python """
        if self.sites is None:
            logging.warning('No sites available - Please check the hydrometry instance')
            return []

        list_name_code = [curname+' --- '+curno  for curname,curno in zip(self.sites[kiwis_site_fields.site_name.value].values,self.sites[kiwis_site_fields.site_no.value].values)]
        return list_name_code

    def get_stations(self):
        """Obtention des stations pour le serveur courant.

        Une requête sur le serveur KIWIS retourne les informations pour toutes les stations.
        Une séparation entre station réelle et station calculée est ensuite effectuée:
            - self.realstations
            - self.compstations

        Champs des stations :
            - site_no : numéro du site ; le site correspond au réseau de mesure : DGH pour les stations du SPW-MI et DCENN pour les stations du SPW-ARNE ;
            - station_no, station_name : code et nom de la station ;
            - station_local_x, station_local_y : coordonnées de la station en Lambert belge 1972 ;
            - station_latitude,station_longitude : coordonnées de la station en ETRS89 ;
            - river_name : nom de la rivière, cette information n’est disponible que pour les stations de mesure de hauteur d’eau et de débits, les pluviomètres ne sont pas installés sur une rivière – il n’y a donc pas de nom de rivière associé ;
            - parametertype_name : type de paramètre ;
            - ts_id, ts_name : code et nom de la chronique ;
            - ts_unitname, ts_unitsymbol : nom et symbole de l’unité de mesure ;
            - ca_sta&ca_sta_returnfields=BV_DCE : nom du bassin versant principal suivi de son abréviation (2 lettres)
        """

        returnfields = f'{kiwis_site_fields.site_no.value},'
        returnfields += f'{station_fields.STATION_NO.value},{station_fields.STATION_NAME.value},{station_fields.STATION_ID.value},'
        returnfields += f'{station_fields.STATION_LOCAL_X.value},{station_fields.STATION_LOCAL_Y.value},' if self.url==URL_SPW else ''
        returnfields += f'{station_fields.STATION_LATITUDE.value},{station_fields.STATION_LONGITUDE.value},'
        returnfields += f'{station_fields.RIVER_NAME.value},'
        returnfields += 'ca_sta'

        ca_sta_returnfields = 'station_gauge_datum,'
        ca_sta_returnfields += 'CATCHMENT_SIZE,'
        ca_sta_returnfields += 'BV_DCE'
        # returnfields += 'parametertype_name,'
        # returnfields += 'ts_id,ts_name,'
        # returnfields += 'ts_unitname,ts_unitsymbol,'

        if self.dir!='' and self.get_path(self.dir,'stations.csv').exists():
            self.stations = pd.read_csv(self.get_path(self.dir, 'stations.csv'),index_col=0)
        elif self.url!='':
            try:
                if self.url == URL_SPW:
                    json_data = requests.get(self._get_commandstr(kiwis_command.getStationList) \
                                            +'&metadata=true' \
                                            +'&returnfields='+returnfields \
                                            +'&ca_sta_returnfields='+ca_sta_returnfields \
                                            +'&orderby=station_no', \
                                            verify=True, \
                                            headers=self._header,
                                            timeout=TIMEOUT).json()
                else:
                    json_data = requests.get(self._get_commandstr(kiwis_command.getStationList, 'json') \
                                            +'&metadata=true' \
                                            +'&returnfields='+returnfields \
                                            +'&orderby=station_no', \
                                            verify=True, \
                                            headers=self._header,
                                            timeout=TIMEOUT)

                    json_data = json_data.text.replace('\x1a', ' ')
                    json_data = json.loads(json_data)

            except Exception as e:
                self.stations = None
                return

            self.stations = pd.DataFrame(json_data[1:], columns = json_data[0])

        #Conversion en minuscules
        self.stations[station_fields.STATION_NAME.value]=self.stations[station_fields.STATION_NAME.value].str.lower()

        # # In case of Waterinfo, get part of station_id
        # if self.url == URL_WATERINFO:
        #     self.stations[station_fields.STATION_ID.value] = self.stations[station_fields.STATION_ID.value].str[2:]

        if self.url == URL_SPW:
            # real stations are those with coordinates and not null
            self.realstations = self.stations[(~pd.isnull(self.stations[station_fields.STATION_LOCAL_X.value])) & (self.stations[station_fields.STATION_LOCAL_X.value]!='')]
            # computed stations are those without coordinates or null
            self.compstations = self.stations[pd.isnull(self.stations[station_fields.STATION_LOCAL_X.value]) | self.stations[station_fields.STATION_LOCAL_X.value]!='']
        else:
            self.realstations = self.stations
            self.compstations = None

    def get_names_xy(self, site_no = None):
        """Obtention des noms et coordonnées des stations pour le site

        :param site_no: numéro du site
        """

        if site_no is None:
            stations_r = self.realstations
            # stations_c = self.compstations
        else:
            stations_r = self.realstations[self.realstations[kiwis_site_fields.site_no.value]==site_no]
            # stations_c = self.compstations[self.stations[kiwis_site_fields.site_no.value]==site_no]

        if stations_r is None:
            return ([],[],[])
        else:
            return ([curname + ' - ' + str(curid) for curname, curid in zip(stations_r[station_fields.STATION_NAME.value].values,
                                                                            stations_r[station_fields.STATION_NO.value].values)],
                    stations_r[station_fields.STATION_LOCAL_X.value].values,
                    stations_r[station_fields.STATION_LOCAL_Y.value].values)

    def get_names_latlon(self, site_no = None):
        """ Obtention des noms et coordonnées des stations pour le site

        :param site_no: numéro du site
        """

        if site_no is None:
            stations_r = self.realstations
            # stations_c = self.compstations
        else:
            stations_r = self.realstations[self.realstations[kiwis_site_fields.site_no.value]==site_no]
            # stations_c = self.compstations[self.stations[kiwis_site_fields.site_no.value]==site_no]

        if stations_r is None:
            return ([],[],[])
        else:
            return ([curname + ' - ' + str(curid) for curname, curid in zip(stations_r[station_fields.STATION_NAME.value].values,
                                                                            stations_r[station_fields.STATION_ID.value].values)],
                    stations_r[station_fields.STATION_LATITUDE.value].values,
                    stations_r[station_fields.STATION_LONGITUDE.value].values)


    def select_inside(self, xll:float, yll:float, xur:float, yur:float, tolist=False):
        """
        Recherche les stations dans une zone rectangulaire

        :param xll: X lower left - Lambert 72
        :param yll: Y lower left - Lambert 72
        :param xur: X upper right - Lambert 72
        :param yur: Y upper right - Lambert 72
        :param tolist: retourne une liste de noms et codes de stations et nom un dataframe

        :return: liste de noms et codes de stations ou dataframe
        """

        if xll>xur:
            tmpx=xll
            xll=xur
            xur=tmpx
        if yll>yur:
            tmpy=yll
            yll=yur
            yur=tmpy

        df = self.realstations[(self.realstations[station_fields.STATION_LOCAL_X.value].to_numpy(dtype=np.float64)>=xll) & (self.realstations[station_fields.STATION_LOCAL_X.value].to_numpy(dtype=np.float64)<=xur) & \
            (self.realstations[station_fields.STATION_LOCAL_Y.value].to_numpy(dtype=np.float64)>=yll) & (self.realstations[station_fields.STATION_LOCAL_Y.value].to_numpy(dtype=np.float64)<=yur)]
        if tolist:
            list_name_code = [curname+' --- '+curno  for curname,curno in zip(df[station_fields.STATION_NAME.value].values,df[station_fields.STATION_NO.value].values)]
            return list_name_code
        else:
            return df

    def select_inside_latlon(self, lonll:float, latll:float, lonur:float, latur:float, tolist=False):
        """
        Recherche les stations dans une zone rectangulaire

        :param lonll: Longitude lower left - WGS84
        :param latll: Latitude lower left - WGS84
        :param lonur: Longitude upper right - WGS84
        :param latur: Latitude upper right - WGS84
        :param tolist: retourne une liste de noms et codes de stations et nom un dataframe

        :return: liste de noms et codes de stations ou dataframe
        """

        if lonll>lonur:
            tmpx=lonll
            lonll=lonur
            lonur=tmpx
        if latll>latur:
            tmpy=latll
            latll=latur
            latur=tmpy

        df = self.realstations[(self.realstations[station_fields.STATION_LONGITUDE.value].to_numpy(dtype=np.float64)>=lonll) & (self.realstations[station_fields.STATION_LONGITUDE.value].to_numpy(dtype=np.float64)<=lonur) & \
            (self.realstations[station_fields.STATION_LATITUDE.value].to_numpy(dtype=np.float64)>=latll) & (self.realstations[station_fields.STATION_LATITUDE.value].to_numpy(dtype=np.float64)<=latur)]
        if tolist:
            list_name_code = [curname+' --- '+curno  for curname,curno in zip(df[station_fields.STATION_NAME.value].values,df[station_fields.STATION_NO.value].values)]
            return list_name_code
        else:
            return df

    def sort_nearests(self, x:float, y:float):
        """
        Trie les stations en fonction de la distance et retourne un index trié

        :param x: coordonnée x - Lambert 72
        :param y: coordonnée y - Lambert 72
        """
        dist = np.asarray([(float(cur[station_fields.STATION_LOCAL_X.value]) - x)**2 + (float(cur[station_fields.STATION_LOCAL_Y.value]) - y)**2 for idx,cur in self.realstations.iterrows()])
        index = np.arange(len(dist))[dist.argsort()]

        return index

    def sort_nearests_latlon(self, lon:float, lat:float):
        """
        Trie les stations en fonction de la distance et retourne un index trié

        :param lon: longitude - WGS84
        :param lat: latitude - WGS84
        """
        dist = np.asarray([(float(cur[station_fields.STATION_LATITUDE.value]) - lat)**2 + (float(cur[station_fields.STATION_LONGITUDE.value]) - lon)**2 for idx,cur in self.realstations.iterrows()])
        index = np.arange(len(dist))[dist.argsort()]

        return index

    def find_nearest(self, x:float, y:float, tolist=False):
        """
        Trouve la station la plus proche

        :param x: coordonnée x - Lambert 72
        :param y: coordonnée y - Lambert 72
        """
        index = self.sort_nearests(x,y)

        if tolist:
            return [self.realstations.iloc[index[0]][station_fields.STATION_NAME.value]+' --- '+self.realstations.iloc[index[0]][station_fields.STATION_NO.value]]
        else:
            return self.realstations.iloc[index[0]]

    def find_nearest_latlon(self, lon:float, lat:float, tolist=False):
        """
        Trouve la station la plus proche

        :param lon: longitude - WGS84
        :param lat: latitude - WGS84
        """

        index = self.sort_nearests_latlon(lon,lat)

        if tolist:
            return [self.realstations.iloc[index[0]][station_fields.STATION_NAME.value]+' --- '+self.realstations.iloc[index[0]][station_fields.STATION_NO.value]]
        else:
            return self.realstations.iloc[index[0]]

    def get_timeseries_group(self, rfw:Literal['rain','waterdepth','flowrate'], time:Literal['highres','5min','5or10min','15min','1h','1d','1m']):
        """Obtention des stations pour le groupe souhaité.

        Temps retourné en UTC

        :param rfw: type de groupe - rain, flowrate, waterdepth
        :param time: type de série - 5min, 5or10min, 1h, 1d, 1m
        """

        if self.url!='':
            stations=None

            if self.url == URL_SPW:
                locdict = KIWIS_GROUP_TS
                returnFields = ''
            elif self.url == URL_WATERINFO:
                locdict = KIWIS_GROUP_TS_WATERINFO
                returnFields = '&metadata=true&custattr_returnfields=dataprovider,dataowner&md_returnfields=custom_attributes,station_id,station_no,station_name,ts_id,ts_name,stationparameter_name,ts_unitsymbol,parametertype_name'
            elif self.url == URL_HICWS:
                locdict = KIWIS_GROUP_TS_HIC
                returnFields = '&metadata=true&custattr_returnfields=dataprovider,dataowner&md_returnfields=custom_attributes,station_id,station_no,station_name,ts_id,ts_name,stationparameter_name,ts_unitsymbol,parametertype_name'

            if rfw in locdict.keys():
                if time in locdict[rfw].keys():
                    group_id = locdict[rfw][time]['id']
                    json_data = requests.get(self._get_commandstr(kiwis_command.getTimeseriesList) +
                                             '&timeseriesgroup_id='+str(group_id)+
                                             '&orderby=station_no'+
                                             returnFields,
                                             verify=True,
                                             headers=self._header,
                                             timeout=TIMEOUT).json()
                    stations = pd.DataFrame(json_data[1:], columns = json_data[0])
                else:
                    logging.error(f'{time} not found in Enum')

            return stations

    def get_timeseries_group_spw(self, rfw:Literal['rain','waterdepth','flowrate'], time:Literal['5min','5or10min','1h','1d','1m']):
        """alias for get_timeseries_group"""

        return self.get_timeseries_group(rfw, time)

    def get_timeseries_group_winfo_hic(self, group:WaterInfo_GroupdID | HICWS_GroupID):
        """Obtention des stations pour le groupe souhaité.

        Temps retourné en UTC

        :param group: type de groupe - see WaterInfo_GroupdID or HICWS_GroupID
        """

        if self.url!='':
            stations=None
            group_id = group.value[1]
            returnFields = '&metadata=true&custattr_returnfields=dataprovider,dataowner&md_returnfields=custom_attributes,station_id,station_no,station_name,ts_id,ts_name,stationparameter_name,ts_unitsymbol,parametertype_name'
            # json_data = requests.get(self._get_commandstr(kiwis_command.getTimeseriesValueLayer) +
            json_data = requests.get(self._get_commandstr(kiwis_command.getTimeseriesList) +
                                     '&timeseriesgroup_id='+str(group_id)+
                                     '&orderby=station_no'+
                                     returnFields,
                                     verify=True,
                                     headers=self._header,
                                     timeout=TIMEOUT).json()

            stations = pd.DataFrame(json_data[1:], columns = json_data[0])

            return stations

    def get_sites(self, forcerequest=False):
        """Obtention des sites pour le serveur courant

        :param forcerequest: force la requête même si les données de cache sont déjà présentes"""

        if self.dir!='' and self.get_path(self.dir, 'sites.csv').exists() and not forcerequest:
            self.sites = pd.read_csv(self.get_path(self.dir, 'sites.csv'),index_col=0)
        elif self.url!='' or forcerequest:
            json_data = requests.get(self._get_commandstr(kiwis_command.getSiteList),
                                     verify=True,
                                     headers=self._header,
                                     timeout=TIMEOUT).json()

            self.sites = pd.DataFrame(json_data[1:], columns = json_data[0])
        else:
            self.sites = None

    def get_groups(self, forcerequest=False):
        """Obtention des groupes pour le serveur courant

        :param forcerequest: force la requête même si les données de cache sont déjà présentes"""

        if self.dir!='' and self.get_path(self.dir, 'groups.csv').exists() and not forcerequest:
            self.groups = pd.read_csv(self.get_path(self.dir, 'groups.csv'),index_col=0)
        elif self.url!='' or forcerequest:
            json_data = requests.get(self._get_commandstr(kiwis_command.getGroupList),
                                     verify=True,
                                     headers=self._header,
                                     timeout=TIMEOUT).json()
            self.groups = pd.DataFrame(json_data[1:], columns = json_data[0])
        else:
            self.groups = None

    # def get_ratingcurves(self):
    #     """Obtention des courbes de tarage pour le serveur courant"""
    #     if self.dir!='':
    #         self.ratingcurves = pd.read_csv(join(self.dir,'ratingcurves.csv'),index_col=0)
    #     elif self.url!='':
    #         json_data = requests.get(self.url+'?request=getRatingCurveList&datasource=0&format=json',verify=True).json()
    #         self.ratingcurves = pd.DataFrame(json_data[1:], columns = json_data[0])

    def get_requests(self, forcerequest=False):
        """Obtention des requêtes possibles pour le serveur courant

        :param forcerequest: force la requête même si les données de cache sont déjà présentes"""

        if self.dir!='' and self.get_path(self.dir, 'requests.csv').exists() and not forcerequest:
            self.requests = pd.read_csv(self.get_path(self.dir, 'requests.csv'),index_col=0)
        elif self.url!='' or forcerequest:
            json_data = requests.get(self._get_commandstr(kiwis_command.getrequestinfo),
                                     verify=True,
                                     headers=self._header,
                                     timeout=TIMEOUT).json()

            self.requests = pd.DataFrame(json_data[0]['Requests'])
        else:
            self.requests = None

    def print_requestinfo(self, which:kiwis_command):
        """ Affichage des informations pour une requête donnée

        :param which: requête à afficher"""

        if self.requests is None:
            self.get_requests()

        if which.value in self.requests.keys():
            myrequest = self.requests[which.value]

            for cur in kiwis_request_info:
                print(myrequest[cur.value])

    def timeseries_list(self, stationname:str = '', stationcode:str = ''):
        """Récupération de la liste des TimeSeries pour l'id d'une station
        soit via le nom de la station, soit via le code de la station.

        :param stationname: nom de la station
        :param stationcode: code de la station
        """

        if stationname!='':
            id=self.get_stationid(stationname)
        elif stationcode!='':
            id=self.get_stationid(code=stationcode)

        try:
            json_data = requests.get(self._get_commandstr(kiwis_command.getTimeseriesList)
                                    +'&station_id='+str(id)
                                    +'&format=json'
                                    ,verify=True,
                                    headers=self._header,
                                    timeout=TIMEOUT).json()
        except requests.exceptions.RequestException as e:
            logging.error(f"Error fetching timeseries list: {e}")
            return id, None

        try:
            if json_data[0] == 'No matches.':
                return id, None

            return id, pd.DataFrame(json_data[1:], columns = json_data[0])
        except Exception as e:
            logging.error('Error in timeseries_list :', e)
            return id, None

    def save_all_lists(self, dir:str):
        """Sauveragde des listes pour toutes les stations

        :param dir: répertoire de sauvegarde"""

        for curstation in self.stations[station_fields.STATION_NO.value]:
            self.save_list(stationcode=curstation, dir=dir)

    def _get_filename_list(self, stationname:str='', stationcode:str=''):
        """retourne un nom de fichier avec la station et le code

        Utile car dans certains noms de la BDD KIWIS il y a un caractère '/' qui ne peut être utilisé comme nom de fichier
        Il est remplacé par '-'
        """
        if stationname=='':
            stationname = self.get_stationname(stationcode)

        if stationcode=='':
            stationcode = self.get_stationcode(stationname)

        id = self.get_stationid(stationname,stationcode)

        return stationname.replace('/','-') + '_' + stationcode + '_' + str(id) + '.csv'

    def _get_filename_series(self,stationname:str='',stationcode:str='',
                             which:kiwis_default_q | kiwis_default_h | kiwis_keywords_horq | kiwis_default_rain = kiwis_default_q.Q_FULL):
        """retourne un nom de fichier avec la station et le code et le type de données

        Utile car dans certains noms de la BDD KIWIS il y a un caractère '/' qui ne peut être utilisé comme nom de fichier
        Il est remplacé par '-'
        """
        if stationname=='':
            stationname = self.get_stationname(stationcode)

        if stationcode=='':
            stationcode = self.get_stationcode(stationname)

        id = self.get_stationid(stationname,stationcode)

        return stationname.replace('/','-') + '_' + stationcode + '_' + str(id) + '_' + which.value + '.csv'

    def save_list(self, stationname:str = '', stationcode:str = '', dir:str = ''):
        """Sauvegarde de la liste des des timeseries dans un fichier

        :param stationname: nom de la station
        :param stationcode: code de la station
        :param dir: répertoire de sauvegarde"""

        dir = Path(dir)
        if not dir.exists():
            dir.mkdir(parents=True, exist_ok=True)

        id,list=self.timeseries_list(stationname=stationname,stationcode=stationcode)
        filename = self._get_filename_list(stationname,stationcode)
        list.to_csv(self.get_path(dir,filename))

    def timeseries(self, stationname:str='', stationcode:str='', stationid:str='',
                   dir:str='',
                   fromdate=datetime.now()-timedelta(60), todate=datetime.now(),
                   ts_name:str='', ts_id:str='', interval:int=3600, timezone:str = 'GMT+0'):
        """
        Récupération des valeurs d'une TimeSerie
          - sur base des dates
          - soit en donnant :
            - le nom de la station ou le code ET le nom de la timeserie --> dans ce cas, la routine commence par retrouver l'id de la ts
            - directement l'id de la timeserie

        :param stationname: nom de la station
        :param stationcode: code de la station
        :param dir: répertoire de sauvegarde
        :param fromdate: date de début
        :param todate: date de fin
        :param ts_name: nom de la timeserie
        :param ts_id: id de la timeserie
        :param interval: intervalle de temps
        :param timezone: timezone

        """

        ts_name = str(ts_name)

        if timezone=='Europe/Brussels' or timezone=='local':
            timezone=''

        nb = int((todate - fromdate).days*24 * (3600/interval))
        cursec = interval
        # id = ''
        if ts_id == '':
            if str(stationid) !='':
                id = stationid
            else:
                if stationname=='':
                    stationname = self.get_stationname(stationcode)
                if stationcode=='':
                    stationcode = self.get_stationcode(stationname)
                id = self.get_stationid(stationname,stationcode)

            if dir=='':
                json_data = requests.get(self._get_commandstr(kiwis_command.getTimeseriesList)
                                        +"&"+urllib.parse.urlencode({
                                        "station_id":str(id),
                                        "ts_name":ts_name,
                                        "timezone":timezone})
                                        ,verify=True,
                                        timeout=TIMEOUT).json()
                if len(json_data)==1:
                    return None

                elif len(json_data)>2:
                    logging.warning('More than one timeseries found for station {0} with name {1}'.format(stationname,ts_name))
                    logging.warning('We are using the first one - Please check if it is the right one')

                ts_id = str(int(pd.DataFrame(json_data[1:], columns = json_data[0])[timeseries_fields.TS_ID.value].iloc[0]))
            else:
                filename = self._get_filename_list(stationname,stationcode)
                curlist=pd.read_csv(join(dir,filename),index_col=0)
                ts_id = str(int(curlist.loc(curlist[timeseries_fields.TS_NAME.value==ts_name])[timeseries_fields.TS_ID.value]))

            if "1h" in ts_name or "60" in ts_name:
                nb = (todate - fromdate).days*24
                cursec = 3600
            elif "5min" in ts_name:
                nb = (todate - fromdate).days*24*12
                cursec = 300
            elif "15" in ts_name:
                nb = (todate - fromdate).days*24*4
                cursec = 300
            elif "10min" in ts_name:
                nb = (todate - fromdate).days*24*6
                cursec = 600
            elif "2min" in ts_name:
                nb = (todate - fromdate).days*24*30
                cursec = 120
            elif "1min" in ts_name:
                nb = (todate - fromdate).days*24*60
                cursec = 120
            elif "jour" in ts_name or "day in ts_name":
                nb = (todate - fromdate).days*24
                cursec = 24*3600
            elif "mois" in ts_name or "month" in ts_name:
                nb = (todate - fromdate).days/30
                cursec = 24*30*3600

        if nb>250000:
            curfrom = fromdate
            curend = curfrom+timedelta(seconds=200000 * cursec)
            locts=[]
            while curfrom<todate:
                logging.info('Getting data from {0} to {1}'.format(curfrom, curend))
                tmpts = self.timeseries(stationname, stationcode, dir = dir, fromdate= curfrom, todate= curend, ts_name= ts_name, ts_id= ts_id, timezone=timezone)

                if isinstance(tmpts, pd.Series):
                    if len(tmpts)>0:
                        locts.append(tmpts)

                curfrom = curend
                curend = curfrom+timedelta(seconds=200000 * cursec)
                if curend>todate:
                    curend=todate

            if len(locts)==0:
                logging.warning('No data found for timeseries {0} for station {1} ({2}) between {3} and {4}'.format(ts_name, stationname, stationcode, fromdate, todate))
                return pd.DataFrame()

            return pd.concat(locts)
        else:
            try:
                json_data = requests.get(self._get_commandstr(kiwis_command.getTimeseriesValues)
                                        +"&"+urllib.parse.urlencode({
                                        "ts_id":str(ts_id),
                                        "from":fromdate.strftime("%Y-%m-%dT%H:%M:%S"),
                                        "to":todate.strftime("%Y-%m-%dT%H:%M:%S"),
                                        # "format":"json",
                                        "timezone":timezone})
                                        ,verify=True,
                                        headers=self._header,
                                        timeout=TIMEOUT).json()

                df = pd.DataFrame(json_data[0]['data'], columns = json_data[0]['columns'].split(','))
                df.set_index('Timestamp', inplace = True)
                df.index = pd.to_datetime(df.index,format="%Y-%m-%dT%H:%M:%S.%f%z")

            except Exception as e:
                logging.error('Error in timeseries ! - Check if the server is responding.')
                return pd.DataFrame()

        return df.squeeze()

    def timeseries_qc(self, stationname:str='', stationcode:str='', dir:str='',
                      fromdate=datetime.now()-timedelta(60), todate=datetime.now(),
                      ts_name:str='', ts_id:str='', interval:int=3600, timezone:str = 'GMT+0'):
        """
        Récupération des quality code d'une TimeSerie
          - sur base des dates
          - soit en donnant :
            - le nom de la station ou le code ET le nom de la timeserie --> dans ce cas, la routine commence par retrouver l'id de la ts
            - directement l'id de la timeserie

        :param stationname: nom de la station
        :param stationcode: code de la station
        :param dir: répertoire de sauvegarde
        :param fromdate: date de début
        :param todate: date de fin
        :param ts_name: nom de la timeserie
        :param ts_id: id de la timeserie
        :param interval: intervalle de temps
        :param timezone: timezone

        """
        if timezone=='Europe/Brussels' or timezone=='local':
            timezone=''

        nb = (todate - fromdate).days*24 * (3600/interval)
        cursec = interval
        # id = ''
        if ts_id == '':
            if stationname=='':
                stationname = self.get_stationname(stationcode)
            if stationcode=='':
                stationcode = self.get_stationcode(stationname)
            id = self.get_stationid(stationname,stationcode)

            if dir=='':
                json_data = requests.get(self._get_commandstr(kiwis_command.getTimeseriesList)
                                        +"&"+urllib.parse.urlencode({
                                        "station_id":str(id),
                                        "ts_name":ts_name,
                                        "timezone":timezone})+
                                        "&returnfields=Timestamp,Quality%20Code"
                                        ,verify=True,
                                        timeout=TIMEOUT).json()
                if len(json_data)==1:
                    return None

                ts_id = str(int(pd.DataFrame(json_data[1:], columns = json_data[0])[timeseries_fields.TS_ID.value].iloc[0]))
            else:
                filename = self._get_filename_list(stationname,stationcode)
                curlist=pd.read_csv(join(dir,filename),index_col=0)
                ts_id = str(int(curlist.loc(curlist[timeseries_fields.TS_NAME.value==ts_name])[timeseries_fields.TS_ID.value]))

            if "1h" in ts_name:
                nb = (todate - fromdate).days*24
                cursec = 3600
            elif "5min" in ts_name:
                nb = (todate - fromdate).days*24*12
                cursec = 300
            elif "10min" in ts_name:
                nb = (todate - fromdate).days*24*6
                cursec = 600
            elif "2min" in ts_name:
                nb = (todate - fromdate).days*24*30
                cursec = 120
            elif "jour" in ts_name:
                nb = (todate - fromdate).days*24
                cursec = 24*3600
            elif "mois" in ts_name:
                nb = (todate - fromdate).days/30
                cursec = 24*30*3600

        if nb>250000:
            curfrom = fromdate
            curend = curfrom+timedelta(seconds=200000 * cursec)
            locts=[]
            while curfrom<todate:
                logging.info('Getting data from {0} to {1}'.format(curfrom, curend))
                locts.append(self.timeseries(stationname,stationcode, dir = dir, fromdate= curfrom, todate= curend, ts_name= ts_name, ts_id= ts_id))
                curfrom = curend
                curend = curfrom+timedelta(seconds=200000 * cursec)
                if curend>todate:
                    curend=todate

            return pd.concat(locts)
        else:
            json_data = requests.get(self._get_commandstr(kiwis_command.getTimeseriesValues)
                                    +"&"+urllib.parse.urlencode({
                                    "ts_id":str(ts_id),
                                    "from":fromdate.strftime("%Y-%m-%dT%H:%M:%S"),
                                    "to":todate.strftime("%Y-%m-%dT%H:%M:%S"),
                                    "timezone":timezone})+
                                    "&returnfields=Timestamp,Quality%20Code"
                                    ,verify=True,
                                    headers=self._header,
                                    timeout=TIMEOUT).json()

            df = pd.DataFrame(json_data[0]['data'], columns = json_data[0]['columns'].split(','))
            df.set_index('Timestamp', inplace = True)
            df.index = pd.to_datetime(df.index,format="%Y-%m-%dT%H:%M:%S.%f%z")

        return df.squeeze()

    def fromcsv(self, dir:str='spw', stationname:str='', stationcode:str='',
                which:kiwis_default_q | kiwis_default_h | kiwis_keywords_horq | kiwis_default_rain = kiwis_default_q.Q_FULL,
                fromdate:datetime=None, todate:datetime=None):
        """
        Lecture depuis un fichier csv créé depuis un import précédent.
        Les fichiers doivent être disponibles depuis un sous-répertoire spw.

        :param dir: répertoire de sauvegarde
        :param stationname: nom de la station
        :param stationcode: code de la station
        :param which: type de données
        :param fromdate: date de début
        :param todate: date de fin

        """
        filename=self._get_filename_series(stationname,stationcode,which)

        dir = Path(dir)
        filename = dir / filename

        if filename.exists():
            mydata= pd.read_csv(filename,header=0,index_col=0,parse_dates=True,engine='pyarrow').squeeze("columns")
        else:
            return

        if fromdate is None and todate is None:
            return mydata
        elif fromdate is None:
            return mydata[:todate]
        elif todate is None:
            return mydata[fromdate:]
        else:
            return mydata[fromdate:todate]

    def saveas(self, flow:pd.Series, dir:str, stationname='', stationcode='',
               which:kiwis_default_q | kiwis_default_h | kiwis_keywords_horq | kiwis_default_rain = kiwis_default_q.Q_FULL):
        """Sauvegarde d'une series pandas dans un fichier .csv

        :param flow: série pandas
        :param dir: répertoire de sauvegarde
        :param stationname: nom de la station
        :param stationcode: code de la station
        :param which: type de données
        """

        filename=self._get_filename_series(stationname,stationcode,which.value)

        dir = Path(dir)
        filename = dir / filename

        flow.to_csv(filename,header=['Data'], date_format="%Y-%m-%dT%H:%M:%S.%f%z")

    def get_stationid(self, name:str='', code:str='') -> int:
        """Récupération de l'id sur base du nom ou du code

        :param name: nom de la station
        :param code: code de la station"""

        if name!='':
            return int(self.stations.loc[self.stations[station_fields.STATION_NAME.value]==name.lower()][station_fields.STATION_ID.value].iloc[0])
        elif code!='':
            return int(self.stations.loc[self.stations[station_fields.STATION_NO.value]==code][station_fields.STATION_ID.value].iloc[0])
        else:
            return None

    def get_gauge_datum(self,name:str='',code:str=''):
        """Récupération de l'altitude de référence sur base du nom ou du code

        :param name: nom de la station
        :param code: code de la station"""

        try:
            if name!='':
                return self.stations.loc[self.stations[station_fields.STATION_NAME.value]==name.lower()]['station_gauge_datum'].iloc[0]
            elif code!='':
                return self.stations.loc[self.stations[station_fields.STATION_NO.value]==code]['station_gauge_datum'].iloc[0]
            else:
                return None
        except:
            return None

    def get_catchment_size(self,name:str='',code:str=''):
        """Récupération de la surface du BV de référence sur base du nom ou du code

        :param name: nom de la station
        :param code: code de la station"""

        try:
            if name!='':
                return self.stations.loc[self.stations[station_fields.STATION_NAME.value]==name.lower()]['CATCHMENT_SIZE'].iloc[0]
            elif code!='':
                return self.stations.loc[self.stations[station_fields.STATION_NO.value]==code]['CATCHMENT_SIZE'].iloc[0]
            else:
                return None
        except:
            return None

    def get_bv_dce(self,name:str='',code:str=''):
        """Récupération du nom de BV au sens de la DCE "Directive Cadre Eau" sur base du nom ou du code

        :param name: nom de la station
        :param code: code de la station"""

        try:
            if name!='':
                return self.stations.loc[self.stations[station_fields.STATION_NAME.value]==name.lower()]['BV_DCE'].iloc[0]
            elif code!='':
                return self.stations.loc[self.stations[station_fields.STATION_NO.value]==code]['BV_DCE'].iloc[0]
            else:
                return None
        except:
            return None

    def get_stationcode(self,name:str=''):
        """Récupération du code sur base du nom

        :param name: nom de la station
        """

        if name!='':
            return self.stations.loc[self.stations[station_fields.STATION_NAME.value]==name.lower()][station_fields.STATION_NO.value].squeeze()
        else:
            return None

    def get_stationname(self,code:str=''):
        """Récupération du nom sur base du code

        :param code: code de la station"""

        if code!='':
            return self.stations.loc[self.stations[station_fields.STATION_NO.value]==code][station_fields.STATION_NAME.value].squeeze()
        else:
            return None

    def get_siteid(self,name:str='',code:str=''):
        """Récupération de l'id sur base du nom ou du code

        :param name: nom de la station
        :param code: code de la station"""

        if name!='':
            return int(self.sites.loc[self.sites[kiwis_site_fields.site_name.value]==name.lower()][kiwis_site_fields.site_id.value])
        elif code!='':
            return int(self.sites.loc[self.sites[kiwis_site_fields.site_no.value]==code][kiwis_site_fields.site_id.value])
        else:
            return None

    def get_sitecode(self, name:str=''):
        """Récupération du code sur base du nom

        :param name: nom de la station"""

        if name!='':
            return self.sites.loc[self.sites[kiwis_site_fields.site_name.value]==name.lower()][kiwis_site_fields.site_no.value].squeeze()
        else:
            return None

    def get_sitename(self,code:str=''):
        """Récupération du nom sur base du code

        :param code: code de la station"""

        if code!='':
            return self.sites.loc[self.sites[kiwis_site_fields.site_no.value]==code][kiwis_site_fields.site_name.value].squeeze()
        else:
            return None
