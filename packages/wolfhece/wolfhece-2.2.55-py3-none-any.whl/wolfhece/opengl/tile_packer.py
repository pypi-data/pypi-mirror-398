from enum import Enum
import logging
from math import sqrt, ceil
import numpy as np

class TilePackingMode(Enum):
    REGULAR = 1
    #SHUFFLED = 2
    TRANSPARENT = 3 # For debugging: set it to disable the tile packing.

class TilePacker:
    """
    A class that packs an array in tiles and provides an indirection map

    After the initialization phase based on the "NAP" array, the class provides two methods:
        - shuffle_and_pack_array
        - unpack_and_deshuffle_array
    """


    def __init__(self, nap: np.ndarray, tile_size: int, mode: TilePackingMode = TilePackingMode.REGULAR):
        """
        Initialize the tile indirection system.

        The motivation is that usually, due to the shape of our rivers, the computation
        domain (a matrix) is mostly empty. Therefore we don't use the memory very
        wisely if we keep a plain rectangular domain to store a riverbed.

        What we do is:
        - cut the computation domain in tiles. A tile is either active or inactive.
          An active tile is one that contains meshes which are marke active in the NAP map.
        - translate all the active tiles so that they are close together ("packing")

        Of course, once the tiles are packed, the whole hydro computation must still continue
        to work. So each time the hydro computation looks for a mesh at (i,j), we must
        translate those coordinates to the "packed" domain. So in this function we also
        compute an "indirection" map that tells us where a (t_i, t_j) tile falls in the
        packed domain.

        nap: the NAP array.
        """
        self._tile_size = tile_size
        self._mode = mode
        self._height, self._width = nap.shape

        # Save the NAP for reuse later on (in our case, saving it to disk in the ResultStore)
        # ATTENTION don't build upon it because it eats a lot of memory. It's just here
        # as a cheap placeholder.
        # FIXME Later on one should store it directly from the sim to the disk
        self._original_nap = nap

        nap = self._pad_array_to_tiles(nap)

        nb_tiles_x, nb_tiles_y = self.size_in_tiles()

        # Here we cut the original NAP array into tiles.
        # (I(ve tried to do it with reshape, but it seems to not being able to do the
        # job. E.g. cut a 4x4 array in 2x2 tiles:  np.arange(16).reshape(4,4).T.reshape(2,2,2,2) fail...)
        # In the end we get a (nb tiles x, nb tiles y) array of which
        # each element is a (_tile_size, _tile_size) tile array.
        # To understand the stride trick, do this:
        # - read the shape parameter as the shape you *want*.
        # - read the strides as strides over the flattened array. The first
        #   two strides are to choose the tile. The other two strides are
        #   to enumerate the elements inside a tile.

        TS = self._tile_size

        # # ATTENTION stride_tricks comes with tons of gotcha's !
        # # array item size (in bytes)
        # ais = nap.dtype.itemsize
        # tiled = np.lib.stride_tricks.as_strided(
        #     np.ascontiguousarray(nap), # This one is really necessary (see warning in side_tricks documentation)
        #     shape=((nap.shape[0]//TS,nap.shape[1]//TS,TS,TS)),
        #     strides=(nap.shape[1]*TS*ais, TS*ais, # choose tile
        #              nap.shape[1]*ais, 1*ais), # enumerate meshes inside tile
        #     writeable=False)
        # # Determine if a tile has some active meshes inside it
        # # We do that by summing the NAP values inside each tile.
        # tiles_sums = np.sum(tiled, axis=(2,3))

        # Replacing the above lines by more numpy-ish code.
        tiles_sums = np.sum(nap.reshape(nap.shape[0]//TS,TS,nap.shape[1]//TS,TS).swapaxes(1,2), axis=(2,3))

        active_tiles = np.zeros_like(tiles_sums, np.uint32)

        assert active_tiles.shape == (nb_tiles_y,nb_tiles_x), f"{active_tiles.shape} ?"

        active_tiles[tiles_sums > 0] = 1

        # Numbering active cells (0 == inactive, >= 1 == active)

        # Note that we have an edge case.

        # This case occurs when we compute meshes located on the border of a
        # tile of which the neighbouring border tile (call it n_t) is not
        # active. When we compute that mesh, we usually have a look at its
        # neighbours. In this edge case, one of the neighbours in question (call
        # it n_m) will be inside the neighbouring tile (n_t) which is inactive.
        # Since this tile is inactive, it will not be part of the "packed tiles"
        # and thus has no representation whatsoever. Therefore, the values
        # h,qx,qy,bathy,... of n_m ill be unknown.

        # On a regular (non packed) computation domain it's not a problem
        # because we put default/neutral values (such as water height == 0) in
        # inactive meshes. So when we look outside the domain, we get these safe
        # values.

        # Once tiles are packed, as we have seen, we may reach out to a not
        # existing, or worse, random tile. To avoid that, we choose to have an
        # "emtpy" tile and number it zero. Any lookup outside the regular active
        # tiles will fall on the empty tile. Adding a tile imply that if we have
        # N active tiles in the computation domain we'll store N+1 tiles. So we
        # have to make enough room to allow that.

        self._active_tiles_ndx = np.nonzero(active_tiles) # Only indices (don't multiply by tile_size)
        self._nb_active_tiles = len(self._active_tiles_ndx[0])
        active_tiles[self._active_tiles_ndx] = np.arange(1, self._nb_active_tiles+1) #+1 for the "empy" tile

        # Now transforming the numbers of the numbered cells in coordinates

        # Indir will map a tile index (ty,tx) into its indirected x (indir[ty,tx,0]) and y ([ty,tx,1])
        # coordinates
        # Note  : dtype can not be changed because it's used in the OpenGL shader code or you have to modify the shader code too.
        indir = np.zeros( (nb_tiles_y,nb_tiles_x,2), dtype=np.uint16)

        used_tiles = self._nb_active_tiles + 1
        # pack tiles in a square or almost in a square
        self._packed_nb_tiles_x = int(sqrt(used_tiles))
        self._packed_nb_tiles_y = int(ceil(used_tiles / self._packed_nb_tiles_x))
        indir[:,:,0] = active_tiles % self._packed_nb_tiles_x
        indir[:,:,1] = active_tiles // self._packed_nb_tiles_x

        # Convert to mesh position (this spares a multiplication
        # in the shader code)
        indir *= self._tile_size

        # When shuffling arrays, it should be faster to read directly
        # the active cells.

        if self._mode == TilePackingMode.TRANSPARENT:
            # For debugging purpose: create some "harmless" indirection maps.
            # This is basically a transparent map
            nb_tiles_x, nb_tiles_y = self.size_in_tiles()
            self._packed_nb_tiles_x, self._packed_nb_tiles_y = nb_tiles_x, nb_tiles_y

            xs = np.repeat( np.atleast_2d( np.arange(nb_tiles_x)), nb_tiles_y, axis=0)
            ys = np.repeat( np.atleast_2d( np.arange(nb_tiles_y)), nb_tiles_x, axis=0).T
            indir = np.zeros( (nb_tiles_y,nb_tiles_x,2), dtype=np.uint16)
            indir[:,:,0] = xs
            indir[:,:,1] = ys
            indir *= self._tile_size

            self._active_tiles_ndx = None
            self._nb_active_tiles = None

            #indir = np.roll(indir, shift=nbx//4, axis = 1)
            #indir = np.roll(indir, shift=nby//4, axis = 0)

        #print(indir)
        self._tile_indirection_map = indir

    # FIXME : why not a property ?
    def tile_indirection_map(self):
        return self._tile_indirection_map

    # FIXME : why not a property ?
    def mode(self) -> TilePackingMode:
        return self._mode

    # FIXME : why not a property ?
    def packed_size(self):
        """ Size of the arrays after padding them and packing them in tiles,
        expressed in meshes. Size is a (width, height) tuple.

        Note that this size can be very different than the actual computation
        domain size.
        """
        if self._mode != TilePackingMode.TRANSPARENT:
            return (self._packed_nb_tiles_x * self._tile_size,
                    self._packed_nb_tiles_y * self._tile_size)
        else:
            return (self._width, self._height)

    # FIXME : why not a property ?
    def packed_size_in_tiles(self):
        """ Size of the arrays after padding them and packing them in tiles,
        expressed in tiles. Size is a (width, height) tuple.

        Note that this size can be very different than the actual computation
        domain size.
        """
        return (self._packed_nb_tiles_x,
                self._packed_nb_tiles_y)

    # FIXME : why not a property ?
    def size_in_tiles(self):
        """
        Size of the (original, non packed, non tiled) computation domain, in
        tiles. Not that we count full tiles. So if one dimension of the domain
        is not a multiple of the tile size, then we round one tile up.

        Size is a (width, height) tuple.
        """
        return ((self._width +self._tile_size-1) // self._tile_size,
                (self._height+self._tile_size-1) // self._tile_size)

    # FIXME : why not a property ?
    def tile_size(self) -> int:
        """ The tile size. Note that tiles are squared.
        """
        return self._tile_size

    # FIXME : why not a property ?
    def active_tiles_ndx(self):
        return self._active_tiles_ndx

    def unpack_and_deshuffle_array(self, a: np.ndarray) -> np.ndarray:
        """ De-shuffle and un-pad an array that was shuffled and padded.
        """
        psw, psh = self.packed_size()
        assert a.shape[0] == psh and a.shape[1] == psw, \
              f"Seems like the array you gave is not shuffled/padded. Its shape is {a.shape}. " \
              f"I was expecting something with a shape like ({psh},{psw},...)"

        if self._mode == TilePackingMode.TRANSPARENT:
            return a

        s = list(a.shape)
        s[0], s[1] = self._height, self._width
        r = np.zeros( tuple(s), dtype=a.dtype )

        for tile_pos in zip(self._active_tiles_ndx[0], self._active_tiles_ndx[1]):

            j, i = tile_pos

            if (i+1)*self._tile_size > self._width:
                tw = self._tile_size - ((i+1)*self._tile_size - self._width)
            else:
                tw = self._tile_size

            if (j+1)*self._tile_size > self._height:
                th = self._tile_size - ((j+1)*self._tile_size - self._height)
            else:
                th = self._tile_size

            dest_slice_i = slice(i*self._tile_size, i*self._tile_size + tw)
            dest_slice_j = slice(j*self._tile_size, j*self._tile_size + th)

            tc = self._tile_indirection_map[j,i,:]
            source_slice_i = slice(tc[0], tc[0]+tw)
            source_slice_j = slice(tc[1], tc[1]+th)

            r[dest_slice_j, dest_slice_i, ...] = a[source_slice_j, source_slice_i, ...]

        return r


    def _unpad_array(self, a: np.ndarray) -> np.ndarray:
        """ Undo `_pad_array_to_tiles`.
        """
        ntx, nty = self.size_in_tiles()
        assert a.shape[0] == nty*self._tile_size, "Seems like the array you gave is not padded"
        assert a.shape[1] == ntx*self._tile_size, "Seems like the array you gave is not padded"
        return a[0:self._height, 0:self._width]


    def _pad_array_to_tiles(self, a: np.ndarray) -> np.ndarray:
        """ Make an array fit in a given number of tiles (on x and y axis).
        After this, the array's dimensions are multiple of the tile_size.
        """

        assert a.shape[0] == self._height, "The array seems to have nothing to do with a computation domain"
        assert a.shape[1] == self._width, "The array seems to have nothing to do with a computation domain"
        ntx, nty = self.size_in_tiles()
        mesh_to_add_on_y = nty*self._tile_size - a.shape[0]
        mesh_to_add_on_x = ntx*self._tile_size - a.shape[1]
        assert mesh_to_add_on_y >= 0, "Your array is too tall (or there's something wrong in the tiles)"
        assert mesh_to_add_on_x >= 0, "Your array is too wide (or there's something wrong in the tiles)"

        if len(a.shape) == 3:
            return np.pad(a, [(0,mesh_to_add_on_y), (0,mesh_to_add_on_x), (0,0)])
        elif len(a.shape) == 2:
            return np.pad(a, [(0,mesh_to_add_on_y), (0,mesh_to_add_on_x)])
        else:
            raise Exception(f"Array shape {a.shape} is not not supported")


    def shuffle_and_pack_array(self, a: np.ndarray, neutral_values = None) -> np.ndarray:
        """ Reorganize an array by moving tiles around to
        follow the ordering given by `self._tile_indirection_map`
        The array is resized in order to be just as large as
        needed to hold the active tiles plus the "empty" tile.

        `neutral_values`: value to fill the empty tile with.
        """

        if self._mode == TilePackingMode.TRANSPARENT:
            return a

        logging.debug(f"Packing {a.shape}")

        # Padding to avoid tricky computations over "incomplete" tiles.
        a = self._pad_array_to_tiles(a)

        packed_shape = list(a.shape) # Preserve the third dimension, if any.
        packed_shape[0] = self._packed_nb_tiles_y * self._tile_size
        packed_shape[1] = self._packed_nb_tiles_x * self._tile_size

        # Clearing non used tiles because they're acutally use while computing
        # max step size ('cos that computation doesn't use the indirection mechanism)

        # FIXME We clear too much, only the last row of tiles and the "neutral" tile
        # should be cleared.

        # The array containing the active tiles, packed.
        if neutral_values is None:
            packed_tiles = np.zeros(tuple(packed_shape), dtype=a.dtype)
        else:
            packed_tiles = np.empty(tuple(packed_shape), dtype=a.dtype)
            packed_tiles[:,:,...] = neutral_values

        # There's the 0-th tile which is meant to be neutral. So we clear it
        # because 0 is mostly neutral (it depends on what `a` (the input array)
        # represents. If it's h,qx,qy then it's neutral, but for bathymetry it
        # may be different.

        # FIXME For the moment, I believe that if h,qx,qy then, the mesh is
        # neutral, regardless of the other params such as bathymetry.

        if neutral_values is None:
            packed_tiles[0:self._tile_size, 0:self._tile_size, ...] = 0
        else:
            packed_tiles[0:self._tile_size, 0:self._tile_size, ...] = neutral_values

        # Go over all NAP-active tiles and pack each of them.
        for tile_coord in zip(self._active_tiles_ndx[0], self._active_tiles_ndx[1]):

            j,i = tile_coord
            source_i = slice(i*self._tile_size, (i+1)*self._tile_size)
            source_j = slice(j*self._tile_size, (j+1)*self._tile_size)

            # Remember that the active tiles are numbered 1-based. The 0-th tile
            # is the "neutral value" tile (used to represent out of domain, neutral data)
            tc = self._tile_indirection_map[j,i,:]
            dest_i = slice(tc[0], tc[0]+self._tile_size)
            dest_j = slice(tc[1], tc[1]+self._tile_size)

            #logging.trace(f"{a.shape} -> {packed_shape}: {dest_i}, {dest_j}")
            packed_tiles[dest_j, dest_i, ...] = a[source_j, source_i, ...]

        return packed_tiles
