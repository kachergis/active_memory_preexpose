import json
import pandas as pd
import numpy as np
from sqlalchemy import *
#from mypy.datautil import download_data_from_mysqldb

DATADIR = '/Users/george/active_memory_preexpose/analysis/data'
def spath(sid):
    return '%s/%s.json' % (DATADIR, sid)

FIGDEST = '/Users/george/active_memory_preexpose/analysis/figures'

##########################################
# Data from mysql database
##########################################
def download_data_from_mysqldb(dburl, tablename):
    versionname = ''
    engine = create_engine(dburl)
    metadata = MetaData()
    metadata.bind = engine
    table = Table(tablename, metadata, autoload=True)
    s = table.select()
    rs = s.execute()
    data = []
    for row in rs:
        data.append(row)
    df = pd.DataFrame(data, columns=table.columns.keys())
    return df

dburl = "mysql://lab:fishneversink@gureckislab.org/mt_experiments"
tablename = "activemem"
datacolumn = "datastring"
df_all = download_data_from_mysqldb(dburl, tablename)

# save datastring to separate files
for i, r in df_all.iterrows():
    if r['datastring']!=None:
        with open(spath(r['workerid']), 'w') as f:
            f.write(r['datastring'])

# subject ids should be same as workerid in the table
SUBJ = ['11', '017', '18', '26', '27', '28', '29', '31', '33', '34', '36', '41', \
        '45', '46', '47', '48', '55', '56', '57', '58', '110', '111', '113', '115', '211', '213', \
        '215', '410','411','413','415','510','511','513','1000','1058','1061','1065',\
       '1071','1075','1076','1081','1082','1086','1091','1095','1097','1101','1105','1106','1107',\
       '1112','1115','1116','1117','1122','1126','1127','1131','1135','1137','10613','10615','10617',\
       '10710','10715','10717','10718','10811','10813','10817','10910','10911','10915','10917','10918',\
       '11010','11011','11013','11111','11115','11117','11210','11211','11213','11215','11217','11218',\
       '11310','11313','11317','11318'] 
# '1065-retest', '10811-retest' ..a few with weird names (A3GDTSFHVBUJHD), and some tests
print len(SUBJ) # 92


def data(sid):
    try:
        with open('/Users/george/active_memory_preexpose/analysis/data/%s.json' % sid, 'r') as f:
            lines = f.read()
        data = json.loads(lines)
        trialdata = [d['trialdata'] for d in data['data']]
        return trialdata
    except:
        return None

# nobody has a partnerid in the preexpose study
#def partnerid(sid):
#    return filter(lambda d: d[0]=='partnerid', data(sid))[0][1]

# just grabs the item id..?
def item_map(sid, block):
    items = filter(lambda d: d[0]=='study' and d[1]==block and d[3]=='item', data(sid))
    return dict([map(int, [it[5].lstrip('ind='), it[4].lstrip('id=')]) for it in items])
# where each item in a study block is: {0: 131, 1: 129, 2: 27, 3: 71, 4: 133, 5: 142, 6: 132, 7: 44}

def studyseq_locations(sid, block):
    studied = filter(lambda d: d[0]=='study' and d[1]==block and d[3].count('item-') > 0 and d[4]=='study', data(sid))
    locs = map(int, [ep[3].lstrip('item-') for ep in studied])
    return locs

# want an array of the seuqnece of study items -- with times
def get_studyseq(sid, block):
    # 'subject', 'block', 'preexpose', 'item', 'index', 'startt', 'stopt', 'duration', 'id'
    # [u'study', 2, u'all', u'item-4', u'episode', 18216, 18589, 373]
    print str(sid) + " " + str(block)
    m = item_map(sid, block) # {0: 127, 1: 32, 2: 84, 3: 100, 4: 108, 5: 53, 6: 51, 7: 68}
    studied = filter(lambda d: d[0]=='study' and d[1]==block and d[3].count('item-') > 0 and d[4]=='episode', data(sid))
    arr = []
    index = 0
    bl = 0
    for st in studied:
        if bl==st[1]:
            index += 1
        else:
            bl += 1
            index = 1
        st[0] = sid
        st[3] = st[3].lstrip('item-')
        st[4] = index
        st.append(m[int(st[3])])
        arr.append(st)
    #locs = map(int, [ep[3].lstrip('item-') for ep in studied])
    return arr

def studyseq_items(sid, block):
    m = item_map(sid, block)
    return [m[loc] for loc in studyseq_locations(sid, block)]

# data(sid)[2]
# [u'preexpose', [u'left', u'right', u'all']]
# studyseq_locations('11', 0) 0,1,2 = gives sequence of locations that they studied during that block
#  e.g. [5, 4, 0, 1, 2, 3]   would like to extract the time each item is exposed, too...

# studyseq_items('11',0) picture numbers (not locations):
# [131, 129, 27, 133, 131, 129, 27, 71, 142, 133, 142, 44, 133, 142, 44, 132, 129, 131, 129]

preexpose_inds = {'left':[0,1,4,5], 'right':[2,3,6,7], 'all':[0,1,2,3,4,5,6,7]}

def studieditems(sid, block):
    return list(np.unique(studyseq_items(sid, block)))

# change to n_preexposed_items_studied
def n_active_items_studied(sid):
    """Across both active blocks, find proportion of items that chosen for study."""
    preexp_ord = data(sid)[2][1] # e.g., ['left','all','right']
    # intersect studyseq_locations(sid, 0) and preexpose_inds[preexp_ord[0]]
    # (and do the same for blocks 1 and 2)
    return (len(studieditems(sid, 0)) + len(studieditems(sid, 2)))

def proportion_active_items_studied(sid):
    """Across both active blocks, find proportion of items that chosen for study."""
    return n_active_items_studied(sid)/24.

def testdata(sid):
    return filter(lambda tr: tr[0]=='test' and len(tr)==8 and tr[2]!='item', data(sid))

def get_testdata(sid):
    T = testdata(sid)
    arr = []
    # [u'test', 3, 11, 127, False, u'new', u'old', False]
    for td in T:
        td[0] = sid
        arr.append(td)
    return arr

def test_scores(sid):
    T = testdata(sid)
    hits_active = 0
    hits_yoked = 0
    misses_active = 0
    misses_yoked = 0
    fa = 0
    cr = 0
    for td in T:
        print td
        if td[5]=='active':
            if td[6]=='old':
                hits_active += 1
            else:
                misses_active += 1
        elif td[5]=='yoked':
            if td[6]=='old':
                hits_yoked += 1
            else:
                misses_yoked += 1
        else:
            if td[6]=='old':
                fa += 1
            else:
                cr += 1
    return [hits_active, misses_active, hits_yoked, misses_yoked, fa, cr]

def test_scores_studied(sid):
    items = []
    for block in range(4):
        items += studieditems(sid, block)
    td = filter(lambda d: d[3] in items, testdata(sid))
    active_resp = 1*np.array([x[-1] for x in filter(lambda d: d[5]=='active', td)])
    yoked_resp = 1*np.array([x[-1] for x in filter(lambda d: d[5]=='yoked', td)])
    return [np.sum(active_resp==1), np.sum(active_resp==0), active_resp.mean(), np.sum(yoked_resp==1), np.sum(yoked_resp==0), yoked_resp.mean()]

# def retest_scores(sid):
#     if data('%s-retest' % sid) == None:
#         return [np.nan for _ in range(6)]
#     else:
#         return test_scores('%s-retest' % sid)


# old (doug's study)
# arr = []
# for sid in SUBJ:
#     arr.append([sid] + [str(df_all[df_all.workerid==sid]['beginhit'].values[0]).split('T')[0]] + test_scores(sid) + retest_scores(sid) + [n_active_items_studied(sid), proportion_active_items_studied(sid)])
# df = pd.DataFrame(arr, columns=['subj', 'date', 'H_active', 'M_active', 'H_yoked', 'M_yoked', 'FA', 'CR', 'T2_H_active', 'T2_M_active', 'T2_H_yoked', 'T2_M_yoked', 'T2_FA', 'T2_CR', 'nStudiedActive', 'propStudiedActive'])
# df['T1_diff'] = df['H_active'] - df['H_yoked']
# df['T2_diff'] = df['T2_H_active'] - df['T2_H_yoked']
# df.to_csv('results.csv')

# from task.js:
# output(['item', 'id='+self.stimid, 'ind='+self.ind, 'row='+self.row, 'col='+self.col, 'image='+self.img, 'preexpose='+self.preexposed]);
# output([self.id, 'episode', self.episode['start_time'], self.episode['end_time'], self.episode['duration']]);
# test: output([i, ti['ind'], ti['studied'], ti['cond'], resp, correct ])

arr = []
for sid in SUBJ:
    arr = arr + get_testdata(sid)

df = pd.DataFrame(arr, columns=['subj', 'block','index', 'item', 'studied', 'cond', 'response', 'correct'])
df.to_csv('test_trials.csv')


sarr = []
for sid in SUBJ:
    for bl in range(3):
        sarr = sarr + get_studyseq(sid, bl)
sdf = pd.DataFrame(sarr, columns=['subj', 'block', 'preexpose', 'item', 'index', 'startt', 'stopt', 'duration', 'id'])
sdf.to_csv('study_trials.csv')

studlocs = []
for sid in SUBJ:
    for bl in range(3):
        tmp = item_map(sid, bl)
        for loc, item in tmp.iteritems():
            studlocs.append([sid, bl, loc, item])
sdf = pd.DataFrame(studlocs, columns=['subj', 'block', 'loc', 'item'])
sdf.to_csv('study_locations.csv')

# new -- preexpose; no partner, no yoked vs. active...now have preexpose left/right/all, 
arr = []
for sid in SUBJ:
    arr.append([sid] + [str(df_all[df_all.workerid==sid]['beginhit'].values[0]).split('T')[0]] + test_scores(sid) + [n_active_items_studied(sid), proportion_active_items_studied(sid)])
df = pd.DataFrame(arr, columns=['subj', 'date', 'H_active', 'M_active', 'H_yoked', 'M_yoked', 'FA', 'CR', 'nStudiedActive', 'propStudiedActive'])
df['T1_diff'] = df['H_active'] - df['H_yoked']
df['T2_diff'] = df['T2_H_active'] - df['T2_H_yoked']
df.to_csv('results.csv')


