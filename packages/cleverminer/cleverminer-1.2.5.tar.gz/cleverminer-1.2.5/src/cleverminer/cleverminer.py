import sys
import time
import copy
import inspect
from time import strftime
from time import gmtime
import pandas as pd
import numpy as np
from pandas.api.types import CategoricalDtype
import progressbar
import re
from textwrap import wrap
import seaborn as sns
import matplotlib.pyplot as plt
import re
import pickle
import json
import hashlib
from datetime import datetime
import tempfile
import os
import urllib

class cleverminer:
    version_string = '1.2.5'
    temppath = tempfile.gettempdir()
    cache_dir = os.path.join(temppath, 'clm_cache')

    def __init__(O000000O00O0, **OO0O0OOOOO0O):
        O000000O00O0._print_disclaimer()
        O000000O00O0.use_cache = False
        O000000O00O0.cache_also_data = True
        O000000O00O0.stats = {'total_cnt': 0, 'total_ver': 0, 'total_valid': 0, 'control_number': 0, 'start_prep_time': time.time(), 'end_prep_time': time.time(), 'start_proc_time': time.time(), 'end_proc_time': time.time()}
        O000000O00O0.options = {'max_categories': 100, 'max_rules': None, 'optimizations': True, 'automatic_data_conversions': True, 'progressbar': True, 'keep_df': False}
        O000000O00O0.df = None
        O000000O00O0.kwargs = None
        if len(OO0O0OOOOO0O) > 0:
            O000000O00O0.kwargs = OO0O0OOOOO0O
        O000000O00O0.profiles = {}
        O000000O00O0.verbosity = {}
        O000000O00O0.verbosity['debug'] = False
        O000000O00O0.verbosity['print_rules'] = False
        O000000O00O0.verbosity['print_hashes'] = True
        O000000O00O0.verbosity['last_hash_time'] = 0
        O000000O00O0.verbosity['hint'] = False
        if 'opts' in OO0O0OOOOO0O:
            O000000O00O0._set_opts(OO0O0OOOOO0O.get('opts'))
        if 'opts' in OO0O0OOOOO0O:
            O00OOO0O0O00 = OO0O0OOOOO0O['opts']
            if 'use_cache' in O00OOO0O0O00:
                O000000O00O0.use_cache = O00OOO0O0O00['use_cache']
            if 'cache_also_data' in O00OOO0O0O00:
                O000000O00O0.cache_also_data = O00OOO0O0O00['cache_also_data']
            if 'verbose' in OO0O0OOOOO0O.get('opts'):
                OO0OOO000OOO = OO0O0OOOOO0O.get('opts').get('verbose')
                if OO0OOO000OOO.upper() == 'FULL':
                    O000000O00O0.verbosity['debug'] = True
                    O000000O00O0.verbosity['print_rules'] = True
                    O000000O00O0.verbosity['print_hashes'] = False
                    O000000O00O0.verbosity['hint'] = True
                    O000000O00O0.options['progressbar'] = False
                elif OO0OOO000OOO.upper() == 'RULES':
                    O000000O00O0.verbosity['debug'] = False
                    O000000O00O0.verbosity['print_rules'] = True
                    O000000O00O0.verbosity['print_hashes'] = True
                    O000000O00O0.verbosity['hint'] = True
                    O000000O00O0.options['progressbar'] = False
                elif OO0OOO000OOO.upper() == 'HINT':
                    O000000O00O0.verbosity['debug'] = False
                    O000000O00O0.verbosity['print_rules'] = False
                    O000000O00O0.verbosity['print_hashes'] = True
                    O000000O00O0.verbosity['last_hash_time'] = 0
                    O000000O00O0.verbosity['hint'] = True
                    O000000O00O0.options['progressbar'] = False
                elif OO0OOO000OOO.upper() == 'DEBUG':
                    O000000O00O0.verbosity['debug'] = True
                    O000000O00O0.verbosity['print_rules'] = True
                    O000000O00O0.verbosity['print_hashes'] = True
                    O000000O00O0.verbosity['last_hash_time'] = 0
                    O000000O00O0.verbosity['hint'] = True
                    O000000O00O0.options['progressbar'] = False
        if 'load' in OO0O0OOOOO0O:
            if O000000O00O0.use_cache:
                O000000O00O0.use_cache = False
        O000OO000OO0 = copy.deepcopy(OO0O0OOOOO0O)
        if 'df' in O000OO000OO0:
            O000OO000OO0['df'] = O000OO000OO0['df'].to_json()
        hash = O000000O00O0._get_hash(O000OO000OO0)
        O000000O00O0.guid = hash
        if O000000O00O0.use_cache:
            if not os.path.isdir(O000000O00O0.cache_dir):
                os.mkdir(O000000O00O0.cache_dir)
            O000000O00O0.cache_fname = os.path.join(O000000O00O0.cache_dir, hash + '.clm')
            if os.path.isfile(O000000O00O0.cache_fname):
                print(f'Will use cached file {O000000O00O0.cache_fname}')
                OO000000000O = 'pickle'
                if 'fmt' in OO0O0OOOOO0O:
                    OO000000000O = OO0O0OOOOO0O.get('fmt')
                O000000O00O0.load(O000000O00O0.cache_fname, fmt=OO000000000O)
                return
            print(f'Task {hash} not in cache, will calculate it.')
        O000000O00O0._is_py310 = sys.version_info[0] >= 4 or (sys.version_info[0] >= 3 and sys.version_info[1] >= 10)
        if not O000000O00O0._is_py310:
            print('Warning: Python 3.10+ NOT detected. You should upgrade to Python 3.10 or greater to get better performance')
        elif O000000O00O0.verbosity['debug']:
            print('Python 3.10+ detected.')
        O000000O00O0._initialized = False
        if 'load' in OO0O0OOOOO0O:
            OO000000000O = 'pickle'
            if 'fmt' in OO0O0OOOOO0O:
                OO000000000O = OO0O0OOOOO0O.get('fmt')
            O000000O00O0.load(filename=OO0O0OOOOO0O.get('load'), fmt=OO000000000O)
            return
        O000000O00O0._init_data()
        O000000O00O0._init_task()
        if len(OO0O0OOOOO0O) > 0:
            if 'df' in OO0O0OOOOO0O:
                O000000O00O0._prep_data(OO0O0OOOOO0O.get('df'))
            else:
                print('Missing dataframe. Cannot initialize.')
                O000000O00O0._initialized = False
                return
            O00O0OO0O000 = OO0O0OOOOO0O.get('proc', None)
            if not O00O0OO0O000 == None:
                O000000O00O0._calculate(**OO0O0OOOOO0O)
            else:
                if O000000O00O0.verbosity['debug']:
                    print('INFO: just initialized')
                OOO0O0O0O0OO = {}
                OO0000OOO0O0 = {}
                OO0000OOO0O0['varname'] = O000000O00O0.data['varname']
                OO0000OOO0O0['catnames'] = O000000O00O0.data['catnames']
                OOO0O0O0O0OO['datalabels'] = OO0000OOO0O0
                O000000O00O0.result = OOO0O0O0O0OO
        O000000O00O0._initialized = True
        if O000000O00O0.use_cache:
            O000000O00O0.save(O000000O00O0.cache_fname, savedata=O000000O00O0.cache_also_data, embeddata=False)
            print(f'CACHE: results cache saved into {O000000O00O0.cache_fname}')

    def _get_hash(self,x):

        class NpEncoder(json.JSONEncoder):
            def default(self, obj):
                if isinstance(obj, np.integer):
                    return int(obj)
                if isinstance(obj, np.floating):
                    return float(obj)
                if isinstance(obj, np.ndarray):
                    return obj.tolist()
                if callable(obj):
                    #non-unique, non-chacheable; return always a different number
                    return time.time()
                
                return super(NpEncoder, self).default(obj)

        hash = hashlib.sha256(json.dumps(x, sort_keys=True,cls=NpEncoder).encode('utf-8')).hexdigest()
        return hash

    def _get_fast_hash(O0O0OO0O0000, O0OOO0OO00OO):
        O0OO0OO000O0 = pickle.dumps(O0OOO0OO00OO)
        print(f'...CALC THE HASH {datetime.now()}')
        hash = hashlib.md5(O0OO0OO000O0).hexdigest()
        return hash

    def _set_opts(O0O00000OO0O, OO00O0O00O00):
        if 'no_optimizations' in OO00O0O00O00:
            O0O00000OO0O.options['optimizations'] = not OO00O0O00O00['no_optimizations']
            print('No optimization will be made.')
        if 'disable_progressbar' in OO00O0O00O00:
            O0O00000OO0O.options['progressbar'] = False
            print('Progressbar will not be shown.')
        if 'max_rules' in OO00O0O00O00:
            O0O00000OO0O.options['max_rules'] = OO00O0O00O00['max_rules']
        if 'max_categories' in OO00O0O00O00:
            O0O00000OO0O.options['max_categories'] = OO00O0O00O00['max_categories']
            if O0O00000OO0O.verbosity['debug'] == True:
                print(f"Maximum number of categories set to {O0O00000OO0O.options['max_categories']}")
        if 'no_automatic_data_conversions' in OO00O0O00O00:
            O0O00000OO0O.options['automatic_data_conversions'] = not OO00O0O00O00['no_automatic_data_conversions']
            print('No automatic data conversions will be made.')
        if 'keep_df' in OO00O0O00O00:
            O0O00000OO0O.options['keep_df'] = OO00O0O00O00['keep_df']

    def _init_data(OOOOOO0O0OOO):
        OOOOOO0O0OOO.data = {}
        OOOOOO0O0OOO.data['varname'] = []
        OOOOOO0O0OOO.data['catnames'] = []
        OOOOOO0O0OOO.data['vtypes'] = []
        OOOOOO0O0OOO.data['dm'] = []
        OOOOOO0O0OOO.data['rows_count'] = int(0)
        OOOOOO0O0OOO.data['data_prepared'] = 0

    def _init_task(OOOO000O0OO0):
        if 'opts' in OOOO000O0OO0.kwargs:
            OOOO000O0OO0._set_opts(OOOO000O0OO0.kwargs.get('opts'))
        OOOO000O0OO0.cedent = {'cedent_type': 'none', 'defi': {}, 'num_cedent': 0, 'trace_cedent': [], 'trace_cedent_asindata': [], 'traces': [], 'generated_string': '', 'rule': {}, 'filter_value': int(0)}
        OOOO000O0OO0.task_actinfo = {'proc': '', 'cedents_to_do': [], 'cedents': []}
        OOOO000O0OO0.rulelist = []
        OOOO000O0OO0.stats['total_cnt'] = 0
        OOOO000O0OO0.stats['total_valid'] = 0
        OOOO000O0OO0.stats['control_number'] = 0
        OOOO000O0OO0.result = {}
        OOOO000O0OO0._opt_base = None
        OOOO000O0OO0._opt_relbase = None
        OOOO000O0OO0._opt_base1 = None
        OOOO000O0OO0._opt_relbase1 = None
        OOOO000O0OO0._opt_base2 = None
        OOOO000O0OO0._opt_relbase2 = None
        OOOOO00O000O = None
        if not OOOO000O0OO0.kwargs == None:
            OOOOO00O000O = OOOO000O0OO0.kwargs.get('quantifiers', None)
            if not OOOOO00O000O == None:
                for OOOO00OOO000 in OOOOO00O000O.keys():
                    if OOOO00OOO000.upper() == 'BASE':
                        OOOO000O0OO0._opt_base = OOOOO00O000O.get(OOOO00OOO000)
                    if OOOO00OOO000.upper() == 'RELBASE':
                        OOOO000O0OO0._opt_relbase = OOOOO00O000O.get(OOOO00OOO000)
                    if (OOOO00OOO000.upper() == 'FRSTBASE') | (OOOO00OOO000.upper() == 'BASE1'):
                        OOOO000O0OO0._opt_base1 = OOOOO00O000O.get(OOOO00OOO000)
                    if (OOOO00OOO000.upper() == 'SCNDBASE') | (OOOO00OOO000.upper() == 'BASE2'):
                        OOOO000O0OO0._opt_base2 = OOOOO00O000O.get(OOOO00OOO000)
                    if (OOOO00OOO000.upper() == 'FRSTRELBASE') | (OOOO00OOO000.upper() == 'RELBASE1'):
                        OOOO000O0OO0._opt_relbase1 = OOOOO00O000O.get(OOOO00OOO000)
                    if (OOOO00OOO000.upper() == 'SCNDRELBASE') | (OOOO00OOO000.upper() == 'RELBASE2'):
                        OOOO000O0OO0._opt_relbase2 = OOOOO00O000O.get(OOOO00OOO000)
            else:
                print('Warning: no quantifiers found. Optimization will not take place (1)')
        else:
            print('Warning: no quantifiers found. Optimization will not take place (2)')

    def mine(OOOOO0OOO0OO, **OO0OO000O0O0):
        if not OOOOO0OOO0OO._initialized:
            print('Class NOT INITIALIZED. Please call constructor with dataframe first')
            return
        OOOOO0OOO0OO.kwargs = None
        if len(OO0OO000O0O0) > 0:
            OOOOO0OOO0OO.kwargs = OO0OO000O0O0
        OOOOO0OOO0OO._init_task()
        if len(OO0OO000O0O0) > 0:
            O0O0OO0O0O0O = OO0OO000O0O0.get('proc', None)
            if not O0O0OO0O0O0O == None:
                OOOOO0OOO0OO._calc_all(**OO0OO000O0O0)
            else:
                print('Rule mining procedure missing')

    def _get_ver(OOO0O000OO00):
        return OOO0O000OO00.version_string

    def _print_disclaimer(OOOO0O0OOOOO):
        print(f'Cleverminer version {OOOO0O0OOOOO._get_ver()}.')

    def _automatic_data_conversions(O0O0O0OOOOO0, OOOOOO0OO00O):
        print('Automatically reordering numeric categories ...')
        for OOO0O0O00000 in range(len(OOOOOO0OO00O.columns)):
            if O0O0O0OOOOO0.verbosity['debug']:
                print(f'#{OOO0O0O00000}: {OOOOOO0OO00O.columns[OOO0O0O00000]} : {OOOOOO0OO00O.dtypes[OOO0O0O00000]}.')
            try:
                OOOOOO0OO00O[OOOOOO0OO00O.columns[OOO0O0O00000]] = OOOOOO0OO00O[OOOOOO0OO00O.columns[OOO0O0O00000]].astype(str).astype(float)
                if O0O0O0OOOOO0.verbosity['debug']:
                    print(f'CONVERTED TO FLOATS #{OOO0O0O00000}: {OOOOOO0OO00O.columns[OOO0O0O00000]} : {OOOOOO0OO00O.dtypes[OOO0O0O00000]}.')
                O0O0OO0000OO = pd.unique(OOOOOO0OO00O[OOOOOO0OO00O.columns[OOO0O0O00000]])
                O0O0O0OO00O0 = True
                for O0O0O00OOO0O in O0O0OO0000OO:
                    if O0O0O00OOO0O % 1 != 0:
                        O0O0O0OO00O0 = False
                if O0O0O0OO00O0:
                    OOOOOO0OO00O[OOOOOO0OO00O.columns[OOO0O0O00000]] = OOOOOO0OO00O[OOOOOO0OO00O.columns[OOO0O0O00000]].astype(int)
                    if O0O0O0OOOOO0.verbosity['debug']:
                        print(f'CONVERTED TO INT #{OOO0O0O00000}: {OOOOOO0OO00O.columns[OOO0O0O00000]} : {OOOOOO0OO00O.dtypes[OOO0O0O00000]}.')
                O0OO0OOO0O00 = pd.unique(OOOOOO0OO00O[OOOOOO0OO00O.columns[OOO0O0O00000]])
                OO0OOOO00OOO = CategoricalDtype(categories=O0OO0OOO0O00.sort(), ordered=True)
                OOOOOO0OO00O[OOOOOO0OO00O.columns[OOO0O0O00000]] = OOOOOO0OO00O[OOOOOO0OO00O.columns[OOO0O0O00000]].astype(OO0OOOO00OOO)
                if O0O0O0OOOOO0.verbosity['debug']:
                    print(f'CONVERTED TO CATEGORY #{OOO0O0O00000}: {OOOOOO0OO00O.columns[OOO0O0O00000]} : {OOOOOO0OO00O.dtypes[OOO0O0O00000]}.')
            except:
                if O0O0O0OOOOO0.verbosity['debug']:
                    print('...cannot be converted to int')
                try:
                    O00O0OO00OO0 = OOOOOO0OO00O[OOOOOO0OO00O.columns[OOO0O0O00000]].unique()
                    if O0O0O0OOOOO0.verbosity['debug']:
                        print(f'Values: {O00O0OO00OO0}')
                    OOOO00O0000O = True
                    O00O0000O000 = []
                    for O0O0O00OOO0O in O00O0OO00OO0:
                        OO00OO00O0OO = re.findall('-?\\d+', O0O0O00OOO0O)
                        if len(OO00OO00O0OO) > 0:
                            O00O0000O000.append(int(OO00OO00O0OO[0]))
                        else:
                            OOOO00O0000O = False
                    if O0O0O0OOOOO0.verbosity['debug']:
                        print(f'Is ok: {OOOO00O0000O}, extracted {O00O0000O000}')
                    if OOOO00O0000O:
                        O0O0OO0OO0O0 = copy.deepcopy(O00O0000O000)
                        O0O0OO0OO0O0.sort()
                        O00O0OO00O0O = []
                        for O0OO0O0OOO00 in O0O0OO0OO0O0:
                            O0OO0OO0OOOO = O00O0000O000.index(O0OO0O0OOO00)
                            O00O0OO00O0O.append(O00O0OO00OO0[O0OO0OO0OOOO])
                        if O0O0O0OOOOO0.verbosity['debug']:
                            print(f'Sorted list: {O00O0OO00O0O}')
                        OO0OOOO00OOO = CategoricalDtype(categories=O00O0OO00O0O, ordered=True)
                        OOOOOO0OO00O[OOOOOO0OO00O.columns[OOO0O0O00000]] = OOOOOO0OO00O[OOOOOO0OO00O.columns[OOO0O0O00000]].astype(OO0OOOO00OOO)
                except:
                    if O0O0O0OOOOO0.verbosity['debug']:
                        print('...cannot extract numbers from all categories')
        print('Automatically reordering numeric categories ...done')

    def _prep_data(O0OO0000OOO0, OO0O0OO0O00O):
        print('Starting data preparation ...')
        O0OO0000OOO0._init_data()
        O0OO0000OOO0.stats['start_prep_time'] = time.time()
        if O0OO0000OOO0.options['automatic_data_conversions']:
            O0OO0000OOO0._automatic_data_conversions(OO0O0OO0O00O)
        O0OO0000OOO0.data['rows_count'] = OO0O0OO0O00O.shape[0]
        for OOO00OOO0000 in OO0O0OO0O00O.select_dtypes(exclude=['category']).columns:
            OO0O0OO0O00O[OOO00OOO0000] = OO0O0OO0O00O[OOO00OOO0000].apply(str)
        try:
            OOO0000000O0 = pd.DataFrame.from_records([(OO0OOO0O00OO, OO0O0OO0O00O[OO0OOO0O00OO].nunique()) for OO0OOO0O00OO in OO0O0OO0O00O.columns], columns=['Column_Name', 'Num_Unique']).sort_values(by=['Num_Unique'])
        except:
            print('Error in input data, probably unsupported data type. Will try to scan for column with unsupported type.')
            OOOO00O0OO0O = ''
            try:
                for OOO00OOO0000 in OO0O0OO0O00O.columns:
                    OOOO00O0OO0O = OOO00OOO0000
                    print(f'...column {OOO00OOO0000} has {int(OO0O0OO0O00O[OOO00OOO0000].nunique())} values')
            except:
                print(f'... detected : column {OOOO00O0OO0O} has unsupported type: {type(OO0O0OO0O00O[OOO00OOO0000])}.')
                exit(1)
            print(f'Error in data profiling - attribute with unsupported type not detected. Please profile attributes manually, only simple attributes are supported.')
            exit(1)
        if O0OO0000OOO0.verbosity['hint']:
            print('Quick profile of input data: unique value counts are:')
            print(OOO0000000O0)
            for OOO00OOO0000 in OO0O0OO0O00O.columns:
                if OO0O0OO0O00O[OOO00OOO0000].nunique() < O0OO0000OOO0.options['max_categories']:
                    OO0O0OO0O00O[OOO00OOO0000] = OO0O0OO0O00O[OOO00OOO0000].astype('category')
                else:
                    print(f"WARNING: attribute {OOO00OOO0000} has more than {O0OO0000OOO0.options['max_categories']} values, will be ignored.\r\n If you haven't set maximum number of categories and you really need more categories and you know what you are doing, please use max_categories option to increase allowed number of categories.")
                    del OO0O0OO0O00O[OOO00OOO0000]
        for OOO00OOO0000 in OO0O0OO0O00O.columns:
            if OO0O0OO0O00O[OOO00OOO0000].nunique() > O0OO0000OOO0.options['max_categories']:
                print(f"WARNING: attribute {OOO00OOO0000} has more than {O0OO0000OOO0.options['max_categories']} values, will be ignored.\r\n If you haven't set maximum number of categories and you really need more categories and you know what you are doing, please use max_categories option to increase allowed number of categories.")
                del OO0O0OO0O00O[OOO00OOO0000]
        if O0OO0000OOO0.options['keep_df']:
            if O0OO0000OOO0.verbosity['debug']:
                print('Keeping df.')
            O0OO0000OOO0.df = OO0O0OO0O00O
        print('Encoding columns into bit-form...')
        OOO00O000O00 = 0
        OOOOOOOO0OOO = 0
        for OOOOO0OO0OO0 in OO0O0OO0O00O:
            if O0OO0000OOO0.verbosity['debug']:
                print('Column: ' + OOOOO0OO0OO0 + ' @ ' + str(time.time()))
            if O0OO0000OOO0.verbosity['debug']:
                print('Column: ' + OOOOO0OO0OO0)
            O0OO0000OOO0.data['varname'].append(OOOOO0OO0OO0)
            O0O0O0OO000O = pd.get_dummies(OO0O0OO0O00O[OOOOO0OO0OO0])
            OOO0OO0OO000 = 0
            if OO0O0OO0O00O.dtypes[OOOOO0OO0OO0].name == 'category':
                OOO0OO0OO000 = 1
            O0OO0000OOO0.data['vtypes'].append(OOO0OO0OO000)
            if O0OO0000OOO0.verbosity['debug']:
                print(O0O0O0OO000O)
                print(OO0O0OO0O00O[OOOOO0OO0OO0])
            OO0OOO0OO0OO = 0
            OO0000O0O0O0 = []
            O0OOOOOO0O0O = []
            if O0OO0000OOO0.verbosity['debug']:
                print('...starting categories ' + str(time.time()))
            for OO0000O0OO00 in O0O0O0OO000O:
                if O0OO0000OOO0.verbosity['debug']:
                    print('....category : ' + str(OO0000O0OO00) + ' @ ' + str(time.time()))
                OO0000O0O0O0.append(OO0000O0OO00)
                O0OO0OOOOOOO = int(0)
                OOOO0O0OOOO0 = O0O0O0OO000O[OO0000O0OO00].values
                if O0OO0000OOO0.verbosity['debug']:
                    print(OOOO0O0OOOO0.ndim)
                OOO0OOOOO00O = np.packbits(OOOO0O0OOOO0, bitorder='little')
                O0OO0OOOOOOO = int.from_bytes(OOO0OOOOO00O, byteorder='little')
                O0OOOOOO0O0O.append(O0OO0OOOOOOO)
                if O0OO0000OOO0.verbosity['debug']:
                    for O0O00O000000 in range(O0OO0000OOO0.data['rows_count']):
                        if OOOO0O0OOOO0[O0O00O000000] > 0:
                            O0OO0OOOOOOO += 1 << O0O00O000000
                            O0OOOOOO0O0O.append(O0OO0OOOOOOO)
                    print('....category ATTEMPT 2: ' + str(OO0000O0OO00) + ' @ ' + str(time.time()))
                    OO00OOO000OO = int(0)
                    OO0O0O0O00O0 = int(1)
                    for O0O00O000000 in range(O0OO0000OOO0.data['rows_count']):
                        if OOOO0O0OOOO0[O0O00O000000] > 0:
                            OO00OOO000OO += OO0O0O0O00O0
                            OO0O0O0O00O0 *= 2
                            OO0O0O0O00O0 = OO0O0O0O00O0 << 1
                            print(str(O0OO0OOOOOOO == OO00OOO000OO) + ' @ ' + str(time.time()))
                OO0OOO0OO0OO += 1
                OOOOOOOO0OOO += 1
                if O0OO0000OOO0.verbosity['debug']:
                    print(OO0000O0O0O0)
            O0OO0000OOO0.data['catnames'].append(OO0000O0O0O0)
            O0OO0000OOO0.data['dm'].append(O0OOOOOO0O0O)
        print('Encoding columns into bit-form...done')
        if O0OO0000OOO0.verbosity['hint']:
            print(f"List of attributes for analysis is: {O0OO0000OOO0.data['varname']}")
            print(f"List of category names for individual attributes is : {O0OO0000OOO0.data['catnames']}")
        if O0OO0000OOO0.verbosity['debug']:
            print(f"List of vtypes is (all should be 1) : {O0OO0000OOO0.data['vtypes']}")
        O0OO0000OOO0.data['data_prepared'] = 1
        print('Data preparation finished.')
        if O0OO0000OOO0.verbosity['debug']:
            print('Number of variables : ' + str(len(O0OO0000OOO0.data['dm'])))
            print('Total number of categories in all variables : ' + str(OOOOOOOO0OOO))
        O0OO0000OOO0.stats['end_prep_time'] = time.time()
        if O0OO0000OOO0.verbosity['debug']:
            print('Time needed for data preparation : ', str(O0OO0000OOO0.stats['end_prep_time'] - O0OO0000OOO0.stats['start_prep_time']))

    def _bitcount(OOOOO0OOOO0O, OO0O000O0O00):
        OOO000000OOO = None
        if OOOOO0OOOO0O._is_py310:
            OOO000000OOO = OO0O000O0O00.bit_count()
        else:
            OOO000000OOO = bin(OO0O000O0O00).count('1')
        return OOO000000OOO

    def _verifyCF(O0O000000OO0, O0O00O00000O):
        O000O0O0O000 = O0O000000OO0._bitcount(O0O00O00000O)
        O0O0OOO0O0OO = []
        O00O0OOOO0O0 = []
        O0O0O0000O0O = 0
        O000OOOOOO00 = 0
        OOOOO000OOOO = 0
        OOOOO0O0OOO0 = 0
        OO00O000O00O = 0
        O0O0000O0000 = 0
        OOOOOOOO00OO = 0
        O000O0O000O0 = 0
        OO000O00OO0O = 0
        OOOOOOO00O00 = None
        O000000O0OOO = None
        O0000O0O0OO0 = None
        if 'min_step_size' in O0O000000OO0.quantifiers:
            OOOOOOO00O00 = O0O000000OO0.quantifiers.get('min_step_size')
        if 'min_rel_step_size' in O0O000000OO0.quantifiers:
            O000000O0OOO = O0O000000OO0.quantifiers.get('min_rel_step_size')
            if O000000O0OOO >= 1 and O000000O0OOO < 100:
                O000000O0OOO = O000000O0OOO / 100
        OO0OOO0O000O = 0
        OOO00OOOO000 = 0
        O0OOOOOOO0OO = []
        if 'aad_weights' in O0O000000OO0.quantifiers:
            OO0OOO0O000O = 1
            O0O0OO00O0O0 = []
            O0OOOOOOO0OO = O0O000000OO0.quantifiers.get('aad_weights')
        OO0O000O0O0O = O0O000000OO0.data['dm'][O0O000000OO0.data['varname'].index(O0O000000OO0.kwargs.get('target'))]

        def O00OOO00OO00(OOOOO00OOOOO, O0OOOOOOOOO0):
            OOO0000OO00O = True
            if OOOOO00OOOOO > O0OOOOOOOOO0:
                if not (OOOOOOO00O00 is None or OOOOO00OOOOO >= O0OOOOOOOOO0 + OOOOOOO00O00):
                    OOO0000OO00O = False
                if not (O000000O0OOO is None or OOOOO00OOOOO >= O0OOOOOOOOO0 * (1 + O000000O0OOO)):
                    OOO0000OO00O = False
            if OOOOO00OOOOO < O0OOOOOOOOO0:
                if not (OOOOOOO00O00 is None or OOOOO00OOOOO <= O0OOOOOOOOO0 - OOOOOOO00O00):
                    OOO0000OO00O = False
                if not (O000000O0OOO is None or OOOOO00OOOOO <= O0OOOOOOOOO0 * (1 - O000000O0OOO)):
                    OOO0000OO00O = False
            return OOO0000OO00O
        for OO0OOOO00000 in range(len(OO0O000O0O0O)):
            O000OOOOOO00 = O0O0O0000O0O
            O0O0O0000O0O = O0O000000OO0._bitcount(O0O00O00000O & OO0O000O0O0O[OO0OOOO00000])
            O0O0OOO0O0OO.append(O0O0O0000O0O)
            if OO0OOOO00000 > 0:
                if O0O0O0000O0O > O000OOOOOO00:
                    if OOOOO000OOOO == 1 and O00OOO00OO00(O0O0O0000O0O, O000OOOOOO00):
                        O000O0O000O0 += 1
                    elif O00OOO00OO00(O0O0O0000O0O, O000OOOOOO00):
                        O000O0O000O0 = 1
                    else:
                        O000O0O000O0 = 0
                    if O000O0O000O0 > OOOOO0O0OOO0:
                        OOOOO0O0OOO0 = O000O0O000O0
                    OOOOO000OOOO = 1
                    if O00OOO00OO00(O0O0O0000O0O, O000OOOOOO00):
                        O0O0000O0000 += 1
                if O0O0O0000O0O < O000OOOOOO00:
                    if OOOOO000OOOO == -1 and O00OOO00OO00(O0O0O0000O0O, O000OOOOOO00):
                        OO000O00OO0O += 1
                    elif O00OOO00OO00(O0O0O0000O0O, O000OOOOOO00):
                        OO000O00OO0O = 1
                    else:
                        OO000O00OO0O = 0
                    if OO000O00OO0O > OO00O000O00O:
                        OO00O000O00O = OO000O00OO0O
                    OOOOO000OOOO = -1
                    if O00OOO00OO00(O0O0O0000O0O, O000OOOOOO00):
                        OOOOOOOO00OO += 1
                if O0O0O0000O0O == O000OOOOOO00:
                    OOOOO000OOOO = 0
                    OO000O00OO0O = 0
                    O000O0O000O0 = 0
            if OO0OOO0O000O:
                OOOO000000OO = O0O000000OO0._bitcount(OO0O000O0O0O[OO0OOOO00000])
                O0O0OO00O0O0.append(OOOO000000OO)
        if OO0OOO0O000O & sum(O0O0OOO0O0OO) > 0:
            for OO0OOOO00000 in range(len(OO0O000O0O0O)):
                if O0O0OO00O0O0[OO0OOOO00000] > 0:
                    if O0O0OOO0O0OO[OO0OOOO00000] / sum(O0O0OOO0O0OO) > O0O0OO00O0O0[OO0OOOO00000] / sum(O0O0OO00O0O0):
                        OOO00OOOO000 += O0OOOOOOO0OO[OO0OOOO00000] * (O0O0OOO0O0OO[OO0OOOO00000] / sum(O0O0OOO0O0OO) / (O0O0OO00O0O0[OO0OOOO00000] / sum(O0O0OO00O0O0)) - 1)
        OOOOOOOO00O0 = True
        for OO00OO0OOO0O in O0O000000OO0.quantifiers.keys():
            if OO00OO0OOO0O.upper() == 'BASE':
                OOOOOOOO00O0 = OOOOOOOO00O0 and O0O000000OO0.quantifiers.get(OO00OO0OOO0O) <= O000O0O0O000
            if OO00OO0OOO0O.upper() == 'RELBASE':
                OOOOOOOO00O0 = OOOOOOOO00O0 and O0O000000OO0.quantifiers.get(OO00OO0OOO0O) <= O000O0O0O000 * 1.0 / O0O000000OO0.data['rows_count']
            if OO00OO0OOO0O.upper() == 'S_UP':
                OOOOOOOO00O0 = OOOOOOOO00O0 and O0O000000OO0.quantifiers.get(OO00OO0OOO0O) <= OOOOO0O0OOO0
            if OO00OO0OOO0O.upper() == 'S_DOWN':
                OOOOOOOO00O0 = OOOOOOOO00O0 and O0O000000OO0.quantifiers.get(OO00OO0OOO0O) <= OO00O000O00O
            if OO00OO0OOO0O.upper() == 'S_ANY_UP':
                OOOOOOOO00O0 = OOOOOOOO00O0 and O0O000000OO0.quantifiers.get(OO00OO0OOO0O) <= OOOOO0O0OOO0
            if OO00OO0OOO0O.upper() == 'S_ANY_DOWN':
                OOOOOOOO00O0 = OOOOOOOO00O0 and O0O000000OO0.quantifiers.get(OO00OO0OOO0O) <= OO00O000O00O
            if OO00OO0OOO0O.upper() == 'MAX':
                OOOOOOOO00O0 = OOOOOOOO00O0 and O0O000000OO0.quantifiers.get(OO00OO0OOO0O) <= max(O0O0OOO0O0OO)
            if OO00OO0OOO0O.upper() == 'MIN':
                OOOOOOOO00O0 = OOOOOOOO00O0 and O0O000000OO0.quantifiers.get(OO00OO0OOO0O) <= min(O0O0OOO0O0OO)
            if OO00OO0OOO0O.upper() == 'RELMAX':
                if sum(O0O0OOO0O0OO) > 0:
                    OOOOOOOO00O0 = OOOOOOOO00O0 and O0O000000OO0.quantifiers.get(OO00OO0OOO0O) <= max(O0O0OOO0O0OO) * 1.0 / sum(O0O0OOO0O0OO)
                else:
                    OOOOOOOO00O0 = False
            if OO00OO0OOO0O.upper() == 'RELMAX_LEQ':
                if sum(O0O0OOO0O0OO) > 0:
                    OOOOOOOO00O0 = OOOOOOOO00O0 and O0O000000OO0.quantifiers.get(OO00OO0OOO0O) >= max(O0O0OOO0O0OO) * 1.0 / sum(O0O0OOO0O0OO)
                else:
                    OOOOOOOO00O0 = False
            if OO00OO0OOO0O.upper() == 'RELMIN':
                if sum(O0O0OOO0O0OO) > 0:
                    OOOOOOOO00O0 = OOOOOOOO00O0 and O0O000000OO0.quantifiers.get(OO00OO0OOO0O) <= min(O0O0OOO0O0OO) * 1.0 / sum(O0O0OOO0O0OO)
                else:
                    OOOOOOOO00O0 = False
            if OO00OO0OOO0O.upper() == 'RELMIN_LEQ':
                if sum(O0O0OOO0O0OO) > 0:
                    OOOOOOOO00O0 = OOOOOOOO00O0 and O0O000000OO0.quantifiers.get(OO00OO0OOO0O) >= min(O0O0OOO0O0OO) * 1.0 / sum(O0O0OOO0O0OO)
                else:
                    OOOOOOOO00O0 = False
            if OO00OO0OOO0O.upper() == 'AAD':
                OOOOOOOO00O0 = OOOOOOOO00O0 and O0O000000OO0.quantifiers.get(OO00OO0OOO0O) <= OOO00OOOO000
            if OO00OO0OOO0O.upper() == 'RELRANGE_LEQ':
                OOO0O0OO0O00 = O0O000000OO0.quantifiers.get(OO00OO0OOO0O)
                if OOO0O0OO0O00 >= 1 and OOO0O0OO0O00 < 100:
                    OOO0O0OO0O00 = OOO0O0OO0O00 * 1.0 / 100
                OOO000O00OOO = min(O0O0OOO0O0OO) * 1.0 / sum(O0O0OOO0O0OO)
                O0O0O0O00OO0 = max(O0O0OOO0O0OO) * 1.0 / sum(O0O0OOO0O0OO)
                OOOOOOOO00O0 = OOOOOOOO00O0 and OOO0O0OO0O00 >= O0O0O0O00OO0 - OOO000O00OOO
        OO0O0OO0000O = {}
        if OOOOOOOO00O0 == True:
            if O0O000000OO0.verbosity['debug']:
                print('Rule found: base: ' + str(O000O0O0O000) + ', hist: ' + str(O0O0OOO0O0OO) + ', max: ' + str(max(O0O0OOO0O0OO)) + ', min: ' + str(min(O0O0OOO0O0OO)) + ', s_up: ' + str(OOOOO0O0OOO0) + ', s_down: ' + str(OO00O000O00O))
            O0O000000OO0.stats['total_valid'] += 1
            OO0O0OO0000O['base'] = O000O0O0O000
            OO0O0OO0000O['rel_base'] = O000O0O0O000 * 1.0 / O0O000000OO0.data['rows_count']
            OO0O0OO0000O['s_up'] = OOOOO0O0OOO0
            OO0O0OO0000O['s_down'] = OO00O000O00O
            OO0O0OO0000O['s_any_up'] = O0O0000O0000
            OO0O0OO0000O['s_any_down'] = OOOOOOOO00OO
            OO0O0OO0000O['max'] = max(O0O0OOO0O0OO)
            OO0O0OO0000O['min'] = min(O0O0OOO0O0OO)
            if O0O000000OO0.verbosity['debug']:
                OO0O0OO0000O['rel_max'] = max(O0O0OOO0O0OO) * 1.0 / O0O000000OO0.data['rows_count']
                OO0O0OO0000O['rel_min'] = min(O0O0OOO0O0OO) * 1.0 / O0O000000OO0.data['rows_count']
            if sum(O0O0OOO0O0OO) > 0:
                OO0O0OO0000O['rel_max'] = max(O0O0OOO0O0OO) * 1.0 / sum(O0O0OOO0O0OO)
                OO0O0OO0000O['rel_min'] = min(O0O0OOO0O0OO) * 1.0 / sum(O0O0OOO0O0OO)
            else:
                OO0O0OO0000O['rel_max'] = 0
                OO0O0OO0000O['rel_min'] = 0
            OO0O0OO0000O['hist'] = O0O0OOO0O0OO
            if OO0OOO0O000O:
                OO0O0OO0000O['aad'] = OOO00OOOO000
                OO0O0OO0000O['hist_full'] = O0O0OO00O0O0
                OO0O0OO0000O['rel_hist'] = [O0000O00O000 / sum(O0O0OOO0O0OO) for O0000O00O000 in O0O0OOO0O0OO]
                OO0O0OO0000O['rel_hist_full'] = [O00O0000O0OO / sum(O0O0OO00O0O0) for O00O0000O0OO in O0O0OO00O0O0]
        if O0O000000OO0.verbosity['debug']:
            print('Info: base: ' + str(O000O0O0O000) + ', hist: ' + str(O0O0OOO0O0OO) + ', max: ' + str(max(O0O0OOO0O0OO)) + ', min: ' + str(min(O0O0OOO0O0OO)) + ', s_up: ' + str(OOOOO0O0OOO0) + ', s_down: ' + str(OO00O000O00O))
        return (OOOOOOOO00O0, OO0O0OO0000O)

    def _verifyUIC(O000000OO0O0, O0OOO0O00O0O):
        OOO0O00OOO00 = {}
        O0OOO0O0OOOO = 0
        for OO000O00OOO0 in O000000OO0O0.task_actinfo['cedents']:
            OOO0O00OOO00[OO000O00OOO0['cedent_type']] = OO000O00OOO0['filter_value']
            O0OOO0O0OOOO = O0OOO0O0OOOO + 1
        if O000000OO0O0.verbosity['debug']:
            print(OO000O00OOO0['cedent_type'] + ' : ' + str(OO000O00OOO0['filter_value']))
        O0OOO0O0O00O = O000000OO0O0._bitcount(O0OOO0O00O0O)
        OO0OO0OO0000 = []
        O0O0000O00OO = 0
        O0OO0O0000O0 = 0
        O00O0OO0OO0O = 0
        O00OO0000O00 = []
        O00000OO0OOO = []
        if 'aad_weights' in O000000OO0O0.quantifiers:
            O00OO0000O00 = O000000OO0O0.quantifiers.get('aad_weights')
            O0OO0O0000O0 = 1
        O000OOOO0OO0 = O000000OO0O0.data['dm'][O000000OO0O0.data['varname'].index(O000000OO0O0.kwargs.get('target'))]
        for O000OOOO000O in range(len(O000OOOO0OO0)):
            OOO0000OO000 = O0O0000O00OO
            O0O0000O00OO = O000000OO0O0._bitcount(O0OOO0O00O0O & O000OOOO0OO0[O000OOOO000O])
            OO0OO0OO0000.append(O0O0000O00OO)
            O0O0000OO0OO = O000000OO0O0._bitcount(OOO0O00OOO00['cond'] & O000OOOO0OO0[O000OOOO000O])
            O00000OO0OOO.append(O0O0000OO0OO)
        O00O0OO0O0O0 = 0
        OOO000OO0O0O = 0
        if O0OO0O0000O0 & sum(OO0OO0OO0000) > 0:
            for O000OOOO000O in range(len(O000OOOO0OO0)):
                if O00000OO0OOO[O000OOOO000O] > 0:
                    if OO0OO0OO0000[O000OOOO000O] / sum(OO0OO0OO0000) > O00000OO0OOO[O000OOOO000O] / sum(O00000OO0OOO):
                        O00O0OO0OO0O += O00OO0000O00[O000OOOO000O] * (OO0OO0OO0000[O000OOOO000O] / sum(OO0OO0OO0000) / (O00000OO0OOO[O000OOOO000O] / sum(O00000OO0OOO)) - 1)
                if O00OO0000O00[O000OOOO000O] > 0:
                    O00O0OO0O0O0 += OO0OO0OO0000[O000OOOO000O]
                    OOO000OO0O0O += O00000OO0OOO[O000OOOO000O]
        OOOO0OO0OO00 = 0
        if sum(OO0OO0OO0000) > 0 and OOO000OO0O0O > 0:
            OOOO0OO0OO00 = O00O0OO0O0O0 / sum(OO0OO0OO0000) / (OOO000OO0O0O / sum(O00000OO0OOO))
        O0OOO0OOOOOO = True
        for O000O00OOOO0 in O000000OO0O0.quantifiers.keys():
            if O000O00OOOO0.upper() == 'BASE':
                O0OOO0OOOOOO = O0OOO0OOOOOO and O000000OO0O0.quantifiers.get(O000O00OOOO0) <= O0OOO0O0O00O
            if O000O00OOOO0.upper() == 'RELBASE':
                O0OOO0OOOOOO = O0OOO0OOOOOO and O000000OO0O0.quantifiers.get(O000O00OOOO0) <= O0OOO0O0O00O * 1.0 / O000000OO0O0.data['rows_count']
            if O000O00OOOO0.upper() == 'AAD_SCORE':
                O0OOO0OOOOOO = O0OOO0OOOOOO and O000000OO0O0.quantifiers.get(O000O00OOOO0) <= O00O0OO0OO0O
            if O000O00OOOO0.upper() == 'RELEVANT_CAT_BASE':
                O0OOO0OOOOOO = O0OOO0OOOOOO and O000000OO0O0.quantifiers.get(O000O00OOOO0) <= O00O0OO0O0O0
            if O000O00OOOO0.upper() == 'RELEVANT_BASE_LIFT':
                O0OOO0OOOOOO = O0OOO0OOOOOO and O000000OO0O0.quantifiers.get(O000O00OOOO0) <= OOOO0OO0OO00
        OO0O00OOO00O = {}
        if O0OOO0OOOOOO == True:
            O000000OO0O0.stats['total_valid'] += 1
            OO0O00OOO00O['base'] = O0OOO0O0O00O
            OO0O00OOO00O['rel_base'] = O0OOO0O0O00O * 1.0 / O000000OO0O0.data['rows_count']
            OO0O00OOO00O['hist'] = OO0OO0OO0000
            OO0O00OOO00O['aad_score'] = O00O0OO0OO0O
            OO0O00OOO00O['hist_cond'] = O00000OO0OOO
            OO0O00OOO00O['rel_hist'] = [O00OO0000000 / sum(OO0OO0OO0000) for O00OO0000000 in OO0OO0OO0000]
            OO0O00OOO00O['rel_hist_cond'] = [O00O00O000OO / sum(O00000OO0OOO) for O00O00O000OO in O00000OO0OOO]
            OO0O00OOO00O['relevant_base_lift'] = OOOO0OO0OO00
            OO0O00OOO00O['relevant_cat_base'] = O00O0OO0O0O0
            OO0O00OOO00O['relevant_cat_base_full'] = OOO000OO0O0O
        return (O0OOO0OOOOOO, OO0O00OOO00O)

    def _verify4ft(O0O0O00O00O0, O00OOOOOOO0O, _trace_cedent=None, _traces=None):
        O0000O0O0O00 = {}
        OOO00O000OOO = 0
        for O0OO0O000OO0 in O0O0O00O00O0.task_actinfo['cedents']:
            O0000O0O0O00[O0OO0O000OO0['cedent_type']] = O0OO0O000OO0['filter_value']
            OOO00O000OOO = OOO00O000OOO + 1
        O000O000000O = O0O0O00O00O0._bitcount(O0000O0O0O00['ante'] & O0000O0O0O00['succ'] & O0000O0O0O00['cond'])
        OOOOOOO0O000 = None
        OOOOOOO0O000 = 0
        if O000O000000O > 0:
            OOOOOOO0O000 = O0O0O00O00O0._bitcount(O0000O0O0O00['ante'] & O0000O0O0O00['succ'] & O0000O0O0O00['cond']) * 1.0 / O0O0O00O00O0._bitcount(O0000O0O0O00['ante'] & O0000O0O0O00['cond'])
        OOOO00O0O0OO = 1 << O0O0O00O00O0.data['rows_count']
        OOO0O0OOO0O0 = O0O0O00O00O0._bitcount(O0000O0O0O00['ante'] & O0000O0O0O00['succ'] & O0000O0O0O00['cond'])
        OO00OO000O0O = O0O0O00O00O0._bitcount(O0000O0O0O00['ante'] & ~(OOOO00O0O0OO | O0000O0O0O00['succ']) & O0000O0O0O00['cond'])
        O0OO0O000OO0 = O0O0O00O00O0._bitcount(~(OOOO00O0O0OO | O0000O0O0O00['ante']) & O0000O0O0O00['succ'] & O0000O0O0O00['cond'])
        OO0000OOOO00 = O0O0O00O00O0._bitcount(~(OOOO00O0O0OO | O0000O0O0O00['ante']) & ~(OOOO00O0O0OO | O0000O0O0O00['succ']) & O0000O0O0O00['cond'])
        OOOOOO00OOOO = 0
        O000OOO0OOO0 = 0
        if (OOO0O0OOO0O0 + OO00OO000O0O) * (OOO0O0OOO0O0 + O0OO0O000OO0) > 0:
            OOOOOO00OOOO = OOO0O0OOO0O0 * (OOO0O0OOO0O0 + OO00OO000O0O + O0OO0O000OO0 + OO0000OOOO00) / (OOO0O0OOO0O0 + OO00OO000O0O) / (OOO0O0OOO0O0 + O0OO0O000OO0) - 1
            O000OOO0OOO0 = OOOOOO00OOOO + 1
        else:
            OOOOOO00OOOO = None
            O000OOO0OOO0 = None
        O0O0OO00O00O = 0
        if (OOO0O0OOO0O0 + OO00OO000O0O) * (OOO0O0OOO0O0 + O0OO0O000OO0) > 0:
            O0O0OO00O00O = 1 - OOO0O0OOO0O0 * (OOO0O0OOO0O0 + OO00OO000O0O + O0OO0O000OO0 + OO0000OOOO00) / (OOO0O0OOO0O0 + OO00OO000O0O) / (OOO0O0OOO0O0 + O0OO0O000OO0)
        else:
            O0O0OO00O00O = None
        O00O0O0O0000 = True
        for OO0000OO00OO in O0O0O00O00O0.quantifiers.keys():
            if OO0000OO00OO.upper() == 'BASE':
                O00O0O0O0000 = O00O0O0O0000 and O0O0O00O00O0.quantifiers.get(OO0000OO00OO) <= O000O000000O
            if OO0000OO00OO.upper() == 'RELBASE':
                O00O0O0O0000 = O00O0O0O0000 and O0O0O00O00O0.quantifiers.get(OO0000OO00OO) <= O000O000000O * 1.0 / O0O0O00O00O0.data['rows_count']
            if OO0000OO00OO.upper() == 'PIM' or OO0000OO00OO.upper() == 'CONF':
                O00O0O0O0000 = O00O0O0O0000 and O0O0O00O00O0.quantifiers.get(OO0000OO00OO) <= OOOOOOO0O000
            if OO0000OO00OO.upper() == 'AAD':
                if OOOOOO00OOOO != None:
                    O00O0O0O0000 = O00O0O0O0000 and O0O0O00O00O0.quantifiers.get(OO0000OO00OO) <= OOOOOO00OOOO
                else:
                    O00O0O0O0000 = False
            if OO0000OO00OO.upper() == 'BAD':
                if O0O0OO00O00O != None:
                    O00O0O0O0000 = O00O0O0O0000 and O0O0O00O00O0.quantifiers.get(OO0000OO00OO) <= O0O0OO00O00O
                else:
                    O00O0O0O0000 = False
            if OO0000OO00OO.upper() == 'DBLPIM':
                if OOO0O0OOO0O0 + OO00OO000O0O + O0OO0O000OO0 > 0:
                    OO0OOOO000O0 = O0O0O00O00O0.quantifiers.get(OO0000OO00OO)
                    O00O0O0O0000 = O00O0O0O0000 and OO0OOOO000O0 <= OOO0O0OOO0O0 / (OOO0O0OOO0O0 + OO00OO000O0O + O0OO0O000OO0)
                else:
                    O00O0O0O0000 = False
            if OO0000OO00OO.upper() == 'EQUIV':
                if OOO0O0OOO0O0 + OO00OO000O0O + O0OO0O000OO0 + OO0000OOOO00 > 0:
                    OO0OOOO000O0 = O0O0O00O00O0.quantifiers.get(OO0000OO00OO)
                    O00O0O0O0000 = O00O0O0O0000 and OO0OOOO000O0 <= (OOO0O0OOO0O0 + OO0000OOOO00) / (OOO0O0OOO0O0 + OO00OO000O0O + O0OO0O000OO0 + OO0000OOOO00)
                else:
                    O00O0O0O0000 = False
            if OO0000OO00OO.upper() == 'LAMBDA' or OO0000OO00OO.upper() == 'FN':
                OOO0O000OO0O = O0O0O00O00O0.quantifiers.get(OO0000OO00OO)
                O0OO00O00O00 = [OOO0O0OOO0O0, OO00OO000O0O, O0OO0O000OO0, OO0000OOOO00]
                O0000O0O0OOO = OOO0O000OO0O.__code__.co_argcount
                if O0000O0O0OOO == 1:
                    O00O0O0O0000 = O00O0O0O0000 and OOO0O000OO0O(O0OO00O00O00)
                elif O0000O0O0OOO == 2:
                    O00OO00O0OO0 = {}
                    OO00000O000O = {}
                    OO00000O000O['varname'] = O0O0O00O00O0.data['varname']
                    OO00000O000O['catnames'] = O0O0O00O00O0.data['catnames']
                    O00OO00O0OO0['datalabels'] = OO00000O000O
                    O00OO00O0OO0['trace_cedent'] = _trace_cedent
                    O00OO00O0OO0['traces'] = _traces
                    O00O0O0O0000 = O00O0O0O0000 and OOO0O000OO0O(O0OO00O00O00, O00OO00O0OO0)
                else:
                    print(f'Unsupported number of arguments for lambda function ({O0000O0O0OOO} for procedure SD4ft-Miner')
            OO0OO0OOO000 = {}
        if O00O0O0O0000 == True:
            O0O0O00O00O0.stats['total_valid'] += 1
            OO0OO0OOO000['base'] = O000O000000O
            OO0OO0OOO000['rel_base'] = O000O000000O * 1.0 / O0O0O00O00O0.data['rows_count']
            OO0OO0OOO000['conf'] = OOOOOOO0O000
            OO0OO0OOO000['aad'] = OOOOOO00OOOO
            OO0OO0OOO000['bad'] = O0O0OO00O00O
            OO0OO0OOO000['fourfold'] = [OOO0O0OOO0O0, OO00OO000O0O, O0OO0O000OO0, OO0000OOOO00]
        return (O00O0O0O0000, OO0OO0OOO000)

    def _verifysd4ft(O00000OOO0OO, O0000000O0O0):
        OOOO0O0O0O0O = {}
        OO0O0000OO00 = 0
        for OOOOOO0OOOOO in O00000OOO0OO.task_actinfo['cedents']:
            OOOO0O0O0O0O[OOOOOO0OOOOO['cedent_type']] = OOOOOO0OOOOO['filter_value']
            OO0O0000OO00 = OO0O0000OO00 + 1
        OO0O00OOOOO0 = O00000OOO0OO._bitcount(OOOO0O0O0O0O['ante'] & OOOO0O0O0O0O['succ'] & OOOO0O0O0O0O['cond'] & OOOO0O0O0O0O['frst'])
        OO000O0OO00O = O00000OOO0OO._bitcount(OOOO0O0O0O0O['ante'] & OOOO0O0O0O0O['succ'] & OOOO0O0O0O0O['cond'] & OOOO0O0O0O0O['scnd'])
        OO0O00O00000 = None
        O0OO0O0000OO = 0
        OO0O00OO00O0 = 0
        if OO0O00OOOOO0 > 0:
            O0OO0O0000OO = O00000OOO0OO._bitcount(OOOO0O0O0O0O['ante'] & OOOO0O0O0O0O['succ'] & OOOO0O0O0O0O['cond'] & OOOO0O0O0O0O['frst']) * 1.0 / O00000OOO0OO._bitcount(OOOO0O0O0O0O['ante'] & OOOO0O0O0O0O['cond'] & OOOO0O0O0O0O['frst'])
        if OO000O0OO00O > 0:
            OO0O00OO00O0 = O00000OOO0OO._bitcount(OOOO0O0O0O0O['ante'] & OOOO0O0O0O0O['succ'] & OOOO0O0O0O0O['cond'] & OOOO0O0O0O0O['scnd']) * 1.0 / O00000OOO0OO._bitcount(OOOO0O0O0O0O['ante'] & OOOO0O0O0O0O['cond'] & OOOO0O0O0O0O['scnd'])
        OOOO000OOO0O = 1 << O00000OOO0OO.data['rows_count']
        O00OOOOO0O00 = O00000OOO0OO._bitcount(OOOO0O0O0O0O['ante'] & OOOO0O0O0O0O['succ'] & OOOO0O0O0O0O['cond'] & OOOO0O0O0O0O['frst'])
        OOO00OO00OOO = O00000OOO0OO._bitcount(OOOO0O0O0O0O['ante'] & ~(OOOO000OOO0O | OOOO0O0O0O0O['succ']) & OOOO0O0O0O0O['cond'] & OOOO0O0O0O0O['frst'])
        O0OOOOO00OO0 = O00000OOO0OO._bitcount(~(OOOO000OOO0O | OOOO0O0O0O0O['ante']) & OOOO0O0O0O0O['succ'] & OOOO0O0O0O0O['cond'] & OOOO0O0O0O0O['frst'])
        O0OOO0O0000O = O00000OOO0OO._bitcount(~(OOOO000OOO0O | OOOO0O0O0O0O['ante']) & ~(OOOO000OOO0O | OOOO0O0O0O0O['succ']) & OOOO0O0O0O0O['cond'] & OOOO0O0O0O0O['frst'])
        OOOOO000O000 = O00000OOO0OO._bitcount(OOOO0O0O0O0O['ante'] & OOOO0O0O0O0O['succ'] & OOOO0O0O0O0O['cond'] & OOOO0O0O0O0O['scnd'])
        OO0O0O00O0OO = O00000OOO0OO._bitcount(OOOO0O0O0O0O['ante'] & ~(OOOO000OOO0O | OOOO0O0O0O0O['succ']) & OOOO0O0O0O0O['cond'] & OOOO0O0O0O0O['scnd'])
        OO0O0O0OO0O0 = O00000OOO0OO._bitcount(~(OOOO000OOO0O | OOOO0O0O0O0O['ante']) & OOOO0O0O0O0O['succ'] & OOOO0O0O0O0O['cond'] & OOOO0O0O0O0O['scnd'])
        OO0OOOO00O0O = O00000OOO0OO._bitcount(~(OOOO000OOO0O | OOOO0O0O0O0O['ante']) & ~(OOOO000OOO0O | OOOO0O0O0O0O['succ']) & OOOO0O0O0O0O['cond'] & OOOO0O0O0O0O['scnd'])
        O00OOO0OOO00 = True
        for O0OOOOO0OOOO in O00000OOO0OO.quantifiers.keys():
            if (O0OOOOO0OOOO.upper() == 'FRSTBASE') | (O0OOOOO0OOOO.upper() == 'BASE1'):
                O00OOO0OOO00 = O00OOO0OOO00 and O00000OOO0OO.quantifiers.get(O0OOOOO0OOOO) <= OO0O00OOOOO0
            if (O0OOOOO0OOOO.upper() == 'SCNDBASE') | (O0OOOOO0OOOO.upper() == 'BASE2'):
                O00OOO0OOO00 = O00OOO0OOO00 and O00000OOO0OO.quantifiers.get(O0OOOOO0OOOO) <= OO000O0OO00O
            if (O0OOOOO0OOOO.upper() == 'FRSTRELBASE') | (O0OOOOO0OOOO.upper() == 'RELBASE1'):
                O00OOO0OOO00 = O00OOO0OOO00 and O00000OOO0OO.quantifiers.get(O0OOOOO0OOOO) <= OO0O00OOOOO0 * 1.0 / O00000OOO0OO.data['rows_count']
            if (O0OOOOO0OOOO.upper() == 'SCNDRELBASE') | (O0OOOOO0OOOO.upper() == 'RELBASE2'):
                O00OOO0OOO00 = O00OOO0OOO00 and O00000OOO0OO.quantifiers.get(O0OOOOO0OOOO) <= OO000O0OO00O * 1.0 / O00000OOO0OO.data['rows_count']
            if (O0OOOOO0OOOO.upper() == 'FRSTPIM') | (O0OOOOO0OOOO.upper() == 'PIM1') | (O0OOOOO0OOOO.upper() == 'FRSTCONF') | (O0OOOOO0OOOO.upper() == 'CONF1'):
                O00OOO0OOO00 = O00OOO0OOO00 and O00000OOO0OO.quantifiers.get(O0OOOOO0OOOO) <= O0OO0O0000OO
            if (O0OOOOO0OOOO.upper() == 'SCNDPIM') | (O0OOOOO0OOOO.upper() == 'PIM2') | (O0OOOOO0OOOO.upper() == 'SCNDCONF') | (O0OOOOO0OOOO.upper() == 'CONF2'):
                O00OOO0OOO00 = O00OOO0OOO00 and O00000OOO0OO.quantifiers.get(O0OOOOO0OOOO) <= OO0O00OO00O0
            if (O0OOOOO0OOOO.upper() == 'DELTAPIM') | (O0OOOOO0OOOO.upper() == 'DELTACONF'):
                O00OOO0OOO00 = O00OOO0OOO00 and O00000OOO0OO.quantifiers.get(O0OOOOO0OOOO) <= O0OO0O0000OO - OO0O00OO00O0
            if (O0OOOOO0OOOO.upper() == 'RATIOPIM') | (O0OOOOO0OOOO.upper() == 'RATIOCONF'):
                if OO0O00OO00O0 > 0:
                    O00OOO0OOO00 = O00OOO0OOO00 and O00000OOO0OO.quantifiers.get(O0OOOOO0OOOO) <= O0OO0O0000OO * 1.0 / OO0O00OO00O0
                else:
                    O00OOO0OOO00 = False
            if (O0OOOOO0OOOO.upper() == 'RATIOPIM_LEQ') | (O0OOOOO0OOOO.upper() == 'RATIOCONF_LEQ'):
                if OO0O00OO00O0 > 0:
                    O00OOO0OOO00 = O00OOO0OOO00 and O00000OOO0OO.quantifiers.get(O0OOOOO0OOOO) >= O0OO0O0000OO * 1.0 / OO0O00OO00O0
                else:
                    O00OOO0OOO00 = False
            if O0OOOOO0OOOO.upper() == 'LAMBDA' or O0OOOOO0OOOO.upper() == 'FN':
                OO0OO000OOO0 = O00000OOO0OO.quantifiers.get(O0OOOOO0OOOO)
                O00OOOO0O00O = OO0OO000OOO0.func_code.co_argcount
                OO00OOOO0000 = [O00OOOOO0O00, OOO00OO00OOO, O0OOOOO00OO0, O0OOO0O0000O]
                OOO00O0O00OO = [OOOOO000O000, OO0O0O00O0OO, OO0O0O0OO0O0, OO0OOOO00O0O]
                if O00OOOO0O00O == 2:
                    O00OOO0OOO00 = O00OOO0OOO00 and OO0OO000OOO0(OO00OOOO0000, OOO00O0O00OO)
                elif O00OOOO0O00O == 3:
                    O00OOO0OOO00 = O00OOO0OOO00 and OO0OO000OOO0(OO00OOOO0000, OOO00O0O00OO, None)
                else:
                    print(f'Unsupported number of arguments for lambda function ({O00OOOO0O00O} for procedure SD4ft-Miner')
        O000O00000O0 = {}
        if O00OOO0OOO00 == True:
            O00000OOO0OO.stats['total_valid'] += 1
            O000O00000O0['base1'] = OO0O00OOOOO0
            O000O00000O0['base2'] = OO000O0OO00O
            O000O00000O0['rel_base1'] = OO0O00OOOOO0 * 1.0 / O00000OOO0OO.data['rows_count']
            O000O00000O0['rel_base2'] = OO000O0OO00O * 1.0 / O00000OOO0OO.data['rows_count']
            O000O00000O0['conf1'] = O0OO0O0000OO
            O000O00000O0['conf2'] = OO0O00OO00O0
            O000O00000O0['deltaconf'] = O0OO0O0000OO - OO0O00OO00O0
            if OO0O00OO00O0 > 0:
                O000O00000O0['ratioconf'] = O0OO0O0000OO * 1.0 / OO0O00OO00O0
            else:
                O000O00000O0['ratioconf'] = None
            O000O00000O0['fourfold1'] = [O00OOOOO0O00, OOO00OO00OOO, O0OOOOO00OO0, O0OOO0O0000O]
            O000O00000O0['fourfold2'] = [OOOOO000O000, OO0O0O00O0OO, OO0O0O0OO0O0, OO0OOOO00O0O]
        return (O00OOO0OOO00, O000O00000O0)

    def _verify_opt(O0OOO0O0OO0O, OO00OO000O00, O0000OOO0OOO):
        O0OOO0O0OO0O.stats['total_ver'] += 1
        O0O000OO0OO0 = False
        if not OO00OO000O00['optim'].get('only_con'):
            return False
        if O0OOO0O0OO0O.verbosity['debug']:
            print(O0OOO0O0OO0O.options['optimizations'])
        if not O0OOO0O0OO0O.options['optimizations']:
            if O0OOO0O0OO0O.verbosity['debug']:
                print('NO OPTS')
            return False
        if O0OOO0O0OO0O.verbosity['debug']:
            print('OPTS')
        OOOO00OO000O = {}
        for OO0O0O0OO000 in O0OOO0O0OO0O.task_actinfo['cedents']:
            if O0OOO0O0OO0O.verbosity['debug']:
                print(OO0O0O0OO000['cedent_type'])
            OOOO00OO000O[OO0O0O0OO000['cedent_type']] = OO0O0O0OO000['filter_value']
            if O0OOO0O0OO0O.verbosity['debug']:
                print(OO0O0O0OO000['cedent_type'] + ' : ' + str(OO0O0O0OO000['filter_value']))
        OOO00O0OO0OO = 1 << O0OOO0O0OO0O.data['rows_count']
        OOO0O0O0O0O0 = OOO00O0OO0OO - 1
        O0000OOO0O0O = ''
        O0O0O0O0OO00 = 0
        if OOOO00OO000O.get('ante') != None:
            OOO0O0O0O0O0 = OOO0O0O0O0O0 & OOOO00OO000O['ante']
        if OOOO00OO000O.get('succ') != None:
            OOO0O0O0O0O0 = OOO0O0O0O0O0 & OOOO00OO000O['succ']
        if OOOO00OO000O.get('cond') != None:
            OOO0O0O0O0O0 = OOO0O0O0O0O0 & OOOO00OO000O['cond']
        O0OOOOOOOOOO = None
        if (O0OOO0O0OO0O.proc == 'CFMiner') | (O0OOO0O0OO0O.proc == '4ftMiner') | (O0OOO0O0OO0O.proc == 'UICMiner'):
            O00OOO0OOOO0 = O0OOO0O0OO0O._bitcount(OOO0O0O0O0O0)
            if not O0OOO0O0OO0O._opt_base == None:
                if not O0OOO0O0OO0O._opt_base <= O00OOO0OOOO0:
                    O0O000OO0OO0 = True
            if not O0OOO0O0OO0O._opt_relbase == None:
                if not O0OOO0O0OO0O._opt_relbase <= O00OOO0OOOO0 * 1.0 / O0OOO0O0OO0O.data['rows_count']:
                    O0O000OO0OO0 = True
        if O0OOO0O0OO0O.proc == 'SD4ftMiner':
            O00OOO0OOOO0 = O0OOO0O0OO0O._bitcount(OOO0O0O0O0O0)
            if (not O0OOO0O0OO0O._opt_base1 == None) & (not O0OOO0O0OO0O._opt_base2 == None):
                if not max(O0OOO0O0OO0O._opt_base1, O0OOO0O0OO0O._opt_base2) <= O00OOO0OOOO0:
                    O0O000OO0OO0 = True
            if (not O0OOO0O0OO0O._opt_relbase1 == None) & (not O0OOO0O0OO0O._opt_relbase2 == None):
                if not max(O0OOO0O0OO0O._opt_relbase1, O0OOO0O0OO0O._opt_relbase2) <= O00OOO0OOOO0 * 1.0 / O0OOO0O0OO0O.data['rows_count']:
                    O0O000OO0OO0 = True
        return O0O000OO0OO0

    def _print(O0OO0OOOO00O, O000OO000000, OO0O0OO000OO, OOOOOO0O00O0):
        if len(OO0O0OO000OO) != len(OOOOOO0O00O0):
            print('DIFF IN LEN for following cedent : ' + str(len(OO0O0OO000OO)) + ' vs ' + str(len(OOOOOO0O00O0)))
            print('trace cedent : ' + str(OO0O0OO000OO) + ', traces ' + str(OOOOOO0O00O0))
        OO0000OOOO0O = ''
        O0OOO00O0O00 = {}
        OOO0O0000OOO = []
        for OO00O0000OO0 in range(len(OO0O0OO000OO)):
            OOO0OO00000O = O0OO0OOOO00O.data['varname'].index(O000OO000000['defi'].get('attributes')[OO0O0OO000OO[OO00O0000OO0]].get('name'))
            OO0000OOOO0O = OO0000OOOO0O + O0OO0OOOO00O.data['varname'][OOO0OO00000O] + '('
            OOO0O0000OOO.append(OOO0OO00000O)
            OOOO00O0O000 = []
            for O0OO0OO0O0OO in OOOOOO0O00O0[OO00O0000OO0]:
                OO0000OOOO0O = OO0000OOOO0O + str(O0OO0OOOO00O.data['catnames'][OOO0OO00000O][O0OO0OO0O0OO]) + ' '
                OOOO00O0O000.append(str(O0OO0OOOO00O.data['catnames'][OOO0OO00000O][O0OO0OO0O0OO]))
            OO0000OOOO0O = OO0000OOOO0O[:-1] + ')'
            O0OOO00O0O00[O0OO0OOOO00O.data['varname'][OOO0OO00000O]] = OOOO00O0O000
            if OO00O0000OO0 + 1 < len(OO0O0OO000OO):
                OO0000OOOO0O = OO0000OOOO0O + ' & '
        return (OO0000OOOO0O, O0OOO00O0O00, OOO0O0000OOO)

    def _print_hypo(O0OOOOOOO0O0, OOOO00000O0O):
        O0OOOOOOO0O0.print_rule(OOOO00000O0O)

    def _print_rule(OOOO0OOOOO00, O0000000OOOO):
        if OOOO0OOOOO00.verbosity['print_rules']:
            print('Rules info : ' + str(O0000000OOOO['params']))
            for O0O000O0OOO0 in OOOO0OOOOO00.task_actinfo['cedents']:
                print(O0O000O0OOO0['cedent_type'] + ' = ' + O0O000O0OOO0['generated_string'])

    def _genvar(O00O0000O00O, O000O00O0000, O0000OOO00OO, O0OO00O000O0, O000OO00OO0O, OOO00OO00O00, O000O00O0OOO, O0O0OO0O0OO0, O0O00O0O000O, OO00OOOOO000):
        OO000OOOO0OO = 0
        OO0O0O00O0O0 = []
        for O00OO00O0O0O in range(O0000OOO00OO['num_cedent']):
            if 'force' in O0000OOO00OO['defi'].get('attributes')[O00OO00O0O0O] and O0000OOO00OO['defi'].get('attributes')[O00OO00O0O0O].get('force'):
                OO0O0O00O0O0.append(O00OO00O0O0O)
        if O0000OOO00OO['num_cedent'] > 0:
            OO000OOOO0OO = (OO00OOOOO000 - O0O00O0O000O) / O0000OOO00OO['num_cedent']
        if O0000OOO00OO['num_cedent'] == 0:
            if len(O000O00O0000['cedents_to_do']) > len(O000O00O0000['cedents']):
                O0000O00OO00, O000000OOOOO, OOO00OOOOOO0 = O00O0000O00O._print(O0000OOO00OO, O0OO00O000O0, O000OO00OO0O)
                O0000OOO00OO['generated_string'] = O0000O00OO00
                O0000OOO00OO['rule'] = O000000OOOOO
                O0000OOO00OO['filter_value'] = (1 << O00O0000O00O.data['rows_count']) - 1
                O0000OOO00OO['traces'] = []
                O0000OOO00OO['trace_cedent'] = []
                O0000OOO00OO['trace_cedent_asindata'] = []
                O000O00O0000['cedents'].append(O0000OOO00OO)
                O0OO00O000O0.append(None)
                O00O0000O00O._start_cedent(O000O00O0000, O0O00O0O000O, OO00OOOOO000)
                O000O00O0000['cedents'].pop()
        for O00OO00O0O0O in range(O0000OOO00OO['num_cedent']):
            O0O0O00OO00O = True
            for OO000OO00000 in range(len(OO0O0O00O0O0)):
                if OO000OO00000 < O00OO00O0O0O and OO000OO00000 not in O0OO00O000O0 and (OO000OO00000 in OO0O0O00O0O0):
                    O0O0O00OO00O = False
            if (len(O0OO00O000O0) == 0 or O00OO00O0O0O > O0OO00O000O0[-1]) and O0O0O00OO00O:
                O0OO00O000O0.append(O00OO00O0O0O)
                OOOOO00000OO = O00O0000O00O.data['varname'].index(O0000OOO00OO['defi'].get('attributes')[O00OO00O0O0O].get('name'))
                O0O00OOO00O0 = O0000OOO00OO['defi'].get('attributes')[O00OO00O0O0O].get('minlen')
                O00O0O0OOO0O = O0000OOO00OO['defi'].get('attributes')[O00OO00O0O0O].get('maxlen')
                OO0O00OO0O00 = O0000OOO00OO['defi'].get('attributes')[O00OO00O0O0O].get('type')
                OOO0O0O00OOO = len(O00O0000O00O.data['dm'][OOOOO00000OO])
                OO0O00O00OO0 = []
                O000OO00OO0O.append(OO0O00O00OO0)
                O00OOOO0000O = int(0)
                O00O0000O00O._gencomb(O000O00O0000, O0000OOO00OO, O0OO00O000O0, O000OO00OO0O, OO0O00O00OO0, OOO00OO00O00, O00OOOO0000O, OOO0O0O00OOO, OO0O00OO0O00, O000O00O0OOO, O0O0OO0O0OO0, O0O00OOO00O0, O00O0O0OOO0O, O0O00O0O000O + O00OO00O0O0O * OO000OOOO0OO, O0O00O0O000O + (O00OO00O0O0O + 1) * OO000OOOO0OO)
                O000OO00OO0O.pop()
                O0OO00O000O0.pop()

    def _gencomb(OOO0OO00O000, O00OO000O0OO, O0O0O00OO0O0, O00000O00O0O, OO0O000OOO00, OO0000O0OOOO, OOO0OO00OOO0, O00000O0O00O, OO0000OO0000, O0O0O00O00OO, OO0OOO0000O0, OO0OOOO0OO0O, O00000000O00, O000O0OO0OOO, O0OO0OOO0OO0, OO0O0OOO000O, val_list=None):
        OO00O00OO000 = []
        O0O0O00OO0OO = val_list
        if O0O0O00O00OO == 'subset':
            if len(OO0000O0OOOO) == 0:
                OO00O00OO000 = range(OO0000OO0000)
            else:
                OO00O00OO000 = range(OO0000O0OOOO[-1] + 1, OO0000OO0000)
        elif O0O0O00O00OO == 'seq':
            if len(OO0000O0OOOO) == 0:
                OO00O00OO000 = range(OO0000OO0000 - O00000000O00 + 1)
            else:
                if OO0000O0OOOO[-1] + 1 == OO0000OO0000:
                    return
                O0OOOOO0O0O0 = OO0000O0OOOO[-1] + 1
                OO00O00OO000.append(O0OOOOO0O0O0)
        elif O0O0O00O00OO == 'lcut':
            if len(OO0000O0OOOO) == 0:
                O0OOOOO0O0O0 = 0
            else:
                if OO0000O0OOOO[-1] + 1 == OO0000OO0000:
                    return
                O0OOOOO0O0O0 = OO0000O0OOOO[-1] + 1
            OO00O00OO000.append(O0OOOOO0O0O0)
        elif O0O0O00O00OO == 'rcut':
            if len(OO0000O0OOOO) == 0:
                O0OOOOO0O0O0 = OO0000OO0000 - 1
            else:
                if OO0000O0OOOO[-1] == 0:
                    return
                O0OOOOO0O0O0 = OO0000O0OOOO[-1] - 1
                if OOO0OO00O000.verbosity['debug']:
                    print('Olditem: ' + str(OO0000O0OOOO[-1]) + ', Newitem : ' + str(O0OOOOO0O0O0))
            OO00O00OO000.append(O0OOOOO0O0O0)
        elif O0O0O00O00OO == 'one':
            if len(OO0000O0OOOO) == 0:
                O0O0O0OO0O0O = OOO0OO00O000.data['varname'].index(O0O0O00OO0O0['defi'].get('attributes')[O00000O00O0O[-1]].get('name'))
                try:
                    O0OOOOO0O0O0 = OOO0OO00O000.data['catnames'][O0O0O0OO0O0O].index(O0O0O00OO0O0['defi'].get('attributes')[O00000O00O0O[-1]].get('value'))
                except:
                    print(f"ERROR: attribute '{O0O0O00OO0O0['defi'].get('attributes')[O00000O00O0O[-1]].get('name')}' has not value '{O0O0O00OO0O0['defi'].get('attributes')[O00000O00O0O[-1]].get('value')}'")
                    exit(1)
                OO00O00OO000.append(O0OOOOO0O0O0)
                O00000000O00 = 1
                O000O0OO0OOO = 1
            else:
                print('DEBUG: one category should not have more categories')
                return
        elif O0O0O00O00OO == 'list':
            if O0O0O00OO0OO is None:
                O0O0O0OO0O0O = OOO0OO00O000.data['varname'].index(O0O0O00OO0O0['defi'].get('attributes')[O00000O00O0O[-1]].get('name'))
                OO0OOOO0OO00 = None
                OO0000OOOOOO = []
                try:
                    O0OO000OOOO0 = O0O0O00OO0O0['defi'].get('attributes')[O00000O00O0O[-1]].get('value')
                    for O00OO0OOO00O in O0OO000OOOO0:
                        OO0OOOO0OO00 = O00OO0OOO00O
                        O0OOOOO0O0O0 = OOO0OO00O000.data['catnames'][O0O0O0OO0O0O].index(O00OO0OOO00O)
                        OO0000OOOOOO.append(O0OOOOO0O0O0)
                except:
                    print(f"ERROR: attribute '{O0O0O00OO0O0['defi'].get('attributes')[O00000O00O0O[-1]].get('name')}' has not value '{O00OO0OOO00O}'")
                    exit(1)
                O0O0O00OO0OO = OO0000OOOOOO
                O00000000O00 = len(O0O0O00OO0OO)
                O000O0OO0OOO = len(O0O0O00OO0OO)
            OO00O00OO000.append(O0O0O00OO0OO[len(OO0000O0OOOO)])
        else:
            print('Attribute type ' + O0O0O00O00OO + ' not supported.')
            return
        if len(OO00O00OO000) > 0:
            O00000000000 = (OO0O0OOO000O - O0OO0OOO0OO0) / len(OO00O00OO000)
        else:
            O00000000000 = 0
        O00OO0O000OO = 0
        for OO0O000O00O0 in OO00O00OO000:
            OO0000O0OOOO.append(OO0O000O00O0)
            OO0O000OOO00.pop()
            OO0O000OOO00.append(OO0000O0OOOO)
            OOO00OOOOO0O = O00000O0O00O | OOO0OO00O000.data['dm'][OOO0OO00O000.data['varname'].index(O0O0O00OO0O0['defi'].get('attributes')[O00000O00O0O[-1]].get('name'))][OO0O000O00O0]
            OOO0OO0O0O00 = 1
            if len(O00000O00O0O) < OO0OOO0000O0:
                OOO0OO0O0O00 = -1
                if OOO0OO00O000.verbosity['debug']:
                    print('DEBUG: will not verify, low cedent length')
            if len(OO0O000OOO00[-1]) < O00000000O00:
                OOO0OO0O0O00 = 0
                if OOO0OO00O000.verbosity['debug']:
                    print('DEBUG: will not verify, low attribute length')
            OOO0OO000OOO = 0
            if O0O0O00OO0O0['defi'].get('type') == 'con':
                OOO0OO000OOO = OOO0OO00OOO0 & OOO00OOOOO0O
            else:
                OOO0OO000OOO = OOO0OO00OOO0 | OOO00OOOOO0O
            O0O0O00OO0O0['trace_cedent'] = O00000O00O0O
            O0O0O00OO0O0['traces'] = OO0O000OOO00
            OO0OOO000OO0, OO0O0000000O, OOO00OO0O000 = OOO0OO00O000._print(O0O0O00OO0O0, O00000O00O0O, OO0O000OOO00)
            O0O0O00OO0O0['generated_string'] = OO0OOO000OO0
            O0O0O00OO0O0['rule'] = OO0O0000000O
            O0O0O00OO0O0['filter_value'] = OOO0OO000OOO
            O0O0O00OO0O0['traces'] = copy.deepcopy(OO0O000OOO00)
            O0O0O00OO0O0['trace_cedent'] = copy.deepcopy(O00000O00O0O)
            O0O0O00OO0O0['trace_cedent_asindata'] = copy.deepcopy(OOO00OO0O000)
            if OOO0OO00O000.verbosity['debug']:
                print(f"TC :{O0O0O00OO0O0['trace_cedent_asindata']}")
            O00OO000O0OO['cedents'].append(O0O0O00OO0O0)
            OOOOO0O0O0OO = OOO0OO00O000._verify_opt(O00OO000O0OO, O0O0O00OO0O0)
            if OOO0OO00O000.verbosity['debug']:
                print(f"DEBUG: {O0O0O00OO0O0['generated_string']}.")
                print(f'DEBUG: {O00000O00O0O},{OO0OOO0000O0}.')
                if OOOOO0O0O0OO:
                    print('DEBUG: Optimization: cutting')
            if not OOOOO0O0O0OO:
                if OOO0OO0O0O00 == 1:
                    if OOO0OO00O000.verbosity['debug']:
                        print('DEBUG: verifying')
                    if len(O00OO000O0OO['cedents_to_do']) == len(O00OO000O0OO['cedents']):
                        if OOO0OO00O000.proc == 'CFMiner':
                            O00O00OOO0O0, O00O0O000O0O = OOO0OO00O000._verifyCF(OOO0OO000OOO)
                        elif OOO0OO00O000.proc == 'UICMiner':
                            O00O00OOO0O0, O00O0O000O0O = OOO0OO00O000._verifyUIC(OOO0OO000OOO)
                        elif OOO0OO00O000.proc == '4ftMiner':
                            O00O00OOO0O0, O00O0O000O0O = OOO0OO00O000._verify4ft(OOO00OOOOO0O, O00000O00O0O, OO0O000OOO00)
                        elif OOO0OO00O000.proc == 'SD4ftMiner':
                            O00O00OOO0O0, O00O0O000O0O = OOO0OO00O000._verifysd4ft(OOO00OOOOO0O)
                        else:
                            print('Unsupported procedure : ' + OOO0OO00O000.proc)
                            exit(0)
                        if O00O00OOO0O0 == True:
                            O0O0O0OOOO00 = {}
                            O0O0O0OOOO00['rule_id'] = OOO0OO00O000.stats['total_valid']
                            O0O0O0OOOO00['cedents_str'] = {}
                            O0O0O0OOOO00['cedents_struct'] = {}
                            O0O0O0OOOO00['traces'] = {}
                            O0O0O0OOOO00['trace_cedent_taskorder'] = {}
                            O0O0O0OOOO00['trace_cedent_dataorder'] = {}
                            for O0000O00OOOO in O00OO000O0OO['cedents']:
                                if OOO0OO00O000.verbosity['debug']:
                                    print(O0000O00OOOO)
                                O0O0O0OOOO00['cedents_str'][O0000O00OOOO['cedent_type']] = O0000O00OOOO['generated_string']
                                O0O0O0OOOO00['cedents_struct'][O0000O00OOOO['cedent_type']] = O0000O00OOOO['rule']
                                O0O0O0OOOO00['traces'][O0000O00OOOO['cedent_type']] = O0000O00OOOO['traces']
                                O0O0O0OOOO00['trace_cedent_taskorder'][O0000O00OOOO['cedent_type']] = O0000O00OOOO['trace_cedent']
                                O0O0O0OOOO00['trace_cedent_dataorder'][O0000O00OOOO['cedent_type']] = O0000O00OOOO['trace_cedent_asindata']
                            O0O0O0OOOO00['params'] = O00O0O000O0O
                            if OOO0OO00O000.verbosity['debug']:
                                O0O0O0OOOO00['trace_cedent'] = copy.deepcopy(O00000O00O0O)
                            OOO0OO00O000._print_rule(O0O0O0OOOO00)
                            OOO0OO00O000.rulelist.append(O0O0O0OOOO00)
                        OOO0OO00O000.stats['total_cnt'] += 1
                        OOO0OO00O000.stats['total_ver'] += 1
                if OOO0OO0O0O00 >= 1:
                    if len(O00OO000O0OO['cedents_to_do']) > len(O00OO000O0OO['cedents']):
                        OOO0OO00O000._start_cedent(O00OO000O0OO, O0OO0OOO0OO0 + O00OO0O000OO * O00000000000, O0OO0OOO0OO0 + (O00OO0O000OO + 0.33) * O00000000000)
                O00OO000O0OO['cedents'].pop()
                if not OOO0OO0O0O00 == 0 and len(O00000O00O0O) < OO0OOOO0OO0O:
                    OOO0OO00O000._genvar(O00OO000O0OO, O0O0O00OO0O0, O00000O00O0O, OO0O000OOO00, OOO0OO000OOO, OO0OOO0000O0, OO0OOOO0OO0O, O0OO0OOO0OO0 + (O00OO0O000OO + 0.33) * O00000000000, O0OO0OOO0OO0 + (O00OO0O000OO + 0.66) * O00000000000)
            else:
                O00OO000O0OO['cedents'].pop()
            if len(OO0000O0OOOO) < O000O0OO0OOO:
                OOO0OO00O000._gencomb(O00OO000O0OO, O0O0O00OO0O0, O00000O00O0O, OO0O000OOO00, OO0000O0OOOO, OOO0OO00OOO0, OOO00OOOOO0O, OO0000OO0000, O0O0O00O00OO, OO0OOO0000O0, OO0OOOO0OO0O, O00000000O00, O000O0OO0OOO, O0OO0OOO0OO0 + O00000000000 * (O00OO0O000OO + 0.66), O0OO0OOO0OO0 + O00000000000 * (O00OO0O000OO + 1), O0O0O00OO0OO)
            OO0000O0OOOO.pop()
            O00OO0O000OO += 1
            if OOO0OO00O000.options['progressbar']:
                OOO0OO00O000.bar.update(min(100, O0OO0OOO0OO0 + O00000000000 * O00OO0O000OO))
            if OOO0OO00O000.verbosity['debug']:
                print(f'Progress : lower: {O0OO0OOO0OO0}, step: {O00000000000}, step_no: {O00OO0O000OO} overall: {O0OO0OOO0OO0 + O00000000000 * O00OO0O000OO}')

    def _start_cedent(O0OO0OO0OOO0, OOOO0O00O00O, OOOOOO0O0000, OO00O0OO00OO):
        if len(OOOO0O00O00O['cedents_to_do']) > len(OOOO0O00O00O['cedents']):
            O0000OO000O0 = []
            O0OO0000OO0O = []
            O00OO0O00O00 = {}
            O00OO0O00O00['cedent_type'] = OOOO0O00O00O['cedents_to_do'][len(OOOO0O00O00O['cedents'])]
            O000OO0O0OOO = O00OO0O00O00['cedent_type']
            if (O000OO0O0OOO[-1] == '-') | (O000OO0O0OOO[-1] == '+'):
                O000OO0O0OOO = O000OO0O0OOO[:-1]
            O00OO0O00O00['defi'] = O0OO0OO0OOO0.kwargs.get(O000OO0O0OOO)
            if O00OO0O00O00['defi'] == None:
                print('Error getting cedent ', O00OO0O00O00['cedent_type'])
            OO00000O0OO0 = int(0)
            O00OO0O00O00['num_cedent'] = len(O00OO0O00O00['defi'].get('attributes'))
            if O00OO0O00O00['defi'].get('type') == 'con':
                OO00000O0OO0 = (1 << O0OO0OO0OOO0.data['rows_count']) - 1
            O0OO0OO0OOO0._genvar(OOOO0O00O00O, O00OO0O00O00, O0000OO000O0, O0OO0000OO0O, OO00000O0OO0, O00OO0O00O00['defi'].get('minlen'), O00OO0O00O00['defi'].get('maxlen'), OOOOOO0O0000, OO00O0OO00OO)

    def _calc_all(O000O00O000O, **OO0000OOO000):
        if 'df' in OO0000OOO000:
            O000O00O000O._prep_data(O000O00O000O.kwargs.get('df'))
        if not O000O00O000O._initialized:
            print('ERROR: dataframe is missing and not initialized with dataframe')
        else:
            O000O00O000O._calculate(**OO0000OOO000)

    def _check_cedents(O000O0OOO0OO, O0O0O000O0O0, **O0OOOO0O0O0O):
        O0OOO000OO00 = True
        if O0OOOO0O0O0O.get('quantifiers', None) == None:
            print(f'Error: missing quantifiers.')
            O0OOO000OO00 = False
            return O0OOO000OO00
        if type(O0OOOO0O0O0O.get('quantifiers')) != dict:
            print(f'Error: quantifiers are not dictionary type.')
            O0OOO000OO00 = False
            return O0OOO000OO00
        for O0000O0OOOOO in O0O0O000O0O0:
            if O0OOOO0O0O0O.get(O0000O0OOOOO, None) == None:
                print(f'Error: cedent {O0000O0OOOOO} is missing in parameters.')
                O0OOO000OO00 = False
                return O0OOO000OO00
            OOOOO0OOOOO0 = O0OOOO0O0O0O.get(O0000O0OOOOO)
            if (OOOOO0OOOOO0.get('minlen'), None) == None:
                print(f'Error: cedent {O0000O0OOOOO} has no minimal length specified.')
                O0OOO000OO00 = False
                return O0OOO000OO00
            if not type(OOOOO0OOOOO0.get('minlen')) is int:
                print(f"Error: cedent {O0000O0OOOOO} has invalid type of minimal length ({type(OOOOO0OOOOO0.get('minlen'))}).")
                O0OOO000OO00 = False
                return O0OOO000OO00
            if (OOOOO0OOOOO0.get('maxlen'), None) == None:
                print(f'Error: cedent {O0000O0OOOOO} has no maximal length specified.')
                O0OOO000OO00 = False
                return O0OOO000OO00
            if not type(OOOOO0OOOOO0.get('maxlen')) is int:
                print(f'Error: cedent {O0000O0OOOOO} has invalid type of maximal length.')
                O0OOO000OO00 = False
                return O0OOO000OO00
            if (OOOOO0OOOOO0.get('type'), None) == None:
                print(f'Error: cedent {O0000O0OOOOO} has no type specified.')
                O0OOO000OO00 = False
                return O0OOO000OO00
            if not OOOOO0OOOOO0.get('type') in ['con', 'dis']:
                print(f"Error: cedent {O0000O0OOOOO} has invalid type. Allowed values are 'con' and 'dis'.")
                O0OOO000OO00 = False
                return O0OOO000OO00
            if (OOOOO0OOOOO0.get('attributes'), None) == None:
                print(f'Error: cedent {O0000O0OOOOO} has no attributes specified.')
                O0OOO000OO00 = False
                return O0OOO000OO00
            for O000OO0OO00O in OOOOO0OOOOO0.get('attributes'):
                if (O000OO0OO00O.get('name'), None) == None:
                    print(f"Error: cedent {O0000O0OOOOO} / attribute {O000OO0OO00O} has no 'name' attribute specified.")
                    O0OOO000OO00 = False
                    return O0OOO000OO00
                if not O000OO0OO00O.get('name') in O000O0OOO0OO.data['varname']:
                    print(f"Error: cedent {O0000O0OOOOO} / attribute {O000OO0OO00O.get('name')} not in variable list. Please check spelling.")
                    O0OOO000OO00 = False
                    return O0OOO000OO00
                if (O000OO0OO00O.get('type'), None) == None:
                    print(f"Error: cedent {O0000O0OOOOO} / attribute {O000OO0OO00O.get('name')} has no 'type' attribute specified.")
                    O0OOO000OO00 = False
                    return O0OOO000OO00
                if not O000OO0OO00O.get('type') in ['rcut', 'lcut', 'seq', 'subset', 'one', 'list']:
                    print(f"Error: cedent {O0000O0OOOOO} / attribute {O000OO0OO00O.get('name')} has unsupported type {O000OO0OO00O.get('type')}. Supported types are 'subset','seq','lcut','rcut','one','list'.")
                    O0OOO000OO00 = False
                    return O0OOO000OO00
                if (O000OO0OO00O.get('minlen'), None) == None:
                    print(f"Error: cedent {O0000O0OOOOO} / attribute {O000OO0OO00O.get('name')} has no minimal length specified.")
                    O0OOO000OO00 = False
                    return O0OOO000OO00
                if not type(O000OO0OO00O.get('minlen')) is int:
                    if not (O000OO0OO00O.get('type') == 'one' or O000OO0OO00O.get('type') == 'list'):
                        print(f"Error: cedent {O0000O0OOOOO} / attribute {O000OO0OO00O.get('name')} has invalid type of minimal length.")
                        O0OOO000OO00 = False
                        return O0OOO000OO00
                if (O000OO0OO00O.get('maxlen'), None) == None:
                    print(f"Error: cedent {O0000O0OOOOO} / attribute {O000OO0OO00O.get('name')} has no maximal length specified.")
                    O0OOO000OO00 = False
                    return O0OOO000OO00
                if not type(O000OO0OO00O.get('maxlen')) is int:
                    if not (O000OO0OO00O.get('type') == 'one' or O000OO0OO00O.get('type') == 'list'):
                        print(f"Error: cedent {O0000O0OOOOO} / attribute {O000OO0OO00O.get('name')} has invalid type of maximal length.")
                        O0OOO000OO00 = False
                        return O0OOO000OO00
        return O0OOO000OO00

    def _calculate(O0OOO0O00000, **O0OOOO0000OO):
        if O0OOO0O00000.data['data_prepared'] == 0:
            print('Error: data not prepared')
            return
        O0OOO0O00000.kwargs = O0OOOO0000OO
        O0OOO0O00000.proc = O0OOOO0000OO.get('proc')
        O0OOO0O00000.quantifiers = O0OOOO0000OO.get('quantifiers')
        O0OOO0O00000._init_task()
        O0OOO0O00000.stats['start_proc_time'] = time.time()
        O0OOO0O00000.task_actinfo['cedents_to_do'] = []
        O0OOO0O00000.task_actinfo['cedents'] = []
        if O0OOOO0000OO.get('proc') == 'UICMiner':
            if not O0OOO0O00000._check_cedents(['ante'], **O0OOOO0000OO):
                return
            OOOOO0OO00O0 = O0OOOO0000OO.get('cond')
            if OOOOO0OO00O0 != None:
                O0OOO0O00000.task_actinfo['cedents_to_do'].append('cond')
            else:
                O0OOO00OOO0O = O0OOO0O00000.cedent
                O0OOO00OOO0O['cedent_type'] = 'cond'
                O0OOO00OOO0O['filter_value'] = (1 << O0OOO0O00000.data['rows_count']) - 1
                O0OOO00OOO0O['generated_string'] = '---'
                if O0OOO0O00000.verbosity['debug']:
                    print(O0OOO00OOO0O['filter_value'])
                O0OOO0O00000.task_actinfo['cedents_to_do'].append('cond')
                O0OOO0O00000.task_actinfo['cedents'].append(O0OOO00OOO0O)
            O0OOO0O00000.task_actinfo['cedents_to_do'].append('ante')
            if O0OOOO0000OO.get('target', None) == None:
                print('ERROR: no succedent/target variable defined for UIC Miner')
                return
            if not O0OOOO0000OO.get('target') in O0OOO0O00000.data['varname']:
                print("ERROR: target parameter is not variable. Please check spelling of variable name in parameter 'target'.")
                return
            if 'aad_score' in O0OOO0O00000.quantifiers:
                if not 'aad_weights' in O0OOO0O00000.quantifiers:
                    print('ERROR: for aad quantifier you need to specify aad weights.')
                    return
                if not len(O0OOO0O00000.quantifiers.get('aad_weights')) == len(O0OOO0O00000.data['dm'][O0OOO0O00000.data['varname'].index(O0OOO0O00000.kwargs.get('target'))]):
                    print('ERROR: aad weights has different number of weights than classes of target variable.')
                    return
        elif O0OOOO0000OO.get('proc') == 'CFMiner':
            O0OOO0O00000.task_actinfo['cedents_to_do'] = ['cond']
            if O0OOOO0000OO.get('target', None) == None:
                print('ERROR: no target variable defined for CF Miner')
                return
            O0000OOO0O00 = O0OOOO0000OO.get('target', None)
            O0OOO0O00000.profiles['hist_target_entire_dataset_labels'] = O0OOO0O00000.data['catnames'][O0OOO0O00000.data['varname'].index(O0OOO0O00000.kwargs.get('target'))]
            OOO0OOO00OOO = O0OOO0O00000.data['dm'][O0OOO0O00000.data['varname'].index(O0OOO0O00000.kwargs.get('target'))]
            OOO00OO00OO0 = []
            for O00000O0000O in range(len(OOO0OOO00OOO)):
                OOO00000O000 = O0OOO0O00000._bitcount(OOO0OOO00OOO[O00000O0000O])
                OOO00OO00OO0.append(OOO00000O000)
            O0OOO0O00000.profiles['hist_target_entire_dataset_values'] = OOO00OO00OO0
            if not O0OOO0O00000._check_cedents(['cond'], **O0OOOO0000OO):
                return
            if not O0OOOO0000OO.get('target') in O0OOO0O00000.data['varname']:
                print("ERROR: target parameter is not variable. Please check spelling of variable name in parameter 'target'.")
                return
            if 'aad' in O0OOO0O00000.quantifiers:
                if not 'aad_weights' in O0OOO0O00000.quantifiers:
                    print('ERROR: for aad quantifier you need to specify aad weights.')
                    return
                if not len(O0OOO0O00000.quantifiers.get('aad_weights')) == len(O0OOO0O00000.data['dm'][O0OOO0O00000.data['varname'].index(O0OOO0O00000.kwargs.get('target'))]):
                    print('ERROR: aad weights has different number of weights than classes of target variable.')
                    return
        elif O0OOOO0000OO.get('proc') == '4ftMiner':
            if not O0OOO0O00000._check_cedents(['ante', 'succ'], **O0OOOO0000OO):
                return
            OOOOO0OO00O0 = O0OOOO0000OO.get('cond')
            if OOOOO0OO00O0 != None:
                O0OOO0O00000.task_actinfo['cedents_to_do'].append('cond')
            else:
                O0OOO00OOO0O = O0OOO0O00000.cedent
                O0OOO00OOO0O['cedent_type'] = 'cond'
                O0OOO00OOO0O['filter_value'] = (1 << O0OOO0O00000.data['rows_count']) - 1
                O0OOO00OOO0O['generated_string'] = '---'
                O0OOO0O00000.task_actinfo['cedents_to_do'].append('cond')
                O0OOO0O00000.task_actinfo['cedents'].append(O0OOO00OOO0O)
            O0OOO0O00000.task_actinfo['cedents_to_do'].append('ante')
            O0OOO0O00000.task_actinfo['cedents_to_do'].append('succ')
        elif O0OOOO0000OO.get('proc') == 'SD4ftMiner':
            if not O0OOO0O00000._check_cedents(['ante', 'succ', 'frst', 'scnd'], **O0OOOO0000OO):
                return
            OOOOO0OO00O0 = O0OOOO0000OO.get('cond')
            if OOOOO0OO00O0 != None:
                O0OOO0O00000.task_actinfo['cedents_to_do'].append('cond')
            else:
                O0OOO00OOO0O = O0OOO0O00000.cedent
                O0OOO00OOO0O['cedent_type'] = 'cond'
                O0OOO00OOO0O['filter_value'] = (1 << O0OOO0O00000.data['rows_count']) - 1
                O0OOO00OOO0O['generated_string'] = '---'
                O0OOO0O00000.task_actinfo['cedents_to_do'].append('cond')
                O0OOO0O00000.task_actinfo['cedents'].append(O0OOO00OOO0O)
            O0OOO0O00000.task_actinfo['cedents_to_do'].append('frst')
            O0OOO0O00000.task_actinfo['cedents_to_do'].append('scnd')
            O0OOO0O00000.task_actinfo['cedents_to_do'].append('ante')
            O0OOO0O00000.task_actinfo['cedents_to_do'].append('succ')
        else:
            print('Unsupported procedure')
            return
        print('Will go for ', O0OOOO0000OO.get('proc'))
        O0OOO0O00000.task_actinfo['optim'] = {}
        OO0OOO00O0OO = True
        for OOOOOO0OO0O0 in O0OOO0O00000.task_actinfo['cedents_to_do']:
            try:
                O0O00OO00O0O = O0OOO0O00000.kwargs.get(OOOOOO0OO0O0)
                if O0OOO0O00000.verbosity['debug']:
                    print(O0O00OO00O0O)
                    print(f"...cedent {OOOOOO0OO0O0} is type {O0O00OO00O0O.get('type')}")
                    print(f"Will check cedent type {OOOOOO0OO0O0} : {O0O00OO00O0O.get('type')}")
                if O0O00OO00O0O.get('type') != 'con':
                    OO0OOO00O0OO = False
                    if O0OOO0O00000.verbosity['debug']:
                        print(f"Cannot optim due to cedent type {OOOOOO0OO0O0} : {O0O00OO00O0O.get('type')}")
            except:
                O0000O0OOO00 = 1 < 2
        if O0OOO0O00000.options['optimizations'] == False:
            OO0OOO00O0OO = False
        OO000OO0OOOO = {}
        OO000OO0OOOO['only_con'] = OO0OOO00O0OO
        O0OOO0O00000.task_actinfo['optim'] = OO000OO0OOOO
        if O0OOO0O00000.verbosity['debug']:
            print('Starting to prepare data.')
            O0OOO0O00000._prep_data(O0OOO0O00000.data.df)
            O0OOO0O00000.stats['mid1_time'] = time.time()
            O0OOO0O00000.quantifiers = O0OOOO0000OO.get('self.quantifiers')
        print('Starting to mine rules.')
        sys.stdout.flush()
        time.sleep(0.01)
        if O0OOO0O00000.options['progressbar']:
            O0000000OOO0 = [progressbar.Percentage(), progressbar.Bar(), progressbar.Timer()]
            O0OOO0O00000.bar = progressbar.ProgressBar(widgets=O0000000OOO0, max_value=100, fd=sys.stdout).start()
            O0OOO0O00000.bar.update(0)
        O0OOO0O00000.progress_lower = 0
        O0OOO0O00000.progress_upper = 100
        O0OOO0O00000._start_cedent(O0OOO0O00000.task_actinfo, O0OOO0O00000.progress_lower, O0OOO0O00000.progress_upper)
        if O0OOO0O00000.options['progressbar']:
            O0OOO0O00000.bar.update(100)
            O0OOO0O00000.bar.finish()
        O0OOO0O00000.stats['end_proc_time'] = time.time()
        print('Done. Total verifications : ' + str(O0OOO0O00000.stats['total_cnt']) + ', rules ' + str(O0OOO0O00000.stats['total_valid']) + ', times: prep ' + '{:.2f}'.format(O0OOO0O00000.stats['end_prep_time'] - O0OOO0O00000.stats['start_prep_time']) + 'sec, processing ' + '{:.2f}'.format(O0OOO0O00000.stats['end_proc_time'] - O0OOO0O00000.stats['start_proc_time']) + 'sec')
        OOO00OO0O00O = {}
        O0OO0OOO0000 = {}
        O0OO0OOO0000['guid'] = O0OOO0O00000.guid
        O0OO0OOO0000['task_type'] = O0OOOO0000OO.get('proc')
        O0OO0OOO0000['target'] = O0OOOO0000OO.get('target')
        O0OO0OOO0000['self.quantifiers'] = O0OOO0O00000.quantifiers
        if O0OOOO0000OO.get('cond') != None:
            O0OO0OOO0000['cond'] = O0OOOO0000OO.get('cond')
        if O0OOOO0000OO.get('ante') != None:
            O0OO0OOO0000['ante'] = O0OOOO0000OO.get('ante')
        if O0OOOO0000OO.get('succ') != None:
            O0OO0OOO0000['succ'] = O0OOOO0000OO.get('succ')
        if O0OOOO0000OO.get('opts') != None:
            O0OO0OOO0000['opts'] = O0OOOO0000OO.get('opts')
        if O0OOO0O00000.df is None:
            O0OO0OOO0000['rowcount'] = O0OOO0O00000.data['rows_count']
        else:
            O0OO0OOO0000['rowcount'] = len(O0OOO0O00000.df.index)
        OOO00OO0O00O['taskinfo'] = O0OO0OOO0000
        OOO0OO0O00OO = {}
        OOO0OO0O00OO['total_verifications'] = O0OOO0O00000.stats['total_cnt']
        OOO0OO0O00OO['valid_rules'] = O0OOO0O00000.stats['total_valid']
        OOO0OO0O00OO['total_verifications_with_opt'] = O0OOO0O00000.stats['total_ver']
        OOO0OO0O00OO['time_prep'] = O0OOO0O00000.stats['end_prep_time'] - O0OOO0O00000.stats['start_prep_time']
        OOO0OO0O00OO['time_processing'] = O0OOO0O00000.stats['end_proc_time'] - O0OOO0O00000.stats['start_proc_time']
        OOO0OO0O00OO['time_total'] = O0OOO0O00000.stats['end_prep_time'] - O0OOO0O00000.stats['start_prep_time'] + O0OOO0O00000.stats['end_proc_time'] - O0OOO0O00000.stats['start_proc_time']
        OOO00OO0O00O['summary_statistics'] = OOO0OO0O00OO
        OOO00OO0O00O['rules'] = O0OOO0O00000.rulelist
        O0OO000000O0 = {}
        O0OO000000O0['varname'] = O0OOO0O00000.data['varname']
        O0OO000000O0['catnames'] = O0OOO0O00000.data['catnames']
        OOO00OO0O00O['datalabels'] = O0OO000000O0
        O0OOO0O00000.result = OOO00OO0O00O

    def print_summary(O00000O0OO0O):
        if not O00000O0OO0O._is_calculated():
            print('ERROR: Task has not been calculated.')
            return
        print('')
        print('CleverMiner task processing summary:')
        print('')
        print(f"Task type : {O00000O0OO0O.result['taskinfo']['task_type']}")
        print(f"Number of verifications : {O00000O0OO0O.result['summary_statistics']['total_verifications']}")
        print(f"Number of rules : {O00000O0OO0O.result['summary_statistics']['valid_rules']}")
        print(f"Total time needed : {strftime('%Hh %Mm %Ss', gmtime(O00000O0OO0O.result['summary_statistics']['time_total']))}")
        if O00000O0OO0O.verbosity['debug']:
            print(f"Total time needed : {O00000O0OO0O.result['summary_statistics']['time_total']}")
        print(f"Time of data preparation : {strftime('%Hh %Mm %Ss', gmtime(O00000O0OO0O.result['summary_statistics']['time_prep']))}")
        print(f"Time of rule mining : {strftime('%Hh %Mm %Ss', gmtime(O00000O0OO0O.result['summary_statistics']['time_processing']))}")
        print('')

    def print_hypolist(O0OO0O000O00):
        O0OO0O000O00.print_rulelist()

    def print_rulelist(O000OOOO0OOO, sortby=None, storesorted=False):
        if not O000OOOO0OOO._is_calculated():
            print('ERROR: Task has not been calculated.')
            return

        def OO00O0OO0OO0(O0OOO0OO000O):
            O0OOOO0OO000 = O0OOO0OO000O['params']
            return O0OOOO0OO000.get(sortby, 0)
        print('')
        print('List of rules:')
        if O000OOOO0OOO.result['taskinfo']['task_type'] == '4ftMiner':
            print('RULEID BASE  CONF  AAD    Rule')
        elif O000OOOO0OOO.result['taskinfo']['task_type'] == 'UICMiner':
            print('RULEID BASE  AAD_SCORE  Rule')
        elif O000OOOO0OOO.result['taskinfo']['task_type'] == 'CFMiner':
            print('RULEID BASE  S_UP  S_DOWN Condition')
        elif O000OOOO0OOO.result['taskinfo']['task_type'] == 'SD4ftMiner':
            print('RULEID BASE1 BASE2 RatioConf DeltaConf Rule')
        else:
            print('Unsupported task type for rulelist')
            return
        OOO0OO0OO0OO = O000OOOO0OOO.result['rules']
        if sortby is not None:
            OOO0OO0OO0OO = sorted(OOO0OO0OO0OO, key=OO00O0OO0OO0, reverse=True)
            if storesorted:
                O000OOOO0OOO.result['rules'] = OOO0OO0OO0OO
        for O00O00O0O0O0 in OOO0OO0OO0OO:
            OO00OOOO0O0O = '{:6d}'.format(O00O00O0O0O0['rule_id'])
            if O000OOOO0OOO.result['taskinfo']['task_type'] == '4ftMiner':
                if O000OOOO0OOO.verbosity['debug']:
                    print(f"{O00O00O0O0O0['params']}")
                OO00OOOO0O0O = OO00OOOO0O0O + ' ' + '{:5d}'.format(O00O00O0O0O0['params']['base']) + ' ' + '{:.3f}'.format(O00O00O0O0O0['params']['conf']) + ' ' + '{:+.3f}'.format(O00O00O0O0O0['params']['aad'])
                OO00OOOO0O0O = OO00OOOO0O0O + ' ' + O00O00O0O0O0['cedents_str']['ante'] + ' => ' + O00O00O0O0O0['cedents_str']['succ'] + ' | ' + O00O00O0O0O0['cedents_str']['cond']
            elif O000OOOO0OOO.result['taskinfo']['task_type'] == 'UICMiner':
                OO00OOOO0O0O = OO00OOOO0O0O + ' ' + '{:5d}'.format(O00O00O0O0O0['params']['base']) + ' ' + '{:.3f}'.format(O00O00O0O0O0['params']['aad_score'])
                OO00OOOO0O0O = OO00OOOO0O0O + '     ' + O00O00O0O0O0['cedents_str']['ante'] + ' => ' + O000OOOO0OOO.result['taskinfo']['target'] + '(*) | ' + O00O00O0O0O0['cedents_str']['cond']
            elif O000OOOO0OOO.result['taskinfo']['task_type'] == 'CFMiner':
                OO00OOOO0O0O = OO00OOOO0O0O + ' ' + '{:5d}'.format(O00O00O0O0O0['params']['base']) + ' ' + '{:5d}'.format(O00O00O0O0O0['params']['s_up']) + ' ' + '{:5d}'.format(O00O00O0O0O0['params']['s_down'])
                OO00OOOO0O0O = OO00OOOO0O0O + ' ' + O00O00O0O0O0['cedents_str']['cond']
            elif O000OOOO0OOO.result['taskinfo']['task_type'] == 'SD4ftMiner':
                OO00OOOO0O0O = OO00OOOO0O0O + ' ' + '{:5d}'.format(O00O00O0O0O0['params']['base1']) + ' ' + '{:5d}'.format(O00O00O0O0O0['params']['base2']) + '    ' + '{:.3f}'.format(O00O00O0O0O0['params']['ratioconf']) + '    ' + '{:+.3f}'.format(O00O00O0O0O0['params']['deltaconf'])
                OO00OOOO0O0O = OO00OOOO0O0O + '  ' + O00O00O0O0O0['cedents_str']['ante'] + ' => ' + O00O00O0O0O0['cedents_str']['succ'] + ' | ' + O00O00O0O0O0['cedents_str']['cond'] + ' : ' + O00O00O0O0O0['cedents_str']['frst'] + ' x ' + O00O00O0O0O0['cedents_str']['scnd']
            print(OO00OOOO0O0O)
        print('')

    def print_hypo(O00O00O0OO00, OO000OOOOOOO):
        O00O00O0OO00.print_rule(OO000OOOOOOO)

    def print_rule(OO000O0OOOO0, OOOOOOOOO00O):
        if not OO000O0OOOO0._is_calculated():
            print('ERROR: Task has not been calculated.')
            return
        print('')
        if OOOOOOOOO00O <= len(OO000O0OOOO0.result['rules']):
            if OO000O0OOOO0.result['taskinfo']['task_type'] == '4ftMiner':
                print('')
                OOOO0O000000 = OO000O0OOOO0.result['rules'][OOOOOOOOO00O - 1]
                print(f"Rule id : {OOOO0O000000['rule_id']}")
                print('')
                print(f"Base : {'{:5d}'.format(OOOO0O000000['params']['base'])}  Relative base : {'{:.3f}'.format(OOOO0O000000['params']['rel_base'])}  CONF : {'{:.3f}'.format(OOOO0O000000['params']['conf'])}  AAD : {'{:+.3f}'.format(OOOO0O000000['params']['aad'])}  BAD : {'{:+.3f}'.format(OOOO0O000000['params']['bad'])}")
                print('')
                print('Cedents:')
                print(f"  antecedent : {OOOO0O000000['cedents_str']['ante']}")
                print(f"  succcedent : {OOOO0O000000['cedents_str']['succ']}")
                print(f"  condition  : {OOOO0O000000['cedents_str']['cond']}")
                print('')
                print('Fourfold table')
                print(f'    |  S  |  ¬S |')
                print(f'----|-----|-----|')
                print(f" A  |{'{:5d}'.format(OOOO0O000000['params']['fourfold'][0])}|{'{:5d}'.format(OOOO0O000000['params']['fourfold'][1])}|")
                print(f'----|-----|-----|')
                print(f"¬A  |{'{:5d}'.format(OOOO0O000000['params']['fourfold'][2])}|{'{:5d}'.format(OOOO0O000000['params']['fourfold'][3])}|")
                print(f'----|-----|-----|')
            elif OO000O0OOOO0.result['taskinfo']['task_type'] == 'CFMiner':
                print('')
                OOOO0O000000 = OO000O0OOOO0.result['rules'][OOOOOOOOO00O - 1]
                print(f"Rule id : {OOOO0O000000['rule_id']}")
                print('')
                OO0OOOO000OO = ''
                if 'aad' in OOOO0O000000['params']:
                    OO0OOOO000OO = 'aad : ' + str(OOOO0O000000['params']['aad'])
                print(f"Base : {'{:5d}'.format(OOOO0O000000['params']['base'])}  Relative base : {'{:.3f}'.format(OOOO0O000000['params']['rel_base'])}  Steps UP (consecutive) : {'{:5d}'.format(OOOO0O000000['params']['s_up'])}  Steps DOWN (consecutive) : {'{:5d}'.format(OOOO0O000000['params']['s_down'])}  Steps UP (any) : {'{:5d}'.format(OOOO0O000000['params']['s_any_up'])}  Steps DOWN (any) : {'{:5d}'.format(OOOO0O000000['params']['s_any_down'])}  Histogram maximum : {'{:5d}'.format(OOOO0O000000['params']['max'])}  Histogram minimum : {'{:5d}'.format(OOOO0O000000['params']['min'])}  Histogram relative maximum : {'{:.3f}'.format(OOOO0O000000['params']['rel_max'])} Histogram relative minimum : {'{:.3f}'.format(OOOO0O000000['params']['rel_min'])} {OO0OOOO000OO}")
                print('')
                print(f"Condition  : {OOOO0O000000['cedents_str']['cond']}")
                print('')
                O0O00O0O00O0 = OO000O0OOOO0.get_category_names(OO000O0OOOO0.result['taskinfo']['target'])
                print(f'Categories in target variable  {O0O00O0O00O0}')
                print(f"Histogram                      {OOOO0O000000['params']['hist']}")
                if 'aad' in OOOO0O000000['params']:
                    print(f"Histogram on full set          {OOOO0O000000['params']['hist_full']}")
                    print(f"Relative histogram             {OOOO0O000000['params']['rel_hist']}")
                    print(f"Relative histogram on full set {OOOO0O000000['params']['rel_hist_full']}")
            elif OO000O0OOOO0.result['taskinfo']['task_type'] == 'UICMiner':
                print('')
                OOOO0O000000 = OO000O0OOOO0.result['rules'][OOOOOOOOO00O - 1]
                print(f"Rule id : {OOOO0O000000['rule_id']}")
                print('')
                OO0OOOO000OO = ''
                if 'aad_score' in OOOO0O000000['params']:
                    OO0OOOO000OO = 'aad score : ' + str(OOOO0O000000['params']['aad_score'])
                print(f"Base : {'{:5d}'.format(OOOO0O000000['params']['base'])}  Relative base : {'{:.3f}'.format(OOOO0O000000['params']['rel_base'])}   {OO0OOOO000OO}")
                print('')
                print(f"Condition  : {OOOO0O000000['cedents_str']['cond']}")
                print(f"Antecedent : {OOOO0O000000['cedents_str']['ante']}")
                print('')
                print(f"Histogram                                        {OOOO0O000000['params']['hist']}")
                if 'aad_score' in OOOO0O000000['params']:
                    print(f"Histogram on full set with condition             {OOOO0O000000['params']['hist_cond']}")
                    print(f"Relative histogram                               {OOOO0O000000['params']['rel_hist']}")
                    print(f"Relative histogram on full set with condition    {OOOO0O000000['params']['rel_hist_cond']}")
                O000O0OOOO0O = OO000O0OOOO0.result['datalabels']['catnames'][OO000O0OOOO0.result['datalabels']['varname'].index(OO000O0OOOO0.result['taskinfo']['target'])]
                print(' ')
                print('Interpretation:')
                for O0O0000O0O00 in range(len(O000O0OOOO0O)):
                    OOOO00000OOO = 0
                    if OOOO0O000000['params']['rel_hist'][O0O0000O0O00] > 0:
                        OOOO00000OOO = OOOO0O000000['params']['rel_hist'][O0O0000O0O00] / OOOO0O000000['params']['rel_hist_cond'][O0O0000O0O00]
                    OOOO00000OO0 = ''
                    if not OOOO0O000000['cedents_str']['cond'] == '---':
                        OOOO00000OO0 = 'For ' + OOOO0O000000['cedents_str']['cond'] + ': '
                    print(f"    {OOOO00000OO0}{OO000O0OOOO0.result['taskinfo']['target']}({O000O0OOOO0O[O0O0000O0O00]}) has occurence {'{:.1%}'.format(OOOO0O000000['params']['rel_hist_cond'][O0O0000O0O00])}, with antecedent it has occurence {'{:.1%}'.format(OOOO0O000000['params']['rel_hist'][O0O0000O0O00])}, that is {'{:.3f}'.format(OOOO00000OOO)} times more.")
            elif OO000O0OOOO0.result['taskinfo']['task_type'] == 'SD4ftMiner':
                print('')
                OOOO0O000000 = OO000O0OOOO0.result['rules'][OOOOOOOOO00O - 1]
                print(f"Rule id : {OOOO0O000000['rule_id']}")
                print('')
                print(f"Base1 : {'{:5d}'.format(OOOO0O000000['params']['base1'])} Base2 : {'{:5d}'.format(OOOO0O000000['params']['base2'])}  Relative base 1 : {'{:.3f}'.format(OOOO0O000000['params']['rel_base1'])} Relative base 2 : {'{:.3f}'.format(OOOO0O000000['params']['rel_base2'])} CONF1 : {'{:.3f}'.format(OOOO0O000000['params']['conf1'])}  CONF2 : {'{:+.3f}'.format(OOOO0O000000['params']['conf2'])}  Delta Conf : {'{:+.3f}'.format(OOOO0O000000['params']['deltaconf'])} Ratio Conf : {'{:+.3f}'.format(OOOO0O000000['params']['ratioconf'])}")
                print('')
                print('Cedents:')
                print(f"  antecedent : {OOOO0O000000['cedents_str']['ante']}")
                print(f"  succcedent : {OOOO0O000000['cedents_str']['succ']}")
                print(f"  condition  : {OOOO0O000000['cedents_str']['cond']}")
                print(f"  first set  : {OOOO0O000000['cedents_str']['frst']}")
                print(f"  second set : {OOOO0O000000['cedents_str']['scnd']}")
                print('')
                print('Fourfold tables:')
                print(f'FRST|  S  |  ¬S |  SCND|  S  |  ¬S |')
                print(f'----|-----|-----|  ----|-----|-----| ')
                print(f" A  |{'{:5d}'.format(OOOO0O000000['params']['fourfold1'][0])}|{'{:5d}'.format(OOOO0O000000['params']['fourfold1'][1])}|   A  |{'{:5d}'.format(OOOO0O000000['params']['fourfold2'][0])}|{'{:5d}'.format(OOOO0O000000['params']['fourfold2'][1])}|")
                print(f'----|-----|-----|  ----|-----|-----|')
                print(f"¬A  |{'{:5d}'.format(OOOO0O000000['params']['fourfold1'][2])}|{'{:5d}'.format(OOOO0O000000['params']['fourfold1'][3])}|  ¬A  |{'{:5d}'.format(OOOO0O000000['params']['fourfold2'][2])}|{'{:5d}'.format(OOOO0O000000['params']['fourfold2'][3])}|")
                print(f'----|-----|-----|  ----|-----|-----|')
            else:
                print('Unsupported task type for rule details')
            print('')
        else:
            print('No such rule.')

    def get_ruletext(O0OO0O00000O, OO0OO0O0O000):
        if not O0OO0O00000O._is_calculated():
            print('ERROR: Task has not been calculated.')
            return
        if OO0OO0O0O000 <= 0 or OO0OO0O0O000 > O0OO0O00000O.get_rulecount():
            if O0OO0O00000O.get_rulecount() == 0:
                print('No such rule. There are no rules in result.')
            else:
                print(f'No such rule ({OO0OO0O0O000}). Available rules are 1 to {O0OO0O00000O.get_rulecount()}')
            return None
        O0OOOOO0O0OO = ''
        OOO00OOOO0O0 = O0OO0O00000O.result['rules'][OO0OO0O0O000 - 1]
        if O0OO0O00000O.result['taskinfo']['task_type'] == '4ftMiner':
            O0OOOOO0O0OO = O0OOOOO0O0OO + ' ' + OOO00OOOO0O0['cedents_str']['ante'] + ' => ' + OOO00OOOO0O0['cedents_str']['succ'] + ' | ' + OOO00OOOO0O0['cedents_str']['cond']
        elif O0OO0O00000O.result['taskinfo']['task_type'] == 'UICMiner':
            O0OOOOO0O0OO = O0OOOOO0O0OO + '     ' + OOO00OOOO0O0['cedents_str']['ante'] + ' => ' + O0OO0O00000O.result['taskinfo']['target'] + '(*) | ' + OOO00OOOO0O0['cedents_str']['cond']
        elif O0OO0O00000O.result['taskinfo']['task_type'] == 'CFMiner':
            O0OOOOO0O0OO = O0OOOOO0O0OO + ' ' + OOO00OOOO0O0['cedents_str']['cond']
        elif O0OO0O00000O.result['taskinfo']['task_type'] == 'SD4ftMiner':
            O0OOOOO0O0OO = O0OOOOO0O0OO + '  ' + OOO00OOOO0O0['cedents_str']['ante'] + ' => ' + OOO00OOOO0O0['cedents_str']['succ'] + ' | ' + OOO00OOOO0O0['cedents_str']['cond'] + ' : ' + OOO00OOOO0O0['cedents_str']['frst'] + ' x ' + OOO00OOOO0O0['cedents_str']['scnd']
        return O0OOOOO0O0OO

    def _annotate_chart(O0OOO0000O0O, OO0OOOOOOO00, O000O000OOOO, cnt=2):
        OO00O0O0OOO0 = OO0OOOOOOO00.axes.get_ylim()
        for OO0OO000O00O in OO0OOOOOOO00.patches:
            OOOO000O0000 = '{:.1f}%'.format(100 * OO0OO000O00O.get_height() / O000O000OOOO)
            O000OOOO00OO = OO0OO000O00O.get_x() + OO0OO000O00O.get_width() / 4
            OO0OO0O000O0 = OO0OO000O00O.get_y() + OO0OO000O00O.get_height() - OO00O0O0OOO0[1] / 8
            if OO0OO000O00O.get_height() < OO00O0O0OOO0[1] / 8:
                OO0OO0O000O0 = OO0OO000O00O.get_y() + OO0OO000O00O.get_height() + OO00O0O0OOO0[1] * 0.02
            OO0OOOOOOO00.annotate(OOOO000O0000, (O000OOOO00OO, OO0OO0O000O0), size=23 / cnt)

    def draw_rule(OO0O0O00OO0O, OO00OOO00O00, show=True, filename=None):
        if not OO0O0O00OO0O._is_calculated():
            print('ERROR: Task has not been calculated.')
            return
        print('')
        if OO00OOO00O00 <= len(OO0O0O00OO0O.result['rules']):
            if OO0O0O00OO0O.result['taskinfo']['task_type'] == '4ftMiner':
                O00O000O0OOO, OO0O0O0O0OO0 = plt.subplots(2, 2)
                OOO0OO0O000O = ['S', 'not S']
                O0OO0OOOO000 = ['A', 'not A']
                OO00OOOOO0OO = OO0O0O00OO0O.get_fourfold(OO00OOO00O00)
                OOOOOO00O0O0 = [OO00OOOOO0OO[0], OO00OOOOO0OO[1]]
                OOO0000O0O0O = [OO00OOOOO0OO[2], OO00OOOOO0OO[3]]
                OOO0OO00OO00 = [OO00OOOOO0OO[0] + OO00OOOOO0OO[2], OO00OOOOO0OO[1] + OO00OOOOO0OO[3]]
                OO0O0O0O0OO0[0, 0] = sns.barplot(ax=OO0O0O0O0OO0[0, 0], x=OOO0OO0O000O, y=OOOOOO00O0O0, color='lightsteelblue')
                OO0O0O00OO0O._annotate_chart(OO0O0O0O0OO0[0, 0], OO00OOOOO0OO[0] + OO00OOOOO0OO[1])
                OO0O0O0O0OO0[0, 1] = sns.barplot(ax=OO0O0O0O0OO0[0, 1], x=OOO0OO0O000O, y=OOO0OO00OO00, color='gray', edgecolor='black')
                OO0O0O00OO0O._annotate_chart(OO0O0O0O0OO0[0, 1], sum(OO00OOOOO0OO))
                OO0O0O0O0OO0[0, 0].set(xlabel=None, ylabel='Count')
                OO0O0O0O0OO0[0, 1].set(xlabel=None, ylabel='Count')
                O000O00OOOOO = sns.color_palette('Blues', as_cmap=True)
                O000OOOOOOO0 = sns.color_palette('Greys', as_cmap=True)
                OO0O0O0O0OO0[1, 0] = sns.heatmap(ax=OO0O0O0O0OO0[1, 0], data=[OOOOOO00O0O0, OOO0000O0O0O], xticklabels=OOO0OO0O000O, yticklabels=O0OO0OOOO000, annot=True, cbar=False, fmt='.0f', cmap=O000O00OOOOO)
                OO0O0O0O0OO0[1, 0].set(xlabel=None, ylabel='Count')
                OO0O0O0O0OO0[1, 1] = sns.heatmap(ax=OO0O0O0O0OO0[1, 1], data=np.asarray([OOO0OO00OO00]), xticklabels=OOO0OO0O000O, yticklabels=False, annot=True, cbar=False, fmt='.0f', cmap=O000OOOOOOO0)
                OO0O0O0O0OO0[1, 1].set(xlabel=None, ylabel='Count')
                OOOO000OO00O = OO0O0O00OO0O.result['rules'][OO00OOO00O00 - 1]['cedents_str']['ante']
                OO0O0O0O0OO0[0, 0].set(title='\n'.join(wrap(OOOO000OO00O, 30)))
                OO0O0O0O0OO0[0, 1].set(title='Entire dataset')
                O0O0OOO00000 = OO0O0O00OO0O.result['rules'][OO00OOO00O00 - 1]['cedents_str']
                O00O000O0OOO.suptitle('Antecedent : ' + O0O0OOO00000['ante'] + '\nSuccedent : ' + O0O0OOO00000['succ'] + '\nCondition : ' + O0O0OOO00000['cond'], x=0, ha='left', size='small')
                O00O000O0OOO.tight_layout()
            elif OO0O0O00OO0O.result['taskinfo']['task_type'] == 'SD4ftMiner':
                O00O000O0OOO, OO0O0O0O0OO0 = plt.subplots(2, 2)
                OOO0OO0O000O = ['S', 'not S']
                O0OO0OOOO000 = ['A', 'not A']
                O000000000OO = OO0O0O00OO0O.get_fourfold(OO00OOO00O00, order=1)
                OO00OOOO00O0 = OO0O0O00OO0O.get_fourfold(OO00OOO00O00, order=2)
                OO0OOO0OOO0O = [O000000000OO[0], O000000000OO[1]]
                O0OOO0OO0O00 = [O000000000OO[2], O000000000OO[3]]
                OOOO00O00OOO = [O000000000OO[0] + O000000000OO[2], O000000000OO[1] + O000000000OO[3]]
                OOOOO0O00OO0 = [OO00OOOO00O0[0], OO00OOOO00O0[1]]
                OOO00OO0000O = [OO00OOOO00O0[2], OO00OOOO00O0[3]]
                OO0O0O00O000 = [OO00OOOO00O0[0] + OO00OOOO00O0[2], OO00OOOO00O0[1] + OO00OOOO00O0[3]]
                OO0O0O0O0OO0[0, 0] = sns.barplot(ax=OO0O0O0O0OO0[0, 0], x=OOO0OO0O000O, y=OO0OOO0OOO0O, color='orange')
                OO0O0O00OO0O._annotate_chart(OO0O0O0O0OO0[0, 0], O000000000OO[0] + O000000000OO[1])
                OO0O0O0O0OO0[0, 1] = sns.barplot(ax=OO0O0O0O0OO0[0, 1], x=OOO0OO0O000O, y=OOOOO0O00OO0, color='green')
                OO0O0O00OO0O._annotate_chart(OO0O0O0O0OO0[0, 1], OO00OOOO00O0[0] + OO00OOOO00O0[1])
                OO0O0O0O0OO0[0, 0].set(xlabel=None, ylabel='Count')
                OO0O0O0O0OO0[0, 1].set(xlabel=None, ylabel='Count')
                O000O00OOOOO = sns.color_palette('Oranges', as_cmap=True)
                O000OOOOOOO0 = sns.color_palette('Greens', as_cmap=True)
                OO0O0O0O0OO0[1, 0] = sns.heatmap(ax=OO0O0O0O0OO0[1, 0], data=[OO0OOO0OOO0O, O0OOO0OO0O00], xticklabels=OOO0OO0O000O, yticklabels=O0OO0OOOO000, annot=True, cbar=False, fmt='.0f', cmap=O000O00OOOOO)
                OO0O0O0O0OO0[1, 0].set(xlabel=None, ylabel='Count')
                OO0O0O0O0OO0[1, 1] = sns.heatmap(ax=OO0O0O0O0OO0[1, 1], data=[OOOOO0O00OO0, OOO00OO0000O], xticklabels=OOO0OO0O000O, yticklabels=False, annot=True, cbar=False, fmt='.0f', cmap=O000OOOOOOO0)
                OO0O0O0O0OO0[1, 1].set(xlabel=None, ylabel='Count')
                OOOO000OO00O = OO0O0O00OO0O.result['rules'][OO00OOO00O00 - 1]['cedents_str']['frst']
                OO0O0O0O0OO0[0, 0].set(title='\n'.join(wrap(OOOO000OO00O, 30)))
                O0O00000O0OO = OO0O0O00OO0O.result['rules'][OO00OOO00O00 - 1]['cedents_str']['scnd']
                OO0O0O0O0OO0[0, 1].set(title='\n'.join(wrap(O0O00000O0OO, 30)))
                O0O0OOO00000 = OO0O0O00OO0O.result['rules'][OO00OOO00O00 - 1]['cedents_str']
                O00O000O0OOO.suptitle('Antecedent : ' + O0O0OOO00000['ante'] + '\nSuccedent : ' + O0O0OOO00000['succ'] + '\nCondition : ' + O0O0OOO00000['cond'] + '\nFirst : ' + O0O0OOO00000['frst'] + '\nSecond : ' + O0O0OOO00000['scnd'], x=0, ha='left', size='small')
                O00O000O0OOO.tight_layout()
            elif OO0O0O00OO0O.result['taskinfo']['task_type'] == 'CFMiner' or OO0O0O00OO0O.result['taskinfo']['task_type'] == 'UICMiner':
                OO0O000OO0O0 = OO0O0O00OO0O.result['taskinfo']['task_type'] == 'UICMiner'
                O00O000O0OOO, OO0O0O0O0OO0 = plt.subplots(2, 2, gridspec_kw={'height_ratios': [3, 1]})
                OO00O0O00O0O = OO0O0O00OO0O.result['taskinfo']['target']
                OOO0OO0O000O = OO0O0O00OO0O.result['datalabels']['catnames'][OO0O0O00OO0O.result['datalabels']['varname'].index(OO0O0O00OO0O.result['taskinfo']['target'])]
                O0OOO00OOO00 = OO0O0O00OO0O.result['rules'][OO00OOO00O00 - 1]
                OO00O0O0OOOO = OO0O0O00OO0O.get_hist(OO00OOO00O00)
                if OO0O000OO0O0:
                    OO00O0O0OOOO = O0OOO00OOO00['params']['hist']
                else:
                    OO00O0O0OOOO = OO0O0O00OO0O.get_hist(OO00OOO00O00)
                OO0O0O0O0OO0[0, 0] = sns.barplot(ax=OO0O0O0O0OO0[0, 0], x=OOO0OO0O000O, y=OO00O0O0OOOO, color='lightsteelblue')
                O00O0O00OOO0 = []
                OO00O0O0O00O = []
                if OO0O000OO0O0:
                    O00O0O00OOO0 = OOO0OO0O000O
                    OO00O0O0O00O = OO0O0O00OO0O.get_hist(OO00OOO00O00, fullCond=True)
                else:
                    O00O0O00OOO0 = OO0O0O00OO0O.profiles['hist_target_entire_dataset_labels']
                    OO00O0O0O00O = OO0O0O00OO0O.profiles['hist_target_entire_dataset_values']
                OO0O0O0O0OO0[0, 1] = sns.barplot(ax=OO0O0O0O0OO0[0, 1], x=O00O0O00OOO0, y=OO00O0O0O00O, color='gray', edgecolor='black')
                OO0O0O00OO0O._annotate_chart(OO0O0O0O0OO0[0, 0], sum(OO00O0O0OOOO), len(OO00O0O0OOOO))
                OO0O0O00OO0O._annotate_chart(OO0O0O0O0OO0[0, 1], sum(OO00O0O0O00O), len(OO00O0O0O00O))
                OO0O0O0O0OO0[0, 0].set(xlabel=None, ylabel='Count')
                OO0O0O0O0OO0[0, 1].set(xlabel=None, ylabel='Count')
                O0O0O0OO0000 = [OOO0OO0O000O, OO00O0O0OOOO]
                O0OO000O00OO = pd.DataFrame(O0O0O0OO0000).transpose()
                O0OO000O00OO.columns = [OO00O0O00O0O, 'No of observatios']
                O000O00OOOOO = sns.color_palette('Blues', as_cmap=True)
                O000OOOOOOO0 = sns.color_palette('Greys', as_cmap=True)
                OO0O0O0O0OO0[1, 0] = sns.heatmap(ax=OO0O0O0O0OO0[1, 0], data=np.asarray([OO00O0O0OOOO]), xticklabels=OOO0OO0O000O, yticklabels=False, annot=True, cbar=False, fmt='.0f', cmap=O000O00OOOOO)
                OO0O0O0O0OO0[1, 0].set(xlabel=OO00O0O00O0O, ylabel='Count')
                OO0O0O0O0OO0[1, 1] = sns.heatmap(ax=OO0O0O0O0OO0[1, 1], data=np.asarray([OO00O0O0O00O]), xticklabels=O00O0O00OOO0, yticklabels=False, annot=True, cbar=False, fmt='.0f', cmap=O000OOOOOOO0)
                OO0O0O0O0OO0[1, 1].set(xlabel=OO00O0O00O0O, ylabel='Count')
                O0000O0000O0 = ''
                O0O00OO0OO0O = 'Entire dataset'
                if OO0O000OO0O0:
                    if len(O0OOO00OOO00['cedents_struct']['cond']) > 0:
                        O0O00OO0OO0O = O0OOO00OOO00['cedents_str']['cond']
                        O0000O0000O0 = ' & ' + O0OOO00OOO00['cedents_str']['cond']
                OO0O0O0O0OO0[0, 1].set(title=O0O00OO0OO0O)
                if OO0O000OO0O0:
                    OOOO000OO00O = OO0O0O00OO0O.result['rules'][OO00OOO00O00 - 1]['cedents_str']['ante'] + O0000O0000O0
                else:
                    OOOO000OO00O = OO0O0O00OO0O.result['rules'][OO00OOO00O00 - 1]['cedents_str']['cond']
                OO0O0O0O0OO0[0, 0].set(title='\n'.join(wrap(OOOO000OO00O, 30)))
                O0O0OOO00000 = OO0O0O00OO0O.result['rules'][OO00OOO00O00 - 1]['cedents_str']
                O0O00OO0OO0O = 'Condition : ' + O0O0OOO00000['cond']
                if OO0O000OO0O0:
                    O0O00OO0OO0O = O0O00OO0OO0O + '\nAntecedent : ' + O0O0OOO00000['ante']
                O00O000O0OOO.suptitle(O0O00OO0OO0O, x=0, ha='left', size='small')
                O00O000O0OOO.tight_layout()
            else:
                print('Unsupported task type for rule details')
                return
            if filename is not None:
                plt.savefig(filename=filename)
            if show:
                plt.show()
            print('')
        else:
            print('No such rule.')

    def get_rulecount(OOO0O0000O00):
        if not OOO0O0000O00._is_calculated():
            print('ERROR: Task has not been calculated.')
            return
        return len(OOO0O0000O00.result['rules'])

    def get_fourfold(O00O00OO0OOO, OO0OOOOO0OO0, order=0):
        if not O00O00OO0OOO._is_calculated():
            print('ERROR: Task has not been calculated.')
            return
        if OO0OOOOO0OO0 <= len(O00O00OO0OOO.result['rules']):
            if O00O00OO0OOO.result['taskinfo']['task_type'] == '4ftMiner':
                O00OOOOO000O = O00O00OO0OOO.result['rules'][OO0OOOOO0OO0 - 1]
                return O00OOOOO000O['params']['fourfold']
            elif O00O00OO0OOO.result['taskinfo']['task_type'] == 'CFMiner':
                print('Error: fourfold for CFMiner is not defined')
                return None
            elif O00O00OO0OOO.result['taskinfo']['task_type'] == 'SD4ftMiner':
                O00OOOOO000O = O00O00OO0OOO.result['rules'][OO0OOOOO0OO0 - 1]
                if order == 1:
                    return O00OOOOO000O['params']['fourfold1']
                if order == 2:
                    return O00OOOOO000O['params']['fourfold2']
                print('Error: for SD4ft-Miner, you need to provide order of fourfold table in order= parameter (valid values are 1,2).')
                return None
            else:
                print('Unsupported task type for rule details')
        else:
            print('No such rule.')

    def get_hist(O0OO000OO000, O0OO000OO0OO, fullCond=True):
        if not O0OO000OO000._is_calculated():
            print('ERROR: Task has not been calculated.')
            return
        if O0OO000OO0OO <= len(O0OO000OO000.result['rules']):
            if O0OO000OO000.result['taskinfo']['task_type'] == 'CFMiner':
                OOO00OO0O0O0 = O0OO000OO000.result['rules'][O0OO000OO0OO - 1]
                return OOO00OO0O0O0['params']['hist']
            elif O0OO000OO000.result['taskinfo']['task_type'] == 'UICMiner':
                OOO00OO0O0O0 = O0OO000OO000.result['rules'][O0OO000OO0OO - 1]
                OOOO00OO0O0O = None
                if fullCond:
                    OOOO00OO0O0O = OOO00OO0O0O0['params']['hist_cond']
                else:
                    OOOO00OO0O0O = OOO00OO0O0O0['params']['hist']
                return OOOO00OO0O0O
            elif O0OO000OO000.result['taskinfo']['task_type'] == 'SD4ftMiner':
                print('Error: SD4ft-Miner has no histogram')
                return None
            elif O0OO000OO000.result['taskinfo']['task_type'] == '4ftMiner':
                print('Error: 4ft-Miner has no histogram')
                return None
            else:
                print('Unsupported task type for rule details')
        else:
            print('No such rule.')

    def get_hist_cond(OO000OO0OO00, OO00O0OOOOOO):
        if not OO000OO0OO00._is_calculated():
            print('ERROR: Task has not been calculated.')
            return
        if OO00O0OOOOOO <= len(OO000OO0OO00.result['rules']):
            if OO000OO0OO00.result['taskinfo']['task_type'] == 'UICMiner':
                OO0OO00OOOO0 = OO000OO0OO00.result['rules'][OO00O0OOOOOO - 1]
                return OO0OO00OOOO0['params']['hist_cond']
            elif OO000OO0OO00.result['taskinfo']['task_type'] == 'CFMiner':
                OO0OO00OOOO0 = OO000OO0OO00.result['rules'][OO00O0OOOOOO - 1]
                return OO0OO00OOOO0['params']['hist']
            elif OO000OO0OO00.result['taskinfo']['task_type'] == 'SD4ftMiner':
                print('Error: SD4ft-Miner has no histogram')
                return None
            elif OO000OO0OO00.result['taskinfo']['task_type'] == '4ftMiner':
                print('Error: 4ft-Miner has no histogram')
                return None
            else:
                print('Unsupported task type for rule details')
        else:
            print('No such rule.')

    def get_quantifiers(OOO000OOO00O, OOO0O0000000, order=0):
        if not OOO000OOO00O._is_calculated():
            print('ERROR: Task has not been calculated.')
            return None
        if OOO0O0000000 <= len(OOO000OOO00O.result['rules']):
            O0O000O000OO = OOO000OOO00O.result['rules'][OOO0O0000000 - 1]
            if OOO000OOO00O.result['taskinfo']['task_type'] == '4ftMiner':
                return O0O000O000OO['params']
            elif OOO000OOO00O.result['taskinfo']['task_type'] == 'CFMiner':
                return O0O000O000OO['params']
            elif OOO000OOO00O.result['taskinfo']['task_type'] == 'SD4ftMiner':
                return O0O000O000OO['params']
            else:
                print('Unsupported task type for rule details')
        else:
            print('No such rule.')

    def get_varlist(OOOOO00O00O0):
        return OOOOO00O00O0.result['datalabels']['varname']

    def get_category_names(O0O0OOOOOO0O, varname=None, varindex=None):
        OO0O0O0O0O00 = 0
        if varindex is not None:
            if OO0O0O0O0O00 >= 0 & OO0O0O0O0O00 < len(O0O0OOOOOO0O.get_varlist()):
                OO0O0O0O0O00 = varindex
            else:
                print('Error: no such variable.')
                return
        if varname is not None:
            OOOO0O000OOO = O0O0OOOOOO0O.get_varlist()
            OO0O0O0O0O00 = OOOO0O000OOO.index(varname)
            if OO0O0O0O0O00 == -1 | OO0O0O0O0O00 < 0 | OO0O0O0O0O00 >= len(O0O0OOOOOO0O.get_varlist()):
                print('Error: no such variable.')
                return
        return O0O0OOOOOO0O.result['datalabels']['catnames'][OO0O0O0O0O00]

    def print_data_definition(O0000O000OO0):
        O00OO000000O = O0000O000OO0.get_varlist()
        print(f'Dataset has {len(O00OO000000O)} variables.')
        for OO00OOO0O000 in O00OO000000O:
            O00000O0O0OO = O0000O000OO0.get_category_names(OO00OOO0O000)
            O0OOO0OOO0O0 = ''
            for OO0OOO000O0O in O00000O0O0OO:
                O0OOO0OOO0O0 = O0OOO0OOO0O0 + str(OO0OOO000O0O) + ' '
            O0OOO0OOO0O0 = O0OOO0OOO0O0[:-1]
            print(f'Variable {OO00OOO0O000} has {len(O00000O0O0OO)} categories: {O0OOO0OOO0O0}')

    def _is_calculated(O00O00OOOO00):
        O000OO00OOOO = False
        if 'taskinfo' in O00O00OOOO00.result:
            O000OO00OOOO = True
        return O000OO00OOOO

    def save(OO0OOOO0OOO0, O0OOOO00O00O, savedata=False, embeddata=True, fmt='pickle'):
        if not OO0OOOO0OOO0._is_calculated():
            print('ERROR: Task has not been calculated.')
            return None
        OOO00O0O0000 = {'program': 'CleverMiner', 'version': OO0OOOO0OOO0.get_version_string()}
        OO0O00OO00OO = {}
        OO0O00OO00OO['control'] = OOO00O0O0000
        OO0O00OO00OO['result'] = OO0OOOO0OOO0.result
        OO0O00OO00OO['stats'] = OO0OOOO0OOO0.stats
        OO0O00OO00OO['options'] = OO0OOOO0OOO0.options
        OO0O00OO00OO['profiles'] = OO0OOOO0OOO0.profiles
        if savedata:
            if embeddata:
                OO0O00OO00OO['data'] = OO0OOOO0OOO0.data
                OO0O00OO00OO['df'] = OO0OOOO0OOO0.df
            else:
                O0O0OOO000O0 = {}
                O0O0OOO000O0['data'] = OO0OOOO0OOO0.data
                O0O0OOO000O0['df'] = OO0OOOO0OOO0.df
                print(f'CALC HASH {datetime.now()}')
                OOOOO000OO0O = OO0OOOO0OOO0._get_fast_hash(O0O0OOO000O0)
                print(f'CALC HASH ...done {datetime.now()}')
                O00000O00O00 = os.path.join(OO0OOOO0OOO0.cache_dir, OOOOO000OO0O + '.clmdata')
                O00O0O0O0OOO = open(O00000O00O00, 'wb')
                pickle.dump(O0O0OOO000O0, O00O0O0O0OOO, protocol=pickle.HIGHEST_PROTOCOL)
                OO0O00OO00OO['datafile'] = O00000O00O00
        if fmt == 'pickle':
            OOO0O00O0OO0 = open(O0OOOO00O00O, 'wb')
            pickle.dump(OO0O00OO00OO, OOO0O00O0OO0, protocol=pickle.HIGHEST_PROTOCOL)
        elif fmt == 'json':
            OOO0O00O0OO0 = open(O0OOOO00O00O, 'w')
            json.dump(OO0O00OO00OO, OOO0O00O0OO0)
        else:
            print(f'Unsupported format - {fmt}. Supported formats are pickle, json.')

    def load(OO0O000O000O, O0O0O0OOO000, fmt='pickle'):
        O00O00OOO0OO = False
        if '://' in O0O0O0OOO000:
            O00O00OOO0OO = True
        if fmt == 'pickle':
            if O00O00OOO0OO:
                OO0O0000O0O0 = pickle.load(urllib.request.urlopen(O0O0O0OOO000))
            else:
                O0000O0O0O0O = open(O0O0O0OOO000, 'rb')
                OO0O0000O0O0 = pickle.load(O0000O0O0O0O)
        elif fmt == 'json':
            if O00O00OOO0OO:
                OO0O0000O0O0 = json.load(urllib.request.urlopen(O0O0O0OOO000))
            else:
                O0000O0O0O0O = open(O0O0O0OOO000, 'r')
                OO0O0000O0O0 = json.load(O0000O0O0O0O)
        else:
            print(f'Unsupported format - {fmt}. Supported formats are pickle, json.')
            return
        if not 'control' in OO0O0000O0O0:
            print('Error: not a CleverMiner save file (1)')
            return None
        O0O00000OO00 = OO0O0000O0O0['control']
        if not 'program' in O0O00000OO00 or not 'version' in O0O00000OO00:
            print('Error: not a CleverMiner save file (2)')
            return None
        if not O0O00000OO00['program'] == 'CleverMiner':
            print('Error: not a CleverMiner save file (3)')
            return None
        OO0O000O000O.result = OO0O0000O0O0['result']
        OO0O000O000O.stats = OO0O0000O0O0['stats']
        OO0O000O000O.options = OO0O0000O0O0['options']
        if 'profiles' in OO0O0000O0O0:
            OO0O000O000O.profiles = OO0O0000O0O0['profiles']
        if 'data' in OO0O0000O0O0:
            OO0O000O000O.data = OO0O0000O0O0['data']
            OO0O000O000O._initialized = True
        if 'df' in OO0O0000O0O0:
            OO0O000O000O.df = OO0O0000O0O0['df']
        if 'datafile' in OO0O0000O0O0:
            try:
                O000OO0OOOOO = open(OO0O0000O0O0['datafile'], 'rb')
                O0O000OOOOO0 = pickle.load(O000OO0OOOOO)
                OO0O000O000O.data = O0O000OOOOO0['data']
                OO0O000O000O.df = O0O000OOOOO0['df']
                print(f"...data loaded from file {OO0O0000O0O0['datafile']}.")
            except:
                print(f'Error loading saved file. Linked data file does not exists or it is in incorrect structure or path. If you are transferring saved file to another computer, please embed also data.')
                exit(1)
        print(f'File {O0O0O0OOO000} loaded ok.')

    def get_version_string(OO0O0O0OO00O):
        return OO0O0O0OO00O.version_string

    def get_rule_cedent_list(O0O000O00000, OO000O0000OO):
        if not O0O000O00000._is_calculated():
            print('ERROR: Task has not been calculated.')
            return
        if OO000O0000OO <= 0 or OO000O0000OO > O0O000O00000.get_rulecount():
            if O0O000O00000.get_rulecount() == 0:
                print('No such rule. There are no rules in result.')
            else:
                print(f'No such rule ({OO000O0000OO}). Available rules are 1 to {O0O000O00000.get_rulecount()}')
            return None
        O0O000OO00O0 = []
        O000000OOO0O = O0O000O00000.result['rules'][OO000O0000OO - 1]
        O0O000OO00O0 = list(O000000OOO0O['trace_cedent_dataorder'].keys())
        return O0O000OO00O0

    def get_rule_variables(OOO0OOOO0O00, OOOO0OO00OOO, O000OOO00OO0, get_names=True):
        if not OOO0OOOO0O00._is_calculated():
            print('ERROR: Task has not been calculated.')
            return
        if OOOO0OO00OOO <= 0 or OOOO0OO00OOO > OOO0OOOO0O00.get_rulecount():
            if OOO0OOOO0O00.get_rulecount() == 0:
                print('No such rule. There are no rules in result.')
            else:
                print(f'No such rule ({OOOO0OO00OOO}). Available rules are 1 to {OOO0OOOO0O00.get_rulecount()}')
            return None
        OO00O0O0000O = []
        OO00O000O000 = OOO0OOOO0O00.result['rules'][OOOO0OO00OOO - 1]
        OOO00O00O0OO = OOO0OOOO0O00.result['datalabels']['varname']
        if not O000OOO00OO0 in OO00O000O000['trace_cedent_dataorder']:
            print(f'ERROR: cedent {O000OOO00OO0} not in result.')
            exit(1)
        for O0O00O0OO0O0 in OO00O000O000['trace_cedent_dataorder'][O000OOO00OO0]:
            if get_names:
                OO00O0O0000O.append(OOO00O00O0OO[O0O00O0OO0O0])
            else:
                OO00O0O0000O.append(O0O00O0OO0O0)
        return OO00O0O0000O

    def get_rule_categories(OOO0OOO00O0O, OOO0OO0OOO00, OO00OOO0OOOO, O0O0O000OOO0, get_names=True):
        if not OOO0OOO00O0O._is_calculated():
            print('ERROR: Task has not been calculated.')
            return
        if OOO0OO0OOO00 <= 0 or OOO0OO0OOO00 > OOO0OOO00O0O.get_rulecount():
            if OOO0OOO00O0O.get_rulecount() == 0:
                print('No such rule. There are no rules in result.')
            else:
                print(f'No such rule ({OOO0OO0OOO00}). Available rules are 1 to {OOO0OOO00O0O.get_rulecount()}')
            return None
        O0O0OOO0O00O = []
        O00OOOOO0000 = OOO0OOO00O0O.result['rules'][OOO0OO0OOO00 - 1]
        OOOO0O0O00OO = OOO0OOO00O0O.result['datalabels']['varname']
        if O0O0O000OOO0 in OOOO0O0O00OO:
            OO0OO00000O0 = OOOO0O0O00OO.index(O0O0O000OOO0)
            OO00O0O0OO0O = OOO0OOO00O0O.result['datalabels']['catnames'][OO0OO00000O0]
            if not OO00OOO0OOOO in O00OOOOO0000['trace_cedent_dataorder']:
                print(f'ERROR: cedent {OO00OOO0OOOO} not in result.')
                exit(1)
            O00OOO000O00 = O00OOOOO0000['trace_cedent_dataorder'][OO00OOO0OOOO].index(OO0OO00000O0)
            for O00O0OOO0OOO in O00OOOOO0000['traces'][OO00OOO0OOOO][O00OOO000O00]:
                if get_names:
                    O0O0OOO0O00O.append(OO00O0O0OO0O[O00O0OOO0OOO])
                else:
                    O0O0OOO0O00O.append(O00O0OOO0OOO)
        else:
            print(f'ERROR: variable not found: {OO00OOO0OOOO},{O0O0O000OOO0}. Possible variables are {OOOO0O0O00OO}')
            exit(1)
        return O0O0OOO0O00O

    def get_dataset_variable_count(OOOO00OO0OO0):
        if not OOOO00OO0OO0._is_calculated():
            print('ERROR: Task has not been calculated.')
            return
        O00000OO000O = OOOO00OO0OO0.result['datalabels']['varname']
        return len(O00000OO000O)

    def get_dataset_variable_list(O0O00O0OO000):
        if not O0O00O0OO000._is_calculated():
            print('ERROR: Task has not been calculated.')
            return
        OOOO0O0OO0OO = O0O00O0OO000.result['datalabels']['varname']
        return OOOO0O0OO0OO

    def get_dataset_variable_name(O0OOO0O0O0O0, O00O0OOO0O0O):
        if not O0OOO0O0O0O0._is_calculated():
            print('ERROR: Task has not been calculated.')
            return
        OOOOO0O0OO00 = O0OOO0O0O0O0.get_dataset_variable_list()
        if O00O0OOO0O0O >= 0 and O00O0OOO0O0O < len(OOOOO0O0OO00):
            return OOOOO0O0OO00[O00O0OOO0O0O]
        else:
            print(f'ERROR: dataset has only {len(OOOOO0O0OO00)} variables, required index is {O00O0OOO0O0O}, but available values are 0-{len(OOOOO0O0OO00) - 1}.')
            exit(1)

    def get_dataset_variable_index(OO00OOOOOOOO, OOO0OO0OOOO0):
        if not OO00OOOOOOOO._is_calculated():
            print('ERROR: Task has not been calculated.')
            return
        OO000OOOO00O = OO00OOOOOOOO.get_dataset_variable_list()
        if OOO0OO0OOOO0 in OO000OOOO00O:
            return OO000OOOO00O.index(OOO0OO0OOOO0)
        else:
            print(f'ERROR: attribute {OOO0OO0OOOO0} is not in dataset. The list of attribute names is  {OO000OOOO00O}.')
            exit(1)

    def get_dataset_category_list(OO0OOO000000, OOO00OO000OO):
        if not OO0OOO000000._is_calculated():
            print('ERROR: Task has not been calculated.')
            return
        OO00OO0O00O0 = OO0OOO000000.result['datalabels']['catnames']
        OO0O00OOOO0O = None
        if isinstance(OOO00OO000OO, int):
            OO0O00OOOO0O = OOO00OO000OO
        else:
            OO0O00OOOO0O = OO0OOO000000.get_dataset_variable_index(OOO00OO000OO)
        if OO0O00OOOO0O >= 0 and OO0O00OOOO0O < len(OO00OO0O00O0):
            return OO00OO0O00O0[OO0O00OOOO0O]
        else:
            print(f'ERROR: dataset has only {len(OO00OO0O00O0)} variables, required index is {OO0O00OOOO0O}, but available values are 0-{len(OO00OO0O00O0) - 1}.')
            exit(1)

    def get_dataset_category_count(O000O00O0O00, OOOOO0000OOO):
        if not O000O00O0O00._is_calculated():
            print('ERROR: Task has not been calculated.')
            return
        O00OO0000OO0 = None
        if isinstance(OOOOO0000OOO, int):
            O00OO0000OO0 = OOOOO0000OOO
        else:
            O00OO0000OO0 = O000O00O0O00.get_dataset_variable_index(OOOOO0000OOO)
        OOOOOO00000O = O000O00O0O00.get_dataset_category_list(O00OO0000OO0)
        return len(OOOOOO00000O)

    def get_dataset_category_name(OO0000O0O000, OO000OO0O0OO, O000OOOOO0O0):
        if not OO0000O0O000._is_calculated():
            print('ERROR: Task has not been calculated.')
            return
        O00000000O0O = None
        if isinstance(OO000OO0O0OO, int):
            O00000000O0O = OO000OO0O0OO
        else:
            O00000000O0O = OO0000O0O000.get_dataset_variable_index(OO000OO0O0OO)
        OO000OOOOO00 = OO0000O0O000.get_dataset_category_list(O00000000O0O)
        if O000OOOOO0O0 >= 0 and O000OOOOO0O0 < len(OO000OOOOO00):
            return OO000OOOOO00[O000OOOOO0O0]
        else:
            print(f'ERROR: variable has only {len(OO000OOOOO00)} categories, required index is {O000OOOOO0O0}, but available values are 0-{len(OO000OOOOO00) - 1}.')
            exit(1)

    def get_dataset_category_index(O00O0000OOOO, OOOO00O0OOO0, O0O00000O00O):
        if not O00O0000OOOO._is_calculated():
            print('ERROR: Task has not been calculated.')
            return
        OO0OO00O0000 = None
        if isinstance(OOOO00O0OOO0, int):
            OO0OO00O0000 = OOOO00O0OOO0
        else:
            OO0OO00O0000 = O00O0000OOOO.get_dataset_variable_index(OOOO00O0OOO0)
        O00O0OOO00OO = O00O0000OOOO.get_dataset_category_list(OO0OO00O0000)
        if O0O00000O00O in O00O0OOO00OO:
            return O00O0OOO00OO.index(O0O00000O00O)
        else:
            print(f'ERROR: value {O0O00000O00O} is invalid for the variable {O00O0000OOOO.get_dataset_variable_name(OO0OO00O0000)}. Available category names are {O00O0OOO00OO}.')
            exit(1)

def O00000O000O0(O00OOO00OO0O, minlen=1, maxlen=3, type='con'):
    O0OO0OO00O00 = []
    for O00OO00O0OOO in O00OOO00OO0O:
        if isinstance(O00OO00O0OOO, dict):
            OOOOOO0O0OO0 = O00OO00O0OOO
        else:
            OOOOOO0O0OO0 = {}
            OOOOOO0O0OO0['name'] = O00OO00O0OOO
            OOOOOO0O0OO0['type'] = 'subset'
            OOOOOO0O0OO0['minlen'] = 1
            OOOOOO0O0OO0['maxlen'] = 1
        O0OO0OO00O00.append(OOOOOO0O0OO0)
    O0OO0O0O000O = {}
    O0OO0O0O000O['attributes'] = O0OO0OO00O00
    O0OO0O0O000O['minlen'] = minlen
    O0OO0O0O000O['maxlen'] = maxlen
    O0OO0O0O000O['type'] = type
    return O0OO0O0O000O

def O00OOOOOO000(OO0O0OOOO0OO, minlen=1, maxlen=1):
    O0O00O00O0O0 = {}
    O0O00O00O0O0['name'] = OO0O0OOOO0OO
    O0O00O00O0O0['type'] = 'subset'
    O0O00O00O0O0['minlen'] = minlen
    O0O00O00O0O0['maxlen'] = maxlen
    return O0O00O00O0O0

def O0O0O00O0O0O(OO0O0O00OO00, minlen=1, maxlen=2):
    O00O000OOOOO = {}
    O00O000OOOOO['name'] = OO0O0O00OO00
    O00O000OOOOO['type'] = 'seq'
    O00O000OOOOO['minlen'] = minlen
    O00O000OOOOO['maxlen'] = maxlen
    return O00O000OOOOO

def O0OO0OOOOOO0(O0OOO00OO00O, minlen=1, maxlen=2):
    O00O0OO00000 = {}
    O00O0OO00000['name'] = O0OOO00OO00O
    O00O0OO00000['type'] = 'lcut'
    O00O0OO00000['minlen'] = minlen
    O00O0OO00000['maxlen'] = maxlen
    return O00O0OO00000

def O000O00000OO(OOOO0OOO00O0, minlen=1, maxlen=2):
    O0O00O0OOO0O = {}
    O0O00O0OOO0O['name'] = OOOO0OOO00O0
    O0O00O0OOO0O['type'] = 'rcut'
    O0O00O0OOO0O['minlen'] = minlen
    O0O00O0OOO0O['maxlen'] = maxlen
    return O0O00O0OOO0O