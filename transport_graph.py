from utils import get_elevation, read_route_file, read_connections_file, read_stop_file, cache_elevations, read_departure_times, read_trips_file

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
        self.elevation = get_elevation(lat, lon, True, self.id, None)
        self.people = []
        self.passengers = []
        # self.is_flooded = False
    
    def __str__(self):
        return str(f'{self.id}')


class Connection():
    '''
    Represents a series of roads connecting a bus stop. This is an
    edge in the graph.
    '''

    def __init__(self, stop_1, stop_2, time:int):
        self.stop_1 = stop_1
        self.stop_2 = stop_2

        self.elevation = get_elevation((stop_1.lat + stop_2.lat)/2,
            (stop_1.lon + stop_2.lon)/2, False, stop_1.id, stop_2.id)

        self.time=time
        # self.is_flooded = False

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
        self.required_stops = set()
        self.required_stops.add(self.origin_stop)
        self.parent_network = network
    
    def add_required_stop(self, stop):
        self.required_stops.add(stop)
    
    def __str__(self):
        return str(self.route_num)
    

class Passenger():

    def __init__(self, route, dest_stop, origin_stop):
        self.route = route
        #determined in realtime
        self.bus = None
        self.origin_stop = origin_stop
        self.dest_stop = dest_stop
        #best stop they can get to given current flooding
        self.non_preffered_dest_stop = None

        self.arrived = False
        self.stop_arrived_at = None
    
    def depart(self, controller, bus):
        '''
        get on the bus, if you can't make it to your preffered stop, make it
        to the next best one
        '''
        self.bus = bus
        self.bus.passengers.append(self)

        if (not(self.dest_stop in self.bus.stops_visited_on_walk)):
            #find non-prefferred stop
            best_stop = None
            best_time = 5e10
            for stop in self.bus.stops_visited_on_walk:
                next_time = controller.shortest_paths[self.dest_stop][stop]
                if (next_time < best_time):
                    best_stop = stop
                    best_time = next_time
            self.non_preffered_dest_stop = best_stop
    
    def visit_stop(self, stop):
        '''
        if the stop is your destination, get off
        if the stop is your next best destination, get off
        '''
        if (stop.id == self.dest_stop.id):
            self.arrived = True
            self.bus.passengers.remove(self)
        elif ((not(self.non_preffered_dest_stop is None)) and (stop == self.non_preffered_dest_stop)):
            self.arrived = True
            self.bus.passengers.remove(self)

class Bus():
    
    def __init__(self, route, departure_time):
        self.route = route
        self.departure_time = departure_time
        self.passengers = []
        self.capacity = 62

        self.walk = None
        self.stops_visited_on_walk = None
        self.time_at_last_stop = 0
        self.lat = 0
        self.lon = 0

        self.departed = False
        self.done = False

    def update(self, controller, current_time):
        '''
        if the bus is on route, update the bus

        must be able to handle the bus passing several stops in a single tick
        '''
        if (self.done):
            return
        elif (self.departed):
            self.update_journey(controller, current_time)
        elif (self.departure_time <= current_time):
            self.depart(controller, current_time)
    
    def depart(self, controller, current_time):
        '''
        depart the start stop
        '''
        self.departed = True

        self.walk = controller.get_optimal_walk(self.route, self.departure_time)
        if (self.walk is None):
            self.done = True
            return
        
        #make shallow copy
        self.walk = self.walk.copy()

        #initialize stops_visited_on_walk for passengers to calculate non_preffered_dest_stop
        next_stop = self.route.origin_stop
        self.stops_visited_on_walk = set()
        self.stops_visited_on_walk.add(next_stop)
        for connection in self.walk:
            if (connection.stop_1 == next_stop):
                next_stop = connection.stop_2
            else:
                next_stop = connection.stop_1
            self.stops_visited_on_walk.add(next_stop)
        
        #visit first stop
        self.visit_stop(controller, self.route.origin_stop, self.departure_time)

        #recursively call update until we reach stop condition
        self.update(controller, current_time)
        
    def update_journey(self, controller, current_time):
        '''
        update journey for new timestep
        '''
        if (len(self.walk) == 0):
            self.done = True
            return
        
        #get next connection and next stop
        next_connection = self.walk[0]
        if (next_connection.stop_1 == self.current_stop):
            next_stop = next_connection.stop_2
        else:
            next_stop = next_connection.stop_1
        
        if ((current_time - self.time_at_last_stop) >= next_connection.time):
            self.visit_stop(controller, next_stop, self.time_at_last_stop + next_connection.time)
            self.walk.pop(0)
            self.update(controller, current_time)
        else:
            #interpolate lat and lon
            fraction_complete = (current_time - self.time_at_last_stop)/next_connection.time
            self.lat = self.current_stop.lat + (next_stop.lat - self.current_stop.lat)*(fraction_complete)
            self.lon = self.current_stop.lon + (next_stop.lon - self.current_stop.lon)*(fraction_complete)

    def visit_stop(self, controller, stop, time):
        '''
        visit the given stop at the given time
        '''
        self.lat = stop.lat
        self.lon = stop.lon
        self.time_at_last_stop = time
        self.current_stop = stop

        #have all passengers on bus that need to get off, get off
        for passenger in self.passengers.copy():
            passenger.visit_stop(stop)

        for passenger in stop.passengers.copy():
            if (len(self.passengers) >= self.capacity):
                break
            if (passenger.route == self.route):
                stop.passengers.remove(passenger)
                passenger.depart(controller, self)



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
        self.buses = []
        self.passengers = []

        #caching for efficiency
        self.stop_connections = dict()

        #add stops, connections and routes
        self.init_stops()
        self.init_connections()
        self.add_route(414)
        self.add_route(427)
        self.add_route(428)
        self.add_route(432)
        self.init_buses()
        self.init_passengers()

        cache_elevations()
    
    def init_passengers(self):
        '''
        initialize passengers
        get all relevant passengers and add them to their respective stop queues
        shuffle all stop queues
        '''
        stop_id_sets = dict()
        for route in self.routes:
            next_stop_set = set()
            for stop in route.required_stops:
                next_stop_set.add(stop.id)
            stop_id_sets[route.route_num] = next_stop_set

        passenger_numbers = read_trips_file(stop_id_sets, self.chancellors_place.id, self.indooroopilly_interchange.id)
        for route_num in passenger_numbers.keys():
            route = self.get_route(route_num)
            for origin_stop_id in passenger_numbers[route_num].keys():
                origin_stop = self.get_stop(origin_stop_id)
                for dest_stop_id in passenger_numbers[route_num][origin_stop_id].keys():
                    destination_stop = self.get_stop(dest_stop_id)
                    no_passengers = passenger_numbers[route_num][origin_stop_id][dest_stop_id]

                    for i in range(no_passengers):
                        #add the passengers to the origin_stop
                        next_passenger = Passenger(route, destination_stop, origin_stop)
                        origin_stop.passengers.append(next_passenger)
                        self.passengers.append(next_passenger)
    
    def init_buses(self):
        '''
        initialize buses and give them their appropriate departure times and routes
        '''
        departures = read_departure_times()
        for departure in departures:
            route = self.get_route(departure[0])
            self.buses.append(Bus(route, departure[1]))
        
    
    def init_stops(self):
        '''
        add stops to graph
        '''
        stops_data = read_stop_file()
        for stop_data in stops_data:
            self.stops.append(Stop(stop_data['id'], stop_data['name'], stop_data['lat'], stop_data['lon']))
    
    def init_connections(self):
        '''
        add connections to graph
        '''
        connections_data = read_connections_file()
        for connection_data in connections_data:
            stop_1 = self.get_stop(connection_data[0])
            for i in range(1, len(connection_data)):
                stop_2 = self.get_stop(connection_data[i][0])
                if (self.is_connected(stop_1, stop_2)):
                    #don't load connections twice
                    continue
                time = connection_data[i][1]
                self.connections.append(Connection(stop_1, stop_2, time))

    
    def add_route(self, route_num:int):
        '''
        add the route definied by the file to the graph
        '''
        #get route data from file
        route_data = read_route_file(route_num)
        route = Route(route_num, self.chancellors_place, self)

        #add stops to route
        for i in range(len(route_data)-1):
            stop_dict = route_data[i]
            next_stop =  self.get_stop(stop_dict['id'])
            route.add_required_stop(next_stop)

        route.add_required_stop(self.indooroopilly_interchange)
        self.routes.append(route)

    
    def get_stop(self, id):
        '''
        return stop with given ID or None if no such stop exists
        '''
        for stop in self.stops:
            if stop.id == id:
                return stop
        print(f'No stop with id: {id}')
        return None
    
    def get_route(self, route_num):
        '''
        return route with the given route nubmer of NOne if no such route exists
        '''
        for route in self.routes:
            if (route.route_num == route_num):
                return route
        print(f'No route with number: {route_num}')
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
    
    def get_connection(self, stop_1, stop_2):
        '''
        return connection for two stops or None
        '''
        for connection in self.connections:
            if ((connection.stop_1 == stop_1 and connection.stop_2 == stop_2) or
                (connection.stop_2 == stop_1 and connection.stop_1 == stop_2)):
                return connection
        return None
    
    def get_connections_for_stop(self, stop):
        '''
        return all connections for a given stop
        '''
        if (not (stop in self.stop_connections.keys())):
            relevant_connections = []
            for connection in self.connections:
                if (connection.stop_1 == stop or connection.stop_2 == stop):
                    relevant_connections.append(connection)
            self.stop_connections[stop] = relevant_connections
            return relevant_connections
        return self.stop_connections[stop]

    
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