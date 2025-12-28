import numpy as np


def sin_wave(f: float, A: float, phi: float, t: float) -> float:
    
    return A*np.sin(2*np.pi*f*t + phi*(np.pi/180))

def square_wave1(frequency, duty_cycle, max_value, min_value, duration, sampling_rate):
    """
    Generate a square wave signal.
    
    Parameters:
    frequency (float): Frequency of the square wave in Hz
    duty_cycle (float): Duty cycle of the square wave (0 to 1)
    max_value (float): Maximum value of the square wave
    min_value (float): Minimum value of the square wave
    duration (float): Duration of the signal in seconds
    sampling_rate (float): Sampling rate in samples per second
    
    Returns:
    t (numpy array): Time array
    square_wave (numpy array): Square wave signal
    """
    t = np.linspace(0, duration, int(sampling_rate * duration), endpoint=False)
    period = 1.0 / frequency
    square_wave = np.where((t % period) < (duty_cycle * period), max_value, min_value)
    return t, square_wave

def square_wave(frequency, duty_cycle, max_value, min_value, t):
    """
    Generate a square wave signal.
    
    Parameters:
    frequency (float): Frequency of the square wave in Hz
    duty_cycle (float): Duty cycle of the square wave (0 to 1)
    max_value (float): Maximum value of the square wave
    min_value (float): Minimum value of the square wave
    t (float  or numpy array): Time array
    
    Returns:
    square_wave (float  or numpy array): Square wave signal
    """
    period = 1.0 / frequency
    square_wave = np.where((t % period) < (duty_cycle * period), max_value, min_value)
    return square_wave


if __name__ == '__main__':
    import matplotlib.pyplot as plt
    t = []
    y2=[]
    y3=[]
    # t,y2 = square_wave(20,0.5,1,-1,1,1000)
    duration=5
    sampling_rate=1000
    for i in range(duration*sampling_rate):
        t.append(i/sampling_rate)
    
        y2.append(square_wave(60, 0.5,1,-1, i/sampling_rate))
        y3.append(sin_wave(60, 1, 0, i/sampling_rate)) 
    
    plt.xlabel('time')
    plt.ylabel('amplitude')
    plt.grid()
    plt.plot(t,y2)
    plt.plot(t,y3)
    plt.show()
    
   