"""
Author: HECE - University of Liege, Pierre Archambeau
Date: 2024

Copyright (c) 2024 University of Liege. All rights reserved.

This script and its content are protected by copyright law. Unauthorized
copying or distribution of this file, via any medium, is strictly prohibited.
"""

import numpy as np
from typing import Literal, Union
import wx
import logging
from pathlib import Path
import glob
import asyncio
from os.path import getsize

logging.info('Importing wolfhece modules')
from ..PyTranslate import _
from .particle_system import Particle_system
from .emitter import Emitter
from .velocity_field import Velocity_Field
from ..drawing_obj import Element_To_Draw
from ..PyParams import Wolf_Param, key_Param, Type_Param
from ..wolf_array import WolfArray, WOLF_ARRAY_FULL_SINGLE, WOLF_ARRAY_FULL_INTEGER, header_wolf
from ..PyVertexvectors import Zones,zone,vector, wolfvertex
logging.info('wolfhece modules imported')
class Particle_system_to_draw(Element_To_Draw):

    def __init__(self, idx: str = '', plotted: bool = True, mapviewer=None, need_for_wx: bool = False) -> None:

        super().__init__(idx, plotted, mapviewer, need_for_wx)

        self._ps = Particle_system()
        self._trace_size = 10

        self.fps = 60.
        self.single_color = True
        self.peremitter_color = True

        self._unique_color = (0., 0., 0., 1.)
        self._nb_colors_edited = 0

        self._canbake = False

        self._ui = None

    def reset(self) -> None:
        """
        Reset the object.
        """
        self._ps.reset()

    def show_properties(self) -> None:
        """
        Show the properties of the object.
        """
        if self._ui is None:
            self._ui = Wolf_Param(None, self.idx, to_read=False, DestroyAtClosing=True)
            self._ui.show_in_active_if_default = True
            self._ui.set_callbacks(self.update_properties, self.update_properties_destroy)
            self._ui.hide_selected_buttons()
            self._ui.SetSize((600,500))

        self._fill_default()
        self._fill_properties()
        self._ui.Show()

    def _fill_default(self) -> None:
        """
        Fill the default properties of the object.
        """
        if self._ui is None:
            logging.warning('No UI to fill')
            return

        self._ui.Clear()

        self._ui.addparam(_('General'), _('Trace size'), 10,
                          Type_Param.Integer, _('Number of steps to plot'), whichdict='Default')
        self._ui.addparam(_('General'), _('Blending trace'), True,
                          Type_Param.Logical, _('Blending trace or not'), whichdict='Default')
        self._ui.addparam(_('General'), _('FPS'), 40,
                          Type_Param.Integer, _('Number of frames per second\n\nModification will be applied when it is run again or after a pause/resume'), whichdict='Default')
        self._ui.addparam(_('General'), _('Using single color'), True,
                          Type_Param.Logical, _('If True, the same color will be used for all frames'), whichdict='Default')
        self._ui.addparam(_('General'), _('Unique color'), [0, 0, 0, 255],
                          Type_Param.Color, _('Color for all particles'), whichdict='Default')

        self._ui.addparam(_('General'), _('Nb emitters'), 0,
                          Type_Param.Integer, _('Number of emitters'), whichdict='Default')

        self._ui.addparam(_('General'), _('Nb velocity fields'), 0,
                          Type_Param.Integer, _('Number of velocity fields'), whichdict='Default')

        # self._ui.add_group(_('Velocity Fields'), self._ui.myparams_default)

        self._ui.addparam(_('Velocity fields'), _('Starting time $n({}, {},0,99999)$'.format(_('General'), _('Nb velocity fields'))), 0.,
                          Type_Param.Float, _('Starting time for velocity field'), whichdict='Default')

        self._ui.add_IncGroup(_('Emitter $n$'), 0, 255, _('General'), _('Nb emitters'))

        self._ui.addparam(_('General'), _('Per emitter color'), False,
                            Type_Param.Logical, _('Colorize particles per emitter -- ONLY used if "Unique color" is False'), whichdict='Default')

        self._ui.addparam(_('Computation'), _('Total time [s]'), 3600.,
                          Type_Param.Float, _('Total time of computation'), whichdict='Default')
        self._ui.addparam(_('Computation'), _('Time step [s]'), 1.,
                          Type_Param.Float, _('Fixed time step [s] -- Except for RK45'), whichdict='Default')

        self._ui.addparam(_('Computation'), _('Scheme'), 1,
                          Type_Param.Integer, _('Scheme to use for computation'),
                          whichdict='Default', jsonstr={"Values":{_("Euler explicit"):0,
                                                              "RK22":1,
                                                              "RK4":2,
                                                              "RK45":3},
                                                    "Full_Comment":_('Make a choice betwwen the proposed schemes\n 1st order: Euler explicit\n 2nd order: RK22\n 4th order: RK4\n 5th order: RK45')})

        self._ui.addparam(_('Emitter $n$'), _('Active'), True,
                          Type_Param.Logical, _('If True, the emitter is active'), whichdict='IncGroup')
        self._ui.addparam(_('Emitter $n$'), _('How many'), 10,
                          Type_Param.Integer, _('Total number of particles for this emitters.\nIf the emitter is made up of several cells and the number of particles is less than the numer of cells, some cells will not emit.'), whichdict='IncGroup')
        self._ui.addparam(_('Emitter $n$'), _('Every seconds'), 1.,
                            Type_Param.Float, _('Emit "How many" particles every seconds - starting at 0.0 [s]'), whichdict='IncGroup')
        self._ui.addparam(_('Emitter $n$'), _('Area\'s color'), [0,0,0,255],
                            Type_Param.Color, _('Color of the area'), whichdict='IncGroup')
        self._ui.addparam(_('Emitter $n$'), _('Particles\'s color'), [0,0,0,255],
                            Type_Param.Color, _('Color of the particles'), whichdict='IncGroup')
        self._ui.addparam(_('Emitter $n$'), _('Nb clock times'), 0,
                          Type_Param.Integer, _('Number of clock times'), whichdict='IncGroup')

        self._ui.add_IncParam(_('Emitter $n$'), _('Clock interval $n$'), '', _('Interval in which the emitter is active'),
                              Type_Param.String, 0, 255, _('Nb clock times'))

    def _fill_properties(self) -> None:
        """
        Fill the properties of the object.
        """
        if self._ui is None:
            logging.warning('No UI to fill')
            return

        self._ui.update_incr_at_every_change = False

        self._ui.addparam(_('General'), _('Trace size'), self.trace_size,
                          Type_Param.Integer, _('Number of steps to plot'), whichdict='Active')
        self._ui.addparam(_('General'), _('Blending trace'), self.blend,
                          Type_Param.Logical, _('Blending trace or not'), whichdict='Active')
        self._ui.addparam(_('General'), _('FPS'), self.fps,
                          Type_Param.Integer, _('Number of frames per second\n\nModification will be applied when it is run again or after a pause/resume'), whichdict='Active')
        self._ui.addparam(_('General'), _('Using single color'), self.single_color,
                          Type_Param.Logical, _('If True, the same color will be used for all frames'), whichdict='Active')

        if self.single_color:
            self._ui.addparam(_('General'), _('Unique color'), [int(cur*255) for cur in self._unique_color],
                            Type_Param.Color, _('Color for all particles'), whichdict='Active')

        self._ui.addparam(_('General'), _('Nb emitters'), self._ps.number_of_emitters,
                          Type_Param.Integer, _('Number of emitters'), whichdict='Active')

        if not self.single_color:
            self._ui.addparam(_('General'), _('Per emitter color'), self.peremitter_color,
                              Type_Param.Logical, _('Colorize particles per emitter -- ONLY used if "Unique color" is False'), whichdict='Active')

        self._ui.addparam(_('Computation'), _('Total time [s]'), self.totaltime,
                          Type_Param.Float, _('Total time of computation'), whichdict='Active')
        self._ui.addparam(_('Computation'), _('Time step [s]'), self.dt,
                          Type_Param.Float, _('Fixed time step [s] -- Except for RK45'), whichdict='Active')

        self._ui.addparam(_('Computation'), _('Scheme'), self.scheme,
                          Type_Param.Integer, _('Scheme to use for computation'),
                          whichdict='Active', jsonstr={"Values":{_("Euler explicit"):0,
                                                              "RK22":1,
                                                              "RK4":2,
                                                              "RK45":3},
                                                    "Full_Comment":_('Make a choice betwwen the proposed schemes\n 1st order: Euler explicit\n 2nd order: RK22\n 4th order: RK4\n 5th order: RK45')})

        # self._ui[(_('General'), _('Nb emitters'))] = self._ps.number_of_emitters

        # Update the UI for incremental groups and params
        self._ui.update_incremental_groups_params(True, False)

        # Emitters properties
        for i in range(self._ps.number_of_emitters):
            curemitter = self._ps._emitters[i]
            groupname = _('Emitter {}').format(i+1)
            self._ui[(groupname, _('Active'))] = curemitter.active
            self._ui[(groupname, _('How many'))] = curemitter.how_many
            self._ui[(groupname,_('Every seconds'))] = curemitter.every_seconds
            self._ui[(groupname, _('Area\'s color'))] = [int(cur*255) for cur in curemitter.color_area]
            if self.single_color or not self.peremitter_color:
                self._ui.myparams[groupname].pop(_('Particles\'s color'))
            elif self.peremitter_color:
                if not self._ui.is_in_active(groupname, _('Particles\'s color')):
                    self._ui.addparam(groupname, _('Particles\'s color'), [int(cur*255) for cur in curemitter.color_particles],
                                      Type_Param.Color, _('Color of the particles'), whichdict='Active')

            clocktimes = curemitter.clock.to_str()
            self._ui[(groupname, _('Nb clock times'))] = len(clocktimes)

            # Update the UI for incremental groups and params
            self._ui.update_incremental_groups_params(False, True)

            for idx, curtimestr in enumerate(clocktimes):
                self._ui[(groupname, _('Clock interval {}'.format(idx+1)))] = curtimestr

        if not self.single_color and not self.peremitter_color:
            listcolors = self.colors
            self._nb_colors_edited = len(listcolors)
            for curcol in listcolors:

                step, key, color = curcol
                self._ui.addparam(_('Colors'), _('Color particles {}-{}'.format(step, key)), [int(cur*255) for cur in color], 'Color', 'Color for time {} s - and emitter {}'.format(step, key), whichdict='Active')

        times = self.get_times_vf()
        self._ui[(_('General'), _('Nb velocity fields'))] = len(times)
        # Update the UI for incremental groups and params
        self._ui.update_incremental_groups_params(False, True)

        groupname = _('Velocity fields')
        self._ps.sort_vf()
        times = self._ps.times_vf
        for i in range(len(times)):
            self._ui[(groupname, _('Starting time {}'.format(i+1)))] = times[i]

        self._ui.Populate()

    def update_properties(self) -> None:
        """
        Update the properties of the object.
        """

        if self._ui is None:
            logging.warning('No UI to update')
            return

        self._ui.update_incr_at_every_change = False

        self._trace_size = self._ui[(_('General'), _('Trace size'))]
        self.blend = self._ui[_('General'), _('Blending trace')]
        self.fps = self._ui[_('General'), _('FPS')]
        self._unique_color = tuple([float(cur)/255. for cur in self._ui[_('General'), _('Unique color')]])

        for i in range(self._ps.number_of_emitters):
            curemitter = self._ps._emitters[i]
            groupname = _('Emitter {}').format(i+1)
            curemitter.active = self._ui[groupname, _('Active')]
            curemitter.how_many = self._ui[groupname, _('How many')]
            curemitter.every_seconds = self._ui[groupname, _('Every seconds')]
            curemitter.color_area = tuple([float(cur)/255. for cur in self._ui[groupname, _('Area\'s color')]])
            if not self.single_color and self.peremitter_color:
                curemitter.color_particles = tuple([float(cur)/255. for cur in self._ui[groupname, _('Particles\'s color')]])

            timesclock = []
            for idx in range(self._ui[groupname, _('Nb clock times')]):
                timesclock.append(self._ui[(groupname, _('Clock interval {}'.format(idx+1)))])

            curemitter.clock.from_str(timesclock)

        if self.single_color:
            # only one color for all particles for all emitters and all steps
            listcolors = self.colors
            self.colors = [ (step, key, self._unique_color) for step, key, _ in listcolors]

        elif self.peremitter_color:
            # one color per emitter for all steps
            listcolors = self.colors
            emit_colors = [curemitter.color_particles for curemitter in self._ps._emitters]
            self.colors = [ (step, key, emit_colors[key]) for step, key, _ in listcolors]
        else:
            listcolors = self.colors[:self._nb_colors_edited]
            newcolors=[]
            for curcol in listcolors:

                step, key, color = curcol
                loccol = tuple([float(cur)/255. for cur in self._ui[_('Colors'), _('Color particles {}-{}'.format(step, key))]])
                newcolors.append((step, key, loccol))

            self.colors = newcolors

        old_single_color = self.single_color
        self.single_color = self._ui[_('General'), _('Using single color')]
        self._unique_color = self._ui[_('General'), _('Unique color')]

        old_peremitter = self.peremitter_color
        if not old_single_color:
            self.peremitter_color = self._ui[_('General'), _('Per emitter color')]

        if (old_single_color != self.single_color) or (old_peremitter != self.peremitter_color):
            self._fill_properties()

        self.dt = self._ui[_('Computation'), _('Time step [s]')]
        self.totaltime = self._ui[_('Computation'), _('Total time [s]')]
        self.scheme = self._ui[_('Computation'), _('Scheme')]

        times = [self._ui[_('Velocity fields'), _('Starting time {}'.format(i+1))] for i in range(self._ps.number_of_vf)]
        self.set_times_vf(times)

    def update_properties_destroy(self) -> None:
        """
        Update the properties of the object.
        """
        self._ui = None

    @property
    def totaltime(self) -> float:
        """
        Return the total time.
        """
        return self._ps.totaltime

    @totaltime.setter
    def totaltime(self, value:float) -> None:
        """
        Set the total time.
        """
        self._ps.totaltime = value

    @property
    def dt(self) -> float:
        """
        Return the time step.
        """
        return self._ps.dt

    @dt.setter
    def dt(self, value:float) -> None:
        """
        Set the time step.
        """
        self._ps.dt = value

    @property
    def scheme(self) -> int:
        """
        Return the scheme.
        """
        scheme = self._ps.scheme

        if scheme == 'Euler_expl':
            return 0
        elif scheme == 'RK22':
            return 1
        elif scheme == 'RK4':
            return 2
        elif scheme == 'RK45':
            return 3
        else:
            return 1

    @scheme.setter
    def scheme(self, value:int) -> None:
        """
        Set the scheme.
        """
        if value in ['0',0]:
            self._ps.scheme = 'Euler_expl'
        elif value in ['1',1]:
            self._ps.scheme = 'RK22'
        elif value in ['2',2]:
            self._ps.scheme = 'RK4'
        elif value == ['3',3]:
            self._ps.scheme = 'RK45'
        else:
            self._ps.scheme = ''


    def get_domain(self, output_type:Literal['numpy', 'wolf'] = 'wolf') -> Union[np.ndarray, WolfArray]:
        """
        Return the domain as Numpy array or WolfArray to put in the UI.
        """
        if not isinstance(output_type, str):
            output_type = str(output_type)

        if output_type.lower() == 'numpy':
            return self._ps.domain
        elif output_type.lower() == 'wolf':
            ox,oy,dx,dy,nbx,nby = self._ps.get_header()
            locheader = header_wolf()
            locheader.origx, locheader.origy, locheader.dx, locheader.dy, locheader.nbx, locheader.nby = ox,oy,dx,dy,nbx,nby
            wolf = WolfArray(whichtype=WOLF_ARRAY_FULL_INTEGER, srcheader=locheader, idx = self.idx+'_domain')
            wolf.array = np.ma.asarray(self._ps.domain.astype(np.int32))
            wolf.mask_data(wolf.nullvalue)

            return wolf
        else:
            return None

    def set_domain(self, value:Union[np.ndarray, WolfArray]) -> None:
        """
        Set the domain.
        """
        if isinstance(value, WolfArray):
            self._ps.domain = ~value.array.mask
            self._ps.nbx, self._ps.nby = value.array.shape
            self._ps.dx, self._ps.dy = value.dx, value.dy
        else:
            assert value.dtype == np.bool, 'Domain must be boolean'
            self._ps.domain = value
            self._ps.nbx, self._ps.nby = value.shape

    def get_u(self, output_type:Literal['numpy', 'wolf'] = 'wolf') -> Union[np.ndarray, WolfArray]:
        """
        Return the u as Numpy array or WolfArray to put in the UI.
        """
        if not isinstance(output_type, str):
            output_type = str(output_type)

        if output_type.lower() == 'numpy':
            return self._ps._velocity_fields[0].u
        elif output_type.lower() == 'wolf':
            ox,oy,dx,dy,nbx,nby = self._ps.get_header()
            locheader = header_wolf()
            locheader.origx, locheader.origy, locheader.dx, locheader.dy, locheader.nbx, locheader.nby = ox,oy,dx,dy,nbx,nby
            wolf = WolfArray(whichtype=WOLF_ARRAY_FULL_SINGLE, srcheader=locheader, idx = self.idx+'_u')
            wolf.array = np.ma.asarray(self._ps.u.astype(np.float32))
            wolf.mask_data(wolf.nullvalue)
            return wolf
        else:
            return None

    def get_v(self, output_type:Literal['numpy', 'wolf'] = 'wolf') -> Union[np.ndarray, WolfArray]:
        """
        Return the v as Numpy array or WolfArray to put in the UI.
        """
        if not isinstance(output_type, str):
            output_type = str(output_type)

        if output_type.lower() == 'numpy':
            return self._ps._velocity_fields[0].v
        elif output_type.lower() == 'wolf':
            ox,oy,dx,dy,nbx,nby = self._ps.get_header()
            locheader = header_wolf()
            locheader.origx, locheader.origy, locheader.dx, locheader.dy, locheader.nbx, locheader.nby = ox,oy,dx,dy,nbx,nby
            wolf = WolfArray(whichtype=WOLF_ARRAY_FULL_SINGLE, srcheader=locheader, idx = self.idx+'_v')
            wolf.array = np.ma.asarray(self._ps.v.astype(np.float32))
            wolf.mask_data(wolf.nullvalue)
            return wolf
        else:
            return None

    def get_uv(self, output_type:Literal['numpy', 'wolf'] = 'wolf') -> Union[tuple[np.ndarray], tuple[WolfArray]]:
        """
        Return the uv as Numpy array or WolfArray to put in the UI.
        """
        return self.u(output_type), self.v(output_type)

    def get_uv_absolute(self, output_type:Literal['numpy', 'wolf'] = 'wolf') -> Union[np.ndarray, WolfArray]:

        u = self.get_u(output_type)
        v = self.get_v(output_type)

        if output_type.lower() == 'numpy':
            return np.sqrt(u**2 + v**2)
        elif output_type.lower() == 'wolf':
            norm = (u**2 + v**2)**.5
            norm.idx = self.idx+'_uv_norm'
            return norm

    def set_uv(self, value:Union[tuple[np.ndarray], tuple[WolfArray]], header:tuple[float] = (0.,0.,1.,1.), time:float=0.) -> None:
        """
        Set the uv.
        """
        if isinstance(value[0], WolfArray):

            header = value[0].get_header()
            newfield = Velocity_Field(u     = value[0].array.data,
                                      v     = value[1].array.data,
                                      origx = header.origx,
                                      origy = header.origy,
                                      dx    = header.dx,
                                      dy    = header.dy)
        else:
            newfield = Velocity_Field(u     = value[0],
                                      v     = value[1],
                                      origx = header[0],
                                      origy = header[1],
                                      dx    = header[2],
                                      dy    = header[3])

        self._ps.append_velocity_field(newfield, time)


    def get_emitters(self, output_type:Literal['shapely', 'wolf'] = 'wolf') -> Union[list[Emitter], Zones]:
        """
        Return the emitters as Shapely array or Zones to put in the UI.
        """
        if not isinstance(output_type, str):
            output_type = str(output_type)

        if output_type.lower() == 'shapely':
            return [cur.area for cur in self._ps._emitters]
        elif output_type.lower() == 'wolf':
            wolf = Zones(idx = self.idx+'_emitters')
            for id, cur in enumerate(self._ps._emitters):
                wolf.add_zone(zone(name='emitter_{}'.format(id), parent=wolf, fromshapely=cur.area))
            return wolf
        else:
            return None

    def set_emitters(self, value:Union[list[Emitter], Zones]) -> None:
        """
        Set the emitters.
        """
        if isinstance(value, Zones):
            curzone:zone
            curvect:vector
            self._ps._emitters = [Emitter(curvect.asshapely_ls(), self._ps.get_header()) for curzone in value.myzones if curzone.used for curvect in curzone.myvectors if curvect.myprop.used]
        else:
            self._ps._emitters = value

    def set_emitter(self, value:vector) -> None:
        """
        Add an emitter.
        """
        self._ps._emitters.append(Emitter(value.asshapely_ls()))

    def get_times_vf(self) -> list[float]:
        """
        Get the times for velocity fields.
        """
        return list(self._ps._velocity_fields.keys())

    def set_times_vf(self, times:list[float]):
        """
        Set the times for velocity fields.
        """

        assert len(times) == len(self._ps._velocity_fields), 'Number of times must be equal to number of velocity fields'

        vf = list(self._ps._velocity_fields.values())
        self._ps._velocity_fields = {times[i]:vf[i] for i in range(len(times))}
        pass

    def get_times(self):
        """
        Get the times.
        """
        return self._ps.times

    @property
    def blend(self) -> bool:
        """
        Return the blend status.
        """
        return self._ps.blend

    @blend.setter
    def blend(self, value:bool) -> None:
        """
        Set the blend status.
        """
        self._ps.blend = value

    @property
    def colors(self) -> list[tuple[float, int, tuple[float]]]:
        """ colors of particles """
        return self._ps.colors

    @colors.setter
    def colors(self, value:list[tuple[float, int, tuple[float]]]) -> None:
        """ colors of particles """
        self._ps.colors = value


    @property
    def nb_steps(self) -> int:
        """
        Return the number of steps.
        """
        return self._ps.nb_steps

    @property
    def timestep(self) -> float:
        """
        Return the timestep.
        """
        return self._ps.times

    @property
    def trace_size(self) -> int:
        """
        Return the trace size.
        """
        return self._trace_size

    @trace_size.setter
    def trace_size(self, value:int) -> None:
        """
        Set the trace size.
        """
        self._trace_size = value

    @property
    def ps(self) -> Particle_system:
        return self._ps

    @property
    def keys(self) -> list[float]:
        """
        Return the keys of the particles.
        """
        return self._ps.keys

    @property
    def current_step(self) -> float:
        """
        Return the current step.
        """
        return self._ps.current_step

    @current_step.setter
    def current_step(self, value:Union[float, int]) -> None:
        """
        Set the current step.
        """
        self._ps.current_step = value

    @property
    def current_step_idx(self) -> int:
        """
        Return the current step index.
        """
        return self._ps.current_step_idx

    @current_step_idx.setter
    def current_step_idx(self, value:int) -> None:
        """
        Set the current step index.
        """
        self._ps.current_step_idx = value

    @property
    def list_to_plot(self) -> list[float]:
        """
        Return the list of keys to plot.
        """
        return self._ps.n_previous_step(self._trace_size-1) + [self._ps.current_step]

    def load(self, f:str) -> None:
        """
        Load the particles from file.
        """

        fpath = Path(f)
        if fpath.exists():

            if (fpath.parent / 'particles').exists():
                allnpz = glob.glob(str(fpath.parent /'particles' / '*.npz'))
                size = 0
                for file in allnpz:
                    size += getsize(file)

                logging.info(_('Loading particles from {} ({:.3f} Mo)'.format(fpath.parent, size/1024/1024)))
                logging.info(_('It could take a while... -- but I am using multiprocess :-)'))
            else:
                logging.error(_('Dir {} does not contain particles'.format(fpath.parent)))

            self._ps.load(f)
            # with wx.BusyInfo(_('Importing particle system')):
                # wx.Log.FlushActive()
                # wait = wx.BusyCursor()
                # self._ps.load(f)
                # del wait

            logging.info(_('Particles loaded -- It takes less than I thought :-)'))
        else:
            logging.error('File {} does not exist'.format(f))

    def save(self, f:str='') -> None:
        """
        Save the particles to file.
        """
        self._ps.save(f)

    def plot(self, sx=None, sy=None, xmin=None, ymin=None, xmax=None, ymax=None, size=None):
        """
        Plot data in OpenGL context
        """
        if self.plotted:
            if len(self._ps.times)>0:

                to_plot = self.list_to_plot
                mintime = max(min(to_plot),1.e-6)
                maxtime = max(max(to_plot),1.e-6)
                if maxtime == mintime:
                    maxtime = mintime + 1.e-6

                for curtime in self.list_to_plot:
                    self._ps.plot(time = curtime, alpha=(curtime-mintime)/(maxtime-mintime))

    def next_step(self):
        """
        Go to next step.
        """
        self.current_step_idx += 1

    def previous_step(self):
        """
        Go to previous step.
        """
        self.current_step_idx -= 1

    @property
    def bounds(self) -> tuple[float]:
        """
        Return the bounds of the object.
        """
        return self._ps.bounds

    def find_minmax(self, update=False):
        """
        Generic function to find min and max spatial extent in data
        """

        self.xmin, self.ymin, self.xmax, self.ymax = self.bounds

        pass

    def check(self):
        """
        Check the object validity
        """

        internal_check, msg = self._ps.check()

        if self.fps <= 0.:
            internal_check = False
            msg += 'fps <= 0.\n'

        self._canbake = internal_check

        return internal_check, msg

    def bake(self) -> tuple[bool, str]:
        """
        Bake the object
        """
        check, msg = self.check()

        if self._canbake:
            self._ps.bake(self.totaltime, self.dt)
        else:
            logging.error('Cannot bake -- Check failed')

        return check, msg
