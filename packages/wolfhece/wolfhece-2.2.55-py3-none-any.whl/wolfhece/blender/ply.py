"""
Author: HECE - University of Liege, Pierre Archambeau
Date: 2024

Copyright (c) 2024 University of Liege. All rights reserved.

This script and its content are protected by copyright law. Unauthorized
copying or distribution of this file, via any medium, is strictly prohibited.
"""

import plyfile
import numpy as np

# Assuming you have a 3D NumPy array called 'data'
# with shape (height, width, depth)

x = np.random.uniform(-100.,100.,10000)
y = np.random.uniform(-100.,100.,10000)
z = np.random.uniform(1.,2.,10000)

vertices = np.array([(x[i],y[i],z[i]) for i in range(len(x))], dtype=[('x', 'f4'), ('y', 'f4'), ('z', 'f4')])

# Create the PLY file
plydata = plyfile.PlyData(
    [
        plyfile.PlyElement.describe(vertices, 'vertex')
    ],
    text=True
)

# Save the PLY file
plydata.write('output.ply')
