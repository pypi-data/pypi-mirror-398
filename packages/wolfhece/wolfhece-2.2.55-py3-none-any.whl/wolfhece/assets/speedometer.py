import matplotlib.pyplot as plt
import numpy as np
from matplotlib.colors import LinearSegmentedColormap



class Semi_Circle_Gauge():

    def __init__(self):
        # Create a polar plot for the speedometer background
        self.fig, self.ax = plt.subplots(figsize=(6, 3), subplot_kw={'projection': 'polar'})
        self.ax.set_theta_zero_location('W')
        self.ax.set_theta_direction(-1)

    def plot_background(self):                
        # Define the ranges for red, yellow, and green
        theta = np.linspace(0, np.pi, 500)
        # Create metallic gradient for green with highlights for a modern effect
        green_cmap = LinearSegmentedColormap.from_list(
            "metallic_green", ["#003300", "#00FF00", "#66FF66", "#00FF00", "#003300"]
        )
        green_colors = green_cmap(np.linspace(0, 1, 500))
        self.ax.fill_between(theta, 0, 1, where=(theta <= np.pi/3), color=None, alpha=0.7, facecolor=green_colors)
        # green_cmap = LinearSegmentedColormap.from_list("metallic_green", ["#006400", "#00FF00", "#006400"])
        # green_colors = green_cmap(np.linspace(0, 1, 500))
        # ax.fill_between(theta, 0, 1, where=(theta <= np.pi/3), color=None, alpha=0.7, facecolor=green_colors)

        # Create metallic gradient for yellow
        yellow_cmap = LinearSegmentedColormap.from_list("metallic_yellow", ["#FFD700", "#FFFF00", "#FFD700"])
        yellow_colors = yellow_cmap(np.linspace(0, 1, 500))
        self.ax.fill_between(theta, 0, 1, where=((theta > np.pi/3) & (theta <= 2*np.pi/3)), color=None, alpha=0.7, facecolor=yellow_colors)

        # Create metallic gradient for red
        red_cmap = LinearSegmentedColormap.from_list("metallic_red", ["#8B0000", "#FF0000", "#8B0000"])
        red_colors = red_cmap(np.linspace(0, 1, 500))
        self.ax.fill_between(theta, 0, 1, where=(theta > 2*np.pi/3), color=None, alpha=0.7, facecolor=red_colors)

        # Remove polar grid and labels for a clean look
        self.ax.grid(False)
        self.ax.set_yticks([])
        self.ax.set_xticks([])

        self.ax.set_ylim(0, 1)
        self.ax.set_xlim(0, np.pi)

    def plot_needle(self, value, color='black'):
        # Add a needle to indicate a specific value
        width = 0.1  # Needle width
        self.ax.fill([value, value-width, value, value+width, value], 
                [0, .25, .9, .25, 0], color='black', linewidth=2, zorder=5)
        self.ax.plot([value, value+width*.9, value], 
                [.9, .25, 0], color='grey', linewidth=2, zorder=6)
        self.ax.plot([value, value+width, value], 
                [.9, .25, 0], color='white', linewidth=1, zorder=6)
        # Plot a black semi-circle at the origin
        semi_circle = plt.Circle((0, 0), 0.1, transform=self.ax.transData._b, color='black', zorder=7)
        self.ax.add_artist(semi_circle)

    def plot_text(self, text, value):
        # Add text to the speedometer
        # The text is above the speedometer in the center
        # The value is the angle of the needle
        self.ax.text(np.pi/2., 1.15, text, fontsize=12, ha='center', va='center', color='black')

class Rectangular_Gauge():

    def __init__(self, horizontal_or_vertical='vertical'):
        # Create a rectangular plot for the speedometer background

        if horizontal_or_vertical == 'horizontal':
            self.fig, self.ax = plt.subplots(figsize=(6, 3))
            self.direction = 'horizontal'
        else:
            # Default to vertical if not specified
            self.fig, self.ax = plt.subplots(figsize=(3, 6))
            self.direction = 'vertical'

        self.ax.set_xlim(0, 1)
        self.ax.set_ylim(0, 1)

    def plot_background(self):
        # Define the ranges for red, yellow, and green

        if self.direction == 'horizontal':
            # Horizontal speedometer
            self.ax.fill_between([0, 1/3], 0, 1, color='green', alpha=0.7)
            self.ax.fill_between([1/3, 2/3], 0, 1, color='yellow', alpha=0.7)
            self.ax.fill_between([2/3, 1], 0, 1, color='red', alpha=0.7)
        else:
            # Vertical speedometer
            self.ax.fill_between([0, 1], 0, 1/3, color='green', alpha=0.7)
            self.ax.fill_between([0, 1], 1/3, 2/3, color='yellow', alpha=0.7)
            self.ax.fill_between([0, 1], 2/3, 1, color='red', alpha=0.7)

        # Remove grid and ticks for a clean look
        self.ax.grid(False)
        self.ax.set_xticks([])
        self.ax.set_yticks([])

    def plot_needle(self, value):
        # Add a needle to indicate a specific value
        width = 0.01  # Needle width

        if self.direction == 'horizontal':
            # Horizontal speedometer
            self.ax.fill([value-width, value+width, value+width, value-width],
                         [0.25, 0.25, 0.9, 0.9], color='black', linewidth=2)
        else:
            # Vertical speedometer
            self.ax.fill([0, 1, 1, 0],
                            [value-width, value-width, value+width, value+width], color='black', linewidth=2)

    def plot_text(self, text, value):
        # Add text to the speedometer
        self.ax.text(0.5, 1.15, text, fontsize=12, ha='center', va='center', color='black')




if __name__ == "__main__":
    # Test the speedometer function
    fig = Semi_Circle_Gauge()
    import matplotlib.animation as animation

    def update(frame):
        fig.ax.clear()
        fig.plot_background()  # Reinitialize the speedometer to clear previous needle
        fig.plot_needle(frame)
        fig.plot_text("Danger: {:.2f}".format(frame), frame)

    # Create an animation with values ranging from 0 to π
    ani = animation.FuncAnimation(fig.fig, update, frames=np.linspace(0, np.pi, 100), interval=50)

    plt.show()
    pass