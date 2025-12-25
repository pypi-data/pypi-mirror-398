import numpy as np
import heapq
import multiprocessing as mp
import scipy.ndimage
import logging
from numba import njit
from tqdm import tqdm

@njit
def _evaluate_distance_and_data_first_order_iso(i, j,
                                                fixed:np.ndarray, where_compute:np.ndarray,
                                                dx_mesh:float, dy_mesh:float,
                                                times:np.ndarray,
                                                base_data:np.ndarray, test_data:np.ndarray,
                                                speed:float = 1.0) -> tuple[float, float]:
    """
    Evaluate the time and data using a first order isotropic method.

    :param i: (int): The row index.
    :param j: (int): The column index.
    :param fixed: (2D numpy array): A boolean array where True indicates fixed points.
    :param where_compute: (2D numpy array): A boolean array where True indicates cells to be included in computation.
    :param dx_mesh: (float): The mesh size in x direction.
    :param dy_mesh: (float): The mesh size in y direction.
    :param times: (2D numpy array): The time function.
    :param base_data: (2D numpy array): The base data that will propagate.
    :param test_data: (2D numpy array): The test data that will be used to validate propagation.
    :param speed: (float): The isotropic propagation speed.

    :return: tuple[float, float]: The time and data.
    """

    # search for fixed neighbors
    fixed_neighbors = [(i + di, j + dj) for di, dj in [(-1, 0), (1, 0), (0, -1), (0, 1)] if fixed[i + di, j + dj] and not where_compute[i + di, j + dj] and test_data[i, j] < base_data[i + di, j + dj]]

    if len(fixed_neighbors) == 0:
        return np.inf, test_data[i, j]

    a_data = a_time = np.float64(len(fixed_neighbors))
    b_time = np.sum(np.asarray([np.abs(times[cur]) for cur in fixed_neighbors]), dtype=np.float64)
    c_time = np.sum(np.asarray([times[cur] ** 2 for cur in fixed_neighbors]), dtype= np.float64)

    b_data = np.sum(np.asarray([base_data[cur] for cur in fixed_neighbors]))

    # Résolution d'une équation du second degré pour trouver la distance
    b_time = -2.0 * b_time
    # l'hypothèse implicite dx = dy est faite ici
    c_time = c_time - dx_mesh*dy_mesh * speed**2.0

    if b_time != 0. and c_time!= 0.:
        Realisant = abs(b_time*b_time-4*a_time*c_time)
        new_time = (-b_time+np.sqrt(Realisant)) / (2.0*a_time)

    elif c_time == 0.0 and b_time != 0.:
        new_time = -b_time/a_time

    elif b_time == 0.:
        new_time = np.sqrt(-c_time/a_time)

    data = b_data/a_data

    if data < test_data[i,j]:
        return np.inf, test_data[i,j]

    return new_time, data

def __solve_eikonal_with_data(sources:list[list[int,int]],
                              where_compute:np.ndarray,
                                base_data:np.ndarray,
                                test_data:np.ndarray,
                                speed:np.ndarray,
                                dx_mesh:float, dy_mesh:float) -> np.ndarray:
    """ Solve the Eikonal equation using the Fast Marching Method (FMM).

    Jit version of the function. The next one is the non-jit version which uses this.
    """

    # store the fixed points
    #  - fix sources points
    #  - fix every first element of the heap after pop
    fixed = np.zeros(speed.shape, dtype = np.uint8)

    # fix the border
    fixed[:, 0] = True
    fixed[:, -1] = True
    fixed[0, :] = True
    fixed[-1, :] = True

    time = np.ones(base_data.shape) * np.inf
    time[:,0] = 0.
    time[:,-1] = 0.
    time[0,:] = 0.
    time[-1,:] = 0.

    heap = [(0., sources[0])]
    for source in sources:
        time[source[0], source[1]] = 0
        fixed[source[0], source[1]] = True
        heapq.heappush(heap, (0., source))

    while heap:
        t, (i, j) = heapq.heappop(heap)

        fixed[i,j] = True
        where_compute[i,j] = False # as we are sure that this point is fixed

        # Add neighbors to the heap if not already added
        for di, dj in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
            new_i, new_j = i + di, j + dj

            if fixed[new_i, new_j] or not where_compute[new_i, new_j]:
                continue

            new_t, new_data = _evaluate_distance_and_data_first_order_iso(new_i, new_j,
                                                                          fixed,
                                                                          where_compute,
                                                                          dx_mesh, dy_mesh,
                                                                          time,
                                                                          base_data,
                                                                          test_data,
                                                                          speed[new_i, new_j])

            if new_t < time[new_i, new_j]:
                time[new_i, new_j] = new_t
                base_data[new_i, new_j] = new_data
                heapq.heappush(heap, (new_t, (new_i, new_j)))

    return time

def _solve_eikonal_with_data(sources:list[tuple[int,int]],
                            where_compute:np.ndarray=None,
                            base_data:np.ndarray=None,
                            test_data:np.ndarray=None,
                            speed:np.ndarray = None,
                            dx_mesh:float = 1.0, dy_mesh:float = 1.0) -> np.ndarray:
    """
    Solve the Eikonal equation using the Fast Marching Method (FMM).

    :param sources: (list of tuples): The coordinates of the source points.
    :param where_compute: (2D numpy array,  optional): A boolean array where True indicates cells to be included in computation.
    :param base_data: (2D numpy array, optional): The base data that will propagate.
    :param test_data: (2D numpy array, optional): The test data that will be used to validate propagation.
    :param speed: (2D numpy array): The speed function.
    :param dx_mesh: (float, optional): The mesh size in x direction.
    :param dy_mesh: (float, optional): The mesh size in y direction.

    :return: 2D numpy array The solution to the Eikonal equation.
    """

    rows, cols = where_compute.shape

    assert base_data.shape == where_compute.shape
    assert test_data.shape == where_compute.shape

    if len(sources) == 0:
        logging.error("No sources provided")
        return np.zeros((rows, cols))

    if speed is None:
        speed = np.ones((rows, cols))

    # Ensure sources are tuple
    #
    # FIXME : We force a global tupleof tuples because list of tuple can cause problems with Numba
    # https://numba.readthedocs.io/en/stable/reference/deprecation.html#deprecation-of-reflection-for-list-and-set-types
    sources = list(list(source) for source in sources)

    return __solve_eikonal_with_data(sources, where_compute, base_data, test_data, speed, dx_mesh, dy_mesh)

def _extract_patch_slices_with_margin(shape, labels, margin= 2):
    """ Extract the slices of the patches with a margin around the labels.

    :param shape: (tuple): The shape of the array.
    :param labels: (2D numpy array): The labels of the patches.
    :param margin: (int, optional): The margin around the labels.
    """

    slices = scipy.ndimage.find_objects(labels)
    patches_slices = []

    for s in slices:
        sl1 = slice(max(0, s[0].start - margin), min(shape[0], s[0].stop + margin))
        sl2 = slice(max(0, s[1].start - margin), min(shape[1], s[1].stop + margin))
        patches_slices.append((sl1, sl2))

    return patches_slices

def _process_submatrix(args):
    """ Function to process a submatrix in a multiprocess. """

    id_label, speed, where_compute, base_data, test_data, labels, dx, dy, NoData = args

    # Ignore the border
    labels[:,0] = -1
    labels[:,-1] = -1
    labels[0,:] = -1
    labels[-1,:] = -1
    sources = np.argwhere(np.logical_and(labels == 0, base_data != NoData))

    if len(sources) == 0:
        return (None, None)
    return (args, _solve_eikonal_with_data(sources, where_compute, base_data, test_data, speed, dx, dy))

def _solve_eikonal_with_value_on_submatrices(where_compute:np.ndarray,
                                 base_data:np.ndarray,
                                 test_data:np.ndarray = None,
                                 speed:np.ndarray = None,
                                 multiprocess:bool = False,
                                 dx:float = 1., dy:float = 1.,
                                 ignore_last_patches:int = 1,
                                 NoDataValue:float = 0.) -> np.ndarray:
    """ Propagate data inside the mask using the Fast Marching Method (FMM).

    "base_data" will be updated with the new values.

    :param where_compute: (2D numpy array): A boolean array where True indicates cells to be included in computation.
    :param base_data: (2D numpy array): The base data that will propagate.
    :param test_data: (2D numpy array, optional): The test data that will be used to validate propagation (we used upstream data only if base_data > test_data).
    :param speed: (2D numpy array, optional): The isotropic propagation speed.
    :param multiprocess: (bool, optional): Whether to use multiprocessing.
    :param dx: (float, optional): The mesh size in x direction.
    :param dy: (float, optional): The mesh size in y direction.

    :return: 2D numpy array The solution to the Eikonal equation.
    """

    # Labelling the patches
    labels, numfeatures = scipy.ndimage.label(where_compute)

    if ignore_last_patches > 0:
        # counts the number of cells in each patch
        sizes = np.bincount(labels.ravel())

        # get the indices of the patches sorted by size
        indices = np.argsort(sizes[1:])[::-1]

        # ignore the last patches
        for idx in indices[:ignore_last_patches]:
            where_compute[labels == idx+1] = 0 # idx +1 because np.argsort starts at 1, so "indices" are shifted by 1

        # relabel the patches
        labels, numfeatures = scipy.ndimage.label(where_compute)

        logging.info(f"Ignoring {ignore_last_patches} last patches.")

    logging.info(f"Number of patches: {numfeatures}")

    if numfeatures == 0:
        logging.warning("No patch to compute.")
        return np.zeros_like(where_compute)

    if speed is None:
        logging.debug("Speed not provided. Using default value of 1.")
        speed = np.ones_like(where_compute)

    if test_data is None:
        logging.debug("Test data not provided. Using -inf.")
        test_data = np.full_like(base_data, -np.inf)

    # Extract the slices of the patches with a margin of 2 cells around the labels.
    # 2 cells are added to avoid test during computation.
    # The external border will be ignored.
    patch_slices = _extract_patch_slices_with_margin(where_compute.shape, labels)

    # Prepare the submatrices to be processed
    subs = [(idx+1, speed[cur], where_compute[cur], base_data[cur], test_data[cur], labels[cur].copy(), dx, dy, NoDataValue) for idx, cur in enumerate(patch_slices)]

    if multiprocess:
        # In multiprocess mode, the base_data is updated in a local copy of the submatrix.
        # We need to merge the results at the end.
        with mp.Pool(processes=max(min(mp.cpu_count(), numfeatures),1)) as pool:
            results = pool.map(_process_submatrix, subs)

        time = np.zeros_like(where_compute)
        for slice, (sub, result) in zip(patch_slices, results):
            if result is None:
                continue
            useful_result = sub[3] != NoDataValue
            base_data[slice][useful_result] = sub[3][useful_result]
            time[slice][useful_result] = result[useful_result]

    else:
        # In single process mode, the base_data is updated in place.
        # We do not need to merge the results but only the time.
        # results = [_process_submatrix(sub) for sub in subs]

        results = []
        for sub in tqdm(subs):
            results.append(_process_submatrix(sub))

        time = np.zeros_like(where_compute)
        for slice, (sub, result) in zip(patch_slices, results):
            if result is None:
                continue
            useful_result = result != NoDataValue
            time[slice][useful_result] = result[useful_result]

    return time


def count_holes(mask:np.ndarray = None):
    """ Count the number of holes in the mask. """

    labels, numfeatures = scipy.ndimage.label(mask)

    return numfeatures

def inpaint_array(data:np.ndarray | np.ma.MaskedArray,
                  where_compute:np.ndarray,
                  test:np.ndarray,
                  ignore_last_patches:int = 1,
                  inplace:bool = True,
                  dx:float = 1., dy:float = 1.,
                  NoDataValue:float = 0.,
                  multiprocess:bool = True) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """ Inpaint the array using the Fast Marching Method (FMM).

    Main idea:
        - We have a 2D array "data" that we want to inpaint.
        - We have a 2D array "test" that will be used to validate the inpainting.
        - We have a 2D array "where_compute" that indicates where to compute the inpainting.
        - We will use the FMM to propagate the data inside the mask.
        - We will update the data only if the new value is greater than the test data.
        - (We can ignore n greatest patches to avoid computation in some large areas.)

    :param data: (2D numpy array): The water level to inpaint.
    :param mask: (2D numpy array): The simulation's Digital Elevation Model (DEM).
    :param test: (2D numpy array, optional): The digital terrain model (DTM).
    :param ignore_last_patches: (int, optional): The number of last patches to ignore.
    :param inplace: (bool, optional): Whether to update the water_level in place.
    :param dx: (float, optional): The mesh size in x direction.
    :param dy: (float, optional): The mesh size in y direction.
    :param NoDataValue: (float, optional): The NoDataValue, used if mask is not explicitly provided (mask atribute or water_level as a Numpy MaskedArray). Default is 0.
    :param multiprocess: (bool, optional): Whether to use multiprocessing.
    """
    if inplace:
        if isinstance(data, np.ma.MaskedArray):
            base_data = data.data
        else:
            base_data = data
    else:
        if isinstance(data, np.ma.MaskedArray):
            base_data = data.data.copy()
        else:
            base_data = data.copy()

    assert where_compute.shape == base_data.shape
    assert test.shape == base_data.shape

    time = _solve_eikonal_with_value_on_submatrices(where_compute,
                                                    base_data,
                                                    test,
                                                    speed=None,
                                                    dx=dx, dy=dy,
                                                    ignore_last_patches=ignore_last_patches,
                                                    NoDataValue=NoDataValue,
                                                    multiprocess=multiprocess)

    if inplace:
        if isinstance(data, np.ma.MaskedArray):
            data.mask[:,:] = base_data == NoDataValue

            extra = np.ma.masked_array(base_data - test, mask=data.mask.copy())
            extra.data[extra.data <= 0.] = NoDataValue
            extra.mask[extra.data == NoDataValue] = True
        else:
            extra = base_data - test
            extra[extra <= 0.] = NoDataValue
    else:
        if isinstance(data, np.ma.MaskedArray):
            data = np.ma.masked_array(base_data, mask=base_data == NoDataValue)

            extra = np.ma.masked_array(base_data - test, mask=data.mask)
            extra.data[extra.data <= 0.] = NoDataValue
            extra.mask[extra.data == NoDataValue] = True
        else:
            extra = base_data - test
            extra[extra <= 0.] = NoDataValue

    return time, data, extra

def inpaint_waterlevel(water_level:np.ndarray | np.ma.MaskedArray,
                       dem:np.ndarray,
                       dtm:np.ndarray,
                       ignore_last_patches:int = 1,
                       inplace:bool = True,
                       dx:float = 1., dy:float = 1.,
                       NoDataValue:float = 0.,
                       multiprocess:bool = True,
                       epsilon:float = 1e-3) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """ Inpaint the water level using the Fast Marching Method (FMM). Similar to the HOLES.EXE Fortran program.

    Assumptions:
        - The simulations are in a steady state.
        - The flood extent is limited by:
            - natural topography (where DEM == DTM)
            - buildings or blocks of buildings
            - protective structures

    The goal is to propagate the free surface elevations into the buildings.

    We calculate the difference between the DEM (including buildings and walls) and the DTM to identify where the buildings are.

    Specifically:
        - if it is natural topography, the differences will be zero or almost zero
        - if it is a building or anthropogenic structure, the differences are significant

    We set the elevations of the cells where the difference is zero to a value unreachable by the flood.
    Thus, only buildings in contact with the flood will be affected and filled.

    HOLES.EXE vs Python code:
        - In "holes.exe", we must provide "in", "mask", and "dem" files:
            - "in" is the water level
            - "dem" is the digital terrain model (DTM) associated with the simulation's topo-bathymetry (not the topo-bathymetry itself)
            - "mask" is the DTM where the buildings are identified and a large value (above the maximum water level) if the cell is not inside a building.
            - The patches are identified by the water level "0.0" in the "in" file.
            - FMM is used and new water levels are calculated and retained if greater than the "mask" value.
            - The DTM is only used in the final part when evaluating the new water depths (Z-DTM).

        - In Python, we must provide the water level, the DEM, and the DTM:
            - The patches will be identified by the buildings array (filtered DEM - DTM).
            - FMM is used and new water levels are calculated and retained if greater than the DTM value.
            - FMM is only propagated in the cells where "buildings = True".

        - Final results must be the same even if the algorithm is a little bit different.
        - Fortran code demands the "mask" file to be provided (pre-computed/modified by the user), but in Python, we calculate it automatically from the DEM and DTM.
        - We can use "inpaint_array" to be more flexible... by manually providing a "where_compute" and a "test" arrays

    :param water_level: (2D numpy array): The water level to inpaint.
    :param dem: (2D numpy array): The simulation's Digital Elevation Model (DEM).
    :param dtm: (2D numpy array, optional): The digital terrain model (DTM).
    :param ignore_last_patches: (int, optional): The number of last patches to ignore.
    :param inplace: (bool, optional): Whether to update the water_level in place.
    :param dx: (float, optional): The mesh size in x direction.
    :param dy: (float, optional): The mesh size in y direction.
    :param NoDataValue: (float, optional): The NoDataValue, used if mask is not explicitly provided (mask attribute or water_level as a Numpy MaskedArray). Default is 0.
    :param multiprocess: (bool, optional): Whether to use multiprocessing.
    :param epsilon: (float, optional): The minimum value to consider that a water height is present.
    """
    if inplace:
        if isinstance(water_level, np.ma.MaskedArray):
            base_data = water_level.data
        else:
            base_data = water_level
    else:
        if isinstance(water_level, np.ma.MaskedArray):
            base_data = water_level.data.copy()
        else:
            base_data = water_level.copy()

    assert dem.shape == base_data.shape
    assert dtm.shape == base_data.shape

    # Create the mask where we can fill the water level

    # first we identify the buildings by the difference between the DEM and the DTM
    buildings = dem - dtm
    # If DTM is above DEM, we set the value to 0
    if np.any(buildings < 0.) > 0:
        logging.warning("Some cells in the DTM are above the DEM.")
        logging.info("Setting these values to 0.")
    buildings[buildings < 0.] = 0.

    # If DTM is below DEM, we set the value to 1
    buildings[buildings <= epsilon] = 0.
    buildings[buildings > 0.] = 1.

    # We interpolate only if building cells are not already in the water_level
    comp = np.logical_and(buildings == 1., base_data != NoDataValue)
    if np.any(comp):
        logging.warning("Some building cells are already flooded.")
        logging.info("Ignoring these cells in the interpolation.")

    buildings = np.logical_and(buildings, base_data == NoDataValue)

    time = _solve_eikonal_with_value_on_submatrices(buildings,
                                                    base_data,
                                                    dtm,
                                                    speed=None,
                                                    dx=dx, dy=dy,
                                                    ignore_last_patches=ignore_last_patches,
                                                    NoDataValue=NoDataValue,
                                                    multiprocess=multiprocess)

    if inplace:
        if isinstance(water_level, np.ma.MaskedArray):
            water_level.mask[:,:] = base_data == NoDataValue

            water_height = np.ma.masked_array(base_data - dtm, mask=water_level.mask.copy())
            water_height.data[water_height.data <= 0.] = NoDataValue
            water_height.mask[water_height.data == NoDataValue] = True
        else:
            water_height = base_data - dtm
            water_height[water_height <= 0.] = NoDataValue
    else:
        if isinstance(water_level, np.ma.MaskedArray):
            water_level = np.ma.masked_array(base_data, mask=base_data == NoDataValue)

            water_height = np.ma.masked_array(base_data - dtm, mask=water_level.mask)
            water_height.data[water_height.data <= 0.] = NoDataValue
            water_height.mask[water_height.data == NoDataValue] = True
        else:
            water_height = base_data - dtm
            water_height[water_height <= 0.] = NoDataValue

    return time, water_level, water_height
