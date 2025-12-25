import json


def drug_target_file():
    with open('analysis/Data/drug_target_UniprotID_all.json') as f:
        return json.load(f)


def converter_func(model='recon3D'):
    if model == 'recon2':
        with open('analysis/Data/uniprot_hgnc_converter.json') as f:
            return json.load(f)
    elif model == 'recon3D':
        with open('analysis/Data/Uniprot_Entrez_Converter.json') as f:
            return json.load(f)
    elif model == 'recon301':
        with open('analysis/Data/converter301.json') as f:
            return json.load(f)



"""def breastCancerDrugs():
    with open('/home/enis/DrugAnalysis/metabolitics/analysis/Data/breast_cancer_drugs_set') as f:
        return json.load(f)
"""

class DrugReactionAnalysis:
    def __init__(self, model='recon3D'):
        """
        :param drugs: iterable just has the id's of drugs
        :param targets: dictionary keys are drug ids and values are target gene ids
        :param converter: dictionary keys are in the type of target dictionary values, values are the type we want to
        have
        """
        self.targets = drug_target_file()
        self.converter = converter_func(model=model)

    def drug_target(self, drug_id):
        """
        :param drug_id: string that has information about drugs id's and serves as a key in self.targets
        :return:
        """
        return self.convert(self.targets[drug_id])

    def convert(self, target):
        """
        :param target: iterable item has target ids
        :return: converted version of ids depending on the converting file
        """
        r = []
        for t in target:
            try:
                r.append(self.converter[t])
            except:
                continue
        return r

