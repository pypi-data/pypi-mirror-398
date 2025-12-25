# This is a sample Python script.
#!/bin/python3
# Press Shift+F10 to execute it or replace it with your code.
# Press Double Shift to search everywhere for classes, files, tool windows, actions, and settings.
import pandas as pd
import numpy as np
from numba.cuda import cg
from ..cobra.io import load_json_model
import cobra
from bioservices import UniProt
from .graph import Graph
from .graph_visualizer import display_graph
import time
import ijson
import json
import requests
# Press the green button in the gutter to run the script.

ecdict = json.load('ecDict.json')

def get_result(result) :
    i = result['results'][0]
    label = [{'database' : 'uniport', 'id' : i['primaryAccession']}]
    if 'secondaryAccessions' in i :
        for k in i['secondaryAccessions'] :
            label.append({'database' : 'uniport', 'id' : k})

    if 'uniProtKBCrossReferences' in i :
        for j in i['uniProtKBCrossReferences'] :
            items = list(j.items())
            first_two_elements = items[:2]
            new_dict = dict(first_two_elements)
            label.append(new_dict)

    return(label[0]['id'], label, i)

def get_uniport_gname(gene_name):
    u = UniProt()
    taxon_id = 9606
    result = u.search(f'gene:{gene_name}+and+taxonomy_id:{taxon_id}', frmt='json')
    print()
    return get_result(result)
'''with open('Databases/uniprotkb_AND_model_organism_9606_2023_11_30.json', 'r') as file:
    parser = ijson.items(file, 'results.item')
    for event in parser:
        if 'genes' in event :
            if gene_name == event['genes'][0]['geneName']['value']:
                return get_result(event)
            elif 'synonyms' in event['genes'][0].keys() :
                for i in event['genes'][0]['synonyms'] :
                    if gene_name == i['value'] :
                        return get_result(event)'''



def get_uniport_byId(accession_id):
    u = UniProt()
    result = u.search(accession_id, frmt='json')
    return get_result(result)

def get_uniport_byEc(ec_code) :
    u = UniProt()
    taxon_id = 9606
    result = u.search(f'ec:{ec_code}+and+taxonomy_id:{taxon_id}', frmt='json')
    return get_result(result)

if __name__ == '__main__':

    start = time.time()
    universal_graph = Graph()

    modelREcon3d = load_json_model('Databases/Recon3D.json')
    empty = 0
    for r in modelREcon3d.reactions[20:25] :
        if r.gene_reaction_rule != '' :
            try :
                universal_graph.add_vertex(r.id, [], vert_info = r, omic_type='R')
                # print(r.id)
                # get related enzym by ec-code
                if 'ec-code' in r.annotation :
                    for ec in r.annotation['ec-code'] :
                        id_e, label_e, info_e = get_uniport_byEc(ec)
                        universal_graph.add_vertex(id_e, label_e, info_e, omic_type='enzyme')
                        universal_graph.add_edge(id_e, r.id, int_info = {} )
                # get related genes
                for gen in r.genes :
                    print(gen.name)
                    id_g, label_g, info_g = get_uniport_gname(gen.name)
                    universal_graph.add_vertex(id_g, label_g, info_g, omic_type='gene')
                    universal_graph.add_edge(r.id, id_g, int_info = {} )
            except Exception as e:
                # Handle the error and continue the loop
                print(f"Error processing {r}: {e}")
                continue
        else :
            print("empty")
            empty += 1

    print("The number of reactions which is gene_reaction rule is empty : ", empty)
    print("recon finish")

    # Adding TRRUST(TF-gene) database to network
    columns = ['TF', 'Target', 'Mode of Regulation', 'References (PMID)']
    trrust_tfg = pd.read_csv('Databases/trrust_rawdata.human.tsv', sep='\t', names=columns)
    count = 0
    for j in trrust_tfg.values[:1000] :
        try :
            id_tf, label_tf, info_tf = get_uniport_gname(j[0])
            universal_graph.add_vertex(id_tf, label_tf, info_tf, omic_type='TF') # TF : Transcriptional Factor
            print(id_tf)
            id_target, label_target, info_target = get_uniport_gname(j[1])
            universal_graph.add_vertex(id_target, label_target, info_target, omic_type='gene')

            universal_graph.add_edge(id_tf, id_target, int_info = {'Mode of Regulation' : j[2]} )

            if count==5 :
                print(count)
                break
            count += 1
        except Exception as e:
            print(f"Error processing {j}: {e}")
            continue
    print("trrust finish")

    # Adding intact(p-p) database to network
    intact_pp = pd.read_csv('Databases/intact-micluster.txt', sep='\t')
    # Remove rows where column innate_pp['Taxid interactor A' and 'Taxid interactor B'] != 'taxid:9606(human)'
    intact_pp = intact_pp.drop(intact_pp[(intact_pp['Taxid interactor A'] != 'taxid:9606(human)') | (intact_pp['Taxid interactor B'] != 'taxid:9606(human)')].index)
    count = 0
    for j in intact_pp.values[:1000] :
        try :
            id_tf, label_tf, info_tf = get_uniport_byId(j[2][10:])
            universal_graph.add_vertex(id_tf, label_tf, info_tf, omic_type='protein')
            print(id_tf)
            id_target, label_target, info_target = get_uniport_byId(j[3][10:])
            universal_graph.add_vertex(id_target, label_target, info_target, omic_type='protein')

            # different Interaction detection method(s) gives different Interaction type(s) for one row
            key = j[6].split('|')
            value = j[11].split('|')
            a = dict(zip(key, value))
            universal_graph.add_edge(id_tf, id_target, int_info = {'Interaction type(s)' : a, 'Confidence value(s)' : j[14]} )
            if count==5 :
                print(count)
                break
            count += 1
        except Exception as e:
            print(f"Error processing {j}: {e}")
            continue
    print("intact finish")

    mirTarBase = pd.read_excel('Databases/hsa_MTI.xlsx')
    # print(mirTarBase)
    count = 0
    for j in mirTarBase.values[:1000] :
        try :
            id_target, label_target, info_target = get_uniport_gname(j[3])
            universal_graph.add_vertex(id_target, label_target, info_target, omic_type='gene')
            print(id_target)
            # label_target, info_target = get_uniprot_id(j[1])
            universal_graph.add_vertex(j[1], label=[{'database' : 'mirTarBase', 'id' : j[1]}], vert_info={'int_id' : j[0]} , omic_type='miRNA')

            universal_graph.add_edge(j[1], id_target, int_info={'Support Type References ' : j[7]} )
            if count==5 :
                print(count)
                break
            count += 1
        except Exception as e:
        # Handle the error and continue the loop
            print(f"Error processing {j}: {e}")
            continue

    # for cytoscape
    react = pd.DataFrame(columns=['Source', 'Source_Omic_Type', 'Target', 'Target_Omic_Type'])
    colored = pd.DataFrame(columns=['Name', 'Color'])
    for i in universal_graph.get_edges() :
        react.loc[len(react)] = [i.get_start_vertex().get_id(), i.get_start_vertex().get_omic_type(), i.get_end_vertex().get_id(), i.get_end_vertex().get_omic_type()]
        colored.loc[len(colored)] = [i.get_start_vertex().get_id(), i.get_start_vertex().get_omic_type()]
        colored.loc[len(colored)] = [i.get_end_vertex().get_id(), i.get_end_vertex().get_omic_type()]
    react.to_csv('react_graph.tsv', index=False, sep="\t")
    colored.to_csv('colored.tsv', index=False, sep="\t")

    print("Number of vertex : ", len(universal_graph.get_vertices()))
    print("NUmber of edge : ", len(universal_graph.get_edges()))

    end = time.time()
    print(f"Elapsed time : ",  round((end-start)/60.0, 2), " minutes")
    # print(universal_graph)

    # display_graph(universal_graph, "Universal Interaction Network")


# See PyCharm help at https://www.jetbrains.com/help/pycharm/
