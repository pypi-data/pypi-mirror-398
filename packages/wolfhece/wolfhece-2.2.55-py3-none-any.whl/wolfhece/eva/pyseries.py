"""
EXTREME VALUES ANALYSIS - EVA

@author : Pierre Archambeau - ULiege - HECE
@date   : 2023
"""

# extra modules
try:
    import numpy as np
    import pandas as pd
    from scipy import stats
    from scipy.interpolate import interp1d
    import os
    from datetime import datetime as dt, timedelta
    import matplotlib.pyplot as plt
    from matplotlib.axes import Axes
    from matplotlib.figure import Figure
    from matplotlib.patches import Rectangle
    import matplotlib.colors as mcolors
    from distfit import distfit
    import typing
except:
    raise Exception('Please install "numpy, pandas, scipy, matplotlib, distfit" module via "pip"')

# own modules
try:
    from . import bootstrap
    from .mixture_models import SeasonMixtureModel
    from .joint_models import JointModel
    from .hydrogramme_mono import Hydro_HSMF
except:
    import bootstrap
    from joint_models import JointModel
    from mixture_models import SeasonMixtureModel
    from hydrogramme_mono import Hydro_HSMF


# global fucntions

def change_font_size(ax:Axes, fontsize):
    """Adapte la taille de police d'un graphique"""

    for item in ([ax.title, ax.xaxis.label, ax.yaxis.label] +
                ax.get_xticklabels() + ax.get_yticklabels()):
        item.set_fontsize(fontsize)

def set_style(color:typing.Literal['b','g','r','c','m','y','k'],
               linestyle:typing.Literal['solid', 'dotted', 'deshed', 'dashdot']='solid',
               linewidth=1) -> dict['color':str,'linestyle':str,'linewidth':int]:

    return {'color':color, 'linestyle':linestyle, 'linewidth':linewidth}

def get_style(style:dict['color':str,'linestyle':str,'linewidth':int]):

    try:
        color = style['color']
    except:
        color     = 'k'
    try:
        linestyle = style['linestyle']
    except:
        linestyle = 'solid'
    try:
        linewidth = style['linewidth']
    except:
        linewidth = 2

    return color, linestyle, linewidth

def cunnane(r,n):
    """
    Calcul de la fréquence empirique selon Cunnane(1979)
    MAJ de la formulation de Weibull a priori mieux adaptée aux problèmes hydrologiques

    r : rang de la donnée 1<=r<=n
    n : nombre total de données dans l'échantillon
    """
    return ((r-0.4)/(n+0.2))

def weibull(r,n):
    """
    Calcul de la fréquence empirique selon Weibull - loi "uniforme"

    r : rang de la donnée 1<=r<=n
    n : nombre total de données dans l'échantillon
    """
    return r/(n+1)

def filliben(r,n):
    """
    Calcul de la fréquence empirique selon Filliben

    r : rang de la donnée 1<=r<=n
    n : nombre total de données dans l'échantillon
    """
    if  r==n:
        return 0.5**(1/n)
    elif r==1:
        return 1 - 0.5**(1/n)
    else:
        return (r - 0.3175) / (n + 0.365)

def aic(mle, n, k=2, corrected=True):
    """
    The Akaike information criterion (AIC) is a metric that is used to compare the fit of different regression models.

    It is calculated as:

    AIC = 2K – 2ln(L)

    where:

    K: The number of model parameters (including loc and scale)
    mle = ln(L): The log-likelihood of the model. This tells us how likely the model is, given the data.

    https://fr.wikipedia.org/wiki/Crit%C3%A8re_d%27information_d%27Akaike
    https://www.statology.org/aic-in-python/
    """
    aic = 2*k-2*mle

    if corrected:
        aic += (2*k*(k+1))/(n-k-1)

    return aic

def bic(mle, n, k=2):
    """
    the Bayesian information criterion (BIC) or Schwarz information criterion (also SIC, SBC, SBIC) is a criterion for model selection among a finite set of models
    Models with lower BIC are generally preferred. It is based, in part, on the likelihood function and it is closely related to the Akaike information criterion (AIC).

    https://en.wikipedia.org/wiki/Bayesian_information_criterion
    https://fr.wikipedia.org/wiki/Crit%C3%A8re_d%27information_bay%C3%A9sien
    """
    bic = k * np.log(n) - 2 * mle

    return bic

def _get_hist_params(X, bins, mhist='numpy'):
    """
    Get histogram of original data
    """

    histvals, binedges = np.histogram(X, bins=bins, density=True,)
    bincenters = (binedges + np.roll(binedges, -1))[:-1] / 2.0

    return(bincenters, histvals)

def rss(data, pdf, bins=100):
    """
    Residual sum of squares

    based on pdf and data's histogram

    https://en.wikipedia.org/wiki/Residual_sum_of_squares
    """
    binedges,hist = _get_hist_params(data,bins)
    y_obs = hist / hist.sum()
    return np.sum(np.power(y_obs[~(y_obs==0)] - pdf(binedges[~(y_obs==0)]), 2.0))

def _generate_clusters(exceedances: pd.Series, r: typing.Union[pd.Timedelta, typing.Any]) -> typing.Generator[pd.Series, None, None]:
    if not isinstance(r, pd.Timedelta):
        try:
            r = pd.to_timedelta(r)
        except Exception as error:
            raise ValueError(f"invalid value in {r} for the 'r' argument") from error

    # Locate clusters separated by gaps not smaller than `r`
    gap_indices = np.argwhere(
        (exceedances.index[1:] - exceedances.index[:-1]) > r
    ).flatten()
    if len(gap_indices) == 0:
        # All exceedances fall within the same cluster
        yield exceedances
    else:
        for i, gap_index in enumerate(gap_indices):
            if i == 0:
                # First cluster contains all values left from the gap
                yield exceedances.iloc[: gap_index + 1]
            else:
                # Other clusters contain values between previous and current gaps
                yield exceedances.iloc[gap_indices[i - 1] + 1 : gap_index + 1]

        # Last cluster contains all values right from the last gap
        yield exceedances.iloc[gap_indices[-1] + 1 :]

# Constants
MONTHS_WINTER = [10,11,12,1,2,3]
MONTS_SUMMER = [4,5,6,7,8,9]
SEASONS = ['annual', 'winter', 'summer']
SEASONS_MARKERS = ['o', '*', 'x', '2']
SEASONS_COLORS = ['r', 'g', 'b', 'c']
SEASONS_ALL = SEASONS + ['mixture', 'joint']
RETURN_PERIOD_ESTIMATE = np.asarray([1.005, 1.0101, 1.0204, 1.111, 1.25, 1.4286, 2, 3, 5, 10, 15, 20, 25, 30, 40, 50, 60, 70, 80, 90, 100, 125, 150, 200, 300, 400, 500, 600, 750, 1000], dtype=np.float64)
INTERV_CI = [60, 75, 90, 95]

def sanitize_seasons(seasons = None, all=False):
    if all:
        def_values = SEASONS_ALL
    else:
        def_values = SEASONS

    if seasons is None:
        seasons = def_values
    else:
        if isinstance(seasons,list):
            pass
        elif seasons in def_values:
            seasons = [seasons]
        else:
            raise Exception('Bad season ! - retry')

    return seasons

# Liste des lois à tester
#  2, 3 ou 4 paramétres
#  fonction, couleur et type de trait, nombre de points de départ différents à tester
dists_4params = {'Johnsonsu':[stats.johnsonsu,'k--',-1]}

dists_3params = {'GEV':[stats.genextreme,'c',-1],       #contains Gumbel, Weibull, Fréchet
                'Weibull':[stats.weibull_min,'r',0],    #special case of GEV (if c==1 --> exponential, c==2 --> Rayleigh)
                'Fréchet':[stats.invweibull,'r--',0],   #special case of GEV
                #  'Weibull inverse cdf':[stats.invweibull,'k--',0] #== Fréchet
                'Log normale':[stats.lognorm,'k',-1],
                'Gamma':[stats.gamma,'y',0],
                #  'GenGamma cdf':[stats.gengamma,'c--',0],
                'Loggamma':[stats.loggamma,'y--',0],
                'Pearson3':[stats.pearson3,'m--',-1],    #== Gamma
                'Gamma inverse':[stats.invgamma,'m',-1],
                }

dists_2params = {'Gumbel':[stats.gumbel_r,'b',-1],       #special case of GEV with c=0
                'Normal':[stats.norm,'g',0],
                'Gibrat':[stats.gibrat,'orange',0],    #special case of lognorm with s=1
                'Exponentielle':[stats.expon,'b--',0]}    #special case of Weibull with c==1 or genpareto with c==0

LAWS_FULL = list(dists_2params.keys()) +list(dists_3params.keys()) + list(dists_4params.keys())
LAWS_POPULAR = ['GEV', 'Log normale', 'Gumbel', 'Exponentielle', 'Pearson3', 'Gamma inverse', 'Weibull', 'Gamma', 'Johnsonsu']

class EVA_Serie:
    """
    One time serie
    """
    def __init__(self, data, datetime_index=None, datetime_format="%Y%m%d%H%M%S", data_headers=("#DateHeure", "Debit"), duration=1, startmonth_winter = 10, startmonth_summer=4, hydrol=True, verbose=True) -> None:

        self.duration = duration
        self.startmonth_winter = startmonth_winter
        self.startmonth_summer = startmonth_summer
        self.hydrological_year = hydrol
        self.best = None

        head_date, head_q = data_headers

        self.index_NaN = []
        self.index_NA = []

        if isinstance(data,pd.Series):
            self.data = pd.to_numeric(data, 'coerce')
            data.dropna(how='all', inplace=True)
        elif isinstance(data,np.ndarray):
            self.data = pd.to_numeric(pd.Series(data), 'coerce')
            self.data.index=datetime_index
            self.data.dropna(how='all', inplace=True)
        elif isinstance(data,str):
            # récupération du fichier CSV
            # ouverture du fichier en entrée et création de la matrice de base --> Datetime, Debit

            # soit :
            # custom_date_parser = lambda x: datetime.strptime(x, "%Y%m%d%H%M%S")
            # df=pd.read_csv(fichier_in,sep=";",header=0, parse_dates=['#DateHeure'],date_parser=custom_date_parser,na_values=-777.) # Note PA : Normalement plus rapide à lire que l'Excel
            # soit : (un peu plus rapide !)
            df = pd.read_csv(data,sep=";",header=0) # Note PA : Normalement plus rapide à lire que l'Excel
            df.dropna(how='all', inplace=True)

            if head_date in df.columns and head_q in df.columns:
                df[head_date] = pd.to_datetime(df[head_date],format=datetime_format)
            elif 'Timestamp'  in df.columns and 'Value' in df.columns:
                head_date, head_q = ('Timestamp','Value')
                df[head_date] = pd.to_datetime(df[head_date],format=datetime_format)
            else:
                raise RuntimeError('Please check your headers {}, {}'.format(head_date,head_q))

            #Suppression des dates incorrectes
            df.drop(index=np.where(pd.isnull(df[head_date]))[0], inplace=True)

            # conversion en time series pandas
            self.data = df.set_index(head_date)[head_q]

            self.index_NaN  = np.where(self.data=="#VALEUR!")[0]
            self.index_NA   = np.where(self.data!=self.data)[0]

            self.data = pd.to_numeric(df.set_index(head_date)[head_q], 'coerce')

            # Aprés lecture, le champ d'index '#DateHeure'est un objet datetime assez facile à manipuler --> .year, .day, .month, .hour, ...
            # ou à filtrer!
            # exemple : self.data[self.data.index >= '2020-09-01'] --> Tous les débits au-delà du 2020/09/01
            # exemple : self.data[(self.data.index >= '2020-09-01') & (self.data.index < '2021-01-01')] --> Tous les débits entre 2 dates
        else:
            raise Exception('Format non supported -- Please code your importing filter')

        self.check_dupliactes()

        self.nb = self.data.shape[0]

        self.index_isnan = np.where(np.isnan(self.data))[0]
        self.index_neg   = np.where(self.data<0.)[0]
        self.index_zero  = np.where(self.data==0.)[0]

        self.nodata = {'negative':self.index_neg, 'nan': self.index_isnan, "null" : self.index_zero, 'nan_excel': self.index_NaN, 'na_excel': self.index_NA}

        self.nbneg  = self.index_neg.shape[0]
        self.nbzero  = self.index_zero.shape[0]
        try:
            # gestion de ce cas spécial d'un NaN d'Excel
            self.nbnan_excel  = self.index_NaN.shape[0]
        except:
            self.nbnan_excel  = 0

        try:
            # gestion de ce cas spécial d'un #N/A d'Excel
            self.nbNA_excel  = self.index_NA.shape[0]
        except:
            self.nbNA_excel  = 0

        self.nbnan  = self.index_isnan.shape[0] - self.nbnan_excel - self.nbNA_excel

        self.years_bounds = [np.min(self.data.index.year), np.max(self.data.index.year)]

        if verbose:
            print(self.duration,'heures')
            print('How many zero values ? {}'.format(self.nbzero))
            print('How many negative values ? {}'.format(self.nbneg))
            print('How many NaN values ? {}'.format(self.nbnan))
            print('How many #VALEUR! values ? {}'.format(self.nbnan_excel))
            print('How many #N/A values ? {}'.format(self.nbNA_excel))
            print()
            print('Starting year : {}'.format(self.years_bounds[0]))
            print('Ending year : {}'.format(self.years_bounds[-1]))

        self.filter()
        self.maxima={}
        self.pot={}

        self.tz_info = self.data.index[0].tz

    def check_dupliactes(self):
        """
        Check if there are duplicates in the data
        """
        if not self.data.index.is_unique:
            print('****\n')
            print('Non unique index detected - removing duplicates - keep first value\n')
            print(self.data.index[self.data.index.duplicated()])
            print('****\n\n')
            self.data = self.data[~self.data.index.duplicated(keep='first')]

    def filter(self):
        """
        Set zero, negative, NaN, Nat to np.nan
        """
        for curindex in self.nodata.values():
            if len(curindex)>0:
                self.data.iloc[curindex]=np.nan

    def get_date_max(self, year, seasons=None) -> list:
        """
        Récupère la date du maximum de l'année "year"
        Possibilité de traiter plusieurs saisons
        """
        seasons = sanitize_seasons(seasons)

        resdates = []
        for curseason in seasons:
            if not 'water_year' in self.maxima[curseason].keys():
                self.find_maxima(self.hydrological_year)

            idx = self.maxima[curseason]['water_year'].index(dt(year,1,1, tzinfo=self.tz_info))
            resdates.append((self.maxima[curseason]['date'][idx], curseason))
        return resdates

    def get_one_maxevent(self, year, seasons=None) -> list:
        """
        Récupération de l'événement max pour une année spécifique
        Possibilité de traiter plusieurs saisons
        """
        seasons = sanitize_seasons(seasons)

        resevents = []
        for curseason in seasons:
            if not 'water_year' in self.maxima[curseason].keys():
                self.find_maxima(self.hydrological_year)
            if not 'events' in self.maxima[curseason].keys():
                self.extract_maxevents()

            if dt(year,1,1, tzinfo=self.tz_info) in self.maxima[curseason]['water_year']:
                idx = self.maxima[curseason]['water_year'].index(dt(year,1,1, tzinfo=self.tz_info))
                curevent = self.maxima[curseason]['events'][year]
                date = self.maxima[curseason]['date'][idx]

                resevents.append( (date, curevent, idx, curseason))

        return resevents

    def get_nb_maxevents(self, nbevents:int, seasons=None) -> dict[str, pd.DataFrame]:
        """Récupère les nbevents lus grands pics de crue"""
        seasons = sanitize_seasons(seasons)

        max_nb = {}

        for curseason in seasons:
            maxima = pd.DataFrame({'date':self.maxima[curseason]['date'].copy(),
                                   'value':self.maxima[curseason]['maxval'].copy()})
            maxima.set_index('date')
            maxima.sort_values(['value'], inplace=True)

            max_nb[curseason] = maxima.iloc[-nbevents:]

        return max_nb

    def get_nb_max_hydro(self, nbevents:int, seasons=None) -> dict[str, pd.DataFrame]:
        """Récupère les nbevents plus grands hydrogrammes de crue"""
        seasons = sanitize_seasons(seasons)

        ret = {}
        for curseason in seasons:

            if not 'water_year' in self.maxima[curseason].keys():
                self.find_maxima(self.hydrological_year)
            if not 'events' in self.maxima[curseason].keys():
                self.extract_maxevents()

            dates = self.maxima[curseason]['date']
            water_year = self.maxima[curseason]['water_year']
            curdict = self.maxima[curseason]['events']

            hydro = pd.DataFrame({'date':water_year,
                                  'hydro':[val for val in curdict.values()],
                                  'max':[val.max() for val in curdict.values()]})
            hydro.sort_values('max', inplace=True)
            ret[curseason] = hydro.iloc[-nbevents:]

        return ret

    def save_max_events(self, filename, years_bounds:list=None, seasons=None):
        """
        Enregistrement des crues maximales dans un fichier CSV
        """
        seasons = sanitize_seasons(seasons)

        if years_bounds is None:
            year_begin = self.years_bounds[0]
            year_end   = self.years_bounds[-1]
        else:
            year_begin = years_bounds[0]
            year_end   = years_bounds[-1]

        # writer = pd.ExcelWriter(filename, engine="xlsxwriter")

        for curseason in seasons:
            res = {}
            for curyear in np.arange(year_begin, year_end+1):
                ret = self.get_one_maxevent(curyear, curseason) # récupération du timeseries
                if len(ret)>0:
                    res[curyear] = ret[0][1]

            df= pd.DataFrame.from_dict(res) #, 'index')

            # df.to_excel(writer, sheet_name=curseason)
            df.to_csv(filename, sep=";")

        # writer.close()

    def _select_dict(self,method:typing.Literal['BM', 'POT'] ='BM'):

        if method=='BM':
            return self.maxima
        elif method=='POT':
            return self.pot

    def _get_dates(self, year=None, hydrol=True, season=None):
        """
        Compute date for current year and season

        Args:
            year (integer, optional): If None, the complete interval will be used. Defaults to None.
            hydrol (bool, optional): Hydrological year or not. Defaults to True.
            season ('annual', 'winter' or 'summer', optional): None == 'annual'. Defaults to None.
        """
        if year is None:
            start_date = dt(self.years_bounds[0]  , 1, 1, tzinfo=self.tz_info)
            end_date   = dt(self.years_bounds[1]+1, 1, 1, tzinfo=self.tz_info)
        else:
            if hydrol:
                if season is None or season.lower() == 'annual':
                    start_date = dt(year-1,10,1, tzinfo=self.tz_info)
                    end_date   = dt(year,10,1, tzinfo=self.tz_info)
                elif season.lower() == 'winter' or season.lower() == 'hiver':
                    start_date = dt(year-1,self.startmonth_winter,1, tzinfo=self.tz_info)
                    end_date   = dt(year,self.startmonth_summer,1, tzinfo=self.tz_info)
                elif season.lower() == 'summer' or season.lower() == 'ete'  or season.lower() == 'été':
                    start_date = dt(year,self.startmonth_summer,1, tzinfo=self.tz_info)
                    end_date   = dt(year,self.startmonth_winter,1, tzinfo=self.tz_info)
                else:
                    raise Exception('Bad season !! - retry')
            else:
                start_date = dt(year,1,1, tzinfo=self.tz_info)
                end_date   = dt(year+1,1,1, tzinfo=self.tz_info)

        return start_date, end_date

    def _get_max(self,
                 year=None,
                 hydrol=True,
                 season=None,
                 method: typing.Literal['BM', 'POT'] ='BM',
                 threshold=0.,
                 r: typing.Union[pd.Timedelta, typing.Any] = "24H"):
        """
        Find maxima in specific period
        """
        start_date, end_date = self._get_dates(year, hydrol, season)

        df = self.data[(self.data.index>=start_date) & (self.data.index<end_date)]

        if method=='BM':
            if len(df)>0:
                idx = df.argmax()
                return [df.index[idx], df.iloc[idx]]
            else:
                return [None, np.nan]
        elif method =='POT':
            # Get exceedances
            exceedances = df.loc[df.values > threshold]

            # Locate clusters separated by gaps not smaller than `r`
            # and select min or max (depending on `extremes_type`) within each cluster
            extreme_dates, extreme_values = [], []
            for cluster in _generate_clusters(exceedances=exceedances, r=r):
                extreme_dates.append(cluster.idxmax())
                extreme_values.append(cluster.loc[cluster.idxmax()])

            return [extreme_dates, extreme_values]

    def get_data_for_one_season(self, method:typing.Literal['BM', 'POT'] ='BM', season=None):

        if season is None:
            return None
        else:
            try:
                return self._select_dict(method)[season]
            except:
                return None

    def get_fit_one_season(self, method:typing.Literal['BM', 'POT'] ='BM', season=None):

        if season is None:
            return None
        else:
            try:
                return self._select_dict(method)[season]['fit']
            except:
                return None

    def save_fit_one_season(self, filename:str, method:typing.Literal['BM', 'POT'] ='BM', season=None, fit_method='MLE', sep=';'):

        df = pd.DataFrame.from_dict(self.get_fit_one_season(method='BM', season=season)[fit_method], orient='index')
        df.drop('func', inplace=True, axis=1)

        df.to_csv(filename, sep=sep)

    def find_maxima(self, hydrol=True, excluded_years=[], method:typing.Literal['BM', 'POT']='BM', threshold: float=0., r: typing.Union[pd.Timedelta, typing.Any] = "24H", verbose=True):
        """
        Find maxima in whole data
        """
        self.hydrological_year = hydrol

        curdict = self._select_dict(method)
        if method=='POT':
            self.pot_threshold = threshold
            self.pot_r = r

        for cur in SEASONS:
            curdict[cur]={}
            curdict[cur]['date'] = []
            curdict[cur]['water_year'] = []
            curdict[cur]['maxval'] = []
            curdict[cur]['serie'] = None

        for cur in SEASONS:
            for curyear in range(self.years_bounds[0],self.years_bounds[1]+1):

                if not curyear in excluded_years:

                    date,val = self._get_max(curyear,hydrol,season=cur,method=method , threshold=threshold, r=r)

                    if method=='BM':
                        if not np.isnan(val):
                            curdict[cur]['date'].append(date)
                            curdict[cur]['water_year'].append(dt(curyear,1,1, tzinfo=self.tz_info))
                            curdict[cur]['maxval'].append(val)
                        else:
                            if verbose:
                                print('NaN value encountered - season : {} - year : {}'.format(cur,curyear))
                    elif method=='POT':
                        if not val==[]:
                            curdict[cur]['date']+= date
                            curdict[cur]['water_year']+= [dt(curyear,1,1, tzinfo=self.tz_info)]*len(date)
                            curdict[cur]['maxval']+=val
                        else:
                            if verbose:
                                print('Void value encountered - season : {} - year : {}'.format(cur,curyear))

        for cur in SEASONS:
            curdict[cur]['maxval'] = np.asarray(curdict[cur]['maxval'])

            df = pd.DataFrame(curdict[cur]['maxval'])
            df.index=curdict[cur]['date']
            curdict[cur]['serie'] = df.squeeze()

    def extract_oneevent(self, datecenter, before=1, after=2):
        """
        Extract hydrograph around a date

        Args:
            before : number of days before center
            after : number of days after center
        """
        return self.data[(self.data.index >= datecenter - timedelta(before)) & (self.data.index <= datecenter + timedelta(after))]

    def extract_maxevents(self,before=1, after=2):
        """
        Extract hydrograph for each maximum

        Args:
            before : number of days before maximum
            after : number of days after maximum
        """
        for cur in SEASONS:
            dates = self.maxima[cur]['date']
            water_year = self.maxima[cur]['water_year']
            curdict = self.maxima[cur]['events'] = {}
            self.maxima[cur]['before']=before
            self.maxima[cur]['after'] =after
            for curdate, curwy in zip(dates,water_year):
                curdict[curwy.year] = self.data[(self.data.index >= curdate - timedelta(before)) & (self.data.index <= curdate + timedelta(after))]

    def sort_maxima(self, seasons=None):
        """
        Sort maxima in increasing order to calculate empirical frequency
        """
        seasons = sanitize_seasons(seasons)

        for curseason in seasons:
            self.maxima[curseason]['sorted_maxval'] = sorted(self.maxima[curseason]['maxval'])

    def _fit_multistarts(self, data, fdist, nb=0, method='MLE'):
        """
        Fit de la loi en adaptant éventuellement le point de départ
        Ceci n'est sans doute réellement utile que pour la loi de Weibull
        """
        dist:stats.rv_continuous
        dist,res=fdist

        if res is None:
            # Pas de points de départ fournis
            if nb==0:
                nb=5

            if dist is stats.genextreme :
                # la loi de Gumbel étant un cas particulier de la GEV, on initialise les paramétres sur base de ce fit
                res = stats.gumbel_r.fit(data,method=method)
                res = dist.fit(data,0.,loc=res[0],scale=res[1],method=method)
            elif dist is stats.weibull_min :
                # la loi de Weibull étant un cas particulier de la GEV
                res = stats.gumbel_r.fit(data,method=method)
                res = dist.fit(data,0.,loc=res[0],scale=res[1],method=method)
                res = dist.fit(data,1.,loc=res[0],scale=res[1],method=method)
            elif dist is stats.gamma or dist is stats.gengamma:
                res = stats.pearson3.fit(data,method=method)
                res = dist.fit(data,res[0],loc=res[1],scale=res[2],method=method)
            elif dist is stats.lognorm:
                res = stats.gibrat.fit(data,method=method)
                res = dist.fit(data,0.,loc=res[0],scale=res[1],method=method)
            else:
                res = dist.fit(data,method=method)
        else:
            if dist.numargs>0:
                res = dist.fit(data,res[0],loc=res[1],scale=res[2],method=method)
            else:
                res = dist.fit(data,loc=res[0],scale=res[1],method=method)

        mle = -dist.nnlf(res,data)
        resul=(mle,res)

        if nb>0:
            mlemax=mle
            all=[]

            if dist.numargs==1:
                loc = np.random.normal(res[1],10,nb)
                scale = np.random.normal(res[2],5,nb)
                skew = np.random.normal(res[0],1,nb)
                for curloc in loc:
                    for curscal in scale:
                        for curskew in skew:
                            try:
                                res = dist.fit(data,curskew,loc=curloc,scale=curscal,method=method)
                                mle = dist.nnlf(res,data)

                                if mle is not np.inf:
                                    all.append((mle,res))
                                if mle < mlemax:
                                    mlemax=mle
                                    resul=(mle,res)
                            except:
                                pass
            else:
                loc = np.random.normal(res[0],10,nb)
                scale = np.random.normal(res[1],5,nb)
                for curloc in loc:
                    for curscal in scale:

                        res = dist.fit(data,loc=curloc,scale=curscal,method=method)
                        mle = dist.nnlf(res,data)

                        if mle is not np.inf:
                            all.append((mle,res))
                            if mle < mlemax:
                                mlemax=mle
                                resul=(mle,res)

        return resul

    def _evaluate_ci(self, data, fdist, nboot=500, method='MLE'):
        """
        Evaluate confidence interval based on bootstrap method

        REMARK : CI for MLE can be analyzed by Fisher coefficients
        """
        p_cum = 1.-1./RETURN_PERIOD_ESTIMATE

        # Intervalles de confiance pour la distribution dist

        dist:stats.rv_continuous
        dist,res=fdist

        # recherche des intervalles de confiance par Bootstraping
        data_boot = bootstrap.Bootstrap(data)
        data_boot.generate(nboot)

        all_mle=[]
        all_params=[]
        for curdata in data_boot.series:
            mle, res = self._fit_multistarts(curdata,fdist,-1,method)
            all_mle.append(mle)
            all_params.append(res)

        ic = {}
        ic['mle'] = all_mle
        ic['params'] = all_params
        ic['sup'] = {}
        ic['inf'] = {}
        for idx,curinterv in enumerate(INTERV_CI):
            ic['inf'][curinterv] = []
            ic['sup'][curinterv] = []

        for curp in p_cum:
            if dist.numargs>0:
                ic['funcs'] = [dist(curres[0],loc=curres[1],scale=curres[2]) for curres in all_params]
            else:
                ic['funcs'] = [dist(loc=curres[0],scale=curres[1]) for curres in all_params]

            val = [curfunc.ppf(curp) for curfunc in ic['funcs']]

            bounds = [ (100-curinterv)/2./100. for curinterv in INTERV_CI]
            bounds = bounds + [ 1.- ((100-curinterv)/2./100.) for curinterv in INTERV_CI]
            quant=np.quantile(val,bounds)

            nb = len(INTERV_CI)
            for idx,curinterv in enumerate(INTERV_CI):
                ic['inf'][curinterv].append(quant[idx])
                ic['sup'][curinterv].append(quant[idx+nb])

        return ic

    def get_fitted_params(self, season=None, law='GEV', method='MLE'):

        if season is None:
            return None

        try:
            return self.maxima[season]['fit'][method][law]['params']
        except:
            return None

    def get_T_from_q(self,
                     q:list,
                     season:str='best',
                     law:str='best',
                     method:str='MLE',
                     ic=False) -> pd.DataFrame:

        try:
            if law == 'best':
                lawfit = self.best
            else:
                try:
                    lawfit = self.maxima[season]['fit'][method][law]['func']
                except:
                    lawfit = None
        except:
            lawfit = None

        if lawfit is None:
            raise NameError('Bad law -- retry!')

        if not isinstance(q,list):
            q=list(q)

        rp = {curq : {'mean':1./(1.-lawfit.cdf(curq))} for curq in q}

        if ic and law!='best':
            dictm = self.maxima[season]['fit'][method]
            dictlaw = dictm[law]
            if 'ic' in dictlaw.keys():
                dictic_sup = dictlaw['ic']['sup']
                dictic_inf = dictlaw['ic']['inf']

                for idx, curic in enumerate(dictic_inf):
                    c_inf = dictic_inf[curic]
                    c_sup = dictic_sup[curic]

                    finf = interp1d(c_inf, RETURN_PERIOD_ESTIMATE)
                    fsup = interp1d(c_sup, RETURN_PERIOD_ESTIMATE)

                    for curq in q:
                        try:
                            rp[curq][str(curic)+'sup'] = float(fsup(curq))
                        except:
                            rp[curq][str(curic)+'sup'] = None
                        try:
                            rp[curq][str(curic)+'inf'] = float(finf(curq))
                        except:
                            rp[curq][str(curic)+'inf'] = None

        df= pd.DataFrame.from_dict(rp, 'index')

        return df

    def get_q_from_T(self,
                     return_periods:list=[5,10,15,20,25,50,75,100,200,500,1000],
                     season:str='best',
                     law:str='best',
                     method:str='MLE',
                     ic=False) -> pd.DataFrame:

        try:
            if law == 'best':
                lawfit = self.best
            else:
                try:
                    lawfit = self.maxima[season]['fit'][method][law]['func']
                except:
                    lawfit = None
        except:
            raise NameError('Bad law -- retry!')

        if lawfit is None:
            return None

        if not isinstance(return_periods,list):
            return_periods=list(return_periods)

        q = {curT : {'mean_value':lawfit.ppf(1.-1./float(curT))} for curT in return_periods}

        if ic and law!='best':
            dictm = self.maxima[season]['fit'][method]
            dictlaw = dictm[law]
            if 'ic' in dictlaw.keys():
                dictic_sup = dictlaw['ic']['sup']
                dictic_inf = dictlaw['ic']['inf']

                for idx, curic in enumerate(dictic_inf):
                    c_inf = dictic_inf[curic]
                    c_sup = dictic_sup[curic]

                    finf = interp1d(RETURN_PERIOD_ESTIMATE, c_inf)
                    fsup = interp1d(RETURN_PERIOD_ESTIMATE, c_sup)

                    for curT in return_periods:
                        # q[curT][str(curic)+'sup'] = float(fsup(curT))
                        # q[curT][str(curic)+'inf'] = float(finf(curT))
                        try:
                            q[curT][str(curic)+'sup'] = float(fsup(curT))
                        except:
                            q[curT][str(curic)+'sup'] = None
                        try:
                            q[curT][str(curic)+'inf'] = float(finf(curT))
                        except:
                            q[curT][str(curic)+'inf'] = None


        df= pd.DataFrame.from_dict(q, 'index',)


        return df

    def save_q_from_T(self,
                      filename:str='',
                      return_periods=[5,10,15,20,25,50,75,100,200,500,1000],
                      season='best',
                      law='best',
                      method='MLE',
                      ic=False):

        q = self.get_q_from_T(return_periods, season, law, method, ic)

        if '.csv' in filename:
            q.to_csv(filename, sep=";")
        elif '.xlsx' in filename:
            q.to_excel(filename)
        else:
            q.to_excel('q_from_t.xlsx')

    def save_T_from_q(self,
                      filename:str='',
                      q=[5,10,15,20,25,50,75,100,200,500,1000],
                      season='best',
                      law='best',
                      method='MLE',
                      ic=False):

        rp = self.get_T_from_q(q, season, law, method, ic)

        if '.csv' in filename:
            rp.to_csv(filename)
        elif '.xlsx' in filename:
            rp.to_excel(filename)
        else:
            rp.to_excel('q_from_t.xlsx')

    def fit(self, seasons=None, laws=['GEV'], init_EVA=None, methods=['MLE'], ic=False, nboot=100, verbose=True):
        """
        Fitting of selected laws
        """
        seasons = sanitize_seasons(seasons)

        if laws == 'popular':
            laws = LAWS_POPULAR
        elif isinstance(laws,str):
            laws=[laws]

        for curseason in seasons:

            data = self.maxima[curseason]['maxval']

            if not 'fit' in self.maxima[curseason].keys():
               self.maxima[curseason]['fit']={}

            curdict = self.maxima[curseason]['fit']

            for curmethod in methods:
                if not curmethod in curdict.keys():
                    curdict[curmethod]={}
                curdictm = curdict[curmethod]

                for curlaw in laws:
                    if not curlaw in curdictm.keys():
                        curdictm[curlaw]={}
                    resdict = curdictm[curlaw]

                    if curlaw in dists_2params.keys():
                        val = dists_2params[curlaw]

                        if verbose:
                            print(self.duration,curseason,curlaw,curmethod)

                        dist:stats.rv_continuous
                        dist, color, nb =val

                        resini = None
                        if init_EVA is not None:
                            resini = init_EVA.get_fitted_params(curseason, curlaw, curmethod)

                        mle,res = self._fit_multistarts(data,(dist,resini),nb,curmethod)
                        resdict['mle']=mle
                        resdict['params']=res
                        resdict['func']=dist(loc=res[0],scale=res[1])

                        resdict['aic'] = aic(mle,len(data),2,False)
                        resdict['aicc'] = aic(mle,len(data),2,True)
                        resdict['bic'] = bic(mle,len(data),2)
                        resdict['rss'] = rss(data,resdict['func'].pdf)
                        resdict['color'] = color

                        if ic:
                            resdict['ic'] = self._evaluate_ci(data,(dist,res),nboot,curmethod)

                    elif curlaw in dists_3params.keys():
                        val = dists_3params[curlaw]

                        if verbose:
                            print(self.duration,curseason,curlaw,curmethod)

                        dist:stats.rv_continuous
                        dist, color, nb =val
                        try:

                            resini = None
                            if init_EVA is not None:
                                resini = init_EVA.get_fitted_params(curseason, curlaw, curmethod)

                            mle,res = self._fit_multistarts(data,(dist,resini),nb,curmethod)
                            resdict['mle']=mle
                            resdict['params']=res
                            resdict['func']=dist(res[0],loc=res[1],scale=res[2])

                            resdict['aic'] = aic(mle,len(data),3,False)
                            resdict['aicc'] = aic(mle,len(data),3,True)
                            resdict['bic'] = bic(mle,len(data),3)
                            resdict['rss'] = rss(data,resdict['func'].pdf)
                            resdict['color'] = color

                            if ic:
                                resdict['ic'] = self._evaluate_ci(data,(dist,res),nboot,curmethod)
                        except:
                            pass
                    elif curlaw in dists_4params.keys():
                        val = dists_4params[curlaw]

                        if verbose:
                            print(self.duration,curseason,curlaw,curmethod)

                        dist:stats.rv_continuous
                        dist, color, nb =val
                        try:

                            resini = None
                            if init_EVA is not None:
                                resini = init_EVA.get_fitted_params(curseason, curlaw, curmethod)

                            mle,res = self._fit_multistarts(data,(dist,resini),nb,curmethod)
                            resdict['mle']=mle
                            resdict['params']=res
                            resdict['func']=dist(loc=res[2],scale=res[3],*res[0:2])

                            resdict['aic'] = aic(mle,len(data),4,False)
                            resdict['aicc'] = aic(mle,len(data),4,True)
                            resdict['bic'] = bic(mle,len(data),4)
                            resdict['rss'] = rss(data,resdict['func'].pdf)
                            resdict['color'] = color

                            if ic:
                                resdict['ic'] = self._evaluate_ci(data,(dist,res),nboot,curmethod)
                        except:
                            pass

    def select_best_func(self, season, law, method):
        """
        Select one function as best fit
        """
        try:
            self.best = self.maxima[season]['fit'][method][law]['func']
        except:
            self.best = None

    def distfit(self, seasons=None, laws='popular', smooth=0, bins=100):
        """
        Laws can be 'full', 'popular'

        ***
        Be carefull, fit of law is based on default scipy.stats parames. In our implementation, non-default initial conditions are used for specific laws, including GEV.
        ***

        https://erdogant.github.io/distfit/pages/html/Parametric.html
        https://erdogant.github.io/distfit
        """

        seasons = sanitize_seasons(seasons)

        for curseason in seasons:

            data = self.maxima[curseason]['maxval']

            if not 'distfit' in self.maxima[curseason].keys():
               self.maxima[curseason]['distfit']={}

            curdict = self.maxima[curseason]['distfit']

            if smooth>0:
                curdict['func'] = dist = distfit(distr=laws,smooth=smooth, bins=bins)  # Initialize
            else:
                curdict['func'] = dist = distfit(distr=laws, bins=bins)  # Initialize

            dist.fit_transform(data)                    # Fit distributions on empirical data X

    def set_mixture(self, laws=['GEV'], methods=['MLE']):
        """
        Set mixture model based on "50-50" "winter-summer" fitted models
        """
        if laws == 'popular':
            laws = LAWS_POPULAR
        elif isinstance(laws,str):
            laws=[laws]

        for curmethod in methods:
            if ('winter' in self.maxima.keys()) and ('summer' in self.maxima.keys()):
                if ('fit' in self.maxima['winter'].keys()) and ('fit' in self.maxima['summer'].keys()):
                    if (curmethod in self.maxima['winter']['fit'].keys()) and (curmethod in self.maxima['summer']['fit'].keys()):

                        dict_mix = self.maxima['mixture'] = {}
                        dict_mixf = dict_mix['fit'] = {}
                        dict_mixm = dict_mixf[curmethod] = {}

                        dictm_w = self.maxima['winter']['fit'][curmethod]
                        dictm_s = self.maxima['summer']['fit'][curmethod]

                        for curlaw in laws:
                            if (curlaw in dictm_w.keys()) and (curlaw in dictm_s.keys()):
                                if ('func' in dictm_w[curlaw].keys()) and ('func' in dictm_s[curlaw].keys()):
                                    func_w = dictm_w[curlaw]['func']
                                    func_s = dictm_s[curlaw]['func']

                                    dict_mixr = dict_mixm[curlaw] = {}

                                    dict_mixr['func'] = SeasonMixtureModel([func_w,func_s],[0.5,0.5])
                                    dict_mixr['color'] = 'k'
                                else:
                                    print('The desired law {} is not fitted for all seasons'.format(curlaw))
                    else:
                        raise Warning('Fit winter and summer before set_mixture')

    def set_joint(self, laws=['GEV'], methods=['MLE']):
        """
        Set joint model based on product probability of fitted models
        """
        if laws == 'popular':
            laws = LAWS_POPULAR
        elif isinstance(laws,str):
            laws=[laws]

        for curmethod in methods:
            if ('winter' in self.maxima.keys()) and ('summer' in self.maxima.keys()):
                if ('fit' in self.maxima['winter'].keys()) and ('fit' in self.maxima['summer'].keys()):
                    if (curmethod in self.maxima['winter']['fit'].keys()) and (curmethod in self.maxima['summer']['fit'].keys()):

                        dict_mix = self.maxima['joint'] = {}
                        dict_mixf = dict_mix['fit'] = {}
                        dict_mixm = dict_mixf[curmethod] = {}

                        dictm_w = self.maxima['winter']['fit'][curmethod]
                        dictm_s = self.maxima['summer']['fit'][curmethod]

                        for curlaw in laws:
                            if (curlaw in dictm_w.keys()) and (curlaw in dictm_s.keys()):
                                if ('func' in dictm_w[curlaw].keys()) and ('func' in dictm_s[curlaw].keys()):
                                    func_w = dictm_w[curlaw]['func']
                                    func_s = dictm_s[curlaw]['func']

                                    dict_mixr = dict_mixm[curlaw] = {}

                                    dict_mixr['func'] = JointModel([func_w,func_s])
                                    dict_mixr['color'] = 'k'
                                else:
                                    print('The desired law {} is not fitted for all seasons'.format(curlaw))
                    else:
                        raise Warning('Fit winter and summer before set_joint')

    def set_empfreq(self, seasons=None):
        """
        Compute empirical frequency based on sorted maxima
        """
        seasons = sanitize_seasons(seasons)

        for curseason in seasons:
            if not 'sorted_maxval' in self.maxima[curseason].keys():
                self.sort_maxima(curseason)

            nb = len(self.maxima[curseason]['maxval'])
            curdict=self.maxima[curseason]['Empirical_frequency']={}
            curdict['Cunnane'] = np.asarray([cunnane(i+1,nb) for i in range(nb)])
            curdict['Weibull'] = np.asarray([weibull(i+1,nb) for i in range(nb)])
            curdict['Filliben'] = np.asarray([filliben(i+1,nb) for i in range(nb)])

    def compute_median_event(self, seasons = None, before:int = 1, after:int = 2):
        """
        Evaluation de la crue mediane
        Stockage dans "self.maxima[curseason]['median_event']"
        """
        seasons = sanitize_seasons(seasons)

        nbmax=0
        for curseason in seasons:

            if not 'events' in self.maxima[curseason].keys():
                self.extract_maxevents(before,after)
            elif (self.maxima[curseason]['before'] != before) or (self.maxima[curseason]['after'] != after):
                self.extract_maxevents(before,after)

            curdict = self.maxima[curseason]['events']
            dates   = self.maxima[curseason]['date']

            all_adims = {}
            for idx in np.arange((before+after)*24+1, dtype=np.int16):
                all_adims[idx]=[]

            for idx,(key,curevent) in enumerate(curdict.items()):
                nb    = len(curevent)
                nbmax = max(nb,nbmax)

                mymax  = np.max(curevent)
                values = curevent.copy()/mymax

                if nb != (before+after)*24+1:
                    x = np.zeros(nb)
                    for curidx, curdelta in enumerate(values.index):
                        curhour = int(((curdelta-dates[idx]).days *24)+((curdelta-dates[idx]).seconds)/3600) + before*24
                        x[curidx] = curhour
                        all_adims[curhour].append(values[curidx])
                else:
                    x = np.arange((before+after)*24+1, dtype=np.int16)
                    for curidx, curq in enumerate(values):
                        all_adims[curidx].append(curq)

            time= np.arange((before+after)*24+1, dtype=np.int16)
            crue_mediane = [np.median(curval) for curval in all_adims.values()]
            self.maxima[curseason]['median_event'] = pd.DataFrame({'time [hour]':time, 'Discharge[m3s-1]':crue_mediane})

    def get_median_event(self, seasons = None, before=1, after=2)-> dict[str, pd.DataFrame]:
        """
        Get median hydrograph
        """

        seasons = sanitize_seasons(seasons)

        retdict = {}
        for cur in seasons:
            # if not 'median_event' in self.maxima[cur].keys():
            self.compute_median_event(seasons, before, after)

            retdict[cur] = self.maxima[cur]['median_event']

        return retdict

    def plot_median_event(self,
                          scale:float,
                          seasons = None,
                          before=1,
                          after=2,
                          fig:Figure=None,
                          ax:Axes=None,
                          color:str='red',
                          alpha=1.) -> tuple[Figure,Axes]:
        """
        Plot median hydrograph scale by constant
        """

        seasons = sanitize_seasons(seasons)

        if fig is None and ax is None:
            fig,ax = plt.subplots(len(seasons),1)

        qmedian = self.get_median_event(seasons, before, after)

        k=0
        for curseason in seasons:
            if len(seasons)==1:
                curax=ax
            else:
                curax=ax[k]

            x = qmedian[curseason]['time [hour]']
            crue_mediane = qmedian[curseason]['Discharge[m3s-1]'].copy() * scale

            curax.step(x,crue_mediane,where='post', c=color, alpha=alpha, lw=2, label = "Median")

            k+=1


    def plot_classified_flowrate_curve(self, fig:Figure=None, ax:Axes=None, label='', textvalues=True, show=False) -> tuple[Figure,Axes, dict]:
        """
        Plot classified flow rate curve.

        Characteristics returned in dict are:
            - DCE : Débit journalier dépassé en moyenne 355 jours par an
            - DC10 : Débit journalier dépassé en moyenne 10 mois par an
            - Q347 : Débit atteint ou dépassé, en moyenne, pendant 347 jours par an
            - DM : Débit atteint ou dépassé, en moyenne, pendant 50% du temps - débit médian
            - DCC : Débit journalier qui est dépassé 10 jours par an

        Previous lines are keys of characteristics dict.

        Each characteristic is a dict with:
        - 'help' : explanation of characteristic
        - 'x' : number of days with exceedance
        - 'value' : discharge value

        :param fig: Matplotlib figure
        :param ax: Matplotlib axis
        :param label: label for the curve
        :param textvalues: if True, text of characteristics are added
        :param show: if True, plt.show() is called
        :return: fig, ax, resdict
        """
        if ax is None:
            fig,ax = plt.subplots(1,1)

        sorteddata = self.data[~(np.isnan(self.data))].copy().sort_values()
        nb = len(sorteddata)
        f = (np.arange(nb)+1)/nb

        resdict = {}

        resdict['mean discharge'] = sorteddata.to_numpy(copy=True)
        resdict['duration'] = self.duration
        resdict['frequency of non exceedance'] = f
        resdict['frequency of exceedance'] = 1-f

        chardict = resdict['characteristics'] = {}

        f = (1-f)*365

        curdict = chardict['DCE'] = {}
        curdict['help'] = 'Débit journalier dépassé en moyenne 355 jours par an'
        curdict['x'] = 355
        curdict['value'] = np.quantile(sorteddata, 1-355/365)

        curdict = chardict['DC10'] = {}
        curdict['help'] = 'Débit journalier dépassé en moyenne 10 mois par an'
        curdict['x'] = 300
        curdict['value'] = np.quantile(sorteddata, 1-300/365)

        curdict = chardict['Q347'] = {}
        curdict['help'] = 'Débit atteint ou dépassé, en moyenne, pendant 347 jours par an'
        curdict['x'] = 347
        curdict['value'] = np.quantile(sorteddata, 1-347/365)

        curdict = chardict['DM'] = {}
        curdict['help'] = 'Débit atteint ou dépassé, en moyenne, pendant 50% du temps - débit médian'
        curdict['x'] = .5*365
        curdict['value'] = np.quantile(sorteddata, .5)

        curdict = chardict['DCC'] = {}
        curdict['x'] = 10
        curdict['help'] = 'Débit journalier qui est dépassé 10 jours par an'
        curdict['value'] = np.quantile(sorteddata, 1- 10/365)

        if label != '':
            ax.plot(f,sorteddata, label=label)
            ax.legend()
        else:
            ax.plot(f,sorteddata)

        ax.set_xlabel('Number of days with exceedance [days]')
        ax.set_ylabel('Discharge [$m^3s^{-1}]')
        ax.set_title('Classified flow rates curve')

        ax.set_xbound(0,365)
        ax.set_ybound(0,sorteddata.max())

        # used = ['DCE', 'DC10','Q347', 'DM', 'DCC']
        # unused = ['mean discharge','duration', 'frequency of non exceedance','frequency of exceedance','characteristics' ]

        if textvalues:
            for idx,(key,value) in enumerate(chardict.items()):
                ax.plot([value['x'],value['x']], [0, value['value']], 'k--')
                ax.text(value['x'], value['value']*1.05, '{0} : {1:.2f}'.format(key,value['value']), rotation=90)

        valsx= np.hstack((np.arange(365, step=30), 365))
        ax.set_xticks(valsx)
        ax.set_xticklabels(valsx)

        valsy= np.unique(sorted(np.hstack((np.arange(sorteddata.max(), step=25), sorteddata.max(), [curdict['value'] for curdict in chardict.values()]))))
        ax.set_yticks(valsy)
        ax.set_yticklabels(valsy)
        ax.set_yscale('log')

        ax.grid()

        if show:
            plt.show()

        return fig, ax, resdict

    def plot_distfit(self, seasons=None, n_top=20, show=False):
        """
        Plots of distfit module
        """
        seasons = sanitize_seasons(seasons)

        for curseason in seasons:

            if not 'distfit' in self.maxima[curseason].keys():
                self.distfit(curseason)

            curdict = self.maxima[curseason]['distfit']
            dist = curdict['func']

            fig,ax=dist.plot()             # Plot the best fitted distribution (y is included if prediction is made)
            fig,ax=dist.plot_summary(n_top=n_top)

            if show:
                plt.show()

    def plot_ci(self, seasons=None, laws=['GEV'], methods=['MLE'], fig:Figure=None, ax:Axes=None, show=False, alpha=.1) -> tuple[Figure,Axes]:
        """
        Plotting confidence interval
        """
        if laws == 'popular':
            laws = LAWS_POPULAR
        elif isinstance(laws,str):
            laws=[laws]

        if fig is None and ax is None:
            fig,ax = plt.subplots(1,1)

        colors = ['r', 'g', 'b', 'r--', 'g--', 'b--']

        seasons = sanitize_seasons(seasons)

        ax.set_xscale('log')
        ax.set_xlim([1,1000])
        ax.set_xticks([1,2,5,10,15,25,50,100,1000])
        ax.set_xticklabels([1,2,5,10,15,25,50,100,1000])
        ax.set_ylabel('Discharge [$m^3s^{-1}$]')
        ax.set_xlabel('Return period [year]')
        ax.grid(True)

        for curseason in seasons:
            for curmethod in methods:
                if curmethod in self.maxima[curseason]['fit'].keys():
                    dictm = self.maxima[curseason]['fit'][curmethod]
                    for curlaw in laws:
                        if curlaw in dictm.keys():
                            dictlaw = dictm[curlaw]
                            if 'ic' in dictlaw.keys():
                                dictic_sup = dictlaw['ic']['sup']
                                dictic_inf = dictlaw['ic']['inf']

                                for idx, curic in enumerate(dictic_inf):
                                    c_inf = dictic_inf[curic]
                                    c_sup = dictic_sup[curic]

                                    ax.plot(RETURN_PERIOD_ESTIMATE, c_inf, 'k', lw=3, alpha=min(alpha*idx+.1,1), label='c_inf_{}%'.format(curic))
                                    ax.plot(RETURN_PERIOD_ESTIMATE, c_sup, 'k', lw=3, alpha=min(alpha*idx+.1,1), label='c_sup_{}%'.format(curic))
                                    # ax.scatter(RETURN_PERIOD_ESTIMATE, c_inf)
                                    # ax.scatter(RETURN_PERIOD_ESTIMATE, c_sup)

        ax.legend()
        plt.tight_layout()

        if show:
            plt.show()

        return (fig,ax)

    def plot_annual(self, years=None, hydrol=True, fig:Figure=None, ax:Axes=None, show=False, withdatemax=True) -> tuple[Figure,Axes]:
        """
        Tracé en superposition des différentes années sur l'emprise d'une année civile ou hydrologique
        """
        if fig is None and ax is None:
            fig,ax = plt.subplots(1,1)

        if years is None:
            years = range(self.years_bounds[0],self.years_bounds[1]+1)

        delta = 0
        if hydrol:
            delta = (dt(2021,1,1, tzinfo=self.tz_info)-dt(2020,10,1, tzinfo=self.tz_info))

        for curyear in years:
            start_date, end_date = self._get_dates(curyear, hydrol)

            df = self.data[(self.data.index>=start_date) & (self.data.index<end_date)].copy()
            if hydrol:
                df.index = df.index + delta

            ax.step(df.index.day_of_year*24 + df.index.hour,df,where='post',c='black',alpha=.2)

        for curdata, curcolor, cursymb in zip(SEASONS,SEASONS_COLORS,SEASONS_MARKERS):
            curdate = self.maxima[curdata]['serie'].index.copy() + delta
            ax.scatter(curdate.day_of_year*24 + curdate.hour,
                        self.maxima[curdata]['maxval'],
                        marker = cursymb,
                        c=curcolor,label=curdata)

        if withdatemax:
            curdate = self.maxima['annual']['serie'].index.copy() + delta
            txt = [str(cur) for cur in curdate.year]
            x = np.asarray(curdate.day_of_year*24 + curdate.hour)
            if np.max(self.maxima['annual']['maxval'])>100:
                y = self.maxima['annual']['maxval']+5
            else:
                y = self.maxima['annual']['maxval']+.5
            for curx,cury,curtxt in zip(x,y,txt):
                ax.text(curx,cury,curtxt,rotation=90)

        ax.set_xlabel('Date')
        ax.set_ylabel('Discharge [$ m^3s^{-1} $]')

        if hydrol:
            days = [0,31,30,31,31,28,31,30,31,30,31,31]
            ticks_pos = np.cumsum(days)*24
            ticks_labels = ['Oct','Nov','Dec','Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep']
        else:
            days = [0,31,28,31,30,31,30,31,31,30,31,30]
            ticks_pos = np.cumsum(days)*24
            ticks_labels = ['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec']
        ax.set_xticks(ticks_pos)
        ax.set_xticklabels(ticks_labels)
        ax.set_title('Duration {} h'.format(self.duration))

        ax.legend()
        fig.tight_layout()

        if show:
            plt.show()

        return (fig,ax)

    def plot_serie(self, fig:Figure=None, ax:Axes=None, show=False, background=True, backcolor='lemonchiffon') -> tuple[Figure,Axes]:
        """Tracé de l'ensemble de la série pour toutes les années"""
        if fig is None and ax is None:
            fig,ax = plt.subplots(1,1)

        ax.step(self.data.index,self.data,where='post')
        for curdata, curcolor, cursymb in zip(SEASONS,SEASONS_COLORS,SEASONS_MARKERS):
            ax.scatter(self.maxima[curdata]['date'],self.maxima[curdata]['maxval'],marker = cursymb,c=curcolor,label=curdata)

        ax.set_xlabel('Date')
        ax.set_ylabel('Discharge [$ m^3s^{-1} $]')
        ax.legend()
        ax.set_title('Duration {} h'.format(self.duration))

        if background:
            for curyear in range(self.years_bounds[0], self.years_bounds[1]+1):
                ax.add_patch(  Rectangle((dt(curyear,self.startmonth_summer,1),ax.get_ybound()[0]),
                                         width=dt(curyear,self.startmonth_winter,1)-dt(curyear,self.startmonth_summer,1),
                                         height=ax.get_ybound()[1]-ax.get_ybound()[0],
                                         color=backcolor,
                                         zorder=0))

        if show:
            plt.show()

        return (fig,ax)

    def plot_cdf(self, seasons=None, fig:Figure=None, ax:Axes=None, show=False, n_bins=100) -> tuple[Figure,Axes]:
        """
        Plotting empirical cdf
        """

        if fig is None and ax is None:
            fig,ax = plt.subplots(1,1)

        seasons = sanitize_seasons(seasons)

        for curseason in seasons:
            values = self.maxima[curseason]['maxval'].copy()
            n, bins, patches = ax.hist(values, n_bins, density=True, histtype='step',
                                    cumulative=True, label='Empirical - '+curseason)

        ax.grid(True)
        ax.legend(loc='right')
        ax.set_title('Cumulative step histograms')
        ax.set_xlabel('Discharge [$m^3s^{-1}$]')
        ax.set_ylabel('Likelihood of occurrence')
        ax.set_title('Duration {} h'.format(self.duration))

        if show:
            plt.show()

        return (fig,ax)

    def plot_T_Qmaxima(self, seasons=None, empirical_func='Cunnane', fig:Figure=None, ax:Axes=None, show=False, alpha=1., color_marker_label=None) -> tuple[Figure,Axes]:
        """
        Plotting Q vs return period
        """

        if fig is None and ax is None:
            fig,ax = plt.subplots(1,1)

        seasons = sanitize_seasons(seasons, True)

        k=0
        if seasons == ['mixture'] or seasons == ['joint']:
            for curseason in SEASONS:
                if not 'sorted_maxval' in self.maxima[curseason].keys():
                    self.sort_maxima(curseason)
                    self.set_empfreq(curseason)

                p_emp = self.maxima[curseason]['Empirical_frequency'][empirical_func]
                y = self.maxima[curseason]['sorted_maxval']
                T_emp = 1/(1-p_emp)

                if color_marker_label is not None:
                    curcolor, curmark, curlab = color_marker_label
                    ax.scatter(T_emp,y,marker=curmark,c=curcolor,label=curlab, alpha=alpha)
                else:
                    ax.scatter(T_emp,y,marker=SEASONS_MARKERS[k],c=SEASONS_COLORS[k],label=curseason +' - '+str(self.duration), alpha=alpha)
                k+=1
        else:
            for curseason in seasons:
                if curseason != 'mixture' and curseason != 'joint':

                    if len(self.maxima.keys())==0:
                        self.find_maxima()

                    if not 'sorted_maxval' in self.maxima[curseason].keys():
                        self.sort_maxima(curseason)
                        self.set_empfreq(curseason)

                    p_emp = self.maxima[curseason]['Empirical_frequency'][empirical_func]
                    y = self.maxima[curseason]['sorted_maxval']
                    T_emp = 1./(1.-p_emp)

                    if color_marker_label is not None:
                        curcolor, curmark, curlab = color_marker_label
                        ax.scatter(T_emp,y,marker=curmark,c=curcolor,label=curlab, alpha=alpha)
                    else:
                        ax.scatter(T_emp,y,marker=SEASONS_MARKERS[k],c=SEASONS_COLORS[k],label=curseason +' - '+str(self.duration), alpha=alpha)
                    k+=1

        ax.set_xscale('log')
        ax.set_xticks([1,2,5,10,15,25,50,100,1000])
        ax.set_xticklabels([1,2,5,10,15,25,50,100,1000])
        ax.set_ylabel('Discharge [$m^3s^{-1}$]')
        ax.set_xlabel('Return period [year]')
        ax.grid(True)
        ax.set_title('T-Q relation (Emp. freq. estimator : {})'.format(empirical_func) )
        ax.legend()

        if show:
            plt.show()

        return (fig,ax)

    def plot_maxevents(self, seasons=None, before=1, after=2, adim=True, fig:Figure=None, ax:Axes=None, show=False, alpha=.2, nbevents=None) -> tuple[Figure,Axes]:
        """
        Tracé des événements/hydrogrammes associés aux maxima identifiés
        Les ordonnées sont adimensionnaliées sur base de la valeur maximale
        """
        seasons = sanitize_seasons(seasons)
        colors = ['black'] * len(seasons)

        if fig is None and ax is None:
            fig,ax = plt.subplots(len(seasons),1)

        self.compute_median_event(seasons, before, after)

        nbmax=0
        k=0
        for curseason in seasons:

            if not 'events' in self.maxima[curseason].keys():
                self.extract_maxevents(before,after)
            elif (self.maxima[curseason]['before'] != before) or (self.maxima[curseason]['after'] != after):
                self.extract_maxevents(before,after)

            if len(seasons)==1:
                curax=ax
            else:
                curax=ax[k]

            curdict = self.maxima[curseason]['events']
            dates = self.maxima[curseason]['date']

            if nbevents is not None:
                locmax = self.maxima[curseason]['maxval'].copy()
                locmax = np.sort(locmax)
                locmax = list(locmax[-nbevents:])

            all_adims = {}
            for idx in np.arange((before+after)*24+1, dtype=np.int16):
                all_adims[idx]=[]

            for idx,(key,curevent) in enumerate(curdict.items()):
                nb    = len(curevent)
                nbmax = max(nb,nbmax)

                mymax = np.max(curevent)
                if adim:
                    values = curevent.copy()/mymax
                else:
                    values = curevent

                if nb != (before+after)*24+1:
                    x = np.zeros(nb)
                    for curidx, curdelta in enumerate(values.index):
                        curhour = int(((curdelta-dates[idx]).days *24)+((curdelta-dates[idx]).seconds)/3600) + before*24
                        x[curidx] = curhour
                        all_adims[curhour].append(values[curidx])
                else:
                    x = np.arange((before+after)*24+1, dtype=np.int16)
                    for curidx, curq in enumerate(values):
                        all_adims[curidx].append(curq)

                if nbevents is None:
                    curax.step(x,values,where='post',alpha=alpha,c=colors[k], label = dates[idx].strftime("%m/%Y"))
                elif mymax in locmax:
                    curax.step(x,values,where='post',alpha=alpha,c=colors[k], label = dates[idx].strftime("%m/%Y"))
                    print(dates[idx].strftime("%m/%Y"), mymax)

            if adim:
                x = self.maxima[curseason]['median_event']['time [hour]']
                crue_mediane = self.maxima[curseason]['median_event']['Discharge[m3s-1]']
                curax.step(x,crue_mediane,where='post',alpha=1., c=colors[k], lw=2, label = "Median")

            curax.set_xticks(np.arange(0, (before+after)*24+1, 6, dtype=np.int16))
            curax.set_xticklabels(np.arange(0, (before+after)*24+1, 6, dtype=np.int16))
            curax.grid(True)

            curax.set_title('Maxima events - duration : {} - {}'.format(self.duration,curseason))
            curax.set_xlabel('Time [hour]')

            if adim:
                curax.set_ylabel('Discharge / DisMax [-]')
            else:
                curax.set_ylabel('Discharge [$m^3s^{-1}$]')
            curax.set_xbound(0,(before+after)*24+1)
            k+=1

        plt.tight_layout()

        if show:
            plt.show()

        return (fig,ax)

    def plot_comp_maxevents(self, seasons=None, before=1, after=2, fig:Figure=None, ax:Axes=None, show=False, alpha=.2, nbevents=None) -> tuple[Figure,Axes]:
        """
        Tracé des événements médians
        Les ordonnées sont adimensionnaliées sur base de la valeur maximale
        """
        seasons = sanitize_seasons(seasons)
        colors = ['red', 'green', 'blue']

        if fig is None and ax is None:
            fig,ax = plt.subplots(1,1)

        nbmax=0
        k=0
        for curseason in seasons:

            if not 'events' in self.maxima[curseason].keys():
                self.extract_maxevents(before,after)
            elif (self.maxima[curseason]['before'] != before) or (self.maxima[curseason]['after'] != after):
                self.extract_maxevents(before,after)

            curax=ax

            curdict = self.maxima[curseason]['events']
            dates = self.maxima[curseason]['date']

            all_adims = {}
            for idx in np.arange((before+after)*24+1, dtype=np.int16):
                all_adims[idx]=[]

            if nbevents is not None:
                locmax = self.maxima[curseason]['maxval'].copy()
                locmax = np.sort(locmax)
                locmax = list(locmax[-nbevents:])

            for idx,(key,curevent) in enumerate(curdict.items()):
                nb=len(curevent)
                nbmax=max(nb,nbmax)

                mymax = np.max(curevent)
                values = curevent.copy()/mymax

                if nb != (before+after)*24+1:
                    x = np.zeros(nb)
                    for curidx, curdelta in enumerate(values.index):
                        curhour = int(((curdelta-dates[idx]).days *24)+((curdelta-dates[idx]).seconds)/3600) + before*24
                        x[curidx] = curhour
                        all_adims[curhour].append(values[curidx])
                else:
                    x = np.arange((before+after)*24+1, dtype=np.int16)
                    for curidx, curq in enumerate(values):
                        all_adims[curidx].append(curq)

                # if nbevents is None:
                #     curax.step(x,values,where='post',alpha=alpha,c=colors[k], label = dates[idx].strftime("%m/%Y"))
                # elif mymax in locmax:
                #     curax.step(x,values,where='post',alpha=alpha,c=colors[k], label = dates[idx].strftime("%m/%Y"))

            x = np.arange((before+after)*24+1, dtype=np.int16)
            crue_mediane = [np.median(curval) for curval in all_adims.values()]
            curax.step(x,crue_mediane,where='post',alpha=1., c=colors[k], lw=2, label = 'MedianQ {}'.format(curseason))

            self.maxima[curseason]['median_event'] = pd.DataFrame({'time [hour]':x, 'Discharge[m3s-1]':crue_mediane})

            curax.set_xticks(np.arange(0, (before+after)*24+1, 6, dtype=np.int16))
            curax.set_xticklabels(np.arange(0, (before+after)*24+1, 6, dtype=np.int16))
            curax.grid(True)

            curax.set_title('Maxima events - duration : {} - {}'.format(self.duration,curseason))
            curax.set_xlabel('Time [hour]')
            curax.set_ylabel('Discharge / DisMax [-]')
            curax.set_xbound(0,(before+after)*24+1)
            k+=1

        plt.tight_layout()

        if show:
            plt.show()

        return (fig,ax)

    def plot_one_event(self,
                       datecenter,
                       before=1,
                       after=2,
                       adim=True,
                       color='k',
                       fig:Figure=None,
                       ax:Axes=None,
                       show=False,
                       alpha=.2) -> tuple[Figure,Axes]:
        """
        Tracé d'un événement quelconque autour d'une date
        """
        if fig is None and ax is None:
            fig,ax = plt.subplots(1,1)
            ax.set_title('Event - duration : {} - {}'.format(self.duration, 'data source'))

        curevent = self.extract_oneevent(datecenter,before,after)

        nb=len(curevent)
        x = np.arange(nb)

        if adim:
            values = curevent.copy()/np.max(curevent)
            ax.set_ylabel('Discharge / DisMax [-]')
        else:
            values = curevent
            ax.set_ylabel('Discharge [$m^3s^{-1}$]')

        ax.step(x,values,where='post',alpha=alpha,c=color, label = datecenter.strftime("%m/%Y"))

        ax.set_xticks(np.arange(0,nb,6))
        ax.set_xticklabels(np.arange(0,nb,6))
        ax.grid(True)
        ax.legend()
        ax.set_xlabel('Time [hour]')
        ax.set_xbound(0,nb)

        if show:
            plt.show()

        return (fig,ax)

    def plot_one_maxevents(self,
                           season,
                           year,
                           before=1,
                           after=2,
                           adim=True,
                           color='k',
                           fig:Figure=None,
                           ax:Axes=None,
                           show=False,
                           alpha=.2) -> tuple[Figure,Axes]:
        """
        Tracé d'un événement spécifique associés au maxima identifié
        Les ordonnées sont adimensionnaliées sur base de la valeur maximale
        """
        if fig is None and ax is None:
            fig,ax = plt.subplots(1,1)
            ax.set_title('Events - duration : {} - {}'.format(self.duration,season))

        if not 'events' in self.maxima[season].keys():
            self.extract_maxevents(before,after)
        elif (self.maxima[season]['before'] != before) or (self.maxima[season]['after'] != after):
            self.extract_maxevents(before,after)

        idx = self.maxima[season]['water_year'].index(dt(year,1,1, tzinfo=self.tz_info))
        curevent = self.maxima[season]['events'][year]
        date = self.maxima[season]['date'][idx]

        nb=len(curevent)
        x = np.arange(nb)

        if adim:
            values = curevent.copy()/np.max(curevent)
            ax.set_ylabel('Discharge / DisMax [-]')
        else:
            values = curevent
            ax.set_ylabel('Discharge [$m^3s^{-1}$]')

        ax.step(x,values,where='post',alpha=alpha,c=color, label = date.strftime("%m/%Y"))

        ax.set_xticks(np.arange(0,nb,6))
        ax.set_xticklabels(np.arange(0,nb,6))
        ax.grid(True)
        ax.legend()
        ax.set_xlabel('Time [hour]')
        ax.set_xbound(0,nb)

        if show:
            plt.show()

        return (fig,ax)

    def plot_fit(self,
                 seasons=None,
                 laws=['GEV'],
                 methods=['MLE'],
                 fig:Figure=None,
                 ax:Axes=None,
                 show=False,
                 alpha=1.,
                 styles:dict=None) -> tuple[Figure,Axes]:
        """
        Plotting fitted models
        """

        ## Périodes de retour et fréquences
        if laws == 'popular':
            laws = LAWS_POPULAR
        elif isinstance(laws,str):
            laws=[laws]

        if fig is None and ax is None:
            fig,ax = plt.subplots(1,1)

        colors = ['r', 'g', 'b']*20
        linestyles = ['solid', 'solid', 'solid', 'dashed', 'dashed', 'dashed'] *10
        seasons = sanitize_seasons(seasons, True)

        # où doit-on estimer la fonction?
        data = self.maxima['annual']['maxval']
        Q = np.asarray([(x*((np.max(data)*1.5-np.min(data))/100)+np.min(data)) for x in range(100)])

        oldcolor = colors[0]
        oldstyle = linestyles[0]
        for idx,curseason in enumerate(seasons):
            for curmethod in methods:
                if curmethod in self.maxima[curseason]['fit'].keys():
                    dictm = self.maxima[curseason]['fit'][curmethod]
                    for curlaw in laws:
                        if curlaw in dictm.keys():
                            dist = dictm[curlaw]['func']

                            if len(laws)==1:

                                if styles is not None :
                                    if curseason in styles.keys():
                                        curcolor, curlinestyle, curlinewidth = get_style(styles[curseason])
                                    else:
                                        curcolor, curlinestyle, curlinewidth = get_style(styles)
                                else:
                                    k=idx
                                    curcolor = colors[k]
                                    curlinestyle = linestyles[k]
                                    while curcolor == oldcolor or curlinestyle == oldstyle:
                                        k+=1
                                        curcolor = colors[k]
                                        curlinestyle = linestyles[k]

                                    oldcolor = curcolor
                                    oldstyle = curlinestyle

                                    curlinewidth = 2

                                ax.plot(1/(1-dist.cdf(Q)),Q,
                                        curcolor,
                                        linestyle=curlinestyle,
                                        lw=curlinewidth,
                                        alpha=alpha,
                                        label='{} - {} - {}h'.format(curlaw,curseason,self.duration))
                            else:
                                if styles is not None :
                                    if curseason in styles.keys():
                                        curcolor, curlinestyle, curlinewidth = get_style(styles[curseason])
                                    else:
                                        curcolor, curlinestyle, curlinewidth = get_style(styles)
                                else:
                                    curcolor = dictm[curlaw]['color']
                                    curlinewidth = 2
                                    if not '--' in curcolor:
                                        curlinestyle='solid'
                                    else:
                                        curlinestyle='--'

                                ax.plot(1/(1-dist.cdf(Q)),Q,
                                        curcolor,
                                        linestyle=curlinestyle,
                                        lw=curlinewidth,
                                        alpha=alpha,
                                        label=curlaw+' - '+curseason )

        ax.set_xscale('log')
        ax.set_xlim([1,1000])
        ax.set_xticks([1,2,5,10,15,25,50,100,1000])
        ax.set_xticklabels([1,2,5,10,15,25,50,100,1000])
        ax.set_ylabel('Discharge [$m^3s^{-1}$]')
        ax.set_xlabel('Return period [year]')
        ax.grid(True)
        ax.legend()

        if show:
            plt.show()

        return (fig,ax)

    def plot_qq(self, seasons=None, laws=['GEV'], methods=['MLE'], fig:Figure=None, ax:Axes=None) -> tuple[Figure,Axes]:
        """
        Q-Q Plot

        Comparaison de la valeur théorique avec la mesure (attention scipy.probploit n'utilise pas Cunnane mais Filliben cf https://docs.scipy.org/doc/scipy/reference/generated/scipy.stats.probplot.html)
        """
        if laws == 'popular':
            laws = LAWS_POPULAR
        elif isinstance(laws,str):
            laws=[laws]

        if fig is None and ax is None:
            fig,ax = plt.subplots(1,1)
            ax.set_title('QQ Plot')

        colors = ['r', 'g', 'b', 'r--', 'g--', 'b--']
        seasons = sanitize_seasons(seasons)

        k=0
        for curseason in seasons:
            if not 'sorted_maxval' in self.maxima[curseason].keys():
                self.sort_maxima(curseason)
                self.set_empfreq(curseason)

            data = self.maxima[curseason]['sorted_maxval']
            p_cum_Cun = self.maxima[curseason]['Empirical_frequency']['Cunnane']
            for curmethod in methods:
                if curmethod in self.maxima[curseason]['fit'].keys():
                    dictm = self.maxima[curseason]['fit'][curmethod]
                    for curlaw in laws:
                        if curlaw in dictm.keys():
                            dist = dictm[curlaw]['func']
                            # avec Cunnane
                            th_cun = [dist.ppf(curp) for curp in p_cum_Cun]

                            ax.scatter(th_cun,data,marker='o',label='Cunnane - '+curseason)
                            ax.plot([0,np.max(data)],[0,np.max(data)],'r')
                            ax.set_xlabel('Theoretical Quantile')
                            ax.set_ylabel('Empirical Quantile')
                            ax.legend()
        return(fig, ax)

    def plot_summary(self, seasons=None, nb_laws=None, forced_laws=[], sort:typing.Literal['RSS', 'AICc', 'AIC', 'BIC']='RSS', fig:Figure=None, ax:Axes=None, show=False) -> tuple[Figure,Axes]:
        """Plot summary results.

        Parameters
        ----------
        n_top : int, optional
            Show the top number of results. The default is None.
        figsize : tuple, optional (default: (10,8))
            The figure size.
        ylim : Float, optional (default: None)
            Limit figure in y-axis.
        fig : Figure, optional (default: None)
            Matplotlib figure
        ax : Axes, optional (default: None)
            Matplotlib Axes object

        Returns
        -------
        tuple (fig, ax)

        """

        seasons = sanitize_seasons(seasons)

        if ax is None:
            fig, ax = plt.subplots(len(seasons),1)

        nb_seasons = len(seasons)-1
        for idx, curseason in enumerate(seasons):
            if 'fit' in self.maxima[curseason].keys():

                if len(seasons)>1:
                    curax = ax[idx]
                else:
                    curax = ax

                curax2 = curax.twinx()
                curdict = self.maxima[curseason]['fit']

                for curmethod in curdict.keys():
                    if curmethod=='MLE':
                        curdictm = curdict[curmethod]

                        aic  = np.asarray([curdictm[curlaw]['aic'] for curlaw in curdictm.keys()])
                        aicc = np.asarray([curdictm[curlaw]['aicc'] for curlaw in curdictm.keys()])
                        bic  = np.asarray([curdictm[curlaw]['bic'] for curlaw in curdictm.keys()])
                        rss  = np.asarray([curdictm[curlaw]['rss'] for curlaw in curdictm.keys()] )

                        labels = np.asarray(list(curdictm.keys()))

                        if nb_laws is None:
                            nb_laws=len(aicc)

                        if nb_laws>len(aicc):
                            nb_laws=len(aicc)

                        if sort=='RSS':
                            #tri selon RSS
                            index_sort = rss.argsort()[:nb_laws]
                        elif sort=='AICc':
                            #tri selon AICc
                            index_sort = aicc.argsort()[:nb_laws]
                        elif sort=='AIC':
                            #tri selon AIC
                            index_sort = aic.argsort()[:nb_laws]
                        elif sort=='BIC':
                            #tri selon BIC
                            index_sort = bic.argsort()[:nb_laws]

                        if len(forced_laws)>0:
                            # on doit ajouter au moins certaines lois
                            for curlaw in forced_laws:
                                selected_labels = list(labels[index_sort])
                                if not (curlaw in selected_labels):
                                    #la loi n'est pas dans les meilleures sélectionnées
                                    # on doit donc l'ajouter
                                    idx = np.where(labels==curlaw)
                                    index_sort = np.append(index_sort, idx)

                        curax.plot(aic[index_sort], 'b*', label='AIC')
                        curax.plot(aicc[index_sort], 'r*', label='AICc')
                        curax.plot(bic[index_sort], 'gd', label='BIC')
                        curax2.plot(rss[index_sort], 'co', label='RSS')

                        curax.set_xticks(np.arange(len(index_sort)))

                        curax.set_xticklabels(labels[index_sort], rotation='vertical')
                        curax.set_xlabel('Distribution name')
                        curax.legend()
                        curax2.legend()
                        # if idx == nb_seasons:
                        #     curax.set_xticklabels(labels[index_sort], rotation='vertical')
                        #     curax.set_xlabel('Distribution name')
                        #     curax.legend()
                        #     curax2.legend()
                        # else:
                        #     curax.set_xticklabels([])

                        # Pad margins so that markers don't get clipped by the axes
                        curax.set_ymargin(0.2)
                        curax.grid(True)

                        curax.set_ylabel('Indicator (AIC, AICc, BIC - lower is better)')
                        curax2.set_ylabel('Indicator (RSS - lower is better)')

                        curax.set_title(curseason)
                        # Tweak spacing to prevent clipping of tick-labels
                        plt.subplots_adjust(bottom=0.15)
        if show:
            plt.show()

        return fig, ax, list(labels[index_sort][:nb_laws])

    def summary_max(self, seasons=None):

        seasons = sanitize_seasons(seasons)

        res = {}

        for curseason in seasons:
            data_max = self.maxima[curseason]['maxval']
            curdic = res[curseason] = {}
            curdic['nb values']  = len(data_max)
            curdic['max_of_max'] = np.max(data_max)
            curdic['min_of_max'] = np.min(data_max)
            curdic['median_of_max'] = np.median(data_max)
            curdic['maxvals'] = data_max.tolist()
            curdic['maxdates'] = [curdate.strftime('%Y/%m/%d %H') for curdate in self.maxima[curseason]['date']]

            if curseason == 'annual':
                if self.hydrological_year:
                    decal_start = [curdate - dt(curwy.year-1, self.startmonth_winter,1, tzinfo=self.tz_info) for curdate, curwy in zip(self.maxima[curseason]['date'],self.maxima[curseason]['water_year'])]
                    decal_end   = [curdate - dt(curwy.year  , self.startmonth_winter,1, tzinfo=self.tz_info) for curdate, curwy in zip(self.maxima[curseason]['date'],self.maxima[curseason]['water_year'])]
                else:
                    decal_start = [curdate - curwy                 for curdate, curwy in zip(self.maxima[curseason]['date'],self.maxima[curseason]['water_year'])]
                    decal_end   = [curdate - dt(curwy.year+1, 1,1, tzinfo=self.tz_info) for curdate, curwy in zip(self.maxima[curseason]['date'],self.maxima[curseason]['water_year'])]
            elif curseason == 'winter':
                if self.hydrological_year:
                    decal_start = [curdate - dt(curwy.year-1, self.startmonth_winter,1, tzinfo=self.tz_info) for curdate, curwy in zip(self.maxima[curseason]['date'],self.maxima[curseason]['water_year'])]
                    decal_end   = [curdate - dt(curwy.year  , self.startmonth_summer,1, tzinfo=self.tz_info) for curdate, curwy in zip(self.maxima[curseason]['date'],self.maxima[curseason]['water_year'])]
                else:
                    decal_start = [curdate - curwy               for curdate, curwy in zip(self.maxima[curseason]['date'],self.maxima[curseason]['water_year'])]
                    decal_end   = [curdate - dt(curwy.year, 7,1, tzinfo=self.tz_info) for curdate, curwy in zip(self.maxima[curseason]['date'],self.maxima[curseason]['water_year'])]
            elif curseason =='summer':
                if self.hydrological_year:
                    decal_start = [curdate - dt(curwy.year, self.startmonth_summer,1, tzinfo=self.tz_info) for curdate, curwy in zip(self.maxima[curseason]['date'],self.maxima[curseason]['water_year'])]
                    decal_end   = [curdate - dt(curwy.year, self.startmonth_winter,1, tzinfo=self.tz_info) for curdate, curwy in zip(self.maxima[curseason]['date'],self.maxima[curseason]['water_year'])]
                else:
                    decal_start = [curdate - dt(curwy.year, 7,1, tzinfo=self.tz_info)   for curdate, curwy in zip(self.maxima[curseason]['date'],self.maxima[curseason]['water_year'])]
                    decal_end   = [curdate - dt(curwy.year+1, 1,1, tzinfo=self.tz_info) for curdate, curwy in zip(self.maxima[curseason]['date'],self.maxima[curseason]['water_year'])]

            curdic['earliest_max [days after start]'] = np.min(decal_start).days
            curdic['earliest_date'] = self.maxima[curseason]['date'][np.argmin(decal_start)].strftime('%Y/%m/%d')
            curdic['latest_max [days before end]']   = np.max(decal_end).days
            curdic['lastest_date'] = self.maxima[curseason]['date'][np.argmax(decal_end)].strftime('%Y/%m/%d')

        return res

class EVA_Series:

    def __init__(self, data, datetime_index=None, datetime_format="%Y%m%d%H%M%S", data_headers=("#DateHeure", "Debit"), startmonth_winter = 10, startmonth_summer=4, hydrol=True) -> None:
        """
        Initialisation de la classe sur base de la chronique de données
        """
        self.base_serie = EVA_Serie(data,
                                    datetime_index,
                                    datetime_format,
                                    data_headers,
                                    startmonth_winter=startmonth_winter,
                                    startmonth_summer=startmonth_summer,
                                    hydrol=hydrol)
        self.all_series:dict[str, EVA_Serie] = {}
        self.MFSH={}

        self.hydrological_year = hydrol
        self.startmonth_winter = startmonth_winter
        self.startmonth_summer = startmonth_summer

        self._current_serie = self.base_serie

    def activate_serie(self, key:int = 1):

        self._current_serie = self.get_serie(key)

    def plot_T_Qmaxima(self,
                       seasons=None,
                       empirical_func='Cunnane',
                       fig:Figure=None,
                       ax:Axes=None,
                       show=False,
                       alpha=1.,
                       color_marker_label=None) -> tuple[Figure,Axes]:

        return self._current_serie.plot_T_Qmaxima(seasons, empirical_func, fig, ax, show, alpha, color_marker_label)

    def plot_fit(self,
                 seasons=None,
                 laws=['GEV'],
                 methods=['MLE'],
                 fig:Figure=None,
                 ax:Axes=None,
                 show=False,
                 alpha=1.,
                 styles:dict=None) -> tuple[Figure,Axes]:

        return self._current_serie.plot_fit(seasons, laws, methods, fig, ax, show, alpha, styles)

    def get_q_from_T(self,
                     return_periods:list=[5,10,15,20,25,50,75,100,200,500,1000],
                     season:str='best',
                     law:str='best',
                     method:str='MLE',
                     ic=False) -> pd.DataFrame:

        return self._current_serie.get_q_from_T(return_periods, season, law, method, ic)

    def get_T_from_q(self,
                     q:list,
                     season:str='best',
                     law:str='best',
                     method:str='MLE',
                     ic=False) -> pd.DataFrame:

        return self._current_serie.get_T_from_q(q, season, law, method, ic)

    def save_q_from_T(self,
                      filename:str='',
                      return_periods=[5,10,15,20,25,50,75,100,200,500,1000],
                      season='best',
                      law='best',
                      method='MLE',
                      ic=False):

        return self._current_serie.save_q_from_T(filename, return_periods, season, law, method, ic)

    def save_T_from_q(self,
                      filename:str='',
                      q=[5,10,15,20,25,50,75,100,200,500,1000],
                      season='best',
                      law='best',
                      method='MLE',
                      ic=False):

        return self._current_serie.save_T_from_q(filename, q, season, law, method, ic)

    def get_serie(self, key=1) -> EVA_Serie:

        if key in self.all_series.keys():
            return self.all_series[key]
        else:
            raise Exception('Bad key -- try again !')

    def find_maxima(self,
                    excluded_years=[],
                    hydrol=True,
                    method:typing.Literal['BM', 'POT']='BM',
                    threshold: float=0.,
                    r: typing.Union[pd.Timedelta, typing.Any] = "24H",
                    verbose = True):
        """
        Recherche des maxima pour toutes les saisons et toutes les durées
        """
        self.hydrological_year = hydrol

        for key,curserie in self.all_series.items():
            curserie:EVA_Serie
            curserie.find_maxima(hydrol=hydrol, excluded_years=excluded_years, method=method, threshold=threshold, r=r, verbose=verbose)

    def create_all_durations(self, durations=[1], verbose=True):
        """
        Création des chroniques pour toutes les durées souhaitées [heures]
        """

        # Opération de convolution pour déterminer les valeurs moyennes sur toutes les durées
        # !! Un peu plus optimisé que des boucles Python !!
        def convolve_data(data,nbsteps):
            locsum = np.ones(nbsteps)
            return np.convolve(locsum,data,'same')/float(nbsteps)

        # bouclage sur toutes le durées et calcul de la donnée moyenne par convolution
        # ATTENTION : les NaN vont se propager --> filtrer/traiter la série initiale en cas de besoin
        durations.sort()
        for curdur in durations:
            if verbose:
                print( '  **{}**'.format(curdur))
            self.all_series[curdur] = EVA_Serie(convolve_data(self.base_serie.data,curdur),
                                                self.base_serie.data.index,
                                                duration=curdur,
                                                startmonth_winter=self.startmonth_winter,
                                                startmonth_summer=self.startmonth_summer,
                                                hydrol=self.hydrological_year,
                                                verbose=verbose)

    def bake_data(self,
                  durations=[1],
                  excluded_years=[],
                  hydrol=True,
                  method:typing.Literal['BM', 'POT']='BM',
                  threshold: float=0.,
                  r: typing.Union[pd.Timedelta, typing.Any] = "24H",
                  verbose=True):
        self.create_all_durations(durations, verbose)
        self.find_maxima(excluded_years, hydrol,method, threshold, r, verbose)

    def plot_series(self,
                    durations=None,
                    oneyear = True,
                    show=False,
                    background=True,
                    backcolor='lemonchiffon'):
        """
        Viauslaisation des chroniques
        """
        if durations is None:
            durations = self.all_series.keys()

        figs=[]
        axes=[]
        for curdur in durations:
            curserie:EVA_Serie
            curserie = self.all_series[curdur]

            if oneyear:
                fig,ax = curserie.plot_annual(withdatemax=True)
                figs.append(fig)
                axes.append(ax)
            else:
                fig,ax = curserie.plot_serie(background=background,backcolor=backcolor)
                figs.append(fig)
                axes.append(ax)

        if show:
            plt.show()

        return figs, axes

    def plots_spw(self, stationcode:str, fontsize:int = 12, width=20, height=10, durations=[1], backcolor='lemonchiffon'):

        fig,ax   = self.plot_series(durations= durations, oneyear= False, show=True, backcolor=backcolor)

        ax[0].set_title('Station '+ stationcode + ' - Durée 1h - Toutes les années')
        ax[0].set_ylabel('Débit $m^3s^{-1}$')
        change_font_size(ax[0], fontsize)
        fig[0].set_size_inches(width, height)
        fig[0].tight_layout()

        fig2,ax2 = self.plot_series(durations= durations, oneyear= True , show=True)

        ax2[0].set_title('Station '+ stationcode + ' - Durée 1h - Années superposées')
        ax2[0].set_ylabel('Débit $m^3s^{-1}$')
        change_font_size(ax2[0], fontsize)
        fig2[0].set_size_inches(width, height)

        return ax[0], ax2[0]

    def eva(self,
            durations=[1],
            laws='popular',
            hydrol=True,
            excluded_years=[],
            plot=True,
            method:typing.Literal['BM', 'POT']='BM',
            threshold: float=0.,
            r: typing.Union[pd.Timedelta, typing.Any] = "24H",
            verbose=True,
            show=False) -> dict[str, tuple]:
        """
        Extreme Value Analysis

        durations : (list) durations in hours - default [1]
        laws : (str) laws to fit - default 'GEV'
        hydrol : (bool) use hydrological year - default True
        excluded_years : (list) years to exclude
        plot : (bool) creation of different plots
        method : (str) selection of maxima - default 'BM' == Block Maxima

        return : dict of tuples (fig,axes) of the plots
        """
        self.hydrological_year = hydrol

        self.bake_data(durations, excluded_years, hydrol, method, threshold, r, verbose)

        plots = {}

        if plot:
            plots['series_oneyear']    = self.plot_series(oneyear=True)
            plots['series_continuous'] = self.plot_series(oneyear=False)

        prev_serie = None
        for curdur in durations:
            locserie:EVA_Serie
            locserie = self.all_series[curdur]

            # optimisation des paramètres pour toutes les saisons
            locserie.fit(laws=laws, init_EVA=prev_serie, verbose=verbose)
            # fonction de mélange sur base d'une pondération "50-50" "summer"-"winter"
            locserie.set_mixture(laws=laws)
            # fonction jointe sur base du produit des probabilités saisonnières
            locserie.set_joint(laws=laws)

            if plot:
                plots['cdf'] = locserie.plot_cdf()
                plots['max_events'] = locserie.plot_maxevents()
                plots['summary'] = locserie.plot_summary()
                plots['qq'] = locserie.plot_qq()

                # création d'un graphique pour chaque saison
                for curseason in SEASONS:
                    fig,ax = locserie.plot_T_Qmaxima(curseason)
                    locserie.plot_fit(curseason, laws, fig=fig, ax=ax)
                    plots['TQ_' + curseason] = (fig,ax)

                # création d'un graphique et supersposition des saiosns pour une seule loi
                fig,ax = locserie.plot_T_Qmaxima()
                locserie.plot_fit(laws='GEV', fig=fig, ax=ax)
                plots['TQ_all_seasons'] = (fig,ax)

            prev_serie = locserie

        if show:
            plt.show()

        self.activate_serie(1)

        return plots

    def evaluate_ci(self, seasons=None, durations=[1], laws=['GEV'], nboot=100, show=False) -> dict:
        """
        Intervalles de confiance

        Retourne une liste contenant des tuples (fig,ax) pour chaque durée et chaque saison

        La boucle principale est sur les durées
        La boucle interne est sur les saisons
        """
        seasons = sanitize_seasons(seasons, False)

        figax={}
        for curdur in durations:
            locserie:EVA_Serie
            locserie = self.all_series[curdur]

            locserie.fit(laws=laws, seasons=seasons, ic=True, nboot=nboot)

            curfigax = figax[curdur] = {}

            for curseason in seasons:
                fig,ax = locserie.plot_T_Qmaxima(curseason, show=False)
                locserie.plot_fit(curseason,laws,fig=fig,ax=ax, show=False)
                locserie.plot_ci(curseason,laws, fig=fig, ax=ax, show=False)
                curfigax[curseason] = (fig,ax)

            if show:
                plt.show()

        return figax

    def evaluate_ic(self, seasons=None, durations=[1], laws=['GEV'], nboot=100, show=False) -> dict:
        """ alias evaluate_ci """
        return self.evaluate_ci(seasons, durations, laws, nboot, show)

    def test_distfit(self, durations=[1], plot=True):
        """
        Ajustement de lois avec la toolbox distfit
        """
        for curdur in durations:
            locserie:EVA_Serie
            locserie = self.all_series[curdur]
            locserie.distfit(laws='full',bins=50,smooth=3)

            if plot:
                locserie.plot_distfit()

    def plot_qdf(self, seasons=None, durations=None, law='GEV', show = False):
        """Graphique de toutes les relations fittées pour chaque durée sur une même figure"""
        colors = ['r', 'g', 'b', 'r--', 'g--', 'b--'] * int(np.ceil(len(self.all_series.keys()) /6))

        seasons = sanitize_seasons(seasons,True)
        if durations is None:
            durations = self.all_series.keys()

        resdict = {}

        for curseason in seasons:
            fig = None
            for idx, curdur in enumerate(durations):
                locserie:EVA_Serie

                if curdur in self.all_series.keys():
                    locserie = self.all_series[curdur]

                    if fig is None:
                        fig,ax = locserie.plot_fit(curseason, law, styles=set_style(colors[idx]))
                        resdict[curseason] = (fig,ax)
                    else:
                        locserie.plot_fit(curseason, law, fig=fig, ax=ax, styles=set_style(colors[idx]))

        if show:
            plt.show()

        return resdict

    def select_best_func(self, season='mixture', law='GEV', method='MLE'):
        """
        Sélection de la fonction à retenir comme meilleur ajustement
        """
        for idx, curdur in enumerate(self.all_series.keys()):
            # bouclage sur les durées
            locserie = self.all_series[curdur]
            locserie.select_best_func(season, law, method)

            if locserie.best is None:
                raise Exception('Bad "best" func selection - retry !')

    def get_one_MFSH(self, rising_time:float=6., return_period:float=50., deltat:float=1.) -> Hydro_HSMF:

        durees = list(self.all_series.keys())
        Qp = [d.ppf(1.-1./float(return_period)) for d in self.bests]

        # Qp est maintenant une liste qui reprend les valeurs de Q pour la période de retour T pour les différentes durées
        # Sur cette base, on lance la génération de l'hydrogramme

        res = Hydro_HSMF(Qp, durees, rising_time, deltat, 'HSMF_{}'.format(return_period))
        res.opt_hydro()

        return res

    def opti_mfsh(self, label, rising_time=6, return_period = [2, 5, 10, 25, 50, 100, 200, 500, 1000], deltat=1):
        """
        #############################
        ## CALCUL DES HYDROGRAMMES ##
        #############################
        """
        return_period.sort()

        dict = self.MFSH[label]={}

        self.bests = [cur.best for cur in self.all_series.values()]

        # lancer une boucle 'for' sur les différentes périodes de retour
        for curT in return_period:
            dict[curT] = self.get_one_MFSH(rising_time, curT, deltat)

    def plot_msfh(self,
                  label,
                  return_period= [2, 5, 10, 25, 50, 100, 200, 500, 1000],
                  ref_season='annual',
                  ylim=None,
                  before = 1,
                  after = 3,
                  show=False) -> tuple[Figure, Axes, Axes]:
        """
        ################
        ## GRAPHIQUES ##
        ################
        """

        if not label in self.MFSH.keys():
            raise Warning('No hydrogram to plot -- retry')

        ref_serie = self.all_series[1]
        fig, ax = ref_serie.plot_maxevents(ref_season, before, after, alpha=.15)

        ax2 = ax.twinx()

        for curT in return_period:
            curhydro:Hydro_HSMF
            curhydro=self.MFSH[label][curT]

            curhydro._plot_Q(ax2, before*24 - curhydro.temps_montee, label=str(curT), lw=3, xup_bound=(before+after)*24)

        ax.legend().set_visible(False)
        ax2.legend()

        if ylim is not None:
            ax.set_ylim(ylim)

        if show:
            plt.show()

        return fig,ax,ax2

    def plot_msfh_mainplot(self,
                           label,
                           return_period= [2, 5, 10, 25, 50, 100, 200, 500, 1000],
                           ref_season='annual',
                           ylim=None,
                           before = 1,
                           after=2,
                           show=False) -> tuple[Figure, Axes]:
        """
        ################
        ## GRAPHIQUES ##
        ################
        """

        if not label in self.MFSH.keys():
            raise Warning('No hydrogram to plot -- retry')

        fig,ax = plt.subplots(1,1)

        for curT in return_period:
            curhydro:Hydro_HSMF
            curhydro=self.MFSH[label][curT]

            curhydro._plot_Q(ax, before*24 - curhydro.temps_montee, label=str(curT), lw=3, xup_bound=(before+after)*24)

        ax.legend()

        if ylim is not None:
            ax.set_ylim(ylim)

        if show:
            plt.show()

        return fig,ax

    def save_max_event(self,
                       filename:str,
                       years_bounds:list,
                       seasons = None):

        self._current_serie.save_max_events(filename, years_bounds, seasons)

    def save_msfh(self, label,
                  filename,
                  return_period= [2, 5, 10, 25, 50, 100, 200, 500, 1000]):
        """
        ################
        ## SAUVEGARDE ##
        ################
        """

        if not label in self.MFSH.keys():
            raise Warning('No hydrogram to plot -- retry')

        dicthydro={}

        for curT in return_period:
            curhydro:Hydro_HSMF
            curhydro=self.MFSH[label][curT]

            dicthydro['Temps [heure]'] = curhydro.temps
            dicthydro['Debit [m3s-1] - {} ans'.format(curT)] = curhydro.hydro

        df = pd.DataFrame.from_dict(dicthydro, orient='columns')
        df.to_csv(filename, sep=';')

    def plot_one_fit(self, seasons=None, durations=None, laws='popular',
                     split_duration=True, split_season=True, xbounds=None,
                     ybounds=None, show=False) -> tuple[Figure, Axes]:

        seasons = sanitize_seasons(seasons)

        if durations is None:
            durations = list(self.all_series.keys())
        elif isinstance(durations,str) or isinstance(durations,int):
            durations=[durations]

        if laws == 'popular':
            laws = LAWS_POPULAR
        elif isinstance(laws,str):
            laws=[laws]

        nbrows = 1
        nbcols  = 1
        if split_duration:
            nbrows = len(durations)
        if split_season:
            nbcols = len(seasons)

        fig,ax = plt.subplots(nbrows, nbcols)

        for iddur, curdur in enumerate(durations):
            locserie:EVA_Serie
            locserie = self.all_series[curdur]

            for idseas, curseason in enumerate(seasons):

                if split_duration and split_season:
                    curax = ax[iddur, idseas]
                elif split_season:
                    curax = ax[idseas]
                elif split_duration:
                    curax = ax[iddur]
                else:
                    curax = ax

                locserie.plot_T_Qmaxima(curseason, fig=fig, ax = curax)
                locserie.plot_fit(laws=laws, fig=fig, ax=curax)

        if xbounds is not None:
            if split_duration and split_season:
                for curax in ax:
                    for curax2 in curax:
                        curax2.set_xbound(xbounds)
            elif split_duration or split_season:
                for curax in ax:
                    curax.set_xbound(xbounds)
            else:
                ax.set_xbound(xbounds)

        if ybounds is not None:
            if split_duration and split_season:
                for curax in ax:
                    for curax2 in curax:
                        curax2.set_ybound(ybounds)
            elif split_duration or split_season:
                for curax in ax:
                    curax.set_ybound(ybounds)
            else:
                ax.set_ybound(ybounds)


        if show:
            plt.show()

        return fig, ax

    def print_summary(self, seasons=None, durations=None, show=False):
        import json

        seasons = sanitize_seasons(seasons)

        if durations is None:
            durations = list(self.all_series.keys())

        summary={}

        for idx, curdur in enumerate(durations):
            locserie:EVA_Serie
            locserie = self.all_series[curdur]

            summary[str(curdur)] = locserie.summary_max(seasons)

        if show:
            print(json.dumps(summary, indent=4))

        return summary

    def plot_selected_max(self, seasons=None, durations=None,
                          split_seasons = False, scaling=False, show=False)-> tuple[Figure, Axes]:
        """
        Graphique des dates des événements sélectionnés pour chaque durée (par défaut, toutes les durées)
        """
        seasons = sanitize_seasons(seasons)

        if durations is None:
            durations = list(self.all_series.keys())

        locserie     = self.base_serie
        ticks_year   = [ locserie._get_dates(curyear,self.hydrological_year)[0] for curyear in np.arange(locserie.years_bounds[0],locserie.years_bounds[1]+1)]
        ticks_season = [ locserie._get_dates(curyear,self.hydrological_year, 'winter')[1] for curyear in np.arange(locserie.years_bounds[0],locserie.years_bounds[1]+1)]

        if split_seasons and len(seasons)>1:
            fig, ax = plt.subplots(len(seasons),1)

            for idx, curdur in enumerate(durations):
                locserie:EVA_Serie
                locserie = self.all_series[curdur]

                k=0
                for curseason, curcolor, curmarker in zip(seasons, SEASONS_COLORS, SEASONS_MARKERS):
                    label=''
                    if idx==0:
                        label=curseason
                    nb = len(locserie.maxima[curseason]['date'])

                    if scaling:
                        ax[k].scatter(locserie.maxima[curseason]['date'],[idx+1]*nb, s=locserie.maxima[curseason]['maxval'], marker=curmarker,c=curcolor, label=label)
                    else:
                        ax[k].scatter(locserie.maxima[curseason]['date'],[idx+1]*nb, marker=curmarker,c=curcolor, label=label)

                    k+=1

            for curax in ax:
                curax.set_yticks(np.arange(int(len(durations)))+1)
                curax.set_yticklabels(durations)

                curax.set_ylabel('Durations [hours]')
                curax.grid(True)
                curax.legend()

                curax.set_xticks(ticks_year + ticks_season)
                curax.set_xticklabels( [curyear for curyear in np.arange(locserie._get_dates(locserie.years_bounds[0],self.hydrological_year)[0].year
                                                                         ,locserie._get_dates(locserie.years_bounds[1]+1,self.hydrological_year, 'winter')[0].year)] + ['w->s']*len(ticks_season), rotation='vertical')

            curax = ax[-1]
            if self.hydrological_year:
                curax.set_xlabel('Date (hydrological year)')
            else:
                curax.set_xlabel('Date (real calendar)')

        else:
            fig, ax = plt.subplots(1,1)

            for idx, curdur in enumerate(durations):
                locserie:EVA_Serie
                locserie = self.all_series[curdur]
                for curseason, curcolor, curmarker in zip(seasons, SEASONS_COLORS, SEASONS_MARKERS):
                    label=''
                    if idx==0:
                        label=curseason
                    nb = len(locserie.maxima[curseason]['date'])
                    ax.scatter(locserie.maxima[curseason]['date'],[idx+1]*nb,marker=curmarker,c=curcolor, label=label)

            ax.set_yticks(np.arange(int(len(durations)))+1)
            ax.set_yticklabels(durations)

            ticks_year = [ locserie._get_dates(curyear,self.hydrological_year)[0] for curyear in np.arange(locserie.years_bounds[0],locserie.years_bounds[1]+1)]
            ticks_season = [ locserie._get_dates(curyear,self.hydrological_year, 'winter')[1] for curyear in np.arange(locserie.years_bounds[0],locserie.years_bounds[1]+1)]

            ax.set_xticks(ticks_year + ticks_season)
            ax.set_xticklabels( [curyear for curyear in np.arange(locserie._get_dates(locserie.years_bounds[0],self.hydrological_year)[0].year
                                                                         ,locserie._get_dates(locserie.years_bounds[1]+1,self.hydrological_year, 'winter')[0].year)] + ['w->s']*len(ticks_season), rotation='vertical')

            ax.set_ylabel('Durations [hours]')
            if self.hydrological_year:
                ax.set_xlabel('Date (hydrological year)')
            else:
                ax.set_xlabel('Date (real calendar)')
            ax.grid(True)
            ax.legend()

        # plt.tight_layout()

        if show:
            plt.show()

        return fig, ax


def example1():
    # durees=np.arange(1,24,1,dtype=np.int32)
    durees = [1]
    myseries = EVA_Series(filepath, data_headers=("#DateHeure", "Debit"))
    myseries.eva(durees,plot=True)
    myseries.eva(durees, excluded_years=[2021,2022], plot=True)
    myseries.evaluate_ci()

def example1bis():
    # durees=np.arange(1,24,1,dtype=np.int32)
    durees = [24]
    myseries = EVA_Series(filepath, data_headers=("#DateHeure", "Debit"))
    myseries.bake_data(durees)
    locserie = myseries.get_serie(24)
    fig,ax,Qchar = locserie.plot_classified_flowrate_curve()

def example2():
    # durees=np.arange(1,24,1,dtype=np.int32)
    durees = [1,6,12,24,48]
    myseries = EVA_Series(filepath, data_headers=("#DateHeure", "Debit"))
    myseries.eva(durees, laws='GEV', excluded_years=[2021,2022], plot=False)
    myseries.plot_qdf(show=True)
    myseries.select_best_func('mixture')
    myseries.opti_mfsh('summer')
    myseries.plot_msfh('summer',show=True)

def example3():
    # durees=np.arange(1,24,1,dtype=np.int32)
    durees = np.hstack([np.arange(1,49),72,120])
    myseries = EVA_Series(filepath, data_headers=("#DateHeure", "Debit"))
    myseries.eva(durees, laws='GEV', excluded_years=[2021,2022], plot=False)
    myseries.select_best_func('mixture')
    myseries.plot_qdf(show=False)
    myseries.opti_mfsh('12',rising_time=12)
    myseries.plot_msfh('12',ref_season='annual')
    myseries.plot_msfh('12',ref_season='winter')
    myseries.plot_msfh('12',ref_season='summer')

    myseries.opti_mfsh('6',rising_time=6)
    myseries.plot_msfh('6',ref_season='annual')
    myseries.plot_msfh('6',ref_season='winter')
    myseries.plot_msfh('6',ref_season='summer',show=True)

def example4():

    durees = np.hstack([np.arange(1,49),72,120])
    durees = [48]
    filepath = os.path.join(strdir,filename_verviers_naturel_test)
    myseries = EVA_Series(filepath, startmonth_winter=10, startmonth_summer=4, hydrol=True)
    myseries.bake_data(durees, excluded_years=[2022], verbose=False)

    locserie:EVA_Serie
    locserie = myseries.all_series[48]
    locserie.plot_one_maxevents('annual',1998,show=True)

    myseries.print_summary()
    fig,ax = myseries.plot_selected_max(split_seasons=True, show=True)

    myseries.plot_selected_max(split_seasons=True, scaling=True, show=True)
    myseries.plot_selected_max(split_seasons=True, show=True)
    myseries.plot_selected_max(split_seasons=False, show=True)

def example5():

    durees = np.hstack([np.arange(1,49),72,120])
    durees = [1,48]
    filepath = os.path.join(strdir,filename_verviers_naturel_test)
    myseries = EVA_Series(filepath, startmonth_winter=10, startmonth_summer=4, hydrol=True)
    myseries.eva([1], laws='GEV', excluded_years=[2021,2022], plot=True)

def example6_POT():
    durees = [1]
    myseries = EVA_Series(filepath, data_headers=("#DateHeure", "Debit"))
    myseries.eva(durees,plot=True, method='POT', threshold=10.)
    myseries.eva(durees, excluded_years=[2021,2022], plot=True)
    myseries.evaluate_ci()


if __name__=='__main__':
    strPath = os.path.realpath(__file__)
    strdir = os.path.join(os.path.dirname(strPath),'..\\..\\data\\stats')

    filename_Theux      = 'L5860_Qh_Mean.csv'
    filename_verviers   = 'L7150_Qh_Mean.csv'
    filename_verviers_ecrete = 'L7150_Ecrete_Qh_Mean.csv'
    filename_verviers_naturel= 'L7150_Naturel_Qh_Mean.csv'
    filename_test_nan_excel = 'L7150_Naturel_Qh_Mean_#valeur.csv'
    filename_verviers_naturel_test = 'L7150_Naturel_Qh_Mean_#valeur.csv'

    filepath = os.path.join(strdir,filename_verviers)
    example6_POT()
    pass
