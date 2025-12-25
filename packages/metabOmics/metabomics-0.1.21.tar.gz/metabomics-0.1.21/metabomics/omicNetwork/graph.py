from .edge import Edge
from .vertex import Vertex
import json

class Graph :
    def __init__(self, directed=True) :
        self.__vertices = {}
        self.__edges = {}
        self.__directed = directed

    def __str__(self) :
        graph_str = ""
        for key in self.__vertices :
            graph_str += str(self.__vertices[key]) + "\n"
        return graph_str

    def add_vertex(self, id, label, vert_info, omic_type) :
        '''if '_x' in id :
            if id[:-2] in self.__vertices :
                return True
        if id in self.__vertices :
            return
        key = id + '_x'
        if key in self.__vertices :
            self.__vertices[id] = self.__vertices[key]
            self.get_vertex(id).set_label([self.get_vertex(id).get_label()[0][:-2]])
            # Delete the old key
            del self.__vertices[key]
            # self.remove_vertex(key)
            return True'''
        if id in self.__vertices :
            return True
        else:
            self.__vertices[id] = Vertex(id, label, self.__directed, vert_info, omic_type)
    def add_edge(self, start_id, end_id, weight=1, int_info = {}) :
        start_vertex = self.get_vertex(start_id)
        end_vertex = self.get_vertex(end_id)
        if(start_vertex or end_vertex) is None :
            raise ValueError("Can not find start or end vertex in graph")

        edge = Edge(start_vertex, end_vertex, weight, self.__directed, int_info)
        start_vertex.add_edge(edge)
        if start_vertex != end_vertex :
            end_vertex.add_edge(edge)
        if '_x' in start_id :
            start_id = start_id[:-2]
        if '_x' in end_id :
            end_id = end_id[:-2]
        key = str(start_id)+str(end_id)
        if key in self.__edges :
            self.__edges[key].set_int_info(int_info)
            return
        self.__edges.update({key : edge})

    def remove_edge(self, start_label, end_label, weight=1) :
        start_vertex = self.get_vertex(start_label)
        end_vertex = self.get_vertex(end_label)
        if (start_vertex or end_vertex) is None :
            raise ValueError("Can not find start or end vertex in graph")
        edge = Edge(start_vertex, end_vertex, weight, self.__directed)
        if edge not in self.__edges :
            raise ValueError("Can not find edge {0} in graph".format(str(edge)))
        start_vertex.remove_edge(edge)
        end_vertex.remove_edge(edge)
        key = start_label + end_label
        del self.__edges[key]

    def remove_vertex(self, vertex_label) :
        if vertex_label not in self.__vertices:
            raise ValueError(f"Cannot find vertex {vertex_label} in graph")
        vertex = self.__vertices[vertex_label]
        # Make a copy of edges to avoid modifying the set while iterating
        outbound_edges = vertex.get_outbound_edges().copy()
        inbound_edges = vertex.get_inbound_edges().copy()

        # Remove all outbound edges
        for edge in outbound_edges:
            neighbor = edge.get_end_vertex()
            neighbor.remove_edge(edge)
            vertex.remove_edge(edge)

            edge_key = edge.get_start_vertex().get_id() + edge.get_end_vertex().get_id()
            if edge_key in self.__edges:
                del self.__edges[edge_key]

    def get_vertex(self, label) :
        return self.__vertices.get(label)

    def get_vertices(self) :
        return self.__vertices

    def get_edges(self) :
        return self.__edges

    def get_indegree(self, label) :
        return len(self.get_vertex(label).get_inbound_edges())

    def get_outdegree(self, label) :
        return len(self.get_vertex(label).get_outbound_edges())

    def get_degree(self, label) :
        if self.is_directed() :
            degree = self.get_indegree(label) + self.get_outdegree(label)
        else :
            degree = len(self.get_vertex(label).get_outbound_edges())
        return degree

    def is_directed(self) :
        return self.__directed

    def to_json(self):
        vertices_data = {vertex.get_id(): {"label": vertex.get_label(),
                                          "vert_info": vertex.get_vert_info(),
                                          "omic_type": vertex.get_omic_type()}
                        for vertex in self.__vertices.values()}

        edges_data = [{"start_vertex": edge.get_start_vertex().get_id(),
                       "end_vertex": edge.get_end_vertex().get_id(),
                       "weight": edge.get_weight(),
                       "int_info": edge.get_int_info()}
                      for edge in self.__edges.values()]

        graph_data = {
            "vertices": vertices_data,
            "edges": edges_data,
            "directed": self.__directed
        }
        return graph_data

    def save_to_json(self, filename):

        graph_data = self.to_json()
        with open(filename, 'w') as file:
            json.dump(graph_data, file, indent=2)











