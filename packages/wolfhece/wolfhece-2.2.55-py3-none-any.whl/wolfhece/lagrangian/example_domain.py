"""
Author: HECE - University of Liege, Pierre Archambeau
Date: 2024

Copyright (c) 2024 University of Liege. All rights reserved.

This script and its content are protected by copyright law. Unauthorized
copying or distribution of this file, via any medium, is strictly prohibited.
"""

from shapely.geometry import Polygon, Point
import numpy as np
from pathlib import Path

from .velocity_field import Velocity_Field
from .emitter import Emitter
from .particle_system  import Particle_system

def circle_velocity_field(size:int=201, oxoy:tuple[float]=(0.,0.), dxdy:tuple[float]=(1.,1.), nb_particles:int=100, t_total:float='one round') -> tuple[Particle_system, float]:
    """
    Create a circle velocity field.

    :param size: Size of the velocity field. (odd int)
    """
    dx,dy = dxdy
    ox,oy = oxoy

    assert dx==dy, "dx and dy must be equal"

    # allocate velocity components
    u = np.zeros((size,size), dtype=np.float64)
    v = np.zeros((size,size), dtype=np.float64)

    # center of the circle
    center_ij = (size-1)/2
    radius = (center_ij* max(dx,dy))
    # Total time for one complete round
    if t_total == 'one round':
        t_total = radius * 2 * np.pi

    center_x, center_y = (center_ij+.5)*dx + ox, (center_ij+.5)*dy + oy

    # compute velocity at border of the cells
    #   - along X [i,j] is related to the left border
    #   - along Y [i,j] is related to the down border

    # First way - Geometry
    # --------------------
    # for i in range(2,size-2):
    #     for j in range(2,size-2):
    #         dist_x = np.sqrt((float(i) * dx      + ox - center_x)**2 + ((float(j)+.5) *dy + oy - center_y)**2)
    #         dist_y = np.sqrt(((float(i)+.5) * dx + ox - center_x)**2 + (float(j) *dy      + oy - center_y)**2)

    #         vabs_x = dist_x / center_x
    #         vabs_y = dist_y / center_y

    #         if dist_x == 0:
    #             dist_x = 1.
    #         if dist_y == 0:
    #             dist_y = 1.

    #         u[i,j] =  vabs_x * ((float(j)+.5) * dy - center_y) / dist_x
    #         v[i,j] = -vabs_y * ((float(i)+.5) * dx - center_x) / dist_y

    # Second way - Algebra
    # --------------------

    # circle is a linear velocity field along X and Y with an inverted sign
    uv_part = np.linspace(0., 1., int(center_ij + 1), endpoint=True)
    semi_array = np.tile(uv_part, (size,1))
    u[:,0:int(center_ij+1)] = np.flip(semi_array)
    u[:,int(center_ij):]  = -semi_array
    v[0:int(center_ij+1),:] = -np.flip(semi_array).T
    v[int(center_ij):,:]  = semi_array.T

    vel = Velocity_Field(u, v,origx=ox, origy=oy, dx=dx, dy=dy)

    # domain in which particles will be alive
    domain = np.ones(u.shape, dtype=np.int8)
    domain[int(center_ij-2):int(center_ij+3), int(center_ij-2):int(center_ij+3)] = 0
    domain[0:2,:] = 0
    domain[:,-2:] = 0
    domain[:,0:2] = 0
    domain[-2:,:] = 0

    for i in range(2,size-2):
        for j in range(2,size-2):
            dist = np.sqrt((float(i) * dx + ox - center_x)**2 + ((float(j)+.5) *dy + oy - center_y)**2)
            if dist > radius:
                domain[i,j] = 0

    # Emitter - Centered on Y
    vect_emit = Polygon([Point(center_x - dx, 2. * dy + oy),
                         Point(center_x + dx, 2. * dy + oy),
                         Point(center_x + dx, (size-2) * dy + oy),
                         Point(center_x - dx, (size-2) * dy + oy)])

    emit = Emitter(vect_emit, nb_particles, t_total+100.)

    # Particle System
    ps = Particle_system(domain, [emit], [vel])


    return ps, t_total

def labyrinth(filename:str=r'docs\source\_static\examples\labyrinth\lab_uv.npz', nb_particles:int=100, every:float=100.) -> tuple[Particle_system, float]:
    """
    Load a labyrinth velocity field from file.

    the file must contain:
        - u: x velocity component - np.ndarray - float64
        - v: y velocity component - np.ndarray - float64
        - domain: array containing the domain - np.ndarray - int8

    u, v, domain must have the same shape
    Inlet is located in the first line of the array
    """

    lab_uv = Path(filename)
    if not lab_uv.exists():
        raise FileNotFoundError(f"File {lab_uv} not found. -- Please check your file path or download it from the wolfhece gitlab repository.")

    with np.load(lab_uv) as data:
        u = data['u']
        v = data['v']
        domain = data['domain']

    inlet  = np.where(domain[0,:]==1)
    inlet = np.vstack((np.zeros_like(inlet[0]), inlet))

    vel = Velocity_Field(u, v)
    emit = Emitter(inlet, how_many= nb_particles, every_seconds= every)

    ps = Particle_system(domain, [emit], [vel])

    return ps