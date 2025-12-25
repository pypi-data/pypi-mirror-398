from ..cobra.flux_analysis.variability import flux_variability_analysis
from ..cobra.flux_analysis.geometric import geometric_fba
from ..cobra.flux_analysis.parsimonious import pfba
from ..cobra.flux_analysis.moma import moma
from ..cobra.util import fix_objective_as_constraint
from ..utils import load_network_model
from sympy.core.singleton import S
from .drugAnalysis import DrugReactionAnalysis
import sys
import numpy as np
sys.path.append(r'../omicNetwork')
from ..omicNetwork.graph import Graph
from datetime import datetime
import json
from ..cobra import Reaction
import metabomics.extensions
import pandas as pd


class MetaboliticsAnalysis:
    '''
    Metabolitics analysis for metabolic dataset.
    '''

    def __init__(self, model='recon3D', drug='', target='', reaction='', without_transports=True):
        """
        :param model: cobra Model
        :param drug: Drugs that blocks certain genes
        :type drug: List or string, depending on singular or multiple drugs
        :param target: Targeted Gene without a drug, gene id in model
        :type target: string
        :param reaction Reaction id in model, reaction's upper and lower bound is set to zero
        """

        self.model = load_network_model(model=model)
        self.model.solver = 'cplex'
        # self.model.solver = "glpk"
        # self.model.solver.configuration.timeout = 10 * 60
        self.without_transports = without_transports
        self.drug = drug
        self.target = target
        self.reaction = reaction
        self.drug_analyzer = DrugReactionAnalysis(model=model)
        self.sample_count = 1
    def drug_knock_out(self):
        if type(self.drug) != list:
            self.drug = [self.drug]

        for drug in self.drug:
            for gene in self.drug_analyzer.drug_target(drug):
                try:
                    self.model.genes.get_by_id(gene).knock_out()
                except:
                    continue

    def reaction_knockout(self):
        if type(self.reaction) != list:
            self.reaction = [self.reaction]
        for r_id in self.reaction:
            r = self.model.reactions.get_by_id(r_id)
            r.lower_bound = 0
            r.upper_bound = 0

    def set_objective(self, measured_metabolites):
        '''
        Updates objective function for given measured metabolites.

        :param dict measured_metabolites: dict in which keys are metabolite names 
            and values are float numbers represent fold changes in metabolites. 
        '''
        self.clean_objective()

        for k, v in measured_metabolites.items():

            m = self.model.metabolites.get_by_id(k)
            total_stoichiometry = m.total_stoichiometry(self.without_transports)
            for r in m.producers(self.without_transports):
                #print(r, " lower bound : ", r.lower_bound)
                #print(r, " upper bound : ", r.upper_bound)
                update_rate = v * r.metabolites[m] / total_stoichiometry
                r.objective_coefficient += update_rate

    def add_constraint(self, measured_metabolites):
        '''
        Add measurements as constraint to model.

        :param dict measured_metabolites: dict in which keys are metabolite names 
            and values are float numbers represent fold changes in metabolites.
        '''
        self.set_objective(measured_metabolites)
        fix_objective_as_constraint(self.model)

    def update_bound(self, active_node, reactions, toy_graph):

        '''Updates update reaction bound for given predicted gens.

        :param dict active_node : dict in which keys are activated genes(transcriptom) names
            and values are float numbers represent fold changes in genes(transcriptom).
        :param list reactions : activated reactions
        :param toy_graph : transcriptomic graph'''

        infeasable_react = 0
        count = 0
        for react in reactions:
            try:
                # Aktif edilmiş reaksiyonun komşularını al (reaksiyonu aktive eden genler olmuş oluyor)
                neighbors = set(
                    i.get_start_vertex().get_id() for i in toy_graph.get_vertex(react).get_inbound_edges())
                # difussion'da aktive edilmişler ile kesişimini al
                act_gens = neighbors.intersection(list(active_node.keys()))
                # kesişen genleri uniprot idleri ile tut
                act_gens_uniprot = [item.split('_')[0] for item in act_gens]

                # gpr'daki genleri uniprot id'leri ile sakla. kuralına uyanları ayır
                hold = []
                for gpr_list in toy_graph.get_vertex(react).get_vert_info()['gpr']:
                    valid_gene = True
                    for gene in gpr_list:
                        if gene not in act_gens_uniprot:
                            valid_gene = False
                            break
                    if valid_gene:
                        hold.append(min(active_node.get(key + '_protein', active_node.get(key + '_protein_x'))
                                        for key in gpr_list
                                        if key + '_protein_x' in active_node or key + '_protein' in active_node))

                if len(hold) == 0 :
                    continue
                value = max(hold)
                if value == 0:
                    count += 1
                if self.model.reactions.get_by_id(react).lower_bound >= 0:
                    dif = self.model.reactions.get_by_id(react).upper_bound - self.model.reactions.get_by_id(
                        react).lower_bound
                    if value > 0 and value < 1:
                        self.model.reactions.get_by_id(react).lower_bound = self.model.reactions.get_by_id(react).lower_bound + dif * value / 1000
                    elif value < 0 and value > -1:
                        self.model.reactions.get_by_id(react).upper_bound = self.model.reactions.get_by_id(react).upper_bound + dif * value
                    else:
                        infeasable_react += 1
                else:
                    if value < 0 and value > -1:
                        self.model.reactions.get_by_id(react).upper_bound = self.model.reactions.get_by_id(react).upper_bound + self.model.reactions.get_by_id(react).upper_bound * value
                        self.model.reactions.get_by_id(react).lower_bound = self.model.reactions.get_by_id(react).lower_bound + self.model.reactions.get_by_id(react).lower_bound * value
            except Exception as e:
                continue

    def variability_analysis(self, measured_metabolites, x_tr):
        if self.drug != '':
            self.drug_knock_out()
        elif self.target != '':
            self.model.genes.get_by_id(self.target).knock_out()
        elif self.reaction != '':
            self.reaction_knockout()

        with open('../omicNetwork/Databases/universalGraph_new.json', 'r') as file:
            data = json.load(file)
        G = Graph()
        #with open('../omicNetwork/Databases/labelGraph_new.json', 'r') as json_file:
        #    label_graph = json.load(json_file)
        with open("../omicNetwork/name_mapping_uniprot/uniprot_synonym_mapping.json", "r", encoding="utf-8") as f:
            synonym_mapping_dict = json.load(f)

        for vertex in data['vertices']:
            G.add_vertex(vertex, label=data['vertices'][vertex]['label'],
                         vert_info=data['vertices'][vertex]['vert_info'],
                         omic_type=data['vertices'][vertex]['omic_type'])
        for edge in data['edges']:
            G.add_edge(start_id=edge['start_vertex'], end_id=edge['end_vertex'], int_info=edge['int_info'])

        vertices_id = set(G.get_vertices().keys())
        x_tr_g = {}
        er = 0
        '''for k, v in x_tr.items():
            try:
                if k + '_transcript' in list(label_graph.keys()):
                    x_tr_g[label_graph[k + '_transcript']] = v
                elif k + '_transcript_x' in list(label_graph.keys()):
                    x_tr_g[label_graph[k + '_transcript_x']] = v

            except Exception as e:
                #print(f"Error processing {k} : {e}")
                continue'''
        for k, v in x_tr.items():
            uniprots = synonym_mapping_dict.get(k)
            if not uniprots:
                #print(f"No mapping found for {k}")
                continue

            for uniprot_id in uniprots:
                transcript_id = f"{uniprot_id}_transcript"
                transcript_x_id = f"{uniprot_id}_transcript_x"

                if transcript_id in vertices_id:
                    x_tr_g[transcript_id] = v
                    break
                elif transcript_x_id in vertices_id:
                    x_tr_g[transcript_x_id] = v
        gr_new, active_node, reactions = self.linear_threshold_model(G, x_tr_g)
        self.update_bound(active_node, reactions, G)
        self.set_objective(measured_metabolites)
        count = 0
        df = flux_variability_analysis(self.model, processes=1)
        return df

    def pfba_analysis(self, measured_metabolites):
        if self.drug != '':
            self.drug_knock_out()
        elif self.target != '':
            self.model.genes.get_by_id(self.target).knock_out()
        elif self.reaction != '':
            self.reaction_knockout()

        self.set_objective(measured_metabolites)

        solution = pfba(self.model)

        return solution.fluxes

    def geometric_fba_analysis(self, measured_metabolites):
        if self.drug != '':
            self.drug_knock_out()
        elif self.target != '':
            self.model.genes.get_by_id(self.target).knock_out()
        elif self.reaction != '':
            self.reaction_knockout()

        self.set_objective(measured_metabolites)

        solution = geometric_fba(self.model, processes=1)

        return solution.fluxes

    # TODO moma does not work
    def moma_analysis(self, measured_metabolites):
        if self.drug != '':
            self.drug_knock_out()
        elif self.target != '':
            self.model.genes.get_by_id(self.target).knock_out()
        elif self.reaction != '':
            self.reaction_knockout()

        self.set_objective(measured_metabolites)

        solution = moma(self.model)

        return solution.fluxes

    def clean_objective(self):
        '''
        Cleans previous objective.
        '''
        self.model.objective = S.Zero

    def copy(self):
        return self.__class__(model=self.model.copy(), drug=self.drug, without_transports=self.without_transports)

    def linear_threshold_model(self, graph1, initial_active_nodes, iterations=2000, k=0.0005):
        active_dict = initial_active_nodes
        active_nodes = set(initial_active_nodes.keys())
        reactions = []
        for i in active_dict:
            graph1.get_vertex(i).set_vert_info({'value': active_dict[i]})
        new_nodes_activated = True
        iters = 0

        while new_nodes_activated and iters < iterations:

            new_nodes_activated = False
            iters += 1
            activated = {}
            for node in list(graph1.get_vertices()):
                if node not in active_nodes:
                    neighbors = set(i.get_start_vertex().get_id() for i in graph1.get_vertex(node).get_inbound_edges())
                    activated_neighbors = neighbors.intersection(active_nodes)
                    control = False
                    if len(activated_neighbors) > 0:
                        if graph1.get_vertex(node).get_omic_type() == 'R':
                            reactions.append(node)
                        if 'COMPLEX' in node :
                            neighbors_len = len(activated_neighbors)
                            neighbors_val = []
                            for edge in graph1.get_vertex(node).get_edges():
                                if edge.get_start_vertex().get_id() in activated_neighbors:
                                    if edge.get_int_info()["interaction"]["0"] == 'part_of':
                                        neighbors_val.append(edge.get_start_vertex().get_vert_info()['value'])
                                    else :
                                        control = True
                                        break
                            if neighbors_len == len(neighbors_val) :
                                activated[node] = min(neighbors_val)
                                graph1.get_vertex(node).set_vert_info({'value': min(neighbors_val)})
                        if control :
                            val_act = 0
                            for edge in graph1.get_vertex(node).get_edges():
                                if edge.get_start_vertex().get_id() in activated_neighbors:
                                    if edge.get_int_info()["interaction"]["0"] == 'Repression':
                                        val_act -= edge.get_start_vertex().get_vert_info()['value']
                                    else :
                                        val_act += edge.get_start_vertex().get_vert_info()['value']

                            activated[node] = val_act
                            graph1.get_vertex(node).set_vert_info({'value': val_act})
                        new_nodes_activated = True
            active_dict.update(activated)
            active_nodes.update(activated.keys())
        print("number of iteration in diffusion process : ", iters)
        return graph1, active_dict, reactions



