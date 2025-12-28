"""
PubChem PUG-REST Dynamic Python Client
--------------------------------------
A professional wrapper for the PubChem API using dynamic metaprogramming to 
generate endpoint functions. Handles batching, throttling, and response parsing.
"""

import sys
import time
import json
import random
import re
import urllib.parse
from urllib.parse import urlparse
import requests

# ==============================================================================
# 1. CONFIGURATION & CONSTANTS
# ==============================================================================

# Define XREF sub-paths for reuse
XREF_PATHS = [
    'xref/RegistryID', 'xref/RN', 'xref/PubMedID', 'xref/MMDBID', 
    'xref/ProteinGI', 'xref/NucleotideGI', 'xref/TaxonomyID', 
    'xref/MIMID', 'xref/GeneID', 'xref/ProbeID', 'xref/PatentID',
    'xref/DBURL', 'xref/SBURL', 'xref/SourceName', 'xref/SourceCategory' 
]

# Define structural sub-paths for reuse
STRUCTURAL_PATHS = [
    'substructure/cid', 'substructure/smiles', 'substructure/inchi', 'substructure/sdf',
    'superstructure/cid', 'superstructure/smiles', 'superstructure/inchi', 'superstructure/sdf',
    'similarity_2d/cid', 'similarity_2d/smiles', 'similarity_2d/inchi', 'similarity_2d/sdf',
    'similarity_3d/cid', 'similarity_3d/smiles', 'similarity_3d/inchi', 'similarity_3d/sdf',
    'identity/cid', 'identity/smiles', 'identity/inchi', 'identity/sdf',
]

FAST_STRUCTURAL_PATHS = [
    'fastsubstructure/cid', 'fastsubstructure/smiles', 'fastsubstructure/inchi', 'fastsubstructure/sdf',
    'fastsuperstructure/cid', 'fastsuperstructure/smiles', 'fastsuperstructure/inchi', 'fastsuperstructure/sdf',
    'fastsimilarity_2d/cid', 'fastsimilarity_2d/smiles', 'fastsimilarity_2d/inchi', 'fastsimilarity_2d/sdf',
    'fastidentity/cid', 'fastidentity/smiles', 'fastidentity/inchi', 'fastidentity/sdf', 
]

# Define Assay Type/Status sub-paths for reuse 
ASSAY_TYPE_PATHS = [
    'type/all', 'type/confirmatory', 'type/doseresponse', 'type/onhold', 
    'type/panel', 'type/rnai', 'type/screening', 'type/summary',
    'type/cellbased', 'type/biochemical', 'type/invivo', 'type/invitro',
    'type/activeconcentrationspecified'
]

ASSAY_TARGET_PATHS = [
    'target/gi', 'target/proteinname', 'target/geneid', 'target/genesymbol', 'target/accession'
]

# Define Classification Node Output Types
CLASSIFICATION_OPERATIONS = {
    'get_cids': ('cids', 'TXT'), 'get_sids': ('sids', 'TXT'), 'get_aids': ('aids', 'TXT'),
    'get_patents': ('patents', 'TXT'), 'get_pmids': ('pmids', 'TXT'), 'get_dois': ('dois', 'TXT'),
    'get_compounds': ('cids', 'TXT'), 'get_cids_cache': ('cids', 'XML'),
    'get_geneids': ('geneids', 'TXT'), 'get_genes': ('geneids', 'TXT'),
    'get_proteinids': ('proteinids', 'TXT'), 'get_taxonomyids': ('taxonomyids', 'TXT'),
    'get_pathwayids': ('pathwayids', 'TXT'), 'get_diseaseids': ('diseaseids', 'TXT'),
    'get_cellids': ('cellids', 'TXT'),
}

# MOVED PROPERTIES TO TOP SO IT CAN BE USED IN DOMAINS
PROPERTIES = [
    "MolecularFormula", "MolecularWeight", "SMILES", "ConnectivitySMILES", "InChI",
    "InChIKey", "IUPACName", "Title", "XLogP", "ExactMass", "MonoisotopicMass",
    "TPSA", "Complexity", "Charge", "HBondDonorCount", "HBondAcceptorCount",
    "RotatableBondCount", "HeavyAtomCount", "IsotopeAtomCount", "AtomStereoCount",
    "DefinedAtomStereoCount", "UndefinedAtomStereoCount", "BondStereoCount",
    "DefinedBondStereoCount", "UndefinedBondStereoCount", "CovalentUnitCount",
    "PatentCount", "PatentFamilyCount", "AnnotationTypes", "AnnotationTypeCount",
    "SourceCategories", "LiteratureCount", "Volume3D", "XStericQuadrupole3D",
    "YStericQuadrupole3D", "ZStericQuadrupole3D", "FeatureCount3D",
    "FeatureAcceptorCount3D", "FeatureDonorCount3D", "FeatureAnionCount3D",
    "FeatureCationCount3D", "FeatureRingCount3D", "FeatureHydrophobeCount3D",
    "ConformerModelRMSD3D", "EffectiveRotorCount3D", "ConformerCount3D",
    "Fingerprint2D"
]

COMPOUND_NAMESPACES = ['cid', 'sid', 'name', 'smiles', 'inchi', 'sdf', 'inchikey', 'formula', 'listkey'] 

# Master Domain Configuration Map
DOMAINS = {
    'compound': {
        'namespaces': COMPOUND_NAMESPACES + STRUCTURAL_PATHS + FAST_STRUCTURAL_PATHS + ['fastformula'] + XREF_PATHS,
        'operations': {
            'get_record': ('record', 'xml'), 'get_synonyms': ('synonyms', 'txt'),
            'get_cids': ('cids', 'txt'), 'get_aids': ('aids', 'txt'), 'get_sids': ('sids', 'txt'),
            'get_description': ('description', 'xml'), 'get_conformers': ('conformers', 'xml'),
            'get_assaysummary': ('assaysummary', 'xml'), 
            'get_classification_tree': ('classification', 'XML'), 
            'get_classification': ('classification', 'xml'), 
            'get_dates': ('dates', 'json'),
            'get_dates_creation': ('dates', 'json'),      # Explicit creation
            'get_dates_deposition': ('dates', 'json'),    # Explicit deposition
            'get_dates_modification': ('dates', 'json'),  # Explicit modification
            'get_dates_hold': ('dates', 'json'),          # Explicit hold
            # --- NEW FEATURES ADDED HERE ---
            # 1. Get ALL properties (CSV format recommended for tabular data)
            'get_all_properties': (f'property/{",".join(PROPERTIES)}', 'csv'),
            # 2. Get specific list of properties (Handled dynamically in make_func)
            'get_properties': ('property', 'csv'),
            # -------------------------------
            # XREF OPERATIONS
            'get_xrefs_RegistryID': ('xrefs/RegistryID', 'txt'), 'get_xrefs_RN': ('xrefs/RN', 'txt'), 
            'get_xrefs_PubMedID': ('xrefs/PubMedID', 'txt'), 'get_xrefs_GeneID': ('xrefs/GeneID', 'txt'), 
            'get_xrefs_PatentID': ('xrefs/PatentID', 'txt'), 'get_xrefs_MMDBID': ('xrefs/MMDBID', 'txt'),
            'get_xrefs_DBURL': ('xrefs/DBURL', 'txt'), 'get_xrefs_SBURL': ('xrefs/SBURL', 'txt'),
            'get_xrefs_ProteinGI': ('xrefs/ProteinGI', 'txt'), 'get_xrefs_NucleotideGI': ('xrefs/NucleotideGI', 'txt'), 
            'get_xrefs_TaxonomyID': ('xrefs/TaxonomyID', 'txt'), 'get_xrefs_MIMID': ('xrefs/MIMID', 'txt'),
            'get_xrefs_ProbeID': ('xrefs/ProbeID', 'txt'), 'get_xrefs_SourceName': ('xrefs/SourceName', 'txt'),
            'get_xrefs_SourceCategory': ('xrefs/SourceCategory', 'txt'),
            # IMAGES & FILTERS
            'get_png': ('PNG', 'PNG'), 'get_png_2d': ('PNG', 'PNG'), 'get_png_3d': ('PNG', 'PNG'),
            'get_aids_active': ('aids', 'txt'), 'get_aids_inactive': ('aids', 'txt'),
            'get_cids_original': ('cids', 'txt'), 'get_cids_parent': ('cids', 'txt'), 
            'get_cids_component': ('cids', 'txt'), 'get_cids_preferred': ('cids', 'txt'), 
            'get_cids_same_stereo': ('cids', 'txt'), 'get_cids_same_tautomer': ('cids', 'txt'), 
            'get_cids_same_connectivity': ('cids', 'txt'), 'get_cids_same_isotopes': ('cids', 'txt'),
            'get_concise': ('concise', 'json'),
        }
    },
    'substance': {
        'namespaces': ['sid', 'name', 'sourceid', 'sourceall', 'listkey'] + STRUCTURAL_PATHS + FAST_STRUCTURAL_PATHS + ['fastformula'] + XREF_PATHS,
        'operations': {
            'get_record': ('record', 'xml'), 'get_synonyms': ('synonyms', 'txt'),
            'get_cids': ('cids', 'txt'), 'get_sids': ('sids', 'txt'), 
            'get_aids': ('aids', 'txt'), 'get_aids_active': ('aids', 'txt'), 'get_aids_inactive': ('aids', 'txt'), 
            'get_classification_tree': ('classification', 'XML'), 
            'get_classification': ('classification', 'xml'), 
            'get_xrefs': ('xrefs', 'xml'), 
            'get_sids_original': ('sids', 'txt'), 
            'get_cids_standardized': ('cids', 'txt'),
            # XREF OPERATIONS
            'get_xrefs_RegistryID': ('xrefs/RegistryID', 'txt'), 'get_xrefs_RN': ('xrefs/RN', 'txt'), 
            'get_xrefs_PubMedID': ('xrefs/PubMedID', 'txt'), 'get_xrefs_GeneID': ('xrefs/GeneID', 'txt'), 
            'get_xrefs_PatentID': ('xrefs/PatentID', 'txt'), 'get_xrefs_MMDBID': ('xrefs/MMDBID', 'txt'),
            'get_xrefs_DBURL': ('xrefs/DBURL', 'txt'), 'get_xrefs_SBURL': ('xrefs/SBURL', 'txt'),
            'get_xrefs_ProteinGI': ('xrefs/ProteinGI', 'txt'), 'get_xrefs_NucleotideGI': ('xrefs/NucleotideGI', 'txt'), 
            'get_xrefs_TaxonomyID': ('xrefs/TaxonomyID', 'txt'), 'get_xrefs_MIMID': ('xrefs/MIMID', 'txt'),
            'get_xrefs_ProbeID': ('xrefs/ProbeID', 'txt'), 'get_xrefs_SourceName': ('xrefs/SourceName', 'txt'),
            'get_xrefs_SourceCategory': ('xrefs/SourceCategory', 'txt'),
            'get_dates': ('dates', 'json'),
            'get_dates_creation': ('dates', 'json'),      # Explicit creation
            'get_dates_deposition': ('dates', 'json'),    # Explicit deposition
            'get_dates_modification': ('dates', 'json'),  # Explicit modification
            'get_dates_hold': ('dates', 'json'),          # Explicit hold

    }  },
    'assay': {
        'namespaces': ['aid', 'listkey', 'type', 'sourceall', 'activity'] + ASSAY_TYPE_PATHS + ASSAY_TARGET_PATHS,
        'operations': {
            'get_record': ('record', 'xml'), 'get_description': ('description', 'xml'), 'get_summary': ('summary', 'json'), 
            'get_classification_tree': ('classification', 'XML'),
            'get_cids': ('cids', 'txt'), 'get_cids_active': ('cids', 'txt'), 'get_cids_inactive': ('cids', 'txt'),
            'get_sids': ('sids', 'txt'), 'get_sids_active': ('sids', 'txt'), 'get_sids_inactive': ('sids', 'txt'),
            'get_doseresponse': ('doseresponse', 'xml'), 'get_doseresponse_sid': ('doseresponse/sid', 'xml'), 
            'get_sids_doseresponse_listkey': ('sids', 'xml'), 
            'get_targets': ('targets', 'xml'), 'get_aids': ('aids', 'txt'), 'get_geneids': ('targets/geneid', 'txt'), 
            'get_accessions': ('targets/accession', 'txt'), 'get_gi': ('targets/gi', 'txt'),
            # XREFS
            'get_xrefs_RegistryID': ('xrefs/RegistryID', 'txt'), 'get_xrefs_RN': ('xrefs/RN', 'txt'), 
            'get_xrefs_PubMedID': ('xrefs/PubMedID', 'txt'), 'get_xrefs_GeneID': ('xrefs/GeneID', 'txt'), 
            'get_xrefs_PatentID': ('xrefs/PatentID', 'txt'), 'get_xrefs_MMDBID': ('xrefs/MMDBID', 'txt'),
            'get_xrefs_DBURL': ('xrefs/DBURL', 'txt'), 'get_xrefs_SBURL': ('xrefs/SBURL', 'txt'),
            'get_xrefs_ProteinGI': ('xrefs/ProteinGI', 'txt'), 'get_xrefs_NucleotideGI': ('xrefs/NucleotideGI', 'txt'), 
            'get_xrefs_TaxonomyID': ('xrefs/TaxonomyID', 'txt'), 'get_xrefs_MIMID': ('xrefs/MIMID', 'txt'),
            'get_xrefs_ProbeID': ('xrefs/ProbeID', 'txt'), 'get_xrefs_SourceName': ('xrefs/SourceName', 'txt'),
            'get_xrefs_SourceCategory': ('xrefs/SourceCategory', 'txt'),
        }
    },
    'pathway': {
        'namespaces': ['pwacc'], 
        'operations': {
            'get_summary': ('summary', 'json'), 'get_cids': ('cids', 'txt'), 
            'get_geneids': ('geneids', 'txt'), 'get_accessions': ('proteins', 'txt') 
        }
    },
    'gene': {
        'namespaces': ['geneid', 'genesymbol', 'synonym'], 
        'operations': {
            'get_summary': ('summary', 'json'), 'get_aids': ('aids', 'txt'), 
            'get_aids_active': ('aids', 'txt'), 'get_aids_inactive': ('aids', 'txt'),
            'get_concise': ('concise', 'json'), 'get_pwaccs': ('pwaccs', 'txt'),
        }
    },
    'protein': {
        'namespaces': ['accession', 'gi', 'synonym'], 
        'operations': {
            'get_summary': ('summary', 'json'), 'get_aids': ('aids', 'txt'), 
            'get_aids_active': ('aids', 'txt'), 'get_aids_inactive': ('aids', 'txt'),
            'get_concise': ('concise', 'json'), 'get_pwaccs': ('pwaccs', 'txt'),
        }
    },
    'taxonomy': {
        'namespaces': ['taxid', 'synonym'], 
        'operations': {
            'get_summary': ('summary', 'json'), 'get_aids': ('aids', 'txt'), 
            'get_aids_active': ('aids', 'txt'), 'get_aids_inactive': ('aids', 'txt')
        }
    },
    'cell': {
        'namespaces': ['cellacc', 'synonym'], 
        'operations': {
            'get_summary': ('summary', 'json'), 'get_aids': ('aids', 'txt'), 
            'get_aids_active': ('aids', 'txt'), 'get_aids_inactive': ('aids', 'txt')
        }
    },
    'classification': {
        'namespaces': ['hnid'],
        'operations': CLASSIFICATION_OPERATIONS 
    }
}

# ==============================================================================
# 2. HELPER FUNCTIONS
# ==============================================================================

def check_pugrest_status(response: requests.Response) -> dict:
    """Parses PUG-REST HTTP status codes into readable errors."""
    status_code = response.status_code
    error_map = {
        200: ("Success", "The request was successful and results are available."),
        202: ("Accepted", "Asynchronous operation pending; check back later."),
        400: ("PUGREST.BadRequest", "Request is improperly formed (syntax error in the URL, POST body, etc.)."),
        404: ("PUGREST.NotFound", "The input record was not found (e.g. invalid CID or AID)."),
        500: ("PUGREST.ServerError", "An unknown error or server-side problem occurred."),
        503: ("PUGREST.ServerBusy", "Too many requests or server is busy, retry later."),
        504: ("PUGREST.Timeout", "The request timed out from server overload or too broad a request."),
    }
    status, meaning = error_map.get(status_code, ("Unknown Error", "Status code not in standard PUG-REST map."))
    return {
        "status_code": status_code, 
        "error_code": status.split('.')[-1] if '.' in status else status, 
        "category": status, 
        "meaning": meaning, 
        "url": response.url
    }

def _get_listkey_from_url(url_list):
    """Helper to retrieve a ListKey from a JSON response URL."""
    if not url_list: return None
    url = url_list[0]
    try:
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()
        if 'ListKey' in data:
            return data['ListKey']
        return None
    except Exception as e:
        print(f"ListKey retrieval failed: {e}")
        return None

def extract_listkey_from_xml(xml_text):
    """Parses the PubChem XML response to find and return the ListKey string."""
    match = re.search(r'<ListKey>(\d+)</ListKey>', xml_text)
    if match:
        return match.group(1)
    return None

def convert_json_get_txt(input_url):
    """Convert a URL from JSON format to TXT format."""
    return input_url.replace("/JSON", "/txt")

def get_list_text_from_url(url_or_list):
    """
    Retrieve text content from one or more URLs.
    Always returns a list of stripped non-empty lines.
    - Accepts a string URL or an iterable of string URLs.
    - Unwraps single-element lists.
    - Handles Throttling (1s) automatically between requests.
    """
    # Normalize input into a flat list of URLs
    if isinstance(url_or_list, (list, tuple, set)):
        urls = list(url_or_list)
        if len(urls) == 1:
            urls = [urls[0]]  # unwrap
    elif isinstance(url_or_list, str):
        urls = [url_or_list]
    else:
        raise TypeError(f"Expected string or iterable of strings, got {type(url_or_list)}")

    results = []
    
    for i, url in enumerate(urls):
        # Validate URL format
        parsed = urlparse(url)
        if not parsed.scheme or not parsed.netloc:
            print(f"Warning: Skipping invalid URL: {url}")
            continue

        # --- THROTTLING APPLIED HERE ---
        # Sleep 0.2s between requests (but not before the first one)
        if ( i % 5 == 4 ) :
            time.sleep(1)

        try:
            # --- TIMEOUT INCREASED TO 30s ---
            resp = requests.get(url, timeout=30) 
            resp.raise_for_status()

            lines = [
                line.strip() 
                for line in resp.text.splitlines()
                if line.strip()
            ]
            results.extend(lines)

        except requests.exceptions.RequestException as e:
            print(f"Error: Request failed for {url}: {e}")

    return results

def extract_identifiers_from_json(json_data, key='CID'):
    """
    Safely extracts a list of identifiers from a PubChem JSON response dictionary.
    """
    if not json_data:
        return []

    # Navigate: InformationList -> Information -> [First Item] -> Key
    try:
        info_list = json_data.get('InformationList', {})
        info = info_list.get('Information', [])
        
        if info and isinstance(info, list):
            # PubChem usually returns a list of dicts under 'Information'.
            return info[0].get(key, [])
            
    except (AttributeError, IndexError, TypeError):
        return []

    return []

# ==============================================================================
# 3. UNIVERSAL REQUEST BUILDER
# ==============================================================================
import urllib.parse

def _base_request(domain, identifiers, namespace, operation, default_fmt, override_fmt=None, **kwargs):
    """
    Universal Request Builder for ALL PubChem domains.
    Returns the final URL link string (Not executed).
    
    Enforces single-identifier batches for all known single-input operations
    to prevent "silent failures" or fragile endpoints.
    """
    out_fmt = override_fmt if override_fmt else default_fmt
    
    # Default batch size for simple numeric IDs
    BATCH_SIZE = 10
    
    params = {}
    
    # --- 1. Process kwargs into Params ---
    for k, v in kwargs.items():
        if k == 'operation' or k == 'output_format': 
            continue
        if v is not None:
            if isinstance(v, bool): 
                params[k] = 'true' if v else 'false'
            else: 
                params[k] = str(v)

    # Define namespaces that are structural searches (require batch size 1)
    structural_namespaces = ['substructure', 'superstructure', 'similarity', 'identity', 'fastidentity', 'fastsimilarity_2d', 'fastsimilarity_3d', 'fastsubstructure', 'fastsuperstructure']
    is_structural_search = any(s_ns in namespace for s_ns in structural_namespaces)

    # --- 2. Flatten Identifiers (FIXED: Removed encoding here) ---
    flat_list = []
    
    def flatten(args):
        if args is None: return 
        if isinstance(args, (list, tuple)): 
            for element in args:
                flatten(element)
        else: 
            # Just convert to string, do NOT encode yet.
            flat_list.append(str(args))
                
    flatten(identifiers)
    
    def chunker(seq, size):
        for pos in range(0, len(seq), size):
            yield seq[pos:pos + size]

    urls_or_results = []
    
    # List of namespaces that act as complex strings (require batch size 1)
    STRING_INPUT_NAMESPACES = ['name', 'smiles', 'inchi', 'inchikey', 'formula', 'sdf', 'fastformula']
    
    # --- 3. Batch Size Adjustment Logic ---
    current_batch_size = BATCH_SIZE
    
    is_string_input = (namespace in STRING_INPUT_NAMESPACES) or is_structural_search or ('xref/' in namespace)

    # Condition 1: Force batch size 1 for string/structural/xref inputs
    if is_string_input:
        current_batch_size = 1
    
    # Condition 2: Gene/Pathway and Assay/Target lookup (known to fail on batches)
    elif (domain == 'gene' and operation == 'pwaccs') or \
       (domain == 'assay' and operation == 'targets/geneid'):
       current_batch_size = 1
    
    # Condition 3: All Single-Input Operations (API limitations)
    elif (domain == 'gene' and operation == 'concise') or \
    (domain == 'assay' and operation in ['record', 'doseresponse', 'doseresponse/sid']) or \
    (domain == 'classification') or \
    (operation == 'classification') or \
    (operation in ['PNG', 'record'] and domain in ['compound', 'substance'] and out_fmt in ['PNG', 'PNG_3D']) or \
    (domain == 'protein' and namespace in ['gi', 'synonym'] and operation in ['summary', 'concise', 'pwaccs', 'aids', 'aids_active', 'aids_inactive']) or \
    (domain == 'protein' and namespace == 'accession') or \
    (domain == 'taxonomy' and operation in ['aids', 'aids_active', 'aids_inactive', 'summary']) or \
    (domain == 'cell'):
        current_batch_size = 1

    batches = chunker(flat_list, current_batch_size) if flat_list else [['']] 

    # --- 4. URL Assembly Loop (FIXED: Centralized Encoding) ---
    for batch in batches:
        # Join the batch with commas. For batch size 1, this is just the single item string.
        batch_str = ",".join(batch)
        
        # Apply URL encoding to the final string.
        # safe=',' allows commas to remain for batched numeric IDs (e.g., "2244,3672")
        # while still encoding special characters in SMILES/names.
        safe_item = urllib.parse.quote(batch_str, safe=',')
        
        # A. Build Base Path
        if domain == 'standardize':
            base = f"https://pubchem.ncbi.nlm.nih.gov/rest/pug/{domain}"
        elif domain in ['sources', 'sourcetable', 'periodictable', 'classification']:
             base = f"https://pubchem.ncbi.nlm.nih.gov/rest/pug/{domain}"
             if namespace: base += f"/{namespace}"
             if domain == 'classification' and safe_item: 
                 base += f"/{safe_item}" 
        else: # Standard and Search Domains (compound, assay, etc.)
             base = f"https://pubchem.ncbi.nlm.nih.gov/rest/pug/{domain}/{namespace}/{safe_item}"
             
        # B. Append Operation 
        if operation:
            if operation.lower() == out_fmt.lower():
                url = f"{base}/{operation}"
            else:
                url = f"{base}/{operation}/{out_fmt}"
        else:
            url = f"{base}/{out_fmt}"

        # C. Append Parameters
        # Remove 'formula' param if it's not the namespace (prevents conflicts)
        if 'formula' in params and namespace != 'formula':
             del params['formula']
             
        final_url = url + ("?" + urllib.parse.urlencode(params) if params else "")

        urls_or_results.append(final_url)
            
    return urls_or_results
# ==============================================================================
# 4. DYNAMIC FUNCTION GENERATOR (Factory Pattern)
# ==============================================================================

current_module = sys.modules[__name__]

def make_func(domain, ns, func_suffix, url_op, fmt):
    """
    Dynamically creates an API wrapper function and attaches it to the module.
    """
    # 1. Split Namespace 
    ns_parts = ns.split('/')
    
    # 2. Build the core function name parts
    func_name_parts = [domain] + ns_parts + [func_suffix]
    
    # Final name construction
    func_name = "_".join(func_name_parts)

    def dynamic_wrapper(*args, output_format=None, operation=url_op, **kwargs):
        local_kwargs = kwargs.copy()
        
        # --- 1. Automated Option Injection based on function name ---
        if func_suffix:
            # Inject cids_type for Tautomer/Stereo/Parent
            if func_suffix.startswith('get_cids_same_') or func_suffix.startswith('get_cids_parent'):
                type_suffix = func_suffix.replace('get_cids_', '')
                local_kwargs['cids_type'] = type_suffix 
                
            # Inject aids_type (Fixed to ensure it only targets aids)
            if func_suffix.endswith('aids_active'):
                local_kwargs['aids_type'] = 'active'
            elif func_suffix.endswith('aids_inactive'): 
                local_kwargs['aids_type'] = 'inactive'

            # Inject cids_type
            if func_suffix.endswith('cids_active'):
                local_kwargs['cids_type'] = 'active'
            elif func_suffix.endswith('cids_inactive'):
                local_kwargs['cids_type'] = 'inactive'

            # Inject sids_type
            if func_suffix.endswith('sids_active'):
                local_kwargs['sids_type'] = 'active'
            elif func_suffix.endswith('sids_inactive'):
                local_kwargs['sids_type'] = 'inactive'

            # PNG/Image Injection (record_type)
            if 'png_3d' in func_suffix:
                local_kwargs['record_type'] = '3d'
            elif 'png_2d' in func_suffix:
                local_kwargs['record_type'] = '2d'

            # Specific injection for Dose-Response ListKey
            if func_suffix == 'get_sids_doseresponse_listkey':
                local_kwargs['sids_type'] = 'doseresponse'
                local_kwargs['list_return'] = 'listkey'
            
            # Dates Type Injection
            elif 'get_dates_' in func_suffix:
                # Split 'get_dates_creation' -> ['get', 'dates', 'creation']
                parts = func_suffix.split('_')
                date_type = parts[-1] 
                if date_type in ['deposition', 'modification', 'hold', 'creation']:
                    local_kwargs['dates_type'] = date_type

        # --- 2. Dynamic Property Injection (NEW FEATURE) ---
        if 'properties' in local_kwargs:
            props = local_kwargs.pop('properties')
            if isinstance(props, list):
                props = ",".join(props)
            # If the base operation was generic 'property', replace it with specific list
            if operation == 'property':
                operation = f"property/{props}"

        # --- 3. Gene Summary Taxonomy Filter (Path Fix) ---
        if domain == 'gene' and ns == 'genesymbol' and len(args) > 1:
            identifier = args[0]
            tax_filter_list = args[1] 
            
            if isinstance(tax_filter_list, (list, tuple)):
                 tax_filter_str = str(tax_filter_list[0])
            else:
                 tax_filter_str = str(tax_filter_list)

            if 'summary' in url_op:
                new_op = f"{url_op}/{tax_filter_str}" 
                # Early return for this specific edge case
                return _base_request(domain, [identifier], ns, new_op, fmt, override_fmt=output_format, **local_kwargs)

        # --- 4. Classification CacheKey Injection ---
        if domain == 'classification' and 'cache' in func_suffix:
             local_kwargs['list_return'] = 'cachekey'
             if output_format is None:
                  output_format = 'XML'
        
        # --- FINAL RETURN STATEMENT ---
        return _base_request(domain, args, ns, operation, fmt, override_fmt=output_format, **local_kwargs)
    
    dynamic_wrapper.__doc__ = f"Auto-generated: {func_name}\nAPI Operation: {url_op}"
    setattr(current_module, func_name, dynamic_wrapper)

# --- A. EXECUTE FACTORY FOR STANDARD DOMAINS ---
for domain, config in DOMAINS.items():
    for ns in config['namespaces']:
        # 1. Operations
        for suffix, (api_path, default_fmt) in config['operations'].items():
            make_func(domain, ns, suffix, api_path, default_fmt)
        # 2. Properties (Compound only)
        if domain == 'compound':
            for prop in PROPERTIES:
                make_func(domain, ns, f"get_{prop}", f"property/{prop}", 'txt')

# --- B. GENERATE SPECIAL DOMAINS (Metadata, Standardization, etc.) ---
special_funcs = [
    ('get_sources_substance', 'sources', 'substance', None, 'xml'),
    ('get_sourcetable_substance', 'sourcetable', 'substance', None, 'json'), 
    ('standardize_smiles', 'standardize', 'smiles', None, 'sdf'),
]

for s_name, dom, ns, op, fmt in special_funcs:
    def wrapper(*args, output_format=None, _d=dom, _n=ns, _o=op, _f=fmt, **kwargs):
        return _base_request(_d, args, _n, _o, _f, override_fmt=output_format, **kwargs)
    setattr(current_module, s_name, wrapper)