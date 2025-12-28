# PubChmAPI Library

## Overview

### Introduction

The **PubChmAPI** Python package simplifies interaction with the PubChem database via the PUG-REST API. Unlike traditional wrappers with hard-coded functions, PubChmAPI uses dynamic metaprogramming to generate endpoints, ensuring full coverage of the PubChem schema. It handles URL generation, automatic batching, and throttling to provide a seamless data retrieval experience.

---

## Naming Convention

Functions in **PubChmAPI** follow a strict semantic naming convention to eliminate ambiguity:

`domain_identifier_get_operation_option`

* **Domain:** The primary database being queried (e.g., `compound`, `substance`, `assay`, `gene`).
* **Identifier:** The input type provided (e.g., `cid`, `name`, `smiles`, `geneid`).
* **Operation:** The specific data to retrieve (e.g., `properties`, `aids`, `synonyms`).
* **Option (Optional):** Filters or variants (e.g., `active`, `inactive`, `2d`).

---

## Functions

### Compound Property Functions (By Name)

Retrieve calculated properties using a compound name (e.g., "Aspirin").
**Format:** `compound_name_get_[Property](identifier)`

#### Code Example

```python
# test_pubchmapi.py
from PubChmAPI import (
    compound_name_get_Title,
    compound_name_get_MolecularFormula,
    compound_name_get_MolecularWeight,
    compound_name_get_CanonicalSMILES,
    compound_name_get_InChI,
    compound_name_get_InChIKey,
    compound_name_get_IUPACName,
    compound_name_get_XLogP,
    compound_name_get_ExactMass
)

def test_pubchmapi():
    compound = "Aspirin"
    print("Testing PubChmAPI functions for:", compound)

    print("Title:", compound_name_get_Title(compound))
    print("Molecular Formula:", compound_name_get_MolecularFormula(compound))
    print("Molecular Weight:", compound_name_get_MolecularWeight(compound))
    print("Canonical SMILES:", compound_name_get_CanonicalSMILES(compound))
    print("InChI:", compound_name_get_InChI(compound))
    print("InChIKey:", compound_name_get_InChIKey(compound))
    print("IUPAC Name:", compound_name_get_IUPACName(compound))
    print("XLogP:", compound_name_get_XLogP(compound))
    print("Exact Mass:", compound_name_get_ExactMass(compound))

if __name__ == "__main__":
    test_pubchmapi()
```

#### Sample Output

```text
Testing PubChmAPI functions for: Aspirin
Title: ['[https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/name/Aspirin/property/Title/txt](https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/name/Aspirin/property/Title/txt)']
Molecular Formula: ['[https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/name/Aspirin/property/MolecularFormula/txt](https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/name/Aspirin/property/MolecularFormula/txt)']
Molecular Weight: ['[https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/name/Aspirin/property/MolecularWeight/txt](https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/name/Aspirin/property/MolecularWeight/txt)']
Canonical SMILES: ['[https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/name/Aspirin/property/SMILES/txt](https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/name/Aspirin/property/SMILES/txt)']
InChI: ['[https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/name/Aspirin/property/InChI/txt](https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/name/Aspirin/property/InChI/txt)']
InChIKey: ['[https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/name/Aspirin/property/InChIKey/txt](https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/name/Aspirin/property/InChIKey/txt)']
IUPAC Name: ['[https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/name/Aspirin/property/IUPACName/txt](https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/name/Aspirin/property/IUPACName/txt)']
XLogP: ['[https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/name/Aspirin/property/XLogP/txt](https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/name/Aspirin/property/XLogP/txt)']
Exact Mass: ['[https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/name/Aspirin/property/ExactMass/txt](https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/name/Aspirin/property/ExactMass/txt)']
```

---

### Compound CID Functions

Retrieve data using a Compound Identifier (CID).
**Format:** `compound_cid_get_[Operation](identifier)`

#### Code Example

```python
# test_pubchmapi_cid.py
from PubChmAPI import (
    compound_cid_get_description,
    compound_cid_get_synonyms,
    compound_cid_get_sids,
    compound_cid_get_cids,
    compound_cid_get_conformers,
    compound_cid_get_png,
    compound_cid_get_aids,
    compound_cid_get_aids_active,
    compound_cid_get_aids_inactive,
    compound_cid_get_assaysummary
)

def test_cid_functions():
    cid = 2244  # Aspirin CID
    print(f"Testing PubChmAPI CID functions for CID: {cid}")

    print("Description:", compound_cid_get_description(cid))
    print("Synonyms:", compound_cid_get_synonyms(cid)[:5], "...")
    print("Substance IDs:", compound_cid_get_sids(cid)[:5], "...")
    print("Self-retrieved CIDs:", compound_cid_get_cids(cid))
    print("Conformers:", compound_cid_get_conformers(cid)[:3], "...")
    print("PNG URL or data type:", type(compound_cid_get_png(cid)))
    print("All Assay IDs:", compound_cid_get_aids(cid)[:5], "...")
    print("Active Assay IDs:", compound_cid_get_aids_active(cid)[:5], "...")
    print("Inactive Assay IDs:", compound_cid_get_aids_inactive(cid)[:5], "...")
    print("Assay Summary:", compound_cid_get_assaysummary(cid))

if __name__ == "__main__":
    test_cid_functions()
```

#### Sample Output

```text
Testing PubChmAPI CID functions for CID: 2244
Description: ['[https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/cid/2244/description/xml](https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/cid/2244/description/xml)']
Synonyms: ['[https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/cid/2244/synonyms/txt](https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/cid/2244/synonyms/txt)'] ...
Substance IDs: ['[https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/cid/2244/sids/txt](https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/cid/2244/sids/txt)'] ...
Self-retrieved CIDs: ['[https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/cid/2244/cids/txt](https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/cid/2244/cids/txt)']
Conformers: ['[https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/cid/2244/conformers/xml](https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/cid/2244/conformers/xml)'] ...
PNG URL or data type: <class 'list'>
All Assay IDs: ['[https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/cid/2244/aids/txt](https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/cid/2244/aids/txt)'] ...
Active Assay IDs: ['[https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/cid/2244/aids/txt?aids_type=active](https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/cid/2244/aids/txt?aids_type=active)'] ...
Inactive Assay IDs: ['[https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/cid/2244/aids/txt?aids_type=inactive](https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/cid/2244/aids/txt?aids_type=inactive)'] ...
Assay Summary: ['[https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/cid/2244/assaysummary/xml](https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/cid/2244/assaysummary/xml)']
```

---

### Biological Domain Functions

Retrieve data related to proteins, genes, taxonomy, and cell lines.

#### Code Example

```python
# test_pubchmapi_biological.py
from PubChmAPI import (
    # Protein
    protein_accession_get_summary,
    protein_accession_get_aids,
    protein_gi_get_summary,
    protein_synonym_get_aids,
    # Gene
    gene_geneid_get_summary,
    gene_geneid_get_aids,
    gene_genesymbol_get_summary,
    gene_genesymbol_get_aids,
    # Taxonomy
    taxonomy_taxid_get_summary,
    taxonomy_taxid_get_aids,
    taxonomy_synonym_get_aids,
    # Cell line
    cell_cellacc_get_summary,
    cell_cellacc_get_aids,
    cell_synonym_get_summary
)

def test_biological_functions():
    print("Testing PubChmAPI Biological Functions\n")

    # Protein
    accession = "P68871"
    gi = "4506723"
    protein_syn = "Hemoglobin"
    print("Protein Functions:")
    print("Summary:", protein_accession_get_summary(accession))
    print("AIDs:", protein_accession_get_aids(accession)[:5], "...")
    print("GI Summary:", protein_gi_get_summary(gi))
    print("Synonym AIDs:", protein_synonym_get_aids(protein_syn)[:5], "...\n")

    # Gene
    geneid = "3043"
    symbol = "HBB"
    print("Gene Functions:")
    print("GeneID Summary:", gene_geneid_get_summary(geneid))
    print("GeneID AIDs:", gene_geneid_get_aids(geneid)[:5], "...")
    print("Symbol Summary:", gene_genesymbol_get_summary(symbol))
    print("Symbol AIDs:", gene_genesymbol_get_aids(symbol)[:5], "...\n")

    # Taxonomy
    taxid = "9606"
    tax_syn = "Human"
    print("Taxonomy Functions:")
    print("TaxID Summary:", taxonomy_taxid_get_summary(taxid))
    print("TaxID AIDs:", taxonomy_taxid_get_aids(taxid)[:5], "...")
    print("Synonym AIDs:", taxonomy_synonym_get_aids(tax_syn)[:5], "...\n")

    # Cell Line
    cellacc = "CVCL_0030"
    cell_syn = "HeLa"
    print("Cell Line Functions:")
    print("Cell Summary:", cell_cellacc_get_summary(cellacc))
    print("Cell AIDs:", cell_cellacc_get_aids(cellacc)[:5], "...")
    print("Synonym Summary:", cell_synonym_get_summary(cell_syn))

if __name__ == "__main__":
    test_biological_functions()
```

#### Sample Output

```text
Testing PubChmAPI Biological Functions

Protein Functions:
Summary: ['[https://pubchem.ncbi.nlm.nih.gov/rest/pug/protein/accession/P68871/summary/json](https://pubchem.ncbi.nlm.nih.gov/rest/pug/protein/accession/P68871/summary/json)']
AIDs: ['[https://pubchem.ncbi.nlm.nih.gov/rest/pug/protein/accession/P68871/aids/txt](https://pubchem.ncbi.nlm.nih.gov/rest/pug/protein/accession/P68871/aids/txt)'] ...
GI Summary: ['[https://pubchem.ncbi.nlm.nih.gov/rest/pug/protein/gi/4506723/summary/json](https://pubchem.ncbi.nlm.nih.gov/rest/pug/protein/gi/4506723/summary/json)']
Synonym AIDs: ['[https://pubchem.ncbi.nlm.nih.gov/rest/pug/protein/synonym/Hemoglobin/aids/txt](https://pubchem.ncbi.nlm.nih.gov/rest/pug/protein/synonym/Hemoglobin/aids/txt)'] ...

Gene Functions:
GeneID Summary: ['[https://pubchem.ncbi.nlm.nih.gov/rest/pug/gene/geneid/3043/summary/json](https://pubchem.ncbi.nlm.nih.gov/rest/pug/gene/geneid/3043/summary/json)']
GeneID AIDs: ['[https://pubchem.ncbi.nlm.nih.gov/rest/pug/gene/geneid/3043/aids/txt](https://pubchem.ncbi.nlm.nih.gov/rest/pug/gene/geneid/3043/aids/txt)'] ...
Symbol Summary: ['[https://pubchem.ncbi.nlm.nih.gov/rest/pug/gene/genesymbol/HBB/summary/json](https://pubchem.ncbi.nlm.nih.gov/rest/pug/gene/genesymbol/HBB/summary/json)']
Symbol AIDs: ['[https://pubchem.ncbi.nlm.nih.gov/rest/pug/gene/genesymbol/HBB/aids/txt](https://pubchem.ncbi.nlm.nih.gov/rest/pug/gene/genesymbol/HBB/aids/txt)'] ...

Taxonomy Functions:
TaxID Summary: ['[https://pubchem.ncbi.nlm.nih.gov/rest/pug/taxonomy/taxid/9606/summary/json](https://pubchem.ncbi.nlm.nih.gov/rest/pug/taxonomy/taxid/9606/summary/json)']
TaxID AIDs: ['[https://pubchem.ncbi.nlm.nih.gov/rest/pug/taxonomy/taxid/9606/aids/txt](https://pubchem.ncbi.nlm.nih.gov/rest/pug/taxonomy/taxid/9606/aids/txt)'] ...
Synonym AIDs: ['[https://pubchem.ncbi.nlm.nih.gov/rest/pug/taxonomy/synonym/Human/aids/txt](https://pubchem.ncbi.nlm.nih.gov/rest/pug/taxonomy/synonym/Human/aids/txt)'] ...

Cell Line Functions:
Cell Summary: ['[https://pubchem.ncbi.nlm.nih.gov/rest/pug/cell/cellacc/CVCL_0030/summary/json](https://pubchem.ncbi.nlm.nih.gov/rest/pug/cell/cellacc/CVCL_0030/summary/json)']
Cell AIDs: ['[https://pubchem.ncbi.nlm.nih.gov/rest/pug/cell/cellacc/CVCL_0030/aids/txt](https://pubchem.ncbi.nlm.nih.gov/rest/pug/cell/cellacc/CVCL_0030/aids/txt)'] ...
Synonym Summary: ['[https://pubchem.ncbi.nlm.nih.gov/rest/pug/cell/synonym/HeLa/summary/json](https://pubchem.ncbi.nlm.nih.gov/rest/pug/cell/synonym/HeLa/summary/json)']
```

---

```python
# ===============================
# PubChemAPI Workflow Examples
# ===============================

import requests
from PubChmAPI import (
    compound_name_get_cids,
    compound_fastsimilarity_2d_cid_get_cids,
    taxonomy_taxid_get_aids,
    gene_geneid_get_aids,
    assay_aid_get_cids_active,
    protein_accession_get_aids
)

# --- Helper Functions ---
def get_list_text_from_url(url_or_list):
    """Fetches text data from a URL and returns a list of lines."""
    url = url_or_list[0] if isinstance(url_or_list, list) else url_or_list
    try:
        response = requests.get(url)
        response.raise_for_status()
        return [line for line in response.text.split('\n') if line]
    except Exception as e:
        print(f"Error: {e}")
        return []

def convert_json_get_txt(url_or_list):
    """Modifies a PubChem URL to request TXT format instead of JSON/XML."""
    url = url_or_list[0] if isinstance(url_or_list, list) else url_or_list
    return url.replace('/json', '/txt').replace('/xml', '/txt')

# --- 1. Resolve Compound and Find 2D Analogs (≥90% similarity) ---
CID_QUERY = "Nirmatrelvir"

# Get the CID for the compound name
cid_list = get_list_text_from_url(compound_name_get_cids(CID_QUERY)[0])

if cid_list:
    NIRMATRELVIR_CID = cid_list[0]
    # Find similar compounds (≥90% 2D similarity)
    similar_cids = get_list_text_from_url(compound_fastsimilarity_2d_cid_get_cids(NIRMATRELVIR_CID))
    print(f"Query CID: {NIRMATRELVIR_CID}")
    print(f"Total Analogs (≥90%): {len(similar_cids)} | Top 5: {similar_cids[:5]}")
else:
    print(f"No CID found for '{CID_QUERY}'")

# Expected Output:
# Query CID: 155903259
# Total Analogs (≥90%): 724 | Top 5: ['155903259', '162396372', '162396442', '162396452', '162396458']


# --- 2. Identifying Assays for Streptomyces (TaxID 1883) ---
STREPTOMYCES_TAX_ID = 1883
print(f"--- Identifying assays for Streptomyces (TaxID {STREPTOMYCES_TAX_ID}) ---")

# Fetch all assay IDs (AIDs) for the given Taxonomy ID
streptomyces_aids = get_list_text_from_url(taxonomy_taxid_get_aids(STREPTOMYCES_TAX_ID))

if streptomyces_aids:
    print(f"Found {len(streptomyces_aids)} AIDs associated with Streptomyces (TaxID {STREPTOMYCES_TAX_ID}).")
    print(f"First 5 AIDs: {streptomyces_aids[:5]}")
else:
    print(f"Failed to retrieve AIDs for Streptomyces (TaxID {STREPTOMYCES_TAX_ID}).")

# Expected Output:
# --- Identifying assays for Streptomyces (TaxID 1883) ---
# Found 33 AIDs associated with Streptomyces (TaxID 1883).
# First 5 AIDs: ['286595', '286596', '288804', '288805', '288806']


# --- 3. Gene → Assay → Active Compounds Workflow (EGFR) ---
EGFR_GENE_ID = "1956"
# Convert JSON response to TXT for easier parsing
aids_txt_url = convert_json_get_txt(gene_geneid_get_aids(EGFR_GENE_ID))
aids_list = get_list_text_from_url(aids_txt_url)

if aids_list:
    FIRST_AID = aids_list[0]
    active_cid_url = assay_aid_get_cids_active(FIRST_AID)
    active_cids_list = get_list_text_from_url(active_cid_url)
    print(f"Active CIDs URL: {active_cid_url[0]}")
    print(f"First 5 Active CIDs: {active_cids_list[:5]}")
else:
    print("Failed to retrieve AIDs for the GeneID.")

# Expected Output:
# Active CIDs URL: [https://pubchem.ncbi.nlm.nih.gov/rest/pug/assay/aid/1433/cids/txt?aids_type=active](https://pubchem.ncbi.nlm.nih.gov/rest/pug/assay/aid/1433/cids/txt?aids_type=active)
# First 5 Active CIDs: ['135398510', '3038522', '5329102', '24867231', '11485656']


# --- 4. Protein → Assay → Active Compounds Workflow (EGFR, Accession P00533) ---
EGFR_ACCESSION_ID = "P00533"
print(f"--- Protein Target Resolution ({EGFR_ACCESSION_ID}) ---")

# Retrieve all AIDs (convert to TXT using helper)
aids_url = protein_accession_get_aids(EGFR_ACCESSION_ID)
aids_list = get_list_text_from_url(convert_json_get_txt(aids_url))
FIRST_AID = aids_list[0]
print(f"Total AIDs: {len(aids_list)} | First AID: {FIRST_AID}")

# Retrieve active compounds for the first AID
active_cids = get_list_text_from_url(assay_aid_get_cids_active(FIRST_AID))
print(f"Active CIDs ({len(active_cids)}): {active_cids[:5] if active_cids else 'None found'}")

# Expected Output:
# --- Protein Target Resolution (P00533) ---
# Total AIDs: 6329 | First AID: 1433
# Active CIDs (38): ['135398510', '3038522', '5329102', '24867231', '11485656']
```