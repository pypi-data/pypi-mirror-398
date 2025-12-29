import math #line:2
import pandas as pd #line:4
import numpy as np #line:5
from sklearn .metrics import precision_recall_curve ,roc_curve ,confusion_matrix #line:6
from numpy import argmax #line:7
from numpy import arange #line:8
import sys #line:9
from sklearn .metrics import f1_score #line:10
from datetime import datetime #line:11
import scipy #line:13
import sklearn .impute #line:14
from sklearn .impute import SimpleImputer #line:17
from sklearn .model_selection import train_test_split #line:18
from sklearn .preprocessing import OneHotEncoder #line:19
from cleverminer import cleverminer #line:21
import pickle #line:22
import operator #line:23
import openpyxl #line:24
from enum import Enum #line:25
class bcolors :#line:27
    HEADER ='\033[95m'#line:28
    OKBLUE ='\033[94m'#line:29
    OKCYAN ='\033[96m'#line:30
    OKGREEN ='\033[92m'#line:31
    WARNING ='\033[93m'#line:32
    FAIL ='\033[91m'#line:33
    ENDC ='\033[0m'#line:34
    BOLD ='\033[1m'#line:35
    UNDERLINE ='\033[4m'#line:36
    BLACK ='\033[0;30m'#line:37
    RED ='\033[0;31m'#line:38
    GREEN ='\033[0;32m'#line:39
    BROWN ='\033[0;33m'#line:40
    BLUE ='\033[0;34m'#line:41
    PURPLE ='\033[0;35m'#line:42
    CYAN ='\033[0;36m'#line:43
    GREY ='\033[0;37m'#line:44
    DARK_GREY ='\033[1;30m'#line:46
    LIGHT_RED ='\033[1;31m'#line:47
    LIGHT_GREEN ='\033[1;32m'#line:48
    YELLOW ='\033[1;33m'#line:49
    LIGHT_BLUE ='\033[1;34m'#line:50
    LIGHT_PURPLE ='\033[1;35m'#line:51
    LIGHT_CYAN ='\033[1;36m'#line:52
    WHITE ='\033[1;37m'#line:53
    RESET ="\033[0m"#line:55
class clmeq_rq (Enum ):#line:59
    NONE =0 #line:60
    CONF =1 #line:61
    LIFT =2 #line:62
    DBLCONF =10 #line:63
    DBLLIFT =11 #line:64
    BOTHSIDELIFT =12 #line:65
    DBLFOUNDEDIMPLICATION =13 #line:66
    FOUNDEDEQUIV =14 #line:67
    CONFS =21 #line:68
    CRAMERVS =22 #line:69
    DBLCONFS =23 #line:70
    DBLCONFSS =24 #line:71
    DBLFOUNDEDIMPLICATIONS =25 #line:72
class clmec :#line:76
    canbeignored =bcolors .DARK_GREY #line:80
    is_fitted =False #line:85
    clm_f =None #line:86
    clm_s =None #line:87
    sorted_rulelist =None #line:88
    backup_val =None #line:89
    most_frequent_val =None #line:90
    cutoff =None #line:92
    is_multiclass =False #line:93
    classes =None #line:94
    multi_probas =[]#line:95
    use_dissimilarity =False #line:96
    robustness ={'min_base_for_mining':10 ,'rule_mining_quantifier':clmeq_rq .CONF ,'rule_mining_quantifier_value':0.1 ,'min_additionally_scored':3 ,'int_rule_buffer_size':2000 ,'rq_quantifier':clmeq_rq .CONF }#line:98
    y_for_inner_eval =None #line:100
    show_processing_details =0 #line:102
    show_csv_for_export =False #line:103
    def _get_dissimilarity (OO0O0O0000OOO00OO ,O000000O00OOO00O0 ,O000OOO0OO0O0OOO0 ):#line:105
        return 1 #line:107
    def __init__ (O0O00000O00O00OO0 ,use_dissimilarity =False ,rq_quantifier =None ,robustness_min_base =None ,robustness_min_additioanlly_scored =3 ,robustness_int_rule_buffer_size =2000 ,rule_mining_quantifier =None ,rule_mining_quantifier_value =None ,show_processing_details =0 ,show_csv_for_export =False ):#line:109
        O0O00000O00O00OO0 .use_dissimilarity =use_dissimilarity #line:110
        if O0O00000O00O00OO0 .use_dissimilarity :#line:111
            print ("ERROR: DISSIMILARITY FUNCTION IS SUSPENDED.")#line:112
            exit (1 )#line:113
        O0O00000O00O00OO0 .robustness ={'min_base_for_mining':10 ,'rule_mining_quantifier':clmeq_rq .CONF ,'rule_mining_quantifier_value':0.1 ,'min_additionally_scored':3 ,'int_rule_buffer_size':2000 ,'rq_quantifier':clmeq_rq .CONF }#line:114
        if robustness_min_base is not None :#line:115
            O0O00000O00O00OO0 .robustness ['min_base_for_mining']=robustness_min_base #line:116
        if robustness_min_additioanlly_scored is not None :#line:117
            O0O00000O00O00OO0 .robustness ['min_additionally_scored']=robustness_min_additioanlly_scored #line:118
        if robustness_int_rule_buffer_size is not None :#line:119
            O0O00000O00O00OO0 .robustness ['int_rule_buffer_size']=robustness_int_rule_buffer_size #line:120
        if rq_quantifier is not None :#line:121
            O0O00000O00O00OO0 .robustness ['rq_quantifier']=rq_quantifier #line:122
        if rule_mining_quantifier is not None :#line:123
            O0O00000O00O00OO0 .robustness ['rule_mining_quantifier']=rule_mining_quantifier #line:124
        if rule_mining_quantifier_value is not None :#line:125
            O0O00000O00O00OO0 .robustness ['rule_mining_quantifier_value']=rule_mining_quantifier_value #line:126
        O0O00000O00O00OO0 .show_processing_details =show_processing_details #line:128
        O0O00000O00O00OO0 .show_csv_for_export =show_csv_for_export #line:129
        print (f"CLM PC initialized.")#line:131
        pass #line:132
    def check_full_structure (O0OO0000O0OO0OO00 ,O0000OO00OOOO0O0O ,O000OO00O0OO0OOO0 ):#line:134
        return #line:135
        print (f"CHECK FULL STRUCTURE: {O0000OO00OOOO0O0O}")#line:136
        for O0OO0OO0000OO00OO in range (len (O000OO00O0OO0OOO0 )):#line:137
            OOOOOO00OO000OOOO =O000OO00O0OO0OOO0 [O0OO0OO0000OO00OO ]#line:138
        print (f"CHECK FULL STRUCTURE : {O0000OO00OOOO0O0O} .... OK")#line:139
    def fit (OOO00000O0OOOOOOO ,OOO00OO0000OOO00O ,O00OOO0O0O0O00O00 ):#line:141
        O000OOO0O0OO00O0O =OOO00OO0000OOO00O #line:147
        OOO00000O0OOOOOOO .y_for_inner_eval =O00OOO0O0O0O00O00 #line:148
        OOO00000O0OOOOOOO .check_full_structure ('fit:check:y',O00OOO0O0O0O00O00 )#line:149
        O0OO00OO0000O0OO0 =O000OOO0O0OO00O0O .columns #line:150
        O0O0O0OOO00O0OOO0 =[]#line:151
        for O0O0OOO0OO0O000OO in O0OO00OO0000O0OO0 :#line:152
            OO0O0OO0O000OO00O ={}#line:153
            OO0O0OO0O000OO00O ['name']=O0O0OOO0OO0O000OO #line:154
            OO0O0OO0O000OO00O ['type']='subset'#line:155
            OO0O0OO0O000OO00O ['minlen']=1 #line:156
            OO0O0OO0O000OO00O ['maxlen']=1 #line:157
            O0O0O0OOO00O0OOO0 .append (OO0O0OO0O000OO00O )#line:158
        O000OOO0O0OO00O0O ['target']=O00OOO0O0O0O00O00 #line:159
        OOOO00O000O00O0OO =len (O00OOO0O0O0O00O00 )#line:160
        OO00OO00O0OO0O0O0 ,OO0O00OO0O000OO0O =np .unique (O00OOO0O0O0O00O00 ,return_counts =True )#line:161
        O00OOOO00OO000O00 =dict (zip (OO00OO00O0OO0O0O0 ,OO0O00OO0O000OO0O ))#line:162
        OOOOOO0O00O0000O0 =sorted (O00OOOO00OO000O00 .items (),key =lambda O000OO000OO00OOO0 :O000OO000OO00OOO0 [1 ],reverse =True )#line:163
        O0OO0OO0O0000OO0O =None #line:165
        print (f"PREDICTED VALUES DISTRIBUTION: DZ: {O00OOOO00OO000O00}, DZ_SORTED: {OOOOOO0O00O0000O0}")#line:166
        if len (O00OOOO00OO000O00 )<=2 :#line:167
            OOO00000O0OOOOOOO .is_multiclass =False #line:168
            OOO00000O0OOOOOOO .classes =None #line:169
            OOO00000O0OOOOOOO .multi_probas =None #line:170
        else :#line:171
            OOO00000O0OOOOOOO .is_multiclass =True #line:172
            OOO00000O0OOOOOOO .classes =O00OOOO00OO000O00 #line:173
            OOOOOO00O0OOOO0O0 =[O00OOOO00OO000O00 [OOOO0OOOOOO0OOO0O ]/OOOO00O000O00O0OO for OOOO0OOOOOO0OOO0O in O00OOOO00OO000O00 ]#line:174
            OOO00000O0OOOOOOO .multi_probas =OOOOOO00O0OOOO0O0 #line:176
            O0000OO00O00OO0O0 =np .argmax (OOOOOO00O0OOOO0O0 )#line:177
            OOO00000O0OOOOOOO .most_frequent_val =OO00OO00O0OO0O0O0 [O0000OO00O00OO0O0 ]#line:178
        for O0O0OOO0OO0O000OO in O00OOOO00OO000O00 .keys ():#line:180
            if O0OO0OO0O0000OO0O is None :#line:181
                O0OO0OO0O0000OO0O =O00OOOO00OO000O00 [O0O0OOO0OO0O000OO ]#line:182
            else :#line:183
                if O0OO0OO0O0000OO0O >O00OOOO00OO000O00 [O0O0OOO0OO0O000OO ]:#line:184
                    O0OO0OO0O0000OO0O =O00OOOO00OO000O00 [O0O0OOO0OO0O000OO ]#line:185
        O00OOOO00O0OOOO0O =OOO00000O0OOOOOOO .robustness ['min_base_for_mining']#line:186
        O000O0O0OOOOO0000 ={}#line:187
        for O0O0OOO0OO0O000OO in O00OOO0O0O0O00O00 :#line:191
            if O0O0OOO0OO0O000OO in O000O0O0OOOOO0000 :#line:193
                O000O0O0OOOOO0000 [O0O0OOO0OO0O000OO ]+=1 #line:195
            else :#line:196
                O000O0O0OOOOO0000 [O0O0OOO0OO0O000OO ]=1 #line:198
        O0OO00O00OO0O0O0O =[]#line:204
        OO0O0OO0O000OO00O ={}#line:205
        OO0O0OO0O000OO00O ['name']='target'#line:207
        if OOO00000O0OOOOOOO .is_multiclass :#line:208
            OO0O0OO0O000OO00O ['type']='subset'#line:209
            OO0O0OO0O000OO00O ['minlen']=1 #line:210
            OO0O0OO0O000OO00O ['maxlen']=1 #line:211
        else :#line:212
            OO0O0OO0O000OO00O ['type']='one'#line:213
            OO0O0OO0O000OO00O ['value']=list (O00OOOO00OO000O00 .keys ())[1 ]#line:214
        O0OO00O00OO0O0O0O .append (OO0O0OO0O000OO00O )#line:215
        O00OOO0OOOOOO0O00 ='conf'#line:217
        OO00O0O00O00OO0O0 =0.1 #line:218
        if OOO00000O0OOOOOOO .robustness ['rule_mining_quantifier']==clmeq_rq .CONF :#line:220
            O00OOO0OOOOOO0O00 ='conf'#line:221
        elif OOO00000O0OOOOOOO .robustness ['rule_mining_quantifier']==clmeq_rq .DBLCONF :#line:222
            O00OOO0OOOOOO0O00 ='dblconf'#line:223
        elif OOO00000O0OOOOOOO .robustness ['rule_mining_quantifier']==clmeq_rq .DBLLIFT :#line:224
            O00OOO0OOOOOO0O00 ='dbllift'#line:225
        else :#line:226
            print (f"Error: quantifier {OOO00000O0OOOOOOO.robustness['rule_mining_quantifier']} is not supported for mining.")#line:227
            exit (1 )#line:228
        OO00O0O00O00OO0O0 =OOO00000O0OOOOOOO .robustness ['rule_mining_quantifier_value']#line:229
        OOO00000O0OOOOOOO .clm_f =cleverminer (df =O000OOO0O0OO00O0O ,proc ='4ftMiner',quantifiers ={'base':O00OOOO00O0OOOO0O ,O00OOO0OOOOOO0O00 :OO00O0O00O00OO0O0 },ante ={'attributes':O0O0O0OOO00O0OOO0 ,'minlen':1 ,'maxlen':2 ,'type':'con'},succ ={'attributes':O0OO00O00OO0O0O0O ,'minlen':1 ,'maxlen':1 ,'type':'con'},opts ={'use_cache':True })#line:240
        print (f"FIT: RULE COUNT: {OOO00000O0OOOOOOO.clm_f.get_rulecount()}")#line:242
        OO0OOO0OO00O0OO00 =[]#line:245
        O00OOOO0000OO0OOO =None #line:246
        for OO0OOOOOOO0000O0O in range (OOO00000O0OOOOOOO .clm_f .get_rulecount ()):#line:248
            OOOO0O0OOO00OO0O0 =OO0OOOOOOO0000O0O +1 #line:249
            OOOO0OOOO00O0OOOO =OOO00000O0OOOOOOO .clm_f .get_fourfold (OOOO0O0OOO00OO0O0 )#line:250
            if OOO00000O0OOOOOOO .backup_val is None :#line:251
                OOO00000O0OOOOOOO .backup_val =(OOOO0OOOO00O0OOOO [0 ]+OOOO0OOOO00O0OOOO [2 ])/sum (OOOO0OOOO00O0OOOO )#line:252
            OOO0O0O00OOO00O0O =0 #line:257
            if (OOOO0OOOO00O0OOOO [0 ]+OOOO0OOOO00O0OOOO [1 ])*(OOOO0OOOO00O0OOOO [2 ]+OOOO0OOOO00O0OOOO [3 ])*(OOOO0OOOO00O0OOOO [0 ]+OOOO0OOOO00O0OOOO [2 ])*(OOOO0OOOO00O0OOOO [1 ]+OOOO0OOOO00O0OOOO [3 ])>0 :#line:258
                OOO0O0O00OOO00O0O =abs ((OOOO0OOOO00O0OOOO [0 ]*OOOO0OOOO00O0OOOO [3 ]-OOOO0OOOO00O0OOOO [1 ]*OOOO0OOOO00O0OOOO [2 ]))/math .sqrt ((OOOO0OOOO00O0OOOO [0 ]+OOOO0OOOO00O0OOOO [1 ])*(OOOO0OOOO00O0OOOO [2 ]+OOOO0OOOO00O0OOOO [3 ])*(OOOO0OOOO00O0OOOO [0 ]+OOOO0OOOO00O0OOOO [2 ])*(OOOO0OOOO00O0OOOO [1 ]+OOOO0OOOO00O0OOOO [3 ]))#line:260
            OO0O0OOOO00O0O00O =OOOO0OOOO00O0OOOO [0 ]/(sum (OOOO0OOOO00O0OOOO ))#line:261
            OO000OOOOO0OOO000 =OOOO0OOOO00O0OOOO [0 ]/(OOOO0OOOO00O0OOOO [0 ]+OOOO0OOOO00O0OOOO [1 ])#line:262
            OO0OO0000OO0O00O0 =OOOO0OOOO00O0OOOO [0 ]*(sum (OOOO0OOOO00O0OOOO ))/(OOOO0OOOO00O0OOOO [0 ]+OOOO0OOOO00O0OOOO [1 ])/(OOOO0OOOO00O0OOOO [0 ]+OOOO0OOOO00O0OOOO [2 ])#line:263
            OOOOOOO000OO000OO =None #line:264
            if not (OOO00000O0OOOOOOO .is_multiclass )or 1 ==1 :#line:265
                OOOOOOO000OO000OO =OO0OO0000OO0O00O0 #line:266
                if OOOOOOO000OO000OO <1 :#line:267
                    if OOOOOOO000OO000OO ==0 :#line:268
                        OOOOOOO000OO000OO =1 #line:269
                    else :#line:270
                        OOOOOOO000OO000OO =1 /OOOOOOO000OO000OO #line:271
            OOOOO0O000OO0O0OO =0 #line:272
            if OOO00000O0OOOOOOO .is_multiclass or 1 ==1 :#line:273
                O0O00OO0O000O000O =OOOO0OOOO00O0OOOO [0 ]#line:274
                OOOOO0O0OO000OOO0 =OOOO0OOOO00O0OOOO [1 ]#line:275
                OO0O0O000OOO00O00 =OOOO0OOOO00O0OOOO [2 ]#line:276
                OO0O0OO0O000OO00O =OOOO0OOOO00O0OOOO [3 ]#line:277
                if O0O00OO0O000O000O +OOOOO0O0OO000OOO0 >0 and OO0O0O000OOO00O00 +OO0O0OO0O000OO00O >0 and O0O00OO0O000O000O +OO0O0O000OOO00O00 >0 and OOOOO0O0OO000OOO0 +OO0O0OO0O000OO00O >0 :#line:278
                    OOOOO0O000OO0O0OO =O0O00OO0O000O000O /(O0O00OO0O000O000O +OOOOO0O0OO000OOO0 )/((O0O00OO0O000O000O +OO0O0O000OOO00O00 )/(O0O00OO0O000O000O +OOOOO0O0OO000OOO0 +OO0O0O000OOO00O00 +OO0O0OO0O000OO00O ))*OO0O0OO0O000OO00O /(OO0O0O000OOO00O00 +OO0O0OO0O000OO00O )/((OOOOO0O0OO000OOO0 +OO0O0OO0O000OO00O )/(O0O00OO0O000O000O +OOOOO0O0OO000OOO0 +OO0O0O000OOO00O00 +OO0O0OO0O000OO00O ))#line:279
            OO0OO000OO000OOOO =0 #line:280
            if (O0O00OO0O000O000O +OOOOO0O0OO000OOO0 )*(OO0O0O000OOO00O00 +OO0O0OO0O000OO00O )>0 :#line:281
                OO0OO000OO000OOOO =O0O00OO0O000O000O /(O0O00OO0O000O000O +OOOOO0O0OO000OOO0 )*OO0O0OO0O000OO00O /(OO0O0O000OOO00O00 +OO0O0OO0O000OO00O )#line:282
            O0O00O00O0O00000O =OO000OOOOO0OOO000 #line:284
            if OOO00000O0OOOOOOO .robustness ['rq_quantifier']==clmeq_rq .CONF :#line:286
                O0O00O00O0O00000O =OO000OOOOO0OOO000 #line:287
            elif OOO00000O0OOOOOOO .robustness ['rq_quantifier']==clmeq_rq .DBLCONF :#line:288
                O0O00O00O0O00000O =OO0OO000OO000OOOO #line:289
            elif OOO00000O0OOOOOOO .robustness ['rq_quantifier']==clmeq_rq .DBLLIFT :#line:290
                O0O00O00O0O00000O =OOOOO0O000OO0O0OO #line:291
            elif OOO00000O0OOOOOOO .robustness ['rq_quantifier']==clmeq_rq .LIFT :#line:292
                O0O00O00O0O00000O =OO0OO0000OO0O00O0 #line:293
            elif OOO00000O0OOOOOOO .robustness ['rq_quantifier']==clmeq_rq .BOTHSIDELIFT :#line:294
                O0O00O00O0O00000O =OOOOOOO000OO000OO #line:295
            elif OOO00000O0OOOOOOO .robustness ['rq_quantifier']==clmeq_rq .DBLFOUNDEDIMPLICATION :#line:296
                O0O00O00O0O00000O =(OOOO0OOOO00O0OOOO [0 ]/(OOOO0OOOO00O0OOOO [0 ]+OOOO0OOOO00O0OOOO [1 ]))*OOOO0OOOO00O0OOOO [0 ]/(OOOO0OOOO00O0OOOO [0 ]+OOOO0OOOO00O0OOOO [2 ])#line:297
            elif OOO00000O0OOOOOOO .robustness ['rq_quantifier']==clmeq_rq .FOUNDEDEQUIV :#line:298
                O0O00O00O0O00000O =OOOO0OOOO00O0OOOO [0 ]/(OOOO0OOOO00O0OOOO [0 ]+OOOO0OOOO00O0OOOO [1 ]+OOOO0OOOO00O0OOOO [2 ])#line:299
            elif OOO00000O0OOOOOOO .robustness ['rq_quantifier']==clmeq_rq .CONFS :#line:300
                O0O00O00O0O00000O =OO000OOOOO0OOO000 *math .log (math .log (1 +OOOO0OOOO00O0OOOO [0 ]))#line:301
            elif OOO00000O0OOOOOOO .robustness ['rq_quantifier']==clmeq_rq .CRAMERVS :#line:302
                O0O00O00O0O00000O =OOO0O0O00OOO00O0O *math .log (1 +OOOO0OOOO00O0OOOO [0 ])#line:303
            elif OOO00000O0OOOOOOO .robustness ['rq_quantifier']==clmeq_rq .DBLCONFS :#line:304
                O0O00O00O0O00000O =OO0OO000OO000OOOO *math .log (1 +OOOO0OOOO00O0OOOO [0 ])#line:305
            elif OOO00000O0OOOOOOO .robustness ['rq_quantifier']==clmeq_rq .DBLCONFSS :#line:306
                O0O00O00O0O00000O =OO0OO000OO000OOOO *math .log (1 +math .log (1 +OOOO0OOOO00O0OOOO [0 ]))#line:307
            elif OOO00000O0OOOOOOO .robustness ['rq_quantifier']==clmeq_rq .DBLFOUNDEDIMPLICATIONS :#line:308
                O0O00O00O0O00000O =(OOOO0OOOO00O0OOOO [0 ]/(OOOO0OOOO00O0OOOO [0 ]+OOOO0OOOO00O0OOOO [1 ]))*OOOO0OOOO00O0OOOO [0 ]/(OOOO0OOOO00O0OOOO [0 ]+OOOO0OOOO00O0OOOO [2 ])*math .log (1 +OOOO0OOOO00O0OOOO [0 ])#line:309
            else :#line:310
                print (f"ERROR: RQ quantifier {OOO00000O0OOOOOOO.robustness['rq_quantifier']} not supported for RQ")#line:311
                exit (1 )#line:312
            if OOO00000O0OOOOOOO .is_multiclass :#line:314
                O00OO0OOO0O00O000 =OOO00000O0OOOOOOO .clm_f .result ['rules'][OOOO0O0OOO00OO0O0 -1 ]['trace_cedent_dataorder']['succ'][0 ]#line:315
                OO0OO000O00OO00OO =OOO00000O0OOOOOOO .clm_f .result ['rules'][OOOO0O0OOO00OO0O0 -1 ]['traces']['succ'][0 ][0 ]#line:316
                O0O0O0O0O0OOOO0O0 =OOO00000O0OOOOOOO .clm_f .result ['datalabels']['catnames'][O00OO0OOO0O00O000 ][OO0OO000O00OO00OO ]#line:317
                OO0OOO00O0O00O000 =O00OOOO00OO000O00 [O0O0O0O0O0OOOO0O0 ]#line:318
            OO00000000OOOOO00 ={}#line:322
            OO00000000OOOOO00 ['rule_id']=OOOO0O0OOO00OO0O0 #line:323
            OO00000000OOOOO00 ['rq']=O0O00O00O0O00000O #line:324
            OO00000000OOOOO00 ['cramerV']=OOO0O0O00OOO00O0O #line:325
            OO00000000OOOOO00 ['supp']=OO0O0OOOO00O0O00O #line:326
            OO00000000OOOOO00 ['conf']=OO000OOOOO0OOO000 #line:327
            OO00000000OOOOO00 ['bothsidelift']=OOOOOOO000OO000OO #line:328
            OO00000000OOOOO00 ['dbllift']=OOOOO0O000OO0O0OO #line:329
            OO00000000OOOOO00 ['dblconf']=OO0OO000OO000OOOO #line:330
            OO0OOO0OO00O0OO00 .append (OO00000000OOOOO00 )#line:331
        OOO00000O0OOOOOOO .sorted_rulelist =(sorted (OO0OOO0OO00O0OO00 ,key =lambda OOOO0O0OOOO000OO0 :OOOO0O0OOOO000OO0 ['rq'],reverse =True ))#line:333
        O0OOO0O00OOO0000O =OOO00000O0OOOOOOO .robustness ['int_rule_buffer_size']#line:334
        OOO00000O0OOOOOOO .sorted_rulelist =OOO00000O0OOOOOOO .sorted_rulelist [:O0OOO0O00OOO0000O ]#line:335
        O000OOO0O000OOO00 =None #line:340
        O0O000OOO0O0O0O0O =None #line:341
        O0O0OO0O0O00O0OOO =None #line:342
        O0O0OO00OOOO00O0O =None #line:343
        for OO0OOOOOOO0000O0O in range (len (OOO00000O0OOOOOOO .sorted_rulelist )):#line:345
            O0O0OOOOO000O0O00 =OOO00000O0OOOOOOO .sorted_rulelist [OO0OOOOOOO0000O0O ]#line:346
            OO0OOOOO00O00OO0O ,O00OOO000OO0OO000 ,OO0O0O0OO00O0OO00 =OOO00000O0OOOOOOO ._get_rule_scoring (O0O0OOOOO000O0O00 ['rule_id'],phase_is_fitting =True )#line:347
            O0OO0O000O00O0000 =O0O0OOOOO000O0O00 ['rule_id']#line:348
            OOOOOO00000O0O00O =None #line:350
            if OOO00000O0OOOOOOO .is_multiclass or 1 :#line:351
                OO00OO0OOO000000O =OOO00000O0OOOOOOO .clm_f .result ['rules'][O0OO0O000O00O0000 -1 ]#line:352
                OOO0O0OO0O0OO0O0O =OO00OO0OOO000000O ['trace_cedent_dataorder']['succ'][0 ]#line:354
                OO0O000O0O00O0000 =OO00OO0OOO000000O ['traces']['succ'][0 ][0 ]#line:355
                OOOOOO00000O0O00O =OOO00000O0OOOOOOO .clm_f .result ['datalabels']['catnames'][OOO0O0OO0O0OO0O0O ][OO0O000O0O00O0000 ]#line:356
            OOO000O0O00OOO000 =0 #line:358
            OO00O00OOO0000O00 =0 #line:359
            O000OOOOO00OO000O =0 #line:360
            if O0O000OOO0O0O0O0O is None :#line:361
                O0O000OOO0O0O0O0O =OO0O0O0OO00O0OO00 #line:362
            if O000OOO0O000OOO00 is None :#line:363
                O000OOO0O000OOO00 =OO0OOOOO00O00OO0O #line:364
                O0OOO00OO0O00000O =None #line:365
                if isinstance (O000OOO0O000OOO00 ,list ):#line:366
                    O0OOO00OO0O00000O =range (len (O000OOO0O000OOO00 ))#line:367
                else :#line:368
                    O0OOO00OO0O00000O =O000OOO0O000OOO00 .keys ()#line:369
                for O00O0OO0OO000OO00 in O0OOO00OO0O00000O :#line:372
                    if O000OOO0O000OOO00 [O00O0OO0OO000OO00 ]is not None :#line:373
                        OO00O00OOO0000O00 +=1 #line:374
                        if (O0O000OOO0O0O0O0O .iloc [O00O0OO0OO000OO00 ]==OOOOOO00000O0O00O ):#line:378
                            OOO000O0O00OOO000 +=1 #line:379
                        else :#line:380
                            if OOO00000O0OOOOOOO .use_dissimilarity :#line:381
                                O000OOOOO00OO000O +=OOO00000O0OOOOOOO ._get_dissimilarity (O0O000OOO0O0O0O0O [O00O0OO0OO000OO00 ],OOOOOO00000O0O00O )#line:382
                            else :#line:383
                                O000OOOOO00OO000O +=1 #line:384
            else :#line:385
                for O00O0OO0OO000OO00 in range (len (O000OOO0O000OOO00 )):#line:388
                    if O000OOO0O000OOO00 [O00O0OO0OO000OO00 ]is None and OO0OOOOO00O00OO0O [O00O0OO0OO000OO00 ]is not None :#line:390
                        O000OOO0O000OOO00 [O00O0OO0OO000OO00 ]=OO0OOOOO00O00OO0O [O00O0OO0OO000OO00 ]#line:391
                        OO00O00OOO0000O00 +=1 #line:392
                        if (O0O000OOO0O0O0O0O .iloc [O00O0OO0OO000OO00 ]==OOOOOO00000O0O00O ):#line:395
                            OOO000O0O00OOO000 +=1 #line:396
                        else :#line:397
                            if OOO00000O0OOOOOOO .use_dissimilarity :#line:398
                                O000OOOOO00OO000O +=OOO00000O0OOOOOOO ._get_dissimilarity (O0O000OOO0O0O0O0O [O00O0OO0OO000OO00 ],OOOOOO00000O0O00O )#line:399
                            else :#line:400
                                O000OOOOO00OO000O +=1 #line:401
            O0O0OO0O0O00O0OOO =sum (1 for OO000OOOOOO00OO0O in OO0OOOOO00O00OO0O if OO000OOOOOO00OO0O is not None )#line:402
            OO000OOOO00000O00 =sum (1 for O0O00O00000OO00OO in O000OOO0O000OOO00 if O0O00O00000OO00OO is not None )#line:403
            OO0O0O0O00000OO00 =0 #line:404
            if OO00O00OOO0000O00 >0 :#line:405
                OO0O0O0O00000OO00 =OOO000O0O00OOO000 /OO00O00OOO0000O00 #line:406
            OOO00000O0OOOOOOO .sorted_rulelist [OO0OOOOOOO0000O0O ]['add_conf']=OO0O0O0O00000OO00 #line:407
            OOO00000O0OOOOOOO .sorted_rulelist [OO0OOOOOOO0000O0O ]['can_be_ignored']=(OO00O00OOO0000O00 <OOO00000O0OOOOOOO .robustness ['min_additionally_scored']or (abs (OO0O0O0O00000OO00 )<0.0000001 ))#line:408
        if not (OOO00000O0OOOOOOO .is_multiclass ):#line:412
            def O0O0O00000000OOOO (O0OOO0000O00000O0 ,O0OO0O00000O00O00 ):#line:413
                return (O0OOO0000O00000O0 >=O0OO0O00000O00O00 ).astype ('int')#line:414
            O0OOO00000000OO00 =OOO00000O0OOOOOOO .predict_proba (OOO00OO0000OOO00O )#line:417
            OO0OO00OO00O000O0 =O0OOO00000000OO00 [:,1 ]#line:419
            O0000O00O0OO00OOO ,OO00O000OO0O00O00 ,O00000OO000000O00 =roc_curve (O00OOO0O0O0O00O00 ,OO0OO00OO00O000O0 )#line:422
            OOOOO00OO0OOO00O0 =OO00O000OO0O00O00 -O0000O00O0OO00OOO #line:424
            OOO0O000O0OO0O00O =argmax (OOOOO00OO0OOO00O0 )#line:425
            OOO00000O0OOOOOOO .cutoff =O00000OO000000O00 [OOO0O000O0OO0O00O ]#line:429
        else :#line:430
            OOO00000O0OOOOOOO .cutoff =None #line:431
        OOO00000O0OOOOOOO .y_for_inner_eval =None #line:433
        pass #line:435
    def predict (OOOO00000O00000O0 ,OOO00O000OO0OO0O0 ):#line:437
        O000O000O00O0O0O0 =OOOO00000O00000O0 .predict_proba (OOO00O000OO0OO0O0 ,justvector =True )#line:438
        if not (OOOO00000O00000O0 .is_multiclass ):#line:441
            O000O000O00O0O0O0 =[0 if O0O0OO00O00O00O00 <OOOO00000O00000O0 .cutoff else 1 for O0O0OO00O00O00O00 in O000O000O00O0O0O0 ]#line:442
            return np .array (O000O000O00O0O0O0 )#line:443
        else :#line:444
            O00OOOO00O00O00OO =None #line:446
            O0OOOOO0OOO0O0OO0 =None #line:447
            for O000000O000OOOO00 in OOOO00000O00000O0 .classes :#line:448
                if O0OOOOO0OOO0O0OO0 ==None :#line:449
                    O0OOOOO0OOO0O0OO0 =O000000O000OOOO00 #line:450
                    O00OOOO00O00O00OO =OOOO00000O00000O0 .classes [O000000O000OOOO00 ]#line:451
                else :#line:452
                    if OOOO00000O00000O0 .classes [O000000O000OOOO00 ]>O00OOOO00O00O00OO :#line:453
                        O0OOOOO0OOO0O0OO0 =O000000O000OOOO00 #line:454
                        O00OOOO00O00O00OO =OOOO00000O00000O0 .classes [O000000O000OOOO00 ]#line:455
            print (f"DEBUG: classes are {OOOO00000O00000O0.classes}.")#line:456
            print (f"DEBUG: most frequest class is {O0OOOOO0OOO0O0OO0}.")#line:457
            print (f"DEBUG: res so far is {O000O000O00O0O0O0}")#line:458
            O000O000O00O0O0O0 =[O0OOOOO0OOO0O0OO0 if OO00O0O000O000OO0 is None else OO00O0O000O000OO0 for OO00O0O000O000OO0 in O000O000O00O0O0O0 ]#line:459
            return np .array (O000O000O00O0O0O0 )#line:460
        pass #line:461
    def describe (O00O00OO00000O00O ):#line:463
        if O00O00OO00000O00O .sorted_rulelist is None :#line:464
            print ("DESCRIBE: Model not fitted.")#line:465
            return #line:466
        OO0O0OOOO00000O00 =0 #line:467
        O0000OOOO00OOO0OO =0 #line:468
        for O0O00O0OO000OO000 in O00O00OO00000O00O .sorted_rulelist :#line:469
            OO00O0OO0OO0O0OOO =O00O00OO00000O00O .clm_f .get_fourfold (O0O00O0OO000OO000 ['rule_id'])#line:470
            OO0000O0O0O0O0OOO =O00O00OO00000O00O .clm_f .get_ruletext (O0O00O0OO000OO000 ['rule_id'])#line:471
            OO0O0OOOO00000O00 +=1 #line:472
            O00O00OO00O0OO000 =""#line:473
            O00OO000O0000000O =""#line:474
            if O0O00O0OO000OO000 ['can_be_ignored']:#line:475
                O00O00OO00O0OO000 =bcolors .DARK_GREY #line:476
                O00OO000O0000000O =bcolors .ENDC #line:477
            else :#line:478
                O0000OOOO00OOO0OO +=1 #line:479
        print (f"TOTAL RULES : {OO0O0OOOO00000O00}, USED RULES : {O0000OOOO00OOO0OO}")#line:480
        pass #line:481
    def _get_vector (O0O0OOOO0O0O0O000 ,OOOOO00O0O0OOO000 ,use_add_conf =True ):#line:484
        if O0O0OOOO0O0O0O000 .clm_f is None :#line:485
            print ("Model not fitted (1).")#line:486
            return #line:487
        if O0O0OOOO0O0O0O000 .sorted_rulelist is None :#line:488
            print ("Model not fitted (2).")#line:489
            return #line:490
        if O0O0OOOO0O0O0O000 .is_multiclass and 1 ==0 :#line:491
            print ("Method not implemented.")#line:492
            return #line:494
        O0O0OOOO0O0O0O000 .clm_s =cleverminer (df =OOOOO00O0O0OOO000 )#line:496
        O0O0000OO0O00OOOO =None #line:511
        OOO00000OOOO0O000 =0 #line:513
        OO0OO00OOO0O0O0OO =[]#line:514
        for OO00OOOO0000OO00O in range (len (O0O0OOOO0O0O0O000 .sorted_rulelist )):#line:516
            OO0O0O0O0OOO00O00 =O0O0OOOO0O0O0O000 .sorted_rulelist [OO00OOOO0000OO00O ]#line:517
            if OO0O0O0O0OOO00O00 ['can_be_ignored']:#line:518
                OO00OO00O0OOO0OOO =bcolors .DARK_GREY #line:519
                O0000OO00O0O000O0 =bcolors .ENDC #line:520
            else :#line:522
                OOO00000OOOO0O000 +=1 #line:523
                O0OO0OO0OOOO0O0O0 =None #line:526
                OOO0O0O00O0000OOO =None #line:527
                OOOO00OO0OOO0OO0O =None #line:528
                if use_add_conf and not (O0O0OOOO0O0O0O000 .is_multiclass ):#line:529
                    O0OO0OO0OOOO0O0O0 ,OOO0O0O00O0000OOO ,OOOO00OO0OOO0OO0O =O0O0OOOO0O0O0O000 ._get_rule_scoring (OO0O0O0O0OOO00O00 ['rule_id'],phase_is_fitting =False ,add_conf =OO0O0O0O0OOO00O00 ['add_conf'])#line:530
                else :#line:531
                    O0OO0OO0OOOO0O0O0 ,OOO0O0O00O0000OOO ,OOOO00OO0OOO0OO0O =O0O0OOOO0O0O0O000 ._get_rule_scoring (OO0O0O0O0OOO00O00 ['rule_id'],phase_is_fitting =False )#line:532
                OOO0OO00OOOO0OO00 =0 #line:534
                O0O0OO0OO0O000OO0 =None #line:535
                OOOO0OOOO0O00OO00 =0 #line:536
                if O0O0OOOO0O0O0O000 .y_for_inner_eval is not None :#line:537
                    O0O0OO0OO0O000OO0 =0 #line:538
                OOOO0O0000OO0O0OO =0 #line:539
                if O0O0000OO0O00OOOO is None :#line:540
                    O0O0000OO0O00OOOO =O0OO0OO0OOOO0O0O0 #line:541
                    OOO0OO00OOOO0OO00 =sum ([1 if OOO00O0OOO000OO00 is not None else 0 for OOO00O0OOO000OO00 in O0OO0OO0OOOO0O0O0 ])#line:542
                    if O0O0OOOO0O0O0O000 .y_for_inner_eval is not None :#line:543
                        for OOOOOOO0OO0O0O00O in range (len (O0OO0OO0OOOO0O0O0 )):#line:544
                            if O0OO0OO0OOOO0O0O0 [OOOOOOO0OO0O0O00O ]==O0O0OOOO0O0O0O000 .y_for_inner_eval .iloc [OOOOOOO0OO0O0O00O ]:#line:545
                                O0O0OO0OO0O000OO0 +=1 #line:546
                            else :#line:547
                                if O0OO0OO0OOOO0O0O0 [OOOOOOO0OO0O0O00O ]is not None and O0O0OOOO0O0O0O000 .y_for_inner_eval .iloc [OOOOOOO0OO0O0O00O ]is not None :#line:548
                                    if O0O0OOOO0O0O0O000 .use_dissimilarity :#line:549
                                        OOOO0OOOO0O00OO00 +=O0O0OOOO0O0O0O000 ._get_dissimilarity (O0OO0OO0OOOO0O0O0 .iloc [OOOOOOO0OO0O0O00O ],O0O0OOOO0O0O0O000 .y_for_inner_eval .iloc [OOOOOOO0OO0O0O00O ])#line:550
                                    else :#line:551
                                        OOOO0OOOO0O00OO00 +=1 #line:552
                else :#line:553
                    for OO00O0OO000OO00OO in range (len (O0O0000OO0O00OOOO )):#line:556
                        if O0O0000OO0O00OOOO [OO00O0OO000OO00OO ]is None and O0OO0OO0OOOO0O0O0 [OO00O0OO000OO00OO ]is not None :#line:558
                            O0O0000OO0O00OOOO [OO00O0OO000OO00OO ]=O0OO0OO0OOOO0O0O0 [OO00O0OO000OO00OO ]#line:559
                            OOO0OO00OOOO0OO00 +=1 #line:560
                            if O0O0OOOO0O0O0O000 .y_for_inner_eval is not None :#line:561
                                if O0OO0OO0OOOO0O0O0 [OO00O0OO000OO00OO ]==O0O0OOOO0O0O0O000 .y_for_inner_eval .iloc [OO00O0OO000OO00OO ]:#line:562
                                    O0O0OO0OO0O000OO0 +=1 #line:563
                                else :#line:564
                                    if O0OO0OO0OOOO0O0O0 [OOOOOOO0OO0O0O00O ]is not None and O0O0OOOO0O0O0O000 .y_for_inner_eval .iloc [OOOOOOO0OO0O0O00O ]is not None :#line:565
                                        if O0O0OOOO0O0O0O000 .use_dissimilarity :#line:566
                                            OOOO0OOOO0O00OO00 +=_get_dissimilarity (O0OO0OO0OOOO0O0O0 [OOOOOOO0OO0O0O00O ],O0O0OOOO0O0O0O000 .y_for_inner_eval .iloc [OOOOOOO0OO0O0O00O ])#line:567
                                        else :#line:568
                                            OOOO0OOOO0O00OO00 +=1 #line:569
                O0O0000OO0OO0OO00 =None #line:571
                OOOOO0O0O0OO0OO0O =[1 if OO00O0OOOOOOOO0OO is not None else 0 for OO00O0OOOOOOOO0OO in O0OO0OO0OOOO0O0O0 ]#line:572
                OOO000O0OO0000O0O =None #line:574
                if O0O0OO0OO0O000OO0 is not None :#line:575
                    if OOO0OO00OOOO0OO00 >0 :#line:576
                        OOO000O0OO0000O0O =O0O0OO0OO0O000OO0 /OOO0OO00OOOO0OO00 #line:577
                O0OOO0O00OOOOOOO0 =str (OOO00000OOOO0O000 )+';'+str (OO0O0O0O0OOO00O00 ['rule_id'])+';'+str (OO0O0O0O0OOO00O00 ['conf'])+';'+str (OO0O0O0O0OOO00O00 ['add_conf'])+';'+str (OO0O0O0O0OOO00O00 ['rq'])+';'+str (OO0O0O0O0OOO00O00 ['supp'])+';'+str (OO0O0O0O0OOO00O00 ['bothsidelift'])+';'+str (OO0O0O0O0OOO00O00 ['dbllift'])+';'+str (OO0O0O0O0OOO00O00 ['dblconf'])+';'+str (O0O0OOOO0O0O0O000 .clm_f .result ['rules'][OO0O0O0O0OOO00O00 ['rule_id']-1 ]['traces']['succ'][0 ][0 ])+';'+O0O0OOOO0O0O0O000 .clm_f .get_ruletext (OO0O0O0O0OOO00O00 ['rule_id'])#line:584
                O0OOO0O00OOOOOOO0 +=';'+str (OO00OOOO0000OO00O )+';'+str (OOO0OO00OOOO0OO00 )+';'+str (O0O0OO0OO0O000OO0 )+';'+str (OOO000O0OO0000O0O )+';'+str (sum (OOOOO0O0O0OO0OO0O ))#line:585
                OO0OO00OOO0O0O0OO .append (O0OOO0O00OOOOOOO0 )#line:586
        OO000OO00OO0O0000 =[1 if OOO0000O0OOO0OOO0 is None else 0 for OOO0000O0OOO0OOO0 in O0O0000OO0O00OOOO ]#line:589
        O0OOOOOOO00O0OO0O =sum (OO0O00O00OOOOO0OO is None for OO0O00O00OOOOO0OO in O0O0000OO0O00OOOO )#line:590
        if not (O0O0OOOO0O0O0O000 .is_multiclass ):#line:591
            O0OOO0OOOO00O0000 =None #line:592
            if O0O0OOOO0O0O0O000 .y_for_inner_eval is not None :#line:593
                O0OOO0OOOO00O0000 =0 #line:594
                for OOOOOOO0OO0O0O00O in range (len (O0O0000OO0O00OOOO )):#line:595
                    if O0O0000OO0O00OOOO [OOOOOOO0OO0O0O00O ]is None and O0O0OOOO0O0O0O000 .y_for_inner_eval .iloc [OOOOOOO0OO0O0O00O ]==O0O0OOOO0O0O0O000 .most_frequent_val :#line:596
                        O0OOO0OOOO00O0000 +=1 #line:597
            O0O0000OO0O00OOOO =[O0O0OOOO0O0O0O000 .backup_val if OOO00O0OO0OOOOOO0 is None else OOO00O0OO0OOOOOO0 for OOO00O0OO0OOOOOO0 in O0O0000OO0O00OOOO ]#line:598
        else :#line:599
            O0OOO0OOOO00O0000 =None #line:600
            if O0O0OOOO0O0O0O000 .y_for_inner_eval is not None :#line:601
                O0OOO0OOOO00O0000 =0 #line:602
                for OOOOOOO0OO0O0O00O in range (len (O0O0000OO0O00OOOO )):#line:603
                    if O0O0000OO0O00OOOO [OOOOOOO0OO0O0O00O ]is None and O0O0OOOO0O0O0O000 .y_for_inner_eval .iloc [OOOOOOO0OO0O0O00O ]==O0O0OOOO0O0O0O000 .most_frequent_val :#line:604
                        O0OOO0OOOO00O0000 +=1 #line:605
            O0O0000OO0O00OOOO =[O0O0OOOO0O0O0O000 .most_frequent_val if O00OOO00OOO000O0O is None else O00OOO00OOO000O0O for O00OOO00OOO000O0O in O0O0000OO0O00OOOO ]#line:606
        if O0O0OOOO0O0O0O000 .show_processing_details >=1 :#line:607
            print (f"....FALLBACK will apply in {O0OOOOOOO00O0OO0O}/{len(O0O0000OO0O00OOOO)} cases (out of them scored {O0OOO0OOOO00O0000} correctly.")#line:608
        if O0O0OOOO0O0O0O000 .show_csv_for_export :#line:611
            print ("Printing csv ...")#line:612
            print ("rule_id;applied_rule;conf;add_conf;rq_rule_quality;support;bothsidelift;dbllift;dblconf;CAT;ruletext;this_rule;additionally_scored;additional_successes;success_rate;total_coverage_of_the_rule")#line:613
            for OO0O0O00000OO0OOO in OO0OO00OOO0O0O0OO :#line:614
                print (OO0O0O00000OO0OOO )#line:615
        return O0O0000OO0O00OOOO ,OO000OO00OO0O0000 #line:618
    def predict_proba (O0OOOOO0OO00OO00O ,O0OOO0OOOOO0OO000 ,justvector =False ,include_also_fallback =False ,use_add_conf =True ):#line:620
        O00O000O000000000 ,O000O000O000OOOO0 =O0OOOOO0OO00OO00O ._get_vector (O0OOO0OOOOO0OO000 ,use_add_conf )#line:623
        if justvector :#line:625
            print ("FUTUREWARNING: justvector WILL BE REMOVED SOON.")#line:626
            if include_also_fallback :#line:627
                return O00O000O000000000 ,O000O000O000OOOO0 #line:628
            return O00O000O000000000 #line:629
        if O0OOOOO0OO00OO00O .is_multiclass :#line:632
            print ("Predict Probas not implemented for multiclass now")#line:633
            return None #line:635
        O00O0000O00OO00O0 =O00O000O000000000 #line:640
        OOO00OO000OOO0O0O =[1 -O000OOOOO0O0OO000 for O000OOOOO0O0OO000 in O00O0000O00OO00O0 ]#line:641
        O0O00OO00OOO0OO00 =[OOO00OO000OOO0O0O ,O00O0000O00OO00O0 ]#line:642
        O0OO00000O000OO0O =[[O000OO00OO0000O00 [O00000000O0OOO0O0 ]for O000OO00OO0000O00 in O0O00OO00OOO0OO00 ]for O00000000O0OOO0O0 in range (len (O0O00OO00OOO0OO00 [0 ]))]#line:644
        return np .array (O0OO00000O000OO0O )#line:648
    def _get_rule_scoring (O0OOOOO000000OO00 ,rule_id =None ,phase_is_fitting =False ,add_conf =None ):#line:650
        O0O0OOO0000O0O000 =O0OOOOO000000OO00 .clm_s #line:657
        if phase_is_fitting ==True :#line:659
            O0O0OOO0000O0O000 =O0OOOOO000000OO00 .clm_f #line:660
        O00OOO00OO0O0O000 =O0OOOOO000000OO00 .clm_f .result ['rules'][rule_id -1 ]#line:662
        O00O0OOOO00O0OO00 =O0OOOOO000000OO00 .clm_f .result ['datalabels']#line:668
        O00000OOO00OOO00O =O0OOOOO000000OO00 .clm_f .get_fourfold (rule_id )#line:672
        OOOO00OO000O00OO0 =0 #line:675
        if (O00000OOO00OOO00O [0 ]+O00000OOO00OOO00O [1 ])>0 :#line:676
            OOOO00OO000O00OO0 =O00000OOO00OOO00O [0 ]/(O00000OOO00OOO00O [0 ]+O00000OOO00OOO00O [1 ])#line:677
        O00O00OO0O0O000OO =O00OOO00OO0O0O000 ['trace_cedent_dataorder']['ante']#line:679
        O00O0O0OO000OOOO0 =O00OOO00OO0O0O000 ['traces']['ante']#line:680
        OOO0OO0O000OOOO00 =0 #line:681
        O00000OO0O0OOOOOO =O0O0OOO0000O0O000 .data ['rows_count']#line:682
        O0OO0O0OO0O00OO00 =2 **O00000OO0O0OOOOOO -1 #line:683
        O000O0O000OOOOO0O =O0OO0O0OO0O00OO00 #line:684
        for O00OO000O00O000O0 in O00O00OO0O0O000OO :#line:686
            O0O00O00OO00O0OO0 =O00O0O0OO000OOOO0 [OOO0OO0O000OOOO00 ]#line:688
            O0OO0OOOOOOO0O00O =O00OO000O00O000O0 #line:690
            if not (phase_is_fitting ):#line:691
                OOO0O0000O00OO000 =O0OOOOO000000OO00 .clm_f .result ['datalabels']['varname'][O00OO000O00O000O0 ]#line:692
                if not (OOO0O0000O00OO000 in O0OOOOO000000OO00 .clm_s .result ['datalabels']['varname']):#line:693
                    print (f"ERROR: variable {OOO0O0000O00OO000} is not present in dataset to score")#line:694
                    exit (1 )#line:695
                O0OO0OOOOOOO0O00O =O0OOOOO000000OO00 .clm_s .result ['datalabels']['varname'].index (OOO0O0000O00OO000 )#line:696
            OOO0OO0O000OOOO00 +=1 #line:698
            O00OO00O0OO0OO00O =0 #line:700
            OOO0000O00OO00O0O =0 #line:701
            for O0O00000O0O0000O0 in O0O00O00OO00O0OO0 :#line:702
                OO0OOOO000000O00O =O0O00000O0O0000O0 #line:704
                O0OOO0000OO0000O0 =False #line:705
                if not (phase_is_fitting ):#line:706
                    O00OOO0000O0OOOO0 =O0OOOOO000000OO00 .clm_f .result ['datalabels']['catnames'][O00OO000O00O000O0 ][O0O00000O0O0000O0 ]#line:707
                    if not (O00OOO0000O0OOOO0 in O0OOOOO000000OO00 .clm_s .result ['datalabels']['catnames'][O0OO0OOOOOOO0O00O ]):#line:708
                        print (f"WARNING: variable {OOO0O0000O00OO000}/category {O00OOO0000O0OOOO0} not in target data, will fix the situation.")#line:709
                        O0OOO0000OO0000O0 =True #line:710
                    else :#line:711
                        OO0OOOO000000O00O =O0OOOOO000000OO00 .clm_s .result ['datalabels']['catnames'][O0OO0OOOOOOO0O00O ].index (O00OOO0000O0OOOO0 )#line:712
                if not (O0OOO0000OO0000O0 ):#line:713
                    O00OO00O0OO0OO00O =O00OO00O0OO0OO00O |O0O0OOO0000O0O000 .data ['dm'][O0OO0OOOOOOO0O00O ][OO0OOOO000000O00O ]#line:714
                    OOO0000O00OO00O0O +=1 #line:715
            if OOO0000O00OO00O0O >0 :#line:716
                O000O0O000OOOOO0O =O000O0O000OOOOO0O &O00OO00O0OO0OO00O #line:717
        OOOOOO0OOO0OOO0OO =(2 **O00000OO0O0OOOOOO )+(O000O0O000OOOOO0O )#line:718
        OOOOOO00000O000O0 =[int (OO0OOOOO0OO00OO0O )for OO0OOOOO0OO00OO0O in bin (OOOOOO0OOO0OOO0OO )[2 :]][1 :]#line:720
        OO0O0O000O0O00O0O =None #line:722
        OOOOOO00OO0OO00O0 =None #line:723
        O00OOOOOOO0OO00OO =O00OOO00OO0O0O000 ['trace_cedent_dataorder']['succ'][0 ]#line:725
        O0O0OOO0OOOO0O0O0 =O00OOO00OO0O0O000 ['traces']['succ'][0 ][0 ]#line:726
        OO00OO0OO00OOO0O0 =O0OOOOO000000OO00 .clm_f .data ['dm'][O00OOOOOOO0OO00OO ][O0O0OOO0OOOO0O0O0 ]#line:728
        OOOOOO00OO0OO00O0 =O0OOOOO000000OO00 .clm_f .result ['datalabels']['catnames'][O00OOOOOOO0OO00OO ][O0O0OOO0OOOO0O0O0 ]#line:729
        OO0O0O000O0O00O0O =O0OOOOO000000OO00 .y_for_inner_eval #line:732
        OOOOOO00000O000O0 =[None if OO000OOO00OOOO0OO ==0 else OOOOOO00OO0OO00O0 for OO000OOO00OOOO0OO in OOOOOO00000O000O0 ]#line:735
        OOOOOO00000O000O0 .reverse ()#line:736
        if add_conf is None :#line:739
            OOOO00O00OO00OO0O =[None if OO00OOO0000OO0O00 ==0 else OOOO00OO000O00OO0 for OO00OOO0000OO0O00 in OOOOOO00000O000O0 ]#line:740
        else :#line:741
            OOOO00O00OO00OO0O =[None if O0O000OOOO0000O0O ==0 else add_conf for O0O000OOOO0000O0O in OOOOOO00000O000O0 ]#line:742
        O0OOOOO000000OO00 .check_full_structure ("_get_scoring:result:lst",OOOOOO00000O000O0 )#line:743
        O0OOOOO000000OO00 .check_full_structure ("_get_scoring:result:lst_conf",OOOO00O00OO00OO0O )#line:744
        O0OOOOO000000OO00 .check_full_structure ("_get_scoring:result:lst_TGT",OO0O0O000O0O00O0O )#line:745
        return OOOOOO00000O000O0 ,OOOO00O00OO00OO0O ,OO0O0O000O0O00O0O #line:747
    def getlabels (OOOOO0OO00O0O0O00 ):#line:752
        O000O000OO00O0O0O =[]#line:753
        for OOO00OOO000000OOO in range (len (OOOOO0OO00O0O0O00 )-1 ):#line:754
            OOO0OOO0OOOO000OO =OOO00OOO000000OOO +1 #line:755
            if (OOO0OOO0OOOO000OO ==1 ):#line:756
                O00O000OOO00OO0OO ='<'+str (OOOOO0OO00O0O0O00 [OOO00OOO000000OOO ])+','+str (OOOOO0OO00O0O0O00 [OOO00OOO000000OOO +1 ])+'>'#line:757
            else :#line:759
                O00O000OOO00OO0OO ='('+str (OOOOO0OO00O0O0O00 [OOO00OOO000000OOO ])+','+str (OOOOO0OO00O0O0O00 [OOO00OOO000000OOO +1 ])+'>'#line:760
            O000O000OO00O0O0O .append (O00O000OOO00OO0OO )#line:762
        return O000O000OO00O0O0O #line:766
