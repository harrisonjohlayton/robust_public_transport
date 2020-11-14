from utils import get_altitude, read_route_file

CHANCELLORS_PLACE_IDS = [1798, 1799, 1801]
INDOOROOPILLY_IDS = [2004, 2205]

class Stop():
    '''
    Represents a bus stop. This is a vertex in the graph.
    '''
    
    def __init__(self, id, name:str, lat:float, lon:float):
        self.id = id
        self.name = name
        self.lat = lat
        self.lon = lon
        self.altitude = get_altitude(lat, lon)
        self.people = []
    
    def __str__(self):
        # return str(f'{self.name}, lat:{self.lat}, lon:{self.lon}')
        return str(f'{self.id}')


class Connection():
    '''
    Represents a series of roads connecting a bus stop. This is an
    edge in the graph.
    '''

    def __init__(self, stop_1, stop_2, time:int):
        self.stop_1 = stop_1
        self.stop_2 = stop_2
        self.altitude = get_altitude((stop_1.lat + stop_2.lat)/2,
            (stop_1.lon + stop_2.lon)/2)
        self.time=time

    def __str__(self):
        return f'{self.stop_1} <- {self.time}s -> {self.stop_2}'

class Route():
    '''
    Represents a bus route. This is a series of bus stops that must be
    visited.

    In the graph, this represents the shortest path starting at
    the vertiex origin_stop that contains all vertices in required_stops
    '''

    def __init__(self, route_num:int, first_stop, network):
        self.route_num=route_num
        self.origin_stop = first_stop
        self.current_route = []
        self.required_stops = [self.origin_stop]
        self.parent_network = network
    
    def add_required_stop(self, stop):
        self.required_stops.append(stop)
    
    def calculate_path(self):
        '''
        if the network is not distaster resistant, sets current_route to
        required_stops and returns True if the route is still connected given
        current water levels

        if the network is disaster resistant, dynamically calculates shortest path
        containing all stops in required_stops
        '''
        if (self.parent_network.disaster_resistant):
            #not implemented
            raise NotImplementedError('disaster resistance not implemented')
        else:
            self.current_route = self.required_stops.copy()
            #check if route still works (not implemented)
            return True
            
    def __str__(self):
        return str(self.route_num)
    

# class Passenger():

#     def __init__(self, origin_stop, dest_stop):

# class Bus():
#


class Network():
    '''
    class representing the graph containing the state of the transport network.
    '''

    def __init__(self, disaster_resistant=False):
        self.disaster_resistant = disaster_resistant
        self.chancellors_place = Stop(1799, 'Chancellors Place', -27.497974, 153.011139)
        self.indooroopilly_interchange = Stop(2205, 'Indooroopilly Shopping Center', -27.500941, 152.971946)
        self.connections = []
        self.routes = []
        self.stops = [self.indooroopilly_interchange, self.chancellors_place]

        #add routes
        self.add_route('data/raw_data/route_414.csv', 414)
        self.add_route('data/raw_data/route_427.csv', 427)
        self.add_route('data/raw_data/route_428.csv', 428)
        self.add_route('data/raw_data/route_432.csv', 432)
    
    def add_route(self, route_filename:str, route_num:int):
        '''
        add the route definied by the file to the graph
        '''
        #get route data from file
        route_data = read_route_file(route_filename)
        route = Route(route_num, self.chancellors_place, self)

        #add stops to route
        for i in range(len(route_data)-1):
            stop_dict = route_data[i]
            next_stop =  self.get_stop(stop_dict['id'])
            if (next_stop is None):
                next_stop = Stop(stop_dict['id'], stop_dict['name'], stop_dict['lat'], stop_dict['lon'])
                self.stops.append(next_stop)
            if (not self.is_connected(next_stop, route.required_stops[-1])):
                self.connections.append(Connection(next_stop, route.required_stops[-1], stop_dict['time']))
            route.add_required_stop(next_stop)

        #add final stop to route
        if (not self.is_connected(route.required_stops[-1], self.indooroopilly_interchange)):
            self.connections.append(Connection(self.indooroopilly_interchange,
                    route.required_stops[-1], route_data[-1]['time']))
        route.add_required_stop(self.indooroopilly_interchange)

        self.routes.append(route)

    
    def get_stop(self, id):
        '''
        return stop with given ID or None if no such stop exists
        '''
        for stop in self.stops:
            if stop.id == id:
                return stop
        return None
    
    def is_connected(self, stop_1, stop_2):
        '''
        check if two stops are connected
        '''
        for connection in self.connections:
            if (connection.stop_1 == stop_1 and connection.stop_2 == stop_2):
                return 
            elif (connection.stop_2 == stop_1 and connection.stop_1 == stop_2):
                return True
        return False
    
    def get_connections_for_stop(self, stop):
        '''
        return all connections for a given stop
        '''
        relevant_connections = []
        for connection in self.connections:
            if (connection.stop_1 == stop or connection.stop_2 == stop):
                relevant_connections.append(connection)
        return relevant_connections

    
    def __str__(self):
        return_str = 'Routes\n'
        for route in self.routes:
            return_str = return_str + f'\t{route}\n'
        return_str = return_str + 'Stops:\n'
        for stop in self.stops:
            return_str = return_str + f'\t{stop}\n'
        return_str = return_str + 'Connections:\n'
        for connection in self.connections:
            return_str = return_str + f'\t{connection}\n'
        return return_str