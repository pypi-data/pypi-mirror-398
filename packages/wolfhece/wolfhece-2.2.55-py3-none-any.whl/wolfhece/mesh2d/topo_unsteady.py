"""
Author: HECE - University of Liege, Pierre Archambeau
Date: 2024

Copyright (c) 2024 University of Liege. All rights reserved.

This script and its content are protected by copyright law. Unauthorized
copying or distribution of this file, via any medium, is strictly prohibited.
"""

from pathlib import Path
import logging
import numpy as np
from tqdm import tqdm

from ..wolf_array import header_wolf, WolfArray

class UnsteadyTopoBathymetry():
    """ Manage unsteady topo/bathymetry data for WOLF2D meshes and dike breach.

    Position is in ".topipar" file.
    Array data is in ".topi" file.
    """

    def __init__(self, filename_wo_extension: str | Path, dx_dy : tuple[float, float]):

        self._genfile = Path(filename_wo_extension)
        self._topiparfile = self._genfile.with_suffix('.topipar')
        self._topifile = self._genfile.with_suffix('.topi')
        self._dx, self._dy = dx_dy

        self._arrays_ref: list[WolfArray]
        self._arrays_ref = []
        self._unsteady_arrays = {}

        if not self._topiparfile.exists() or not self._topifile.exists():
            logging.error(f"Unsteady topo/bathymetry files not found: {self._topiparfile}, {self._topifile}")
            return

    def _read_topipar(self) -> dict:
        """ Read the .topipar file and return parameters as a dictionary.
        """
        params = {}
        with open(self._topiparfile, 'r') as f:
            lines = f.readlines()

        nb = int(lines[0].strip())
        idx = 1
        for i in range(1, nb + 1):
            ox, oy = map(float, lines[idx].strip().split(" "))
            nbx, nby = map(int, lines[idx + 1].strip().split(" "))
            idx+=2

            hdr = header_wolf.make((ox, oy), (nbx, nby), (self._dx, self._dy))
            self._arrays_ref.append(WolfArray(srcheader= hdr))

        return params

    def _read_topi(self):
        """ Read the .topi file and populate unsteady arrays.
        """
        with open(self._topifile, 'r') as f:
            lines = f.readlines()

            idx = 0
            while idx < len(lines):
                if lines[idx].strip() == '':
                    idx += 1
                    continue
                time = float(lines[idx].strip())
                for i, array_ref in enumerate(self._arrays_ref):
                    array_data = WolfArray(srcheader= array_ref.get_header())
                    _data = np.loadtxt(lines[idx + 1: idx + 1 + array_ref.get_header().nby], dtype=float)
                    array_data.array.data[:,:] = _data.T
                    array_data.array.mask[:,:] = _data.T == 1.0
                    self._unsteady_arrays[time] = array_data
                    idx += 1 + array_ref.get_header().nby

    def read_all(self):
        """ Read all unsteady topo/bathymetry data from files.
        """
        self._read_topipar()
        self._read_topi()

    def find_first_time_with_difference(self, reference_array: WolfArray) -> float | None:
        """ Find the first time where the unsteady topo/bathymetry differs from the reference array.
        """
        for time in sorted(self._unsteady_arrays.keys()):
            array = self._unsteady_arrays[time]
            if not np.array_equal(array.array.data, reference_array.array.data):
                return time
        return None

    def find_first_time_with_difference_greater_than(self, reference_array: WolfArray, threshold: float) -> float | None:
        """ Find the first time where the unsteady topo/bathymetry differs from the reference array by more than a threshold.
        """
        for time in sorted(self._unsteady_arrays.keys()):
            array = self._unsteady_arrays[time]
            difference = np.abs(array.array.data - reference_array.array.data)
            if np.any(difference > threshold):
                return time
        return None

    def find_last_time_with_difference(self, reference_array: WolfArray) -> float | None:
        """ Find the last time where the unsteady topo/bathymetry differs from the reference array.
        """
        for time in sorted(self._unsteady_arrays.keys(), reverse=True):
            array = self._unsteady_arrays[time]
            if not np.array_equal(array.array.data, reference_array.array.data):
                return time
        return None

    def get_times(self) -> list[float]:
        """ Get the list of available times for unsteady topo/bathymetry data.
        """
        return list(self._unsteady_arrays.keys())

    def get_array_at_time(self, time: float) -> WolfArray | None:
        """ Get the topo/bathymetry array at a specific time.
        """
        return self._unsteady_arrays.get(time, None)

    def get_array_at_nearest_time(self, time: float) -> WolfArray | None:
        """ Get the topo/bathymetry array at the nearest available time.
        """
        if not self._unsteady_arrays:
            return None
        available_times = np.array(list(self._unsteady_arrays.keys()))
        nearest_time = available_times[np.abs(available_times - time).argmin()]
        return self._unsteady_arrays[nearest_time]

    def find_nearest_time(self, time: float) -> float | None:
        """ Find the nearest available time for unsteady topo/bathymetry data.
        """
        if not self._unsteady_arrays:
            return None
        available_times = np.array(list(self._unsteady_arrays.keys()))
        nearest_time = available_times[np.abs(available_times - time).argmin()]
        return nearest_time

    def find_nearest_time_index(self, time: float) -> int | None:
        """ Find the index of the nearest available time for unsteady topo/bathymetry data.
        """
        if not self._unsteady_arrays:
            return None
        available_times = np.array(list(self._unsteady_arrays.keys()))
        nearest_index = np.abs(available_times - time).argmin()
        return nearest_index
