import pandas as pd
import numpy as np
from ..cobra.io import load_json_model
from .graph import Graph
import time
import json

with open('Databases/ecDict.json', 'r') as json_file:
    ec_dict = json.load(json_file)

with open('Databases/nameDict.json', 'r') as json_file:
    name_dict = json.load(json_file)

#with open('uniportData.json', 'r') as json_file:
#    uniport_dict = json.load(json_file)

def get_uniport_byEc(ec_code) :
    return ec_dict[ec_code]

def get_uniport_gname(gene_name):
    return name_dict[gene_name]

if __name__ == '__main__':

    start = time.time()
    universal_graph = Graph()

    modelREcon3d = load_json_model('Databases/Recon3D.json')
    count = 0
    empty = 0
    error = 0
    for r in modelREcon3d.reactions :
        if r.gene_reaction_rule != '' :
            try :
                universal_graph.add_vertex(r.id, label=[], vert_info = {'metabolites' : [{str(metabolite) : coefficient for metabolite, coefficient in r.metabolites.items()}]}, omic_type='R')
                # print(r.id)
                # get related enzym by ec-code
                if 'ec-code' in r.annotation :
                    for ec in r.annotation['ec-code'] :
                        for i in get_uniport_byEc(ec) :
                            universal_graph.add_vertex(i, label=[], vert_info ={}, omic_type='enzyme')
                            universal_graph.add_edge(i, r.id, int_info = {'type' : universal_graph.get_vertex(i).get_omic_type() + " - " + universal_graph.get_vertex(r.id).get_omic_type()} )
                # get related genes
                for gen in r.genes :
                    label = get_uniport_gname(gen.name)
                    universal_graph.add_vertex(label[0], label=label, vert_info ={}, omic_type='gene')
                    universal_graph.add_edge(r.id, label[0], int_info = {'type' : universal_graph.get_vertex(r.id).get_omic_type() + " - " + universal_graph.get_vertex(label[0]).get_omic_type()})
            except Exception as e:
                error += 1
                # print(f"Error processing {r} : {e}")
                continue
        else :
            empty += 1
        if count % 1000 == 0:
            print(count, " reactions are done")
            print(error, ' error occured')
        count += 1
    print("The number of reactions which is gene_reaction rule is empty : ", empty)
    print("Number of error : " , error)
    print("recon finish")

    # Adding TRRUST(TF-gene) database to network
    columns = ['TF', 'Target', 'Mode of Regulation', 'References (PMID)']
    trrust_tfg = pd.read_csv('Databases/trrust_rawdata.human.tsv', sep='\t', names=columns)
    count = 0
    error = 0
    for j in trrust_tfg.values :
        try :
            label_tf = get_uniport_gname(j[0])
            universal_graph.add_vertex(label_tf[0], label_tf, vert_info ={}, omic_type='TF') # TF : Transcriptional Factor
            label_target = get_uniport_gname(j[1])
            universal_graph.add_vertex(label_target[0], label_target, vert_info ={}, omic_type='gene')

            universal_graph.add_edge(label_tf[0], label_target[0], int_info = {'type' : universal_graph.get_vertex(label_tf[0]).get_omic_type() + " - " + universal_graph.get_vertex(label_target[0]).get_omic_type(), 'Mode of Regulation' : j[2]} )
        except Exception as e:
            error += 1
            # print(f"Error processing {j}: {e}")
            continue
        if count % 10000 == 0:
            print(count, " trrust rows are done")
            print(error, ' error occured')
        count += 1
    print("Number of error : " , error)
    print("trrust finish")

    # Adding intact(p-p) database to network
    intact_pp = pd.read_csv('Databases/intact-micluster.txt', sep='\t')
    # Remove rows where column innate_pp['Taxid interactor A' and 'Taxid interactor B'] != 'taxid:9606(human)'
    intact_pp = intact_pp.drop(intact_pp[(intact_pp['Taxid interactor A'] != 'taxid:9606(human)') | (intact_pp['Taxid interactor B'] != 'taxid:9606(human)')].index)
    count = 0
    error = 0
    for j in intact_pp.values :
        try :
            source = j[4].split('|')[1][7:]
            target = j[5].split('|')[1][7:]
            label_s = get_uniport_gname(source)
            label_t = get_uniport_gname(target)
            '''source = j[2][10:]
            target = j[3][10:]
            if '-' in source :
                ind_of_char = source.find('-')
                source = source[:ind_of_char]
            if '-' in target :
                ind_of_char = target.find('-')
                target = target[:ind_of_char]'''
            universal_graph.add_vertex(label_s[0], label=label_s, vert_info ={}, omic_type='protein')
            universal_graph.add_vertex(label_t[0], label=label_t, vert_info ={}, omic_type='protein')

            # different Interaction detection method(s) gives different Interaction type(s) for one row
            key = j[6].split('|')
            value = j[11].split('|')
            a = dict(zip(key, value))
            universal_graph.add_edge(label_s[0], label_t[0], int_info = {'type' : universal_graph.get_vertex(label_s[0]).get_omic_type() + " - " + universal_graph.get_vertex(label_t[0]).get_omic_type(), 'Interaction type(s)' : a, 'Confidence value(s)' : j[14]} )
        except Exception as e:
            error += 1
            continue
        if count % 10000 == 0:
            print(count, " intact rows are done")
            print(error, ' error occured')
        count += 1
    print("Number of error : " , error)
    print("intact finish")

    mirTarBase = pd.read_excel('Databases/hsa_MTI.xlsx')
    count = 0
    error = 0
    for j in mirTarBase.values :
        try :
            label_target = get_uniport_gname(j[3])
            universal_graph.add_vertex(label_target[0], label_target, vert_info={}, omic_type='gene')
            # label_target, info_target = get_uniprot_id(j[1])
            universal_graph.add_vertex(j[1], label=[j[1]], vert_info={'int_id' : j[0]} , omic_type='miRNA')

            universal_graph.add_edge(j[1], label_target[0], int_info={'type' : universal_graph.get_vertex(j[1]).get_omic_type() + " - " + universal_graph.get_vertex(label_target[0]).get_omic_type(), 'Support Type References ' : j[7]} )
        except Exception as e:
            error += 1
            #print(f"Error processing {j}: {e}")
            continue
        if count % 10000 == 0:
            print(count, " mirTarBase rows are done")
            print(error, ' error occured')
        count += 1
    print("Number of error : " , error)
    print("mirTarBase finish")


    print("Number of vertex : ", len(universal_graph.get_vertices()))
    print("Number of edge : ", len(universal_graph.get_edges()))

    universal_graph.save_to_json("Databases/universalGraph.json")

    end = time.time()
    print(f"Elapsed time : ",  round((end-start)/60.0, 2), " minutes")

    # write network information to the file
    info = "Number of vertex : " + str(len(universal_graph.get_vertices())) + "\nNumber of edge : " + str(len(universal_graph.get_edges())) + f"\nElapsed time : " + str(round((end-start)/60.0, 2)) + " minutes"
    json_file_path = 'Databases/networkInfo.txt'
    f = open(json_file_path, "w")
    f.write(info)


    # for cytoscape
    '''react = pd.DataFrame(columns=['Source', 'Source_Omic_Type', 'Target', 'Target_Omic_Type'])
    colored = pd.DataFrame(columns=['Name', 'Color'])
    for i in universal_graph.get_edges() :
        react.loc[len(react)] = [i.get_start_vertex().get_id(), i.get_start_vertex().get_omic_type(), i.get_end_vertex().get_id(), i.get_end_vertex().get_omic_type()]
        colored.loc[len(colored)] = [i.get_start_vertex().get_id(), i.get_start_vertex().get_omic_type()]
        colored.loc[len(colored)] = [i.get_end_vertex().get_id(), i.get_end_vertex().get_omic_type()]
    react.to_csv('Databases/react_graph.tsv', index=False, sep="\t")
    colored.to_csv('Databases/colored.tsv', index=False, sep="\t")'''

