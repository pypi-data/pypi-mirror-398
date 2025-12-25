"""
Author: HECE - University of Liege, Pierre Archambeau
Date: 2024

Copyright (c) 2024 University of Liege. All rights reserved.

This script and its content are protected by copyright law. Unauthorized
copying or distribution of this file, via any medium, is strictly prohibited.
"""

from owslib.wms import WebMapService
from PIL import Image
from io import BytesIO
import pyproj
import urllib.parse as ul
import wx
import logging
from typing import Union, Literal
from enum import Enum
from datetime import datetime, timedelta

try:
    from .PyTranslate import _
except:
    from wolfhece.PyTranslate import _

def to_image(mybytes:BytesIO) -> Image:
    return Image.open(mybytes)

def getWalonmap(cat:Literal['IMAGERIE/ORTHO_2021', 'ALEA', 'CADMAP', 'LIDAXES', '$IDW', 'EAU/ZONES_INONDEES'],
                xl:float,
                yl:float,
                xr:float,
                yr:float,
                w:int = None,
                h:int = None,
                tofile=True) -> BytesIO:

    if cat.find('$')>0:
        catloc=cat[:cat.find('$')]
    elif cat.find('_wo_alea')>0:
        catloc=cat[:cat.find('_wo_alea')]
    else:
        catloc=cat

    try:
        wms=WebMapService('https://geoservices.wallonie.be/arcgis/services/'
                        + catloc+'/MapServer/WMSServer',version='1.3.0', timeout=5)
    except:
        try:
            wms=WebMapService('https://eservices.minfin.fgov.be/arcgis/services/'
                            + catloc+'/MapServer/WMSServer',version='1.3.0')
            # wms=WebMapService('http://ccff02.minfin.fgov.be/geoservices/arcgis/services/'
            #                 + catloc+'/MapServer/WMSServer',version='1.3.0')
        except:
            logging.warning(_('Impossible to get data from web services'))
            return None

    ppkm = 300
    if w is None and h is None:
        real_w = (xr-xl)/1000
        real_h = (yr-yl)/1000
        w = int(real_w * ppkm)
        h = int(real_h * ppkm)
    elif w is None:
        real_w = (xr-xl)/1000
        real_h = (yr-yl)/1000
        ppkm = h/real_h
        w = int(real_w * ppkm)
        # h = int(real_h * ppkm)
    elif h is None:
        real_w = (xr-xl)/1000
        real_h = (yr-yl)/1000
        ppkm = w/real_w
        # w = int(real_w * ppkm)
        h = int(real_h * ppkm)

    if tofile:
        img=wms.getmap(layers=['0'],styles=['default'],srs='EPSG:31370',bbox=(xl,yl,xr,yr),size=(w,h),format='image/png',transparent=True)
        out = open('aqualim.png', 'wb')
        out.write(img.read())
        out.close()
        return None
    else:
        mycontents=list(wms.contents)
        curcont=['0']
        curstyles=['default']

        if cat.find('ALEA')>0:
            ech=(xr-xl)/w
            if ech>6.5:
                curcont=['6'] #au-dessus du 1:25000
            else:
                curcont=['5'] #en-dessous du 1:25000 et au-dessus de 1:5000
        elif cat.find('CADMAP')>0:
            curcont=['0,1']
            curstyles=['default,default']
        elif cat.find('LIMITES_ADMINISTRATIVES')>0:
            curcont=['0,1,2,3']
            curstyles=['default,default,default,default']
        elif cat.find('wms')>0:
            curcont=['1,2,3,4,5']
            curstyles=['default,default,default,default,default']
        elif cat.find('LIDAXES')>0:
            curcont=['4,5,6,7,8,9,11,13']
            curstyles=['default,default,default,default,default,default,default,default']
        elif cat.find('IDW')>0:
            curcont=['0']
            curstyles=['default']
        elif cat.find('ZONES_INONDEES')>0:

            if 'wo_alea' in cat:
                curcont = list(wms.contents)[1:]
                curstyles=['default']*len(curcont)
            else:
                curcont = list(wms.contents)
                curstyles=['default']*len(curcont)

        try:
            img=wms.getmap(layers=curcont,styles=curstyles,srs='EPSG:31370',bbox=(xl,yl,xr,yr),size=(w,h),format='image/png',transparent=True)
            return BytesIO(img.read())
        except:
            logging.warning(_('Impossible to get data from web services'))
            return None

def getVlaanderen(cat:Literal['Adpf'],
                xl:float,
                yl:float,
                xr:float,
                yr:float,
                w:int = None,
                h:int = None,
                tofile=True) -> BytesIO:

    catloc=cat

    try:
        wms=WebMapService('https://geo.api.vlaanderen.be/'
                        + catloc+'/wms',version='1.3.0', timeout=5)
    except:
        logging.warning(_('Impossible to get data from web services'))
        return None

    ppkm = 300
    if w is None and h is None:
        real_w = (xr-xl)/1000
        real_h = (yr-yl)/1000
        w = int(real_w * ppkm)
        h = int(real_h * ppkm)
    elif w is None:
        real_w = (xr-xl)/1000
        real_h = (yr-yl)/1000
        ppkm = h/real_h
        w = int(real_w * ppkm)
        # h = int(real_h * ppkm)
    elif h is None:
        real_w = (xr-xl)/1000
        real_h = (yr-yl)/1000
        ppkm = w/real_w
        # w = int(real_w * ppkm)
        h = int(real_h * ppkm)

    if tofile:
        img=wms.getmap(layers=['0'],styles=['default'],srs='EPSG:31370',bbox=(xl,yl,xr,yr),size=(w,h),format='image/png',transparent=True)
        out = open('aqualim.png', 'wb')
        out.write(img.read())
        out.close()
        return BytesIO(b'1')
    else:
        mycontents=list(wms.contents)
        curcont=['Adpf']
        curstyles=['default']

        try:
            img=wms.getmap(layers=curcont,styles=curstyles,srs='EPSG:31370',bbox=(xl,yl,xr,yr),size=(w,h),format='image/png',transparent=True)
            return BytesIO(img.read())
        except:
            logging.warning(_('Impossible to get data from web services'))
            return None


def getIGNFrance(cat:str,epsg:str,xl,yl,xr,yr,w,h,tofile=True) -> BytesIO:

    if epsg != 'EPSG:2154':
        transf=pyproj.Transformer.from_crs(epsg,'EPSG:2154')
        y1,x1=transf.transform(xl,yl)
        y2,x2=transf.transform(xr,yr)
    else:
        x1=xl
        x2=xr
        y1=yl
        y2=yr

    logging.info(_('Requesting WMS from IGN France...'))
    wms=WebMapService('https://data.geopf.fr/wms-r/wms',version='1.3.0')
    logging.info(_('WMS from IGN France obtained.'))
    assert wms is not None, _('Impossible to get data from web services')

    img=wms.getmap(layers=[cat],styles=[''],srs='EPSG:2154',bbox=(x1,y1,x2,y2),size=(w,h),format='image/png',transparent=True)

    # test response code
    if hasattr(img, 'status_code') and img.status_code != 200:
        logging.warning(_('HTTP error: ') + str(img.status_code))
        return None

    if tofile:
        out = open('ignFrance.png', 'wb')
        out.write(img.read())
        out.close()
        return None
    else:
        return BytesIO(img.read())

def getLifeWatch(cat:Literal['None'],
                xl:float,
                yl:float,
                xr:float,
                yr:float,
                w:int = None,
                h:int = None,
                tofile=True,
                format:Literal['image/png', 'image/png; mode=8bit']='image/png') -> BytesIO:

    wms=WebMapService(f'https://maps.elie.ucl.ac.be/cgi-bin/mapserv72?map=/maps_server/lifewatch/mapfiles/LW_Ecotopes/latest/{cat}.map&SERVICE=wms',
                        version='1.3.0', timeout=10)

    # _p_ixel _p_er _k_ilo_m_etre
    ppkm = 500

    if w is None and h is None:
        # Bounding dimensions width in kilometres
        real_w = (xr-xl)/1000
        real_h = (yr-yl)/1000
        # Size in pixels of the requested area.
        w = int(real_w * ppkm)
        h = int(real_h * ppkm)
    elif w is None:
        real_w = (xr-xl)/1000
        real_h = (yr-yl)/1000
        ppkm = h/real_h
        w = int(real_w * ppkm)
        # h = int(real_h * ppkm)
    elif h is None:
        real_w = (xr-xl)/1000
        real_h = (yr-yl)/1000
        ppkm = w/real_w
        # w = int(real_w * ppkm)
        h = int(real_h * ppkm)

    # If we ask for too many pixels, well, we reduce the number
    # of pixels we ask for (keeping the aspect ratio)
    MAXSIZE = 2048
    if w > MAXSIZE:
        pond = w / MAXSIZE
        w = MAXSIZE
        h = int(h / pond)
    if h > MAXSIZE:
        pond = h / MAXSIZE
        h = MAXSIZE
        w = int(w / pond)

    if tofile:
        img=wms.getmap(layers=['lc_hr_raster'],
                    #    styles=['default'],
                       srs='EPSG:31370',
                       bbox=(xl,yl,xr,yr),
                       # Width/Height of map output, in pixels.
                       # See: https://docs.geoserver.org/stable/en/user/services/wms/reference.html#getmap
                       size=(w,h),
                       format='image/png',
                       transparent=False)

        out = open('LifeWatch.png', 'wb')
        out.write(img.read())
        out.close()
        return None
    else:
        mycontents=list(wms.contents)
        curcont=['lc_hr_raster'] # 'MS
        curstyles=['1']

        try:
            img=wms.getmap(layers=curcont,
                        #    styles=curstyles,
                           srs='EPSG:31370',
                           bbox=(xl,yl,xr,yr),
                           size=(w,h),
                           format=format,
                           transparent=False)
            return BytesIO(img.read())
        except:
            logging.warning(_('Impossible to get data from web services'))
            return None

def getNGI(cat:Literal['orthoimage_coverage',
                       'orthoimage_coverage_2016',
                       'orthoimage_coverage_2017',
                       'orthoimage_coverage_2018',
                       'orthoimage_coverage_2019',
                       'orthoimage_coverage_2020',
                       'orthoimage_coverage_2021',
                       'orthoimage_coverage_2022'],
                xl:float,
                yl:float,
                xr:float,
                yr:float,
                w:int = None,
                h:int = None,
                tofile=True,
                format:Literal['image/png', 'image/GeoTIFF']='image/png') -> BytesIO:

    try:
        wms=WebMapService(f'https://wms.ngi.be/inspire/ortho/service?',
                            version='1.3.0', timeout=10)
    except:
        logging.warning(_('Impossible to get data from web services'))
        return None
    ppkm = 300
    if w is None and h is None:
        real_w = (xr-xl)/1000
        real_h = (yr-yl)/1000
        w = int(real_w * ppkm)
        h = int(real_h * ppkm)
    elif w is None:
        real_w = (xr-xl)/1000
        real_h = (yr-yl)/1000
        ppkm = h/real_h
        w = int(real_w * ppkm)
        # h = int(real_h * ppkm)
    elif h is None:
        real_w = (xr-xl)/1000
        real_h = (yr-yl)/1000
        ppkm = w/real_w
        # w = int(real_w * ppkm)
        h = int(real_h * ppkm)

    MAXSIZE = 4000
    if w > MAXSIZE:
        pond = w / MAXSIZE
        w = MAXSIZE
        h = int(h / pond)
    if h > MAXSIZE:
        pond = h / MAXSIZE
        h = MAXSIZE
        w = int(w / pond)

    if tofile:
        img=wms.getmap(layers=['lc_hr_raster'],
                    #    styles=['default'],
                       srs='EPSG:31370',
                       bbox=(xl,yl,xr,yr),
                       size=(w,h),
                       format='image/png',
                       transparent=False)

        out = open('LifeWatch.png', 'wb')
        out.write(img.read())
        out.close()
        return None
    else:
        mycontents=list(wms.contents) # List all available layers
        curcont=[cat] # 'MS
        curstyles=['1']

        # convert from EPSG:31370 to EPSG:3812
        transf=pyproj.Transformer.from_crs('EPSG:31370','EPSG:3812')
        x1,y1=transf.transform(xl,yl)
        x2,y2=transf.transform(xr,yr)

        try:
            img=wms.getmap(layers=curcont,
                        #    styles=curstyles,
                           srs='EPSG:3812',
                           bbox=(x1,y1,x2,y2),
                           size=(w,h),
                           format=format,
                           transparent=False)

            return BytesIO(img.read())

        except:
            logging.warning(_('Impossible to get data from web services'))
            return None

def getCartoweb(cat:Literal['crossborder',
                            'crossborder_grey',
                            'overlay',
                            'topo',
                            'topo_grey'],
                xl:float,
                yl:float,
                xr:float,
                yr:float,
                w:int = None,
                h:int = None,
                tofile=True,
                format:Literal['image/png', 'image/GeoTIFF']='image/png') -> BytesIO:

    wms=WebMapService(f'https://cartoweb.wms.ngi.be/service?',
                        version='1.3.0', timeout=10)

    ppkm = 300
    if w is None and h is None:
        real_w = (xr-xl)/1000
        real_h = (yr-yl)/1000
        w = int(real_w * ppkm)
        h = int(real_h * ppkm)
    elif w is None:
        real_w = (xr-xl)/1000
        real_h = (yr-yl)/1000
        ppkm = h/real_h
        w = int(real_w * ppkm)
        # h = int(real_h * ppkm)
    elif h is None:
        real_w = (xr-xl)/1000
        real_h = (yr-yl)/1000
        ppkm = w/real_w
        # w = int(real_w * ppkm)
        h = int(real_h * ppkm)

    MAXSIZE = 2000
    if w > MAXSIZE:
        pond = w / MAXSIZE
        w = MAXSIZE
        h = int(h / pond)
    if h > MAXSIZE:
        pond = h / MAXSIZE
        h = MAXSIZE
        w = int(w / pond)

    if tofile:
        img=wms.getmap(layers=['lc_hr_raster'],
                    #    styles=['default'],
                       srs='EPSG:31370',
                       bbox=(xl,yl,xr,yr),
                       size=(w,h),
                       format='image/png',
                       transparent=False)

        out = open('LifeWatch.png', 'wb')
        out.write(img.read())
        out.close()
        return None
    else:
        mycontents=list(wms.contents) # List all available layers
        curcont=[cat] # 'MS
        curstyles=['1']

        try:
            img=wms.getmap(layers=curcont,
                        #    styles=curstyles,
                           srs='EPSG:31370',
                           bbox=(xl,yl,xr,yr),
                           size=(w,h),
                           format=format,
                           transparent=True)

            return BytesIO(img.read())

        except:
            logging.warning(_('Impossible to get data from web services'))
            return None

def getOrthoPostFlood2021(cat:Literal['orthoimage_flood'],
                xl:float,
                yl:float,
                xr:float,
                yr:float,
                w:int = None,
                h:int = None,
                tofile=True,
                format:Literal['image/png', 'image/GeoTIFF']='image/png') -> BytesIO:

    wms=WebMapService(f'https://wms.ngi.be/inspire/flood_ortho/service?',
                        version='1.3.0', timeout=10)

    ppkm = 300
    if w is None and h is None:
        real_w = (xr-xl)/1000
        real_h = (yr-yl)/1000
        w = int(real_w * ppkm)
        h = int(real_h * ppkm)
    elif w is None:
        real_w = (xr-xl)/1000
        real_h = (yr-yl)/1000
        ppkm = h/real_h
        w = int(real_w * ppkm)
        # h = int(real_h * ppkm)
    elif h is None:
        real_w = (xr-xl)/1000
        real_h = (yr-yl)/1000
        ppkm = w/real_w
        # w = int(real_w * ppkm)
        h = int(real_h * ppkm)

    MAXSIZE = 4000
    if w > MAXSIZE:
        pond = w / MAXSIZE
        w = MAXSIZE
        h = int(h / pond)
    if h > MAXSIZE:
        pond = h / MAXSIZE
        h = MAXSIZE
        w = int(w / pond)

    if tofile:
        img=wms.getmap(layers=['lc_hr_raster'],
                    #    styles=['default'],
                       srs='EPSG:31370',
                       bbox=(xl,yl,xr,yr),
                       size=(w,h),
                       format='image/png',
                       transparent=False)

        out = open('LifeWatch.png', 'wb')
        out.write(img.read())
        out.close()
        return None
    else:
        mycontents=list(wms.contents) # List all available layers
        curcont=[cat] # 'MS
        curstyles=['1']

        # convert from EPSG:31370 to EPSG:3812
        transf=pyproj.Transformer.from_crs('EPSG:31370','EPSG:3812')
        x1,y1=transf.transform(xl,yl)
        x2,y2=transf.transform(xr,yr)

        try:
            img=wms.getmap(layers=curcont,
                        #    styles=curstyles,
                           srs='EPSG:3812',
                           bbox=(x1,y1,x2,y2),
                           size=(w,h),
                           format=format,
                           transparent=False)

            return BytesIO(img.read())

        except:
            logging.warning(_('Impossible to get data from web services'))
            return None

def get_Alaro_times():
    wms=WebMapService(f'https://opendata.meteo.be/service/alaro/wms?',
                        version='1.3.0', timeout=10)
    times = wms['Total_precipitation'].timepositions[0].split('/')

    return times

def get_Alaro_legend(layer:str):
    """ Get the legend of the layer

    :param layer: name of the layer
    :return: legend of the layer
    """
    import requests
    from io import BytesIO
    # layers = ['10_m_u__wind_component',
    #             '10_m_v__wind_component',
    #             '2_m_Max_temp_since_ppp',
    #             '2_m_Min_temp_since_ppp',
    #             '2_m_dewpoint_temperature',
    #             '2_m_temperature',
    #             '2m_Relative_humidity',
    #             'Convective_rain',
    #             'Convective_snow',
    #             'Geopotential',
    #             'Inst_flx_Conv_Cld_Cover',
    #             'Inst_flx_High_Cld_Cover',
    #             'Inst_flx_Low_Cld_Cover',
    #             'Inst_flx_Medium_Cld_Cover',
    #             'Inst_flx_Tot_Cld_cover',
    #             'Large_scale_rain',
    #             'Large_scale_snow',
    #             'Mean_sea_level_pressure',
    #             'Relative_humidity',
    #             'Relative_humidity_isobaric',
    #             'SBL_Meridian_gust',
    #             'SBL_Zonal_gust',
    #             'Specific_humidity',
    #             'Surf_Solar_radiation',
    #             'Surf_Thermal_radiation',
    #             'Surface_CAPE',
    #             'Surface_Temperature',
    #             'Surface_orography',
    #             'Temperature',
    #             'Total_precipitation',
    #             'U-velocity',
    #             'V-velocity',
    #             'Vertical_velocity',
    #             'Wet_Bulb_Poten_Temper',
    #             'freezing_level_zeroDegC_isotherm']
    layers = ['2_m_temperature',
              'Surface_Temperature',
                'Convective_rain',
                'Convective_snow',
                'Large_scale_rain',
                'Large_scale_snow',
                'Mean_sea_level_pressure',
                'Total_precipitation',]

    layers_lowercase = [l.lower() for l in layers]
    if layer.lower() not in layers_lowercase:
        logging.warning(_('Layer not found in the list of available layers'))
        return None

    layer = layers[layers_lowercase.index(layer.lower())]

    ows = "https://opendata.meteo.be/geoserver/alaro/ows?"

    legend = requests.get(ows, params={'layer': layer,
                                       'width': 50,
                                       'height': 50,
                                       'format': 'image/png',
                                       'service': 'WMS',
                                       'version': '1.3.0',
                                       'request': 'GetLegendGraphic'})

    return BytesIO(legend.content)

def getAlaro(cat:Literal['10_m_u__wind_component',
                         '10_m_v__wind_component',
                         '2_m_Max_temp_since_ppp',
                         '2_m_Min_temp_since_ppp',
                         '2_m_dewpoint_temperature',
                         '2_m_temperature',
                         '2m_Relative_humidity',
                         'Convective_rain',
                         'Convective_snow',
                         'Geopotential',
                         'Inst_flx_Conv_Cld_Cover',
                         'Inst_flx_High_Cld_Cover',
                         'Inst_flx_Low_Cld_Cover',
                         'Inst_flx_Medium_Cld_Cover',
                         'Inst_flx_Tot_Cld_cover',
                         'Large_scale_rain',
                         'Large_scale_snow',
                         'Mean_sea_level_pressure',
                         'Relative_humidity',
                         'Relative_humidity_isobaric',
                         'SBL_Meridian_gust',
                         'SBL_Zonal_gust',
                         'Specific_humidity',
                         'Surf_Solar_radiation',
                         'Surf_Thermal_radiation',
                         'Surface_CAPE',
                         'Surface_Temperature',
                         'Surface_orography',
                         'Temperature',
                         'Total_precipitation',
                         'U-velocity',
                         'V-velocity',
                         'Vertical_velocity',
                         'Wet_Bulb_Poten_Temper',
                         'freezing_level_zeroDegC_isotherm'],
                xl:float,
                yl:float,
                xr:float,
                yr:float,
                w:int = None,
                h:int = None,
                tofile=True,
                format:Literal['image/png', 'image/GeoTIFF']='image/png',
                time = None) -> BytesIO:

    wms=WebMapService(f'https://opendata.meteo.be/service/alaro/wms?',
                        version='1.3.0', timeout=10)

    ppkm = 300
    if w is None and h is None:
        real_w = (xr-xl)/1000
        real_h = (yr-yl)/1000
        w = int(real_w * ppkm)
        h = int(real_h * ppkm)
    elif w is None:
        real_w = (xr-xl)/1000
        real_h = (yr-yl)/1000
        ppkm = h/real_h
        w = int(real_w * ppkm)
        # h = int(real_h * ppkm)
    elif h is None:
        real_w = (xr-xl)/1000
        real_h = (yr-yl)/1000
        ppkm = w/real_w
        # w = int(real_w * ppkm)
        h = int(real_h * ppkm)

    MAXSIZE = 2000
    if w > MAXSIZE:
        pond = w / MAXSIZE
        w = MAXSIZE
        h = int(h / pond)
    if h > MAXSIZE:
        pond = h / MAXSIZE
        h = MAXSIZE
        w = int(w / pond)

    if tofile:
        img=wms.getmap(layers=['lc_hr_raster'],
                    #    styles=['default'],
                       srs='EPSG:31370',
                       bbox=(xl,yl,xr,yr),
                       size=(w,h),
                       format='image/png',
                       transparent=False)

        out = open('LifeWatch.png', 'wb')
        out.write(img.read())
        out.close()
        return None
    else:
        mycontents=list(wms.contents) # List all available layers
        curcont=[cat] # 'MS
        curstyles=['1']

        # test = get_Alaro_legend(cat)

        try:
            if time is None:
                time = wms[cat].timepositions[0].split('/')[0]

            img=wms.getmap(layers=curcont,
                        #    styles=curstyles,
                           srs='EPSG:31370',
                           bbox=(xl,yl,xr,yr),
                           size=(w,h),
                           format=format,
                           transparent=False,
                           time = time)

            return BytesIO(img.read())

        except:
            logging.warning(_('Impossible to get data from web services'))
            return None

class Alaro_Navigator(wx.Frame):
    """ Frame to navigate through Alaro data

    Propose a caolendar to select the time of the data
    """

    def __init__(self, parent, id, title):
        super(Alaro_Navigator, self).__init__(parent, title=title, size=(500, 150))

        panel = wx.Panel(self)
        vbox = wx.BoxSizer(wx.VERTICAL)
        hbox = wx.BoxSizer(wx.HORIZONTAL)
        hbox_start_end = wx.BoxSizer(wx.HORIZONTAL)
        hbox_interv_alpha = wx.BoxSizer(wx.HORIZONTAL)

        t_start, t_end, interv = get_Alaro_times()
        self._start_date = wx.TextCtrl(panel, value=t_start.replace('.000Z', 'Z'), size=(100, -1), style=wx.TE_READONLY | wx.TE_CENTER)
        self._end_date = wx.TextCtrl(panel, value=t_end.replace('.000Z', 'Z'), size=(100, -1), style=wx.TE_READONLY | wx.TE_CENTER)
        self._interval = wx.TextCtrl(panel, value=interv.replace('PT',''), size=(100, -1), style=wx.TE_READONLY | wx.TE_CENTER)

        self._btn_previous = wx.Button(panel, label=_('Previous'), size=(100, -1))
        self._btn_next = wx.Button(panel, label=_('Next'), size=(100, -1))
        self._time = wx.TextCtrl(panel, value=t_start.replace('.000Z', 'Z'), size=(100, -1), style=wx.TE_CENTER | wx.TE_PROCESS_ENTER)
        self._alpha = wx.TextCtrl(panel, value='1.0', size=(100, -1), style=wx.TE_CENTER | wx.TE_PROCESS_ENTER)
        self._alpha.SetToolTip(_('Transparency of the image (0-1)'))

        self._btn_legend = wx.Button(panel, label=_('Legend'), size=(100, -1))
        self._btn_legend.Bind(wx.EVT_BUTTON, self.OnLegend)

        self._time.Bind(wx.EVT_TEXT_ENTER, self.OnEnterTime)

        hbox.Add(self._btn_previous, 1, flag=wx.EXPAND | wx.ALL, border=1)
        hbox.Add(self._time, 1, flag=wx.EXPAND | wx.ALL, border=1)
        hbox.Add(self._btn_next, 1, flag=wx.EXPAND | wx.ALL, border=1)

        hbox_start_end.Add(self._start_date, 1, flag=wx.EXPAND | wx.ALL, border=1)
        hbox_start_end.Add(self._end_date, 1, flag=wx.EXPAND | wx.ALL, border=1)

        hbox_interv_alpha.Add(self._interval, 1, flag=wx.EXPAND | wx.ALL, border=1)
        hbox_interv_alpha.Add(self._alpha, 1, flag=wx.EXPAND | wx.ALL, border=1)

        vbox.Add(hbox, 1, flag=wx.EXPAND | wx.ALL, border=1)
        vbox.Add(hbox_start_end, 1, flag=wx.EXPAND | wx.ALL, border=1)
        vbox.Add(hbox_interv_alpha, 1, flag=wx.EXPAND | wx.ALL, border=1)
        vbox.Add(self._btn_legend, 1, flag=wx.EXPAND | wx.ALL, border=1)

        panel.SetSizer(vbox)

        self.Bind(wx.EVT_CLOSE, self.OnCloseWindow)
        self._btn_previous.Bind(wx.EVT_BUTTON, self.OnPrevious)
        self._btn_next.Bind(wx.EVT_BUTTON, self.OnNext)

    def OnPrevious(self, event):
        """ Hour minus interval
        """

        try:
            time = self.time

            # force the time to be rounded to the nearest interval
            interval = timedelta(hours=1)
            # nullify the minutes and seconds
            time = time.replace(minute=0, second=0, microsecond=0, hour=time.hour - 1)

            # check is the time is in the interval
            if time < self.start or time > self.end:
                wx.MessageBox(_('The date is not valid'), _('Error'), wx.OK | wx.ICON_ERROR)
                return

            self.time = time
        except ValueError:
            wx.MessageBox(_('The date is not valid'), _('Error'), wx.OK | wx.ICON_ERROR)
            return
        except Exception as e:
            wx.MessageBox(_('An error occurred: ') + str(e), _('Error'), wx.OK | wx.ICON_ERROR)
            return

        self.Parent._alaro_update_time()

        event.Skip()

    def OnNext(self, event):
        """ Hour plus interval
        """

        try:
            time = self.time

            # force the time to be rounded to the nearest interval
            interval = timedelta(hours=1)
            # nullify the minutes and seconds
            time = time.replace(minute=0, second=0, microsecond=0, hour=time.hour + 1)

            # check is the time is in the interval
            if time < self.start or time > self.end:
                wx.MessageBox(_('The date is not valid'), _('Error'), wx.OK | wx.ICON_ERROR)
                return

            self.time = time
        except ValueError:
            wx.MessageBox(_('The date is not valid'), _('Error'), wx.OK | wx.ICON_ERROR)
            return
        except Exception as e:
            wx.MessageBox(_('An error occurred: ') + str(e), _('Error'), wx.OK | wx.ICON_ERROR)
            return

        self.Parent._alaro_update_time()

        event.Skip()

    def OnCloseWindow(self, event):
        self.Hide()

        event.Skip()

    def OnLegend(self, event):
        """ Called when the user press the legend button
        """

        # get the legend of the layer
        layer = self.Parent._alaro_legends()

        event.Skip()

    def OnEnterTime(self, event):
        """ Called when the user press enter in the time text box
        """

        # time must be rounded to the nearest interval
        try:
            time = self.time

            # force the time to be rounded to the nearest interval
            interval = timedelta(hours=1)
            # nullify the minutes and seconds
            time = time.replace(minute=0, second=0, microsecond=0)

            # check is the time is in the interval
            if time < self.start or time > self.end:
                wx.MessageBox(_('The date is not valid'), _('Error'), wx.OK | wx.ICON_ERROR)
                return

            self.time = time
        except ValueError:
            wx.MessageBox(_('The date is not valid'), _('Error'), wx.OK | wx.ICON_ERROR)
            return
        except Exception as e:
            wx.MessageBox(_('An error occurred: ') + str(e), _('Error'), wx.OK | wx.ICON_ERROR)
            return

        self.Parent._alaro_update_time()

        event.Skip()

    @property
    def start(self):
        """ Return the start date selected by the user
        """
        return datetime.strptime(self._start_date.GetValue(), '%Y-%m-%dT%H:%M:%SZ')

    @property
    def end(self):
        """ Return the end date selected by the user
        """
        return datetime.strptime(self._end_date.GetValue(), '%Y-%m-%dT%H:%M:%SZ')

    @property
    def time(self):
        """ Return the time selected by the user
        """
        return datetime.strptime(self._time.GetValue(), '%Y-%m-%dT%H:%M:%SZ')

    @time.setter
    def time(self, value:datetime):
        """ Set the time selected by the user
        """
        self._time.SetValue(value.strftime('%Y-%m-%dT%H:%M:%SZ'))

    @property
    def time_str(self):
        """ Return the time selected by the user as string
        """
        return self._time.GetValue()

    @property
    def alpha(self):
        """ Return the alpha value selected by the user
        """
        try:
            return float(self._alpha.GetValue())
        except:
            self._alpha.SetValue('1.0')
            return 1.0


if __name__=='__main__':
    # me=pyproj.CRS.from_epsg(27573)
    # t=pyproj.Transformer.from_crs(27573,4326)
    # getIGNFrance('OI.OrthoimageCoverage.HR','EPSG:27563',878000,332300,879000,333300,1000,1000)
    img = getAlaro('Total_precipitation',250000,160000,252000,162000,1000,1000,False)
    img = Image.open(img)
    img.show()
    pass