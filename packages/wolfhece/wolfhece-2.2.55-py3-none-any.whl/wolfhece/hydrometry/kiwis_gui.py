"""
Author: HECE - University of Liege, Pierre Archambeau, Loïc Archambeau
Date: 2024

Copyright (c) 2024 University of Liege. All rights reserved.

This script and its content are protected by copyright law. Unauthorized
copying or distribution of this file, via any medium, is strictly prohibited.
"""

"""
WxPython  Graphical User Interface for walloon hydrometry website : https://hydrometrie.wallonie.be/
"""
import wx
import wx.adv
import matplotlib.pyplot as plt
import pandas as pd
from datetime import datetime as dt, timedelta
import logging
import numpy as np

#Test de la présence de la fonction de traduction i18n "gettext" et définition le cas échéant pour ne pas créer d'erreur d'exécution
import os
import gettext
# if os.path.exists(os.path.dirname(__file__)+'\\..\\locales'):
#     t = gettext.translation('base', localedir=os.path.dirname(__file__)+'\\..\\locales', languages=['fr'])
#     t.install()
# else:
#     try:
#         t = gettext.translation('base', localedir='wolfhece\\locales', languages=['fr'])
#         t.install()
#     except:
#         pass

_=gettext.gettext

from .kiwis import hydrometry, kiwis_keywords_horq, kiwis_keywords_rain, quality_code, kiwis_default_rain, kiwis_default_rain_HIC, kiwis_default_rain_Waterinfo

class hydrometry_gui(wx.Frame):
    """
    wxFrame for data selection

    General configuration :
      - sites
      - stations
      - timeseries par station
      --> plot
    """

    def __init__(self, credential='', *args, **kw):

        super().__init__(None,-1,_('Data collector'), size=(1024,600))
        self.panel = wx.Panel(self)

        colonne = wx.BoxSizer(wx.VERTICAL)

        ligne = wx.BoxSizer(wx.HORIZONTAL)

        self.listbox1 = wx.ListBox(self.panel,-1,choices=[],style=wx.LB_EXTENDED)
        self.listbox2 = wx.ListBox(self.panel,-1,choices=[],style=wx.LB_EXTENDED)
        self.listbox3 = wx.ListBox(self.panel,-1,choices=[],style=wx.LB_EXTENDED)

        self.button0 = wx.Button(self.panel,-1,_('Get sites'))

        self.button1 = wx.Button(self.panel,-1,_('Get stations name-code'))
        self.button1_cn = wx.Button(self.panel,-1,_('Get stations code-name'))
        self.button2 = wx.Button(self.panel,-1,_('Get timeseries list'))

        colplot = wx.BoxSizer(wx.VERTICAL)
        self.button3 = wx.Button(self.panel,-1,_('Get data and new plot...'))
        self.button8 = wx.Button(self.panel,-1,_('Get H-Q data, combine and new plot...'))
        self.button4 = wx.Button(self.panel,-1,_('Get data and add to plot...'))
        self.button6 = wx.Button(self.panel,-1,_('Get data quality code and plot...'))
        self.button5 = wx.Button(self.panel,-1,_('Export to CSV (data)...'))
        self.button7 = wx.Button(self.panel,-1,_('Export to CSV (data and QC)...'))

        self.infostations = wx.TextCtrl(self.panel, style = wx.TE_MULTILINE)

        self.timezone = wx.ComboBox(self.panel, -1, value='UTC', choices=['UTC', 'GMT+1', 'Europe/Brussels'], style=wx.CB_DROPDOWN)

        colplot.Add(self.button3, 1, wx.EXPAND, 0)
        colplot.Add(self.button8, 1, wx.EXPAND, 0)
        colplot.Add(self.button4, 1, wx.EXPAND, 0)
        colplot.Add(self.button6, 1, wx.EXPAND, 0)
        colplot.Add(self.button5, 1, wx.EXPAND, 0)
        colplot.Add(self.button7, 1, wx.EXPAND, 0)
        colplot.Add(self.timezone, 1, wx.EXPAND, 0)

        #organizing gui Get->Sites->select->Stations->select->Timeseries->Plot
        ligne.Add(self.button0,0,wx.EXPAND,0)
        ligne.Add(self.listbox1,1,wx.EXPAND,0)

        sizer_button_nc = wx.BoxSizer(wx.VERTICAL)
        sizer_button_nc.Add(self.button1,1,wx.EXPAND,0)
        sizer_button_nc.Add(self.button1_cn,1,wx.EXPAND,0)
        ligne.Add(sizer_button_nc, 0,wx.EXPAND,0)

        ligne.Add(self.listbox2,1,wx.EXPAND,0)
        ligne.Add(self.button2,0,wx.EXPAND,0)
        ligne.Add(self.listbox3,1,wx.EXPAND,0)
        ligne.Add(colplot, 0, wx.EXPAND, 0)

        ligne2 = wx.BoxSizer(wx.HORIZONTAL)

        self.cal1 = wx.adv.CalendarCtrl(self.panel,-1,style=wx.adv.CAL_MONDAY_FIRST)
        self.cal2 = wx.adv.CalendarCtrl(self.panel,-1,style=wx.adv.CAL_MONDAY_FIRST)

        col_dates = wx.BoxSizer(wx.VERTICAL)
        self.oneweek = wx.Button(self.panel,-1,_('Today minus one week'))
        self.onemonth = wx.Button(self.panel,-1,_('Today minus one month'))
        self.oneyear = wx.Button(self.panel,-1,_('Today minus one year'))
        self.tenyears = wx.Button(self.panel,-1,_('Today minus ten years'))

        col_dates.Add(self.oneweek,1,wx.EXPAND,0)
        col_dates.Add(self.onemonth,1,wx.EXPAND,0)
        col_dates.Add(self.oneyear,1,wx.EXPAND,0)
        col_dates.Add(self.tenyears,1,wx.EXPAND,0)

        self.cal2.SetDate(dt.today())
        self.cal1.SetDate(dt.today()-timedelta(60))

        ligne2.Add(self.cal1,1,wx.EXPAND,0)
        ligne2.Add(self.cal2,1,wx.EXPAND,0)
        ligne2.Add(col_dates,0,wx.EXPAND,0)

        #zonage
        ligne3 = wx.BoxSizer(wx.HORIZONTAL)
        colxy1 = wx.BoxSizer(wx.VERTICAL)
        colxy2 = wx.BoxSizer(wx.VERTICAL)
        colbut = wx.BoxSizer(wx.VERTICAL)

        ligne3.Add(colxy1, 1, wx.EXPAND)
        ligne3.Add(colxy2, 1, wx.EXPAND)
        ligne3.Add(colbut, 1, wx.EXPAND)

        self.x_nearest = wx.TextCtrl(self.panel, style = wx.TE_CENTRE |wx.TE_CENTER)
        self.y_nearest = wx.TextCtrl(self.panel, style = wx.TE_CENTRE|wx.TE_CENTER)
        self.x_ur = wx.TextCtrl(self.panel, style = wx.TE_CENTRE|wx.TE_CENTER)
        self.y_ur = wx.TextCtrl(self.panel, style = wx.TE_CENTRE|wx.TE_CENTER)
        self.x_ll = wx.TextCtrl(self.panel, style = wx.TE_CENTRE|wx.TE_CENTER)
        self.y_ll = wx.TextCtrl(self.panel, style = wx.TE_CENTRE|wx.TE_CENTER)

        self.x_nearest.SetToolTip(_('X coordinate for nearest search'))
        self.y_nearest.SetToolTip(_('Y coordinate for nearest search'))

        self.x_ll.SetToolTip(_('X lower left coordinate for interior serach'))
        self.y_ll.SetToolTip(_('Y lower left coordinate for interior serach'))
        self.x_ur.SetToolTip(_('X upper right coordinate for interior serach'))
        self.y_ur.SetToolTip(_('Y upper right coordinate for interior search'))


        self.find_nearest = wx.Button(self.panel,-1,_('Find nearest'))
        self.select_inside = wx.Button(self.panel,-1,_('Select inside'))
        colbut.Add(self.find_nearest, 1, wx.EXPAND)
        colbut.Add(self.select_inside, 1, wx.EXPAND)

        colxy1.Add(self.x_nearest, 1, wx.EXPAND)
        colxy1.Add(self.x_ur, 1, wx.EXPAND)
        colxy1.Add(self.x_ll, 1, wx.EXPAND)

        colxy2.Add(self.y_nearest, 1, wx.EXPAND)
        colxy2.Add(self.y_ur, 1, wx.EXPAND)
        colxy2.Add(self.y_ll, 1, wx.EXPAND)

        colonne.Add(ligne, 1, wx.EXPAND)
        colonne.Add(ligne2, 1, wx.EXPAND)
        colonne.Add(ligne3, 0, wx.EXPAND)

        colonne.Add(self.infostations,0, wx.EXPAND)

        self.panel.SetSizer(colonne)

        self.button0.Bind(wx.EVT_BUTTON, self.getsites)

        self.button1.Bind(wx.EVT_BUTTON, self.getstations)
        self.button1_cn.Bind(wx.EVT_BUTTON, self.getstations)

        self.button2.Bind(wx.EVT_BUTTON, self.gettimeseries)
        self.button3.Bind(wx.EVT_BUTTON, self.getdataandplot)
        self.button8.Bind(wx.EVT_BUTTON, self.getdatacombineandplot)
        self.button4.Bind(wx.EVT_BUTTON, self.getdataandplot)
        self.button6.Bind(wx.EVT_BUTTON, self.getdata_qc_andplot)
        self.button5.Bind(wx.EVT_BUTTON, self.exportcsv)
        self.button7.Bind(wx.EVT_BUTTON, self.exportcsv_qc)
        self.find_nearest.Bind(wx.EVT_BUTTON, self.nearest)
        self.select_inside.Bind(wx.EVT_BUTTON, self.inside)

        self.oneweek.Bind(wx.EVT_BUTTON, self.setdate)
        self.onemonth.Bind(wx.EVT_BUTTON, self.setdate)
        self.oneyear.Bind(wx.EVT_BUTTON, self.setdate)
        self.tenyears.Bind(wx.EVT_BUTTON, self.setdate)


        self.hydro = hydrometry(credential=credential, dir=kw.get('dir',''), url=kw.get('url',''))

        self.figsaxes=[]

        self.cn_or_nc = 'nc'

        self.Show()

    def setdate(self, event:wx.CommandEvent):

        mybut = event.GetEventObject()

        self.cal2.SetDate(dt.today())
        if mybut == self.oneweek:
            decal = timedelta(7)
        elif mybut == self.onemonth:
            decal = timedelta(31)
        elif mybut == self.oneyear:
            decal = timedelta(365)
        elif mybut == self.tenyears:
            decal = timedelta(3652)

        self.cal1.SetDate(dt.today()-decal)

    def getsites(self, event:wx.CommandEvent):
        """
        Get global sites
        """
        self.listbox1.Clear()
        self.listbox1.Append(self.hydro._get_sites_pythonlist())
        self.panel.Layout()

    def getstations(self, event:wx.CommandEvent):
        """
        Get stations for a specific selected site or multisites

        Store a list of these stations in self.stations_list
        """

        but = event.GetId()
        if but == self.button1_cn.Id:
            self.cn_or_nc = 'cn'
        else:
            self.cn_or_nc = 'nc'

        sel1 = self.listbox1.GetSelections()

        self.stations_list_nc=[]
        self.stations_list_cn=[]
        for cur in sel1:
            list_nc, list_cn = self.hydro._get_stations_pythonlist(self.hydro.sites['site_no'][cur], onlyreal=False)
            self.stations_list_nc += list_nc
            self.stations_list_cn += list_cn

        self._fill_list2()

    def _fill_list2(self):
        self.stations_list_nc.sort()
        self.stations_list_cn.sort()
        self.listbox2.Clear()

        if self.cn_or_nc == 'nc':
            self.listbox2.Append(self.stations_list_nc)
        else:
            self.listbox2.Append(self.stations_list_cn)

        self.panel.Layout()

    def _getname_code_fromindex(self,index):
        if self.cn_or_nc == 'nc':
            stationname = self.stations_list_nc[index].split('---')[0][:-1]
            stationcode = self.stations_list_nc[index].split('---')[1][1:]
        else:
            stationcode = self.stations_list_cn[index].split('---')[0][:-1]
            stationname = self.stations_list_cn[index].split('---')[1][1:]

        return stationname, stationcode

    def gettimeseries(self, event:wx.CommandEvent):
        """
        Get the timeseries for a selected station
        """
        to_exclude = ['alarm', 'batterie']

        if len(self.listbox2.GetSelections())==0:
            logging.error(_('No station selected'))
            return

        #treat only the first one if multiple selections
        stationname, stationcode = self._getname_code_fromindex(self.listbox2.GetSelections()[0])

        id,self.timeseries = self.hydro.timeseries_list(stationcode=stationcode)

        if self.timeseries is None:
            logging.warning(_('No timeseries for this station'))
            return

        self.timeseries.sort_values('ts_name', inplace=True)

        self.listbox3.Clear()

        for curkey in kiwis_keywords_horq:
            eltoadd = self.timeseries[self.timeseries['ts_name'].str.lower().str.contains(curkey.value.lower())]['ts_name'].to_list()
            if len(eltoadd)>0:
                for i, curel in reversed(list(enumerate(eltoadd))):
                    for curexc in to_exclude:
                        if curexc in curel.lower():
                            eltoadd.pop(i)
                            break
                self.listbox3.Append(eltoadd)

        for curkey in kiwis_keywords_rain:
            eltoadd = self.timeseries[self.timeseries['ts_name'].str.lower().str.contains(curkey.value.lower())]['ts_name'].to_list()
            if len(eltoadd)>0:
                for i, curel in reversed(list(enumerate(eltoadd))):
                    for curexc in to_exclude:
                        if curexc in curel.lower():
                            eltoadd.pop(i)
                            break
                self.listbox3.Append(eltoadd)

        for curkey in kiwis_default_rain:
            eltoadd = self.timeseries[self.timeseries['ts_name'].str.lower().str.contains(curkey.value.lower())]['ts_name'].to_list()
            if len(eltoadd)>0:
                for i, curel in reversed(list(enumerate(eltoadd))):
                    for curexc in to_exclude:
                        if curexc in curel.lower():
                            eltoadd.pop(i)
                            break
                self.listbox3.Append(eltoadd)

        for curkey in kiwis_default_rain_Waterinfo:
            eltoadd = self.timeseries[self.timeseries['ts_name'].str.lower().str.contains(curkey.value.lower())]['ts_name'].to_list()
            if len(eltoadd)>0:
                for i, curel in reversed(list(enumerate(eltoadd))):
                    for curexc in to_exclude:
                        if curexc in curel.lower():
                            eltoadd.pop(i)
                            break
                self.listbox3.Append(eltoadd)

        for curkey in kiwis_default_rain_HIC:
            eltoadd = self.timeseries[self.timeseries['ts_name'].str.lower().str.contains(curkey.value.lower())]['ts_name'].to_list()
            if len(eltoadd)>0:
                for i, curel in reversed(list(enumerate(eltoadd))):
                    for curexc in to_exclude:
                        if curexc in curel.lower():
                            eltoadd.pop(i)
                            break
                self.listbox3.Append(eltoadd)


        self.listbox3.Append('--')

        self.listbox3.Append(self.timeseries['ts_name'].tolist())

        bv = self.hydro.get_bv_dce(code=stationcode)
        cat_size = self.hydro.get_catchment_size(code=stationcode)
        datum = self.hydro.get_gauge_datum(code=stationcode)
        self.infostations.Clear()
        self.infostations.AppendText('Datum : {} - Catchment : size = {}; name = {}\n'.format(datum, cat_size, bv))

        self.panel.Layout()

    def _get_data(self):
        """
        Download data
        """
        sel2 = self.listbox2.GetSelections()
        sel3 = self.listbox3.GetSelections()

        if len(sel3)==0:
            return None, None, None, None

        self.recup_date()

        stationname, stationcode = self._getname_code_fromindex(self.listbox2.GetSelections()[0])

        datum = self.hydro.get_gauge_datum(code = stationcode)
        cat_size = self.hydro.get_catchment_size(code = stationcode)
        bv_dce = self.hydro.get_bv_dce(code = stationcode)

        data=[]
        tsname=[]

        for cur in sel3:
            #filtre sur base du nom stocké dans le wxListbox
            locname = self.listbox3.GetItems()[cur]
            if locname !='--':
                interval=300
                if "1h" in locname.lower():
                    interval = 3600
                elif "5min" in locname.lower():
                    interval = 300
                elif "10min" in locname.lower():
                    interval = 600
                elif "2min" in locname.lower():
                    interval = 120
                elif "jour" in locname.lower():
                    interval = 24*3600
                elif "mois" in locname.lower():
                    interval = 24*30*3600

                tsname.append('{} - {}'.format(stationname,locname))
                tsid=self.timeseries[self.timeseries['ts_name']==locname]['ts_id'].iloc[0]

                locdata = self.hydro.timeseries(fromdate=self.datefrom, todate=self.dateto, ts_id=tsid, interval=interval, timezone=self.timezone.Value)
                data.append(locdata)

        return stationname, stationcode, data, tsname, (datum, cat_size, bv_dce)

    def _get_data_qc(self):
        """
        Download data
        """
        sel2 = self.listbox2.GetSelections()
        sel3 = self.listbox3.GetSelections()

        if len(sel3)==0:
            return None, None, None, None

        self.recup_date()

        stationname, stationcode = self._getname_code_fromindex(self.listbox2.GetSelections()[0])
        datum = self.hydro.get_gauge_datum(code = stationcode)
        cat_size = self.hydro.get_catchment_size(code = stationcode)
        bv_dce = self.hydro.get_bv_dce(code = stationcode)

        data=[]
        tsname=[]

        for cur in sel3:
            #filtre sur base du nom stocké dans le wxListbox
            locname = self.listbox3.GetItems()[cur]
            if locname !='--':
                interval=300
                if "1h" in locname.lower():
                    interval = 3600
                elif "5min" in locname.lower():
                    interval = 300
                elif "10min" in locname.lower():
                    interval = 600
                elif "2min" in locname.lower():
                    interval = 120
                elif "jour" in locname.lower():
                    interval = 24*3600
                elif "mois" in locname.lower():
                    interval = 24*30*3600

                tsname.append('{} - {}'.format(stationname,locname))
                tsid=self.timeseries[self.timeseries['ts_name']==locname]['ts_id'].iloc[0]

                locdata = self.hydro.timeseries_qc(fromdate=self.datefrom, todate=self.dateto, ts_id=tsid, interval=interval, timezone=self.timezone.Value)
                data.append(locdata)

        return stationname, stationcode, data, tsname, (datum, cat_size, bv_dce)

    def getdataandplot(self,event:wx.CommandEvent):
        """
        Download data and plot
        """
        stationname, stationcode, data, tsname, datumsizebv = self._get_data()
        if stationname is None:
            return

        if event.GetEventObject() == self.button3 or len(self.figsaxes)==0:
            fig,ax = plt.subplots(1,1)
            self.figsaxes.append([fig,ax])
        else:
            fig, ax = self.figsaxes[-1]
            try:
                ax.set_title('{} - {}'.format(stationcode,stationname))
            except:
                fig,ax = plt.subplots(1,1)
                self.figsaxes.append([fig,ax])

        ax.set_title('{} - {}'.format(stationcode,stationname))
        ax.xaxis_date(self.timezone.GetValue())

        for curdata, curname in zip(data,tsname):
            if curdata is not None:
                if len(curdata)>1:
                    if datumsizebv[0]!='' and not np.isnan(datumsizebv[0]):
                        ax.step(curdata.index, curdata+float(datumsizebv[0]), where='post', label=curname)
                    else:
                        ax.step(curdata.index, curdata, where='post', label=curname)
        ax.set_xlabel('Time {}'.format(self.timezone.GetValue()))

        # Rotates and right-aligns the x labels so they don't crowd each other.
        for label in ax.get_xticklabels(which='major'):
            label.set(rotation=30, horizontalalignment='right')

        ax.legend()
        plt.show()

    def getdatacombineandplot(self,event:wx.CommandEvent):
        """
        Download data, combine and plot
        """
        stationname, stationcode, data, tsname, datumsizebv = self._get_data()
        if stationname is None:
            return

        if len(data)!=2:
            logging.warning(_('Select H AND Q series- Retry'))
            return
        if len(data[0])!=len(data[1]):
            logging.warning(_('Series are not of the same length- Retry'))
            return

        h=None
        q=None
        if 'Hauteur' in tsname[0]:
            h = data[0]
        if 'Debit' in tsname[0]:
            q = data[0]
        if 'Hauteur' in tsname[1]:
            h = data[1]
        if 'Debit' in tsname[1]:
            q = data[1]
        if h is None or q is None:
            logging.warning(_('Select H AND Q series- Retry'))
            return

        if event.GetEventObject() == self.button8 or len(self.figsaxes)==0:
            fig,ax = plt.subplots(1,1)
            self.figsaxes.append([fig,ax])
        else:
            fig, ax = self.figsaxes[-1]
            try:
                ax.set_title('{} - {}'.format(stationcode,stationname))
            except:
                fig,ax = plt.subplots(1,1)
                self.figsaxes.append([fig,ax])

        ax.set_title('{} - {}'.format(stationcode,stationname))

        ax.scatter(h, q, label = '{} - {}'.format(stationcode,stationname))

        ax.set_xlabel(_('Water depth [m]'))
        ax.set_ylabel(_('Discharge [$m^3s^{-1}$]'))

        ax.legend()
        fig.show()

    def getdata_qc_andplot(self,event:wx.CommandEvent):
        """
        Download data quality code and plot
        """
        stationname, stationcode, data, tsname, datumsizebv = self._get_data()
        if stationname is None:
            return

        stationname, stationcode, data_qc, tsname, datumsizebv = self._get_data_qc()

        if event.GetEventObject() == self.button3 or len(self.figsaxes)==0:
            fig,ax = plt.subplots(1,1)
            self.figsaxes.append([fig,ax])
        else:
            fig, ax = self.figsaxes[-1]
            try:
                ax.set_title('{} - {}'.format(stationcode,stationname))
            except:
                fig,ax = plt.subplots(1,1)
                self.figsaxes.append([fig,ax])

        ax.set_title('{} - {}'.format(stationcode,stationname))
        ax.xaxis_date(self.timezone.GetValue())

        for curdata, curqc, curname in zip(data, data_qc, tsname):
            if curdata is not None:
                if len(curdata)>1:
                    if datumsizebv[0]!='':
                        ax.step(curdata.index,curdata+float(datumsizebv[0]),where='post', label=curname)
                    else:
                        ax.step(curdata.index,curdata,where='post', label=curname)

                    for qc in quality_code:
                        select = curqc == qc.value[0]
                        ax.scatter(curdata.index[select], curdata[select], marker=qc.value[2], c=qc.value[1])

        ax.set_xlabel('Time {}'.format(self.timezone.GetValue()))

        # Rotates and right-aligns the x labels so they don't crowd each other.
        for label in ax.get_xticklabels(which='major'):
            label.set(rotation=30, horizontalalignment='right')

        ax.legend()
        plt.show()

    def exportcsv(self,event:wx.CommandEvent):
        """
        Download data and export to csv
        """
        stationname, stationcode, data, tsname, datumsizebv = self._get_data()
        if stationname is None:
            return

        for curdata, curname in zip(data, tsname):
            if curdata is not None:
                if len(curdata)>1:
                    curdata.to_csv('{}-{}.csv'.format(stationcode,curname), date_format="%Y%m%d%H%M%S%z", sep=";")

                    if datumsizebv[0]!='' and 'hauteur' in curname.lower():
                        curdata:pd.Series
                        zdata = curdata.copy()
                        zdata +=  float(datumsizebv[0])
                        zdata.to_csv('{}-{}_z.csv'.format(stationcode,curname), date_format="%Y%m%d%H%M%S%z", sep=";")

    def exportcsv_qc(self,event:wx.CommandEvent):
        """
        Download data and quality code and export to csv
        """
        self.exportcsv(1)
        stationname, stationcode, data, tsname, datumsizebv = self._get_data_qc()
        if stationname is None:
            return

        for curdata, curname in zip(data, tsname):
            if curdata is not None:
                if len(curdata)>1:
                    curdata.to_csv('{}-{}_qc.csv'.format(stationcode,curname), date_format="%Y%m%d%H%M%S%z", sep=";")

    def nearest(self, event:wx.CommandEvent):
        x = float(self.x_nearest.GetValue())
        y = float(self.y_nearest.GetValue())

        self.stations_list_nc = self.hydro.find_nearest(x,y,True)

        self._fill_list2()

        self.listbox2.SetSelection(0)

    def inside(self,event:wx.CommandEvent):
        xll = float(self.x_ll.GetValue())
        yll = float(self.y_ll.GetValue())
        xur = float(self.x_ur.GetValue())
        yur = float(self.y_ur.GetValue())

        self.stations_list_nc = self.hydro.select_inside(xll,yll,xur,yur,True)

        self._fill_list2()

    def recup_date(self):
        """
        Get date from calendars and store in self.datefrom and self.dateto
        """
        sel4 = self.cal1.GetDate()
        sel5 = self.cal2.GetDate()
        self.datefrom = dt(sel4.year,sel4.month+1,sel4.day)
        self.dateto = dt(sel5.year,sel5.month+1,sel5.day)
