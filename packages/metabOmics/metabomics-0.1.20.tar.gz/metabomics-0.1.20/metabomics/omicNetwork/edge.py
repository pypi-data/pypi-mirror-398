class Edge :
    def __init__(self, start_vertex, end_vertex, weight=1, directed=True, int_info = {}) :
        self.__start_vertex = start_vertex
        self.__end_vertex = end_vertex
        # weight should be modified
        self.__weight = weight
        self.__directed = directed
        self.__int_info = int_info

    def __str__(self) :
        if self.__directed :
            print_pattern = "{0} -{1}-> {2}"
        else :
            print_pattern = "{0} <-{1}-> {2}"
        return print_pattern.format(self.__start_vertex.get_id(), self.__weight, self.__end_vertex.get_id())

    def get_start_vertex(self) :
        return self.__start_vertex

    def get_end_vertex(self) :
        return self.__end_vertex

    def get_weight(self) :
        return self.__weight
    def get_int_info(self):
        return self.__int_info
    def set_int_info(self, e):
        self.__int_info.update(e)
    # less than (a < b), according to weight
    def __lt__(self, other):
        return self.__weight < other.get_weight()

    def __eq__(self, other) :
        weight_equal = self.__weight == other.get_weight()
        start_vertex_equal = self.__start_vertex == other.get_start_vertex()
        end_vertex_equal = self.__end_vertex == other.get_end_vertex()
        return weight_equal == start_vertex_equal == end_vertex_equal == True

    def __hash__(self) :
        return hash((self.__start_vertex.get_id(), self.__end_vertex.get_id(), self.__weight))


