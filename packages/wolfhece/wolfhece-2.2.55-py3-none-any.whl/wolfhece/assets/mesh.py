from matplotlib import pyplot as plt
from matplotlib.axes import Axes
from matplotlib.figure import Figure
import numpy as np

from ..wolf_array import header_wolf
from ..wolfresults_2D import q_splitting, u_splitting, splitting_rule

class Mesh2D(header_wolf):

    def __init__(self, src_header:header_wolf):

        self.set_origin(src_header.origx, src_header.origy)
        self.set_resolution(src_header.dx, src_header.dy)
        self.set_translation(src_header.translx, src_header.transly)
        self.shape = src_header.shape
        self._factor = None

    def plot_cells(self, ax:Axes=None, transpose:bool= False, color='black', **kwargs):
        """ Plot the grid of the mesh.
        """

        if ax is None:
            fig, ax = plt.subplots()
        else:
            fig = ax.figure

        [xmin, xmax], [ymin, ymax] = self.get_bounds()

        if transpose:

            # plot the grid of the mesh in a transposed way
            for x in np.linspace(xmin, xmax, endpoint=True, num=self.nbx + 1):
                ax.plot([ymin, ymax], [x, x], color=color, **kwargs)

            for y in np.linspace(ymin, ymax, endpoint=True, num=self.nby + 1):
                ax.plot([y, y], [xmin, xmax], color=color, **kwargs)

            self.set_aspect_labels_matrice(ax=ax, **kwargs)

        else:

            # plot the grid of the mesh
            for y in np.linspace(ymin, ymax, endpoint=True, num=self.nby + 1):
                ax.plot([xmin, xmax], [y, y], color=color, **kwargs)

            for x in np.linspace(xmin, xmax, endpoint=True, num=self.nbx + 1):
                ax.plot([x, x], [ymin, ymax], color=color, **kwargs)

            self.set_aspect_labels(ax=ax, **kwargs)

        return fig, ax

    def plot_center_cells(self, ax:Axes=None, color='black', linestyle='--', **kwargs):
        """ Plot lines centered to the cells.
        """

        if ax is None:
            fig, ax = plt.subplots()
        else:
            fig = ax.figure

        [xmin, xmax], [ymin, ymax] = self.get_bounds()

        for y in np.linspace(ymin + self.dy/2., ymax - self.dy/2., endpoint=True, num=self.nby):
            ax.plot([xmin, xmax], [y, y], color=color, linestyle=linestyle, **kwargs)

        for x in np.linspace(xmin + self.dx/2., xmax - self.dx/2., endpoint=True, num=self.nbx):
            ax.plot([x, x], [ymin, ymax], color=color, linestyle=linestyle, **kwargs)

        self.set_aspect_labels(ax=ax, **kwargs)
        return fig, ax

    def set_ticks_as_dxdy(self, ax:Axes=None, **kwargs):
        """ Set the ticks of the axis as the dx and dy of the mesh.
        """

        if ax is None:
            fig, ax = plt.subplots()
        else:
            fig = ax.figure

        [xmin, xmax], [ymin, ymax] = self.get_bounds()

        x_ticks = ['ox + tx', r'+$\Delta x$'] + [f'+{i}$\Delta x$' for i in range(2,self.nbx+1)]
        y_ticks = ['oy + ty', r'+$\Delta y$'] + [f'{+i}$\Delta y$' for i in range(2,self.nby+1)]

        ax.set_xticks(np.linspace(xmin, xmax, endpoint=True, num=self.nbx + 1))
        ax.set_yticks(np.linspace(ymin, ymax, endpoint=True, num=self.nby + 1))
        ax.set_xticklabels(x_ticks)
        ax.set_yticklabels(y_ticks)

        return fig, ax

    def set_ticks_as_matrice(self, ax:Axes=None, Fortran_type:bool = True, **kwargs):
        """ Set the ticks of the axis as the row and column of a matrice """

        if ax is None:
            fig, ax = plt.subplots()
        else:
            fig = ax.figure

        [xmin, xmax], [ymin, ymax] = self.get_bounds()

        if Fortran_type:
            x_ticks = [f'{i}' for i in range(1,self.nbx+1)]
            y_ticks = [f'{i}' for i in range(1,self.nby+1)]
        else:
            x_ticks = [f'{i}' for i in range(self.nbx)]
            y_ticks = [f'{i}' for i in range(self.nby)]

        ax.set_yticks(np.linspace(xmin+self.dx/2., xmax-self.dx/2., endpoint=True, num=self.nbx))
        ax.set_xticks(np.linspace(ymin+self.dy/2., ymax-self.dy/2., endpoint=True, num=self.nby))
        
        x_ticks.reverse()
        ax.set_yticklabels(x_ticks)
        ax.set_xticklabels(y_ticks)

        self.set_aspect_labels_matrice(ax=ax, **kwargs)

        return fig, ax

    def plot_circle_at_centers(self, ax:Axes=None, color='black', radius:float=None, **kwargs):
        """ Plot circles at the center of the cells.
        """

        if radius is None:
            radius = 0.1 * self.dx

        if ax is None:
            fig, ax = plt.subplots()
        else:
            fig = ax.figure

        [xmin, xmax], [ymin, ymax] = self.get_bounds()

        for y in np.linspace(ymin + self.dy/2., ymax - self.dy/2., endpoint=True, num=self.nby):
            for x in np.linspace(xmin + self.dx/2., xmax - self.dx/2., endpoint=True, num=self.nbx):
                circle = plt.Circle((x, y), radius=radius, color=color, **kwargs)
                ax.add_artist(circle)

        self.set_aspect_labels(ax=ax, **kwargs)

        return fig, ax

    def plot_indices_at_centers(self, ax:Axes=None, Fortran_type:bool = True, **kwargs):
        """ Plot the indices of the cells at the center of the cells.
        """

        if ax is None:
            fig, ax = plt.subplots()
        else:
            fig = ax.figure

        [xmin, xmax], [ymin, ymax] = self.get_bounds()

        for y in np.linspace(ymin + self.dy/2., ymax - self.dy/2., endpoint=True, num=self.nby):
            for x in np.linspace(xmin + self.dx/2., xmax - self.dx/2., endpoint=True, num=self.nbx):
                i,j = self.xy2ij(x, y)

                if Fortran_type:
                    i+=1
                    j+=1

                ax.text(x, y, f'({i},{j})', horizontalalignment='center', verticalalignment='center', **kwargs)

        self.set_aspect_labels(ax=ax, **kwargs)

        return fig, ax
    
    def plot_memoryposition_at_centers(self, ax:Axes=None, 
                                       transpose=False, 
                                       Fortran_type:bool = True, 
                                       f_contiguous:bool = True,
                                       **kwargs):
        """ Plot the position of the cells at the center of the cells.
        """

        if ax is None:
            fig, ax = plt.subplots()
        else:
            fig = ax.figure

        [xmin, xmax], [ymin, ymax] = self.get_bounds()

        if transpose:
            k = 0
            if Fortran_type:
                k+=1

            all_y = list(np.linspace(xmin + self.dx/2., xmax - self.dx/2., endpoint=True, num=self.nbx))
            all_x = list(np.linspace(ymin + self.dy/2., ymax - self.dy/2., endpoint=True, num=self.nby))

            all_y.reverse()

            if f_contiguous:

                for x in all_x:
                    for y in all_y:

                        ax.text(x, y, f'{k}', horizontalalignment='center', verticalalignment='center', **kwargs)
                        k+=1
            else:

                for y in all_y:
                    for x in all_x:

                        ax.text(x, y, f'{k}', horizontalalignment='center', verticalalignment='center', **kwargs)
                        k+=1
                        
            self.set_aspect_labels_matrice(ax=ax, **kwargs)

        else:
            
            k = 0
            if Fortran_type:
                k+=1

            for y in np.linspace(ymin + self.dy/2., ymax - self.dy/2., endpoint=True, num=self.nby):
                for x in np.linspace(xmin + self.dx/2., xmax - self.dx/2., endpoint=True, num=self.nbx):

                    ax.text(x, y, f'{k}', horizontalalignment='center', verticalalignment='center', **kwargs)
                    k+=1

            self.set_aspect_labels(ax=ax, **kwargs)

        return fig, ax

    def plot_indices_at_bordersX(self, ax:Axes=None, Fortran_type:bool = True, **kwargs):
        """ Plot the indices of the cells at the borders of the cells.
        """

        if ax is None:
            fig, ax = plt.subplots()
        else:
            fig = ax.figure

        [xmin, xmax], [ymin, ymax] = self.get_bounds()

        for y in np.linspace(ymin + self.dy/2., ymax - self.dy/2., endpoint=True, num=self.nby):
            for x in np.linspace(xmin, xmax, endpoint=True, num=self.nbx + 1):
                i,j = self.xy2ij(x, y)

                if Fortran_type:
                    i+=1
                    j+=1

                ax.text(x, y, f'({i},{j})', horizontalalignment='center', verticalalignment='center', **kwargs)

    def plot_indices_at_bordersY(self, ax:Axes=None, Fortran_type:bool = True, **kwargs):
        """ Plot the indices of the cells at the borders of the cells.
        """

        if ax is None:
            fig, ax = plt.subplots()
        else:
            fig = ax.figure

        [xmin, xmax], [ymin, ymax] = self.get_bounds()

        for y in np.linspace(ymin, ymax, endpoint=True, num=self.nby + 1):
            for x in np.linspace(xmin + self.dx/2., xmax - self.dx/2., endpoint=True, num=self.nbx):
                i,j = self.xy2ij(x, y)

                if Fortran_type:
                    i+=1
                    j+=1

                ax.text(x, y, f'({i},{j})', horizontalalignment='center', verticalalignment='center', **kwargs)

        self.set_aspect_labels(ax=ax, **kwargs)

        return fig, ax

    def plot_Xarrows_at_center(self, ax:Axes=None,
                               randomize:bool=False,
                               amplitude:np.ndarray=None,
                               color='black', **kwargs):
        """ Plot arrows at the center of the cells.
        """

        if ax is None:
            fig, ax = plt.subplots()
        else:
            fig = ax.figure

        [xmin, xmax], [ymin, ymax] = self.get_bounds()

        if amplitude is None:
            amplitude = np.ones((self.nbx, self.nby)) * 0.2 * self.dx
        else:
            amplitude = self.scale_amplitude(amplitude)

        for y in np.linspace(ymin + self.dy/2., ymax - self.dy/2., endpoint=True, num=self.nby):
            for x in np.linspace(xmin + self.dx/2., xmax - self.dx/2., endpoint=True, num=self.nbx):

                i,j = self.xy2ij(x, y)
                if randomize:
                    dx = np.random.uniform(-0.5, 0.5) * self.dx
                    amplitude[i,j] = dx
                else:
                    dx = amplitude[i,j]

                ax.arrow(x - dx/2., y, dx, 0,
                         head_width=0.1 * self.dx, head_length=0.1 * self.dy,
                         fc=color, ec=color)

        self.set_aspect_labels(ax=ax, **kwargs)

        return fig, ax, amplitude

    def plot_Yarrows_at_center(self, ax:Axes=None,
                               randomize:bool=False,
                               amplitude:np.ndarray=None,
                               color='black', **kwargs):
        """ Plot arrows at the center of the cells.
        """

        if ax is None:
            fig, ax = plt.subplots()
        else:
            fig = ax.figure

        [xmin, xmax], [ymin, ymax] = self.get_bounds()

        if amplitude is None:
            amplitude = np.ones((self.nbx, self.nby)) * 0.2 * self.dy
        else:
            amplitude = self.scale_amplitude(amplitude)

        for y in np.linspace(ymin + self.dy/2., ymax - self.dy/2., endpoint=True, num=self.nby):
            for x in np.linspace(xmin + self.dx/2., xmax - self.dx/2., endpoint=True, num=self.nbx):

                i,j = self.xy2ij(x, y)
                if randomize:
                    dy = np.random.uniform(-0.5, 0.5) * self.dy
                    amplitude[i,j] = dy
                else:
                    dy = amplitude[i,j]

                ax.arrow(x, y - dy/2., 0, dy,
                         head_width=0.1 * self.dx, head_length=0.1 * self.dy,
                         fc=color, ec=color)

        self.set_aspect_labels(ax=ax, **kwargs)

        return fig, ax, amplitude

    def plot_Xarrows_at_borders(self, ax:Axes=None,
                                randomize:bool=False,
                                amplitudeX:np.ndarray=None,
                                amplitudeY:np.ndarray=None,
                                color='black', **kwargs):
        """ Plot arrows at the borders of the cells.
        """

        if ax is None:
            fig, ax = plt.subplots()
        else:
            fig = ax.figure

        [xmin, xmax], [ymin, ymax] = self.get_bounds()

        if amplitudeX is None:
            amplitudeX = np.ones((self.nbx+1, self.nby)) * 0.2 * self.dx
        else:
            if self._factor is not None:
                amplitudeX *= self._factor

        if amplitudeY is None:
            amplitudeY = np.ones((self.nbx, self.nby+1)) * 0.2 * self.dy
        else:
            if self._factor is not None:
                amplitudeY *= self._factor

        for y in np.linspace(ymin + self.dy/2., ymax - self.dy/2., endpoint=True, num=self.nby):
            for x in np.linspace(xmin, xmax, endpoint=True, num=self.nbx + 1):

                i,j = self.xy2ij(x, y)
                if randomize:
                    dx = np.random.uniform(-0.5, 0.5) * self.dx
                    amplitudeX[i,j] = dx
                else:
                    dx = amplitudeX[i,j]

                if dx != 0.:
                    ax.arrow(x - dx/2., y, dx, 0,
                            head_width=0.1 * self.dx, head_length=0.1 * self.dy,
                            fc=color, ec=color)

        for y in np.linspace(ymin, ymax, endpoint=True, num=self.nby+1):
            for x in np.linspace(xmin + self.dx/2., xmax - self.dx/2., endpoint=True, num=self.nbx):

                i,j = self.xy2ij(x, y)
                if randomize:
                    dx = np.random.uniform(-0.5, 0.5) * self.dy
                    amplitudeY[i,j] = dx
                else:
                    dx = amplitudeY[i,j]

                if dx != 0.:
                    ax.arrow(x - dx, y, dx, 0,
                            head_width=0.1 * self.dx, head_length=0.1 * self.dy,
                            fc=color, ec=color)

        self.set_aspect_labels(ax=ax, **kwargs)

        return fig, ax, amplitudeX, amplitudeY

    def plot_Yarrows_at_borders(self, ax:Axes=None,
                                randomize:bool=False,
                                amplitudeX:np.ndarray=None,
                                amplitudeY:np.ndarray=None,
                                color='black', **kwargs):
        """ Plot arrows at the borders of the cells.
        """

        if ax is None:
            fig, ax = plt.subplots()
        else:
            fig = ax.figure

        [xmin, xmax], [ymin, ymax] = self.get_bounds()

        if amplitudeX is None:
            amplitudeX = np.ones((self.nbx+1, self.nby)) * 0.2 * self.dx
        else:
            if self._factor is not None:
                amplitudeX *= self._factor

        if amplitudeY is None:
            amplitudeY = np.ones((self.nbx, self.nby+1)) * 0.2 * self.dy
        else:
            if self._factor is not None:
                amplitudeY *= self._factor

        for y in np.linspace(ymin, ymax, endpoint=True, num=self.nby + 1):
            for x in np.linspace(xmin + self.dx/2., xmax - self.dx/2., endpoint=True, num=self.nbx):

                i,j = self.xy2ij(x, y)
                if randomize:
                    dy = np.random.uniform(-0.5, 0.5) * self.dy
                    amplitudeY[i,j] = dy
                else:
                    dy = amplitudeY[i,j]

                if dy != 0.:
                    ax.arrow(x, y - dy/2., 0, dy,
                            head_width=0.1 * self.dx, head_length=0.1 * self.dy,
                            fc=color, ec=color)

        for y in np.linspace(ymin + self.dy/2., ymax - self.dy/2., endpoint=True, num=self.nby):
            for x in np.linspace(xmin, xmax, endpoint=True, num=self.nbx + 1):

                i,j = self.xy2ij(x, y)
                if randomize:
                    dy = np.random.uniform(-0.5, 0.5) * self.dx
                    amplitudeX[i,j] = dy
                else:
                    dy = amplitudeX[i,j]

                if dy != 0.:
                    ax.arrow(x, y - dy/2., 0., dy,
                            head_width=0.1 * self.dx, head_length=0.1 * self.dy,
                            fc=color, ec=color)

        self.set_aspect_labels(ax=ax, **kwargs)

        return fig, ax, amplitudeX, amplitudeY

    def plot_normal_arrows_at_borders(self, ax:Axes=None, color='black', **kwargs):
        """ Plot arrows at the borders of the cells.
        """

        if ax is None:
            fig, ax = plt.subplots()
        else:
            fig = ax.figure

        [xmin, xmax], [ymin, ymax] = self.get_bounds()

        for y in np.linspace(ymin + self.dy/2., ymax - self.dy/2., endpoint=True, num=self.nby):
            for x in np.linspace(xmin, xmax, endpoint=True, num=self.nbx+1):
                ax.arrow(x - 0.1 * self.dx, y, 0.2 * self.dx, 0,
                         head_width=0.1 * self.dx, head_length=0.1 * self.dy,
                         fc=color, ec=color)

        for y in np.linspace(ymin, ymax, endpoint=True, num=self.nby+1):
            for x in np.linspace(xmin + self.dx/2., xmax - self.dx/2., endpoint=True, num=self.nbx):
                ax.arrow(x, y - 0.1 * self.dy, 0., 0.2 * self.dy,
                         head_width=0.1 * self.dx, head_length=0.1 * self.dy,
                         fc=color, ec=color)

        self.set_aspect_labels(ax=ax, **kwargs)

        return fig, ax

    def scale_axes(self, ax:Axes=None, factor:float = 0.1, **kwargs):
        """ Scale the axes of the plot to fit the data.
        """
        # augmenter légèrement la taille visible sans
        # ajouter de ticks
        ticksX = ax.get_xticks()
        ticksY = ax.get_yticks()
        ticklabelsX = ax.get_xticklabels()
        ticklabelsY = ax.get_yticklabels()

        deltaX = ticksX[-1] - ticksX[0]
        deltaY = ticksY[-1] - ticksY[0]
        ax.set_xlim(ticksX[0] - factor * deltaX, ticksX[-1] + factor * deltaX)
        ax.set_ylim(ticksY[0] - factor * deltaY, ticksY[-1] + factor * deltaY)

        ax.set_xticks(ticksX)
        ax.set_yticks(ticksY)
        ax.set_xticklabels(ticklabelsX) #, rotation=45)
        ax.set_yticklabels(ticklabelsY) #, rotation=45)

        # remove up border and right border
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)

        return ax.figure, ax

    def plot_reconstructed_values_at_borders(self, ax:Axes=None,
                                             colors=['green', 'blue', 'red', 'brown'],
                                             radius:float = None, **kwargs):
        """ Plot 4 small circles on each side of the border.
        """

        if radius is None:
            radius = 0.02 * self.dx

        if ax is None:
            fig, ax = plt.subplots()
        else:
            fig = ax.figure

        [xmin, xmax], [ymin, ymax] = self.get_bounds()

        deltay = self.dy / 6.
        for y in np.linspace(ymin + self.dy/2., ymax - self.dy/2., endpoint=True, num=self.nby):
            x = xmin
            for i in range(4):
                ax.add_artist(plt.Circle((x+.1*self.dx, y - 1.5*deltay + i*deltay),
                                         radius=radius, color=colors[-i-1], **kwargs))
            x = xmax
            for i in range(4):
                ax.add_artist(plt.Circle((x-.1*self.dx, y - 1.5*deltay + i*deltay),
                                         radius=radius, color=colors[-i-1], **kwargs))

            for x in np.linspace(xmin + self.dx, xmax - self.dx, endpoint=True, num=self.nbx-1):
                for i in range(4):
                    ax.add_artist(plt.Circle((x+.1*self.dx, y - 1.5*deltay + i*deltay),
                                             radius=radius, color=colors[-i-1], **kwargs))
                    ax.add_artist(plt.Circle((x-.1*self.dx, y - 1.5*deltay + i*deltay),
                                             radius=radius, color=colors[-i-1], **kwargs))

        for x in np.linspace(xmin + self.dx/2., xmax - self.dx/2., endpoint=True, num=self.nbx):
            y = ymin
            for i in range(4):
                ax.add_artist(plt.Circle((x - 1.5*deltay + i*deltay, y+.1*self.dy),
                                         radius=radius, color=colors[i], **kwargs))
            y = ymax
            for i in range(4):
                ax.add_artist(plt.Circle((x - 1.5*deltay + i*deltay, y-.1*self.dy),
                                         radius=radius, color=colors[i], **kwargs))

            for y in np.linspace(ymin + self.dy, ymax - self.dy, endpoint=True, num=self.nby-1):
                for i in range(4):
                    ax.add_artist(plt.Circle((x - 1.5*deltay + i*deltay, y+.1*self.dy),
                                             radius=radius, color=colors[i], **kwargs))
                    ax.add_artist(plt.Circle((x - 1.5*deltay + i*deltay, y-.1*self.dy),
                                             radius=radius, color=colors[i], **kwargs))

        self.set_aspect_labels(ax=ax, **kwargs)

    def plot_splitted_values_at_borders(self, ax:Axes=None,
                                        qx:np.ndarray=None,
                                        qy:np.ndarray=None,
                                        colors=['green', 'blue', 'red', 'brown'],
                                        radius:float = None, **kwargs):
        """ Plot 4 small circles on each side of the border.
        """

        split_x = self.zeros_bordersX()
        split_y = self.zeros_bordersY()

        for i in range(1, self.nbx):
            for j in range(self.nby):
                split_x[i,j] = splitting_rule(qx[i-1,j], qx[i,j])
        for i in range(self.nbx):
            for j in range(1, self.nby):
                split_y[i,j] = splitting_rule(qy[i,j-1], qy[i,j])

        if radius is None:
            radius = 0.02 * self.dx

        if ax is None:
            fig, ax = plt.subplots()
        else:
            fig = ax.figure

        [xmin, xmax], [ymin, ymax] = self.get_bounds()

        deltay = self.dy / 6.

        # X borders
        for y in np.linspace(ymin + self.dy/2., ymax - self.dy/2., endpoint=True, num=self.nby):
            x = xmin
            i,j = self.xy2ij(x, y)
            for i_unk in range(4):
                ax.add_artist(plt.Circle((x+.1*self.dx, y - 1.5*deltay + i_unk*deltay),
                                         radius=radius, color=colors[-i_unk-1], **kwargs))
            x = xmax
            i,j = self.xy2ij(x, y)
            for i_unk in range(4):
                ax.add_artist(plt.Circle((x-.1*self.dx, y - 1.5*deltay + i_unk*deltay),
                                         radius=radius, color=colors[-i_unk-1], **kwargs))

            for x in np.linspace(xmin + self.dx, xmax - self.dx, endpoint=True, num=self.nbx-1):
                i,j = self.xy2ij(x, y)

                pond = split_x[i,j]
                if pond == 0.5:
                    for i_unk in range(4):
                        ax.add_artist(plt.Circle((x+.1*self.dx, y - 1.5*deltay + i_unk*deltay),
                                                radius=radius, color=colors[-i_unk-1], **kwargs))
                        ax.add_artist(plt.Circle((x-.1*self.dx, y - 1.5*deltay + i_unk*deltay),
                                                radius=radius, color=colors[-i_unk-1], **kwargs))
                elif pond == 1.0:
                    # left is upstream
                    for i_unk in [1,2]:
                        ax.add_artist(plt.Circle((x-.1*self.dx, y - 1.5*deltay + i_unk*deltay),
                                                radius=radius, color=colors[-i_unk-1], **kwargs))
                    for i_unk in [0,3]:
                        ax.add_artist(plt.Circle((x+.1*self.dx, y - 1.5*deltay + i_unk*deltay),
                                                radius=radius, color=colors[-i_unk-1], **kwargs))
                elif pond == 0.0:
                    # right is upstream
                    for i_unk in [0,3]:
                        ax.add_artist(plt.Circle((x-.1*self.dx, y - 1.5*deltay + i_unk*deltay),
                                                radius=radius, color=colors[-i_unk-1], **kwargs))
                    for i_unk in [1,2]:
                        ax.add_artist(plt.Circle((x+.1*self.dx, y - 1.5*deltay + i_unk*deltay),
                                                radius=radius, color=colors[-i_unk-1], **kwargs))

        # Y borders
        for x in np.linspace(xmin + self.dx/2., xmax - self.dx/2., endpoint=True, num=self.nbx):
            y = ymin
            i,j = self.xy2ij(x, y)
            for i_unk in range(4):
                ax.add_artist(plt.Circle((x - 1.5*deltay + i_unk*deltay, y+.1*self.dy),
                                         radius=radius, color=colors[i_unk], **kwargs))
            y = ymax
            i,j = self.xy2ij(x, y)
            for i_unk in range(4):
                ax.add_artist(plt.Circle((x - 1.5*deltay + i_unk*deltay, y-.1*self.dy),
                                         radius=radius, color=colors[i_unk], **kwargs))

            for y in np.linspace(ymin + self.dy, ymax - self.dy, endpoint=True, num=self.nby-1):
                i,j = self.xy2ij(x, y)
                pond = split_y[i,j]
                if pond == 0.5:
                    for i_unk in range(4):
                        ax.add_artist(plt.Circle((x - 1.5*deltay + i_unk*deltay, y+.1*self.dy),
                                                radius=radius, color=colors[i_unk], **kwargs))
                        ax.add_artist(plt.Circle((x - 1.5*deltay + i_unk*deltay, y-.1*self.dy),
                                                radius=radius, color=colors[i_unk], **kwargs))
                elif pond == 1.0:
                    for i_unk in [1,2]:
                        ax.add_artist(plt.Circle((x - 1.5*deltay + i_unk*deltay, y-.1*self.dy),
                                                radius=radius, color=colors[i_unk], **kwargs))
                    for i_unk in [0,3]:
                        ax.add_artist(plt.Circle((x - 1.5*deltay + i_unk*deltay, y+.1*self.dy),
                                                radius=radius, color=colors[i_unk], **kwargs))
                elif pond == 0.0:
                    for i_unk in [0,3]:
                        ax.add_artist(plt.Circle((x - 1.5*deltay + i_unk*deltay, y-.1*self.dy),
                                                radius=radius, color=colors[i_unk], **kwargs))
                    for i_unk in [1,2]:
                        ax.add_artist(plt.Circle((x - 1.5*deltay + i_unk*deltay, y+.1*self.dy),
                                                radius=radius, color=colors[i_unk], **kwargs))


        self.set_aspect_labels(ax=ax, **kwargs)

    def set_aspect_labels(self, ax:Axes=None, **kwargs):
        """ Set the aspect of the plot to be equal.
        """
        if ax is None:
            fig, ax = plt.subplots()
        else:
            fig = ax.figure

        [xmin, xmax], [ymin, ymax] = self.get_bounds()

        ax.set_aspect('equal')
        ax.set_xlim(xmin, xmax)
        ax.set_ylim(ymin, ymax)
        ax.set_xlabel('X (m)')
        ax.set_ylabel('Y (m)')
        return fig, ax
    
    def set_aspect_labels_matrice(self, ax:Axes=None, **kwargs):
        """ Set the aspect of the plot to be equal.
        """
        if ax is None:
            fig, ax = plt.subplots()
        else:
            fig = ax.figure

        [xmin, xmax], [ymin, ymax] = self.get_bounds()

        ax.set_aspect('equal')
        ax.set_ylim(xmin, xmax)
        ax.set_xlim(ymin, ymax)
        ax.set_xlabel('columns')
        ax.set_ylabel('rows')

        #set x ais on the upper side
        ax.xaxis.set_ticks_position('top')
        ax.xaxis.set_label_position('top')
        return fig, ax

    def zeros(self):
        """ Return a 2D array of zeros with the shape of the mesh.
        """
        return np.zeros((self.nbx, self.nby))

    def ones(self):
        """ Return a 2D array of ones with the shape of the mesh.
        """
        return np.ones((self.nbx, self.nby))

    def zeros_bordersX(self):
        """ Return a 2D array of zeros with the shape of the mesh + 1 in x direction.
        """
        return np.zeros((self.nbx+1, self.nby))

    def zeros_bordersY(self):
        """ Return a 2D array of zeros with the shape of the mesh + 1 in y direction.
        """
        return np.zeros((self.nbx, self.nby+1))

    def ones_bordersX(self):
        """ Return a 2D array of ones with the shape of the mesh + 1 in x direction.
        """
        return np.ones((self.nbx+1, self.nby))

    def ones_bordersY(self):
        """ Return a 2D array of ones with the shape of the mesh + 1 in y direction.
        """
        return np.ones((self.nbx, self.nby+1))

    def apply_splitting_X(self, q:np.ndarray):
        """ Apply the splitting rule to the X direction.
        """
        q_borderX = self.zeros_bordersX()
        for i in range(1,self.nbx):
            for j in range(self.nby):
                q_borderX[i,j] = q_splitting(q[i-1,j], q[i,j])
        return q_borderX

    def apply_splitting_Y(self, q:np.ndarray):
        """ Apply the splitting rule to the Y direction.
        """
        q_borderY = self.zeros_bordersY()
        for i in range(self.nbx):
            for j in range(1,self.nby):
                q_borderY[i,j] = q_splitting(q[i,j-1], q[i,j])
        return q_borderY

    def scale_amplitude(self, amplitude:np.ndarray, factor:float = None):
        """ Scale the amplitude of the arrows.
        """

        if self._factor is not None:
            return amplitude * self._factor

        if factor is not None:
                return amplitude * factor

        factor = min(self.dx, self.dy) * .5 / np.max(amplitude)
        self._factor = factor

        return amplitude * factor

    def plot_outside_domain(self, ax:Axes=None, color='black', **kwargs):
        """ Plot a hashed zone outside of the domain.
        """
        if ax is None:
            fig, ax = plt.subplots()
        else:
            fig = ax.figure

        [xmin, xmax], [ymin, ymax] = self.get_bounds()

        # Create a rectangle outside the domain
        rect = plt.Rectangle((xmin-self.dx, ymin-self.dy), xmax - xmin + 2.*self.dx, ymax - ymin + 2.*self.dy,
                     color=color, alpha=0.2, hatch='//', **kwargs)
        ax.add_patch(rect)

        rect2 = plt.Rectangle((xmin, ymin), xmax - xmin, ymax - ymin,
                     color='white', alpha=1., hatch='', **kwargs)
        ax.add_patch(rect2)

        return fig, ax