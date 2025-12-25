
"""
Author: HECE - University of Liege, Pierre Archambeau
Date: 2024

Copyright (c) 2024 University of Liege. All rights reserved.

This script and its content are protected by copyright law. Unauthorized
copying or distribution of this file, via any medium, is strictly prohibited.
"""
def test_conversion_LBT72_LBT08():

    from pyproj.transformer import TransformerGroup

    # Créer le groupe de transformateurs
    tg = TransformerGroup(31370, 3812)

    # Choisir le premier transformateur (ou un autre selon ton besoin)
    transformer = tg.transformers[0]

    print(transformer.description)
    if '(3)' in transformer.description:
        # This is the Belgian Lambert 72 + BD72 to ETRS89 (3) + Belgian Lambert 2008
        return True
    elif '(2)' in transformer.description:
        # This is the Belgian Lambert 72 + BD72 to ETRS89 (2) + Belgian Lambert 2008
        return False
    elif '(1)' in transformer.description:
        # This is the Belgian Lambert 72 + BD72 to ETRS89 (1) + Belgian Lambert 2008
        return False
    else:
        # This is not the expected transformer
        return False

def test_conversion_LBT08_LBT72():

    from pyproj.transformer import TransformerGroup

    # Créer le groupe de transformateurs
    tg = TransformerGroup(3812, 31370)

    # Choisir le premier transformateur (ou un autre selon ton besoin)
    transformer = tg.transformers[0]

    print(transformer.description)
    if '(3)' in transformer.description:
        # This is the Belgian Lambert 72 + BD72 to ETRS89 (3) + Belgian Lambert 2008
        return True
    elif '(2)' in transformer.description:
        # This is the Belgian Lambert 72 + BD72 to ETRS89 (2) + Belgian Lambert 2008
        return False
    elif '(1)' in transformer.description:
        # This is the Belgian Lambert 72 + BD72 to ETRS89 (1) + Belgian Lambert 2008
        return False
    else:
        # This is not the expected transformer
        return False

def test_transform_coordinates():
    from pyproj.transformer import TransformerGroup
    from pyproj import Transformer
    import numpy as np
    from wolfhece.Coordinates_operations import transform_coordinates
    tg = TransformerGroup(31370, 3812)

    ret = True

    ret = ret and len(tg.transformers) > 0
    ret = ret and len(tg.transformers) == 3
    ret = ret and '(3)' in tg.transformers[0].description
    ret = ret and '(2)' in tg.transformers[1].description
    ret = ret and '(1)' in tg.transformers[2].description

    tg_inv = TransformerGroup(3812, 31370)
    ret = ret and len(tg_inv.transformers) > 0
    ret = ret and len(tg_inv.transformers) == 3
    ret = ret and '(3)' in tg_inv.transformers[0].description
    ret = ret and '(2)' in tg_inv.transformers[1].description
    ret = ret and '(1)' in tg_inv.transformers[2].description

    tr = Transformer.from_crs(31370, 3812)

    points = np.array([[100000, 200000], [110000, 210000], [120000, 220000]])

    transformed_points_3 = tg.transformers[0].transform(points[:, 0], points[:, 1])
    transformed_points_2 = tg.transformers[1].transform(points[:, 0], points[:, 1])
    transformed_points_1 = tg.transformers[2].transform(points[:, 0], points[:, 1])
    transformed_points = tr.transform(points[:, 0], points[:, 1])
    transform_wolf = transform_coordinates(points, inputEPSG='EPSG:31370', outputEPSG='EPSG:3812')

    # Convert to numpy arrays
    transformed_points_3 = np.array(transformed_points_3).T
    transformed_points_2 = np.array(transformed_points_2).T
    transformed_points_1 = np.array(transformed_points_1).T
    transformed_points = np.array(transformed_points).T

    # Assert that the transformed points are equal
    ret = ret and np.all(transformed_points_3 == transform_wolf)
    ret = ret and np.all(transformed_points_3 == transformed_points)
    ret = ret and not np.all(transformed_points_2 == transformed_points)
    ret = ret and not np.all(transformed_points_1 == transformed_points)

    return ret

def main():
    # Check if installation is complete
    ret = 'Checking installation\n---------------------\n\n'


    # Get list of all packages
    import pkg_resources
    installed_packages = pkg_resources.working_set
    packages = sorted(["%s" % (i.key) for i in installed_packages])

    #is osgeo in packages?
    if 'osgeo' in packages or 'gdal' in packages:
        ret += 'OSGeo seems installed\n\n'
    else:
        ret += 'OSGeo not installed\n Please install GDAL from https://github.com/cgohlke/geospatial-wheels/releases\n\n'

    try:
        from osgeo import ogr, gdal
        ret += 'Correct import of osgeo package - GDAL/OGR installed\n\n'
    except ImportError as e:
        ret += 'Error during osgeo import - GDAL/OGR not/bad installed\n Please (re)install GDAL (64 bits version) from https://github.com/cgohlke/geospatial-wheels/releases\n\n'
        ret += 'Error : ' + str(e) + '\n\n'

    if 'pyproj' in packages:
        ret += 'PyProj seems installed\n\n'
        try:
            conv = test_conversion_LBT72_LBT08()

            if conv:
                ret += 'NTv2 conversion from Lambert 72 to Lambert 2008 seems available\n\n'
            else:
                ret += 'NTv2 conversion from Lambert 72 to Lambert 2008 seems NOT available\n\n'
                ret += 'Please check if the PROJ data files are installed correctly - See OSGOE4W instructions\n\n'
        except ImportError as e:
            ret += 'PyProj not installed properly\n Please install PyProj from "pip install pyproj"\n\n'
            ret += 'Error : ' + str(e) + '\n\n'

        try:
            conv = test_conversion_LBT08_LBT72()

            if conv:
                ret += 'NTv2 conversion from Lambert 2008 to Lambert 72 seems available\n\n'
            else:
                ret += 'NTv2 conversion from Lambert 2008 to Lambert 72 seems NOT available\n\n'
                ret += 'Please check if the PROJ data files are installed correctly - See OSGOE4W instructions\n\n'
        except ImportError as e:
            ret += 'PyProj not installed properly\n Please install PyProj from "pip install pyproj"\n\n'
            ret += 'Error : ' + str(e) + '\n\n'

        try:
            conv = test_transform_coordinates()
            if conv:
                ret += 'Transform coordinates function seems working fine\n\n'
            else:
                ret += 'Transform coordinates function seems NOT available\n\n'
                ret += 'Please check if the PROJ data files are installed correctly - See OSGOE4W instructions\n\n'
        except ImportError as e:
            ret += 'PyProj not installed properly\n Please install PyProj from "pip install pyproj"\n\n'
            ret += 'Error : ' + str(e) + '\n\n'

    else:
        ret += 'PyProj not installed\n Please install PyProj from "pip install pyproj"\n\n'

    if 'wolfgpu' in packages:
        ret += 'WolfGPU seems installed\n\n'
    else:
        ret += 'WolfGPU not installed\n Please install WolfGPU if needed\n\n'

    # try:
    #     from wolf_libs import wolfpy
    #     ret += 'Wolfpy accessible\n\n'
    # except ImportError as e:
    #     ret += 'Wolfpy not accessible\n\n'
    #     ret += 'Error : ' + str(e) + '\n\n'

    try:
        from ..PyGui import MapManager
        ret += 'Wolfhece installed\n\n'
    except ImportError as e:
        ret += 'Wolfhece not installed properly\n Retry installation : pip install wolfhece or pip install wolfhece --upgrade\n\n'
        ret += 'Error : ' + str(e) + '\n\n'

    try:
        from ..lazviewer.processing.estimate_normals.estimate_normals import estimate_normals
    except ImportError as e:
        ret += 'Could not import estimate_normals\n\n'
        ret += 'Wolfhece not installed properly\n Please install the VC++ redistributable\n from https://support.microsoft.com/en-us/help/2977003/the-latest-supported-visual-c-downloads\n\n'
        ret += 'Error : ' + str(e) + '\n\n'

    from pathlib import Path
    dirlaz = Path(__file__).parent.parent / 'lazviewer'
    dirs_to_test =  [dirlaz / 'libs', dirlaz / 'libs/qt_plugins', dirlaz / 'libs/qt_plugins/platforms']

    for d in dirs_to_test:
        if not d.exists() or not d.is_dir():
            ret += str(d) + ' does not exist\n\n'

    curdir = dirlaz / 'libs/qt_plugins/platforms'
    files_to_test = [curdir / 'qwindows.dll']

    for f in files_to_test:
        if not f.exists() or not f.is_file():
            ret += str(f) + ' does not exist\n\n'

    curdir = dirlaz / 'libs'
    files_to_test = [curdir / 'icudt53.dll', curdir / 'icuin53.dll', curdir / 'icuuc53.dll',
                     curdir / 'msvcp120.dll', curdir / 'msvcr120.dll', curdir / 'Qt5Core.dll',
                     curdir / 'Qt5Gui.dll', curdir / 'Qt5Network.dll', curdir / 'Qt5Widgets.dll',
                     curdir / 'tbb.dll', curdir / 'tbbmalloc.dll', curdir / 'vcomp120.dll']

    for f in files_to_test:
        if not f.exists() or not f.is_file():
            ret += str(f) + ' does not exist\n\n'

    try:
        from ..lazviewer.viewer import viewer
        import numpy as np

        pts = np.array([[0, 0, 0], [1, 1, 1], [2, 2, 2]])
        myview = viewer.viewer(pts, debug = True)

        ret += 'LAZ viewer created in debug mode -- check for errors if reported\n\n'

    except ImportError as e:
        ret += 'Could not import/create LAZ viewer\n\n'
        ret += 'Wolfhece not installed properly\n Please check if QT \n\n'
        ret += 'Error : ' + str(e) + '\n\n'

    print(ret)

if __name__=='__main__':
    main()