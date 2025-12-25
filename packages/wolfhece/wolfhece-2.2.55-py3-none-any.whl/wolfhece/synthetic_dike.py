"""
Author: HECE - University of Liege, Pierre Archambeau
Date: 2024

Copyright (c) 2024 University of Liege. All rights reserved.

This script and its content are protected by copyright law. Unauthorized
copying or distribution of this file, via any medium, is strictly prohibited.
"""

import logging

import numpy as np
from shapely.geometry import Point, LineString

from.drawing_obj import Element_To_Draw
from .PyVertexvectors import Triangulation, vector,Zones, zone
from .wolf_array import WolfArray, header_wolf

class SyntheticDike(Element_To_Draw):
    """ Dike class for synthetic dikes based on a trace vector, width of the crest and lateral slopes.
    """

    def __init__(self, idx:str = '', plotted:bool = True, mapviewer = None, need_for_wx:bool = False):

        super().__init__(idx, plotted, mapviewer, need_for_wx)

        self._triangulation = None
        self._zones = Zones()
        newzone = zone(name='dike')

        self._zones.add_zone(newzone, forceparent=True)

    @property
    def triangulation(self) -> Triangulation:
        """ Return the triangulation of the dike """
        return self._triangulation

    @property
    def zones(self) -> Zones:
        """ Return the zones of the dike """
        return self._zones

    def create_from_slopes(self, trace:vector,
                             slope_up:float, slope_down:float,
                             width_up:float, width_down:float,
                             zmin:float, zmax:float, ds:float):

        """ Create the dike triangulation based on the trace vector and the width of the dike.

        :param trace: Trace vector of the dike
        :param slope_up: Slope of the dike on the upstream side [slope = dz/dx]
        :param slope_down: Slope of the dike on the downstream side [slope = dz/dx]
        :param width_up: Width of the dike on the upstream side [m]
        :param width_down: Width of the dike on the downstream side [m]
        :param zmin: Minimum elevation of the dike [m]
        :param zmax: Maximum elevation of the dike [m]
        :param ds: Distance for rebinning [m]
        """

        assert ds > 0.0, "Distance for rebinning must be positive"
        assert slope_up > 0.0, "Slope must be positive"
        assert slope_down > 0.0, "Slope must be positive"
        assert width_up >= 0.0, "Width must be positive"
        assert width_down >= 0.0, "Width must be positive"
        assert zmin < zmax, "zmin must be less than zmax"

        myzone = self._zones.myzones[0]
        myzone.myvectors = []

        # Impose altimetry of the crest
        trace.z = zmax

        # add the trace vector to the zone
        myzone.add_vector(trace, forceparent=True)

        # CREST of the dike
        # create parallel vectors to the trace vector - right and left

        if width_up > 0.0:
            distances_up = list(np.linspace(0, width_up, int(width_up/ds)+1, endpoint=True))[1:]
            for curds in distances_up:
                # create a new vector parallel to the trace vector
                parup = trace.parallel_offset(curds, 'right')
                myzone.add_vector(parup, 0, forceparent=True)
                # impose altimetry of the dike
                parup.z = zmax
        else:
            # no width on the upstream side -> use the trace vector
            parup = trace

        if width_down > 0.0:
            distances_down = list(np.linspace(0, width_down, int(width_down/ds)+1, endpoint=True))[1:]
            for curds in distances_down:
                pardown = trace.parallel_offset(curds, 'left')
                myzone.add_vector(pardown, forceparent=True)
                # impose altimetry of the dike
                pardown.z = zmax
        else:
            # no width on the downstream side -> use the trace vector
            pardown = trace

        # distances to the crest
        distances_up   = (zmax-zmin) / slope_up
        distances_up = list(np.linspace(0, distances_up, int(distances_up/ds)+1, endpoint=True))[1:]
        # distances_up.reverse()
        # iterate over the distup basd on ds
        for curds in distances_up:
            # create a new vector parallel to the trace vector
            parup_new = parup.parallel_offset(curds, 'right')
            myzone.add_vector(parup_new, 0, forceparent=True)
            # impose altimetry of the dike
            parup_new.z = zmax - slope_up * curds

        distances_down = (zmax-zmin) / slope_down
        distances_down = list(np.linspace(0, distances_down, int(distances_down/ds)+1, endpoint=True))[1:]
        for curds in distances_down:
            pardown_new  = pardown.parallel_offset(curds, 'left')
            myzone.add_vector(pardown_new, forceparent=True) # append
            # impose altimetry of the dike
            pardown_new.z = zmax - slope_down * curds

        # on dispose de multiples vecteurs dans la zone, orientés de l'amont vers l'aval
        trace.update_lengths()

        nb_along_trace  = int(trace.length3D / ds) # nombre de points sur la trace

        self._triangulation = myzone.create_multibin(nb_along_trace)

    def create_from_shape(self, trace:vector, shape:vector, ds:float):
        """ create the dike triangulation based on the trace vector and the shape vector

        :param trace: Trace vector of the dike
        :param shape: Transversal shape of the dike in (s,z) coordinates, s=0.0 is on the trace vector, elevations are relative to the trace vector
        :param ds: Distance for rebinning [m]
        """

        myzone = self._zones.myzones[0]
        myzone.myvectors = []

        # add the trace vector to the zone
        myzone.add_vector(trace, forceparent=True)

        # get the shapely linestring of the trace -> projection
        ref_ls = trace.linestring

        # Create parallels of the crest according to the shape vector
        # -----------------------------------------------------------

        # get coordinates of the shape vector
        shape_vertices = shape.xy

        # Separate the upstream and downstream vertices
        up_vertices = shape_vertices[shape_vertices[:, 0] > 0.0]
        down_vertices = shape_vertices[shape_vertices[:, 0] < 0.0]

        # reverse the order of downstream vertices
        down_vertices = down_vertices[::-1]

        # Altitude au droit de la trace
        z_shape_trace = shape_vertices[shape_vertices[:, 0] == 0.0][0][1]

        # UPSTREAM PART

        # Loop over the upstream vertices
        z_previous = z_shape_trace
        s_previous = 0.0
        distance_cum = 0.0 # useful for the cumulated distance -> parallel offset
        for cur_sz in up_vertices:

            ds_loc    = cur_sz[0] - s_previous       # distance between the two points in the shape
            slope_loc = (z_previous - cur_sz[1]) / ds_loc  # local slope of the shape

            # rebin the distance
            distances_up = list(np.linspace(0, ds_loc, int(ds_loc/ds)+1, endpoint=True))[1:]

            deltaz_cum = 0.0 # Cumulated elevation difference

            # iterate over the distup basd on ds
            for curds in distances_up:
                # create a new vector parallel to the trace vector
                # need to add the cumulated distance to the current distance as we
                parup = trace.parallel_offset(curds + distance_cum, 'right')

                if parup is None:
                    logging.warning("No parallel vector found for distance %f", curds + distance_cum)
                    continue

                myzone.add_vector(parup, 0, forceparent=True)

                # local delta elevation
                deltaz_loc = -slope_loc * curds - deltaz_cum # local difference

                parup_z = []

                # we need to interpolate the elevation according to the trace

                # Iterate over the vertices
                for vert in parup.myvertices:
                    # project the vertex on the previous trace
                    proj = ref_ls.project(Point(vert.x, vert.y), normalized=True)
                    # get the elevation of the trace at the projection point
                    z_loc = ref_ls.interpolate(proj, normalized= True).z
                    # add the local delta elevation
                    z_loc += deltaz_loc
                    parup_z.append(z_loc)

                parup.z = parup_z
                ref_ls = parup.linestring
                deltaz_cum += deltaz_loc
                z_previous = cur_sz[1]
                s_previous = cur_sz[0] # update the elevation of the trace

            distance_cum += distances_up[-1] # cumulate the distance

        # create downstream
        ref_ls = trace.linestring

        z_previous = z_shape_trace
        s_previous = 0.0
        distance_cum = 0.0
        # Loop over the downstream vertices
        for cur_sz in down_vertices:

            ds_loc    = -(cur_sz[0] - s_previous)
            slope_loc = (z_previous - cur_sz[1]) / ds_loc

            # rebin the distance
            distances_down = list(np.linspace(0, ds_loc, int(ds_loc/ds)+1, endpoint=True))[1:]

            deltaz_cum = 0.0

            # iterate over the distup basd on ds
            for curds in distances_down:
                pardown = trace.parallel_offset(curds + distance_cum, 'left')

                if pardown is None:
                    logging.warning("No parallel vector found for distance %f", curds + distance_cum)
                    continue

                myzone.add_vector(pardown, forceparent=True)

                # impose local elevation
                deltaz_loc = -slope_loc * curds - deltaz_cum # local difference

                pardown_z = []
                # we need to interpolate the elevation according to the trace
                for vert in pardown.myvertices:
                    # project the vertex on the trace
                    proj = ref_ls.project(Point(vert.x, vert.y), normalized=True)
                    # get the elevation of the trace at the projection point
                    z_loc = ref_ls.interpolate(proj, normalized= True).z
                    # add the local delta elevation
                    z_loc += deltaz_loc
                    pardown_z.append(z_loc)

                # impose the elevation
                pardown.z = pardown_z
                ref_ls = pardown.linestring
                deltaz_cum += deltaz_loc
                z_previous =cur_sz[1] # update the elevation of the trace
                s_previous = cur_sz[0]

            distance_cum += distances_down[-1]

        # on dispose de multiples vecteurs dans la zone, orientés de l'amont vers l'aval
        trace.update_lengths()

        nb_along_trace  = int(trace.length3D / ds) # nombre de points sur la trace

        self._triangulation = myzone.create_multibin(nb_along_trace)

        for curvect in myzone.myvectors:
            curvect.reset_linestring()


