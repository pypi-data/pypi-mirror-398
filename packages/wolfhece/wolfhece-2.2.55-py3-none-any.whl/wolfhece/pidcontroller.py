import numpy as np

class PIDController:
    """
    Tuning a PID controller -- https://dewesoft.com/blog/what-is-pid-controller

    Tuning the PID parameters Kp, Ki and Kd is crucial in PID controller design. 
    Tuning must be customized for each of the many PID applications. 
    Key tuning parameters include:

     - Proportional Gain (Kp): This parameter determines the proportion of 
       the error signal contributing to the controller output. A higher  
       Kp value results in a stronger response to the current error. 
       Too high a Kp can lead to oscillations or instability, while too 
       low a value can result in a sluggish response.

     - Integral Gain (Ki): The integral term considers the accumulation 
       of past errors and amplifies them over time. It helps eliminate 
       steady-state error by continuously adjusting the control signal. 
       A higher Ki value helps reduce steady-state error but can lead 
       to overshoot or instability if set too high.

     - Derivative Gain (Kd): The derivative term predicts the future behavior 
       of the error based on its current rate of change. It helps dampen 
       oscillations by counteracting rapid changes in the error signal. 
       Increasing Kd enhances damping and reduces overshoot, but too high 
       a value can lead to instability or sensitivity to noise.

    The tuning process involves adjusting these parameters to achieve 
    desired system performance, such as stability, responsiveness, 
    and minimal overshoot. Several methods are used for PID tuning, 
    including manual tuning, Ziegler-Nichols method, and optimization 
    algorithms. Let’s take a closer look at each of these methods:

    In manual tuning, the engineer adjusts the parameters based on their 
    understanding of the system dynamics and the desired performance criteria. 
    This method involves iteratively tweaking the parameters while observing 
    the system's response until satisfactory performance is achieved.

    The Ziegler-Nichols Method provides a systematic approach to PID 
    tuning based on step response experiments. The integral and derivative 
    gains are set to zero and gradually increased until the system oscillates 
    at a constant amplitude. The proportional gain and oscillation period 
    are determined from the oscillation period and amplitude, which are 
    then used to calculate suitable PID parameters. Several other tuning 
    methods exist, including Cohen-Coon, Lambda, and Dead Time. 

    Optimization algorithms such as gradient descent, genetic algorithms, 
    or particle swarm optimization automatically search for optimal PID 
    parameters based on specified performance criteria and system models.

    PID tuning is a critical step in control system design. It ensures 
    that the controller effectively regulates the system while meeting 
    performance requirements.    
    """

    def __init__(self, kp, ki, kd):
        """
        Initialize the PID controller with given coefficients.

        :params kp (float): Proportional gain coefficient.
        :params ki (float): Integral gain coefficient.
        :params kd (float): Derivative gain coefficient.
        """

        self.kp = kp
        self.ki = ki
        self.kd = kd
        self.error_sum = 0
        self.last_error = 0

    def calculate(self, setpoint, feedback):
        """ Compute the PID response.
        
        :param setpoint: Objective value to achieve.
        :type setpoint: float
        :param feedback: Current measured value.
        :type feedback: float
        :return: PID control output.
        :rtype: float
        """ 

        error = setpoint - feedback
        self.error_sum += error
        error_diff = error - self.last_error
        self.last_error = error

        p = self.kp * error
        i = self.ki * self.error_sum
        d = self.kd * error_diff

        return p + i + d

if __name__ == "__main__":    

    import matplotlib.pyplot as plt

    # Create a PIDController instance
    pid_controller = PIDController(kp=0.5, ki=0.1, kd=.5)

    # Define time range and step size
    t_start = 0
    t_end = 10
    dt = 0.1

    # Initialize lists to store time and output values
    time = []
    output = []
    measures = [1]

    # Simulate the system over time
    for t in np.arange(t_start, t_end, dt):
        # Calculate the output using the PID controller
        setpoint = 10  # Example setpoint
        control_signal = pid_controller.calculate(setpoint, measures[-1])

        # Simulate the system dynamics
        # In a real-world application, this would be replaced by actual measurements
        measures.append(measures[-1] + .4 * control_signal)
        
        # Store the time and output values
        time.append(t)
        output.append(control_signal)

    # Plot the output over time
    plt.plot(time, measures[1:], label='System Output')
    plt.xlabel('Time')
    plt.ylabel('Output')
    plt.title('PID Controller Output')
    plt.grid(True)
    plt.show()