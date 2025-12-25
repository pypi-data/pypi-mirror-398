import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.widgets import Slider
from numpy import random as rnd
import math
from pathlib import Path
import json
import timeit
import multiprocessing
import cProfile, pstats
import wx
from os.path import join
import threading
from sklearn.neighbors import KernelDensity
from scipy.ndimage import maximum_filter
from scipy.spatial.distance import cdist
from datetime import datetime, timedelta

try:
    from ..PyParams import *
    from ..drawing_obj import Element_To_Draw
    from ..Results2DGPU import getkeyblock
    from ..PyTranslate import _
    from ..PyVertex import cloud_vertices
    from ..wolf_array import WolfArray, header_wolf
    from ..PandasGrid import PandasGrid
except:
    from wolfhece.PyParams import *
    from wolfhece.drawing_obj import Element_To_Draw
    from wolfhece.Results2DGPU import getkeyblock
    from wolfhece.PyTranslate import _
    from wolfhece.PyVertex import cloud_vertices
    from wolfhece.wolf_array import WolfArray
    from wolfhece.PandasGrid import PandasGrid

try:
    from .drowning_functions import *
except:
    from wolfhece.drowning_victims.drowning_functions import *


#index               0         1     2       3         4          5     6         7
COLUMN_Z_PARAM = ['vertical','U_z','z_0','mu_stat','Time_float','T_w','ADD','ADD_resurface']
COLUMNS_HUMAN = ['Age','BMI','BSA','CAM','CDA','CLA','Death','dm','eps','fp_x','fp_y','fp_z','gender','height','lungs_volume_FRC','lungs_volume_TLC','mass','rho','Volume','V_clothes_o','V_clothes_one','V_clothes_two','error_perc_fat','CSA']

class Drowning_victim:
    def __init__(self,Path_dir:str = None):
        """
    Initialize the simulation parameters.

    :param Path_loading:
        Path of the simulation loaded.

    Attributes:
        Profile_this (bool): Binary parameter to activate the profiling of the code.
        saving (bool): Binary parameter to save your results.
        file_name (str): Name of the file to be saved.
        Path_saving (str): Path where you want the file saved.
        loading (bool): Binary parameter to load previous results and start from them.
        Path_loading (str): Path of the simulation loaded.
        Path_Wolf (str): Path of the WolfGPU simulation.
        plot_pos (bool): Binary parameter to plot your results.
        CFL (float): CFL number to calculate the time step of your simulation.
        dt_min (float): Minimum time step for your variable time step.
        dt_max (float): Maximum time step for your variable time step.
        t_initial (float): Initial time of the simulation.
        Days (int): Number of days of the simulation.
        Hours (int): Number of hours of the simulation.
        Minutes (int): Number of minutes of the simulation.
        Seconds (int): Number of seconds of the simulation.
        wanted_time (list): Array with all the times at which we want a save.
        n_t (int): Length of wanted_time.
        count_initial (int): Initial step of the simulation.
        count_pre (int): Initial step of the simulation - 1.
        n_b (int): Number of simulated bodies.
        n_parallel (int): Number of times the process is parallelized (number of cores used).
        random_IP (float): Radius of the uncertainty area of the drowning point (in cells).
        T_water (float): Average water temperature in °C.
        vertical (bool): Binary parameter to consider vertical motion.
        DZ (float): Step size for vertical motion (used in simulation).
        Z_param (pd.DataFrame): Dataframe holding the parameters for vertical motion simulation.
    """

        self.Default_values()
        self.from_attributes_to_dictionnary()

        ## Loads all the parameters from the parameters.param file
        if Path_dir is not None:
            self.Path_saving = Path(Path_dir)
            self.from_dot_param_to_dictionnary(store_dir=self.Path_saving)
            self.from_dictionnary_to_attributes()
            # self.update_params(str(self.Path_saving))

    def Default_values(self):
        """
        Sets the default values for each parameter by creating a first parameter.param
        """
        import pandas as pd
        import math
        import numpy.random as rnd

        self.Profile_this = 0
        self.Redraw = 0#[1,2,3] #0 for no

        current_dir = Path(__file__).resolve().parent
        self.current_dir = current_dir
        self.saving = 1
        self.file_name = 'Test'

        self.loading = 0
        self.Path_loading = None
        self.Path_saving = None

        self.Path_Wolf = None

        self.plot_pos = 0

        self.a_RK = 0.5

        self.image = 0

        self.CFL = 0.01
        self.dt_min = 0.01
        self.dt_max = 1 #s
        self.t_initial = 0*60*60*24
        self.i_initial = math.floor(self.t_initial/self.dt_max)+1

        self.Days = int(0) #days
        self.Hours = int(1) #h
        self.Minutes = int(0) #min
        self.Seconds = int(0) #s
        time_goal = self.Days*24*60*60 + self.Hours*60*60 + self.Minutes*60 + self.Seconds #s
        self.time_goal = time_goal

        self.ind_pos_0_x = 0 #For L14: 3983, L_30: 4303
        self.ind_pos_0_y = 0 #For L14: 3780, L_30: 3902

        self.origx = 215702
        self.origy = 130000
        self.dx = 5
        self.dy = 5
        self.nbx = 8460
        self.nby = 10416

        self.n_saved = 1

        self.n_b = 10000
        n_b = self.n_b
        self.n_parallel = 2 #Number of processes to be ran in parallel
        Z_param = pd.DataFrame(data=None,columns=COLUMN_Z_PARAM,dtype=np.int32)
        Z_param.vertical = 1 # 1 = Consider the vertical motion, 0 = not considered
        Z_param.U_z = 0*np.ones((n_b)) #0 = U constant on depth, 1 = U varies with the depth (log law)
        d_50 = 2*2*40 *10**-3 #to be confirmed
        Z_param.z_0 = d_50/30*np.ones((n_b)) #experimental results of Nikuradse (not found if published in 1933 or 1950 but nobody seems to care)
        Z_param.mu_stat = 1 * np.ones((n_b)) #rnd.beta(1,1,size=(n_b))*(1-0.3)+0.3
        Z_param.Time_float = 0*np.ones((n_b))
        Z_param.T_w = 15*np.ones((n_b))
        Z_param.ADD = time_goal/60/60/24*15
        Z_param.ADD_resurface = 5250/15 * rnd.beta(4,4,size=n_b) #source: Heaton 2011 considering a TADS between 14 and 15 as maximum expension
        self.Z_param = Z_param

        ## Let the viewer edit the parameters
        self.victim()

        self.path = Path(current_dir)
        # self.save_json(Path(self.Path_saving))

    def victim(self):
        """
        Definition of the victim's caracteristics

        gender : Gender of the victim, 1 for man, 2 for women
        Age : Age of the victim in years
        height : Height of the victim in m
        mass : Mass of the victim in kg
        BMI : BMI of the victim in kg/m²
        clothes : clothing type of the victim (0 for naked, 1 for summer clothes, 2 for spring clothes, 3 for winter clothes)
        T_w : Average water temperature in °C
        ini_drowning : Time at which the victim drowned in the day (format 24H)

        """
        self.gender = -1
        self.Age = -1
        self.height = -1
        self.mass = -1
        self.BMI = -1
        self.clothes = -1
        self.T_w = 15
        self.ini_drowning = 10 #simpledialog.askinteger('Hour at which the victim fell in the water','Time of drowning in hours: \nExample: 2 AM (2h00) being 2 \n5 PM (17h00) being 17',minvalue=0,maxvalue=23,parent=root)
        self.m_b_add = 0 #mass of added accessories

    def from_attributes_to_dictionnary(self):
        "Create a dictionnary from the attributes of the class"

        param_dict = {}

        # Dictionnaire des sections et paramètres à ajouter
        param_dict = {
                "Options": {
                    "Profile": {
                        "value": self.Profile_this,
                        "explicit name": "Profile",
                        "description": "Do you want to profile your code?",
                        "type": "Integer",
                        "choices": {
                            "Don't profile the code":0,
                            "Profile the code":1
                        },
                        "mandatory": False
                    },
                    "Save": {
                        "value": self.saving,
                        "explicit name": "Save",
                        "description": "Enable saving of results?",
                        "type": "Integer",
                        "choices": {
                            "Don't save":0,
                            "Save the results":1
                        },
                        "mandatory": True
                    },
                    "Load": {
                        "value": self.loading,
                        "explicit name": "Load",
                        "description": "Enable loading of previous results?",
                        "type": "Integer",
                        "choices":  {
                            "Don't load the results from a previous simulation":0,
                            "Load":1
                        },
                        "mandatory": True
                    },
                    "Plot": {
                        "value": self.plot_pos,
                        "explicit name": "Plot",
                        "description": "Enable plotting of results?",
                        "type": "Integer",
                        "choices":  {
                            "Don't plot":0,
                            "Plot the results when simulation is over":1
                        },
                        "mandatory": False
                    },
                    "n_parallel": {
                        "value": self.n_parallel,
                        "explicit name": "Number of parallel processes",
                        "description": "Number of parallel processes to use",
                        "type": "Integer",
                        "choices": None,
                        "mandatory": True
                    },
                    "vertical": {
                        "value": 1,  # Assuming vertical motion is always enabled
                        "explicit name": "Vertical motion",
                        "description": "Consider vertical motion in the simulation?",
                        "type": "Integer",
                        "choices":  {
                            "No vertical motion allowed":0,
                            "With vertical motion allowed":1
                        },
                        "mandatory": False
                    },
                    "a_RK": {
                        "value": self.a_RK,
                        "explicit name": "Runge-Kutta ponderation coefficient",
                        "description": "Coefficient for RK22 integration",
                        "type": "Float",
                        "choices": None,
                        "mandatory": False
                    },
                    "image": {
                        "value": self.image,
                        "explicit name": "Progression bar",
                        "description": "Enable image generation",
                        "type": "Integer",
                        "choices": {
                            "Plot progress with loading bar":0,
                            "Plot progress with progress image":1
                        },
                        "mandatory": False
                    }
                },
                "Paths": {
                    "File": {
                        "value": self.file_name,
                        "explicit name": "File name",
                        "description": "Name of the file to save",
                        "type": "String",
                        "choices": None,
                        "mandatory": True
                    },
                    "Save": {
                        "value": self.Path_saving,
                        "explicit name": "Save path",
                        "description": "Path where results will be saved",
                        "type": "Directory",
                        "choices": None,
                        "mandatory": True
                    },
                    "Load": {
                        "value": self.Path_loading,
                        "explicit name": "Load path",
                        "description": "Path to load previous results",
                        "type": "Directory",
                        "choices": None,
                        "mandatory": False
                    },
                    "Wolf": {
                        "value": self.Path_Wolf,
                        "explicit name": "Results of Wolf GPU simulation path",
                        "description": "Path to the WolfGPU simulation",
                        "type": "Directory",
                        "choices": None,
                        "mandatory": True
                    }
                },
                "DT": {
                    "CFL": {
                        "value": self.CFL,
                        "explicit name": "CFL",
                        "description": "Courant number for time step calculation",
                        "type": "Float",
                        "choices": None,
                        "mandatory": False
                    },
                    "dt_min": {
                        "value": self.dt_min,
                        "explicit name": "Minimum time step",
                        "description": "Minimum time step in seconds",
                        "type": "Float",
                        "choices": None,
                        "mandatory": False
                    },
                    "dt_max": {
                        "value": self.dt_max,
                        "explicit name": "Maximum time step",
                        "description": "Maximum time step in seconds",
                        "type": "Float",
                        "choices": None,
                        "mandatory": False
                    }
                },
                "Duration": {
                    "t_d": {
                        "value": self.Days,
                        "explicit name": "Days",
                        "description": "Number of days for the simulation",
                        "type": "Integer",
                        "choices": None,
                        "mandatory": True
                    },
                    "t_h": {
                        "value": self.Hours,
                        "explicit name": "Hours",
                        "description": "Number of hours for the simulation",
                        "type": "Integer",
                        "choices": None,
                        "mandatory": True
                    },
                    "t_min": {
                        "value": self.Minutes,
                        "explicit name": "Minutes",
                        "description": "Number of minutes for the simulation",
                        "type": "Integer",
                        "choices": None,
                        "mandatory": True
                    },
                    "t_s": {
                        "value": self.Seconds,
                        "explicit name": "Seconds",
                        "description": "Number of seconds for the simulation",
                        "type": "Integer",
                        "choices": None,
                        "mandatory": True
                    }
                },
                "Victim (-1 for unknown)": {
                    "n_b": {
                        "value": self.n_b,
                        "explicit name": "Number of bodies",
                        "description": "Number of simulated bodies",
                        "type": "Integer",
                        "choices": None,
                        "mandatory": True
                    },
                    "gender": {
                        "value": self.gender,
                        "explicit name": "Gender",
                        "description": "Gender of the victim (1 for male, 2 for female)",
                        "type": "Integer",
                        "choices":  {
                            "Unknown":-1,
                            "Man":1,
                            "Woman":2
                        },
                        "mandatory": True
                    },
                    "age": {
                        "value": self.Age,
                        "explicit name": "Age [years]",
                        "description": "Age of the victim in years",
                        "type": "Integer",
                        "choices": None,
                        "mandatory": True
                    },
                    "h_b": {
                        "value": self.height,
                        "explicit name": "Height [m]",
                        "description": "Height of the victim in meters",
                        "type": "Float",
                        "choices": None,
                        "mandatory": True
                    },
                    "m_b": {
                        "value": self.mass,
                        "explicit name": "Mass [kg]",
                        "description": "Mass of the victim in kilograms",
                        "type": "Float",
                        "choices": None,
                        "mandatory": True
                    },
                    "BMI": {
                        "value": self.BMI,
                        "explicit name": "BMI [kg/m²]",
                        "description": "Body Mass Index of the victim, needed only if the mass is unknown",
                        "type": "Float",
                        "choices": None,
                        "mandatory": True
                    },
                    "clothes": {
                        "value": self.clothes,
                        "explicit name": "Clothing type",
                        "description": "Clothing type of the victim",
                        "type": "Integer",
                        "choices":  {
                            "Unknown":-1,
                            "Naked":0,
                            "Short and T-shirt (Summer clothes)":1,
                            "Sweater and trousers (Spring/Fall)":2,
                            "Sweater, trousers and heavy warm jacket (Winter clothes)":3
                        },
                        "mandatory": True
                    },
                    "T_w": {
                        "value": self.T_w,
                        "explicit name": "Water temperature [°C]",
                        "description": "Average water temperature in °C",
                        "type": "Float",
                        "choices": None,
                        "mandatory": True
                    },
                    "ini_drowning": {
                        "value": self.ini_drowning,
                        "explicit name": "Initial drowning time",
                        "description": "Time at which the victim drowned",
                        "type": "Integer",
                        "choices": None,
                        "mandatory": True
                    },
                    "m_b_add": {
                        "value": self.m_b_add,
                        "explicit name": "Added mass of accessories [kg]",
                        "description": "Mass of added accessories, like a backpack or lifting weights",
                        "type": "Float",
                        "choices": None,
                        "mandatory": True
                    }
                },
                "Initial_drowning_point": {
                    "x": {
                        "value": self.ind_pos_0_x,
                        "explicit name": "X-cell",
                        "description": "X-coordinate of the initial drowning point",
                        "type": "Integer",
                        "choices": None,
                        "mandatory": True
                    },
                    "y": {
                        "value": self.ind_pos_0_y,
                        "explicit name": "Y-cell",
                        "description": "Y-coordinate of the initial drowning point",
                        "type": "Integer",
                        "choices": None,
                        "mandatory": True
                    }
                },
                "Grid": {
                    "origx": {
                        "value": self.origx,
                        "explicit name": "Origin X",
                        "description": "Origin of the matrix in X",
                        "type": "Float",
                        "choices": None,
                        "mandatory": True
                    },
                    "origy": {
                        "value": self.origy,
                        "explicit name": "Origin Y",
                        "description": "Origin of the matrix in Y",
                        "type": "Float",
                        "choices": None,
                        "mandatory": True
                    },
                    "dx": {
                        "value": self.dx,
                        "explicit name": "Delta X",
                        "description": "Spatial step of the matrix in X",
                        "type": "Float",
                        "choices": None,
                        "mandatory": True
                    },
                    "dy": {
                        "value": self.dy,
                        "explicit name": "Delta Y",
                        "description": "Spatial step of the matrix in Y",
                        "type": "Float",
                        "choices": None,
                        "mandatory": True
                    },
                    "nbx": {
                        "value": self.nbx,
                        "explicit name": "Nb X",
                        "description": "Number of steps of the matrix in X",
                        "type": "Integer",
                        "choices": None,
                        "mandatory": True
                    },
                    "nby": {
                        "value": self.nby,
                        "explicit name": "Nb Y",
                        "description": "Number of steps of the matrix in Y",
                        "type": "Integer",
                        "choices": None,
                        "mandatory": True
                    }
                }
            }

        self.param_dict = param_dict

        return

    def from_dictionnary_to_attributes(self):
        """
        Update the attributes of the class based on the values in self.param_dict.
        """
        # Parcourir les sections et les paramètres dans param_dict
        for section, params in self.param_dict.items():
            for key, param_data in params.items():
                # Récupérer la valeur du paramètre
                value = param_data.get("value", None)
                if param_data.get("type", None)=='Integer':
                    value = int(value)

                # Mettre à jour l'attribut correspondant dans self
                if section == "Options":
                    if key == "Profile":
                        self.Profile_this = value
                    elif key == "Save":
                        self.saving = value
                    elif key == "Load":
                        self.loading = value
                    elif key == "Plot":
                        self.plot_pos = value
                    elif key == "n_parallel":
                        self.n_parallel = value
                    elif key == "vertical":
                        self.Z_param.vertical = value
                    elif key == "a_RK":
                        self.a_RK = value
                    elif key == "image":
                        self.image = value

                elif section == "Paths":
                    if key == "File":
                        self.file_name = value
                    elif key == "Save":
                        self.Path_saving = value
                    elif key == "Load":
                        self.Path_loading = value
                    elif key == "Wolf":
                        self.Path_Wolf = value

                elif section == "DT":
                    if key == "CFL":
                        self.CFL = value
                    elif key == "dt_min":
                        self.dt_min = value
                    elif key == "dt_max":
                        self.dt_max = value

                elif section == "Duration":
                    if key == "Days":
                        self.Days = value
                    elif key == "Hours":
                        self.Hours = value
                    elif key == "Minutes":
                        self.Minutes = value
                    elif key == "Seconds":
                        self.Seconds = value

                elif section == "Victim (-1 for unknown)":
                    if key == "n_b":
                        self.n_b = value
                    elif key == "gender":
                        self.gender = value
                    elif key == "age":
                        self.Age = value
                    elif key == "h_b":
                        self.height = value
                    elif key == "m_b":
                        self.mass = value
                    elif key == "BMI":
                        self.BMI = value
                    elif key == "clothes":
                        self.clothes = value
                    elif key == "T_w":
                        self.T_w = value
                    elif key == "ini_drowning":
                        self.ini_drowning = value
                    elif key == "m_b_add":
                        self.m_b_add = value

                elif section == "Initial_drowning_point":
                    if key == "x":
                        self.ind_pos_0_x = value
                    elif key == "y":
                        self.ind_pos_0_y = value

                elif section == "Grid":
                    if key == "Origin X":
                        self.origx = value
                    elif key == "Origin Y":
                        self.origy = value
                    elif key == "Delta X":
                        self.dx = value
                    elif key == "Delta Y":
                        self.dy = value
                    elif key == "Nb X":
                        self.nbx = value
                    elif key == "Nb Y":
                        self.nby = value

        # Initialise the parameters of the simulation with default values and values given in the parameters.param file
        self.t_initial = 0
        self.i_initial = 0
        self.time_goal = self.Days*24*60*60 + self.Hours*60*60 + self.Minutes*60 + self.Seconds #s
        self.wanted_time = np.array([self.t_initial])
        self.n_saved = 1
        for i in np.arange(10,self.time_goal+10,10):
            if i<60:
                self.wanted_time = np.append(self.wanted_time,i)
                self.n_saved += 1
            elif np.logical_and(i<10*60,(i%60==0)):
                self.wanted_time = np.append(self.wanted_time,i)
                self.n_saved += 1
            elif np.logical_and(i<30*60,(i%(5*60)==0)):
                self.wanted_time = np.append(self.wanted_time,i)
                self.n_saved += 1
            elif np.logical_and(i<60*60,(i%(10*60)==0)):
                self.wanted_time = np.append(self.wanted_time,i)
                self.n_saved += 1
            elif np.logical_and(i<=24*60*60,(i%(60*60)==0)):
                self.wanted_time = np.append(self.wanted_time,i)
                self.n_saved += 1
            elif np.logical_and(i<=2*24*60*60,(i%(2*60*60)==0)):
                self.wanted_time = np.append(self.wanted_time,i)
                self.n_saved += 1
            elif (i%(3*60*60)==0):
                self.wanted_time = np.append(self.wanted_time,i)
                self.n_saved += 1

        self.wanted_time = np.append(self.wanted_time,0)

        self.n_t = math.floor(self.time_goal/self.dt_min)+1
        self.count_initial = 1
        self.count_pre = self.count_initial-1

        n_b = self.n_b

        self.random_IP = 1 # number of cells considered for the radius of random position

        ## Parameters of vertical motion (ADD, temp)

        self.DZ = 0.1

        # Update of the dataframe
        Z_param = pd.DataFrame(data=None,columns=COLUMN_Z_PARAM,dtype=np.int32)
        Z_param.U_z = 0*np.ones((n_b)) #0 = U constant on depth, 1 = U varies with the depth (log law)
        d_50 = 2*2*40 *10**-3 #to be confirmed
        Z_param.z_0 = d_50/30*np.ones((n_b)) #experimental results of Nikuradse (not found if published in 1933 or 1950 but nobody seems to care)
        Z_param.mu_stat = 1 * np.ones((n_b)) #rnd.beta(1,1,size=(n_b))*(1-0.3)+0.3
        Z_param.Time_float = 0*np.ones((n_b))
        Z_param.T_w = self.T_w*np.ones((n_b))
        Z_param.ADD = self.time_goal/60/60/24*self.T_w
        Z_param.ADD_resurface = 5250/self.T_w * rnd.beta(4,4,size=n_b) #source: Heaton 2011 considering a TADS between 14 and 15 as maximum expension
        self.Z_param = Z_param

    def from_dot_param_to_dictionnary(self,store_dir: Path = None):
        """
        Update the parameters with the modifications made by the user with the file parameters.param

        :param store_dir: directory where the file parameters.param is
        """

        # Charger le dictionnaire existant
        param_dict = self.param_dict

        data = {}
        text_file_path = join(store_dir,"parameters.param")

        if not os.path.exists(text_file_path):
            raise FileNotFoundError(f"Le fichier {text_file_path} est introuvable.")

        with open(text_file_path, 'r', encoding='ISO-8859-1') as file:
            for line in file:
                line = line.strip()

                # Vérifier si la ligne est un nom de section (par exemple, 'Options:', 'Path:', etc.)
                if line.endswith(":"):
                    # Crée une nouvelle sous-section
                    current_section = line[:-1]  # Retire le ':' pour obtenir le nom de section
                    data[current_section] = {}
                elif "\t" in line and current_section:
                    # Split clé et valeur
                    key, value = line.split("\t", 1)

                    # Convertir la valeur en nombre si possible
                    try:
                        value = float(value)
                    except ValueError:
                        pass  # Garde la valeur comme chaîne de caractères si non convertible

                    # Ajout de la clé et de la valeur dans la section actuelle
                    data[current_section][key] = value

        # Mettre à jour self.param_dict avec les valeurs de data
        for section, params in data.items():
            if section in param_dict:
                for key, value in params.items():
                    # Rechercher la clé dans le dictionnaire existant
                    for param_key, param_data in param_dict[section].items():
                        if param_data["explicit name"] == key:
                            # Mettre à jour la valeur
                            param_dict[section][param_key]["value"] = value
                            break

        # Sauvegarder le dictionnaire mis à jour dans self.param_dict
        self.param_dict = param_dict

        return

    def Human_generation(self):
        """
        Generates the bodies for the simulation

        :return Human

        Attributes:
        Human : Dataframe panda with each line representing a body and n_b lines, so one for eahc body
        gender : Gender of the victim, 1 for man, 2 for women
        Age : Age of the victim in years
        height : Height of the victim in m
        mass : Mass of the victim in kg
        BMI : BMI of the victim in kg/m²
        clothes : clothing type of the victim (0 for naked, 1 for summer clothes, 2 for spring clothes, 3 for winter clothes)
        CAM : Added mass coefficient of the body
        CDA : Drag area of the body (drag coefficient * a reference area)
        CLA : Lift area of the body
        CSA : Side area of the body
        fp_x : Projection coefficient along the x-axis to go from the BSA to the frontal area
        fp_y : Projection coefficient along the y-axis to go from the BSA to the frontal area
        fp_z : Projection coefficient along the z-axis to go from the BSA to the frontal area
        lungs_volume_TLC : Lungs volume at Total Lungs Capacity
        lungs_volume_FRC : Lungs volume at Functionnal Residual Capacity (at rest, after normally expiring)
        dm : Amount of swallowed water
        BSA : Body surface area (i.e. surface of the skin)
        Death : Type of death
        eps : Width of the body
        V_clothes_o : Initial volume of clothes (according to Barwood et al., 2011)
        V_clothes_one : Volume of clothes after 20min at rest (according to Barwood et al., 2011)
        V_clothes_two : Volume of clothes after 20min of swimming (according to Barwood et al., 2011)
        error_perc_fat : Deviation to the average on the percentage body fat of the body calculated from the equation of Siri et al. 1960

        """

        Human = pd.DataFrame(data=None,columns=COLUMNS_HUMAN,dtype=np.int32)

        n_b = self.n_b

        ##Gender
        Human.gender = self.gender * np.ones((n_b))
        if self.gender == -1:
            Human.gender = np.zeros(n_b)
            Human.gender[:n_b // 2] = 2
            Human.gender[n_b // 2:] = 1
        ind_m = np.where(Human.gender==1)[0]
        ind_w = np.where(Human.gender==2)[0]

        ##Age
        Human.Age = self.Age * np.ones((n_b))
        if self.Age==-1:
            age_min = 18
            age_max = 90 + 1
            Human.Age = rnd.randint(age_min,age_max,size=(n_b))

        #Height
        h_av = self.height
        h_max = np.array([205, 190]) /100
        h_min = np.array([150, 140]) /100
        [ah_w,bh_w] = known_1(2,h_min[1],h_max[1],h_av-0.025,h_av+0.025,0.1,0.9)
        [ah_m,bh_m] = known_1(1,h_min[0],h_max[0],h_av-0.025,h_av+0.025,0.1,0.9)
        Human.loc[ind_m,'height'] = rnd.beta(ah_m,bh_m,size=(len(ind_m)))*(h_max[0]-h_min[0])+h_min[0] #men
        Human.loc[ind_w,'height'] = rnd.beta(ah_w,bh_w,size=(len(ind_w)))*(h_max[1]-h_min[1])+h_min[1] #women
        if h_av == -1:
            Human.loc[ind_m,'height'] = rnd.beta(5.8697,6.075,size=(len(ind_m)))*(h_max[0]-h_min[0])+h_min[0] #men
            Human.loc[ind_w,'height'] = rnd.beta(3.976,5.965,size=(len(ind_w)))*(h_max[1]-h_min[1])+h_min[1] #women

        ##Mass or BMI
        m_av = self.mass
        m_max = np.array([135, 130])
        m_min = np.array([35, 35])
        [am_w,bm_w] = known_1(2+3,m_min[1],m_max[1],m_av-2.5,m_av+2.5,0.1,0.9)
        [am_m,bm_m] = known_1(1+3,m_min[0],m_max[0],m_av-2.5,m_av+2.5,0.1,0.9)
        Human.loc[ind_m,'mass'] = rnd.beta(am_m,bm_m,size=((len(ind_m))))*(m_max[0] - m_min[0]) + m_min[0]
        Human.loc[ind_w,'mass'] = rnd.beta(am_w,bm_w,size=((len(ind_w))))*(m_max[1] - m_min[1]) + m_min[1]
        Human.BMI = Human.mass / Human.height**2
        known = 1
        if m_av < 0:
            BMI = self.BMI
            BMI_min = 16
            BMI_max = 40
            BMI_25 = [20, 21.3, 22.5, 23.3, 22.9, 23.7, 23.1]
            BMI_50 = [21.7, 23.4, 24.8, 25.7, 25.9, 26.3, 25.3]
            BMI_75 = [24.3, 26.4, 28, 29, 29.1, 29.7, 28]
            ind_Age = np.minimum(math.floor(np.mean(Human.Age.to_numpy())/10)-1,6)
            if BMI > 0:
                BMI_down = BMI-1
                BMI_up = BMI+1
                [abmi,bbmi] = known_1(3,BMI_min,BMI_max,BMI_down,BMI_up,0.1,0.9)
                Human.BMI = rnd.beta(abmi,bbmi,size=((n_b)))*(BMI_max-BMI_min)+BMI_min
            else:
                [abmi,bbmi] = known_1(3,BMI_min,BMI_max,BMI_25[ind_Age],BMI_75[ind_Age],0.25,0.75)
                Human.BMI = rnd.beta(abmi,bbmi,size=((n_b)))*(BMI_max-BMI_min)+BMI_min
                known = 0
            Human.mass = Human.BMI*Human.height**2

        ##Clothes
        clothes = self.clothes #simpledialog.askinteger('Dialog title','Clothing type with: \n-1 if unknown \n0 for naked or in underwear\n1 for summer clothes (short and a t-shirt or dress)\n2 for autumn/spring clothes (trousers, a t-shirt, a sweater, and eventually a water/windproof jacket)\n3 for winter clothes (trousers, a t-shirt, a sweater, and a heavy warm jacket or more clothes)',minvalue=-1,maxvalue=3,parent=root) #0 for naked, 1 for summer clothes, 2 for autumn/spring clothes, 3 for winter clothes
        if clothes==-1:
            clothes=2

        Human,error_perc_fat = Skinfold(n_b,known,Human)


        Human.CAM = ((2-Human.gender)*0.268+(Human.gender-1)*0.236) *np.ones((n_b)) #according Caspersen et al., 2010: Added mass in human swimmers

        #CD, CL and CS fitted to the results of tests realised in the wind tunnel on 28/02/2023, tight clothing = no clothes or summer clothes
        Human.CDA = 0.4181*np.ones(n_b)*(clothes<2) + 0.5172*np.ones(n_b)*(clothes>=2)
        Human.CLA = 0.07019*np.ones(n_b)*(clothes<2) + 0.08387*np.ones(n_b)*(clothes>=2)
        Human.CSA = 0.03554*np.ones(n_b)*(clothes<2) + 0.04047*np.ones(n_b)*(clothes>=2)
        # Human.CDA = rnd.normal(0.4181,0.03434,n_b)*(clothes<2) + rnd.normal(0.5172,0.0406,n_b)*(clothes>=2)
        # Human.CLA = rnd.normal(0.07019,0.05035,n_b)*(clothes<2) + rnd.normal(0.08387,0.08138,n_b)*(clothes>=2)
        # Human.CSA = rnd.normal(0.03554,0.02545,n_b)*(clothes<2) + rnd.normal(0.04047,0.04311,n_b)*(clothes>=2)

        #Mandatory for the structure of the numpy variable Human generated for the calculations
        Human.fp_x = rnd.beta(1,1,size=(n_b))*(0.36-0.16)+0.16
        Human.fp_y = 0.36-Human.fp_x+0.16
        Human.fp_z = np.ones((n_b)) * 0.2


        Human.lungs_volume_TLC = 10**-3 * ((7.99*Human.height-7.08) * (2-Human.gender) + (6.6*Human.height-5.79) * (Human.gender-1)) #Formulas ERC valid for men between 1.55 and 1.95 m and women between 1.45 and 1.8 m
        Human.lungs_volume_FRC = 10**-3 * ((2.34*Human.height+0.01*Human.Age-1.09) * (2-Human.gender) + (2.24*Human.height+0.001*Human.Age-1) * (Human.gender-1)) #Formulas ERC valid for men between 1.55 and 1.95 m and women between 1.45 and 1.8 m
        Human.lungs_volume_TLC = Human.lungs_volume_TLC * (0.0403*Human.BMI**2 - 3.1049*Human.BMI + 149.58)/100 #Digitalization of TOTAL part of figure 4 of doi:10.1136/bmjresp-2017-000231
        Human.lungs_volume_FRC = Human.lungs_volume_FRC * (0.102*Human.BMI**2 - 7.4504*Human.BMI + 229.61)/100 #Digitalization of TOTAL part of figure 4 of doi:10.1136/bmjresp-2017-000231

        Human.dm = Human.mass * (0.1 * rnd.beta(1.5,1.5,size=((n_b))) + 0.0) #Between x and y% of the body mass (usually around 10 according to test on dogs)
        Human.dm += self.m_b_add

        Human.BSA = ((128.1 * Human.mass**0.44 * (Human.height*100)**0.6) * (2-Human.gender) + (147.4 * Human.mass**0.47 * (Human.height*100)**0.55) * (Human.gender-1))*10**-4

        Human.Death = np.ones(n_b)

        Human.eps = np.ones(n_b)*0.2


        clothes_alpha_m = np.array([[1,0.1771,0.0192,0.0082],[1,5.7342e-6,0.0253,0.8511],[1,5.9719e-6,0.333,4.981e-6]])
        clothes_alpha_w = np.array([[1,0.7676,4.4037,0.8523],[1,0.5375,0.3333,3.5128],[1,0.5375,0.7082,2.333]])
        clothes_beta_m = np.array([[1,0.3542,0.0385,0.0095],[1,9.9565e-6,0.0505,1.7022],[1,1.1522e-5,0.667,8.7348e-6]])
        clothes_beta_w = np.array([[1,1.5353,8.8072,1.7046],[1,1.0749,0.6667,7.0255],[1,1.0749,1.4165,4.6659]])

        clothes_mean_m = np.array([[0.5,0.6127,2.7573,4.3912],[0.5,0.204,0.715,1.021],[0.5,0.408,1.1233,0.613]])*10**-3
        clothes_mean_w = np.array([[0.5,1.123,2.655,4.493],[0.5,0.9191,1.1233,1.94],[0.5,0.9191,1.2254,2.0424]])*10**-3
        clothes_std_m = np.array([[0.5,0.7148,0.817,0.6127],[0.5,0.9191,1.1233,0.817],[0.5,0.817,1.1233,2.451]])*10**-3
        clothes_std_w = np.array([[0.5,0.9191,1.6339,1.6339],[0.5,0.817,1.1233,1.225],[0.5,0.817,1.0212,0.817]])*10**-3

        clothes_max_m = clothes_mean_m + 2*clothes_std_m
        clothes_min_m = clothes_mean_m - 2*clothes_std_m
        clothes_max_w = clothes_mean_w + 2*clothes_std_w
        clothes_min_w = clothes_mean_w - 2*clothes_std_w


        Human.V_clothes_o = (clothes!=0)* ((rnd.beta(clothes_alpha_m[0,clothes],clothes_beta_m[0,clothes],size=(n_b))*(clothes_max_m[0,clothes]-clothes_min_m[0,clothes])+clothes_min_m[0,clothes])*(2-Human.gender) + (rnd.beta(clothes_alpha_w[0,clothes],clothes_beta_w[0,clothes],size=(n_b))*(clothes_max_w[0,clothes]-clothes_min_w[0,clothes])+clothes_min_w[0,clothes])*(Human.gender-1))
        Human.V_clothes_one = (clothes!=0)* ((rnd.beta(clothes_alpha_m[1,clothes],clothes_beta_m[1,clothes],size=(n_b))*(clothes_max_m[1,clothes]-clothes_min_m[1,clothes])+clothes_min_m[1,clothes])*(2-Human.gender) + (rnd.beta(clothes_alpha_w[1,clothes],clothes_beta_w[1,clothes],size=(n_b))*(clothes_max_w[1,clothes]-clothes_min_w[1,clothes])+clothes_min_w[1,clothes])*(Human.gender-1))
        Human.V_clothes_two = (clothes!=0)* ((rnd.beta(clothes_alpha_m[2,clothes],clothes_beta_m[2,clothes],size=(n_b))*(clothes_max_m[2,clothes]-clothes_min_m[2,clothes])+clothes_min_m[2,clothes])*(2-Human.gender) + (rnd.beta(clothes_alpha_w[2,clothes],clothes_beta_w[2,clothes],size=(n_b))*(clothes_max_w[2,clothes]-clothes_min_w[2,clothes])+clothes_min_w[2,clothes])*(Human.gender-1))

        Human.error_perc_fat = error_perc_fat

        self.Human = Human

    def Initialisation_arrays(self):
        """
        Function where the matrixes of body position, speed, time, resurfacing and sinking are initialised, both for computing and saving
        Initialisation of other variables used in the simulation

        Attributes:

        BC_cells : Array containing the index of all cells that are boundary conditions for the hydrodynamic simulation
        DT_WOLF : Time step of the WOLF simulation
        NbX : Number of cells in the x-direction for the WOLF simulation
        NbY : Number of cells in the y-direction for the WOLF simulation
        ini_drowning : Hour at which the victim fell in the water
        count_Wolf : Time step of the Wolf simulation that we consider as our initial time in the Lagrangian simulation
        wanted_Wolf : Array containing all the times at which we have a new Wolf result
        Delta : Array containing the spatial and time steps
        Pos : Working array containing the 3D positions of all bodies at time t and t-dt with shape (n_b,3,2)
        Pos_b : Saving array containing the 3D positions of all bodies at all saving times with shape (n_b,3,n_t)
        U : Working array containing the 3D velocities of all bodies at time t and t-dt with shape (n_b,3,2)
        U_b : Saving array containing the 3D velocities of all bodies at all saving times with shape (n_b,3,n_t)
        time : Working array containing the time associated to each body with shape (n_b,)
        resurface : Saving array containing the resurfacing time of all bodies with shape (n_b,)
        sinking : Saving array containing the sinking time of all bodies with shape (n_b,)
        count : Counter to evaluate the progression of the savings
        sp : Parameter deserving to work with the working variables
        """

        self.Human_generation()
        n_b = self.n_b
        n_saved = self.n_saved

        self.BC_cells,self.DT_WOLF,DX,DY,H_mat,self.NbX,self.NbY,t_tot_Wolf = Read_Wolf_GPU_metadata(self.Path_Wolf)

        X = np.arange(0,DX*self.NbX,DX)+DX/2
        Y = np.arange(0,DY*self.NbY,DY)+DY/2

        self.count_Wolf = self.ini_drowning -1
        self.wanted_Wolf = np.arange(0,t_tot_Wolf+self.DT_WOLF,self.DT_WOLF)


        Delta = np.zeros((5))
        Delta[0] = DX
        Delta[1] = DY
        Delta[2] = 1 #DZ
        Delta[3] = self.dt_max
        Delta[4] = np.sqrt(DX**2+DY**2)
        self.Delta = Delta

        ind_pos_0_x = self.ind_pos_0_x
        ind_pos_0_y = self.ind_pos_0_y
        NbZ = H_mat[ind_pos_0_y,ind_pos_0_x]/Delta[2]
        ind_pos_0_z = NbZ.astype(int)

        index_b = np.zeros((n_b,3,n_saved)) #number of the body,(xyz) index in the matrix, time step
        index_b = index_b.astype(int)

        Pos_b = np.zeros((n_b,3,n_saved)) #number of the body,(xyz), time step

        U_b = np.zeros((n_b,3,n_saved)) #number of the body,(xyz), time step

        self.time_b = np.zeros((n_b,n_saved))

        index_b[:,0,0] = np.ones((n_b)) * ind_pos_0_x
        index_b[:,1,0] = np.ones((n_b)) * ind_pos_0_y
        index_b[:,2,0] = np.zeros((n_b))

        Pos_b[:,0,0] = np.ones((n_b)) * X[ind_pos_0_x]
        Pos_b[:,1,0] = np.ones((n_b)) * Y[ind_pos_0_y]

        ## Calculation of horizontal and vertical body motion

        Pos = np.zeros((n_b,3,2))
        U = np.zeros((n_b,3,2))

        # Generation of uncertainty on the drownin point
        if self.loading == 0:
            rand_x = DX* rnd.uniform(size=(n_b))*np.sign(rnd.uniform(size=(n_b))-1/2)*self.random_IP
            rand_y = DY* rnd.uniform(size=(n_b))*np.sign(rnd.uniform(size=(n_b))-1/2)*self.random_IP

            Pos[:,0,0] = X[int(index_b[0,0,0])]+rand_x
            Pos[:,1,0] = Y[int(index_b[0,1,0])]+rand_y
            Pos[:,2,0] = H_mat[int(index_b[0,1,0]),int(index_b[0,0,0])]
            Pos[:,0,1] = X[int(index_b[0,0,0])]+rand_x
            Pos[:,1,1] = Y[int(index_b[0,1,0])]+rand_y
            Pos[:,2,1] = H_mat[int(index_b[0,1,0]),int(index_b[0,0,0])]
            Pos_b[:,:,0] = Pos[:,:,0]

        else:
            self.count_initial,self.Human,n_loaded,Pos_b,self.time_b,U_b,self.Z_param = Loading(self.Path_loading,Pos_b,self.time_b,U_b)

            Pos[:,0,0] = Pos_b[:,0,n_loaded]
            Pos[:,1,0] = Pos_b[:,1,n_loaded]
            Pos[:,2,0] = Pos_b[:,2,n_loaded]
            Pos[:,0,1] = Pos_b[:,0,n_loaded]
            Pos[:,1,1] = Pos_b[:,1,n_loaded]
            Pos[:,2,1] = Pos_b[:,2,n_loaded]

            U[:,0,0] = U_b[:,0,n_loaded]
            U[:,1,0] = U_b[:,1,n_loaded]
            U[:,2,0] = U_b[:,2,n_loaded]
            U[:,0,1] = U_b[:,0,n_loaded]
            U[:,1,1] = U_b[:,1,n_loaded]
            U[:,2,1] = U_b[:,2,n_loaded]

        self.Pos = Pos
        self.Pos_b = Pos_b

        self.U = U
        self.U_b = U_b

        self.time = self.t_initial*np.ones((n_b))
        self.resurface = np.zeros((n_b,2))
        self.sinking = np.zeros((n_b,2))
        self.count = self.count_initial
        self.sp = 1

    def start(self):

        """
        Main of the class, runs the code with a parallelised code (n_parallel>1) or without

        """

        start = timeit.default_timer()

        self.Initialisation_arrays()

        if self.Profile_this ==1:
            profiler = cProfile.Profile()
            profiler.enable()

        # Conversion of dataframe to numpy array for parallel processing and memory efficiency
        Human_np = self.Human.to_numpy()
        Z_param_np = self.Z_param.to_numpy()

        # Multiprocess run
        if self.n_parallel>1:
            # Set up progress queue for inter-process communication
            with multiprocessing.Manager() as manager:
                progress_queue = manager.Queue()
                stop_event = threading.Event()  # Indicateur pour arrêter le thread

                # Start wxPython application and create the frame
                app = wx.App(False)
                frame = wx.Frame(None)
                if self.image==1:
                    frame = ProgressImage(self.n_parallel,self.time_goal, None)
                else:
                    frame = ProgressBar(None,n_processes=self.n_parallel,total=self.time_goal)
                frame.Show()

                tasks = Preparation_parallelisation(progress_queue,self.a_RK,self.BC_cells,self.count,self.count_Wolf,self.CFL,self.Delta,Human_np,self.i_initial,self.n_b,self.n_saved,self.n_parallel,self.n_t,self.NbX,self.NbY,self.Path_saving,self.Path_Wolf,self.Pos,self.Pos_b,self.resurface,self.sinking,self.time,self.time_b,self.time_goal,self.U,self.U_b,self.wanted_time,self.wanted_Wolf,Z_param_np)

                # Création de la thread de suivi de la progression
                time_viewer = 1
                monitor_thread = threading.Thread(target=state_of_run, args=(progress_queue,frame, time_viewer))
                monitor_thread.daemon = True  # Ensure it terminates when the program exits
                monitor_thread.start()

                with multiprocessing.Pool(processes=self.n_parallel) as pool:
                    result_async = pool.map_async(Parallel_loop, tasks)
                    while not result_async.ready():
                        wx.Yield()  # This allows the GUI to update while waiting for the results
                    # Wait for the result to be ready
                    results = result_async.get()


                def on_close(event):
                    frame.Close()  # Ferme la fenêtre
                    app.ExitMainLoop()

                frame.Bind(wx.EVT_CLOSE, on_close)
                frame.Close()
                stop_event.set()  # Stop the monitoring thread

            self.Pos_b = np.concatenate([result[0] for result in results], axis=0)
            self.resurface = np.concatenate([result[1] for result in results], axis=0)
            self.sinking = np.concatenate([result[2] for result in results], axis=0)
            self.time_b = np.concatenate([result[3] for result in results], axis=0)
            self.U_b = np.concatenate([result[4] for result in results], axis=0)

        # No use of multiprocessing
        else:
            self.Pos_b,self.resurface,self.sinking,self.time_b,self.U_b = Loop_management(-1,-1,self.a_RK,self.BC_cells,self.count,self.count_Wolf,self.CFL,self.Delta,Human_np,self.i_initial,self.n_b,self.n_saved,self.n_t,self.NbX,self.NbY,self.Path_saving,self.Path_Wolf,self.Pos,self.Pos_b,self.resurface,self.sinking,self.time,self.time_b,self.time_goal,self.U,self.U_b,self.wanted_time,self.wanted_Wolf,Z_param_np)


        stop = timeit.default_timer()
        execution_time = stop - start

        n_b = self.n_b
        time_goal = self.time_goal

        # Save of the results
        Path_save = os.path.join(self.Path_saving,'Results')
        os.makedirs(Path_save,exist_ok=True)
        np.savez(Path_save,Pos_b=self.Pos_b,U_b=self.U_b,Human=self.Human,Z_param=self.Z_param,wanted_time=self.wanted_time,time_b=self.time_b)

        logging.info(f"Program executed in "+str(round(execution_time/60,1))+" min, for "+str(n_b)+" bodies and "+str(np.floor(time_goal/(60*60*24)))+" days "+str(int((time_goal/60/60-24*int(time_goal/60/60/24))))+" h "+str((np.floor((time_goal/60)%60)))+" min "+str(time_goal%60)+ " s")
        if self.Profile_this ==1:
            profiler.disable()
            stats = pstats.Stats(profiler).sort_stats('ncalls')
            stats.sort_stats('tottime')
            stats.print_stats()


        if self.saving == 1:
            np.savez(self.Path_saving,Pos_b=self.Pos_b,U_b=self.U_b,Human=self.Human,Z_param=self.Z_param,wanted_time=self.wanted_time,time_b=self.time_b)

    def Parallel_loop(args):
        """
        Necessary for the parallelisation as we have to give a list of arguments to the function instead of all the args separately
        """

        result = Loop_management(*args)

        return result


class Drowning_victim_Viewer(Element_To_Draw):

    def __init__(self, idx = '', plotted = True, mapviewer = None, need_for_wx = False,filedir = None):
        super().__init__(idx, plotted, mapviewer, need_for_wx)

        self.filename = None
        self.filedir = filedir
        self.file_drowning = None
        self.n_peaks = 2
        self.init_plot()

        self.newdrowning = Drowning_victim(Path_dir=filedir)

        self.from_dictionnary_to_wp()

    def selection_drowning_point(self,event):
        """
        Function to select the drowning point in the viewer
        """
        from ..PyDraw import draw_type
        liste = self.mapviewer.get_list_keys(draw_type.RES2D,checked_state=None)

        if not liste:
            dialog = wx.DirDialog(None, "Folder containing the wanted simulation WOLF 2D GPU", style=wx.DD_DEFAULT_STYLE)

            # Afficher la boîte de dialogue et attendre l'interaction de l'utilisateur
            if dialog.ShowModal() == wx.ID_OK:
                # Récupérer le chemin sélectionné
                self.newdrowning.Path_Wolf = dialog.GetPath()
                self.wp.change_param('Paths','Results of Wolf GPU simulation path',self.newdrowning.Path_Wolf)

                # Ajouter l'objet avec le chemin sélectionné
                self.mapviewer.add_object(which='res2d_gpu', ToCheck=True, filename=join(self.newdrowning.Path_Wolf, 'Results'))
                self.mapviewer.menu_wolf2d()
                self.mapviewer.menu_2dgpu()
                self.mapviewer.Autoscale()
                dialog.Destroy()
            else:
                # L'utilisateur a annulé la boîte de dialogue
                logging.info(_('No folder selected for the WOLF 2D GPU simulation.'))
                # Détruire la boîte de dialogue pour libérer les ressources
                dialog.Destroy()
                return

        else:
            myitem = self.mapviewer.single_choice_key(draw_type.RES2D,checked_state=None)
            # nameitem = self.mapviewer.treelist.GetItemText(myitem).lower()
            # curobj = self.mapviewer.getobj_from_id(nameitem)
            # myobj = self.mapviewer.treelist.GetItemData(myitem)
            # self.mapviewer.active_res2d = myobj

        self.wp.change_param('Grid','Origin X',self.mapviewer.active_res2d.origx)
        self.wp.change_param('Grid','Origin Y',self.mapviewer.active_res2d.origy)

        with open(join(self.newdrowning.Path_Wolf,'parameters.json'), 'r', encoding='utf-8') as file:
            data = json.load(file)
        dx = data['parameters']['dx']
        dy = data['parameters']['dy']
        nbx = data['parameters']['nbx']
        nby = data['parameters']['nby']
        self.wp.change_param('Grid','Delta X',dx)
        self.wp.change_param('Grid','Delta Y',dy)
        self.wp.change_param('Grid','Nb X',nbx)
        self.wp.change_param('Grid','Nb Y',nby)

        self.button_selection_progress = wx.Button(self.wp,label='Drowning point')
        self.button_selection_progress.Bind(wx.EVT_BUTTON,self.selection_progress)
        self.button_selection_progress.SetToolTip('Check if you have exactly one drowning point selected')
        self.wp.sizerbut.Insert(4,self.button_selection_progress,1,wx.EXPAND)
        self.wp.sizer.Fit(self.wp)

        self.wp.SetSize(0,0,self.w,800)
        self.wp.Show(True)

    def selection_progress(self,event):
        """
        Function to select the drowning point in the viewer
        """

        if self.mapviewer.active_res2d.SelectionData.nb==0:
            wx.MessageBox(_("No point selected, please select a drowning point"), "Error", wx.OK | wx.ICON_ERROR)
            return

        elif self.mapviewer.active_res2d.SelectionData.nb==1:
            value_got = self.mapviewer.active_res2d.myblocks[getkeyblock(0)].SelectionData.myselection
            x,y = value_got[0]
            self.newdrowning.ind_pos_0_x, self.newdrowning.ind_pos_0_y = self.mapviewer.active_res2d.get_ij_from_xy(x=x,y=y)
            self.update_drowning_pos()
            self.mapviewer.active_res2d.SelectionData.reset_all()
            self.button_selection_progress.SetBackgroundColour(wx.Colour(50, 190, 50))
            self.file_drowning = 1
            return

        elif self.mapviewer.active_res2d.SelectionData.nb>1:
            wx.MessageBox(_("More than one point selected, please select only one drowning point"), "Error", wx.OK | wx.ICON_ERROR)
            return

    def update_drowning_pos(self):
        """
        Update the values of "X-cell" and "Y-cell" in the parameters.param file.
        """

        self.wp.change_param("Initial_drowning_point",'X-cell', int(self.newdrowning.ind_pos_0_x))
        self.wp.change_param("Initial_drowning_point",'Y-cell', int(self.newdrowning.ind_pos_0_y))

    def create_exe_file(self,event):
        """
        Start the drowning in a separate process
        """
        import subprocess
        try:
            if self.filedir is None:
                wx.MessageBox(_("No directory selected for the simulation. \nPlease, save your drowning in a directory."), "Error", wx.OK | wx.ICON_ERROR)
                return

            self.filedir = Path(self.filedir)
            # Créer le répertoire self.Path_saving s'il n'existe pas
            self.filedir.mkdir(parents=True, exist_ok=True)
            # Définir le chemin du fichier exe_drowning.py
            self.exe_file = self.filedir / "exe_drowning.py"
            project_root = Path(__file__).resolve().parents[2]
            # Contenu du fichier exe_drowning.py
            script_content = f"""
import sys
import os
from pathlib import Path

directory = r"{project_root}"
os.chdir(directory)

_root_dir = os.path.dirname(os.path.realpath(__file__))
sys.path.insert(0,os.path.join(directory,'./wolfhece'))

try:
    from .Drowning_victims.Class import Drowning_victim
except:
    from Drowning_victims.Class import Drowning_victim

if __name__ == "__main__":
    # Définir le chemin de sauvegarde
    Path_saving = r"{self.filedir}"

    # Exécuter la simulation
    newdrowning = Drowning_victim(Path_dir=Path_saving)
    newdrowning.start()
"""

            # Créer et écrire le fichier exe_drowning.py
            with open(self.exe_file, "w", encoding="utf-8") as file:
                file.write(script_content)
            logging.info(f"Drowning simulation file created at: {self.exe_file}")
        except subprocess.CalledProcessError as e:
            logging.error(f"Error while creating the drowning simulation file: {e}")

    def run_code(self,event):
        if self.file_drowning is not None:
            import subprocess
            try:
                self.newdrowning.start()
                logging.info(_("Drowning simulation done."))
            except subprocess.CalledProcessError as e:
                logging.error(f"Error while running the drowning simulation file: {e}")
            # process = multiprocessing.Process(target=self.__main__())
            # process.start()  # Démarre code2 dans un processus distinct
        else:
            logging.error(('No drowning point selected, select one before starting the simulation'))

    def show_properties(self):

        self.w=800

        self.wp._set_gui(title='Parameters for the drowning simulation', toShow=True, w=self.w)
        self.wp.hide_selected_buttons([Buttons.Reload,Buttons.Save])

        select_button = wx.Button(self.wp,id=10,label="Wolf2D simulation")
        select_button.SetToolTip(_("Select reference Wolf2D simulation to choose your drowning point"))
        create_file_button = wx.Button(self.wp,id=11,label="Create exe file")
        create_file_button.SetToolTip(_("Create the executable file to run the drowning"))
        run_button = wx.Button(self.wp,id=12,label="Run")
        run_button.SetToolTip(_("Run the drowning simulation \nNot recommended here"))

        select_button.Bind(wx.EVT_BUTTON, self.selection_drowning_point)
        create_file_button.Bind(wx.EVT_BUTTON, self.create_exe_file)
        run_button.Bind(wx.EVT_BUTTON, self.run_code)
        run_button.SetBackgroundColour(wx.Colour(240,160,160))

        self.wp.sizerbut.Add(select_button,2,wx.EXPAND)
        self.wp.sizerbut.Add(create_file_button,2,wx.EXPAND)
        self.wp.sizerbut.Add(run_button,1,wx.EXPAND)


        self.wp.SetSizer(self.wp.sizer)
        # self.SetSize(w,h)
        self.wp.SetAutoLayout(1)
        self.wp.sizer.Fit(self.wp)

        self.wp.SetSize(0,0,self.w,800)
        self.wp.Show(True)

        # self.wp.myparams = self.merge_dicts(self.wp.myparams,self.wp.myparams_default)
        self.from_wp_to_dictionnary()
        self.newdrowning.from_dictionnary_to_attributes()

    def from_dictionnary_to_wp(self):
        """
        Return a Wolf_Param object that represents the parameters of the simulation,
        directly using the attributes of the class.
        """
        # Initialisation de l'objet Wolf_Param
        wp = Wolf_Param(
            parent=None,
            title="Drift of a drowning victim",
            to_read=False,
            withbuttons=True,
            toShow=False,
            init_GUI=False,
            force_even_if_same_default=True,
            filename=self.filename
        )

        params_dict = self.newdrowning.param_dict

        # Ajout des paramètres au Wolf_Param
        for current_section in params_dict.keys():
            for key in params_dict[current_section].keys():

                value = params_dict[current_section][key]["value"]
                description = params_dict[current_section][key]["description"]
                name = params_dict[current_section][key]["explicit name"]

                wp.add_param(
                    groupname=current_section,
                    name=name,
                    value=value,
                    type=params_dict[current_section][key]["type"],
                    whichdict="All" if params_dict[current_section][key]["mandatory"] else "Default",
                    jsonstr={"Values": params_dict[current_section][key]["choices"]} if params_dict[current_section][key]["choices"] else None,
                    comment= description
                )
        self.wp = wp

        self.newdrowning.time_goal = self.newdrowning.Days*24*60*60 + self.newdrowning.Hours*60*60 + self.newdrowning.Minutes*60 + self.newdrowning.Seconds #s
        wanted_time = np.array([self.newdrowning.t_initial])
        self.newdrowning.n_saved = 1
        for i in np.arange(10,self.newdrowning.time_goal+10,10):
            if i<60:
                wanted_time = np.append(wanted_time,i)
                self.newdrowning.n_saved += 1
            elif np.logical_and(i<10*60,(i%60==0)):
                wanted_time = np.append(wanted_time,i)
                self.newdrowning.n_saved += 1
            elif np.logical_and(i<30*60,(i%(5*60)==0)):
                wanted_time = np.append(wanted_time,i)
                self.newdrowning.n_saved += 1
            elif np.logical_and(i<60*60,(i%(10*60)==0)):
                wanted_time = np.append(wanted_time,i)
                self.newdrowning.n_saved += 1
            elif np.logical_and(i<=24*60*60,(i%(60*60)==0)):
                wanted_time = np.append(wanted_time,i)
                self.newdrowning.n_saved += 1
            elif np.logical_and(i<=2*24*60*60,(i%(2*60*60)==0)):
                wanted_time = np.append(wanted_time,i)
                self.newdrowning.n_saved += 1
            elif (i%(3*60*60)==0):
                wanted_time = np.append(wanted_time,i)
                self.newdrowning.n_saved += 1

        self.newdrowning.wanted_time = np.append(wanted_time,0)

    def from_wp_to_dictionnary(self):
        """
        Compare the parameters in self.wp with self.newdrowning.param_dict and update the values
        in self.newdrowning.param_dict when they differ.
        """
        # Charger le dictionnaire existant
        param_dict = self.newdrowning.param_dict

        # Parcourir les sections et les clés de wp
        for current_section in self.wp.myparams.keys():
            if current_section in param_dict:
                for key, wp_param in self.wp.myparams[current_section].items():
                    # Trouver la clé correspondante dans param_dict
                    for param_key, param_data in param_dict[current_section].items():
                        if param_data["explicit name"] == key:
                            # Comparer les valeurs et mettre à jour si elles diffèrent
                            if param_data["value"] != wp_param[key_Param.VALUE]:
                                param_dict[current_section][param_key]["value"] = wp_param[key_Param.VALUE]
                            break

        # Sauvegarder le dictionnaire mis à jour dans self.newdrowning.param_dict
        self.newdrowning.param_dict = param_dict

    def hide_properties(self):
        """
        Hide properties window
        """
        if self.wp is not None:
            self.wp.Destroy()
            self.wp = None

    def save(self):
        '''
        Save the parameters in a text file
        '''
        if self.filename is None:
            self.saveas()

        else:
            self.wp.Save(self.filename)

    def saveas(self):
        '''
        Save the parameters in a text file
        '''
        fdlg = wx.DirDialog(None, "Where should the parameters be stored? File automatically named parameters", style=wx.FD_SAVE)
        ret = fdlg.ShowModal()
        if ret == wx.ID_OK:
            self.filedir = fdlg.GetPath()
            self.filename = self.filedir + "/parameters.param"
            self.Path_saving = self.filedir
            self.wp.change_param("Paths","Save path",self.filedir)
            self.save()

        fdlg.Destroy()

    def load_results(self):
        """
        Load the results from the 'Results.npz' file and assign the arrays as attributes of the class.
        """

        # Construire le chemin du fichier Results.npz
        results_file = join(self.filedir, 'Results.npz')

        # Vérifier si le fichier existe
        if not os.path.exists(results_file):
            logging.error(f"Le fichier {results_file} est introuvable.")
            return

        # Charger le fichier npz
        with np.load(results_file, allow_pickle=True) as data:
            # Assigner les tableaux comme attributs de la classe
            self.Human = data['Human']
            self.Pos_b = data['Pos_b']
            self.U_b = data['U_b']
            self.Z_param = data['Z_param']
            self.wanted_time = data['wanted_time']
            self.time_b = data['time_b']

        self.Pos_b[:,0,:] += self.newdrowning.origx
        self.Pos_b[:,1,:] += self.newdrowning.origy

    def init_plot(self):

        self.bottom_cells = None
        self.bottom_kde = None
        self.vertex_bottom_run = None

        self.surface_cells = None
        self.surface_kde = None
        self.vertex_surface_run = None

        self.plot_runs = None
        self.plot_cells = None
        self.plot_KDE = None

    def read_oneresult(self,idx):
        """
        Read one result of the simulation and update the parameters in the GUI
        """

        count=0

        self.time_id = idx

        if self.plot_runs is not None:
            self.prepare_plot_runs_positions()
            count +=1
        if self.plot_cells is not None:
            self.prepare_plot_cells_positions()
            count +=1
        if self.plot_KDE is not None:
            self.prepare_plot_kde()
            count +=1

        if count==0:
            self.prepare_plot_runs_positions()

        return

    def read_last_result(self):
        """
        Read the last results of the simulation and update the parameters in the GUI
        """

        self.time_id = -1

        self.read_oneresult(idx=-1)

        return

    def find_minmax(self, update=False):
        """
        Generic function to find min and max spatial extent in data

        example : a WolfMapViewer instance needs spatial extent to zoom or test if
                  element must be plotted
        """

        self.xmin=999999.    # spatial extension - lower left corner X
        self.ymin=999999.    # spatial extension - lower left corner Y
        self.xmax=-999999.    # spatial extension - upper right corner X
        self.ymax=-999999.    # spatial extension - upper right corner Y

        if self.bottom_kde is not None:
            [xmin, xmax], [ymin, ymax] = self.bottom_kde.get_bounds()
            self.xmin = min(self.xmin, xmin)
            self.xmax = max(self.xmax, xmax)
            self.ymin = min(self.ymin, ymin)
            self.ymax = max(self.ymax, ymax)
        if self.surface_kde is not None:
            [xmin, xmax], [ymin, ymax] = self.surface_kde.get_bounds()
            self.xmin = min(self.xmin, xmin)
            self.xmax = max(self.xmax, xmax)
            self.ymin = min(self.ymin, ymin)
            self.ymax = max(self.ymax, ymax)

        if self.bottom_cells is not None:
            [xmin, xmax], [ymin, ymax] = self.bottom_cells.get_bounds()
            self.xmin = min(self.xmin, xmin)
            self.xmax = max(self.xmax, xmax)
            self.ymin = min(self.ymin, ymin)
            self.ymax = max(self.ymax, ymax)
        if self.surface_cells is not None:
            [xmin, xmax], [ymin, ymax] = self.surface_cells.get_bounds()
            self.xmin = min(self.xmin, xmin)
            self.xmax = max(self.xmax, xmax)
            self.ymin = min(self.ymin, ymin)
            self.ymax = max(self.ymax, ymax)

        if self.vertex_bottom_run is not None:
            self.vertex_bottom_run.find_minmax(update)
            self.xmin = min(self.xmin, self.vertex_bottom_run.xmin)
            self.xmax = max(self.xmax, self.vertex_bottom_run.xmax)
            self.ymin = min(self.ymin, self.vertex_bottom_run.ymin)
            self.ymax = max(self.ymax, self.vertex_bottom_run.ymax)
        if self.vertex_surface_run is not None:
            self.vertex_surface_run.find_minmax(update)
            self.xmin = min(self.xmin, self.vertex_surface_run.xmin)
            self.xmax = max(self.xmax, self.vertex_surface_run.xmax)
            self.ymin = min(self.ymin, self.vertex_surface_run.ymin)
            self.ymax = max(self.ymax, self.vertex_surface_run.ymax)

        pass

    def plot(self, sx=None, sy=None, xmin=None, ymin=None, xmax=None, ymax=None, size=None):
        """
        Plot data in OpenGL context
        """
        if self.plotted:

            self.plotting = True

            if self.bottom_kde is not None:
                self.bottom_kde.check_plot()
                self.bottom_kde.plot(sx, sy, xmin, ymin, xmax, ymax, size)
            if self.surface_kde is not None:
                self.surface_kde.check_plot()
                self.surface_kde.plot(sx, sy, xmin, ymin, xmax, ymax, size)

            if self.bottom_cells is not None:
                self.bottom_cells.check_plot()
                self.bottom_cells.plot(sx, sy, xmin, ymin, xmax, ymax, size)
            if self.surface_cells is not None:
                self.surface_cells.check_plot()
                self.surface_cells.plot(sx, sy, xmin, ymin, xmax, ymax, size)

            if self.vertex_bottom_run is not None:
                self.vertex_bottom_run.plot()
            if self.vertex_surface_run is not None:
                self.vertex_surface_run.plot()

            self.plotting = False

    def sort_positions_bodies(self):

        time_id = self.time_id

        ind_surface = np.where(self.Pos_b[:,2,time_id] > 0.2)[0]
        ind_bottom = np.where(self.Pos_b[:,2,time_id] <= 0.2)[0]
        if len(ind_surface) == 0:
            ind_surface = [0]
        if len(ind_bottom) == 0:
            ind_bottom = [0]

        return ind_bottom,ind_surface,time_id

    def prepare_plot_runs_positions(self):
        """
        Plot the runs position on a georeferenced map with bodies in blue being at the bottom and red being at the surface.
        """

        self.plot_runs = 1

        ind_bottom,ind_surface,time_id = self.sort_positions_bodies()

        self.vertex_bottom_run = cloud_vertices(mapviewer=self.mapviewer)
        self.vertex_surface_run = cloud_vertices(mapviewer=self.mapviewer)

        self.vertex_bottom_run.init_from_nparray(self.Pos_b[ind_bottom,:,time_id])
        self.vertex_surface_run.init_from_nparray(self.Pos_b[ind_surface,:,time_id])

        self.vertex_bottom_run.myprop.color = [40,50,250]
        self.vertex_surface_run.myprop.color = [250,100,80]

        self.vertex_bottom_run.myprop.alpha = 0.5
        self.vertex_surface_run.myprop.alpha = 0.5

        self.find_minmax(True)

        return

    def reset_plot_runs_positions(self):
        self.vertex_bottom_run = None
        self.vertex_surface_run = None
        self.plot_runs = None

    def kde_on_grid(self,points, bandwidth, xmin, xmax, ymin, ymax, grid_size):
        """
        Function used to calculate the kde on a point cloud. Use a large grid size to identify peaks and a small one to refine
        """


        x_grid = np.linspace(xmin, xmax, grid_size[0])
        y_grid = np.linspace(ymin, ymax, grid_size[1])
        X, Y = np.meshgrid(x_grid, y_grid)
        sample_grid = np.vstack([X.ravel(), Y.ravel()]).T

        kde = KernelDensity(bandwidth=bandwidth)
        kde.fit(points)
        Z = np.exp(kde.score_samples(sample_grid)).reshape(grid_size[0], grid_size[1])

        return Z, x_grid, y_grid

    def detect_peaks(self,x,y,radius,num_peaks=2):
        """
        Détecte les pics locaux dans une matrice 2D sans skimage.

        param: x X coordinate of the points cloud
        param: y Y coordinate of the points cloud
        param: radius size of the grid to detect peaks
        param: n_peaks number of peaks to detect

        """

        x += -self.newdrowning.origx
        y += -self.newdrowning.origy

        dx = self.newdrowning.dx
        dy = self.newdrowning.dy

        ij = np.array([np.int32(x/radius), np.int32(y/radius)]).T
        unique_positions, counts = np.unique(ij,axis=0, return_counts=True)

        ind_peaks = []
        selected_mask = np.zeros(len(counts), dtype=bool)  # pour marquer les indices déjà exclus

        while True:
            # On masque les indices déjà exclus
            valid_indices = np.where(~selected_mask)[0]
            if len(valid_indices) == 0:
                break

            # Trouver le max parmi les valides
            idx_max = valid_indices[np.argmax(counts[valid_indices])]
            ind_peaks.append(idx_max)

            # Marquer les indices trop proches pour les exclure ensuite
            pos_max = unique_positions[idx_max]
            i_diff = np.abs(unique_positions[:, 0] - pos_max[0])
            j_diff = np.abs(unique_positions[:, 1] - pos_max[1])
            too_close = (i_diff <= 0) & (j_diff <= 0)

            selected_mask |= too_close  # mettre à jour le masque d'exclusion

            if len(ind_peaks) >= num_peaks:
                break

        x_peaks = (unique_positions[ind_peaks,0]*radius) + radius/2 + self.newdrowning.origx
        y_peaks = (unique_positions[ind_peaks,1]*radius) + radius/2 + self.newdrowning.origy

        selected_peaks = np.zeros((len(ind_peaks),2))
        selected_peaks[:,0] = x_peaks
        selected_peaks[:,1] = y_peaks

        return selected_peaks

    def kde_refined_based_coarse(self, points, wolfarray, bandwidth=50,
                                coarse_grid_size=50, fine_grid_size=5,
                                window_size=200, radius=150, n_peaks=3):
        """
        Optimisation à 2 étages : détection des pics sur grille grossière puis raffinement local.

        Returns:
        - refined_peaks : coordonnées des pics raffinés
        - clusters : liste de points pour chaque cluster
        - coords : coordonnées (x, y) de chaque maille dans les zones raffinées
        - values : valeur KDE associée à chaque maille
        """
        array = wolfarray.array[:,:]

        x_min, y_min = points.min(axis=0)
        x_max, y_max = points.max(axis=0)

        # 1. Déduction de dx, dy depuis array
        ny, nx = array.shape
        dx = (x_max - x_min) / nx
        dy = (y_max - y_min) / ny

        # 3. Préparation des résultats
        all_indices = []
        all_values = []

        ij = wolfarray.get_ij_from_xy_array(points)
        unique_positions, counts = np.unique(ij,axis=0, return_counts=True)
        delta = radius/self.newdrowning.dx

        ind_peaks = []
        selected_mask = np.zeros(len(counts), dtype=bool)  # pour marquer les indices déjà exclus

        while True:
            # On masque les indices déjà exclus
            valid_indices = np.where(~selected_mask)[0]
            if len(valid_indices) == 0:
                break

            # Trouver le max parmi les valides
            idx_max = valid_indices[np.argmax(counts[valid_indices])]
            ind_peaks.append(idx_max)

            # Marquer les indices trop proches pour les exclure ensuite
            pos_max = unique_positions[idx_max]
            i_diff = np.abs(unique_positions[:, 0] - pos_max[0])
            j_diff = np.abs(unique_positions[:, 1] - pos_max[1])
            too_close = (i_diff <= delta) & (j_diff <= delta)

            selected_mask |= too_close  # mettre à jour le masque d'exclusion

            if len(ind_peaks) >= n_peaks:
                break

        for ind_peak in ind_peaks:

            x0 = int((unique_positions[ind_peak,0]-delta)*dx+x_min)
            x1 = int((unique_positions[ind_peak,0]+delta)*dx+x_min)
            y0 = int((unique_positions[ind_peak,1]-delta)*dy+y_min)
            y1 = int((unique_positions[ind_peak,1]+delta)*dy+y_min)

            grid_nx = max(2, int((x1 - x0) / dx))
            grid_ny = max(2, int((y1 - y0) / dy))

            Z_fine, xg_fine, yg_fine = self.kde_on_grid(
                points, bandwidth, x0, x1, y0, y1, grid_size=(grid_nx, grid_ny)
            )

            # Z_fine, xg_fine, yg_fine = self.kde_on_grid(
            #     local_points, bandwidth, x0, x1, y0, y1, grid_size=grid
            # )

            # Coordonnées physiques -> indices dans `array`
            Y, X = np.meshgrid(yg_fine, xg_fine, indexing='ij')
            x_flat = X.ravel()
            y_flat = Y.ravel()
            i = np.floor((y_flat - y_min) / dy).astype(int)
            j = np.floor((x_flat - x_min) / dx).astype(int)

            # Filtrage : indices valides dans array
            valid = (i >= 0) & (i < ny) & (j >= 0) & (j < nx)
            indices = np.stack((i[valid], j[valid]), axis=1)  # shape (n, 2)
            values = Z_fine.ravel()[valid]

            all_indices.append(indices)
            all_values.append(values)

        # Empilement final
        coords_array = np.vstack(all_indices) if all_indices else np.empty((0, 2), dtype=int)
        values_array = np.concatenate(all_values) if all_values else np.array([])

        return coords_array,values_array

    def prepare_plot_kde(self):
        """
        Plot the kernel density estimation of positions on a georeferenced map with bodies in blue being at the bottom and red being at the surface.
        """

        self.plot_KDE = 1

        self.n_peaks = 2

        ind_bottom,ind_surface,time_id = self.sort_positions_bodies()

        head = header_wolf()

        head.set_origin(self.newdrowning.origx, self.newdrowning.origy)
        head.set_resolution(self.newdrowning.dx,  self.newdrowning.dy)
        head.nbx, head.nby = self.newdrowning.nbx, self.newdrowning.nby
        head.set_translation(0., 0.)

        self.bottom_kde = WolfArray(mapviewer=self.mapviewer, srcheader= head, nullvalue= 0.)
        self.surface_kde = WolfArray(mapviewer=self.mapviewer, srcheader= head, nullvalue= 0.)

        for locarray, locind in zip([self.bottom_kde, self.surface_kde],
                                    [ind_bottom, ind_surface]):

            xy = self.Pos_b[locind,:2,time_id]
            coords,values = self.kde_refined_based_coarse(xy,locarray,bandwidth=50,coarse_grid_size=200,fine_grid_size=5,window_size=50,radius=25,n_peaks=self.n_peaks)

            locarray.array[:,:] = 0.
            locarray.array[coords[:,1],coords[:,0]] = values
            locarray.mask_data(0.)

        self.bottom_kde.mypal.defaultblue_minmax(self.bottom_kde.array)
        self.surface_kde.mypal.defaultred_minmax(self.surface_kde.array)

        self.bottom_kde.reset_plot()
        self.surface_kde.reset_plot()

        return

    def reset_plot_kde(self):
        self.bottom_kde = None
        self.surface_kde = None
        self.plot_KDE = None

    def prepare_plot_cells_positions(self):
        """
        Plot the cells of the WOLF simulation, with a colorbar associated to the number of elements in the cell
        """
        self.plot_cells = 1

        ind_bottom,ind_surface,time_id = self.sort_positions_bodies()

        head = header_wolf()

        head.set_origin(self.newdrowning.origx, self.newdrowning.origy)
        head.set_resolution(self.newdrowning.dx,  self.newdrowning.dy)
        head.nbx, head.nby = self.newdrowning.nbx, self.newdrowning.nby
        head.set_translation(0., 0.)

        self.bottom_cells = WolfArray(mapviewer=self.mapviewer, srcheader= head, nullvalue= 0.)
        self.surface_cells = WolfArray(mapviewer=self.mapviewer, srcheader= head, nullvalue= 0.)

        for locarray, locind in zip([self.bottom_cells, self.surface_cells],
                                    [ind_bottom, ind_surface]):

            # i_bottom,j_bottom = self.bottom_cells.get_ij_from_xy_array(self.Pos_b[ind_bottom,:2,time_id])
            ij = locarray.get_ij_from_xy_array(self.Pos_b[locind,:2,time_id])

            unique_positions, counts = np.unique(ij,axis=0, return_counts=True)

            locarray.array[:,:] = 0.
            locarray.array[unique_positions[:,0],unique_positions[:,1]] = counts/self.newdrowning.n_b*100
            locarray.mask_data(0.)

        array = self.bottom_cells.array
        self.bottom_cells.mypal.nb = 2
        self.bottom_cells.mypal.values = np.asarray([np.min(array), np.max(array)], dtype=np.float64)
        self.bottom_cells.mypal.colors = np.asarray([[175, 200, 255, 255], [0, 0, 255, 255]], dtype=np.int32)
        self.bottom_cells.mypal.colorsflt = np.asarray([[0., 0., 0., 1.], [1., 1., 1., 1.]], dtype=np.float64)
        self.bottom_cells.mypal.fill_segmentdata()

        array = self.surface_cells.array
        self.surface_cells.mypal.nb = 2
        self.surface_cells.mypal.values = np.asarray([np.min(array), np.max(array)], dtype=np.float64)
        self.surface_cells.mypal.colors = np.asarray([[255, 200, 175, 255], [0, 0, 255, 255]], dtype=np.int32)
        self.surface_cells.mypal.colorsflt = np.asarray([[0., 0.2, 0.6, 1.], [1., 1., 1., 1.]], dtype=np.float64)
        self.surface_cells.mypal.fill_segmentdata()

        self.bottom_cells.reset_plot()
        self.surface_cells.reset_plot()

        return

    def reset_plot_cells_positions(self):
        self.bottom_cells = None
        self.surface_cells = None
        self.plot_cells = None

    def zoom_on_hotspots(self,memory_view):
        """
        Zoom on the hotspots of the KDE
        """

        delta = 150

        ind_bottom,ind_surface,time_id = self.sort_positions_bodies()

        xy_peaks_bottom = self.detect_peaks(self.Pos_b[ind_bottom,0,time_id], self.Pos_b[ind_bottom,1,time_id], radius=100, num_peaks=self.n_peaks)
        xy_peaks_surface = self.detect_peaks(self.Pos_b[ind_surface,0,time_id], self.Pos_b[ind_surface,1,time_id], radius=100, num_peaks=self.n_peaks)
        xy_peaks = np.concatenate((xy_peaks_bottom, xy_peaks_surface),axis=0)

        names = ['Highest peak at the bottom','Second peak at the bottom','Highest peak at the surface','Second peak at the surface']

        for locxy,locname in zip(xy_peaks,names):
            xmin = locxy[0] - delta
            xmax = locxy[0] + delta
            ymin = locxy[1] - delta
            ymax = locxy[1] + delta

            memory_view.add_view(locname, self.mapviewer.canvaswidth, self.mapviewer.canvasheight, xmin, xmax, ymin, ymax)

        return

    def get_bodies_characteristics(self):
        """
        Plots a table of the Dataframe panda "Human" with the characteristics of each run
        """

        if not isinstance(self.Human, pd.DataFrame):
            Human = pd.DataFrame(self.Human, columns=COLUMNS_HUMAN)
        else:
            Human = self.Human

        self.grid = PandasGrid(parent=self.mapviewer, id = self.idx, df=Human)
        self.grid.ShowModal()
        self.grid.Destroy()

        return

    def get_vertical_position_proportion(self):
        """
        Gives the proportion of bodies at the surface and at the bottom of the water
        """

        def update_pie(time_idx):
            """Met à jour uniquement la KDE en fonction de l'index temporel sélectionné."""
            time_idx = int(time_idx)  # Assurer que l'indice est un entier
            time_value = self.wanted_time[time_idx]  # Temps sélectionné à afficher

            ax.clear()
            # Mise à jour du titre pour refléter le temps sélectionné
            days = time_value // (24*3600)
            hours = (time_value % (24*3600)) // 3600
            minutes = (time_value % (3600)) // 60
            seconds = time_value % 60
            ax.set_title(f"Proportion of bodies at the bottom and surface after \n{days} days, {hours} hours, {minutes} minutes, {seconds} seconds")

            # Obtenir les positions x, y à l'instant de temps spécifié par time_idx
            z = self.Pos_b[:,2,time_idx]

            surface = np.where(z > 0.2)[0]
            bottom = np.where(z <= 0.2)[0]

            counts = [len(surface)/self.newdrowning.n_b*100, len(bottom)/self.newdrowning.n_b*100]
            labels = ['Surface', 'Bottom']
            colors = [[1,0.7,0.6,1], [0.6,0.7,1,1]]

            ax.pie(counts, labels=labels, colors=colors, autopct='%1.1f%%')

            # Rafraîchissement du graphique
            fig.canvas.draw_idle()

        # Initialisation de la figure et des axes
        fig, ax = plt.subplots()

        time_idx_initial = 0
        z = self.Pos_b[:,2,time_idx_initial]

        surface = np.where(z > 0.2)[0]
        bottom = np.where(z <= 0.2)[0]

        counts = [len(surface)/self.newdrowning.n_b*100, len(bottom)/self.newdrowning.n_b*100]
        labels = ['Surface', 'Bottom']
        colors = [[1,0.7,0.6,1], [0.6,0.7,1,1]]

        ax.pie(counts, labels=labels, colors=colors, autopct='%1.1f%%')

        # Création du slider pour ajuster l'indice temporel
        ax_slider = plt.axes([0.1, 0.1, 0.8, 0.05], facecolor='lightgoldenrodyellow')
        time_slider = Slider(ax_slider, 'Time', 0, len(self.wanted_time) - 2, valinit=time_idx_initial, valstep=1)

        # Mise à jour de la KDE lorsque le slider est utilisé
        time_slider.on_changed(update_pie)

        plt.show()


        return

class ProgressBar(wx.Frame):
    """
    Creates and manages the progress frame
    """
    def __init__(self,parent, n_processes,total):
        super(ProgressBar, self).__init__(parent)
        self.n_processes = n_processes
        self.total = total

        # Set up the main panel and sizer
        panel = wx.Panel(self)
        sizer = wx.BoxSizer(wx.VERTICAL)

        progress_bar = wx.Gauge(panel, range=100)
        sizer.Add(progress_bar, flag=wx.EXPAND | wx.ALL, border=5)
        self.progress_bars = progress_bar
        self.progress_text = wx.StaticText(panel, label="0%")
        sizer.Add(self.progress_text, flag=wx.ALIGN_CENTER | wx.TOP, border=5)

        panel.SetSizer(sizer)
        self.SetTitle(_("Drowning Progress"))
        self.SetSize((300, 90))

    def update_progress(self, progress_dict):
        """
        Update the progress bars based on the values in `progress_dict`.
        """

        min_progress_value = None
        for i, progress in progress_dict.items():
            # Assume progress is a percentage (0 to 100)
            if progress is not None:
                if min_progress_value is None or progress < min_progress_value:
                    min_progress_value = progress
                    progress_percent = int(min_progress_value/self.total*100)

                self.progress_bars.SetValue(progress_percent)
                self.progress_text.SetLabel(f"{progress_percent}%")
                self.SetTitle(f"Drowning Progress - {progress_percent}%")


class ProgressImage(wx.Frame):
    """
    Creates and manages the progress frame with a fractioned image appearance
    """
    def __init__(self, n_processes, total, *args, **kw):
        super(ProgressImage, self).__init__(*args, **kw)
        self.n_processes = n_processes
        total_segments = 10*n_processes
        self.total_segments = total_segments
        self.total = total

        # Set up the main panel and sizer
        panel = wx.Panel(self)
        grid_sizer = wx.GridSizer(rows=total_segments, cols=n_processes, gap=(5, 5))

        current_dir = Path(__file__).resolve().parent
        # Path to your main image (set it to a suitable path)
        self.image_path = str(current_dir / "image.png")

        # Load the image
        image = wx.Image(str(self.image_path), wx.BITMAP_TYPE_PNG)
        img_width, img_height = image.GetSize()

        # Calculate segment dimensions
        segment_height = img_height // total_segments
        segment_width = img_width // n_processes

        # Initialize a 2D list to hold each segment for each process
        self.image_segments = []

        # Create a grid of segments for each process
        for row in range(total_segments):
            row_segments = []
            for col in range(n_processes):
                # Extract the specific segment for each cell in the grid
                x = col * segment_width
                y = row * segment_height
                segment = image.GetSubImage((x, y, segment_width, segment_height))

                # Create a bitmap for the segment and add it to the grid, initially hidden
                segment_bitmap = wx.StaticBitmap(panel, bitmap=wx.Bitmap(segment))
                segment_bitmap.Hide()  # Hide initially; show as progress advances
                grid_sizer.Add(segment_bitmap, flag=wx.ALIGN_CENTER)
                row_segments.append(segment_bitmap)

            self.image_segments.append(row_segments)

        panel.SetSizer(grid_sizer)
        self.SetTitle(_("Drowning Progress"))
        self.SetSize((img_width + 50, img_height + 50))

    def update_progress(self, progress_dict):
        """
        Update the visibility of image segments based on the progress.
        """
        for process_id, progress in progress_dict.items():
            if progress is not None:
                # Calculate the number of segments to show based on progress
                num_segments_to_show = int((progress / self.total) * (self.total_segments // self.n_processes))

                # Show the segments that correspond to the current progress
                for segment_id in range(num_segments_to_show):
                    self.image_segments[segment_id][process_id].Show()

        # Refresh the layout after updating visibility
        self.Layout()
        self.Refresh()
