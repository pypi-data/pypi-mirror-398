import ijson
import json

# Dictionary for ec-code : key:ec-code, value:list of uniport id
dict_ec = {}

'''with open('/home/aycansahin/Desktop/itu/pythonProject/Databases/uniprotkb_AND_model_organism_9606_2023_11_30.json', 'r') as file:
    parser = ijson.items(file, 'results.item')
    for event in parser:
        if 'proteinDescription' in event :
            if 'recommendedName' in event['proteinDescription'] :
                if 'ecNumbers' in event['proteinDescription']['recommendedName'] :
                    for i in event['proteinDescription']['recommendedName']['ecNumbers'] :
                        if i['value'] in dict_ec :
                            dict_ec[i['value']].update([event['primaryAccession']])
                        else:
                            dict_ec[i['value']] = set([event['primaryAccession']])
                    #if 'secondaryAccessions' in event :
                    #    dict_ec[event['proteinDescription']['recommendedName']['ecNumbers'][0]['value']].update(event['secondaryAccessions'])

# print(dict_ec.keys())
converted_dict = {key: list(value) if isinstance(value, set) else value for key, value in dict_ec.items()}
json_file_path = 'ecDict.json'
with open(json_file_path, 'w') as file:
    json.dump(converted_dict, file, indent=2)

print("ec code saved!!!")'''

'''# Dictionary for name -> uniProtkbId, proteinDescriptions, genes, uniProtKBCrossReferences
dict_name = {}
uniport_data = {}
def flatten_dict(d, parent_key='', sep='_'):
    items = []
    for k, v in d.items():
        new_key = f"{parent_key}{sep}{k}" if parent_key else k
        if isinstance(v, dict):
            items.extend(flatten_dict(v, new_key, sep=sep).items())
        elif isinstance(v, list):
            for i, item in enumerate(v):
                new_list_key = f"{new_key}{sep}{i}"
                items.extend(flatten_dict(item, new_list_key, sep=sep).items())
        else:
            items.append((new_key, v))
    return dict(items)

with open('/home/aycansahin/Desktop/itu/pythonProject/Databases/uniprotkb_AND_model_organism_9606_2023_11_30.json', 'r') as file:
    parser = ijson.items(file, 'results.item')
    count = 0
    for event in parser :
        # uniport_data[event['primaryAccession']] = event
        # uniProtkbId
        if 'uniProtkbId' in event :
            if event['uniProtkbId'] in dict_name :
                dict_name[event['uniProtkbId']].update([event['primaryAccession']])
            else:
                dict_name[event['uniProtkbId']] = set([event['primaryAccession']])
        # proteinDescriptions
        if 'proteinDescription' in event :
            flatt = flatten_dict(event['proteinDescription'])
            for key in flatt :
                if 'value' in key :
                    if flatt[key] in dict_name :
                        dict_name[flatt[key]].update([event['primaryAccession']])
                    else:
                        dict_name[flatt[key]] = set([event['primaryAccession']])

        # genes
        if 'genes' in event :
            #for i in event['genes'] :
            flatt = flatten_dict({index: value for index, value in enumerate(event['genes'])} )
            for key in flatt :
                if 'value' in key :
                    if flatt[key] in dict_name :
                        dict_name[flatt[key]].update([event['primaryAccession']])
                    else:
                        dict_name[flatt[key]] = set([event['primaryAccession']])
        # uniProtKBCrossReferences
        if 'uniProtKBCrossReferences' in event :
            for i in event['uniProtKBCrossReferences'] :
                flatt = flatten_dict(i)
                for key in flatt :
                    if 'id' in key :
                        if flatt[key] in dict_name :
                            dict_name[flatt[key]].update([event['primaryAccession']])
                        else:
                            dict_name[flatt[key]] = set([event['primaryAccession']])

        if count % 10000 == 0 :
            print(count, " entity saved!")
        count+=1

converted_dict_name = {key: list(value) if isinstance(value, set) else value for key, value in dict_name.items()}
json_file_path = 'nameDict.json'
with open(json_file_path, 'w') as file:
    json.dump(converted_dict_name, file, indent=2)'''

# Dictionary for uniport data
'''uniport_data = {}
count = 0
with open('/home/aycansahin/Desktop/itu/pythonProject/Databases/uniprotkb_AND_model_organism_9606_2023_11_30.json', 'r') as file:
    parser = ijson.items(file, 'results.item')
    count = 0
    for event in parser :
        row = {}
        uniport_data[event['primaryAccession']] = {}
        if 'secondaryAccessions' in event :
            uniport_data[event['primaryAccession']].update({'secondaryAccessions' : event['secondaryAccessions']})
        if 'organism' in event :
            uniport_data[event['primaryAccession']].update({'organism' : event['organism']})
        if 'sequence' in event :
            uniport_data[event['primaryAccession']].update({'sequence' : event['sequence']})
        if 'extraAttributes' in event :
            uniport_data[event['primaryAccession']].update({'extraAttributes' : event['extraAttributes']})
        if count % 1000 == 0 :
            print(count, " entity readed")
        count += 1

json_file_path = 'uniportData.json'
with open(json_file_path, 'w') as file:
    json.dump(uniport_data, file, indent=2)'''

ccdc_uniprot = {}
count = 0
with open('/home/aycansahin/Desktop/itu/pythonProject/Databases/uniprotkb_AND_model_organism_9606_2023_11_30.json', 'r') as file:
    parser = ijson.items(file, 'results.item')
    count = 0
    for event in parser :
        if 'uniProtKBCrossReferences' in event :
            for i in event['uniProtKBCrossReferences'] :
                if i['database'] == "CCDS":
                    if i['id'] in ccdc_uniprot :
                        ccdc_uniprot[i['id']].update([event['primaryAccession']])
                    else:
                        ccdc_uniprot[i['id']] = set([event['primaryAccession']])

converted_dict_name = {key: list(value) if isinstance(value, set) else value for key, value in ccdc_uniprot.items()}
json_file_path = 'ccdc_uniprot.json'
with open(json_file_path, 'w') as file:
    json.dump(converted_dict_name, file, indent=2)
