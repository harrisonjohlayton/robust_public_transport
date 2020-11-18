import tkinter as tk
import math

from tkinter.font import Font
from transport_graph import Network, Stop, Connection

CONNECTION_WIDTH = 2
CONNECTION_UP_COLOR = '#090'
CONNECTION_DOWN_COLOR = '#900'

STOP_RADIUS = 20
STOP_WIDTH = 25
STOP_HEIGHT = 8
STOP_FONT_SIZE = 8
STOP_COLOR = '#00f'
START_STOP_COLOR = '#099'
END_STOP_COLOR = '#990'
STOP_TEXT_COLOR = 'white'
STOP_DOWN_COLOR = '#900'

BUS_WIDTH=10
BUS_COLOR='#ff0'


class SimulationGUI:
    '''
    Class that handles displaying the network to the user.
    '''

    def __init__(self, network, width=2000, buffer=50):
        self.network = network
        self.buffer = buffer
        self.width = width

        #dictionary to hold UI elements
        self.stop_dict = dict()
        self.connection_dict = dict()
        self.bus_dict = dict()

        #setup canvas and draw initial shapes
        self.setup_canvas()

    
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

        #setup time
        time_font = Font(size=20)
        self.time_stamp = self.canvas.create_text(self.width/2, self.height*0.1, text='3:00:00 PM', fill="#fff", font=time_font)
        #setup water level
        self.water_level_indicator = self.canvas.create_text(self.width/2, self.height*0.15, text='water level: 0.0m', fill='#fff',font=time_font)
    
        # setup connections and add to dict
        for connection in self.network.connections:
            next_x_1 = self.lon_to_x(connection.stop_1.lon)
            next_y_1 = self.lat_to_y(connection.stop_1.lat)
            next_x_2 = self.lon_to_x(connection.stop_2.lon)
            next_y_2 = self.lat_to_y(connection.stop_2.lat)
            next_connection_line = self.canvas.create_line(next_x_1, next_y_1, next_x_2, next_y_2,
                fill=CONNECTION_UP_COLOR, width=CONNECTION_WIDTH)
            self.connection_dict[connection] = next_connection_line

        #setup stops and add to dict
        for stop in self.network.stops:
            if (stop == self.network.indooroopilly_interchange or
                stop == self.network.chancellors_place):
                continue
            next_x = self.lon_to_x(stop.lon)
            next_y = self.lat_to_y(stop.lat)
            next_stop_shape = self.canvas.create_rectangle(next_x - STOP_WIDTH,
                    next_y - STOP_HEIGHT, next_x + STOP_WIDTH, next_y + STOP_HEIGHT, fill=STOP_COLOR) 
            if (stop.id < 0):
                next_stop_text = self.canvas.create_text(next_x, next_y, text='DETOUR', fill=STOP_TEXT_COLOR)
            else:
                next_stop_text = self.canvas.create_text(next_x, next_y, text=str(stop), fill=STOP_TEXT_COLOR)
            self.stop_dict[stop] = [next_stop_shape, next_stop_text]
        #setup start stop
        next_x = self.lon_to_x(self.network.chancellors_place.lon)
        next_y = self.lat_to_y(self.network.chancellors_place.lat)
        next_stop_shape = self.canvas.create_oval(next_x - STOP_RADIUS,
                next_y - STOP_RADIUS, next_x + STOP_RADIUS, next_y + STOP_RADIUS, fill=START_STOP_COLOR) 
        next_stop_text = self.canvas.create_text(next_x, next_y, text=str(self.network.chancellors_place), fill=STOP_TEXT_COLOR)
        self.stop_dict[self.network.chancellors_place] = [next_stop_shape, next_stop_text]
        #setup end stop
        next_x = self.lon_to_x(self.network.indooroopilly_interchange.lon)
        next_y = self.lat_to_y(self.network.indooroopilly_interchange.lat)
        next_stop_shape = self.canvas.create_oval(next_x - STOP_RADIUS,
                next_y - STOP_RADIUS, next_x + STOP_RADIUS, next_y + STOP_RADIUS, fill=END_STOP_COLOR) 
        next_stop_text = self.canvas.create_text(next_x, next_y, text=str(self.network.indooroopilly_interchange), fill=STOP_TEXT_COLOR)
        self.stop_dict[self.network.indooroopilly_interchange] = [next_stop_shape, next_stop_text]

    
    def get_lat_long_constants(self):
        lat_max = -500.0
        lat_min = 500.0
        lon_max = -500.0
        lon_min = 500.0
        for stop in self.network.stops:
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
    
    def get_hours_minutes_seconds(self, time):
        seconds = time%60
        time = (time - seconds)/60
        minutes = time % 60
        time = (time - minutes)/60
        hours = 3 + time

        return int(hours), int(minutes), int(seconds)
    
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
    
    def update(self, current_water_level, current_time):
        '''
        update the view to reflect the new graph
        '''
        self.update_stops(current_water_level)
        self.update_connections(current_water_level)
        self.update_buses()
        self.update_text(current_time, current_water_level)
        self.canvas.update()

    def update_text(self, current_time, current_water_level):
        '''
        update time stamp and water level
        '''
        hours, minutes, seconds = self.get_hours_minutes_seconds(current_time)
        time_string = "{:01d}:{:02d}:{:02d} PM".format(hours, minutes, seconds)
        self.canvas.itemconfig(self.time_stamp, text=time_string)

        water_level_text = "water level: {:02.1f}m".format(current_water_level)
        self.canvas.itemconfig(self.water_level_indicator, text=water_level_text)
    
    def update_stops(self, current_water_level):
        '''
        update the stops for new tick
        '''
        for stop in self.stop_dict.keys():
            self.update_stop(stop, current_water_level)
    
    def update_stop(self, stop, current_water_level):
        #if stop is above water and at least one connection is above water, return
        if stop.elevation > current_water_level:
            return
            # for connection in self.network.get_connections_for_stop(stop):
            #     if connection.elevation > current_water_level:
            #         return
        rect = self.stop_dict[stop][0]
        self.canvas.itemconfig(rect, fill=STOP_DOWN_COLOR)


    def update_connections(self, current_water_level):
        '''
        update connections for new tick
        '''
        for connection in self.connection_dict.keys():
            if ((connection.stop_1.elevation <= current_water_level) or
                    (connection.stop_2.elevation <= current_water_level) or 
                    (connection.elevation <= current_water_level)):
                line = self.connection_dict[connection]
                self.canvas.itemconfig(line, fill=CONNECTION_DOWN_COLOR, dash=(5,5))

    def update_buses(self):
        '''
        update buses for new tick
        '''
        # print(f'WIDTH : {self.width}\t\tHEIGHT : {self.height}')
        for bus in self.network.buses:
            if (bus.done):
                if (bus in self.bus_dict.keys()):
                    rect = self.bus_dict[bus]
                    self.canvas.delete(rect)
                    self.bus_dict.pop(bus, None)
            elif (bus.departed):
                #bus in progress
                if (bus in self.bus_dict.keys()):
                    #update bus
                    next_x = self.lon_to_x(bus.lon)
                    next_y = self.lat_to_y(bus.lat)
                    rect = self.bus_dict[bus]
                    self.canvas.coords(rect, next_x - BUS_WIDTH, next_y - BUS_WIDTH,
                        next_x + BUS_WIDTH, next_y + BUS_WIDTH)
                else:
                    #create new bus
                    next_x = self.lon_to_x(bus.lon)
                    next_y = self.lat_to_y(bus.lat)
                    rect = self.canvas.create_oval(next_x - BUS_WIDTH,
                            next_y - BUS_WIDTH, next_x + BUS_WIDTH, next_y + BUS_WIDTH, fill=BUS_COLOR) 
                    self.bus_dict[bus] = rect
                # print(f'{bus.lon} : {next_x}\t\t{bus.lat} : {next_y}')
                # print(f'{next_x}, {next_y}')

    
    # def start_simulation(self):

