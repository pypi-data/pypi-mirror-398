import sys #line:2
from cleverminer import cleverminer #line:4
def actplusminer (clm =None ,rule_id =None ,ante_flex =None ,succ_flex =None ,quantifiers =None ,show_definition =False ):#line:7
    ""#line:21
    if clm ==None or rule_id ==None or (ante_flex ==None and succ_flex ==None ):#line:23
        print ("ERROR: Mandatory parameter is missing")#line:24
        exit (1 )#line:25
    if not (clm .result ['taskinfo']['task_type']=='4ftMiner'):#line:26
        print (f"ERROR: ACTPLUSMINER is based on iteration of 4ftMiner. {clm.result['taskinfo']['tasktype']} is provided instead.")#line:27
    if 'cond'in clm .result ['taskinfo']:#line:28
        print ("ERROR: ACTPLUSMINER does not support conditions now.")#line:29
        exit (1 )#line:30
    if not (clm .result ['taskinfo']['ante']['type']=='con'and clm .result ['taskinfo']['succ']['type']=='con'):#line:31
        print ("ERROR: ACTPLUSMINER supports only conjunctions in antecedent and succedent.")#line:32
        exit (1 )#line:33
    if clm .df is None :#line:34
        print ("ERROR: dataframe is missing.Please provide a clm class with calculated result and dataframe available (use opts = {'use_cache':True,'keep_df':True} in the original cleverminer call).")#line:35
        exit (1 )#line:36
    O000OOOO00OOO0OOO =clm .result ['rules'][rule_id -1 ]#line:37
    O00OOOO000OO000O0 =clm .result ['datalabels']#line:38
    O000O0O000O000000 =clm .get_fourfold (rule_id )#line:39
    def O0O0000O00OOOOOO0 (OOO00O00OOOOOOOO0 ,OOOO0OO0OO000O0O0 ):#line:41
        O00OO00000OOOOO0O =False #line:42
        for OOOO0OOO00OOO00OO in OOOO0OO0OO000O0O0 :#line:43
            if OOOO0OOO00OOO00OO ['name']==OOO00O00OOOOOOOO0 :#line:44
                O00OO00000OOOOO0O =True #line:45
                return O00OO00000OOOOO0O ,OOOO0OOO00OOO00OO #line:46
        return O00OO00000OOOOO0O ,None #line:47
    OOOOOOO000OOO0OOO ={}#line:49
    OOOOOOO000OOO0OOO ['cond']=[]#line:50
    if ante_flex is None :#line:51
        OOOOOOO000OOO0OOO ['ante']=[]#line:52
    else :#line:53
        OOOOOOO000OOO0OOO ['ante']=ante_flex #line:54
    if succ_flex is None :#line:55
        OOOOOOO000OOO0OOO ['succ']=[]#line:56
    else :#line:57
        OOOOOOO000OOO0OOO ['succ']=succ_flex #line:58
    OO000OO0000OO0O00 =O000OOOO00OOO0OOO ['trace_cedent_dataorder']#line:60
    O0OO0OOO0O0OOO0O0 =O000OOOO00OOO0OOO ['traces']#line:61
    O000OO000000O00OO =['cond','ante','succ']#line:62
    OOOOO000O0OO0O0OO ={}#line:64
    for O0O0OOO000O00OOO0 in O000OO000000O00OO :#line:66
        O0OO0000O0OOOOOOO =OO000OO0000OO0O00 [O0O0OOO000O00OOO0 ]#line:67
        O000OO00OO0OO00O0 =O0OO0OOO0O0OOO0O0 [O0O0OOO000O00OOO0 ]#line:68
        OOOO00OOO0OOO0O0O =[]#line:69
        OOOO00OO0OOO0OOOO =0 #line:70
        OOOOO00O00O0O0000 =0 #line:71
        for O00O0OO00OO0O0O00 in range (len (O0OO0000O0OOOOOOO )):#line:72
            OOOO00OO0OOO0OOOO +=1 #line:73
            OOOO000OO0OOOOO00 =O0OO0000O0OOOOOOO [O00O0OO00OO0O0O00 ]#line:74
            OOOOO0OOO000OOOOO =O00OOOO000OO000O0 ['varname'][OOOO000OO0OOOOO00 ]#line:75
            O000000OO0O000O0O ,O0000000OOOOO0OO0 =O0O0000O00OOOOOO0 (OOOOO0OOO000OOOOO ,OOOOOOO000OOO0OOO [O0O0OOO000O00OOO0 ])#line:76
            if O000000OO0O000O0O :#line:77
                OOOO00OOO0OOO0O0O .append (O0000000OOOOO0OO0 )#line:78
            else :#line:79
                OOOOO00O00O0O0000 +=1 #line:80
                O0O00O00O00O00OOO ={}#line:81
                O0O00O00O00O00OOO ['name']=OOOOO0OOO000OOOOO #line:82
                O0O00O00O00O00OOO ['type']='list'#line:83
                O0O00O00O00O00OOO ['force']=True #line:84
                OO0O0000O00O00O0O =O00OOOO000OO000O0 ['catnames'][OOOO000OO0OOOOO00 ]#line:85
                O00OOO0OOOOOOO000 =[]#line:86
                for OO000O00000O00000 in O000OO00OO0OO00O0 [O00O0OO00OO0O0O00 ]:#line:87
                    O00OOO0OOOOOOO000 .append (OO0O0000O00O00O0O [OO000O00000O00000 ])#line:88
                O0O00O00O00O00OOO ['value']=O00OOO0OOOOOOO000 #line:89
                OOOO00OOO0OOO0O0O .append (O0O00O00O00O00OOO )#line:90
        if show_definition :#line:91
            print (f"SHOWING DEFINITION OF CEDENT : cedent {O0O0OOO000O00OOO0}, definition {OOOO00OOO0OOO0O0O}, minlen {OOOO00OO0OOO0OOOO}, maxlen {cnt}")#line:92
        OOO0OO0OOO0O0OOOO ={}#line:93
        OOO0OO0OOO0O0OOOO ['attributes']=OOOO00OOO0OOO0O0O #line:94
        OOO0OO0OOO0O0OOOO ['minlen']=OOOO00OO0OOO0OOOO #line:95
        OOO0OO0OOO0O0OOOO ['maxlen']=OOOO00OO0OOO0OOOO #line:96
        OOO0OO0OOO0O0OOOO ['type']='con'#line:97
        OOOOO000O0OO0O0OO [O0O0OOO000O00OOO0 ]=OOO0OO0OOO0O0OOOO #line:98
    O000O0OOO00O0OO0O ={}#line:101
    for OO0O0OO0O0O0OO00O in quantifiers .keys ():#line:102
        O000O0OOO00O0OO0O [OO0O0OO0O0O0OO00O .lower ()]=quantifiers [OO0O0OO0O0O0OO00O ]#line:103
    O0O0000OOO0OOOOO0 =0 #line:105
    if 'confratio'in O000O0OOO00O0OO0O :#line:107
        O0O0000OOO0OOOOO0 =O000O0OOO00O0OO0O ['confratio']#line:108
    O0O0000OOO0O0O0OO =sys .maxsize #line:110
    if 'confratio_leq'in O000O0OOO00O0OO0O :#line:112
        O0O0000OOO0O0O0OO =O000O0OOO00O0OO0O ['confratio_leq']#line:113
    def OO0O00OOOOOO0OOOO (O0OOO0OOO000O00OO ):#line:115
        OOO0O0OO00OOO0OO0 =O0OOO0OOO000O00OO [0 ]/(O0OOO0OOO000O00OO [0 ]+O0OOO0OOO000O00OO [1 ])/O000O0O000O000000 [0 ]*(O000O0O000O000000 [0 ]+O000O0O000O000000 [1 ])#line:116
        if (OOO0O0OO00OOO0OO0 >=O0O0000OOO0OOOOO0 )and (OOO0O0OO00OOO0OO0 <=O0O0000OOO0O0O0OO ):#line:117
            return True #line:118
        return False #line:119
    OOOO00O0OO00000O0 =quantifiers #line:121
    OOOO00O0OO00000O0 ['lambda']=OO0O00OOOOOO0OOOO #line:123
    OO0O0OO000O0OO0O0 =cleverminer (df =clm .df ,proc ='4ftMiner',quantifiers =OOOO00O0OO00000O0 ,ante =OOOOO000O0OO0O0OO ['ante'],succ =OOOOO000O0OO0O0OO ['succ'])#line:125
    return OO0O0OO000O0OO0O0 #line:127
