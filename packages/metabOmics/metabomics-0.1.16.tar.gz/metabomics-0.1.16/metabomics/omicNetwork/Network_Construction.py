import pandas as pd
import numpy as np
from ..cobra.io import load_json_model
from .graph import Graph
import time
import json
import re
from collections import defaultdict, deque

with open('Databases/ccdc_uniprot.json', 'r') as json_file:
    ccdc_uniprot = json.load(json_file)

def parse_gpr_expression(gpr_expression, ccdc_uniprot, modelREcon3d):
    # Extract OR conditions using regular expression
    or_conditions = re.split(r' or ', gpr_expression)

    # Split each condition into a list of genes
    gene_lists = []
    for condition in or_conditions:
        genes = condition.strip('()').split(" and ")
        temp = []
        for gene in genes:
            gene = gene.replace('(', '').replace(')', '')
            if 'ccds' in modelREcon3d.genes.get_by_id(gene).annotation.keys():
                for i in modelREcon3d.genes.get_by_id(gene).annotation['ccds']:
                    if i in ccdc_uniprot.keys():
                        temp.extend(ccdc_uniprot[i])
                        break
        gene_lists.append(temp)
    return gene_lists

def add_gene_to_protein_chain(universal_graph, gene_id, label_name=None):
    """Adds gene → transcript → protein to graph, returns protein label."""
    if universal_graph.add_vertex(gene_id, label=[label_name or gene_id], vert_info={}, omic_type='gene'):
        return gene_id + '_protein'
    else:
        tx_label = gene_id + '_transcript'
        px_label = gene_id + '_protein'
        universal_graph.add_vertex(tx_label, label=[(label_name or gene_id) + '_transcript'], vert_info={}, omic_type='transcript')
        universal_graph.add_edge(gene_id, tx_label, int_info={
            'type': 'gene - transcript', 'interaction': {0: 'transcribed_to'}})
        universal_graph.add_vertex(px_label, label=[(label_name or gene_id) + '_protein'], vert_info={}, omic_type='protein')
        universal_graph.add_edge(tx_label, px_label, int_info={
            'type': 'transcript - protein', 'interaction': {0: 'translated_to'}})
        return px_label

def add_protein_complex(universal_graph, complex_id):
    """Adds a protein complex and its parts to the graph."""
    protein_list = complex_id.split(":")[1].split("_")
    universal_graph.add_vertex(complex_id, label=[complex_id], vert_info={'parts': protein_list}, omic_type='protein_complex')
    for pr in protein_list:
        pr_px = add_gene_to_protein_chain(universal_graph, pr, label_name=pr)
        universal_graph.add_edge(pr_px, complex_id, int_info={
            'type': 'protein - protein_complex', 'interaction': {0: 'part_of'}})

def add_interaction_edge(universal_graph, source, target, interaction, type_label=None, weight=None):
    """Adds an edge between two nodes."""
    int_info = {
        'type': type_label or f"{universal_graph.get_vertex(source).get_omic_type()} - {universal_graph.get_vertex(target).get_omic_type()}",
        'interaction': {0: interaction}
    }
    universal_graph.add_edge(source, target, weight=weight, int_info=int_info)


def print_graph_summary(source_name, universal_graph, unique_genes=set(), not_found_genes=set(), total_items=None,
                        empty_count=None):
    count_gene = sum(1 for v in universal_graph.get_vertices().values() if v.get_omic_type() == 'gene')

    print(f"\n--- {source_name} Summary ---")
    if total_items is not None:
        print(f"Total items in {source_name}: {total_items}")
    if empty_count is not None:
        print(f"Number of empty mappings in {source_name}: {empty_count}")

    print("Number of unique genes: ", len(unique_genes))
    print("Number of genes with missing UniProt ID: ", len(not_found_genes))
    print("Number of vertices: ", len(universal_graph.get_vertices()))
    print("Number of edges: ", len(universal_graph.get_edges()))
    print("Number of gene vertices: ", count_gene)

    omic_type_counts = defaultdict(int)
    for v in universal_graph.get_vertices().values():
        omic_type_counts[v.get_omic_type()] += 1

    for omic_type, count in omic_type_counts.items():
        print(f"{omic_type}: {count}")
    print(f"{source_name} processing finished.\n")

# Filtering Graph
def get_reverse_adjacency_list(graph):
    reverse_adj = defaultdict(list)
    for edge in graph.get_edges().values():
        src = edge.get_start_vertex().get_id()
        tgt = edge.get_end_vertex().get_id()
        reverse_adj[tgt].append(src)  # reverse the edge
    return reverse_adj

def get_nodes_that_can_reach_reactions(graph):
    reverse_adj = get_reverse_adjacency_list(graph)
    visited = set()

    # Collect all reaction node IDs
    reaction_nodes = [v.get_id() for v in graph.get_vertices().values() if v.get_omic_type() == 'R']

    # BFS from each reaction node in reversed graph
    queue = deque(reaction_nodes)
    while queue:
        current = queue.popleft()
        if current in visited:
            continue
        visited.add(current)
        for neighbor in reverse_adj[current]:
            if neighbor not in visited:
                queue.append(neighbor)

    return visited  # nodes that can reach at least one reaction

if __name__ == '__main__':

    start = time.time()
    universal_graph = Graph()

    modelREcon3d = load_json_model('Databases/Recon3D.json')
    empty = 0
    unique_gene = set()
    nogene = set()
    for r in modelREcon3d.reactions:
        if r.gene_reaction_rule != '':
            # try :
            universal_graph.add_vertex(r.id, label=[r.id], vert_info={
                'metabolites': [{str(metabolite): coefficient for metabolite, coefficient in r.metabolites.items()}],
                'gpr': parse_gpr_expression(str(r.gpr), ccdc_uniprot, modelREcon3d)}, omic_type='R')
            # get related genes
            for gen in r.genes:
                unique_gene.add(gen.name)
                if 'ccds' in gen.annotation.keys():
                    for i in gen.annotation['ccds']:
                        if i in ccdc_uniprot.keys():
                            label = ccdc_uniprot[i]
                            break
                elif gen.id in ccdc_uniprot.keys():
                    label = ccdc_uniprot[gen.id]
                else:
                    nogene.add(gen.name)
                label_px = add_gene_to_protein_chain(universal_graph, label[0], label_name=gen.name)
                add_interaction_edge(universal_graph, label_px, r.id, interaction='catalyzes')
        else:
            empty += 1

    # Summary for Recon3D
    print_graph_summary(source_name='Recon3D', universal_graph=universal_graph, unique_genes=unique_gene, not_found_genes=nogene, total_items=len(modelREcon3d.reactions),
                        empty_count=empty)

    # Adding TRRUST(TF-gene) database to network
    trrust_tfg = pd.read_csv('Databases/trrust_uniprot_human.tsv', sep='\t')
    count = 1
    error = 0
    unique_gene_trrust = set()
    for j in trrust_tfg.values:
        label_tf = str(j[1])
        label_target = str(j[3])
        if j[4] == 'Unknown' :
            continue
        unique_gene_trrust.add(label_target)
        label_px_tf = add_gene_to_protein_chain(universal_graph, label_tf, label_name=j[0])
        label_px_target = add_gene_to_protein_chain(universal_graph, label_target, label_name=j[2])
        add_interaction_edge(universal_graph, label_px_tf, label_px_target, interaction=j[4])

    # Summary for TRRUST
    print_graph_summary(source_name='TRRUST', universal_graph=universal_graph, unique_genes=unique_gene_trrust,
                        total_items=len(trrust_tfg.values))

    # Adding mirtarbase(miRNA-gene) database to network
    mirTarBase = pd.read_csv('Databases/mirTarBase_evidenceStrong.csv')
    count = 0
    error = 0
    unique_gene_mir = set()
    for j in mirTarBase.values:
        try:
            label_target = j[4]
            unique_gene_mir.add(label_target)
            label_px_target = add_gene_to_protein_chain(universal_graph, label_target, label_name=j[3])
            universal_graph.add_vertex(j[1], label=[j[1]], vert_info={'int_id': j[0]}, omic_type='miRNA')
            add_interaction_edge(universal_graph, j[1], label_px_target, interaction='Repression', weight= j[7])
        except Exception as e:
            error += 1
            universal_graph.remove_vertex(label_target)
            # print(f"Error processing {j}: {e}")
            continue

    print("error : ", error)
    # Summary for mirTarBase
    print_graph_summary(source_name='mirTarBase', universal_graph=universal_graph, unique_genes=unique_gene_mir,
                        total_items=len(mirTarBase.values))

    # Adding Omni-Path(protein-protein signaling) database to network
    omniPath = pd.read_csv('Databases/filtered_omnipath_interactions.csv')
    complex_protein = set()
    unique_gene_omniPath = set()
    for row in omniPath.values:
        src, tgt = row[0], row[1]
        if row[3] == row[4]:
            continue
        interaction = 'Activation' if row[3] == 1 else 'Repression'

        is_src_complex = 'COMPLEX' in src
        is_tgt_complex = 'COMPLEX' in tgt
        if is_src_complex: add_protein_complex(universal_graph, src)
        if is_tgt_complex: add_protein_complex(universal_graph, tgt)

        if is_src_complex and is_tgt_complex :
            add_interaction_edge(universal_graph, src, tgt, interaction)
        elif is_src_complex :
            tgt_px = add_gene_to_protein_chain(universal_graph, tgt, label_name=row[0])
            add_interaction_edge(universal_graph, src, tgt_px, interaction)
        elif is_tgt_complex :
            src_px = add_gene_to_protein_chain(universal_graph, src, label_name=row[1])
            add_interaction_edge(universal_graph, src_px, tgt, interaction)
        else :
            src_px = add_gene_to_protein_chain(universal_graph, src, label_name=row[0])
            tgt_px = add_gene_to_protein_chain(universal_graph, tgt, label_name=row[1])
            add_interaction_edge(universal_graph, src_px, tgt_px, interaction)

        unique_gene_omniPath.update([src, tgt])

    # Summary for Omni-Path
    print_graph_summary(source_name='Omni-Path', universal_graph=universal_graph, unique_genes=unique_gene_omniPath,
                        total_items=len(omniPath.values))

    universal_graph.save_to_json("Databases/universalGraph_with_omniPath_unFiltered.json")

    # Filter out nodes that cannot reach any reaction node
    reachable_nodes = get_nodes_that_can_reach_reactions(universal_graph)
    all_nodes = set(universal_graph.get_vertices().keys())
    unreachable_nodes = all_nodes - reachable_nodes

    for node_id in unreachable_nodes:
        try:
            universal_graph.remove_vertex(node_id)
        except ValueError:
            pass  # vertex might already have been removed during earlier clean-up

    print(f"Filtered out {len(unreachable_nodes)} unreachable nodes.")
    print(f"Remaining vertices: {len(universal_graph.get_vertices())}")
    print(f"Remaining edges: {len(universal_graph.get_edges())}")

    print_graph_summary(source_name='Omni-Path', universal_graph=universal_graph, unique_genes=unique_gene_omniPath,
                        total_items=len(omniPath.values))

    universal_graph.save_to_json("Databases/universalGraph_with_omniPath_Filtered.json")
    end = time.time()
    print(f"Elapsed time : ", round((end - start) / 60.0, 2), " minutes")

    # write network information to the file
    info = "Number of vertex : " + str(len(universal_graph.get_vertices())) + "\nNumber of edge : " + str(
        len(universal_graph.get_edges())) + f"\nElapsed time : " + str(round((end - start) / 60.0, 2)) + " minutes"
    # json_file_path = 'toyExample/toyDataset/toy_networkInfo.txt'
    json_file_path = 'Databases/universalGraph_with_omniPath_Filtered.txt'
    f = open(json_file_path, "w")
    f.write(info)
