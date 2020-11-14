import tkinter as tk
import math
from transport_graph import Network, Stop, Connection


class SimulationGUI:
    '''
    Class that handles displaying the network to the user.
    '''

    def __init__(self, network, width=500, buffer=20):
        self.network = network
        self.buffer = buffer
        self.setup_canvas()

        self.width = width
    
    def setup_canvas(self):
        self.get_lat_long_constants()

        #setup tkinter window
        self.window = tk.Tk()
        self.window.title = ("UQ to Indooroopilly Network Simulation")
        self.window.geometry(f'{self.width}x{self.height}')

        #setup tkinter canvas
        self.canvas = tk.Canvas(self.window)
        self.canvas.configure(bg="black")
        self.canvas.pack(fill="both", expand=True)
    
    
    
    def get_lat_long_constants(self):
        lat_max = -500.0
        lat_min = 500.0
        lon_max = -500.0
        lon_min = 500.0
        for stop in network.stops:
            lat_max = max(lat_max, stop.lat)
            lat_min = min(lat_min, stop.lat)
            lon_max = max(lon_max, stop.lon)
            lon_min = min(lon_min, stop.lon)

        lat_diff = lat_max - lat_min
        lon_diff = lon_max - lon_min

        #get height of screen
        self.lat_lon_scalar = (self.width - 2*self.buffer)/lon_diff
        self.height = math.ceil(self.lat_lon_scalar*lat_diff + 2*self.buffer)
        self.lat_offset = lat_min
        self.lon_offset = lon_min
    
    def lon_to_x(self, lon):
        '''
        convert from longitude to x position in graph
        '''
        return math.floor(self.buffer + (lon-self.lon_offset) * self.lat_lon_scalar)
    
    def lat_to_y(self, lat):
        '''
        convert from latitude to y position in graph
        '''
        return math.floor(self.height - self.buffer - ((lat - self.lat_offset)*self.lat_lon_scalar))


    
    def start_simulation(self):

