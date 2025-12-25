# %%
from .config import INTERIM_DATA_DIR, EXTERNAL_DATA_DIR

import pandas as pd
import json
from tqdm import tqdm
from pathlib import Path
import typer

# %%
STANDARD_NAMES_CSV = EXTERNAL_DATA_DIR / 'Standard_infomation/20250224_Standard_names.csv'

# %%
app = typer.Typer(add_completion=False)

# %%
class PubChemCompound:
    def __init__(self, input_json):
        with open(input_json) as f:
            self.compound_info = json.load(f)
        self.compound_cid = self.compound_info['Record']['RecordNumber']
        self.compound_title = self.compound_info['Record']['RecordTitle']
        self.compound_data = self.compound_info['Record']['Section']

    @staticmethod
    def list_tocheadings(json_data):
        tocheadings = [x['TOCHeading'] for x in json_data]
        return tocheadings

    def slice_json_data(self, json_data, tocheading):
        tocheadings = self.list_tocheadings(json_data)
        if tocheading not in tocheadings:
            return None
        sliced_json_data = json_data[tocheadings.index(tocheading)]
        if 'Section' in sliced_json_data.keys():
            return sliced_json_data['Section']
        elif 'Information' in sliced_json_data.keys():
            return sliced_json_data['Information']
        else:
            return sliced_json_data

    def get_melocular_formula(self):
        json_data = self.slice_json_data(self.compound_data, 'Names and Identifiers')
        json_data = self.slice_json_data(json_data, 'Molecular Formula')
        molecular_formula = [y['String'] for x in json_data for y in x['Value']['StringWithMarkup']]
        return molecular_formula

    def get_synonym(self):
        synonym = [self.compound_title]
        json_data = self.slice_json_data(self.compound_data, 'Names and Identifiers')
        json_data = self.slice_json_data(json_data, 'Synonyms')
        try:
            synonym_data_mesh = self.slice_json_data(json_data, 'MeSH Entry Terms')[0]
            synonym_mesh = [x['String'] for x in synonym_data_mesh['Value']['StringWithMarkup']]
        except:
            synonym_mesh = []
            print(f'No MeSH Entry Terms in CID {self.compound_cid}')
        try:
            synonym_data_depositor = self.slice_json_data(json_data, 'Depositor-Supplied Synonyms')[0]
            synonym_depositor = [x['String'] for x in synonym_data_depositor['Value']['StringWithMarkup']]
        except:
            synonym_depositor = []
            print(f'No Depositor-Supplied Synonyms in CID {self.compound_cid}')
        synonym = synonym + synonym_mesh + synonym_depositor
        return synonym

# %%
def check_molecular_formula(standard_name_data_row):
    pubchem_compound = PubChemCompound(EXTERNAL_DATA_DIR / f'Standard_infomation/COMPOUND_CID_{standard_name_data_row["PubChem CID"]}.json')
    pubchem_molecular_formulas = pubchem_compound.get_melocular_formula()
    assert standard_name_data_row['Formula'] in pubchem_molecular_formulas, \
        f'Maybe used wrong file: COMPOUND_CID_{standard_name_data_row["PubChem CID"]}.json: ' + \
        f'{standard_name_data_row["Formula"]} not in {pubchem_molecular_formulas}'
    return True

def get_pubchem_synonym(standard_name_data_row):
    pubchem_compound = PubChemCompound(EXTERNAL_DATA_DIR / f'Standard_infomation/COMPOUND_CID_{standard_name_data_row["PubChem CID"]}.json')
    pubchem_synonyms = pubchem_compound.get_synonym()
    return pubchem_synonyms

# %%
def read_standard_names_data(input_csv=STANDARD_NAMES_CSV):
    standard_name_data = pd.read_csv(input_csv)
    standard_name_data.dropna(subset=['PubChem CID'], inplace=True)
    standard_name_data['PubChem CID'] = standard_name_data['PubChem CID'].astype(int)
    assert standard_name_data.apply(check_molecular_formula, axis=1).all(), 'Some molecular formula is not matched'

    standard_name_data['PubChem synonyms'] = standard_name_data.apply(get_pubchem_synonym, axis=1)
    standard_name_data = standard_name_data[['Working name', 'PubChem synonyms']].explode('PubChem synonyms')
    standard_name_data['lowercase PubChem synonyms'] = standard_name_data['PubChem synonyms'].str.lower()
    standard_name_data.drop_duplicates(subset=['lowercase PubChem synonyms'], inplace=True)
    return standard_name_data

def read_msdial_quan_data(input_tsv):
    quan_data = pd.read_table(
        input_tsv,
        index_col=[i for i in range(32)],
        header=4,
        sep='\t'
    )
    quan_data.drop(columns=quan_data.columns[-2:], inplace=True) # drop last two unused columns: Average Stdev
    quan_data.reset_index(inplace=True, level=['Alignment ID', 'Metabolite name', 'Adduct type'])
    quan_data.reset_index(inplace=True, drop=True)
    quan_data['lowercase Metabolite name'] = quan_data['Metabolite name'].str.lower()
    return quan_data

# %%
def extract_standard_from_quan_data(standard_name_data, quan_data):
    extracted_quan_data_list = []
    for i, row in tqdm(standard_name_data.iterrows()):
        extracted_data = quan_data.query('@row["lowercase PubChem synonyms"] in `lowercase Metabolite name`')
        if extracted_data.empty:
            continue
        extracted_data.insert(0, 'Working name', row['Working name'])
        extracted_data.insert(1, 'PubChem synonyms', row['PubChem synonyms'])
        extracted_quan_data_list.append(extracted_data)
    extracted_quan_data = pd.concat(extracted_quan_data_list)
    extracted_quan_data.drop(columns=['lowercase Metabolite name'], inplace=True)
    return extracted_quan_data


# %%
@app.command()
def get_standard_quan(
    standard_names_csv: Path = STANDARD_NAMES_CSV,
    msdial_quan_tsv: Path = Path('.'),
    output_csv: Path = Path('.')
):
    standard_name_data = read_standard_names_data(standard_names_csv)
    msdial_quan_data = read_msdial_quan_data(msdial_quan_tsv) # EXTERNAL_DATA_DIR / 'MS-DIAL/20250206_Standards of HESI and multi-emitter analysis/standards-NEG_Area_0_20252241137.txt'
    extracted_quan_data = extract_standard_from_quan_data(standard_name_data, msdial_quan_data)
    extracted_quan_data.to_csv(output_csv, index=False)

@app.callback()
def callback():
    pass

# %%
if __name__ == '__main__':
    app()