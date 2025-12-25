"""
Author: HECE - University of Liege, Vincent Schmitz
Date: 2025

Copyright (c) 2025 University of Liege. All rights reserved.

This script and its content are protected by copyright law. Unauthorized
copying or distribution of this file, via any medium, is strictly prohibited.
"""

import wx
import wx.propgrid as pg
import json
import os
from os.path import join
from pathlib import Path
import logging
import subprocess
import numpy as np
from matplotlib.widgets import Slider, Button
from matplotlib import pyplot as plt
from mpl_toolkits.mplot3d.art3d import Poly3DCollection
import matplotlib.tri as tri
import time

try:
    from wolfpydike.dikeBreaching import pyDike, injector
except ImportError:
    # Test if wolfpydike is installed and check the version
    try:
        import wolfpydike
        version = wolfpydike.__version__
        if version < '0.1.2':
            raise ImportError("wolfpydike version is too old. Please update to at least version 0.1.2")
    except:
        raise ImportError(_("Error importing pyDike. Make sure the pydike library is installed and accessible (use 'pip install wolfpydike')."))

from wolfhece.drawing_obj import Element_To_Draw
from wolfhece.PyParams import Wolf_Param, Type_Param, Buttons, key_Param, new_json
from wolfhece.PyDraw import Triangulation
from wolfhece.wolf_array import WolfArray
from wolfhece.matplotlib_fig import Matplotlib_Figure
from wolfhece.PyTranslate import _

class CoupledSimulation():
    """
    !!! UNDER DEVELOPMENT !!!
    Class for the coupled simulation between WOLF and pydike.
    """

    def __init__(self):
        try:
            from wolfgpu.SimulationRunner import SimulationRunner, SimulationInjector, SimulationProxy
            from wolfgpu.simple_simulation import SimulationDuration, SimpleSimulation
            from wolfgpu.results_store import ResultsStore
        except ImportError:
            logging.warning(_("Warning: wolfgpu module not found. Coupled WOLF-pydike simulations will not be available."))

        self.filename = None
        self.injectorWolf = None
        self.interpMatrix = None
        self.sim = SimpleSimulation()
        self.store_dir = None
        # WHEN INTERACTIONS BETWEEN WOLF AND PYDIKE ARE ACTIVATED
        self.updateFrequency = 30 #[s] Update frequency of the topo in WOLF
        self.firstUpdate = 1 #[s] Time of the first update of the topo in WOLF

class InjectorWolfDike(Element_To_Draw):
    """
    !!! UNDER DEVELOPMENT !!!
    Class for the injector object.
    The injector is used to inject the breach topography in the WOLF simulation.
    """
    def __init__(self, idx = '', plotted = True, mapviewer=None, need_for_wx = False):
        super().__init__(idx, plotted, mapviewer, need_for_wx)
        self.wp = None
        self._injector = injector()

    def set_params(self, params):
        """
        Set the injector parameters.
        :param params: Parameters to set for the injector.
        """
        return self._injector.set_params(params)

    def get_params(self):
        """
        Set the injector parameters.
        :param params: Parameters to set for the injector.
        """
        return self._injector.get_params()

    def save(self):
        '''
        Save the parameters in a .json text file
        '''
        if self.filename is None:
            self.save_as()
        else:
            with open(self.filename, 'w') as f:
                json.dump(self.get_params(), f, indent=4)

    def save_as(self):
        '''
        Save the parameters in a .json text file
        '''
        filterArray = "json (*.json)|*.json|all (*.*)|*.*"
        fdlg = wx.FileDialog(None, _("Where should the parameters be stored (.json file)?"), wildcard=filterArray, style=wx.FD_SAVE)
        ret = fdlg.ShowModal()
        if ret == wx.ID_OK:
            self.filename = fdlg.GetPath()
            self.save()

        fdlg.Destroy()

    def callback_apply(self):
        """
        Callback function to apply changes made in the Wolf_Param window.
        Update the parameters in the dike object.
        """
        updated_wp = self.wp.merge_dicts()
        self.from_wp_to_dict(wolf_dict=updated_wp, dict_ref=self.get_params())

    def show_properties(self):
        """
        Show properties window
        """
        if self.wp is None:
            self.wp = self.from_dict_to_wp(params_dict=self.get_params())
            self.wp.set_callbacks(callback_update=self.callback_apply, callback_destroy=None)
            self.wp._set_gui_dike(title=_('Injector parametrization'))
            self.wp.hide_selected_buttons([Buttons.Reload,Buttons.Save])
        self.wp.Show()

    def hide_properties(self):
        """
        Hide properties window
        """
        if self.wp is not None:
            self.wp.Hide()

    def from_wp_to_dict(self, wolf_dict, dict_ref) -> dict:
        """
        Convert a Wolf_Param dictionary to a "normal" dictionary used as parameters dictionary in the injector object + updates injector attributes accordingly.
        'dict_ref' used to rename keys (=mapping).
        :param wolf_dict: Dictionary containing the parameters from the Wolf_Param object.
        :param dict_ref: Dictionary mapping injector parameter names (keys) to explicit names in wolf_param.
        :return: Dictionary with injector parameter names as keys, containing values and metadata.
        """
        params_dict = {}

        for section in wolf_dict.keys():
            params_dict[section] = {}
            for param_data in wolf_dict[section].values():
                explicit_name = param_data[key_Param.NAME]  # Extract explicit name

                # Search for the corresponding injector_key inside dict_ref
                injector_key = None
                for section_name, section_params in dict_ref.items():
                    for param_key, param_details in section_params.items():
                        if param_details.get("explicit name") == explicit_name:
                            injector_key = param_key  # Get the correct parameter key
                            break
                    if injector_key:  # Exit the outer loop if found
                        break

                if injector_key is None:
                    print(_("Warning: No match found in dict_ref for '%s'") % explicit_name)
                    continue  # Skip if no match is found

                params_dict[section][injector_key] = {
                    "value": param_data[key_Param.VALUE],
                    "description": param_data[key_Param.COMMENT],
                    "explicit name": explicit_name,
                    "type": param_data[key_Param.TYPE],
                    "choices": dict_ref[section_name][injector_key].get("choices"),
                    "mandatory": dict_ref[section_name][injector_key].get("mandatory"),
                }

        self._dike.update_paramsDict(params_dict)

        return

    def from_dict_to_wp(self,params_dict) -> Wolf_Param:
        """ Modify the Wolf_Param object to represent the injector parameters. """

        wp = Wolf_Param_dike(parent = None, # Contains all the parameters of the window
                            title = _("Breaching of a dike"),
                            to_read=False,
                            withbuttons=True,
                            toShow=False,
                            init_GUI=False,
                            force_even_if_same_default = True,
                            filename="default_name.json",
                            DestroyAtClosing=False)

        for current_section in params_dict.keys():
            for key in params_dict[current_section].keys():

                value = params_dict[current_section][key]["value"]
                description = params_dict[current_section][key]["description"]
                name = params_dict[current_section][key]["explicit name"]
                # Parameter type
                if params_dict[current_section][key]["type"] == "Float":
                    type_param = Type_Param.Float
                elif params_dict[current_section][key]["type"] == "Integer":
                    type_param = Type_Param.Integer
                elif params_dict[current_section][key]["type"] == "Logical":
                    type_param = Type_Param.Logical
                elif params_dict[current_section][key]["type"] == "String":
                    type_param = Type_Param.String
                elif params_dict[current_section][key]["type"] == "Directory":
                    type_param = Type_Param.Directory
                elif params_dict[current_section][key]["type"] == "File":
                    type_param = Type_Param.File

                if params_dict[current_section][key]["choices"] != None:
                    wp.add_param((current_section), (name), value, type_param, whichdict='Default', jsonstr=new_json(params_dict[current_section][key]["choices"]), comment=_(description))
                    if params_dict[current_section][key]["mandatory"]:
                        wp.add_param((current_section), (name), value, type_param, whichdict='Active', jsonstr=new_json(params_dict[current_section][key]["choices"]), comment=_(description))
                else:
                    wp.add_param((current_section), (name), value, type_param, whichdict='Default', comment=_(description))
                    if params_dict[current_section][key]["mandatory"]:
                        wp.add_param((current_section), (name), value, type_param, whichdict='Active', comment=_(description))
        return wp

    # def read_params(self, file_name:str, store_dir: Path = None):
        # '''
        # Read the model parameters and store them in a dictionary + updates attributes accordingly
        # :param file_name: name of the file to read
        # :param store_dir: directory where to read the file
        # '''
        # self._dike.read_params(file_name, store_dir)
class DikeWolf(Element_To_Draw):

    def __init__(self, idx = '', plotted = True, mapviewer=None, need_for_wx = False):
        super().__init__(idx, plotted, mapviewer, need_for_wx)

        self.filename = None
        self.wp = None
        self.injector = None
        self.interpMatrix = None
        self._dike = pyDike()

    def run_lumped(self, params_dir=None):
        """
        Run the dike breaching simulation using the lumped model.
        :param store_dir: Directory where the simulation will be run.
        """
        try:
            self._dike.run_initialization(params_dir=params_dir)
            for time_idx in np.arange(0,self._dike.t_end_idx,1):
                self._dike.run(time_idx)
            logging.info(_("Breaching simulation done."))
        except subprocess.CalledProcessError as e:
            logging.error(_("Error while running the breaching simulation: %s") % e)

    def set_injector(self):
        """
        !!! UNDER DEVELOPMENT !!!
        Set the injector for the dike object.
        :param injector: Injector object to be set.
        """
        self.injectorWolf = InjectorWolfDike()
        self.mapviewer.add_object(newobj=self.injectorWolf, which='injector', id=_("Injector_{filename}").format(filename=self.filename))

    def run_2Dcoupled(self, params_dir=None):
        """
        !!! UNDER DEVELOPMENT !!!
        Run the dike breaching simulation coupled with WOLF.
        :param store_dir: Directory where the simulation will be run.
        """
        try:
            from wolfgpu.SimulationRunner import SimulationRunner, SimulationInjector, SimulationProxy
            from wolfgpu.simple_simulation import SimulationDuration, SimpleSimulation
            from wolfgpu.results_store import ResultsStore
        except ImportError:
            logging.warning(_("Warning: wolfgpu module not found. Coupled WOLF-pydike simulations will not be available."))

        if self.injectorWolf is None:
            logging.error(_("Injector is not set. Please set the injector before running the simulation."))
            return

        # Select WOLF array file
        filterArray = "Wolf array files (*.bin)|*.bin"
        dlg = wx.FileDialog(self.mapviewer, _('Choose the file containing the Wolf array on which interpolation is applied'), wildcard=filterArray, style=wx.FD_FILE_MUST_EXIST)
        ret=dlg.ShowModal()
        if ret == wx.ID_CANCEL:
            dlg.Destroy()
        path_TriangArray = dlg.GetPath()
        self.interpMatrix = WolfArray(fname = path_TriangArray)

        # Select WOLF simulation data folder
        dlg = wx.DirDialog(self.mapviewer, _('Folder containing WOLF simulation data'), style=wx.DD_DEFAULT_STYLE)
        ret=dlg.ShowModal()
        if ret == wx.ID_CANCEL:
            dlg.Destroy()
        path_sim = dlg.GetPath()
        sim = SimpleSimulation.load(path_sim)

        # self.mapviewer.add_object(newobj=sim, which='triangulation', id=_("Triangulation_{filename}_{index:03d}").format(filename=self.filename, index=current_idx))
        # logging.info(_("Added triangulation for time index %d to viewer.") % current_idx)

        try:
            self._dike.run_initialization(params_dir=params_dir)
            for time_idx in np.arange(0,self._dike.t_end_idx,1):
                self._dike.run(time_idx)
            logging.info(_("Breaching simulation done."))
        except subprocess.CalledProcessError as e:
            logging.error(_("Error while running the breaching simulation: %s") % e)

    def callback_apply(self):
        """
        Callback function to apply changes made in the Wolf_Param window.
        Update the parameters in the dike object.
        """
        updated_wp = self.wp.merge_dicts()
        self.from_wp_to_dict(wolf_dict=updated_wp, dict_ref=self.get_params())

    def show_properties(self):
        """
        Show properties window
        """
        if self.wp is None:
            self.wp = self.from_dict_to_wp(params_dict=self.get_params())
            self.wp.set_callbacks(callback_update=self.callback_apply, callback_destroy=None)
            self.wp._set_gui_dike(title=_('Parameters for simulation with default parameters already set'))
            self.wp.hide_selected_buttons([Buttons.Reload,Buttons.Save])
        self.wp.Show()

    def hide_properties(self):
        """
        Hide properties window
        """
        if self.wp is not None:
            self.wp.Hide()

    def from_wp_to_dict(self, wolf_dict, dict_ref) -> dict:
        """
        Convert a Wolf_Param dictionary to a "normal" dictionary used as parameters dictionary in the pydike object + updates pydike attributes accordingly.
        'dict_ref' used to rename keys (=mapping).
        :param wolf_dict: Dictionary containing the parameters from the Wolf_Param object.
        :param dict_ref: Dictionary mapping pydike parameter names (keys) to explicit names in wolf_param.
        :return: Dictionary with pydike parameter names as keys, containing values and metadata.
        """
        params_dict = {}

        for section in wolf_dict.keys():
            params_dict[section] = {}
            for param_data in wolf_dict[section].values():
                explicit_name = param_data[key_Param.NAME]  # Extract explicit name

                # Search for the corresponding pydike_key inside dict_ref
                pydike_key = None
                for section_name, section_params in dict_ref.items():
                    for param_key, param_details in section_params.items():
                        if param_details.get("explicit name") == explicit_name:
                            pydike_key = param_key  # Get the correct parameter key
                            break
                    if pydike_key:  # Exit the outer loop if found
                        break

                if pydike_key is None:
                    print(_("Warning: No match found in dict_ref for '%s'") % explicit_name)
                    continue  # Skip if no match is found

                params_dict[section][pydike_key] = {
                    "value": param_data[key_Param.VALUE],
                    "description": param_data[key_Param.COMMENT],
                    "explicit name": explicit_name,
                    "type": param_data[key_Param.TYPE],
                    "choices": dict_ref[section_name][pydike_key].get("choices"),
                    "mandatory": dict_ref[section_name][pydike_key].get("mandatory"),
                }

        self._dike.update_paramsDict(params_dict)

        return

    def from_dict_to_wp(self,params_dict) -> Wolf_Param:
        """ Modify the Wolf_Param object to represent the dike parameters. """

        wp = Wolf_Param_dike(parent = None, # Contains all the parameters of the window
                            title = _("Breaching of a dike"),
                            to_read=False,
                            withbuttons=True,
                            toShow=False,
                            init_GUI=False,
                            force_even_if_same_default = True,
                            filename="default_name.json",
                            DestroyAtClosing=False)

        for current_section in params_dict.keys():
            for key in params_dict[current_section].keys():

                value = params_dict[current_section][key]["value"]
                description = params_dict[current_section][key]["description"]
                name = params_dict[current_section][key]["explicit name"]
                # Parameter type
                if params_dict[current_section][key]["type"] == "Float":
                    type_param = Type_Param.Float
                elif params_dict[current_section][key]["type"] == "Integer":
                    type_param = Type_Param.Integer
                elif params_dict[current_section][key]["type"] == "Logical":
                    type_param = Type_Param.Logical
                elif params_dict[current_section][key]["type"] == "String":
                    type_param = Type_Param.String
                elif params_dict[current_section][key]["type"] == "Directory":
                    type_param = Type_Param.Directory
                elif params_dict[current_section][key]["type"] == "File":
                    type_param = Type_Param.File

                if params_dict[current_section][key]["choices"] != None:
                    wp.add_param((current_section), (name), value, type_param,
                                 whichdict='Default', jsonstr=new_json(params_dict[current_section][key]["choices"]),
                                 comment=_(description))
                    if params_dict[current_section][key]["mandatory"]:
                        wp.add_param((current_section), (name), value, type_param,
                                     whichdict='Active', jsonstr=new_json(params_dict[current_section][key]["choices"]),
                                     comment=_(description))
                else:
                    wp.add_param((current_section), (name), value, type_param, whichdict='Default', comment=_(description))
                    if params_dict[current_section][key]["mandatory"]:
                        wp.add_param((current_section), (name), value, type_param, whichdict='Active', comment=_(description))
        return wp

    def load_results(self):
        """
        Load the main outputs and/or the triangulation of the simulation.
        """
        filterArray = "Parameter files (*_paramsDike.json)|*_paramsDike.json"
        dlg = wx.FileDialog(self.mapviewer, _('Choose the file containing the simulation parametrization'), wildcard=filterArray, style=wx.FD_FILE_MUST_EXIST)
        ret=dlg.ShowModal()
        if ret == wx.ID_CANCEL:
            dlg.Destroy()
        self.param_path = dlg.GetPath()
        if self.param_path.endswith("_paramsDike.json"):
            gen_path = self.param_path.removesuffix("_paramsDike.json")
        else:
            logging.warning(_("ERROR : the name of the file containing the simulation parametrization should end with '_paramsDike.json'"))
            dlg.Destroy()
            return

        self.param_path = Path(self.param_path)
        self.filename = (self.param_path.name).removesuffix("_paramsDike.json")
        self.read_params(file_name=self.filename, store_dir=self.param_path.parent)

        try:
            mainOutputs_path = Path(gen_path + '_mainOutputs.txt')
            mainOutputs_dict = {}
            with open(mainOutputs_path, "r", encoding="utf-8") as f:
                lines = f.readlines()

            if not lines:
                logging.warning(_("ERROR: The file '%s' is empty.") % mainOutputs_path)
            else:
                # Extract column headers
                keys = lines[0].strip().split("\t")

                # Initialize dictionary with empty lists
                mainOutputs_dict = {key: [] for key in keys}

                # Populate lists with float values
                for line in lines[1:]:
                    values = line.strip().split("\t")
                    for key, value in zip(keys, values):
                        try:
                            mainOutputs_dict[key].append(float(value))  # cast to float
                        except ValueError:
                            logging.warning(_("Non-float value encountered: %s (in key: %s)") % (value, key))
                self.set_series(mainOutputs_dict)
        except FileNotFoundError:
            logging.warning(_("WARNING: The file containing the main outputs does not exist. The following format is expected: 'TESTNAME_mainOutputs.txt'"))

        try:
            triangulation_path = Path(gen_path + '_triangulation.json')
            with open(triangulation_path, 'r') as f:
                triangulation_dict = json.load(f)
            self.set_triangulation(triangulation_dict)
        except FileNotFoundError:
            logging.warning(_("WARNING : the file containing the triangulation does not exist. The following format is expected: 'TESTNAME_triangulation.json'"))

    def set_series(self, mainOutputs_dict):
        """
        Set the main outputs in the dike object.
        """
        self._dike.set_series_fromDict(mainOutputs_dict)

    def set_triangulation(self, triangulation_dict):
        """
        Set the triangulation in the dike object.
        """
        self._dike.triangulation_dict = triangulation_dict

    @property
    def mainOutputs_dict(self):
        """
        Get the main outputs of the simulation as a dictionary. Time [s] / Qin [m^3/s] / Btop_US [m] / Btop_DS [m] / z_b [m] / Qb [m^3/s] / z_s [m] / z_t [m]
        :return: dictionary containing the main outputs
        """
        return self._dike.get_series_toDict()

    @property
    def triangulation_dict(self):
        """
        Get the triangulation of the simulation.
        :return: dictionary containing the triangulation
        """
        return self._dike.triangulation_dict

    def show_triangulation(self):
        """
        Plot a graph that shows the dike triangulation.
        """

        def update_triangulation(time_idx: int):

            # Get the XYZ and triangles for the given time
            XYZ = np.array(self.triangulation_dict[str(time_idx)]["XYZ"])
            triangles = np.array(self.triangulation_dict[str(time_idx)]["idx_triangles"])
            time = times_tri[time_idx]

            # Update the vertices and face colors of the Poly3DCollection
            poly_collection.set_verts(XYZ[triangles])

            # Update the title with the current time value
            template = _("Elapsed time: {hours:.0f} [h] {minutes:.0f} [min] {seconds:.0f} [s]")
            elapsed = template.format(hours=np.floor(time / 3600), minutes=np.floor(time / 60) % 60, seconds=time % 60)
            ax.set_title(elapsed, fontsize=18)

            # Refresh the plot
            fig.canvas.draw_idle()

        def update_triangulation_safe(val):
            """
            Safely update the triangulation plot, throttling updates to avoid excessive redraws.
            """
            current_time = time.time()
            if current_time - last_update[0] > 0.2:  # Only update every 0.2 seconds
                update_triangulation(int(val))
                last_update[0] = current_time

        # Prepare data for the initial plot
        times_tri = [entry["time"] for entry in self.triangulation_dict.values()]
        XYZ_ini = np.array(self.triangulation_dict["0"]["XYZ"])
        triangles_ini = np.array(self.triangulation_dict["0"]["idx_triangles"])

        # Calculate axis limits
        min_val_x, max_val_x = np.min(XYZ_ini[:, 0]), np.max(XYZ_ini[:, 0])
        min_val_y, max_val_y = np.min(XYZ_ini[:, 1]), np.max(XYZ_ini[:, 1])
        min_val_z, max_val_z = np.min(XYZ_ini[:, 2]), np.max(XYZ_ini[:, 2])

        range_x = max_val_x - min_val_x
        range_y = max_val_y - min_val_y
        range_z = max_val_z - min_val_z
        max_range = max(range_x, range_y, range_z)

        # Create the figure and 3D axes
        fig = plt.figure(figsize=(8, 8))
        ax = fig.add_subplot(111, projection='3d')

        # Create the initial Poly3DCollection
        poly_collection = Poly3DCollection(XYZ_ini[triangles_ini], edgecolor='k', facecolor=(0.9, 0.7, 0.5), linewidth=0.2)
        ax.add_collection3d(poly_collection)

        # Set axis limits and labels
        ax.set_xlim([min_val_x, max_val_x])
        ax.set_ylim([min_val_y, max_val_y])
        ax.set_zlim([min_val_z, max_val_z])
        ax.set_xlabel('X [m]')
        ax.set_ylabel('Y [m]')
        ax.set_zlabel('Z [m]')
        ax.set_box_aspect([range_x / max_range, range_y / max_range, range_z / max_range])

        # --- Slider ---
        ax_slider = plt.axes([0.1, 0.05, 0.65, 0.03], facecolor='lightgoldenrodyellow')
        time_slider = Slider(ax_slider, _('Time'), 0, len(times_tri) - 1, valinit=0,
                             valstep=int(np.ceil(len(times_tri) / 200)))

        # Connect the slider to the update function
        time_slider.on_changed(update_triangulation_safe)

        # --- Animation ---
        anim_running = [False]
        current_frame = [0]
        last_update = [0]

        def toggle_animation(event):
            """
            Start or stop the animation.
            """
            anim_running[0] = not anim_running[0]
            anim_button.label.set_text(_("Stop") if anim_running[0] else _("Start"))
            if anim_running[0]:
                current_frame[0] = int(time_slider.val)
                timer.start()
            else:
                timer.stop()

        timer = fig.canvas.new_timer(interval=100)  # 100ms between frames

        def run_animation(event=None):
            """
            Run the animation by updating the slider value.
            """
            if anim_running[0]:
                if current_frame[0] < len(times_tri):
                    time_slider.set_val(current_frame[0])
                    current_frame[0] += 1
                else:
                    anim_running[0] = False
                    anim_button.label.set_text(_("Start"))
                    timer.stop()

        timer.add_callback(run_animation)

        ax_anim = plt.axes([0.8, 0.05, 0.1, 0.03])
        anim_button = Button(ax_anim, _('Start'))
        anim_button.on_clicked(toggle_animation)

        # --- Save Frame Button ---
        ax_save = plt.axes([0.78, 0.91, 0.15, 0.05])  # [left, bottom, width, height]
        btn_save = Button(ax_save, _('Save Frame'))

        def save_frame(event):
            """
            Save the current frame as a PNG file.
            """
            current_idx = int(time_slider.val)
            filename = f"{self.filename}_frame_{current_idx:03d}.png"
            fig.savefig(self.param_path.parent / filename, dpi=300)
            logging.info(_("Saved: %s") % filename)

        btn_save.on_clicked(save_frame)

        # --- Add Triangulation to tree Button ---
        ax_add = plt.axes([0.78, 0.84, 0.15, 0.05])  # [left, bottom, width, height]
        btn_add = Button(ax_add, _('Add current\nframe to viewer'))

        def add_tri(event):
            """
            Add current frame to viewer.
            """
            current_idx = int(time_slider.val)
            currenttri_dike = self.extract_triangulation(current_idx)
            if currenttri_dike is not None:
                self.mapviewer.add_object(newobj=currenttri_dike, which='triangulation', id=_("Triangulation_{filename}_{index:03d}").format(filename=self.filename, index=current_idx))
                logging.info(_("Added triangulation for time index %d to viewer.") % current_idx)

        btn_add.on_clicked(add_tri)

        plt.show()

    def extract_triangulation(self, time_idx:int) -> dict:
        """
        Extract the triangulation for a specific time index.
        :param time_idx: Time index to extract the triangulation.
        :return: Triangulation object.
        """
        if str(time_idx) in self.triangulation_dict:
            XYZ = np.array(self.triangulation_dict[str(time_idx)]["XYZ"])
            triangles = np.array(self.triangulation_dict[str(time_idx)]["idx_triangles"])
            return Triangulation(pts=XYZ, tri=triangles)
        else:
            logging.warning(_("No triangulation data available for the specified time index."))
            return None

    def plot_mainOutputs(self, output_type:int):

        fig = Matplotlib_Figure()
        fig.presets()
        ax = fig.ax[0]
        ax.set_xlabel(_('Time [s]'))
        if output_type == 0:
            fig.SetTitle(_('Discharges'))
            ax.set_ylabel(_('Discharges [m^3/s]'))
            fig.plot(x=self.mainOutputs_dict['Time [s]'], y=self.mainOutputs_dict['Qin [m^3/s]'], ax=0, label='Qin')
            fig.plot(x=self.mainOutputs_dict['Time [s]'], y=self.mainOutputs_dict['Qb [m^3/s]'], ax=0, label='Qb')
        elif output_type == 1:
            fig.SetTitle(_('Water levels and breach bottom elevation'))
            ax.set_ylabel(_('Water level/breach bottom [m]'))
            fig.plot(x=self.mainOutputs_dict['Time [s]'], y=self.mainOutputs_dict['z_b [m]'], ax=0, label='z_b')
            fig.plot(x=self.mainOutputs_dict['Time [s]'], y=self.mainOutputs_dict['z_s [m]'], ax=0, label='z_s')
            fig.plot(x=self.mainOutputs_dict['Time [s]'], y=self.mainOutputs_dict['z_t [m]'], ax=0, label='z_t')
        elif output_type == 2:
            fig.SetTitle(_('Breach widening'))
            ax.set_ylabel(_('Breach widening [m]'))
            Btop_DS = np.array(self.mainOutputs_dict['Btop_DS [m]'])
            Btop_US = np.array(self.mainOutputs_dict['Btop_US [m]'])
            Btop = Btop_DS - Btop_US
            fig.plot(x=self.mainOutputs_dict['Time [s]'], y=Btop_US, ax=0, label=_('U/S extremity'))
            fig.plot(x=self.mainOutputs_dict['Time [s]'], y=Btop_DS, ax=0, label=_('D/S extremity'))
            fig.plot(x=self.mainOutputs_dict['Time [s]'], y=Btop, ax=0, label=_('Breach top width'))

    def save(self):
        '''
        Save the parameters in a .json text file
        '''
        if self.filename is None:
            self.save_as()
        else:
            with open(self.filename, 'w') as f:
                json.dump(self.get_params(), f, indent=4)

    def save_as(self):
        '''
        Save the parameters in a .json text file
        '''
        filterArray = "json (*.json)|*.json|all (*.*)|*.*"
        fdlg = wx.FileDialog(None, _("Where should the parameters be stored (.json file)?"), wildcard=filterArray, style=wx.FD_SAVE)
        ret = fdlg.ShowModal()
        if ret == wx.ID_OK:
            self.filename = fdlg.GetPath()
            self.save()

        fdlg.Destroy()

    def get_params(self):
        '''
        Get the parameters of the dike model
        :return: dictionary containing the parameters
        '''
        return self._dike.get_params()

    def read_params(self, file_name:str, store_dir: Path = None):
        '''
        Read the model parameters and store them in a dictionary + updates attributes accordingly
        :param file_name: name of the file to read
        :param store_dir: directory where to read the file
        '''
        self._dike.read_params(file_name, store_dir)


class Wolf_Param_dike(Wolf_Param):
    def __init__(self, parent = None, title = _("Default Title"), w = 500, h = 800, ontop = False, to_read = True, filename = '', withbuttons = True, DestroyAtClosing = True, toShow = True, init_GUI = True, force_even_if_same_default = False, toolbar = True):
        super().__init__(parent, title, w, h, ontop, to_read, filename, withbuttons, DestroyAtClosing, toShow, init_GUI, force_even_if_same_default, toolbar)

    def _set_gui_dike(self,
                parent:wx.Window = None,
                title:str = _("Default Title"),
                w:int = 500,
                h:int = 800,
                ontop:bool = False,
                to_read:bool = True,
                withbuttons:bool = True,
                DestroyAtClosing:bool = False,
                toShow:bool = True,
                full_style = False,
                toolbar:bool = True):
        """
        Set the GUI if wxPython is running. This function is specifically dedicated to the creation of a dike object.

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
            logging.error(_("wxPython is not running - Impossible to set the GUI"))
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
            self.saveme = wx.Button(self,id=10,label=_("Save to file"))
            self.loadme = wx.Button(self,id=10,label=_("Load from file"))
            self.applychange = wx.Button(self,id=10,label=_("Apply change"))
            self.reloadme = wx.Button(self,id=10,label=_("Reload"))

            #liaison des actions des boutons
            self.saveme.Bind(wx.EVT_BUTTON,self.SavetoFile)
            self.loadme.Bind(wx.EVT_BUTTON,self.LoadFromFile_json) # To open a .json file
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

    def LoadFromFile_json(self, event:wx.MouseEvent):
        """ Load parameters from file """

        temp_dict_active = self.myparams.copy() # Save the current parameters in a temporary dictionary
        temp_dict_default = self.myparams_default.copy() # Save the current parameters in a temporary dictionary

        # read the file
        if self.wx_exists:
            #ouverture d'une boîte de dialogue
            file=wx.FileDialog(self,_("Choose .json file"), wildcard="Parameter files (*_paramsDike.json)|*_paramsDike.json")
            if file.ShowModal() == wx.ID_CANCEL:
                return
            else:
                self.Clear() # Clear the parameters before loading new ones
                #récuparétaion du nom de fichier avec chemin d'accès
                self.filename =file.GetPath()
        else:
            logging.warning(_("ERROR : no filename given and wxPython is not running"))
            return

        if not os.path.isfile(self.filename):
            logging.warning(_("ERROR : cannot find the following file : {}".format(self.filename)))
            return

        with open(self.filename, 'r') as f:
            myparams_update = json.load(f)

        myparams_update = (self.update_param_window(params_dict=myparams_update, whichdict='Active')).myparams
        self.myparams = self.merge_dicts(dict_new=myparams_update, dict_ref=temp_dict_active)
        self.myparams_default = temp_dict_default.copy() # Restore the default parameters

        if self._callback is not None:
                self._callback()

        # populate the property grid
        self.Populate()

    def update_param_window(self,params_dict,whichdict) -> Wolf_Param:
        """ Transforms a params_dict into a Wolf_Param object to fill the 'whichdict' page of the parameters window.
         :param params_dict: dictionary containing the parameters
         :param whichdict: dictionary to fill (default or active)"""

        wp = Wolf_Param_dike(parent=None, # Contains all the parameters of the window
                            to_read=False,
                            withbuttons=True,
                            toShow=False,
                            init_GUI=False,
                            force_even_if_same_default = False,
                            filename=join("default_name.json"))

        for current_section in params_dict.keys():
            for key in params_dict[current_section].keys():

                value = params_dict[current_section][key]["value"]
                description = params_dict[current_section][key]["description"]
                name = params_dict[current_section][key]["explicit name"]
                # Parameter type
                if params_dict[current_section][key]["type"] == "Float":
                    type_param = Type_Param.Float
                elif params_dict[current_section][key]["type"] == "Integer":
                    type_param = Type_Param.Integer
                elif params_dict[current_section][key]["type"] == "Logical":
                    type_param = Type_Param.Logical
                elif params_dict[current_section][key]["type"] == "String":
                    type_param = Type_Param.String
                elif params_dict[current_section][key]["type"] == "Directory":
                    type_param = Type_Param.Directory
                elif params_dict[current_section][key]["type"] == "File":
                    type_param = Type_Param.File

                if params_dict[current_section][key]["choices"] != None:
                    wp.add_param((current_section), (name), value, type_param, whichdict=whichdict, jsonstr=new_json(params_dict[current_section][key]["choices"]), comment=_(description))
                else:
                    wp.add_param((current_section), (name), value, type_param, whichdict=whichdict, comment=_(description))

        return wp

    def merge_dicts(self, dict_new=None, dict_ref=None):
        """
        Merge values of dict_new into dict_ref.
        """
        if dict_new is None:
            dict_new = self.myparams
        if dict_ref is None:
            dict_ref = self.myparams_default

        for section, params in dict_new.items():
            if section not in dict_ref:
                dict_ref[section] = {}
            for key, value in params.items():
                if key in dict_ref[section]:
                    dict_ref[section][key].update(value)
                else:
                    dict_ref[section][key] = value
        return dict_ref