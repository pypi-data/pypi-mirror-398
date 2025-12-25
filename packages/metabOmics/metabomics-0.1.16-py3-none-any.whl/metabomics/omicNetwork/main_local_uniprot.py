import pandas as pd
import numpy as np
from ..cobra.io import load_json_model
from .graph import Graph
import time
import json
import re

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
        for gene in genes :
            gene = gene.replace('(', '').replace(')', '')
            if 'ccds' in modelREcon3d.genes.get_by_id(gene).annotation.keys() :
                for i in modelREcon3d.genes.get_by_id(gene).annotation['ccds']:
                    if i in ccdc_uniprot.keys():
                        temp.extend(ccdc_uniprot[i])
                        break
        gene_lists.append(temp)
    return gene_lists

if __name__ == '__main__':

    start = time.time()
    universal_graph = Graph()

    modelREcon3d = load_json_model('Databases/Recon3D.json')
    empty = 0
    unique_gene = set()
    nogene = []
    for r in modelREcon3d.reactions :
        if r.gene_reaction_rule != '' :
            #try :
            universal_graph.add_vertex(r.id, label=[r.id], vert_info = {'metabolites' : [{str(metabolite) : coefficient for metabolite, coefficient in r.metabolites.items()}], 'gpr' : parse_gpr_expression(str(r.gpr), ccdc_uniprot, modelREcon3d)}, omic_type='R')
           # get related genes
            for gen in r.genes :
                unique_gene.add(gen.name)
                if 'ccds' in gen.annotation.keys() :
                    for i in gen.annotation['ccds'] :
                        if i in ccdc_uniprot.keys() :
                            label = ccdc_uniprot[i]
                            break
                elif gen.id in ccdc_uniprot.keys():
                    label = ccdc_uniprot[gen.id]
                else :
                    nogene.append(gen.name)
                if label[0] not in universal_graph.get_vertices() :
                    universal_graph.add_vertex(label[0], label=[gen.name], vert_info ={}, omic_type='gene')
                    label_tx = label[0]+'_transcript_x'
                    universal_graph.add_vertex(label_tx, label=[gen.name+'_transcript_x'], vert_info ={}, omic_type='transcript')
                    universal_graph.add_edge(label[0], label_tx, int_info = {'type' : universal_graph.get_vertex(label[0]).get_omic_type() + " - " + universal_graph.get_vertex(label_tx).get_omic_type(), 'interaction' : {0:'transcribed_to'}})
                    label_px = label[0]+'_protein_x'
                    universal_graph.add_vertex(label_px, label=[gen.name+'_protein_x'], vert_info ={}, omic_type='protein')
                    universal_graph.add_edge(label_tx, label_px, int_info = {'type' : universal_graph.get_vertex(label_tx).get_omic_type() + " - " + universal_graph.get_vertex(label_px).get_omic_type(), 'interaction' : {0:'translated_to'}})
                    universal_graph.add_edge(label_px, r.id, int_info = {'type' : universal_graph.get_vertex(label_px).get_omic_type() + " - " + universal_graph.get_vertex(r.id).get_omic_type(), 'interaction' : {0:'catalyzes'}})
                else:
                    universal_graph.add_edge(label[0]+'_protein_x', r.id, int_info = {'type' : universal_graph.get_vertex(label[0]+'_protein_x').get_omic_type() + " - " + universal_graph.get_vertex(r.id).get_omic_type(), 'interaction' : {0:'catalyzes'}})
            #except Exception as e:
            #    error += 1
            #    print(f"Error processing {r.genes} : {e}")
            #    continue
        else :
            empty += 1
        #if count % 500 == 0:
            #print(count, " reactions are done")
            #print(error, ' error occured')
            # break

    count = 0
    for i, v in universal_graph.get_vertices().items():
        if v.get_omic_type() == 'gene':
            count += 1
    print("The number of rows in recon3d: ", len(modelREcon3d.reactions))
    print("The number of reactions which is gene_reaction rule is empty : ", empty)
    print("Number of unique gene : " , len(unique_gene))
    print("Number of not found unprot id of gene is : ", set(nogene));
    print("Numer of vertex after Recon3d : ", len(universal_graph.get_vertices()))
    print("Number of edge after Recon3d : ", len(universal_graph.get_edges()))
    print("Number of gene after Recon3d : ", count)
    print("recon finish")

    # Adding TRRUST(TF-gene) database to network
    trrust_tfg = pd.read_csv('Databases/trrust_uniprot_human.tsv', sep='\t')
    count = 1
    error = 0
    for j in trrust_tfg.values :
        try :
            label_tf = str(j[1]) + '_x'
            if universal_graph.add_vertex(label_tf, [j[0]+ '_x'], vert_info ={}, omic_type='gene') :
                label_tf = str(j[1])
            label_tf_tx = str(j[1])+'_transcript_x'
            universal_graph.add_vertex(label_tf_tx, [j[0]+'_transcript_x'], vert_info ={}, omic_type='transcript') # TF : Transcriptional Factor
            universal_graph.add_edge(label_tf, label_tf_tx, int_info = {'type' : universal_graph.get_vertex(label_tf).get_omic_type() + " - " + universal_graph.get_vertex(label_tf_tx).get_omic_type(), 'interaction' : {0:'transcribed_to'}})
            label_tf_px = str(j[1]) +'_protein'
            universal_graph.add_vertex(label_tf_px, label=[j[0]+'_protein'], vert_info ={}, omic_type='TF')
            universal_graph.add_edge(label_tf_tx, label_tf_px, int_info = {'type' : universal_graph.get_vertex(label_tf_tx).get_omic_type() + " - " + universal_graph.get_vertex(label_tf_px).get_omic_type(), 'interaction' : {0:'translated_to'}})

            label_target = str(j[3])
            universal_graph.add_vertex(label_target, [j[2]], vert_info ={}, omic_type='gene')
            label_target_tx = label_target+'_transcript_x'
            universal_graph.add_vertex(label_target_tx, [j[2]+'_transcript_x'], vert_info ={}, omic_type='transcript')
            universal_graph.add_edge(label_target, label_target_tx, int_info = {'type' : universal_graph.get_vertex(label_target).get_omic_type() + " - " + universal_graph.get_vertex(label_target_tx).get_omic_type(), 'interaction' : {0:'transcribed_to'}})
            label_target_px = label_target +'_protein_x'
            if universal_graph.add_vertex(label_target_px, label=[j[2]+'_protein_x'], vert_info ={}, omic_type='protein') :
                label_target_px = label_target_px[:-2]
            universal_graph.add_edge(label_target_tx, label_target_px, int_info = {'type' : universal_graph.get_vertex(label_target_tx).get_omic_type() + " - " + universal_graph.get_vertex(label_target_px).get_omic_type(), 'interaction' : {0:'translated_to'}})

            universal_graph.add_edge(label_tf_px, label_target, int_info = {'type' : universal_graph.get_vertex(label_tf_px).get_omic_type() + " - " + universal_graph.get_vertex(label_target).get_omic_type(), 'interaction' : {0 : j[4]}} )
        except Exception as e:
            error += 1
            print(f"Error processing {j}: {e}")
            continue

    count = 0
    for i, v in universal_graph.get_vertices().items():
        if v.get_omic_type() == 'gene':
            count += 1
    print("Number of error : " , error)
    print("the number of rows in TRRUST: ", len(trrust_tfg.values))
    print("Numer of vertex after TRRUST : ", len(universal_graph.get_vertices()))
    print("Number of edge after TRRUST : ", len(universal_graph.get_edges()))
    print("Number of gene after TRRUST : ", count)
    print("trrust finish")

    '''# Adding intact(p-p) database to network
    intact_pp = pd.read_csv('Databases/intact-micluster.txt', sep='\t')
    # Remove rows where column innate_pp['Taxid interactor A' and 'Taxid interactor B'] != 'taxid:9606(human)'
    intact_pp = intact_pp.drop(intact_pp[(intact_pp['Taxid interactor A'] != 'taxid:9606(human)') | (intact_pp['Taxid interactor B'] != 'taxid:9606(human)')].index)
    count = 1
    error = 0
    for j in intact_pp.values :
        try :
            source = j[2][10:]
            target = j[3][10:]
            if '-' in source :
                ind_of_char = source.find('-')
                source = source[:ind_of_char]
            if '-' in target :
                ind_of_char = target.find('-')
                target = target[:ind_of_char]
            source_x = source + '_x'
            if universal_graph.add_vertex(source_x, label=[j[4].split('|')[1][7:]+'_x'], vert_info ={}, omic_type='gene') :
                source_x = source
            source_tr = source + '_transcript_x'
            universal_graph.add_vertex(source_tr, label=[j[4].split('|')[1][7:] + '_transcript_x'], vert_info ={}, omic_type='transcript')
            universal_graph.add_edge(source_x, source_tr, int_info = {'type' : universal_graph.get_vertex(source_x).get_omic_type() + " - " + universal_graph.get_vertex(source_tr).get_omic_type(), 'interaction' : {0:'transcribed_to'}} )
            source_pr = source + '_protein'
            universal_graph.add_vertex(source_pr, label=[j[4].split('|')[1][7:] +'_protein'], vert_info ={}, omic_type='protein')
            universal_graph.add_edge(source_tr, source_pr, int_info = {'type' : universal_graph.get_vertex(source_tr).get_omic_type() + " - " + universal_graph.get_vertex(source_pr).get_omic_type(), 'interaction' : {0:'translated_to'}} )

            target_x = target + '_x'
            if universal_graph.add_vertex(target_x, label=[j[5].split('|')[1][7:]+'_x'], vert_info ={}, omic_type='gene') :
                target_x = target
            target_tr = target + '_transcript_x'
            universal_graph.add_vertex(target_tr, label=[j[5].split('|')[1][7:] + '_transcript_x'], vert_info ={}, omic_type='transcript')
            universal_graph.add_edge(target_x, target_tr, int_info = {'type' : universal_graph.get_vertex(target_x).get_omic_type() + " - " + universal_graph.get_vertex(target_tr).get_omic_type(), 'interaction' : {0:'transcribed_to'}} )
            target_pr = target + '_protein'
            universal_graph.add_vertex(target_pr, label=[j[5].split('|')[1][7:] +'_protein'], vert_info ={}, omic_type='protein')
            universal_graph.add_edge(target_tr, target_pr, int_info = {'type' : universal_graph.get_vertex(target_tr).get_omic_type() + " - " + universal_graph.get_vertex(target_pr).get_omic_type(), 'interaction' : {0:'translated_to'}} )


            # different Interaction detection method(s) gives different Interaction type(s) for one row
            key = j[6].split('|')
            value = j[11].split('|')
            a = dict(zip(key, value))
            universal_graph.add_edge(source_pr, target_pr, int_info = {'type' : universal_graph.get_vertex(source_pr).get_omic_type() + " - " + universal_graph.get_vertex(target_pr,).get_omic_type(), 'interaction' : a , 'Confidence value(s)' : j[14]} )
        except Exception as e:
            error += 1
            continue
        if count % 100 == 0:
            print(count, " intact rows are done")
            print(error, ' error occured')
            break
        count += 1
    print("Number of error : " , error)
    print(count)
    print("intact finish")'''
    count = 1
    mirTarBase = pd.read_csv('Databases/mirtarbase_uniprot.tsv', sep='\t')
    error = 0
    for j in mirTarBase.values :
        try :
            label_target = j[4]
            # print(label_target)
            universal_graph.add_vertex(label_target, [j[3]], vert_info={}, omic_type='gene')
            label_target_tr = j[4] + '_transcript_x'
            universal_graph.add_vertex(label_target_tr, [j[3]+'_transcript_x'], vert_info={}, omic_type='transcript')
            universal_graph.add_edge(label_target, label_target_tr, int_info = {'type' : universal_graph.get_vertex(label_target).get_omic_type() + " - " + universal_graph.get_vertex(label_target_tr).get_omic_type(), 'interaction' : {0:'transcribed_to'}} )
            label_target_pr = j[4] + '_protein_x'
            if universal_graph.add_vertex(label_target_pr, [j[3]+'_protein_x'], vert_info={}, omic_type='protein') :
                label_target_pr = label_target_pr[:-2]
            universal_graph.add_edge(label_target_tr, label_target_pr, int_info = {'type' : universal_graph.get_vertex(label_target_tr).get_omic_type() + " - " + universal_graph.get_vertex(label_target_pr).get_omic_type(), 'interaction' : {0:'translated_to'}} )

            # label_target, info_target = get_uniprot_id(j[1])
            universal_graph.add_vertex(j[1], label=[j[1]], vert_info={'int_id' : j[0]} , omic_type='miRNA')
            universal_graph.add_edge(j[1], label_target_tr, int_info={'type' : universal_graph.get_vertex(j[1]).get_omic_type() + " - " + universal_graph.get_vertex(label_target_tr).get_omic_type(), 'interaction' : {0:'Repression', j[8] : j[7]}} )
        except Exception as e:
            error += 1
            #print(f"Error processing {j}: {e}")
            continue
        if count % 100000 == 0:
            print(count, " mirTarBase rows are done")
            print(error, ' error occured')
            # break
        count += 1
    count = 0
    for i, v in universal_graph.get_vertices().items():
        if v.get_omic_type() == 'gene':
            count += 1
    print("Number of error : " , error)
    print("the number of rows in mirTarBase: ", len(mirTarBase.values))
    print("Number of gene after mirTarBase : ", count)
    print("mirTarBase finish")


    print("Number of vertex : ", len(universal_graph.get_vertices()))
    print("Number of edge : ", len(universal_graph.get_edges()))
    
    universal_graph.save_to_json("Databases/universalGraph.json")
    # universal_graph.save_to_json("toyExample/toyGraph.json")
    label_dict = {}
    for node in universal_graph.get_vertices() :
        label_dict[universal_graph.get_vertex(node).get_label()[0]] = universal_graph.get_vertex(node).get_id()
    with open("Databases/labelGraph.json", 'w') as json_file:
        json.dump(label_dict, json_file, indent=4)
    end = time.time()
    print(f"Elapsed time : ",  round((end-start)/60.0, 2), " minutes")

    # write network information to the file
    info = "Number of vertex : " + str(len(universal_graph.get_vertices())) + "\nNumber of edge : " + str(len(universal_graph.get_edges())) + f"\nElapsed time : " + str(round((end-start)/60.0, 2)) + " minutes"
    # json_file_path = 'toyExample/toyDataset/toy_networkInfo.txt'
    json_file_path = 'Databases/universal_networkInfo.txt'
    f = open(json_file_path, "w")
    f.write(info)

    '''# for cytoscape
    react = pd.DataFrame(columns=['Source', 'Source_Omic_Type', 'Target', 'Target_Omic_Type', 'Interaction'])
    colored = pd.DataFrame(columns=['Name', 'Color'])
    for i in universal_graph.get_edges().values() :
        #if "psi-mi:" in list(i.get_int_info()['interaction'].values())[0] :
        #    react.loc[len(react)] = [i.get_start_vertex().get_label()[0], i.get_start_vertex().get_omic_type(), i.get_end_vertex().get_label()[0], i.get_end_vertex().get_omic_type(), list(i.get_int_info()['interaction'].values())[0][16:]]
        #else :
        react.loc[len(react)] = [i.get_start_vertex().get_label()[0], i.get_start_vertex().get_omic_type(), i.get_end_vertex().get_label()[0], i.get_end_vertex().get_omic_type(), list(i.get_int_info()['interaction'].values())[0]]
        colored.loc[len(colored)] = [i.get_start_vertex().get_label()[0], i.get_start_vertex().get_omic_type()]
        colored.loc[len(colored)] = [i.get_end_vertex().get_label()[0], i.get_end_vertex().get_omic_type()]
    # react.to_csv('Databases/react_graph.tsv', index=False, sep="\t")
    # colored.to_csv('Databases/colored.tsv', index=False, sep="\t")
    react.to_csv('toyExample/toy_react_graph.tsv', index=False, sep="\t")
    colored.to_csv('toyExample/toy_colored.tsv', index=False, sep="\t")'''
