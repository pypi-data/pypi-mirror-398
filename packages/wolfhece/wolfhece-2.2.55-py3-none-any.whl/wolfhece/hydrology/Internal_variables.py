from __future__ import annotations
from typing import Optional
from os.path import exists, join
import numpy as np
import logging
from datetime import datetime as date
from datetime import timezone
from dataclasses import dataclass
from . import read as rd
from ..PyParams import Wolf_Param

ALL_VAR = 0
IV_VAR = 1
FRAC_VAR = 2
FINAL_OUT_VAR = 3
OUT_VAR = 4
DEFAULT_VAR = 5


@dataclass(frozen=True)
class Internal_Variable:
    """
    Class for managing internal variables in hydrological models.
    """
    name:str
    file:str
    type_of_var:int
    linked_param:int
    id:int


    def get_time_serie(self, directory, prefix_file:str="", 
                       interval:Optional[tuple[date, date]]=None) -> tuple[np.ndarray, np.ndarray]:
        """
        Get the time series of the internal variable.

        :param interval: Optional interval for the time series.
        :return: Time series of the internal variable.
        """
        filename, full_path = self.get_filename(directory, prefix=prefix_file)
        if filename is None:
            return None, None
        time, cur_iv = rd.read_hydro_file(directory, fileName=filename)
        # select the interval if needed
        if interval is not None:
            # Check if the datetime in interva are in UTC timezone
            if interval[0].tzinfo == timezone.utc or interval[1].tzinfo == timezone.utc:
                interval = (interval[0].replace(tzinfo=timezone.utc),
                            interval[1].replace(tzinfo=timezone.utc))
                t_start = interval[0].timestamp()
                t_end = interval[1].timestamp()
                time = time[(time >= t_start) & (time <= t_end)]
                cur_iv = cur_iv[(time >= t_start) & (time <= t_end)]
            else:
                logging.error("Interval is not in UTC timezone!")

        return time, cur_iv


    def get_filename(self, directory:str, prefix:str="")->tuple[str, str]:
        """
        Get the filename of the internal variable.

        :param directory: Directory where the file is located.
        :param prefix: Prefix for the filename.
        :return: Tuple containing the name of the file only and the full path of the internal variable.
        """
        filename = "".join([prefix,"_", self.file, ".dat"])
        full_path = join(directory, filename)
        # check if the file exists
        if not exists(full_path):
            logging.error(f"File {full_path} not found!")
            return None, None

        return filename, full_path


# @dataclass(frozen=True)
class Param_to_Activate:
    """
    Class for managing parameters to activate in hydrological models.
    """
    key: str
    group: str
    file: str
    all_variables: list[Internal_Variable]

    def __init__(self, key:str="", group:str="", file:str="", all_variables:list[Internal_Variable]=[]):
        """
        Initialize the Params_to_Activate class with parameters for different models.
        """       
        self.key = key
        self.group = group
        self.file = file
        self.all_variables = all_variables

    def add_param_info(self, key:str, group:str, file:str):
        """
        Add parameter information to the class.
        """
        self.key = key
        self.group = group
        self.file = file

    def check_param_file(self, directory:str):
        """
        Define the working directory for the parameters.
        """
        cur_file = join(directory, self.file)
        # check if the file exists
        if not exists(cur_file):
            logging.error(f"File {cur_file} not found!")
            
    def add_variable(self, variable:Internal_Variable|list[Internal_Variable]):
        """
        Add one or a list of internal variable(s) to the list of variables.
        """
        if isinstance(variable, list):
            self.all_variables += variable
        else:
            self.all_variables.append(variable)
        
    def get_variables_names(self) -> list[str]:
        """
        Get the names of the internal variables.
        """
        return [var.name for var in self.all_variables]
    
    def get_variables_files(self) -> list[str]:
        """
        Get the files of the internal variables.
        """
        return [var.file for var in self.all_variables]
    
    def activate(self, directory:str, prefix_file:str="", type_of_var:int=ALL_VAR):
        """
        Activate the parameters for the internal variables.
        """
        # If the key is None, it means that it either always written or it is just not an internal variable but directly an exit
        if self.key is None or self.group is None:
            return
        
        to_activate = False
        if type_of_var == ALL_VAR:
            to_activate = True
        else:
            for var in self.all_variables:
                if var.type_of_var == type_of_var or type_of_var == ALL_VAR:
                    to_activate = True
                    break

        if to_activate:
            new_prefix = self._build_prefix(prefix_file)
            filename = ".".join([new_prefix,"param"])
            param_filename = join(directory, filename)            
            param_file = Wolf_Param(to_read=True, filename=param_filename,toShow=False, init_GUI=False)
            param_file.change_param(self.group, self.key, 1)
            param_file.SavetoFile(None)
            param_file.Reload(None)


    def deactivate(self, directory:str, prefix_file:str=""):
        """
        Deactivate the parameters for the internal variables.
        """
        # If the key is None, it means that it either always written or it is just not an internal variable but directly an exit
        if self.key is None or self.group is None:
            return
        
        new_prefix = self._build_prefix(prefix_file)
        filename = ".".join([new_prefix,"param"])
        param_filename = join(directory, filename)
        param_file = Wolf_Param(to_read=True, filename=param_filename,toShow=False, init_GUI=False)
        param_file.change_param(self.group, self.key, 0)
        param_file.SavetoFile(None)
        param_file.Reload(None)

    def get_iv_timeseries(self, directory:str, prefix_file:str="", interval:Optional[tuple[date, date]]=None, type_of_var:int=ALL_VAR) -> dict[str, np.ndarray]:
        """
        Get the time series of the internal variables.

        :param directory: Directory where the file is located.
        :param prefix_file: Prefix for the filename.
        :param interval: Optional interval for the time series.
        :return: List of tuples containing the time and internal variable data.
        """

        new_prefix = self._build_prefix(prefix_file)

        all_timeseries = {var.name: 
                          var.get_time_serie(directory, new_prefix, interval)[1]
                          for var in self.all_variables 
                          if var.type_of_var == type_of_var or type_of_var == ALL_VAR}

        return all_timeseries
    

    def get_linked_params(self) -> dict[str, int]:
        """
        Get the linked parameters of the internal variables.

        :return: Dictionary of linked parameters.
        """
        return {var.name: var.linked_param for var in self.all_variables if var.linked_param is not None}
    
    def _build_prefix(self, prefix_file:str) -> str:
        """
        Build the prefix for the filename.

        :param prefix_file: Prefix for the filename.
        :return: Prefix for the filename.
        """
        if self.file == "":
            return prefix_file
        else:
            return "_".join([prefix_file, self.file])
    


class Group_to_Activate:
    """
    Class for managing groups of parameters to activate in hydrological models.
    """
    name: str
    all_params: list[Param_to_Activate]

    def __init__(self, name:str="", all_params:list[Param_to_Activate]=[]):
        """
        Initialize the Group_to_Activate class with parameters for different models.
        """       
        self.name = name
        self.all_params = all_params

    def get_keys(self) -> list[str]:
        """
        Get the keys of the parameters.
        """
        return [param.key for param in self.all_params]

    def get_files_per_keys(self) -> list[str]:
        """
        Get the files of the parameters.
        """
        return [param.get_variables_files() for param in self.all_params]

    def activate_all(self, directory:str, prefix_file:str="", type_of_var:int=ALL_VAR):
        """
        Activate all parameters in the group.
        """
        for param in self.all_params:
            param.activate(directory, prefix_file, type_of_var)

    def deactivate_all(self, directory:str, prefix_file:str=""):
        """
        Deactivate all parameters in the group.
        """
        for param in self.all_params:
            param.deactivate(directory, prefix_file)

    def get_all_iv_timeseries(self, directory:str, prefix_file:str="",
                              interval:Optional[tuple[date, date]]=None,
                              type_of_var:int=ALL_VAR) -> dict[str, np.ndarray]:
        """
        Get the time series of all internal variables in the group.

        :param directory: Directory where the file is located.
        :param prefix_file: Prefix for the filename.
        :param interval: Optional interval for the time series.
        :return: List of tuples containing the time and internal variable data.
        """
        all_timeseries = {}
        for param in self.all_params:
            all_timeseries.update(param.get_iv_timeseries(directory, prefix_file,
                                                          interval, type_of_var))

        return all_timeseries
    
    def get_all_linked_params(self) -> dict[str, int]:
        """
        Get the linked parameters of the internal variables.

        :return: Dictionary of linked parameters.
        """
        all_linked_params = {}
        for param in self.all_params:
            all_linked_params.update(param.get_linked_params())

        return all_linked_params
    
    def get_all_variables_names_from_ids(self, ids:list[int], 
                                         type_of_var:int=ALL_VAR) -> tuple[list[str], list[int]]:
        """
        Get the names of the internal variables from their IDs.

        :param ids: List of IDs of the internal variables.
        :return: List of names of the internal variables.
        """
        all_names = []
        kept_indices = []
        for param in self.all_params:
            for var in param.all_variables:
                if var.id in ids and (var.type_of_var == type_of_var or type_of_var == ALL_VAR):
                    all_names.append(var.name)
                    kept_indices.append(ids.index(var.id))

        return all_names, kept_indices
    
    def get_dict_from_matrix_and_ids(self, matrix:np.ndarray, ids:list[int], 
                                     type_of_var:int=ALL_VAR) -> dict[str, np.ndarray]:
        """
        Get a dictionary from a matrix and a list of IDs.

        :param matrix: Matrix containing the data.
        :param ids: List of IDs corresponding to the data.
        :return: Dictionary with IDs as keys and data as values.
        """
        # Check the dimensions of the matrix and the length of the IDs
        if matrix.shape[1] != len(ids):
            logging.error("Matrix length does not match IDs length!")
            return {}
        # Extract the the names of the internal variables from the IDs
        names, kept_indices = self.get_all_variables_names_from_ids(ids, type_of_var=type_of_var)
        
        return {key: matrix[:,i] for key, i in zip(names, kept_indices)}
