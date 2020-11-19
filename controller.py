

class NetworkController():

    def __init__(self, network, disaster_resistant=False, seconds_per_tick=120):
        self.start_water_level=0.0
        self.end_water_level=20.0
        self.current_water_level = 0.0
        
        self.distaster_resistant = disaster_resistant
        self.network = network

        #start and end time in seconds
        self.end_time = 4*60*60
        self.current_time = 0
        self.seconds_per_tick = seconds_per_tick

        #dict mapping routes to the last calculated optimal walk
        self.get_max_time_per_walk()
        self.shortest_paths = self.init_shortest_paths()
        self.prev_optimal_walks = dict()
        self.init_walks()
        self.cached_optimal_walks = dict()
    
    def get_max_time_per_walk(self):
        '''
        get the maximum time per trip before pruning from search tree
        '''
        self.max_time_per_walk = dict()
        self.max_time_per_walk[414] = 60*47#37
        self.max_time_per_walk[427] = 60*38#28
        self.max_time_per_walk[428] = 60*42#32
        self.max_time_per_walk[432] = 60*37#27

    def update(self):
        self.current_time += self.seconds_per_tick
        self.current_water_level = self.get_water_level_for_time(self.current_time)
        self.update_buses()
        # print(f'TIME: {self.current_time} / {self.end_time}\nWATER:{self.current_water_level}m')
    
    def update_buses(self):
        '''
        update current buses for new tick
        '''
        for bus in self.network.buses:
            bus.update(self, self.current_time)
    
    def is_complete(self):
        for bus in self.network.buses:
            if (not bus.done):
                return False
        #its complete
        self.print_stats()
        self.cache_optimum_walks
        return True

    def print_stats(self):
        print('\n\n')
        total_passengers = len(self.network.passengers)
        stranded_passengers = 0
        non_prefferred_passengers = 0
        non_prefferred_distance = 0
        for passenger in self.network.passengers:
            if (not(passenger.arrived)):
                stranded_passengers += 1
            elif (not (passenger.non_preffered_dest_stop is None)):
                non_prefferred_passengers += 1
                non_prefferred_distance += self.shortest_paths[passenger.non_preffered_dest_stop][passenger.dest_stop]
        print(f'{total_passengers - stranded_passengers - non_prefferred_passengers} passengers arrived at their destination')
        print(f'{stranded_passengers} passengers were stranded at their initial stop')
        if (non_prefferred_passengers != 0):
            print(f'{non_prefferred_passengers} arrived at a non-preffered stop only {non_prefferred_distance/(non_prefferred_passengers*60)} minutes drive from their prefferred stop')
        print('\n\n')
    
    def init_shortest_paths(self):
        '''
        find shortest paths between all stops using djikstras
        '''
        #min_dist[stop_1][stop_2] is the minimum time connecting stop_1 to stop_2 
        STOP = 0
        TIME = 1
        INF = 10e8
        min_dist = dict()

        for main_stop in self.network.stops:
            #nodes take the form [stop, time]
            open_nodes = [[main_stop, 0]]
            visited_stops = set()
            main_stop_min_dist = dict()

            #initlialize open nodes
            for stop in self.network.stops:
                if (stop != main_stop):
                    open_nodes.append([stop, INF])
                open_nodes.sort(key=lambda x: x[TIME])

            #main search loop
            while(len(open_nodes) > 0):
                current_node = open_nodes.pop(0)
                
                for connection in self.network.get_connections_for_stop(current_node[STOP]):
                    if (current_node[STOP] == connection.stop_1):
                        next_stop = connection.stop_2
                    else:
                        next_stop = connection.stop_1
                    
                    if (next_stop in visited_stops):
                        continue
                    
                    next_time = current_node[TIME] + connection.time
                    for node in open_nodes:
                        if node[STOP] == next_stop:
                            node[TIME] = min(next_time, node[TIME])
                            break
                main_stop_min_dist[current_node[STOP]] = current_node[TIME]
                visited_stops.add(current_node[STOP])
                open_nodes.sort(key=lambda x: x[TIME])
            min_dist[main_stop] = main_stop_min_dist
        return min_dist
    

    def init_walks(self):
        '''
        find the initial walks
        '''
        for route in self.network.routes:
            self.prev_optimal_walks[route] = self.optimal_walk_search(route, 0, True)
    
    def cache_optimum_walks(self):
        '''
        cache the optimum walks
        '''
        pass

    def get_optimal_walk(self, route, time):
        '''
        return the optimum walk for the given route starting at the given timestep
        '''
        prev_optimal_walk = self.prev_optimal_walks[route]
        if (prev_optimal_walk is None):
            return prev_optimal_walk
        elif(self.is_walk_valid(prev_optimal_walk, time, route.route_num)):
            return prev_optimal_walk
        elif (self.distaster_resistant):
            #if changing routes, search for new route and return it (None if no route exists)
            new_optimal_walk = self.optimal_walk_search(route, time, trail=True)
            self.prev_optimal_walks[route] = new_optimal_walk
            return new_optimal_walk
        else:
            #if not changing routes, then there is no other walk than the default
            self.prev_optimal_walks[route] = None
            return None


    def optimal_walk_search(self, route, time, trail=False):
        '''
        search for the optimum walk for the given route starting at the given timestep
        if trail is true, do not allow repeated edges
        TODO:
            FUNCTIONALITY:
                -add the 'best option' thing

            OPTIMIZING
                tune max time - initial time for each route + 10 minutes
                go through and check that everything is running snappy (probs isn't too bad since paths are fine)
                remove duplicates - same visited required stops and same current stop
                
                if this still isn't enough, require that indooroopilly is the final stop
                    heuristic = time to furthest univisited required stop + time from that stop to
                                indooroopilly
        '''
        
        CURRENT_STOP=0
        TIME=1
        WALK=2
        REQUIRED_SET=3
        HEURISTIC=4
        #nodes take the form [current_stop, current_time, stops_visited_in_order (first to last)]
        root_node_set = set()
        root_node_set.add(self.network.chancellors_place)
        root_node = [self.network.chancellors_place, time, [], root_node_set, time + self.get_heuristic(route, [], self.network.chancellors_place)]
        best_incomplete_node = root_node
        node_list = [root_node]

        while(len(node_list) > 0):
            node = node_list.pop(0)

            #check if walk is complete
            if (self.is_walk_complete(node[CURRENT_STOP], node[REQUIRED_SET], route)):
                return node[WALK]
            
            #check if walk is better than last best_incomplete_walk
            if ((node[CURRENT_STOP] == self.network.indooroopilly_interchange) and 
                (len(node[REQUIRED_SET]) > len(best_incomplete_node[REQUIRED_SET]))):
                best_incomplete_node = node
            
            #make new node for each connection
            prev_stop = node[CURRENT_STOP]

            for connection in self.network.get_connections_for_stop(prev_stop):

                #if looking for trail, abandon this
                if (trail and (connection in node[WALK])):
                    continue

                #get stop
                if (prev_stop == connection.stop_1):
                    next_stop = connection.stop_2
                else:
                    next_stop = connection.stop_1
                
                #check the step is valid, get next time and check if time is over max
                valid, next_time = self.is_step_valid(prev_stop, next_stop, connection, node[TIME])
                if ((not valid) or ((next_time-time) > self.max_time_per_walk[route.route_num])):
                    continue
                
                #get new walk
                next_walk = node[WALK].copy()
                next_walk.append(connection)
                #prune those with double crossed edges
                if (self.is_walk_suboptimal(next_walk, connection)):
                    continue

                next_heuristic = next_time + self.get_heuristic(route, next_walk, next_stop)
                
                #get new required_set
                new_required_set = node[REQUIRED_SET].copy()
                if ((not (next_stop in node[REQUIRED_SET])) and (next_stop in route.required_stops)):
                    new_required_set.add(next_stop)

                #prune new set if too long
                next_node = [next_stop, next_time, next_walk, new_required_set, next_heuristic]
                if ((next_node[HEURISTIC] - time) > self.max_time_per_walk[route.route_num]):
                    continue
                
                #append new node to open list
                node_list.append(next_node)
            node_list.sort(key=lambda x: x[HEURISTIC])
        if (self.distaster_resistant):
            return best_incomplete_node[WALK]
        else:
            return None

    def get_heuristic(self, route, walk, current_stop):
        '''
        return time plus heuristic for A*
        heuristic is minumum time to the furthest unvisited stop in route.required_stops
        '''
        # walk_stops = set()
        # for connection in walk:
        #     walk_stops.add(connection.stop_1)
        #     walk_stops.add(connection.stop_2)

        # max_time = 0
        # for stop in route.required_stops:
        #     if (not (stop in walk_stops)):
                # max_time = max(max_time, self.shortest_paths[current_stop][stop] + self.shortest_paths[self.network.indooroopilly_interchange][stop])
        # return max_time
        return self.shortest_paths[self.network.indooroopilly_interchange][current_stop]
    
    def get_num_required_visited(self, route, walk):
        '''
        returns how many of the required stops are visited in this path
        '''

    def is_walk_suboptimal(self, walk, connection):
        '''
        checks to see if the walk is suboptimal given the newly added connection
        '''
        num_occurances = walk.count(connection)
        return num_occurances > 2

    def is_walk_complete(self, current_stop, required_set, route):
        '''
        return True if the walk contains all stops in the routes required_stops
        '''
        # stops = []
        # for connection in walk:
        #     stops.append(connection.stop_1)
        #     stops.append(connection.stop_2)
        # for stop in route.required_stops:
        #     if stop in stops:
        #         continue
        #     return False
        # return True
        if (current_stop != self.network.indooroopilly_interchange):
            return False
        for stop in route.required_stops:
            if (stop in required_set):
                continue
            return False
        return True


    def is_walk_valid(self, walk, time, route_num):
        '''
        test if a walk is valid starting at the given time
        '''
        start_time = time
        next_stop = self.network.chancellors_place
        for connection in walk:
            prev_stop = next_stop
            if (connection.stop_1 == prev_stop):
                next_stop = connection.stop_2
            else:
                next_stop = connection.stop_1
            valid, time = self.is_step_valid(prev_stop, next_stop, connection, time)
            if ((not valid) or ((time - start_time) > self.max_time_per_walk[route_num])):
                return False
        return True
            
    
    def is_step_valid(self, start_stop, end_stop, connection, time):
        '''
        returns True and the new time if the step from one stop to another is valid
        for the given start time. Returns False, -1 otherwise

        assumes its valid for the bus to be at the start stop for the given 
        start_time
        '''
        end_time = time + connection.time
        end_water_level = self.get_water_level_for_time(end_time)
        if ((connection.elevation <= end_water_level) or
            (end_stop.elevation <= end_water_level)):
            return False, -1
        return True, end_time

    def get_water_level_for_time(self, time):
        water_level_diff = ((self.end_water_level - self.start_water_level) / (self.end_time)) * time
        return min(water_level_diff + self.start_water_level, self.end_water_level)