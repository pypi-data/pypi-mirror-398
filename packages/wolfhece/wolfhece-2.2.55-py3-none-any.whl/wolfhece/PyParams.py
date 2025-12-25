"""
Author: HECE - University of Liege, Pierre Archambeau
Date: 2024

Copyright (c) 2024 University of Liege. All rights reserved.

This script and its content are protected by copyright law. Unauthorized
copying or distribution of this file, via any medium, is strictly prohibited.
"""

import wx
import wx.propgrid as pg
import pandas as pd
import os.path
import json
import logging
from typing import Union, Literal
from enum import Enum
from copy import deepcopy
import numpy as np
from pathlib import Path

try:
    from .PyTranslate import _
except:
    from wolfhece.PyTranslate import _

if not '_' in __builtins__:
    import gettext
    _=gettext.gettext

PARAM_TRUE = '.True.'
PARAM_FALSE = '.False.'
PREFIX_DEFAULT = 'def'

class Type_Param(Enum):
    """
    Enum to define the type of a parameter

    Strings are also used by Fortran Code -- modify with care
    """
    Integer_or_Float = 'Integer_or_Float'
    Integer = 'Integer'
    Logical = 'Logical'
    Float = 'Float'
    File = 'File'
    Directory = 'Directory'
    Color = 'Color'
    Fontname = 'Fontname'
    String = 'String'
    Empty = ''
    Double = 'Double'
    Real = 'Real'
    Enum = 'Enum'


class key_Param(Enum):
    """
    Enum to define the keys of a parameter

    """
    NAME = 'name'
    TYPE = 'type'
    VALUE = 'value'
    COMMENT = 'comment'
    ADDED_JSON = 'added_json'
    ENUM_CHOICES = 'enum_choices'

class Buttons(Enum):
    """ Enum to define the buttons """
    Load = 'Load'
    Save = 'Save'
    Apply = 'Apply'
    Reload = 'Reload'

def new_json(values:dict=None, fullcomment:str='') -> dict:
    """
    Create a new JSON string from values and fullcomment

    :param values : values to store in the JSON string - dict of key:value - value must be integer
    :param fullcomment : full comment to store in the JSON string - str - can be multiline with \n
    """
    return {"Values":values, "Full_Comment":fullcomment}

def new_infos_incr(groupname:str= None, paramname:str='nb', min:int=1, max:int=100) -> tuple[str]:
    """
    Create a new string for an incrementable group or parameter

    :param groupname : name of the reference group (optional) -- if ommitted, the reference group is in the same group as the parameter
    :param paramname : name of the reference parameter
    :param min : minimum value
    :param max : maximum value
    """
    if groupname is None:
        return paramname, str(min), str(max)
    else:
        return groupname, paramname, str(min), str(max)

# FIXME : Généliser avec les dictionnaire avec Enum
def search_type(chain:str) -> Type_Param:
    """ recherche du typage dans une chaîne de caractères """

    if chain.lower().find(Type_Param.Integer.value.lower())>-1 and chain.find(Type_Param.Double.value.lower())>-1:
        return Type_Param.Integer_or_Float
    elif chain.lower().find(Type_Param.Integer.value.lower())>-1:
        return Type_Param.Integer
    elif chain.lower().find(Type_Param.Logical.value.lower())>-1:
        return Type_Param.Logical
    elif chain.lower().find(Type_Param.Double.value.lower())>-1 or chain.find('dble')>-1 or chain.find(Type_Param.Real.value.lower())>-1:
        return Type_Param.Float
    elif chain.lower().find('({})'.format(Type_Param.File.value.lower()))>-1:
        return Type_Param.File
    elif chain.lower().find('({})'.format(Type_Param.Directory.value.lower()))>-1 or chain.find('(dir)')>-1:
        return Type_Param.Directory
    elif chain.lower().find(Type_Param.Enum.value.lower())>-1:
        return Type_Param.Enum
    else:
        return Type_Param.String


class Wolf_Param(wx.Frame):
    """
    **FR**
        Gestion des paramètres au format WOLF.

        **Fichier texte**

        Les fichiers '.param' sont des fichiers texte contenant des paramètres de type nom=valeur et compatibles avec les codes Fortran.
        L'extension '.param.default' est utilisée pour stocker les paramètres par défaut.

        Une autre extension est possible mais un fichier '.default' sera créé automatiquement si ce fichier n'existe pas.

        Le séparateur (nom, valeur, commentaire) est la tabulation '\t'. Aucun autre caractère ne doit être utilisé comme séparateur.

        Les groupes sont définis par un nom suivi de ':'. Cela signifie que ':' ne peut pas être utilisé dans un nom de paramètre.

        Les lignes débutant par '%' sont des commentaires. Il est possible d'ajouter du code JSON dans un commentaire. Pour cela, il faut ajouter '%json' au début de la ligne suivi d'un dictionnaire (e.g. %json{"Values":{'key1':1, 'key2':2}, "Full_Comment":"fullcomment"} ).

        **Organisation Python**

        L'objet Python est basé sur des dictionnaires Python. Un dictionnaire par groupe de paramètres.

        Les paramètres sont donc stockés dans un dictionnaire de dictionnaires. Le premier niveau est le nom du groupe, le second niveau est le nom du paramètre.

        Les paramètres disposent des clés suivantes :
            - name : nom du paramètre (str)
            - type : type du paramètre (str) -- see Type_Param
            - value : valeur du paramètre (str) -- peut être converti dynamiquement en int, float, bool, str, ... sur base du type
            - comment : commentaire du paramètre (str) -- helpful to understand the parameter
            - added_json : dictionnaire contenant des informations supplémentaires (optionnel) -- permet de stocker des informations supplémentaires sur le paramètre (ex : valeurs possibles, commentaires étendus, ...)

        **Dictionnaires**

        Il existe un dictionnaire de valeurs par défaut "myparams_default". Pour l'interaction Python-Fortran, c'est le Fortran qui écrit ces paramètres.
        Il existe un dictionnaire de paramètres actifs "myparams". Il est utilisé pour stocker les paramètres modifiés par l'utilisateur. Normalement, seuls les paramètres modifiés par l'utilisateur sont stockés dans ce dictionnaire et sont écrits sur disque.

        **Groupe/Paramètre incrémentable**

        Il est également possible de définir des groupes ou des paramètres incrémentables.
        Pour cela, dans le nom du groupe/paramètre, il faut ajouter, à l'emplacement souhaité du **numéro** du groupe/paramètre, des informations entre '$...$' :
            - groupname : nom du groupe (uniquement pour groupe incrémentable)
            - paramname : nom du paramètre contenant le nombre de groupe/paramètre
            - min : valeur minimale
            - max : valeur maximale

        Le nombre de groupes est ainsi défini par le couple (key:value) = (groupname:paramname). Le nombre de groupes doit donc être logiquement positionné dans un groupe distinct.
        Le nombre de paramètres est ainsi défini par le paramètre "paramname" qui est attendu dans le groupe contenant le paramètre incrémentable.
        Le nombre de groupes/paramètres est un entier compris entre 'min' et 'max'.

        Les informations génériques sont stockées dans les dictionnaires "myIncGroup" et "myIncParam".

        **UI**

        Une interface graphique est disponible pour modifier les paramètres. Elle est basée sur "wxPython" et la classe "wxPropertyGrid".
        L'attribut wx_exists permet de savoir si wxPython est en cours d'excution ou non.

        **Accès aux données**

        Les paramètres sont accessibles via la procédure __getitem__ en fournissant un tuple (groupname, paramname).
        Il est possible de modifier un paramètre via la procédure __setitem__.

        Il est possible :
            - d'ajoutrer un groupe via la procédure add_group. Pour un groupe incrémentabe, le nom doit contenir les infos génériques entre '$...$'.
            - d'ajouter un paramètre ou un paramètre incrémentable via la procédure addparam :
                - pour un paramètre classique en choisissant le dictionnaire cible ['All', 'Default', 'Active', 'IncGroup', '']
                    - '' == 'Active'
                    - 'All' == 'Default' + 'Active'
                    - 'IncGroup' pour ajouter un paramètre au template du groupe incrémentable --> sera dupliqué lors de la MAJ du nompbre réel de groupes
                - pour un paramètre incrémentable, en fournissant les données nécessaires dans une chaîne $n(refname,min,max)$ ou $n(groupname,refname,min,max)$
                - si le groupe visé n'existe pas, il sera créé si toutes les infos sont disponibles.
            - d'ajouter seulement un paramètre incrémentable via la procédure add_IncParam.

    **EN**
        Management of parameters in WOLF format.

        **Text File**

        '.param' files are text files containing parameters in the name=value format and compatible with Fortran codes.
        The '.param.default' extension is used to store default parameters.

        Another extension is possible, but a '.default' file will be automatically created if this file does not exist.

        The separator (name, value, comment) is the tab character '\t'. No other character should be used as a separator.

        Groups are defined by a name followed by ':'. This means that ':' cannot be used in a parameter name.

        Lines starting with '%' are comments. It is possible to add JSON code in a comment. To do this, add '%json' at the beginning of the line followed by a dictionary (e.g., %json{"Values":{'key1':1, 'key2':2}, "Full_Comment":"fullcomment"}).

        **Python Organization**

        The Python object is based on Python dictionaries. One dictionary per parameter group.

        Therefore, parameters are stored in a dictionary of dictionaries. The first level is the group name, and the second level is the parameter name.

        Parameters have the following keys:
            - name: parameter name (str)
            - type: parameter type (str) -- see Type_Param
            - value: parameter value (str) -- can be dynamically converted to int, float, bool, str, ... based on the type
            - comment: parameter comment (str) -- helpful to understand the parameter
            - added_json: dictionary containing additional information (optional) -- used to store additional information about the parameter (e.g., possible values, extended comments, ...)

        **Dictionaries**

        There is a default values dictionary "myparams_default." For Python-Fortran interaction, Fortran writes these parameters.
        There is an active parameters dictionary "myparams." It is used to store parameters modified by the user. Normally, only parameters modified by the user are stored in this dictionary and written to disk.

        **Incrementable Group/Parameter**

        It is also possible to define incrementable groups or parameters.
        To do this, in the group/parameter name, add information between '$...$' at the desired **number** location of the group/parameter:
            - groupname: group name (only for incrementable group)
            - paramname: parameter name containing the group/parameter number
            - min: minimum value
            - max: maximum value

        The number of groups is defined by the (key:value) pair (groupname:paramname). The number of groups must logically be positioned in a distinct group.
        The number of parameters is defined by the "paramname" parameter expected in the group containing the incrementable parameter.
        The number of groups/parameters is an integer between 'min' and 'max'.

        Generic information is stored in the "myIncGroup" and "myIncParam" dictionaries.

        **UI**

        A graphical interface is available to modify parameters. It is based on "wxPython" and the "wxPropertyGrid" class.
        The wx_exists attribute indicates whether wxPython is currently running or not.

        **Data Access**

        Parameters are accessible via the __getitem__ method by providing a tuple (groupname, paramname).
        It is possible to modify a parameter via the __setitem__ method.

        It is possible to:
            - add a group via the add_group method. For an incrementable group, the name must contain generic information between '$...$'.
            - add a parameter or an incrementable parameter via the addparam method:
                - for a regular parameter by choosing the target dictionary ['All', 'Default', 'Active', 'IncGroup', '']
                    - '' == 'Active'
                    - 'All' == 'Default' + 'Active'
                    - 'IncGroup' to add a parameter to the template of the incrementable group --> will be duplicated when updating the actual number of groups
                - for an incrementable parameter, by providing the necessary data in a string $n(refname,min,max)$ or $n(groupname,refname,min,max)$
                - if the targeted group does not exist, it will be created if all information is available.
            - only add an incrementable parameter via the add_IncParam method.

    """

    # Définition des propriétés
    filename:str                        # File name
    myparams:dict[str, dict]            # dict for active parameters, see key_Param for keys
    myparams_default:dict[str, dict]    # dict for default parameters, see key_Param for keys

    myIncGroup:dict                     # dict for incrementable groups
    myIncParam:dict                     # dict for incrementable parameters

    prop:pg.PropertyGridManager         # wxPropertyGridManager -- see UI
    wx_exists:bool                      # True if wxPython is running

    def __init__(self,
                 parent:wx.Window = None,
                 title:str = "Default Title",
                 w:int = 500,
                 h:int = 800,
                 ontop:bool   = False,
                 to_read:bool = True,
                 filename:str = '',
                 withbuttons: bool = True,
                 DestroyAtClosing:bool = True,
                 toShow:bool = True,
                 init_GUI:bool = True,
                 force_even_if_same_default:bool = False,
                 toolbar:bool = True):
        """
        Initialisation

        :param parent : parent frame (wx.Window)
        :param title : title of the frame
        :param w : width of the frame
        :param h : height of the frame
        :param ontop : if True, the frame will be on top of all other windows
        :param to_read : if True, the file will be read
        :param filename : filename to read
        :param withbuttons : if True, buttons will be displayed
        :param DestroyAtClosing : if True, the frame will be destroyed when closed
        :param toShow : if True, the frame will be displayed
        :param force_even_if_same_default : if True, the parameter will be displayed even if the default and active parameters are the same

        Callbacks (see 'set_callbacks'):
            - callback : callback function when 'apply' is pressed
            - callbackdestroy : callback function before destroying the frame

        """

        # Initialisation des propriétés
        self.filename=filename
        self.myparams={}
        self.myparams_default={}
        self.myIncGroup={}
        self.myIncParam={}
        self.update_incr_at_every_change = True

        self._callback:function = None
        self._callbackdestroy:function = None

        self.wx_exists = wx.App.Get() is not None # test if wx App is running
        self.show_in_active_if_default = force_even_if_same_default

        if to_read:
            self.ReadFile(filename)

        self.prop = None
        self.sizer = None

        if self.wx_exists and init_GUI:
            self._set_gui(parent,
                          title, w, h,
                          ontop, to_read,
                          withbuttons,
                          DestroyAtClosing,
                          toShow,
                          toolbar=toolbar)

    def __getstate__(self):
        state =  self.__dict__.copy()
        # Remove the wxPython GUI from the state to avoid pickling issues
        state.pop('prop', None)
        state.pop('sizer', None)
        state.pop('callback', None)
        state.pop('callbackdestroy', None)
        state.pop('DestroyAtClosing', None)
        state.pop('show_in_active_if_default', None)
        state.pop('sizerbut', None)
        state.pop('myIncGroup', None)
        state.pop('myIncParam', None)
        state.pop('update_incr_at_every_change', None)
        state.pop('wxparent', None)
        state.pop('gui_hydrometry', None)
        state.pop('cloud_stations_real', None)
        state.pop('cloud_stations', None)
        state.pop('gui_hydrometry', None)

        return state

    def __setstate__(self, state):

        self.__dict__.update(state)

        # Reinitialize the wxPython GUI if it was not initialized before pickling
        if self.wx_exists:
            self._set_gui()

    @property
    def has_prop(self) -> bool:
        """ Return True if the property grid is available """
        return self.prop is not None

    @property
    def has_gui(self) -> bool:
        """ Return True if the own GUI is available"""

        return self.sizer is not None

    def ensure_prop(self, wxparent = None, show_in_active_if_default:bool = False, height:int= 600):
        """ Ensure that the property grid is available """

        if self.wx_exists:
            if not self.has_prop:
                self._set_only_prop(wxparent)
                self.show_in_active_if_default = show_in_active_if_default
                self.prop.SetSizeHints(0,height)

            self.Populate()


    def ensure_gui(self,
                   title:str = "Default Title",
                   w:int = 500, h:int = 800,
                   ontop:bool = False,
                   to_read:bool = True,
                   withbuttons:bool = True,
                   DestroyAtClosing:bool = True,
                   toShow:bool = True,
                   full_style:bool = False):
        """ Ensure that the GUI is available """

        if not self.has_gui and self.wx_exists:
            self._set_gui(title=title,
                          w=w, h=h,
                          ontop=ontop,
                          to_read=to_read,
                          withbuttons=withbuttons,
                          DestroyAtClosing=DestroyAtClosing,
                          toShow=toShow,
                          full_style=full_style,
                          )

    def copy(self):
        """ Return a deep copy of the object """

        newparams = Wolf_Param()

        for group, params in self.myparams.items():
            newparams.myparams[group] = deepcopy(params)

        for group, params in self.myparams_default.items():
            newparams.myparams_default[group] = deepcopy(params)

        newparams.myIncGroup = deepcopy(self.myIncGroup)

        newparams.myIncParam = deepcopy(self.myIncParam)

        return newparams

    def is_like(self, other:"Wolf_Param") -> bool:
        """ Test if the object is like another object """

        # if self.filename != other.filename:
        #     return False

        if self.myparams != other.myparams:
            return False

        if self.myparams_default != other.myparams_default:
            return False

        if self.myIncGroup != other.myIncGroup:
            return False

        if self.myIncParam != other.myIncParam:
            return False

        return True

    def diff(self, other:"Wolf_Param", exclude_incremental:bool = False) -> dict:
        """ Return the differences between two objects """

        diff = {}

        # if self.filename != other.filename:
        #     diff["filename"] = (self.filename, other.filename)

        if self.myparams != other.myparams:
            for group in self.myparams.keys():
                for param in self.myparams[group].keys():
                    try:
                        if self.myparams[group][param] != other.myparams[group][param]:
                            diff[(group, param)] = (self.myparams[group][param], other.myparams[group][param])
                    except:
                        diff[(group, param)] = (self.myparams[group][param], None)

        if self.myparams_default != other.myparams_default:
            for group in self.myparams_default.keys():
                for param in self.myparams_default[group].keys():
                    try:
                        if self.myparams_default[group][param] != other.myparams_default[group][param]:
                            diff[(group, param)] = (self.myparams_default[group][param], other.myparams_default[group][param])
                    except:
                        diff[(group, param)] = (self.myparams_default[group][param], None)

        if exclude_incremental:
            return diff

        if self.myIncGroup != other.myIncGroup:
            for group in self.myIncGroup.keys():
                try:
                    if self.myIncGroup[group] != other.myIncGroup[group]:
                        diff["myIncGroup"] = (self.myIncGroup[group], other.myIncGroup[group])
                except:
                    diff["myIncGroup"] = (self.myIncGroup[group], None)

        if self.myIncParam != other.myIncParam:
            for group in self.myIncParam.keys():
                try:
                    for param in self.myIncParam[group].keys():
                        if self.myIncParam[group][param] != other.myIncParam[group][param]:
                            diff["myIncParam"] = (self.myIncParam[group][param], other.myIncParam[group][param])
                except:
                    diff["myIncParam"] = (self.myIncParam[group][param], None)

        return diff

    def set_callbacks(self, callback_update, callback_destroy):
        """ Set the callbacks for the update and destroy events """

        self.callback = callback_update
        self.callbackdestroy = callback_destroy

    def get_nb_groups(self) -> tuple[int, int]:
        """ Return the number of groups in active and default parameters """
        return len(self.myparams.keys()), len(self.myparams_default.keys())

    def get_nb_params(self, group:str) -> tuple[int, int]:
        """ Return the number of parameters in a group in active and default parameters """
        return len(self.myparams[group].keys()) if group in self.myparams.keys() else None, len(self.myparams_default[group].keys()) if group in self.myparams_default.keys() else None

    def get_nb_inc_params(self) -> int:
        """ Return the number of incrementable parameters """
        return len(self.myIncParam.keys())

    def get_nb_inc_groups(self) -> int:
        """ Return the number of incrementable groups """
        return len(self.myIncGroup.keys())

    def get_group_keys(self) -> list[str]:
        """ Return the keys of the active parameters """
        return list(self.myparams.keys())

    def get_default_group_keys(self) -> list[str]:
        """ Return the keys of the default parameters """
        return list(self.myparams_default.keys())

    def get_param_keys(self, group:str) -> list[str]:
        """ Return the keys of the active parameters """
        if group in self.myparams.keys():
            return list(self.myparams[group].keys())
        else:
            return []

    @property
    def callback(self):
        """ Return the callback function """
        return self._callback

    @callback.setter
    def callback(self, value):
        """ Set the callback function """
        self._callback= value

    @property
    def callbackdestroy(self):
        """ Return the callback function """
        return self._callbackdestroy

    @callbackdestroy.setter
    def callbackdestroy(self, value):
        """ Set the callback function """
        self._callbackdestroy= value

    # GUI Events - WxPython
    # ---------------------

    def _set_gui(self,
                parent:wx.Window = None,
                title:str = "Default Title",
                w:int = 500,
                h:int = 800,
                ontop:bool = False,
                to_read:bool = True,
                withbuttons:bool = True,
                DestroyAtClosing:bool = True,
                toShow:bool = True,
                full_style = False,
                toolbar:bool = True):
        """
        Set the GUI if wxPython is running

        Gui is based on wxPropertyGridManager.

        On the left, there is a group of buttons to load, save, apply or reload the parameters.
        On the right, there is the wxPropertyGridManager for the default and active parameters. Active parameters are displayed in bold.

        To activate a parameter, double-click on it in the default tab. It will be copied to the active tab and the value will be modifiable.

        :param parent : parent frame
        :param title : title of the frame
        :param w : width of the frame
        :param h : height of the frame
        :param ontop : if True, the frame will be on top of all other windows
        :param to_read : if True, the file will be read
        :param withbuttons : if True, buttons will be displayed
        :param DestroyAtClosing : if True, the frame will be destroyed when closed
        :param toShow : if True, the frame will be displayed
        :param full_style : if True, the full style of the PropertyGridManager will be displayed even if ontop is True
        """

        self.wx_exists = wx.App.Get() is not None # test if wx App is running

        if not self.wx_exists:
            logging.error("wxPython is not running - Impossible to set the GUI")
            return

        #Appel à l'initialisation d'un frame général
        if ontop:
            wx.Frame.__init__(self, parent, title=title, size=(w,h),style=wx.DEFAULT_FRAME_STYLE| wx.STAY_ON_TOP)
        else:
            wx.Frame.__init__(self, parent, title=title, size=(w,h),style=wx.DEFAULT_FRAME_STYLE)

        self.Bind(wx.EVT_CLOSE,self.OnClose)
        self.DestroyAtClosing = DestroyAtClosing

        #découpage de la fenêtre
        self.sizer = wx.BoxSizer(wx.HORIZONTAL)

        if withbuttons:
            self.sizerbut = wx.BoxSizer(wx.VERTICAL)
            #boutons
            self.saveme = wx.Button(self,id=10,label="Save to file")
            self.loadme = wx.Button(self,id=10,label="Load from file")
            self.applychange = wx.Button(self,id=10,label="Apply change")
            self.reloadme = wx.Button(self,id=10,label="Reload")

            #liaison des actions des boutons
            self.saveme.Bind(wx.EVT_BUTTON,self.SavetoFile)
            self.loadme.Bind(wx.EVT_BUTTON,self.LoadFromFile)
            self.reloadme.Bind(wx.EVT_BUTTON,self.Reload)
            self.applychange.Bind(wx.EVT_BUTTON,self.ApplytoMemory)

        #ajout d'un widget de gestion de propriétés
        if ontop:
            if full_style:
                self.prop = pg.PropertyGridManager(self,
                    style = pg.PG_BOLD_MODIFIED|pg.PG_SPLITTER_AUTO_CENTER|
                    # Include toolbar.
                    pg.PG_TOOLBAR if toolbar else 0 |
                    # Include description box.
                    pg.PG_DESCRIPTION |
                    pg.PG_TOOLTIPS |
                    # Plus defaults.
                    pg.PGMAN_DEFAULT_STYLE
                )
            else:
                self.prop = pg.PropertyGridManager(self,
                    style = pg.PG_BOLD_MODIFIED|pg.PG_SPLITTER_AUTO_CENTER|
                    pg.PG_TOOLTIPS |
                    # Plus defaults.
                    pg.PGMAN_DEFAULT_STYLE
                )
        else:
            self.prop = pg.PropertyGridManager(self,
                style = pg.PG_BOLD_MODIFIED|pg.PG_SPLITTER_AUTO_CENTER|
                # Include description box.
                pg.PG_DESCRIPTION |
                pg.PG_TOOLTIPS |
                # Plus defaults.
                pg.PGMAN_DEFAULT_STYLE |
                # Include toolbar.
                pg.PG_TOOLBAR if toolbar else 0
            )

        self.prop.Bind(pg.EVT_PG_DOUBLE_CLICK,self.OnDblClick)

        #ajout au sizer
        if withbuttons:
            self.sizerbut.Add(self.loadme,0,wx.EXPAND)
            self.sizerbut.Add(self.saveme,1,wx.EXPAND)
            self.sizerbut.Add(self.applychange,1,wx.EXPAND)
            self.sizerbut.Add(self.reloadme,1,wx.EXPAND)
            self.sizer.Add(self.sizerbut,0,wx.EXPAND)
        self.sizer.Add(self.prop,1,wx.EXPAND)

        if to_read:
            self.Populate()

        #ajout du sizert à la page
        self.SetSizer(self.sizer)
        # self.SetSize(w,h)
        self.SetAutoLayout(1)
        self.sizer.Fit(self)

        self.SetSize(0,0,w,h)
        # self.prop.SetDescBoxHeight(80)

        #affichage de la page
        self.Show(toShow)

    def _set_only_prop(self, wxparent):
        """ Set only the property grid """

        self.prop = pg.PropertyGridManager(wxparent,
            style = pg.PG_BOLD_MODIFIED|pg.PG_SPLITTER_AUTO_CENTER|
            # Include toolbar.
            pg.PG_TOOLBAR |
            # Include description box.
            pg.PG_DESCRIPTION |
            pg.PG_TOOLTIPS |
            # Plus defaults.
            pg.PGMAN_DEFAULT_STYLE
        )

        self.prop.Bind(pg.EVT_PG_DOUBLE_CLICK,self.OnDblClick)

    def hide_selected_buttons(self, to_hide:list[Buttons] = [Buttons.Load, Buttons.Save, Buttons.Reload]):
        """ Mask selected buttons - Default conserve only 'Apply change' """

        for locbutton in to_hide:
            if locbutton == Buttons.Load:
                self.sizerbut.Hide(self.loadme)
            elif locbutton == Buttons.Save:
                self.sizerbut.Hide(self.saveme)
            elif locbutton == Buttons.Reload:
                self.sizerbut.Hide(self.reloadme)
            elif locbutton == Buttons.Apply:
                self.sizerbut.Hide(self.applychange)

        self.Layout()

    def OnDblClick(self, event:wx.MouseEvent):
        """
        Double-click event handler to add a parameter to the active tab or reset to default value.
        Gestion du double-click pour ajouter des éléments ou remise à valeur par défaut.
        """

        # obtention de la propriété sur laquelle on a cliqué
        p = event.GetProperty()
        # nom et valeur du paramètre
        name = p.GetName()
        from_default_page = name[0:3]==PREFIX_DEFAULT
        # val = p.GetValue()

        # nom du groupe
        group=p.GetParent()
        groupname=group.GetName()

        # on se place sur la page des paramètres actifs
        page_active:pg.PropertyGridPage
        page_active = self.prop.GetPage(0)
        # on récupère le nom du paramètre sans le nom du groupe
        if from_default_page:
            paramname = name[3+len(groupname):]
        else:
            paramname = name[len(groupname):]

        if not self.is_in_default(groupname):
            logging.debug(_('Group {} not found in default parameters -- Maybe an incrementable group'.format(groupname)))
            return

        if not self.is_in_default(groupname, paramname):
            logging.warning(_('Param {} not found in default parameters -- Maybe an incrementable param '.format(paramname)))
            return

        #pointage vers le paramètre par défaut
        param_def = self.myparams_default[groupname][paramname]

        if from_default_page:
            #click depuis la page des param par défaut

            #essai pour voir si le groupe existe ou non dans les params actifs
            if not self.is_in_active(groupname):
                page_active.Append(pg.PropertyCategory(groupname))
                self.myparams[groupname] = {}

            #teste si param existe
            activeprop = self.prop.GetPropertyByName(groupname + paramname)
            if activeprop is None:
                #si non existant --> on ajoute, si existant --> rien à faire
                self._insert_elem_to_page(page_active, groupname, param_def)
                self.myparams[groupname][paramname] = param_def.copy()

        else:
            #recopiage de la valeur par défaut
            defvalue = self.value_as_type(param_def[key_Param.VALUE],
                                          param_def[key_Param.TYPE],
                                          param_def.get(key_Param.ENUM_CHOICES),
                                          bool_as_int=True,
                                          color_as=str)
            self.prop.SetPropertyValue(groupname + paramname, defvalue)

    def OnClose(self, event:wx.MouseEvent):
        """ Close event of the frame """
        if not self._callbackdestroy is None:
            self._callbackdestroy()

        if self.DestroyAtClosing:
            self.Destroy()
        else:
            self.Hide()
        pass

    def SavetoFile(self, event:wx.MouseEvent):
        """ sauvegarde dans le fichier texte """

        self.Save()

    def Save(self, filename:str = ''):
        """ Save the parameters in a file """

        if filename != '':
            self.filename = filename

        if self.filename=='':
            logging.warning(_('No filename given'))
            return

        with open(self.filename, 'w') as myfile:

            for group in self.myparams.keys():
                myfile.write(' ' + group +':\n')
                for param_name in self.myparams[group].keys():
                    myfile.write(param_name +'\t' + str(self.myparams[group][param_name][key_Param.VALUE])+'\n')

    def Reload(self, event:wx.MouseEvent):
        """ relecture du fichier sur base du nom déjà connu """
        if self.filename=='':
            logging.warning(_('No filename given'))
            return
        self.Clear()
        self.ReadFile(self.filename)
        self.Populate()

    def LoadFromFile(self, event:wx.MouseEvent):
        """ Load parameters from file """

        self.Clear()
        # read the file
        self.ReadFile()
        # populate the property grid
        self.Populate()

    def _get_prop_names(self, page:pg.PropertyGridPage) -> list[str]:
        """ Return the names of the properties in a page """

        return [prop.GetName() for prop in page.GetPyIterator(pg.PG_ITERATE_ALL)]

    def _is_in_propperty_page(self, page:pg.PropertyGridPage, group:str, param:str="") -> bool:
        """ Test if a parameter is in a page """

        return (group + param) in self._get_prop_names(page)

    def ApplytoMemory(self, event:wx.MouseEvent):
        """ Transfert des données en mémoire --> remplissage des dictionnaires """

        if self.prop.IsPageModified(0):
            #on boucle sur tous les paramètres pour les ajouter au dictionnaire si non présents
            for group in self.myparams_default.keys():
                for param_name in self.myparams_default[group].keys():
                    self._Apply1ParamtoMemory(group, param_name)
            self._update_IncGroup(withGUI=True)
            self._update_IncParam(withGUI=True)

            if self._callback is not None:
                self._callback()
        else:
            if self.has_gui:
                dlg = wx.MessageDialog(None,'Nothing to do!')
                dlg.ShowModal()

    def compare_active_to_default(self, remove_from_active_if_same:bool = True):
        """
        Compare active parameters to default parameters and remove those that are the same.

        :param remove_from_active_if_same: If True, remove parameters from active if they are the same as default.
        """

        for group in self.myparams_default.keys():
            for param_name in self.myparams_default[group].keys():
                if self.is_in_active(group, param_name):

                    val_default = self.myparams_default[group][param_name][key_Param.VALUE]
                    val_active = self.myparams[group][param_name][key_Param.VALUE]

                    if val_active == val_default:
                        if remove_from_active_if_same:
                            # Remove from active parameters
                            del self.myparams[group][param_name]
                            # # Remove from property grid
                            # if self._is_in_propperty_page(self.page_active, group, param_name):
                            #     self.prop.DeleteProperty(group + param_name)
                        else:
                            logging.debug(_('Parameter {} is the same as default and will not be removed'.format(param_name)))

        # Iterate through the groups and remove empty ones
        groups_to_remove = []
        for group in self.myparams.keys():
            if not self.myparams[group]:
                groups_to_remove.append(group)

        for group in groups_to_remove:
            del self.myparams[group]

    @property
    def page_active(self) -> pg.PropertyGridPage:
        """ Return the active page """
        return self.prop.GetPage(0)

    @property
    def page_default(self) -> pg.PropertyGridPage:
        """ Return the default page """
        return self.prop.GetPage(1)

    def _Apply1ParamtoMemory(self,
                             group:str,
                             param_name:str,
                             isIncrementable:bool=False,
                             genGroup:str="",
                             genParam:str=""):
        """
        Routine interne de MAJ d'un paramètre

        :param group : nom du groupe
        :param param_name : nom du paramètre
        :param isIncrementable : True si le paramètre est incrémentable
        :param genGroup : generic name of an incrementable group
        :param genParam : generic name of an incrementable param

        """

        if not self.wx_exists:
            logging.error("wxPython is not running - Impossible to apply changes to memory")

        assert self.wx_exists, "wxPython is not running"

        if isIncrementable:
            if(genParam != ""):
                if(genGroup != ""):
                    dict_param_def = self.myIncParam[genGroup][genParam]["Dict"][genParam]
                else:
                    dict_param_def = self.myIncParam[group][genParam]["Dict"][genParam]

            elif(genGroup != ""):
                dict_param_def = self.myIncGroup[genGroup]["Dict"][param_name]

        else:
            dict_param_def = self.myparams_default[group][param_name]

        enum_choices = dict_param_def.get(key_Param.ENUM_CHOICES)

        if self.is_in_default(group, param_name):

            # récupératrion de la valeur par défaut
            val_default = self.prop.GetPropertyByName(PREFIX_DEFAULT + group + param_name).m_value

            # on tente de récupérer la valeur active mais il ets possible qu'elle n'existe pas si sa valeur est identique à la valeur par défaut
            if self._is_in_propperty_page(self.page_active, group, param_name):
            # if self.is_in_active(group, param_name):
                val_active  = self.prop.GetPropertyByName(group + param_name).m_value
            else:
                val_active = val_default

            val_active  = self.value_as_type(val_active, dict_param_def[key_Param.TYPE], enum_choices)
            val_default = self.value_as_type(val_default, dict_param_def[key_Param.TYPE], enum_choices)

            if self.is_in_active(group, param_name):
                self[(group, param_name)] = val_active
            # if val_active != val_default:
            #    self[(group, param_name)] = val_active
            # else:
            #     logging.debug(_('Parameter {} not modified'.format(param_name)))

        else:
            # La valeur par défaut n'existe pas --> on prend la valeur active car c'est certainement une valeur incrémentable ou d'un groupe incrémentable
            # Si la valeur n'est pas présente, on ne fait rien
            if self._is_in_propperty_page(self.page_active, group, param_name):
            # if self.is_in_active(group, param_name):
                val_active  = self.prop.GetPropertyByName(group + param_name).m_value
                val_active  = self.value_as_type(val_active, dict_param_def[key_Param.TYPE], enum_choices)

                self[(group, param_name)] = val_active
            else:
                logging.debug(_('Parameter {} not found in default parameters'.format(param_name)))

    def position(self,position):
        """ Position the frame """
        self.SetPosition(wx.Point(position[0],position[1]+50))

    def Populate(self, sorted_groups:bool = False):
        """
        Filling the property management object based on dictionaries

        Use default AND active parameters

        Useful only if wxPython is running
        """

        if self.prop is None:
            logging.debug("ERROR : wxPython is not running - Impossible to populate the property grid")
            return

        self.prop.Clear()

        page_active:pg.PropertyGridPage
        page_default:pg.PropertyGridPage
        page_active = self.prop.AddPage(_("Active Parameters"))
        page_default = self.prop.AddPage(_("Default Parameters"))

        #gestion des paramètres actifs
        for group, params in self.myparams.items():

            page_active.Append(pg.PropertyCategory(group))

            for param_name, param in params.items():
                param:dict
                if self.is_in_default(group, param_name):
                    param_def = self.myparams_default[group][param_name]

                    if self.show_in_active_if_default:
                        self._add_elem_to_page(page_active, group, param, param_def = param_def)
                    elif param[key_Param.VALUE] != param_def[key_Param.VALUE]:
                        self._add_elem_to_page(page_active, group, param, param_def = param_def)
                else:
                    logging.debug(_('Parameter {} not found in default parameters'.format(param_name)))
                    param_def = None
                    self._add_elem_to_page(page_active, group, param, param_def = param_def)

        #gestion des paramètres par défaut
        for group, params in self.myparams_default.items():
            page_default.Append(pg.PropertyCategory(group))
            for param_name, param in params.items():
                param:dict
                self._add_elem_to_page(page_default, group, param, prefix = PREFIX_DEFAULT)

        # Display a header above the grid
        self.prop.ShowHeader()

        if sorted_groups:
            self.prop.Sort()

        self.prop.Refresh()

    def _insert_elem_to_page(self, page:pg.PropertyGridPage, group:str, param:dict, param_def:dict = None, prefix:str=''):
        """ Insert an element to a page """

        param_name = param[key_Param.NAME]
        locname = prefix + group + param_name

        # Get parent item based on group name
        parent = page.GetPropertyByName(group)
        assert parent is not None, "Group {} not found in page".format(group)
        assert isinstance(parent, pg.PropertyCategory), "Parent is not a PropertyCategory"

        if param_def is not None:
            # priority to default parameters
            if key_Param.ADDED_JSON in param_def.keys():
                param[key_Param.ADDED_JSON] = param_def[key_Param.ADDED_JSON]

            param[key_Param.COMMENT] = param_def[key_Param.COMMENT]
            param[key_Param.TYPE] = param_def[key_Param.TYPE]

        if key_Param.ADDED_JSON in param.keys()  and param[key_Param.ADDED_JSON] is not None:
            # Ajout des choix via chaîne JSON
            if param[key_Param.ADDED_JSON]['Values'] is not None:

                list_keys   = [k for k in param[key_Param.ADDED_JSON]['Values'].keys()]
                list_values = [k for k in param[key_Param.ADDED_JSON]['Values'].values()]

                value_param = self.value_as_type(param[key_Param.VALUE], param[key_Param.TYPE], param.get(key_Param.ENUM_CHOICES))
                if type(value_param) == str:
                    try:
                        value_param = int(value_param)
                    except:
                        logging.debug("String type will be conserved! -- {}".format(value_param))

                if type(value_param) != int:
                    logging.warning("Parameters -- EnumProperty -- Value {} is not an integer".format(value_param))
                    logging.debug("EnumProperty value must be an integer")

                page.AppendIn(parent, pg.EnumProperty(param_name, name=locname, labels=list_keys, values=list_values, value=int(value_param))) # force value to 'int' type
            else:
                self._insert_with_type_based_on_value(page, group, param, prefix)

            self.prop.SetPropertyHelpString(locname , param[key_Param.ADDED_JSON]['Full_Comment']  + '\n\n' + param[key_Param.COMMENT])
        else:

            self._insert_with_type_based_on_value(page, group, param, prefix)

            self.prop.SetPropertyHelpString(locname, param[key_Param.COMMENT])

    def _pgenum_for_enum(self, label:str, name:str, value:Enum, enum_choices:Union[list[str], Enum]):
        """
        Build a pg.EnumProperty.

        IMPORTANT! This method accepts an enumeration defined as a real Enum or
        or a list of strings. It was desinged this way to allow PyParam to worke
        either on list of strings or actual Enum.

        :param label: The label of the property
        :param name: The name of the proprty
        :param value: The current value of the property (must be of the
            `type_enum` type)
        :param enum_choices: Eiterh a list of string or simply an `Enum`
        """

        logging.debug(f"_pgenum_for_enum: {label} {name} value:{value} ({type(value)}) enum_choices:{enum_choices}")

        if not isinstance(enum_choices, list):
            assert issubclass(enum_choices, Enum)
            enum_choices = [e.name for e in enum_choices]
        else:
            assert enum_choices, "Can't work with an empty"
            assert value is None or isinstance(value, str), "enum_choices is a list of strings, therefore value should be a string"

        if value is None:
            index = 0
        else:
            index = enum_choices.index(value.name)

        indices = list(range(len(enum_choices)))
        return pg.EnumProperty(label=label, name=name,
                               labels=enum_choices, values=indices,
                               value=index)

    def _insert_with_type_based_on_value(self, page:pg.PropertyGridPage, group:str, param:dict, prefix:str=''):

        param_name = param[key_Param.NAME]
        locname = prefix + group + param_name
        locvalue = self[(group, param_name)]

        # Get parent item based on group name
        parent = page.GetPropertyByName(group)
        assert parent is not None, "Group {} not found in page".format(group)
        assert isinstance(parent, pg.PropertyCategory), "Parent is not a PropertyCategory"

        if isinstance(locvalue, float):
            page.AppendIn(parent,pg.FloatProperty(label = param_name, name = locname, value = locvalue))

        elif isinstance(locvalue, int):
            # bool is also an int
            if isinstance(locvalue, bool):
                page.AppendIn(parent,pg.BoolProperty(label=param_name, name = locname, value = locvalue))
            else:
                page.AppendIn(parent,pg.IntProperty(label = param_name, name = locname, value = locvalue))

        elif param[key_Param.TYPE]==Type_Param.File:
            page.AppendIn(parent,pg.FileProperty(label=param_name, name = locname, value = param[key_Param.VALUE]))

        elif param[key_Param.TYPE]==Type_Param.Directory:
            page.AppendIn(parent,pg.DirProperty(label = param_name, name = locname, value = locvalue))
            # newobj.SetLabel(param_name)
            # page.Append(newobj)

        elif param[key_Param.TYPE]==Type_Param.Color:
            page.AppendIn(parent,pg.ColourProperty(label = param_name, name = locname, value = locvalue))

        elif param[key_Param.TYPE]==Type_Param.Fontname:
            page.AppendIn(parent,pg.FontProperty(label = param_name, name = locname, value = locvalue))

        elif param[key_Param.TYPE]==Type_Param.Enum:
            page.AppendIn(parent,
                          self._pgenum_for_enum(label=param_name, name=locname, value=locvalue, enum_choices=param.get(key_Param.ENUM_CHOICES)))

        else:
            page.AppendIn(parent,pg.StringProperty(label = param_name, name = locname, value = locvalue))

    def _add_with_type_based_on_value(self, page:pg.PropertyGridPage, group:str, param:dict, prefix:str=''):

        param_name = param[key_Param.NAME]
        locname = prefix + group + param_name

        locvalue = self._get_param_def(group, param_name) if prefix == PREFIX_DEFAULT else self[(group, param_name)]

        if isinstance(locvalue, float):
            page.Append(pg.FloatProperty(label = param_name, name = locname, value = locvalue))

        elif isinstance(locvalue, int):
            # bool is also an int
            if isinstance(locvalue, bool):
                page.Append(pg.BoolProperty(label=param_name, name = locname, value = locvalue))
            else:
                page.Append(pg.IntProperty(label = param_name, name = locname, value = locvalue))

        elif param[key_Param.TYPE]==Type_Param.File:

            if param[key_Param.VALUE] is None:
                page.Append(pg.FileProperty(label=param_name, name = locname, value = ''))
            else:
                page.Append(pg.FileProperty(label=param_name, name = locname, value = param[key_Param.VALUE]))

        elif param[key_Param.TYPE]==Type_Param.Directory:
            if locvalue is None:
                page.Append(pg.DirProperty(label = param_name, name = locname, value = ''))
            else:
                page.Append(pg.DirProperty(label = param_name, name = locname, value = locvalue))

        elif param[key_Param.TYPE]==Type_Param.Color:
            page.Append(pg.ColourProperty(label = param_name, name = locname, value = locvalue))

        elif param[key_Param.TYPE]==Type_Param.Fontname:
            page.Append(pg.FontProperty(label = param_name, name = locname, value = locvalue))

        elif param[key_Param.TYPE]==Type_Param.Enum:
            page.Append(self._pgenum_for_enum(label=param_name, name=locname, value=locvalue, enum_choices=param.get(key_Param.ENUM_CHOICES)))

        else:
            if locvalue is None:
                locvalue = ""

            page.Append(pg.StringProperty(label = param_name, name = locname, value = locvalue))

    def _add_elem_to_page(self, page:pg.PropertyGridPage, group:str, param:dict, param_def:dict = None, prefix:str=''):
        """ Add an element to a page """

        param_name = param[key_Param.NAME]
        locname = prefix + group + param_name

        if param_def is not None:
            # priority to default parameters
            if key_Param.ADDED_JSON in param_def.keys():
                param[key_Param.ADDED_JSON] = param_def[key_Param.ADDED_JSON]
            param[key_Param.COMMENT] = param_def[key_Param.COMMENT]
            param[key_Param.TYPE] = param_def[key_Param.TYPE]

        if key_Param.ADDED_JSON in param.keys() and param[key_Param.ADDED_JSON] is not None:

            # Ajout des choix via chaîne JSON
            if param[key_Param.ADDED_JSON]['Values'] is not None:

                list_keys   = [ k for k in param[key_Param.ADDED_JSON]['Values'].keys()]
                list_values = [ k for k in param[key_Param.ADDED_JSON]['Values'].values()]

                # FIXME : TO GENERALIZE!!!
                value_param = self.value_as_type(param[key_Param.VALUE], param[key_Param.TYPE], param.get(key_Param.ENUM_CHOICES))
                if type(value_param) == str:
                    try:
                        value_param = int(value_param)
                    except:
                        logging.debug("String type will be conserved! -- {}".format(value_param))

                if type(value_param) != int:
                    logging.warning("Parameters -- EnumProperty -- Value {} is not an integer in file : {}".format(value_param, self.filename))
                    logging.debug("EnumProperty value must be an integer")

                page.Append(pg.EnumProperty(label= param_name, name= locname, labels= list_keys, values= list_values, value= int(value_param)))

            else:
                # Pas de chaîne JSON mais un commentaire complet
                self._add_with_type_based_on_value(page, group, param, prefix)


            if "Full_Comment" in param[key_Param.ADDED_JSON]:
                self.prop.SetPropertyHelpString(locname , param[key_Param.ADDED_JSON]["Full_Comment"] + '\n\n' + param[key_Param.COMMENT])
            else:
                self.prop.SetPropertyHelpString(locname , param[key_Param.COMMENT])

        else:

            self._add_with_type_based_on_value(page, group, param, prefix)

            self.prop.SetPropertyHelpString(locname, param[key_Param.COMMENT])

    def PopulateOnePage(self):
        """
        Filling the property management object based on dictionaries

        Use ONLY active parameters

        Useful only if wxPython is running -- e.g. class "PyDraw"
        """

        if self.prop is None:
            logging.error("ERROR : wxPython is not running - Impossible to populate the property grid")
            return

        #gestion des paramètres actifs
        self.prop.Clear()
        page:pg.PropertyGridPage
        page = self.prop.AddPage("Current")

        for group, params in self.myparams.items():
            page.Append(pg.PropertyCategory(group))
            for param_name, param in params.items():
                param:dict
                self._add_elem_to_page(page, group, param)

        # Display a header above the grid
        self.prop.ShowHeader()
        self.prop.Refresh()


    # File management
    # ---------------

    def check_default_file(self, filename:str):
        """ Check if a default file exists """

        if os.path.isfile(filename + '.default'):
            return True
        else:
            return False

    def ReadFile(self,*args):
        """ Lecture d'un fichier .param et remplissage des dictionnaires myparams et myparams_default """

        if len(args)>0:
            #s'il y a un argument on le prend tel quel
            self.filename = str(args[0])
        else:
            if self.wx_exists:
                #ouverture d'une boîte de dialogue
                file=wx.FileDialog(self,"Choose .param file", wildcard="param (*.param)|*.param|all (*.*)|*.*")
                if file.ShowModal() == wx.ID_CANCEL:
                    return
                else:
                    #récuparétaion du nom de fichier avec chemin d'accès
                    self.filename =file.GetPath()
            else:
                logging.warning("ERROR : no filename given and wxPython is not running")
                return

        if not os.path.isfile(self.filename):
            logging.warning("ERROR : cannot find the following file : {}".format(self.filename))
            return

        myparamsline_default = None
        if self.check_default_file(self.filename):
            with open(self.filename+'.default', 'r') as myfile:
                myparamsline_default = myfile.read()

        # lecture du contenu
        with open(self.filename, 'r') as myfile:
            myparamsline = myfile.read()

        self.fill_from_strings(myparamsline, myparamsline_default)

        if not self.check_default_file(self.filename):
            self._CreateDefaultFile()

    def fill_from_strings(self, chain:str, chaindefault:str = None):
        """ Fill the dictionaries from a string """

        myparamsline = chain.splitlines()
        self.ParseFile(myparamsline,self.myparams)

        if chaindefault is not None:
            myparamsline = chaindefault.splitlines()

        self.ParseFile(myparamsline,self.myparams_default)

        # mise à jour des groupes incrémentables et des paramètres incrémentables
        self._update_IncGroup()
        self._update_IncParam()

    def ParseFile(self, myparamsline:list[str], todict:dict):
        """
        Parsing the file to find groups and parameters and filling a dictionary

        Each parameter is stored in a dictionary associated to the upper group.

        'add_group' is used to add a group in the dictionary 'todict'.
        'groupname' will be there sanitized (strip, decoded if iteratable...) to be used in '_add_param_from_str'.

        myparamsline format:
            ['groupname1:', 'param1', 'param2', 'groupname2:', 'param1', ...]

        """

        if isinstance(myparamsline, str):
            logging.warning("ERROR : myparamsline must be a list of strings -- forcing conversion")
            myparamsline = myparamsline.splitlines()

        for param in myparamsline:
            if param.endswith(':'):
                # GROUPE
                # ------

                #création d'un dict sur base du nom de groupe, sans le :
                groupname = param.replace(':','')
                groupname, groupdict = self.add_group(groupname, todict)

            elif param.startswith('%'):
                # COMMENTAIRE
                # -----------
                #c'est du commentaire --> rien à faire sauf si c'est du code json
                if param.startswith('%json'):
                    #c'est du code json --> on le prend tel quel
                    parsed_json = json.loads(param.replace('%json',''))
                    curparam[key_Param.ADDED_JSON]=parsed_json

            elif param.strip() == '':
                # VOID LINE
                # ---------
                logging.warning(_('A void line is present where it should not be. Removing the blank line'))
                myparamsline.remove(param)

            else:
                # PARAMETRE
                # ---------
                curparam = self._add_param_from_str(param, groupname, groupdict)
                curparam[key_Param.ADDED_JSON]=None

    def _CreateDefaultFile(self):
        """ Create a default file """

        with open(self.filename+'.default', 'w') as myfile:

            for group in self.myparams.keys():
                myfile.write(' ' + group +':\n')
                for param_name in self.myparams[group].keys():
                    myfile.write(param_name +'\t' + str(self.myparams[group][param_name][key_Param.VALUE])+'\n')

            myfile.close()

    def _Extract_IncrInfo(self, nameStr:str) -> tuple[str, list[str, str, int, int]]:
        """
        Extract the information of an incrementable group or param

        The name of an incrementable group or param is of the form: $n(group, param, min, max)$
        """
        iterInfo = []
        newName = ""

        positions = [i for i, char in enumerate(nameStr) if char == "$"]

        assert np.mod(len(positions),2) == 0, "ERROR : the number of '$' must be even"

        if len(positions)>0:
            # indice incrémentable détecté

            # search for the first '$'
            posSep1 = positions[0] #nameStr.find("$")
            # search for the last '$'
            posSep2 = positions[-1] #nameStr[posSep1+1:].find("$")

            # select the string between the two '$'
            iterCode = nameStr[posSep1:posSep2+1]

            positions_left = [i for i, char in enumerate(iterCode) if char == "("]
            positions_right = [i for i, char in enumerate(iterCode) if char == ")"]

            if len(positions_left)==0 and len(positions_right)==0:
                # no '(' and no ')' --> no incrementable information
                return nameStr, None

            assert len(positions_left)>0, "ERROR : no '(' found in the name of an incrementable group or param"
            assert len(positions_right)>0, "ERROR : no ')' found in the name of an incrementable group or param"

            # search for the first '('
            posSep1 = positions_left[0] #iterCode.find("(")
            # search for the second ')'
            posSep2 = positions_right[-1] #iterCode[posSep1:].find(")")

            # select the string between the two '('
            iterCode = iterCode[posSep1:posSep2+1]

            # remove the incrementable code from the name --> conserve $n$
            newName = nameStr.replace(iterCode,'')
            # remove the spaces before and after the name
            newName = newName.strip()

            # decode the incrementable information
            iterInfo = iterCode[1:-1].split(',')
            # remove the spaces before and after the information
            iterInfo = [x.strip() for x in iterInfo]

            if len(iterInfo)==3:
                # no group name provided --> use the current group
                iterInfo = [iterInfo[0], int(iterInfo[1]), int(iterInfo[2])]
            elif len(iterInfo)==4:
                # group name provided --> use the provided group
                iterInfo = [iterInfo[0], iterInfo[1], int(iterInfo[2]), int(iterInfo[3])]
            else:
                logging.error(_("The incrementable information must be of the form: $n(group, param, min, max)$ or $n(param, min, max)$"))
        else:
            newName = nameStr
            iterInfo = None

        return newName, iterInfo

    # File management without wx
    # ---------------------------

    def apply_changes_to_memory(self, verbosity:bool = True):
        """ Transfert des données en mémoire sans wx --> remplissage des dictionnaires """

        if self.prop is None:
            logging.debug("ERROR : wxPython is not running - Impossible to apply changes to memory")
            return

        if self.prop.IsPageModified(0):
            #on boucle sur tous les paramètres pour les ajouter au dictionnaire si non présents
            for group in self.myparams_default.keys():
                for param_name in self.myparams_default[group].keys():
                    self._Apply1ParamtoMemory(group, param_name)
            self._update_IncGroup(withGUI=True)
            self._update_IncParam(withGUI=True)

            if not self._callback is None:
                self._callback()
        else:
            if verbosity:
                logging.warning(_('Nothing to do!'))

    def save_automatically_to_file(self):
        """
        Sauvegarde dans le fichier texte sans wx.Event
        FIXME  weird message caused by the dialog box in log messages.
        """
        if self.prop.IsPageModified(0):
            try:
                dlg  = wx.MessageDialog(self,
                                         _('Would you like to apply & save the modified parameters?'),
                                         style = wx.YES_NO|wx.YES_DEFAULT)
                if dlg.ShowModal() == wx.ID_YES:
                    self.apply_changes_to_memory()
                    if self.wx_exists:
                        logging.info(_("Modifications on parameters applied."))
                    dlg.Destroy()
                else:
                    dlg.Destroy()
                    if self.wx_exists:
                        logging.info(_("The modifications on parameters were not applied."))
                    return

            except:
                if self.wx_exists:
                    raise Exception(logging.info(_("An error occured while applying changes to parameters.")))
                else:
                    raise Exception(_("An error occured while applying changes to parameters."))


        with open(self.filename, 'w') as myfile:

            for group in self.myparams.keys():
                myfile.write(' ' + group +':\n')
                for param_name in self.myparams[group].keys():
                    myfile.write(param_name +'\t' + str(self.myparams[group][param_name][key_Param.VALUE])+'\n')
            myfile.close()
        if self.wx_exists:
            logging.info(_("Parameters' modification saved."))

    # Clear/Rest
    # ----------

    def Clear(self):
        """ Clear all the parameters """

        self.myparams.clear()
        self.myparams_default.clear()
        self.myIncGroup.clear()
        self.myIncParam.clear()
        if self.prop is not None:
            self.prop.Clear()
            self.prop.SetDescription("","")

    # Object access
    # -------------

    def add_group(self, groupname:str, todict:dict = None) -> tuple[str,dict]:
        """
        Add a group in the dictionary 'todict' if provided or in the IncGroup dictionary

        return sanitized groupname and dictionnary attached to the group
        """

        groupname = groupname.strip()

        #On verifie si le groupe est incrémentable
        groupname, iterInfo = self._Extract_IncrInfo(groupname)

        if iterInfo is None:
            if todict is None:
                logging.error(_("You must provide a dictionary to store the group -- Retry"))
                return None

            # Groupe classique
            todict[groupname]={}
            return groupname, todict[groupname]
        else:
            # Le groupe est incrémentable
            iterGroup = iterInfo[0] # nom du groupe contenant le paramètre de nombre de groupes
            iterParam = iterInfo[1] # nom du paramètre contenant le nombre de groupes
            iterMin = iterInfo[2]   # valeur minimale
            iterMax = iterInfo[3]   # valeur maximale

            return groupname, self.add_IncGroup(groupname, iterMin, iterMax, iterGroup, iterParam)

    def _add_param_in_dict(self,
                           group:dict,
                           name:str,
                           value:Union[float, int, str] = '', # la valeur est de toute façon stockée en 'str'
                           type:Type_Param=None,
                           comment:str = '',
                           jsonstr:str = None,
                           enum_choices:list = None) -> dict:

        if not name in group.keys():
            group[name]={}

        curpar=group[name]

        curpar[key_Param.NAME]=name
        curpar[key_Param.TYPE]=type
        curpar[key_Param.VALUE]=value
        curpar[key_Param.COMMENT]=comment

        if jsonstr is not None:
            if isinstance(jsonstr, str):
                parsed_json = json.loads(jsonstr.replace('%json',''))
            elif isinstance(jsonstr, dict):
                parsed_json = jsonstr

            curpar[key_Param.ADDED_JSON]=parsed_json
        else:
            curpar[key_Param.ADDED_JSON]=None

        if enum_choices is not None:
            curpar[key_Param.ENUM_CHOICES]=enum_choices
        else:
            curpar[key_Param.ENUM_CHOICES]=None

        return curpar

    def _new_IncParam_dict(self, groupname, refgroupname, refparamname, min_value, max_value) -> dict:
        """ Create a new dictionary for an incrementable parameter """

        newdict = {}
        newdict["Group"] = groupname
        newdict["Ref group"] = refgroupname
        newdict["Ref param"] = refparamname
        newdict["Min"] = min_value
        newdict["Max"] = max_value
        newdict["Dict"] = {}

        return newdict

    def _add_param_from_str(self, param:str, groupname:str, groupdict:dict, seperator:str = '\t'):
        """ Add a parameter from a complex string """

        #split sur base du sépérateur
        paramloc=param.split(seperator)

        #on enlève les espaces avant et après toutes les variables
        paramloc = [x.strip() for x in paramloc]

        paramloc[0], iterInfo = self._Extract_IncrInfo(paramloc[0])

        if iterInfo is not None:
            #le parametre courant est incrémentable -> ajout au dictionnaire particulier des paramètres
            if not groupname in self.myIncParam:
                self.myIncParam[groupname] = {}

            if not paramloc[0] in self.myIncParam[groupname]:
                curdict = self.myIncParam[groupname][paramloc[0]] = self._new_IncParam_dict(groupname, groupname if len(iterInfo)==3 else iterInfo[0], iterInfo[-3], iterInfo[-2], iterInfo[-1])
            else:
                curdict = self.myIncParam[groupname][paramloc[0]]

            if not "Saved" in curdict:
                curdict["Saved"] = {}

            #pointage du param courant dans le dict de référence
            curparam = curdict["Dict"][paramloc[0]] = {}
        else:
            #création d'un dict sur base du nom de paramètre
            curparam=groupdict[paramloc[0]]={}

        curparam[key_Param.NAME]=paramloc[0]

        if len(paramloc)>1:
            #ajout de la valeur
            curparam[key_Param.VALUE]=paramloc[1]

            try:
                # tentative d'ajout du commentaire --> pas obligatoirement présent
                curparam[key_Param.COMMENT]=paramloc[2]

                # recherche du type dans le commentaire
                curparam[key_Param.TYPE]=search_type(paramloc[2])
                if curparam[key_Param.TYPE] == Type_Param.String:
                    # recherche du type dans la chaîne complète
                    type_in_fulchain = search_type(param)

                    if type_in_fulchain != Type_Param.String:
                        curparam[key_Param.TYPE] = type_in_fulchain
                try:
                    # tentative de recherche du type dans les valeurs par défaut
                    param_def=self.myparams_default[groupname][paramloc[0]]
                    curparam[key_Param.TYPE]=param_def[key_Param.TYPE]
                except:
                    pass
            except:
                curparam[key_Param.COMMENT]=''
                try:
                    # tentative de recherche du type dans les valeurs par défaut
                    param_def=self.myparams_default[groupname][paramloc[0]]
                    curparam[key_Param.TYPE]=param_def[key_Param.TYPE]
                except:
                    if not key_Param.TYPE in curparam:
                        curparam[key_Param.TYPE] = None
        else:
            curparam[key_Param.VALUE]=''
            curparam[key_Param.COMMENT]=''
            curparam[key_Param.TYPE]=None

        return curparam

    def addparam(self,
                 groupname:str = '',
                 name:str = '',
                 value:Union[float, int, str] = '', # la valeur est de toute façon stockée en 'str'
                 type:Type_Param=None,
                 comment:str = '',
                 jsonstr:str = None,
                 whichdict:Literal['All', 'Default', 'Active', 'IncGroup', '']='',
                 enum_choices:list[str]|Enum = None):
        """
        Add or update a parameter

        :param groupname : groupe in which the new param will be strored - If it does not exist, it will be created
        :param name      : param's name - If it does not exist, it will be created
        :param value     : param's value
        :param type      : type -> will influence the GUI
        :param comment   : param's comment -- helpful to understand the parameter
        :param jsonstr   : string containing JSON data -- used in GUI
            jsonstr can be a dict i.e. '{"Values":{choice1:1, choice2:2,
            choice3:3}, "Full_Comment":'Yeah baby !'}'
        :param whichdict : where to store the param -- Default, Active or All, or IncGroup if the param is part of an incrementable group
        :param enum_choices : If we have a Type_Param.Enum parameters, then
            this represents the possible choices for that enum. The possible
            choices are either given as the enum itself or as a list of
            strings (e.g., ['Option1', 'Option2', 'Option3'])

        Return 0 if OK, -1 if the group is incrementable and not created, -2 if the group does not exist
        """

        if isinstance(type, str):
            if type == 'Integer':
                type = Type_Param.Integer
            elif type == 'Float':
                type = Type_Param.Float
            elif type == 'Integer_or_Float':
                type = Type_Param.Integer_or_Float
            elif type == 'Logical':
                type = Type_Param.Logical
            elif type == 'File':
                type = Type_Param.File
            elif type == 'Directory':
                type = Type_Param.Directory
            elif type == 'Color':
                type = Type_Param.Color
            elif type == 'Fontname':
                type = Type_Param.Fontname
            elif type == 'Enum':
                type = Type_Param.Enum
            elif type == 'String':
                type = Type_Param.String
            else:
                type = None

        name_wo, iterInfo = self._Extract_IncrInfo(name)
        if iterInfo is not None:
            return self.add_IncParam(groupname, name, value, comment, type, added_json=jsonstr)

        if '$n$' in groupname:
            if whichdict != 'IncGroup':
                logging.warning(_("WARNING : group is incrementable. -- You must use 'IncGroup' for whichdict"))
                whichdict = 'IncGroup'
        elif '$n(' in groupname:
            if whichdict != 'IncGroup':
                logging.warning(_("WARNING : group is incrementable. -- You must use 'IncGroup' for whichdict"))
                whichdict = 'IncGroup'

            groupname, iterInfo = self._Extract_IncrInfo(groupname)

            if iterInfo is None:
                logging.error(_("ERROR : infos not found in {} -- Retry".format(groupname)))
                return -1

            # Le groupe est incrémentable
            iterGroup = iterInfo[0] # nom du groupe contenant le paramètre de nombre de groupes
            iterParam = iterInfo[1] # nom du paramètre contenant le nombre de groupes
            iterMin = iterInfo[2]   # valeur minimale
            iterMax = iterInfo[3]   # valeur maximale

            if groupname not in self.myIncGroup.keys():
                self.add_IncGroup(groupname, iterMin, iterMax, iterGroup, iterParam)

        if whichdict=='IncGroup':
            if not groupname in self.myIncGroup.keys():
                logging.error(_("ERROR : group {} does not exist. -- You must first create it".format(groupname)))
                logging.error(_("   or pass infos in the group name : $n(group, param, min, max)$"))
                return -2

            self._add_param_in_dict(self.myIncGroup[groupname]["Dict"], name, value, type, comment, jsonstr, enum_choices)
            return 0

        else:
            if whichdict=='All' or whichdict=='':
                locparams=[self.myparams, self.myparams_default]
            elif whichdict=='Default':
                locparams=[self.myparams_default]
            elif whichdict=='Active':
                locparams=[self.myparams]

            for curdict in locparams:
                if not groupname in curdict.keys():
                    curdict[groupname]={}

                self._add_param_in_dict(curdict[groupname], name, value, type, comment, jsonstr, enum_choices)

            return 0

    def add_param(self,
                 groupname:str = '',
                 name:str = '',
                 value:Union[float, int, str] = '', # la valeur est de toute façon stockée en 'str'
                 type:Type_Param=None,
                 comment:str = '',
                 jsonstr:str = None,
                 whichdict:Literal['All', 'Default', 'Active', 'IncGroup', '']='',
                 enum_choices:list = None):
        """alias of addparam"""

        return self.addparam(groupname, name, value, type, comment, jsonstr, whichdict, enum_choices)

    def __getitem__(self, key:tuple[str, str]):
        """
        Retrieve :
          - value's parameter from group if key is a tuple or a list (group, param_name)
          - group dict if key is a string
        """
        if isinstance(key, tuple) or isinstance(key, list):
            group, name = key
            return self.get_param(group, name)
        elif isinstance(key, str):
            return self.get_group(key)

    def __setitem__(self, key:str, value:Union[float, int, str, bool]):
        """set item, key is a tuple or a list (group, param_name)

        Important! If you want to set an Enum you must do so using a `value` of
        type enum and not str. This class should work also with enum as strings,
        but it is not supported in this method.
        """

        if isinstance(key, tuple) or isinstance(key, list):
            group, name = key
            if self.get_param(group, name) is not None:
                self.change_param(group, name, value)
            else:
                self.addparam(group, name, value, self._detect_type_from_value(value), enum_choices=self._detect_enum_choices_from_value(value))

    def is_in_active(self, group:str, name:str = None) -> bool:
        """ Return True if the parameter is in the active parameters """
        return self.is_in(group, name, whichdict='Active')

    def is_in_default(self, group:str, name:str = None) -> bool:
        """ Return True if the parameter is in the default parameters """
        return self.is_in(group, name, whichdict='Default')

    def is_in(self, group:str, name:str = None, whichdict:Literal['All', 'Default', 'Active', 'IncGroup', '']='Active') -> bool:
        """ Return True if the parameter is in the whichdict parameters """

        if whichdict=='All':
            locparams=[self.myparams, self.myparams_default]
        elif whichdict=='Default':
            locparams=[self.myparams_default]
        elif whichdict=='Active' or whichdict=='':
            locparams=[self.myparams]

        for curdict in locparams:
            if group in curdict.keys():
                if name is not None:
                    if name in curdict[group].keys():
                        ret = True
                    else:
                        return False
                else:
                    ret = True
            else:
                return False

        return ret

    def get_param_dict(self, group:str, name:str) -> dict[str, Union[str, int, float, bool, tuple[int, int, int]]]:
        """
        Returns the parameter dict if found, otherwise None obj
        """

        if self.is_in_active(group, name):
            return self.myparams[group][name]
        elif self.is_in_default(group, name):
            return self.myparams_default[group][name]
        else:
            return None

    def get_type(self, group:str, name:str) -> Type_Param:
        """
        Returns the type of the parameter if found, otherwise None obj
        """

        curtype = None

        if self.is_in_default(group, name):
            if key_Param.TYPE in self.myparams_default[group][name].keys():
                curtype = self.myparams_default[group][name][key_Param.TYPE]

        if self.is_in_active(group, name) and curtype is None:
            if key_Param.TYPE in self.myparams[group][name].keys():
                curtype = self.myparams[group][name][key_Param.TYPE]

        return curtype if curtype is not None else Type_Param.String

    def value_as_type(self,
                      value,
                      type: Type_Param,
                      enum_choices,
                      bool_as_int:bool = False,
                      color_as:Union[int,str,float]= int) :

        #logging.debug(f"value_as_type(): value={value}, enum_choices={enum_choices}")
        """ Convert the value to the right type """
        if type == Type_Param.Integer:
            value = int(value)
        elif type == Type_Param.Float:
            value = float(value)
        elif type == Type_Param.Logical:
            if isinstance(value,str):
                if value.lower() in ['.false.', 'false', 'faux']:
                    value = False
                elif value.lower() in ['.true.', 'true', 'vrai']:
                    value = True
            else:
                value = bool(value)

            if bool_as_int:
                value = int(value)

        elif type == Type_Param.Color:
            if color_as == str:
                value = str(value)
            else:
                if isinstance(value,str):
                    value = value.replace('(','')
                    value = value.replace(')','')
                    value = value.split(',')
                elif isinstance(value, wx.Colour):
                    value = [value.Red(), value.Green(), value.Blue(), value.Alpha()]

                if color_as == int:
                    value = tuple([int(x) for x in value])

                elif color_as == float:
                    value = tuple([float(x)/255. for x in value])

        elif type == Type_Param.Integer_or_Float:
            value = float(value)
        elif type == Type_Param.String:
            value = str(value)
        elif type == Type_Param.File:
            value = str(value)
        elif type == Type_Param.Directory:
            value = str(value)
        elif type == Type_Param.Fontname:
            value = str(value)
        elif type == Type_Param.Enum:
            if isinstance(enum_choices, list):
                # Let's formalize our expectations here
                assert isinstance(value, str)
                assert value in enum_choices, f"{value} not in {enum_choices}"
            else:
                assert isinstance(value, enum_choices)
        else:
            value = str(value)

        return value

    def get_param(self, group:str, name:str, default_value=None):
        """
        Returns the value of the parameter if found, otherwise None obj

        used in __getitem__
        """

        #print("get_param()")
        if self.is_in_active(group, name):
            element = self.myparams[group][name][key_Param.VALUE]
            dct = self.myparams[group][name]
        elif self.is_in_default(group, name):
            element = self.myparams_default[group][name][key_Param.VALUE]
            dct = self.myparams_default[group][name]
        else:
            element  = default_value
            return element

        # String conversion according to its type
        curType = self.get_type(group, name)
        return self.value_as_type(element, curType, dct.get(key_Param.ENUM_CHOICES))

    def _get_param_def(self, group:str, name:str, default_value=None):
        """
        Returns the default value of the parameter if found, otherwise None obj

        """

        if self.is_in_default(group, name):
            element = self.myparams_default[group][name][key_Param.VALUE]
        else:
            element  = default_value
            return element

        # String conversion according to its type
        curType = self.get_type(group, name)
        return self.value_as_type(element, curType, self.myparams_default[group][name].get(key_Param.ENUM_CHOICES))

    def get_group(self, group:str) -> dict:
        """
        Return the group dictionnary if found, otherwise None obj
        Check the active parameters first, then the default parameters

        Used in __getitem__
        """

        if self.is_in_active(group):
            return self.myparams[group]
        elif self.is_in_default(group):
            return self.myparams_default[group]
        else:
            return None

    def get_help(self, group:str, name:str) -> list[str, str]:
        """
        Return the help string if found, otherwise None obj

        :return: [comment, full_comment]
        """

        if self.is_in_default(group, name):
            curdict = self.myparams_default[group][name]
            ret = [curdict[key_Param.COMMENT]]

            if key_Param.ADDED_JSON in curdict.keys():
                if curdict[key_Param.ADDED_JSON] is not None:
                    if 'Full_Comment' in curdict[key_Param.ADDED_JSON].keys():
                        ret += [curdict[key_Param.ADDED_JSON]['Full_Comment']]
                    else:
                        ret += ['']
                else:
                    ret += ['']
            else:
                ret += ['']

            return ret

        elif self.is_in_active(group, name):
            curdict = self.myparams[group][name]
            ret = [curdict[key_Param.COMMENT]]
            if key_Param.ADDED_JSON in curdict.keys():
                if curdict[key_Param.ADDED_JSON] is not None:
                    if 'Full Comment' in curdict[key_Param.ADDED_JSON].keys():
                        ret += [curdict[key_Param.ADDED_JSON]['Full_Comment']]
                    else:
                        ret += ['']
                else:
                    ret += ['']
            else:
                ret += ['']

            return ret

        else:
            return None

    def get_json_values(self, group:str, name:str) -> dict:
        """
        Return the 'values' in json string if found, otherwise None obj
        """

        if self.is_in_default(group, name):
            curdict = self.myparams_default[group][name]
            if key_Param.ADDED_JSON in curdict.keys():
                if 'Values' in curdict[key_Param.ADDED_JSON].keys():
                    return curdict[key_Param.ADDED_JSON]['Values']

        elif self.is_in_active(group, name):
            curdict = self.myparams[group][name]
            if key_Param.ADDED_JSON in curdict.keys():
                if 'Values' in curdict[key_Param.ADDED_JSON].keys():
                    return curdict[key_Param.ADDED_JSON]['Values']

        else:
            return {}

    def _detect_enum_choices_from_value(self, value: Enum|None):
        """ Detect the enum choices from the value """
        if isinstance(value, Enum):
            # Choices are represented by the enum class itself.
            return value.__class__
        else:
            # FIXME Ambiguous! A str can be an actual str or a member of an
            # enumeration. In the latter case, we can't really know. That's
            # because we try to infer the type from the value.
            return None

    def _detect_type_from_value(self, value:Union[float, int, str, bool, tuple[int, int, int]]) -> Type_Param:
        """ Detect the type from the value """

        if isinstance(value, float):
            return Type_Param.Float
        # ATTEENTION : les booléens sont des entiers --> il faut les traiter avant
        elif isinstance(value, bool):
            return Type_Param.Logical
        elif isinstance(value, Enum):
            return Type_Param.Enum
        elif isinstance(value, int):
            return Type_Param.Integer
        elif isinstance(value, tuple):
            return Type_Param.Color
        else:
            tmp_path = Path(value)
            if tmp_path.is_file():
                return Type_Param.File
            elif tmp_path.is_dir():
                return Type_Param.Directory
            else:
                return Type_Param.String

    def change_param(self, group:str, name:str, value:Union[float, int, str, bool]):
        """ Modify the value of the parameter if found, otherwise None obj """

        #essai pour voir si le groupe existe ou non
        param = self.get_param_dict(group, name)

        if param is None:
            # le paramètre n'existe pas --> on l'ajoute
            if self.wx_exists:
                wx.MessageBox(_('This parameter is neither in the active group nor in the default group!'), _('Error'), wx.OK|wx.ICON_ERROR)
            else:
                logging.error(_('This parameter is neither in the current group nor in the default group!'))

            self.add_param(group, name, value,
                           self._detect_type_from_value(value),
                           enum_choices=self._detect_enum_choices_from_value(value),
                           whichdict='All')

        elif not self.is_in_active(group, name) and self.is_in_default(group, name):
            # le paramètre est dans les paramètres par défaut mais pas dans les paramètres actifs --> on l'ajoute
            default_value = self.myparams_default[group][name]
            if key_Param.ADDED_JSON in default_value.keys():
                json = default_value[key_Param.ADDED_JSON]
            else:
                json = None
            self.add_param(group, name, value,
                           default_value[key_Param.TYPE],
                           comment=default_value[key_Param.COMMENT],
                           jsonstr=json,
                           whichdict='Active')
        elif self.is_in_active(group, name):
            param = self.myparams[group][name]
            param[key_Param.VALUE] = value

        if self.update_incr_at_every_change:
            self._update_IncGroup()
            self._update_IncParam()


    # GROUPES/PARAMETRES INCREMENTABLES
    # ---------------------------------

    def update_incremental_groups_params(self, update_groups=True, update_params=True):
        """ Update the incremental groups and parameters """

        if update_groups:
            self._update_IncGroup()
        if update_params:
            self._update_IncParam()


    def isIncrementable_group(self, group:Union[str, dict]) -> bool:
        """
        Return True if the group is incrementable
        """

        if isinstance(group, str):
            if group in self.myIncGroup.keys():
                return True
            elif '$n$' in group:
                return True
            elif '$n(' in group:
                return True
            else:
                return False
        elif isinstance(group, dict):
            if group in self.myIncGroup:
                return True
            else:
                return False


    def isIncrementable_param(self, param:Union[str, dict]) -> bool:
        """
        Return True if the group is incrementable
        """
        if isinstance(param, str):
            if param in self.myIncGroup.keys():
                return True
            elif '$n$' in param:
                return True
            elif '$n(' in param:
                return True
            else:
                return False
        elif isinstance(param, dict):
            if param in self.myIncParam:
                return True
            else:
                return False

    def add_IncGroup(self,
                     group:str,
                     min:int,
                     max:int,
                     refGroup:str,
                     refParam:str):

        if not group in self.myIncGroup:
            # creation d'un dict sur base du nom de groupe
            curdict = self.myIncGroup[group] = {}
        else:
            curdict = self.myIncGroup[group]

        curdict["Ref group"] = refGroup
        curdict["Ref param"] = refParam
        curdict["Min"] = int(min)
        curdict["Max"] = int(max)
        curdict["Dict"] = {}

        if not "Saved" in curdict:
            curdict["Saved"] = {}

        return curdict["Dict"]


    def _update_IncGroup(self, withGUI:bool=False):
        """
        Mise à jour des groupes inctrémmentables:
        Les groupes existants dans les paramètres courants seront sauvés dans le dicionnaire myIncGroup avec son incrément associé.
        Tout groupe sauvé avec le même incrément sera écrasé.
        Si le nombre associé au groupe est plus grand que désiré, tous les groupes en surplus seront sauvés dans dans le dicionnaire myIncGroup
        mais supprimé du dictionnaire de paramètre courant.
        S'il n'y a pas assez de groupe dans les paramètres courant, on les ajoute avec les valeurs sauvées, sinon avec des valeurs par défaut.

        Also check the max and min values
        """
        for curIncGroup in self.myIncGroup:

            # groupe contenant le paramètre du nombre de groupes incrémentables
            refGroup = self.myIncGroup[curIncGroup]["Ref group"]
            # paramètre contenant le nompbre de groupes incrémentables
            refParam = self.myIncGroup[curIncGroup]["Ref param"]
            # nombre de groupes min
            iterMin = int(self.myIncGroup[curIncGroup]["Min"])
            # nombre de groupes max
            iterMax = int(self.myIncGroup[curIncGroup]["Max"])

            # nombre de groupes
            nbElements = int(self.get_param(refGroup,refParam))

            # dictionnaire de sauvegarde
            # savedDict = {}
            savedDict = self.myIncGroup[curIncGroup]["Saved"]
            templateDict = self.myIncGroup[curIncGroup]["Dict"]

            if(nbElements is None):
                if self.wx_exists:
                    wx.MessageBox(_('The reference of the incrementable group does not exist!'), _('Error'), wx.OK|wx.ICON_ERROR)
                else:
                    logging.error(_('The reference of the incrementable group does not exist!'))

            elif(nbElements>iterMax):
                nbElements = iterMax

            # elif(nbElements<iterMin):
            #     nbElements = iterMax

            for i in range(1,nbElements+1):
                # nom indicé du groupe incrémpentable
                curGroup = curIncGroup.replace("$n$",str(i))

                if(withGUI):
                    # If a graphical interface exists, we need to ensure that the encoded data is transferred to memory/object first.
                    for curParam in templateDict:
                        self._Apply1ParamtoMemory(curGroup, curParam, isIncrementable=True, genGroup=curIncGroup)

                if(curGroup in self.myparams):
                    # We keep a copy in the 'Saved' dictionary
                    savedDict[curGroup] = deepcopy(self.myparams[curGroup]) # deepcopy is necessary because it is a dict od dict

                elif(curGroup in savedDict):
                    # Priority to the saved dictionary, rather than the default dictionary
                    self.myparams[curGroup] = deepcopy(savedDict[curGroup]) # deepcopy is necessary because it is a dict od dict

                else:
                    # nothing found --> we create a new group from the default dictionary
                    self.myparams[curGroup] = deepcopy(templateDict) # deepcopy is necessary because it is a dict od dict

            for i in range(nbElements+1,iterMax+1):
                # all potential groups with an index greater than the desired number of elements
                curGroup = curIncGroup.replace("$n$",str(i))

                if(curGroup in self.myparams):
                    savedDict[curGroup] = deepcopy(self.myparams[curGroup]) # deepcopy is necessary because it is a dict od dict, copy is not enough
                    del self.myparams[curGroup]
                else:
                    break


    def add_IncParam(self,
                     group:str,
                     name:str,
                     value:Union[float, int, str],
                     comment:str,
                     type:Type_Param,
                     min:int = 0,
                     max:int = 0,
                     refParam:str = None,
                     refGroup:str = None,
                     added_json:str = None):
        """
        Ajout d'un paramètre incrémentable

        :param group: nom du groupe
        :param name: nom du paramètre
        :param value: valeur du paramètre
        :param comment: commentaire du paramètre
        :param type: type du paramètre
        :param min: valeur minimale
        :param max: valeur maximale
        :param refParam: nom du paramètre contenant le nombre de paramètres - doit être dans le même groupe

        """

        if added_json is not None:
            if isinstance(added_json, str):
                added_json = json.loads(added_json.replace('%json',''))
            elif isinstance(added_json, dict):
                pass

        if group not in self.myIncParam:
            self.myIncParam[group] = {}

        name, iterInfo = self._Extract_IncrInfo(name)

        if iterInfo is not None:
            if len(iterInfo) == 3:
                refParam, min, max = iterInfo
                refGroup = None
            elif len(iterInfo) == 4:
                refGroup, refParam, min, max = iterInfo
            else:
                logging.error("ERROR : wrong number of arguments in the incrementable parameter name {}!".format(name))

        refGroup = refGroup if refGroup is not None else group

        assert min >=0, "ERROR : min must be >= 0"
        assert max >0,  "ERROR : max must be > 0"
        assert max >= min, "ERROR : max must be >= min"
        assert refParam is not None, "ERROR : refParam can not be None"
        assert refGroup is not None, "ERROR : refGroup can not be None"

        curdict = self.myIncParam[group][name] = {}
        curdict["Group"] = group
        curdict["Ref group"] = refGroup
        curdict["Ref param"] = refParam
        curdict["Min"] = min
        curdict["Max"] = max
        curdict["Dict"] = {}
        curdict["Dict"][name] = {}
        curdict["Dict"][name][key_Param.NAME] = name
        curdict["Dict"][name][key_Param.VALUE] = value
        curdict["Dict"][name][key_Param.COMMENT] = comment
        curdict["Dict"][name][key_Param.TYPE] = type
        if added_json is not None:
            curdict["Dict"][name][key_Param.ADDED_JSON] = added_json
        else:
            curdict["Dict"][name][key_Param.ADDED_JSON] = None
        curdict["Saved"] = {}
        curdict["Saved"][group] = {}
        curdict["Saved"][group][name] = {}
        curdict["Saved"][group][name][key_Param.NAME] = name
        curdict["Saved"][group][name][key_Param.VALUE] = value
        curdict["Saved"][group][name][key_Param.COMMENT] = comment
        curdict["Saved"][group][name][key_Param.TYPE] = type
        if added_json is not None:
            curdict["Saved"][group][name][key_Param.ADDED_JSON] = added_json
        else:
            curdict["Saved"][group][name][key_Param.ADDED_JSON] = None

        return 0


    def _update_IncParam(self, withGUI:bool=False):
        """
        Mise à jour des paramètres inctrémmentables:
        Les paramètres existants dans les paramètres courants seront sauvés dans le dicionnaire myIncParam avec son incrément associé.
        Tout groupe sauvé avec le même incrément sera écrasé.
        Si le nombre associé au groupe est plus grand que désiré, tous les groupe en surplus seront sauvé dans dans le dicionnaire myIncParam
        mais supprimé du dictionnaire de paramètre courant.
        S'il n'y a pas assez de groupe dans les paramètres courant, on les ajoute avec les valeurs sauvées, sinon avec des valeurs par défaut.

        Also check the max and min values
        """
        for refGroup in self.myIncParam:
            for curIncParam in self.myIncParam[refGroup]:
                if(refGroup.find("$n$")>-1):
                    nbMax = int(self.myIncGroup[refGroup]["Max"])

                    i=1
                    while(i<nbMax+1):
                        curGroup = refGroup.replace("$n$",str(i))
                        i += 1
                        if curGroup in self.myparams:
                            self._Update_OneIncParam(curIncParam, curGroup, genGroup=refGroup, withGUI=withGUI)
                        else:
                            break
                else:
                    if not refGroup in self.myparams:
                        self.myparams[refGroup] = {}
                    self._Update_OneIncParam(curIncParam, refGroup, genGroup=refGroup, withGUI=withGUI)


    def _Update_OneIncParam(self, curIncParam:str, curGroup:str, genGroup:str, withGUI:bool=False):
        """
        Routine interne de mise à jour d'un seul paramétre incrémentable

        :param curIncParam : nom du paramètre incrémentable - contient $n$ à remplacer par le numéro
        :param curGroup : nom du groupe de référence - ! peut être un groupe icrémentable !
        :param genGroup : nom du groupe générique dans lequel sont stockés les informations sur le paramètre (key, value, min, max, ...)
        :param withGUI : True si on est en mode GUI

        """

        refGroup = self.myIncParam[genGroup][curIncParam]["Ref group"] # groupe dans lequel est stocké le nombre de paramètres
        refParam = self.myIncParam[genGroup][curIncParam]["Ref param"] # nom du paramètre contenant le nombre de paramètres
        iterMin = int(self.myIncParam[genGroup][curIncParam]["Min"])   # nombre minimal de paramètres
        iterMax = int(self.myIncParam[genGroup][curIncParam]["Max"])   # nombre maximal de paramètres

        # logging.info(curGroup+" / "+refParam)

        if '$n$' in refGroup:
            # le groupe de référence est incrémentable --> le paramètre est à trouver dans le groupe courant

            part_Group = refGroup.replace("$n$","")
            if part_Group in curGroup:
                refGroup = curGroup
            else:
                logging.error(_("ERROR : the reference group {} does not exist or is not well defined {}!".format(part_Group, curGroup)))

        nbElements = self[(refGroup, refParam)] #int(self.get_param(refGroup, refParam))

        if nbElements is None:
            logging.error(_("ERROR : the reference of the incrementable parameter does not exist!"))
            return

        savedDict = {}
        savedDict = self.myIncParam[genGroup][curIncParam]["Saved"]
        if(not(curGroup in savedDict)):
            savedDict[curGroup] = {}

        templateDict = self.myIncParam[genGroup][curIncParam]["Dict"]

        if curIncParam in templateDict.keys():
            templateDict = templateDict[curIncParam]
        else:
            logging.error(_("ERROR : the template of the incrementable parameter does not exist!"))

        if(nbElements is None):
            if self.wx_exists:
                wx.MessageBox(_('The reference of the incrementable group does not exist!'), _('Error'), wx.OK|wx.ICON_ERROR)
            else:
                logging.error(_('The reference of the incrementable group does not exist!'))
        elif(nbElements>iterMax):
            nbElements = iterMax
        # elif(nbElements<iterMin):
        #     nbElements = iterMax

        for i in range(1, nbElements+1):
            curParam = curIncParam.replace("$n$",str(i))

            if(withGUI):
                self._Apply1ParamtoMemory(curGroup, curParam, isIncrementable=True, genGroup=genGroup, genParam=curIncParam)

            if(curParam in self.myparams[curGroup]):
                savedDict[curGroup][curParam] = {}
                savedDict[curGroup][curParam] = self.myparams[curGroup][curParam]

            elif(curParam in savedDict[curGroup]):
                self.myparams[curGroup][curParam] = {}
                self.myparams[curGroup][curParam] = savedDict[curGroup][curParam]

            else:
                self.myparams[curGroup][curParam] = {}
                self.myparams[curGroup][curParam][key_Param.NAME] = curParam
                self.myparams[curGroup][curParam][key_Param.VALUE] = templateDict[key_Param.VALUE]
                self.myparams[curGroup][curParam][key_Param.COMMENT] = templateDict[key_Param.COMMENT]
                self.myparams[curGroup][curParam][key_Param.TYPE] = templateDict[key_Param.TYPE]
                if key_Param.ADDED_JSON in templateDict:
                    self.myparams[curGroup][curParam][key_Param.ADDED_JSON] = templateDict[key_Param.ADDED_JSON]
                else:
                    self.myparams[curGroup][curParam][key_Param.ADDED_JSON] = None
        # transfert des paramètres en surplus dans le dictionnaire savedDict
        for i in range(nbElements+1, iterMax+1):
            curParam = curIncParam.replace("$n$",str(i))

            if(curParam in self.myparams[curGroup]):
                savedDict[curGroup][curParam] = {}
                savedDict[curGroup][curParam] = self.myparams[curGroup][curParam].copy()
                self.myparams[curGroup].pop(curParam)

            else:
                # inutile de continuer, on a atteint le dernier paramètre
                break

if __name__ =="__main__":
    test = Wolf_Param()
    test[('group1','val1')] = "valtest"
    assert test[('group1','val1')] == "valtest"