"""
Get Grobid output:
res1 = grobidPost('http://localhost:8070', 'api/processFulltextDocument', 'C:/home/pdf/my/files/sample1.pdf')

Get ScienceParse output:
import json
with open('C:/home/pdf/my/SP_Out/sample1.json', encoding="utf8") as f:
    res2 = json.load(f)
"""

import difflib


def compare_header(s1, s2):
    seq = difflib.SequenceMatcher(None, s1, s2)
    seq_ratio = seq.ratio()
    s1_num = ''.join(i for i in s1 if i.isdigit()).strip()
    s2_num = ''.join(i for i in s2 if i.isdigit()).strip()
    if seq_ratio > 0.9 and s1_num == s2_num:
        # both the number and the text need to be matched.
        return True
    else:
        return False


def combine(g, sp):
    # g is the output of grobid; sp is the output of science parse.
    out = {}
    # main text
    sec_g = processFulltext(g)['fulltext']
    sec_sp = sp['metadata']['sections']
    # unify header format
    for i in sec_g:
        header_old = i['header']
        header_new = header_old['number'] + header_old['text']
        i['header'] = header_new
    # find common sections
    sec_common = []
    for i in sec_g:
        for j in sec_sp:
            if compare_header(i['header'], j['heading']) is True:
                current_sec = {}
                current_sec['header'] = j['heading']
                current_sec['text'] = {'grobid': i['text'], 'sp': j['text']}
                sec_common.append(current_sec)
    # sections only find by grobid
    sec_only_g = []
    for i in range(len(sec_g)):
        c = 0
        for j in range(len(sec_common)):
            if compare_header(sec_g[i]['header'], sec_common[j]['header']) is True:
                break
            else:
                c += 1
        if c == len(sec_common):
            sec_only_g.append({'number': i, 'content': sec_g[i]})
    # sections only find by SP
    sec_only_sp = []
    for i in range(len(sec_sp)):
        c = 0
        for j in range(len(sec_common)):
            if compare_header(sec_sp[i]['heading'], sec_common[j]['header']) is True:
                break
            else:
                c += 1
        if c == len(sec_common):
            sec_only_sp.append({'number': i, 'content': sec_sp[i]})

    return {'sec_common': sec_common, 'sec_only_g': sec_only_g, 'sec_only_sp': sec_only_sp}


def combine_string(x):
    # x is the output of function 'combine'
    x1 = x['sec_common']
    out = []
    for i in x1:
        header = i['header']
        g = ''.join(i['text']['grobid'])  # from a list to a string
        sp = i['text']['sp']
        seq = difflib.SequenceMatcher(None, g, sp)
        seq_b = seq.get_matching_blocks()
        # get common text
        common = []
        for j in range(len(seq_b)):
            text = g[seq_b[j].a: seq_b[j].a+seq_b[j].size]
            common.append(text)
        # remove the last one which is always empty.
        common = common[0:-1]
        # get uncommon text between common text
        g_only = []
        sp_only = []
        for k in range(len(seq_b)-1):
            text_g = g[seq_b[k].a+seq_b[k].size: seq_b[k+1].a]
            text_sp = sp[seq_b[k].b+seq_b[k].size: seq_b[k+1].b]
            g_only.append(text_g)
            sp_only.append(text_sp)
        # add text before the first commom part
        g_only = [g[0: seq_b[0].a]] + g_only
        sp_only = [sp[0: seq_b[0].b]] + sp_only
        # remove short non-similar part (length less than 5)
        # link the similar part with the shorter one.
        rem = []
        # find indices of elements to remove
        for n in range(len(g_only)):
            len_g = len(g_only[n])
            len_sp = len(sp_only[n])
            if len_g <= 5 and len_sp <= 5 and len_g+len_sp != 0:
                # 'len_g + len_sp != 0' skip the first and last ''
                if len_g <= len_sp:
                    rem.append([n, 'g'])
                else:
                    rem.append([n, 'sp'])
        # link common parts and fill the space with 'Del'
        for x in rem:
            num = x[0]
            if x[1] == 'g':
                text = g_only[num]
                common = common[0:num-1] + ['Del'] + [common[num-1] + text + common[num]] + common[num+1:]
            else:
                text = sp_only[num]
                common = common[0:num-1] + ['Del'] + [common[num-1] + text + common[num]] + common[num+1:]
        # delete 'Del'
        common = list(filter(lambda a: a != 'Del', common))
        # remove elements in g_only and sp_only
        rem_indices = [i[0] for i in rem]
        g_only = [i for j, i in enumerate(g_only) if j not in rem_indices]
        sp_only = [i for j, i in enumerate(sp_only) if j not in rem_indices]
        out.append({'header': header, 'common': common, 'g_only': g_only, 'sp_only': sp_only, 'rem': rem})
    return out


# test function combine_string:
def test_com_str(l):
    x = 0
    for i in l:
        if len(i['common'])+1 == len(i['g_only']):
            x += 1
    if x == len(l):
        return 'Pass'
    else:
        return 'Fail'


