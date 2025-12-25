import numpy as np
import math
import matplotlib.pyplot as plt

class MaxwellHydrographSwitzerland:

    def __init__(self, qmax:float, tmax:float, n:float = 6):
        """ Initialize the Maxwell hydrograph with given parameters.

        :qmax: Maximum flow rate [m**3/s]
        :tmax: Time to reach maximum flow [s]
        :n: Shape parameter (default is 6)
        """
        self.qmax = qmax
        self.tmax = tmax
        self.n = n

    def _flow_at_time(self, t:float) -> float:
        """ Compute the flow at a given time t based on the Maxwell hydrograph formula.
        """
        if t < 0:
            return 0.0
        else:
            return self.qmax * (t/self.tmax * np.exp(1-(t/self.tmax)))**self.n

    def volume(self) -> float:
        """ Compute the total volume under the hydrograph.
        """
        return self.qmax * self.tmax *np.exp(self.n) * math.factorial(self.n) / (self.n ** (self.n + 1))

    def set_qmax_from_volume_and_tmax(self, volume:float, tmax:float):
        """ Set qmax based on the desired volume and tmax.
        """
        self.tmax = tmax
        self.qmax = volume * (self.n ** (self.n + 1)) / (tmax * np.exp(self.n) * math.factorial(self.n))

    def discretized_hydrograph(self, duration:float, time_step:float) -> tuple[np.ndarray, np.ndarray]:
        """ Generate discretized time and flow arrays for the hydrograph.
        """
        time_array = np.arange(0, duration, time_step)
        flow_array = np.zeros_like(time_array)
        for i, t in enumerate(time_array):
            flow_array[i] = self._flow_at_time(t)
        return time_array, flow_array

    def plot_hydrograph(self, duration:float, time_step:float, figaxe=None):
        """ Plot the hydrograph over a specified duration and time step.
        """
        time_array, flow_array = self.discretized_hydrograph(duration, time_step)

        if figaxe is None:
            fig, ax = plt.subplots()
        else:
            fig, ax = figaxe

        ax.plot(time_array, flow_array, label='Maxwell Hydrograph (Switzerland)')
        ax.set_xlabel('Time')
        ax.set_ylabel('Flow')
        ax.set_title('Maxwell Hydrograph (Switzerland)')
        ax.legend()

        return fig, ax

    def set_parameters(self, qmax:float, tmax:float, n:float):
        """ Set the parameters of the Maxwell hydrograph.
        """
        self.qmax = qmax
        self.tmax = tmax
        self.n = n

    def get_parameters(self) -> tuple[float, float, float]:
        """ Return the parameters of the Maxwell hydrograph.
        """
        return (self.qmax, self.tmax, self.n)

class _MaxwellHydrographGas:

    def __init__(self, K:float, t_concentration:float):
        self.K = K
        self.t_concentration = t_concentration

    def convolve_rainfall(self, rainfall_intensity:np.ndarray, time_step:float) -> np.ndarray:
        """ Convolve the rainfall intensity array with the Maxwell hydrograph to produce the runoff hydrograph.
        """
        duration = len(rainfall_intensity) * time_step
        time_array, unit_hydrograph = self.discretized_unit_hydrograph(duration, time_step)

        runoff_hydrograph = np.convolve(rainfall_intensity, unit_hydrograph)[:len(rainfall_intensity)] * time_step
        return runoff_hydrograph

    def deconvolve_runoff(self, runoff_hydrograph:np.ndarray, time_step:float) -> np.ndarray:
        """ Deconvolve the runoff hydrograph to estimate the rainfall intensity array.
        """
        duration = len(runoff_hydrograph) * time_step
        time_array, unit_hydrograph = self.discretized_unit_hydrograph(duration, time_step)

        # Avoid division by zero in frequency domain
        H_f = np.fft.fft(unit_hydrograph)
        H_f[np.abs(H_f) < 1e-10] = 1e-10

        R_f = np.fft.fft(runoff_hydrograph)
        I_f = R_f / H_f

        estimated_rainfall_intensity = np.fft.ifft(I_f).real
        return estimated_rainfall_intensity[:len(runoff_hydrograph)]

    def optimize_parameters(self, observed_runoff:np.ndarray,
                            rainfall_intensity:np.ndarray,
                            time_step:float,
                            initial_guess:tuple[float, float],
                            bounds:tuple[tuple[float, float], tuple[float, float]]) -> tuple[float, float]:
        """ Optimize the Maxwell hydrograph parameters (K and t_concentration) to fit observed runoff data.
        """
        from scipy.optimize import minimize

        def objective(params):
            K, t_conc = params
            self.K = K
            self.t_concentration = t_conc
            simulated_runoff = self.convolve_rainfall(rainfall_intensity, time_step)
            return np.sum((simulated_runoff - observed_runoff)**2)

        result = minimize(objective, initial_guess, bounds=bounds)
        self.K, self.t_concentration = result.x
        return self.K, self.t_concentration

    def _flow_at_time(self, t:float) -> float:
        """ Compute the flow at a given time t based on the Maxwell hydrograph formula.
        """
        if t < 0:
            return 0.0
        else:
            return self.K * (t**2. / self.t_concentration**3.) * np.exp(-0.5 * (t / self.t_concentration)**2.)

    def _unit_hydrograph_over_time(self, time_array:np.ndarray) -> np.ndarray:
        """ Compute the hydrograph over an array of time values.
        """
        flow_array = np.zeros_like(time_array)
        for i, t in enumerate(time_array):
            flow_array[i] = self._flow_at_time(t)
        return flow_array

    def discretized_unit_hydrograph(self, duration:float, time_step:float) -> tuple[np.ndarray, np.ndarray]:
        """ Generate discretized time and flow arrays for the hydrograph.
        """
        time_array = np.arange(0, duration, time_step)
        flow_array = self._unit_hydrograph_over_time(time_array)
        # normalize to unit volume - integration using constant value over time step
        volume = np.sum(flow_array) * time_step
        flow_array /= volume
        return time_array, flow_array

    def get_parameters(self) -> tuple[float, float]:
        """ Return the parameters of the Maxwell hydrograph.
        """
        return (self.K, self.t_concentration)

    def set_parameters(self, K:float, t_concentration:float):
        """ Set the parameters of the Maxwell hydrograph.
        """
        self.K = K
        self.t_concentration = t_concentration

    def print_hydrograph_info(self):
        """ Print the hydrograph parameters and characteristics.
        """
        print(f"Maxwell Hydrograph Parameters:")
        print(f"  Parameter K: {self.K}")
        print(f"  Time of Concentration (t_concentration): {self.t_concentration}")

    def plot_hydrograph(self, duration:float, time_step:float, figaxe=None):
        """ Plot the hydrograph over a specified duration and time step.
        """
        time_array, flow_array = self.discretized_unit_hydrograph(duration, time_step)

        if figaxe is None:
            fig, ax = plt.subplots()
        else:
            fig, ax = figaxe

        ax.plot(time_array, flow_array, label='Maxwell Hydrograph')
        ax.set_xlabel('Time')
        ax.set_ylabel('Flow')
        ax.set_title('Maxwell Hydrograph')
        ax.legend()

        return fig, ax

if __name__ == "__main__":
    # Example usage
    hydrograph = MaxwellHydrographSwitzerland(qmax = 150., tmax = 3600., n=6)
    time_array, flow_array = hydrograph.discretized_hydrograph(duration=7200.0, time_step=60.0)

    fig,ax = hydrograph.plot_hydrograph(duration=7200.0, time_step=60.0)
    fig.show()
    pass