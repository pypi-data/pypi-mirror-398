"""
Author: HECE - University of Liege, Pierre Archambeau
Date: 2024

Copyright (c) 2024 University of Liege. All rights reserved.

This script and its content are protected by copyright law. Unauthorized
copying or distribution of this file, via any medium, is strictly prohibited.
"""

import numpy as np
import numba
from typing import Union, Literal

@numba.njit
def get_vertices_tri(i:int, j:int) -> list[tuple[int, int]]:
    center_i, center_j = i*2+1, j*2+1
    return [(center_i-1, center_j-1),
            (center_i  , center_j-1),
            (center_i+1, center_j-1),
            (center_i+1, center_j),
            (center_i+1, center_j+1),
            (center_i  , center_j+1),
            (center_i-1, center_j+1),
            (center_i-1, center_j),
            (center_i  , center_j)
            ]

@numba.njit
def get_vertices_quad_horiz(i:int, j:int, val:float, precision:float=1000.) -> list[tuple[int, int, int]]:
    center_i, center_j = i*2+1, j*2+1
    valint  = int(val*precision)
    return [(center_i-1, center_j-1, valint),
            (center_i+1, center_j-1, valint),
            (center_i+1, center_j+1, valint),
            (center_i-1, center_j+1, valint)
            ]

@numba.njit
def get_vertices_quad_vertx(i:int, j:int,
                            valij:float, val2:float,
                            precision:float=1000.) -> list[tuple[int, int, int]]:
    center_i, center_j = i*2+1, j*2+1
    valijint  = int(valij*precision)
    val2int  = int(val2*precision)
    return [(center_i-1, center_j-1, val2int),
            (center_i-1, center_j-1, valijint),
            (center_i-1, center_j+1, valijint),
            (center_i-1, center_j+1, val2int)
            ]

@numba.njit
def get_vertices_quad_verty(i:int, j:int,
                            valij:float, val2:float,
                            precision:float=1000.) -> list[tuple[int, int, int]]:
    center_i, center_j = i*2+1, j*2+1
    valijint  = int(valij*precision)
    val2int  = int(val2*precision)
    return [(center_i-1, center_j-1, valijint),
            (center_i-1, center_j-1, val2int),
            (center_i+1, center_j-1, val2int),
            (center_i+1, center_j-1, valijint)
            ]

@numba.njit
def get_triangles(num:np.ndarray) -> list[tuple[int, int, int]]:
    return [(num[0], num[1], num[-1]),
            (num[1], num[2], num[-1]),
            (num[2], num[3], num[-1]),
            (num[3], num[4], num[-1]),
            (num[4], num[5], num[-1]),
            (num[5], num[6], num[-1]),
            (num[6], num[7], num[-1]),
            (num[7], num[0], num[-1]),
            ]

@numba.njit
def get_value(a:np.array, i:int, j:int) -> float:
    incr_i = 1 - np.mod(i,2)
    incr_j = 1 - np.mod(j,2)
    i = (i-1) //2
    j = (j-1) //2
    return np.sum(a[i:i+1+incr_i,j:j+1+incr_j]) / np.count_nonzero(a[i:i+1+incr_i,j:j+1+incr_j])

def newMaterial(id:str):
    import bpy

    mat = bpy.data.materials.get(id)

    if mat is None:
        mat = bpy.data.materials.new(name=id)

    mat.use_nodes = True

    if mat.node_tree:
        mat.node_tree.links.clear()
        mat.node_tree.nodes.clear()

    return mat

def newShader(id:str,
              type:Literal["diffuse",
                           "emission",
                           "glossy",
                           "trnslucent",
                           "vertex_color"],
              r:float, g:float, b:float):
    import bpy

    mat = newMaterial(id)

    nodes = mat.node_tree.nodes
    links = mat.node_tree.links
    output = nodes.new(type='ShaderNodeOutputMaterial')

    if type == "diffuse":
        shader = nodes.new(type='ShaderNodeBsdfDiffuse')
        nodes["Diffuse BSDF"].inputs[0].default_value = (r, g, b, 1)

    elif type == "emission":
        shader = nodes.new(type='ShaderNodeEmission')
        nodes["Emission"].inputs[0].default_value = (r, g, b, 1)
        nodes["Emission"].inputs[1].default_value = 1

    elif type == "glossy":
        shader = nodes.new(type='ShaderNodeBsdfGlossy')
        nodes["Glossy BSDF"].inputs[0].default_value = (r, g, b, 1)
        nodes["Glossy BSDF"].inputs[1].default_value = 0.1

    elif type == "translucent":
        shader = nodes.new(type='ShaderNodeBsdfTranslucent')
        nodes["Translucent BSDF"].inputs[0].default_value = (r, g, b, 1)

    elif type == "vertex_color":
        shader = nodes.new(type='ShaderNodeVertexColor')
        shader.layer_name = 'color'

    links.new(shader.outputs[0], output.inputs[0])

    mat.blend_method = 'BLEND'

    return mat

def new_mesh(coords:np.ndarray, poly_idx:np.ndarray, painting_mode:Literal['VERTEX_PAINT', 'WATER']):
    import bpy
    import bmesh

    # Créer un nouvel objet mesh
    mesh = bpy.data.meshes.new("Maillage")
    obj = bpy.data.objects.new("Objet", mesh)

    # Ajouter l'objet à la scène
    scene = bpy.context.scene
    scene.collection.objects.link(obj)

    # Créer les sommets et les faces du maillage
    mesh.from_pydata(coords, [], poly_idx)
    mesh.update()

    bm = bmesh.new()
    bm.from_mesh(mesh)

    bpy.context.view_layer.objects.active = obj
    bpy.context.object.data.use_auto_smooth = True
    bpy.ops.object.modifier_add(type='WEIGHTED_NORMAL')

    if painting_mode == 'WATER':
        mat = newShader('Water', 'translucent', 0, 0, 1)
        obj.data.materials.append(mat)
    elif painting_mode == 'VERTEX_PAINT':
        color_layer = bm.loops.layers.color.new("color")
        mat = newShader('vertex_color', 'vertex_color', 0, 0, 1)
        obj.data.materials.append(mat)

        for face in bm.faces:
            for loop in face.loops:
                z = loop.vert.co.z
                loop[color_layer] = (min(z,1.), 0., 0., 1.)
        bm.to_mesh(mesh)
    return mesh

def triangulate(a:np.array, nullvalue:float=0.):
    """ Triangulate a 2D array and apply a water color to it """

    mask = a!=nullvalue
    x, y = np.where(mask)

    verts = np.asarray([get_vertices_tri(i,j) for i,j in zip(x,y)]).reshape((-1,2))

    unique_verts, invert_a = np.unique(verts, return_inverse=True, axis=0)

    triangles = np.asarray([get_triangles(invert_a[idx*9:(idx+1)*9]) for idx in range(len(verts)//9)]).reshape((-1,3))

    z_values = np.asarray([get_value(a, i, j) for i, j in unique_verts])

    triplets = np.hstack((unique_verts, z_values.reshape((-1,1))))

    return triplets, triangles

def quadrangulate(a:np.array, nullvalue:float=0., precision:float=1000.):
    """ Quadrangulate a 2D array and apply a vertex color to it """

    mask = a!=nullvalue
    mask_x = np.logical_and(mask, np.roll(mask, 1, axis=0))
    mask_y = np.logical_and(mask, np.roll(mask, 1, axis=1))

    x, y = np.where(mask)
    internx_x, interny_x = np.where(mask_x)
    internx_y, interny_y = np.where(mask_y)

    quad_h = np.asarray([get_vertices_quad_horiz(i,j, a[i,j], precision) for i,j in zip(x, y)]).reshape((-1,3))
    quad_x = np.asarray([get_vertices_quad_vertx(i,j, a[i,j], a[i-1,j], precision) for i,j in zip(internx_x, interny_x)]).reshape((-1,3))
    quad_y = np.asarray([get_vertices_quad_verty(i,j, a[i,j], a[i,j-1], precision) for i,j in zip(internx_y, interny_y)]).reshape((-1,3))

    verts = np.concatenate((quad_h, quad_x, quad_y))

    unique_verts, invert_a = np.unique(verts, return_inverse=True, axis=0)

    quads = np.asarray([invert_a[idx*4:(idx+1)*4] for idx in range(len(verts)//4)])

    verts_float = unique_verts.astype(np.float32)
    verts_float[:,2] /= precision

    return verts_float, quads

def load_wolfarray(filepath:str):
    from wolfhece.wolf_array import WolfArray
    import plyfile
    import pygltflib

    locarray = WolfArray(filepath)
    locarray.export_to_gltf()

    # verts, quads = quadrangulate(locarray.array.data, nullvalue=locarray.nullvalue)    
    # new_mesh(verts, quads, painting_mode = 'VERTEX_PAINT')

    # triplets, triangles = triangulate(locarray.array.data, nullvalue=locarray.nullvalue)    
    # mesh = new_mesh(triplets, triangles, painting_mode='WATER')


def main():

    # load_wolfarray(r"D:\OneDrive\OneDrive - Universite de Liege\Crues\2021-07 Vesdre\CSC - Convention - ARNE\Data\GPU\Chaudfontaine\bathymetry.tif")
    load_wolfarray(r'C:\Users\Pierre\OneDrive - Universite de Liege\Crues\2021-07 Vesdre\CSC - Convention - ARNE\Data\GPU\Chaudfontaine\bathymetry.tif')

def main_test(nb:int):
    """ Test function """
    a = np.random.rand(nb, nb)
    a[:,0] = 0
    a[:,-1] = 0
    a[0,:] = 0
    a[-1,:] = 0
    a[a<0.02] = 0
    a*=2.

    quadrangulate(a)
    triangulate(a)

    pass

if __name__ == "__main__":
    # main_test(10)
    main()