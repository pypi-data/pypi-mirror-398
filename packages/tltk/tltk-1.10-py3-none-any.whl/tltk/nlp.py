#!/usr/bin/python
# -*- coding: utf-8 -*-
#########################################################
## Thai Language Toolkit : version  1.10
## Chulalongkorn University
## word_segmentation, syl_segementation written by Wirote Aroonmanakun
## Implemented :
##      WordAna, TextAna, TNC_tag, TextAna2json, MaltParser, MaltParser_wordlist, print_dtree
##      chunk, ner_tag, segment, word_segment, syl_segment, word_segment_mm, word_segment_nbest,
##      g2p, th2ipa, th2roman, th2ipa_all, spell_variants, pos_tag, pos_tag_wordlist, 
##      read_thaidict, reset_thaidict, check_thaidict
##      spell_candidates, spoonerism
##      th2read, syl_type
#########################################################

from pydoc import allmethods
import re
import math
import os
import bz2
import json
import sys
from copy import deepcopy
from collections import defaultdict
from itertools import product
import pandas as pd


#import pkg_resources
import pickle
#import gzip
from nltk.tag.perceptron import PerceptronTagger
from nltk.parse import malt


from sklearn.ensemble import RandomForestClassifier
from sklearn.feature_extraction import DictVectorizer
from sklearn.pipeline import Pipeline

from sklearn_crfsuite import CRF

import statistics

##########################################################
## Read Dictionary in a text format one word per one line
##########################################################
def read_thaidict(Filename):
    global TDICT
#    ATA_PATH = pkg_resources.resource_filename('tltk', '/')

    if not os.path.exists(Filename):
        path = os.path.abspath(__file__)
        ATA_PATH = os.path.dirname(path)
        Filename = ATA_PATH + '/' + Filename
    file1 = open(Filename, 'r')
    for line in  file1:
        w = line.rstrip()
        w = re.sub(r'\.','\\\.',w)
        TDICT[w] = 1
    return(1)

def read_thdict(Filename):
    global TDICT
    fileObject = open(Filename,'rb')  
    TDICT = pickle.load(fileObject)


##########################################################
## Clear Dictionary in a text format one word per one line
##########################################################
def reset_thaidict():
    global TDICT
    TDICT.clear()
    return(1)

#### Check whether the word existed in the dictionary 
def check_thaidict(Word):
    global TDICT
    if Word in TDICT:
        return(1)
    else:
        return(0)
    


####################################################################
##  spelling correction modified from Peter Norvig  http://norvig.com/spell-correct.html
####################################################################

#def P(word, N=sum(TDICT.values())):
#    global TDICT
#    "Probability of `word`."
#    return TDICT[word] / N

#def spell_correction(word): 
#    "Most probable spelling correction for word."
#    return max(candidates(word), key=P)

def spell_candidates(word): 
#    return (known([word]) or known(edits1(word)) or known(edits2(word)) )
    return ( known(edits1(word)) )

def known(words):
    global TDICT
    return list(w for w in words if w in TDICT)

def edits1(word):
#    letters    = 'abcdefghijklmnopqrstuvwxyz'
    letters = [chr(i) for i in range(ord('ก'),ord('์')+1)]
    splits     = [(word[:i], word[i:])    for i in range(len(word) + 1)]
    deletes    = [L + R[1:]               for L, R in splits if R]
    transposes = [L + R[1] + R[0] + R[2:] for L, R in splits if len(R)>1]
    replaces   = [L + c + R[1:]           for L, R in splits if R for c in letters]
    inserts    = [L + c + R               for L, R in splits for c in letters]
    return list(deletes + transposes + replaces + inserts)

def edits2(word): 
    return list(e2 for e1 in edits1(word) for e2 in edits1(e1))

########################################################################
##  UD Parser
##  MaltParser(text)
##     return dict { 'sentence':........  'words': [ {id,form,pos,deprel,head} , ..... ]  }
##  thamalt.mco is created from this command
# >java -jar maltparser-1.9.2.jar -c thamalt -i train.conllu -m learn
########################################################################

def match_Engtext(text):
    # Define a regular expression pattern to match English letters, numbers, and symbols
    if re.match(r"^[a-zA-Z0-9 \"\'\(\)#$%&*++,-./:;<=>?@\[\\\]\^_`{\|}\~]+$", text):
        return True
    else:
        return False


from nltk.parse import malt
import warnings
warnings.filterwarnings("ignore", message="The graph doesn't contain a node that depends on the root element")


def MaltParser(txt):
    global Maltparser_Path
    if match_Engtext(txt): return('')
    try:
        path = os.path.abspath(__file__)
        ATA_PATH = os.path.dirname(path)
        mp = malt.MaltParser(parser_dirname=Maltparser_Path, model_filename=ATA_PATH+'/thamalt.mco')
        lst = pos_tag(txt)
        parsed_trees = mp.parse_tagged_sents(remove_sp_join(lst))
        dg = next(next(parsed_trees))
#        print(dg)
        dtree = dg_save(dg,txt)
        return(dtree)

    except NameError:
        print('Install MaltPaser (https://www.maltparser.org/) and add its directory to the variable "Maltparser_Path" in your code before using MaltParser(), e.g.')
        print('tltk.nlp.Maltparser_Path = "/path/to/maltparser-1.9.2"')
        sys.exit()

def MaltParser_wordlist(wlst):
    global Maltparser_Path
    wlst = [item.replace(" ", "") for item in wlst]   ##remove space in an item
#    print(wlst)
    if match_Engtext(' '.join(wlst)): return('')  ## check whether the whole sent is English

    try:
        path = os.path.abspath(__file__)
        ATA_PATH = os.path.dirname(path)
        mp = malt.MaltParser(parser_dirname=Maltparser_Path, model_filename=ATA_PATH+'/thamalt.mco')
        lst = pos_tag_wordlist(wlst)
        parsed_trees = mp.parse_tagged_sents(remove_sp_join([lst]))
        dg = next(next(parsed_trees))
        dtree = dg_save(dg,''.join(wlst))
        return(dtree)

    except NameError:
        print('Install MaltPaser (https://www.maltparser.org/) and add its directory to the variable "Maltparser_Path" in your code before using MaltParser(), e.g.')
        print('tltk.nlp.Maltparser_Path = "/path/to/maltparser-1.9.2"')
        sys.exit()

## remove last element in every list (<s/>,PUNCT) and join into one list
def remove_sp_join(lst):
    newlst = []
    for x in lst:
#        if ('<s/>','PUNCT') in x:
#            x.remove(('<s/>','PUNCT'))
        for y in x:
            if y == ('<s/>','PUNCT') or y[0] == '' or y[0] == ' ' or '\t' in y[0]:
#            if y == ('<s/>','PUNCT') or y[0] == '':
                continue
            else:
                newlst.append(y)    
#        newlst.extend(x)
    return([newlst])  

## return list of object (rel,wordd/pos-i, wordh/pos-j)      
def dg_print(dg):
    wrd = {}
    result = []
    dg.nodes[0]['word'] = "root"
    for node in dg.nodes:
        wrd[node] = dg.nodes[node]['word']+'/'+dg.nodes[node]['tag']
    for node in dg.nodes:
        if node >= 1:
            wd = dg.nodes[node]['word']+'/'+dg.nodes[node]['tag']
            hd = dg.nodes[node]['head']
            rel = dg.nodes[node]['rel']
            result.append( (rel,wd+'-'+str(node),wrd[hd]+'-'+str(hd)))
    return(result)

#### return dict {'sentence' = ....., 'words'= [ {id,form,pos,head,deprel}, ..... ]}
def dg_save(dg,txt):
    ud = {}
    ud["sentence"] = txt
    ud["words"] = []
    dg.nodes[0]['word'] = "root"
    for node in dg.nodes:
        wrd = {}
        wrd['id'] = node
        wrd['form'] = dg.nodes[node]['word']
        wrd['pos'] = dg.nodes[node]['tag']
        wrd['head'] = dg.nodes[node]['head']
        wrd['deprel'] = dg.nodes[node]['rel']
        ud['words'].append(wrd)
    return(ud)

### print dict of d-tree
def print_dtree(ud_parse):
    global PRN_TREE
    PRN_TREE = []
    scan_dtree(ud_parse, node=0, level=0)
    for a in sorted(PRN_TREE, key=lambda k: k['id']):
        print(str(a['id'])+':'+a['msg'])

def scan_dtree(ud_parse, node=0, level=0):
    """
    Scan a d-tree for the Universal Dependencies parse in the given dictionary.
    Args:
    - ud_parse (dict): A dictionary containing the Universal Dependencies parse of a sentence.
    - node (int): The ID of the current node in the parse tree (default: 0 for the root node).
    - level (int): The current level or depth in the parse tree (default: 0 for the root level).
    output is save in PRN_TREE
    """
    # Get the current word dictionary from the UD parse.
    global PRN_TREE
    global D_DEPTH
    current_word = None
    for word in ud_parse["words"]:
        if word['id'] == node:
            current_word = word
            break
    if node > 0 :
    # Save each word and its syntactic properties in PRN_TREE.
        x = {'id' : node,  'msg' :  
        str('--' * level + current_word['form'] + ' (' + current_word['pos'] + ', ' + current_word['deprel'] + ' - ' + str(current_word['head']) + ')') }
        PRN_TREE.append(x)
#        if level > D_DEPTH : D_DEPTH = level
    # Recursively print the d-tree for each of the children of the current word.
    for word in ud_parse['words']:
        if word['head'] == node:
            scan_dtree(ud_parse, node=word['id'], level=level+1)

## get the depth starting from word_id
def get_tree_depth(ud_parse, word_id):
    # find the word in the list of words
    word = next((w for w in ud_parse['words'] if w['id'] == word_id), None)
    if word is None:
        return 0
    
    # if the word has no dependents, return 1
    if not any(w['head'] == word_id for w in ud_parse['words']):
        return 1
    
    # find the maximum depth of the dependents
    max_depth = 0
    for w in ud_parse['words']:
        if w['head'] == word_id:
            depth = get_tree_depth(ud_parse, w['id'])
            if depth > max_depth:
                max_depth = depth
    
    # add 1 to the maximum depth and return it
    return max_depth + 1

### get the maximum depth of ud_tree
def tree_max_depth(ud_parse):
    max_depth = 0
    for word in ud_parse['words']:
        if word['id'] > 0:
            depth = get_tree_depth(ud_parse, word['id'])
#        print(f"Depth of word '{word['form']}' is {depth}")
            if depth > max_depth:
                max_depth = depth
    return(max_depth)

##########################################################################
## POS tagging using nltk.tag.perceptron
#########################################################################
def pos_tag(Input,Option="colloc"):
    global tagger
    results = []
    if Option == 'mm':
        out = word_segment(Input,"mm")
    elif Option == 'ngram':    
        out = word_segment(Input,"ngram")
    else: 
        out = word_segment(Input)
    try:
      tagger
    except NameError:
      pos_load()
#    print('worsseg in pos tag',out)
    for x in out.split('<s/>'):
        tag_result = []
        if x != '':
            sent = x.split('|')
            if '' in sent:
                sent.remove('')
            for (w,pos) in tagger.tag(sent):
                if w == ' ':
                    w = '<s/>'    
                pos = change_tag(w,pos)
                tag_result.append((w,pos))
            tag_result.append(('<s/>','PUNCT'))    
            results.append(tag_result)
    return(results)

## pos tag on a list of words  [w1,w2,w3,...]
def pos_tag_wordlist(sent):
    global tagger
    try:
      tagger
    except NameError:
      pos_load()
    results = []
    for (w,pos) in tagger.tag(sent):
        pos = change_tag(w,pos)
        results.append((w,pos))    
    return(results)

def pos_load():
    global tagger
    tagger = PerceptronTagger(load=False)
    path = os.path.abspath(__file__)
    ATA_PATH = os.path.dirname(path)

    f = bz2.BZ2File(ATA_PATH +'/' + 'pos_tagger.pklz','rb')
    tagger = pickle.load(f)

#    filehandler = open(ATA_PATH +'/' + 'pos_tagger.pick', 'rb') 
#    tagger = pickle.load(filehandler)

def change_tag(w,pos):
    if re.match(r'[\#\+\-\_\=\*\&\^\%\$\@\}\{\]\[\<\>\/]$',w):
        pos = 'SYM'
    elif re.match(r'[\,\;\:\.\(\)\'\"\!\?]$',w):
        pos = 'PUNCT'
    elif re.match(r'[0-9][0-9.,\+\-\*\/]*$',w):
        pos = 'NUM'
    elif re.match(r'<s/>$',w):
        pos = 'PUNCT'        
    elif re.match(r'[\<\>a-zA-Z\/]+$',w):
        pos = 'SYM'        
    elif re.match(r'[a-zA-Z0-9_]+$',w):
        pos = 'X'
    return(pos)


###############################################################################################
### chunk parse  =  segment edu + word segment + pos tag + (ner)
### Input = Thai text
###
def chunk(txt):
    global SegSep
    global SSegSep
    global useg_model
    global tagger
    outs = ""
    out = ""
#    print(txt)
    ## do syllable segmentation
    sylseg = syl_segment(txt)
    sylseg = re.sub(' ','<s/>',sylseg)
    sylseg = re.sub(r'([^~])<s/>',r'\1~<s/>',sylseg)
    sylseg = re.sub(r'<s/>([^~])',r'<s/>~\1',sylseg)

    sylcopy = sylseg
    sylcopy = re.sub(r'~[0-9\.\,]+~','~DIGIT~',sylcopy)
    sylcopy = re.sub(r'~[a-zA-Z0-9\\\/\?\'\"\(\)\.]+~','~FOREIGN~',sylcopy)

    parcopy = sylcopy.split('~')
    par = sylseg.split('~')
#    print(sylcopy)
    ## do edu segmentation
    try:
      useg_model
    except NameError:
      useg_model_load()

    tags = useg_model.predict([features(parcopy, index) for index in range(len(par))])
    lst_tag = zip(par,tags)
    syl_seq = ''
    for (w,t) in lst_tag:
        if t == '<u/>':
            ## do word segmentation
            out = wordseg_colloc(syl_seq)
            ## do pos tagging
            try:
              tagger
            except NameError:
              pos_load()        
            tag_result = []
            if out != '':
                sent = out.split('|')
                ## remove all '' from sent
                sent = list(filter(lambda a: a != '', sent))
                for (w,pos) in tagger.tag(sent):
                    pos = change_tag(w,pos)
                    ## do ner tagging
                    tag_result.append((w,pos))
                out = pack_ner(ner(tag_result))
                outs += out
            syl_seq = ''
            outs += '<u/>'
        else:
            syl_seq += w+'~'
    ### make a correction on dd|</s>/NUM => dd/NUM|</s>/PUNCT        
    outs = re.sub(r"([0-9])<s/>/NUM",r"\1/NUM|<s/>/PUNCT",outs)        
    return(outs)
    
###############################################################################################
### NER extraction 
### Input = Thai text   Option is for selecting word segmentation method
### Output = word/pos with <NE> tags
def ner_tag(Input,Option="colloc"):
    out = ""

    tag_result = []
    ner_result = []
    for lst in pos_tag(Input,Option):    # make a single list of (w,pos)
        tag_result.extend(lst)
    out = pack_ner(ner(tag_result))
    #### remove POS and Word boundary
    out = re.sub(r'<s/>',' ',out)
    out = re.sub(r'\/[A-Z]+\|','',out)

    return(out)
    
###################################################################################
## named entity recognition for Person, Location, Organization
## Input = list of (w,pos)
## Output = list of (w,pos,ner_tag)
## adapted from http://sklearn-crfsuite.readthedocs.io/en/latest/tutorial.html
def ner(sent):
    lx = []
    if sent[-1][0] == ' ': del(sent[-1]) 
    lx = sent2features(sent)
    try:
      ner_tagger
    except NameError:
      ner_load()

    p = ner_tagger.predict_single(lx)
    r = []
    for i in range(len(sent)):
        r.append(( sent[i][0], sent[i][1], p[i]))
    return (r)

def ner_load():
    global ner_tagger
    ner_tagger = CRF(algorithm='lbfgs',
          c1=10,
          c2=0.1,
          max_iterations=100,
          all_possible_transitions=False)
    path = os.path.abspath(__file__)
    ATA_PATH = os.path.dirname(path)

    f = bz2.BZ2File(ATA_PATH +'/' + 'ner_tagger.pklz','rb')
    ner_tagger = pickle.load(f)

#    filehandler = open(ATA_PATH +'/' + 'ner_tagger.pick', 'rb') 
#    ner_tagger = pickle.load(filehandler)

### get the size of word s/m/l
def wrd_len(word):
    if len(word) > 20:
        return('l')
    elif len(word) > 10:
        return('m')
    else:
        return('s')
    
def word2features(sent, i):
    word = sent[i][0]
    postag = sent[i][1]

    features = {
        'bias': 1.0,
        'word': word,
        'postag': postag,
        'len': wrd_len(word)
    }
    if i > 0:
        word1 = sent[i-1][0]
        postag1 = sent[i-1][1]
        features.update({
            '-1:word': word1,
            '-1:postag': postag1,
        })
    else:
        features['BOS'] = True
    if i > 2:
        word1 = sent[i-2][0]
        postag1 = sent[i-2][1]
        features.update({
            '-2:word': word1,
            '-2:postag': postag1,
        })
    if i < len(sent)-1:
        word1 = sent[i+1][0]
        postag1 = sent[i+1][1]
        features.update({
            '+1:word': word1,
            '+1:postag': postag1,
        })
    else:
        features['EOS'] = True
    return features


def sent2features(sent):
    return [word2features(sent, i) for i in range(len(sent))]

def sent2labels(sent):
    return [label for token, postag, label in sent]

def sent2tokens(sent):
    return [token for token, postag, label in sent]

def pack_ner(sent):
    out = ''
    flag = 'O'
    for (w,p,t) in sent:
        if re.match(r'[BI]-P',t) and flag == 'O':
            out += '<NEp>'+w+'/'+p+'|'
            flag = 'NEp'
            continue
        elif t == 'O' and flag == 'NEp':
            out += '</NEp>'+w+'/'+p+'|'
            flag = 'O'
            continue
        elif re.match(r'[BI]-O',t) and flag == 'O':
            out += '<NEo>'+w+'/'+p+'|'
            flag = 'NEo'
            continue
        elif t == 'O' and flag == 'NEo':
            out += '</NEo>'+w+'/'+p+'|'
            flag = 'O'
            continue
        elif re.match(r'[BI]-L',t) and flag == 'O':
            out += '<NEl>'+w+'/'+p+'|'
            flag = 'NEl'
            continue
        elif t == 'O' and flag == 'NEl':
            out += '</NEl>'+w+'/'+p+'|'
            flag = 'O'
            continue
        else:     
            out += w+'/'+p+'|'
            
    if flag == 'NEp':
        out += '</NEp>'
    elif flag == 'NEo':
        out += '</NEo>'
    elif flag == 'NEl':
        out += '</NEl>'
    return(out)

###  collapse <NE> w1/p1|w2/p2|w3/p3 </NE> into <NE> w1w2w3/PROPN </NE>
'''
    print("out1",out)
    while re.search(r'<(NE[plo])>(.+?)/[A-Z]+\|</\1>', out):
        out = re.sub(r'<(NE[plo])>(.+?)/[A-Z]+\|</\1>',r'<\1>\2</\1>', out)
    out = re.sub(r'<(NE[plo])>(.+?)</\1>',r'<\1>\2/PROPN</\1>',out)
    print("out2",out)
'''

###############################################################################################



###############################################################################################
###  segment discourse unit + word segmentation
###  Input = Thai text,  syllable segments will be used to determine edu
###  then, syllable list in each edu will be passed to word segmentation
###  The output is a list of word segments marked with '|' and edu segments marked with '<u/>' 
def segment(txt):
    global SegSep
    global SSegSep
    global useg_model
    output = ""
    out = ""
    
#    print(txt)
    txt = txt + ' '
    sylseg = syl_segment(txt)
    sylseg = re.sub(' ','<s/>',sylseg)
    sylseg = re.sub(r'([^~])<s/>',r'\1~<s/>',sylseg)
    sylseg = re.sub(r'<s/>([^~])',r'<s/>~\1',sylseg)

    sylcopy = sylseg
    sylcopy = re.sub(r'~[0-9\.\,]+~','~DIGIT~',sylcopy)
    sylcopy = re.sub(r'~[a-zA-Z0-9\\\/\?\'\"\(\)\.]+~','~FOREIGN~',sylcopy)

    parcopy = sylcopy.split('~')
    par = sylseg.split('~')
#    print(sylcopy)
    
    
    try:
      useg_model
    except NameError:
      useg_model_load()

    tags = useg_model.predict([features(parcopy, index) for index in range(len(par))])
    lst_tag = zip(par,tags)
    syl_seq = ''
    for (w,t) in lst_tag:
        if t == '<u/>':
            out = word_segment(syl_seq,method="colloc")
            out = wordseg_colloc(syl_seq)
            output += out+'<u/>'
            syl_seq = ''
        else:
#            lst_syl.append(w)
            syl_seq += w+'~'

    output = re.sub(r"([0-9])<s/>",r"\1|<s/>",output)        
    output = re.sub(r"<s/>([0-9])",r"<s/>|\1",output)        
    return(output)

# load a Pickle file and then compress it into a file with bz2 
'''
def useg_model_compress():
    f = open('/Users/macbook/Cloud/Dropbox/prog/python/TLTK/tltk/sent_segment.pick','rb')
    model = pickle.load(f)
    f = bz2.BZ2File('/Users/macbook/Cloud/Dropbox/prog/python/TLTK/tltk/sent_segmentx.pklz','wb')
    pickle.dump(model,f)
    f.close()
'''
def text_class_model_load():
    global chk_level_model
    global chk_genre_model

    path = os.path.abspath(__file__)
    ATA_PATH = os.path.dirname(path)

    filehandler = bz2.BZ2File(ATA_PATH +'/' + 'chklevel_rf.pklz', 'rb') 
    chk_level_model = pickle.load(filehandler)

    filehandler = bz2.BZ2File(ATA_PATH +'/' + 'chkgenre_rf.pklz', 'rb') 
    chk_genre_model = pickle.load(filehandler)
    return(1)

'''
    filename = ATA_PATH +'/' + 'chklevel_rf.pkl'
    with open(filename, 'rb') as file:
        chk_level_model = pickle.load(file)
    filename = ATA_PATH +'/' + 'chkgenre_rf.pkl'
    with open(filename, 'rb') as file:
        chk_genre_model = pickle.load(file)
'''        

def useg_model_load():
    global useg_model
    useg_model = Pipeline([
    ('vectorizer', DictVectorizer(sparse=False)),
    ('classifier', RandomForestClassifier(n_jobs=2, random_state=0))])
 
    path = os.path.abspath(__file__)
    ATA_PATH = os.path.dirname(path)
#    print('XXXXX',ATA_PATH +'/' + 'sent_segment.pick')
#    filehandler = open(ATA_PATH +'/' + 'sent_segment.pick', 'rb') 
    filehandler = bz2.BZ2File(ATA_PATH +'/' + 'sent_segment.pklz', 'rb') 
    useg_model = pickle.load(filehandler)
    return(useg_model)
    
def untag(tagged_sentence):
    return [w for w, t in tagged_sentence]

def transform_to_dataset(tagged_sentences):
    X, y = [], []
    for index in range(len(tagged_sentences)):
        X.append(features(untag(tagged_sentences), index))
        y.append(tagged_sentences[index][1]) 
    return X, y

## This function will get features from each token  sentence = list of tokens
def features(sentence, index):
    return {
        'word': sentence[index],
        'prev_word': '' if index == 0 else sentence[index - 1],
        'prev_biword' : '' if index <= 1 else sentence[index - 2]+sentence[index - 1],
        'next_word': '' if index == len(sentence) - 1 else sentence[index + 1],
        'next_biword': '' if index >= len(sentence) - 2 else sentence[index + 1]+sentence[index + 2],
        'has_hyphen': '-' in sentence[index],
        'is_numeric': sentence[index] == 'DIGIT',
        'is_space' : '<s/>' in sentence[index],
        'after_space' : False if index == 0 else sentence[index-1] == '<s/>',
        'before_space' : False if index == len(sentence) - 1 else sentence[index+1] == '<s/>',
        'dist_space' : 0 if '<s/>' not in sentence[:index] else distance(sentence,index),
        'Mai_yamok' : 'ๆ' in sentence[index],
        'after_FOR' : False if index == 0 else sentence[index-1] == 'FOREIGN',
        'before_FOR' : False if index == len(sentence) - 1 else sentence[index+1] == 'FOREIGN',
        'after_DIG' : False if index == 0 else sentence[index-1] == 'DIGIT',
        'before_DIG' : False if index == len(sentence) - 1 else sentence[index+1] == 'DIGIT',
    }

def distance(sentence,index):
    i = index-1
    while sentence[i] != '<s/>' and i > 0:
        i-=1
    return(index-i)    

###################################
## Thai pun  คำผวน  แบบ สลับหน้าหลัง  output  เป็นคำอ่าน อาจผวนได้สองแบบ  
## แสงดี => สีแดง (คงเสียงพยัญชนะต้นและเสียงวรรณยุกต์) , ซีแด๋ง  (คงพยัญชนะต้น)  
## 2 syllables : ควายตาม => ตามควาย
## 3 syllables : ไฟเราแงน => แฟนเราไง,  
## 4 syllables : เรียวเธอคนดอ => รอเธอคนเดียว  
## 5 syllables : พ่ายกันจนวันเตือน => เพื่อนกันจนวันตาบ
def spoonerism(word):
#    print(word)
    output=[]
    thrd = ''
    word = re.sub(r"[ก-ฮุิ]์","",word)  ##remove karan
    tmp = g2p(word)  #get transciprion    
    tmp = tmp.replace('<s/>','')
    tmp = tmp.replace('|','~')
    (syls, trans) = tmp.split('<tr/>')  ## syllables + transcription
#    print(syls,trans)
    tran_lst = trans.split('~')  # lst of trans
    tran_lst.pop(-1)    ##remove last empty
    syl_lst = syls.split('~')  # lst of syl
    tranx = tran_lst[0]   ## 
    trany = tran_lst[-1]
    intC1, tone1 = Pcompose(tranx)   #get initC + tone from first syl
    intC2, tone2 = Pcompose(trany)   #get initC + tone from last syl
    ## preserve initC
    tranx = re.sub(r".+?([aeiouxOU\@]+)",intC2+r"\1",tranx)  ##replace first initC with initC from last
    trany = re.sub(r".+?([aeiouxOU\@]+)",intC1+r"\1",trany)  ##replace last initC with initC from last
    sylx = PhoneToThai(tranx)  ## get written form
    syly = PhoneToThai(trany)  ## get written form
    ## reverse new last to first syllable, new first to last syllable, prserve tone order
    syl_lst[0] = syly   
    syl_lst[-1] = sylx  
    x = '-'.join(syl_lst)
    if '?' not in x: output.append(x)  # if new form is OK, add to output

    ## preserve initC and tone : replace tone in new first syl with tone from last syl, and vice versa
    tranx = re.sub(r"[0-4]",tone2,tranx)  ## replace tone of first with last
    trany = re.sub(r"[0-4]",tone1,trany)  ## replace tone of last with first
    sylx = PhoneToThai(tranx)  ## get written form new first
    syly = PhoneToThai(trany)
    ## preserve first and last
    syl_lst[0] = syly
    syl_lst[-1] = sylx
    x = '-'.join(syl_lst)
    if x not in output and '?' not in x: output = [x] + output
    return(output)

## get initial consonant, tone
def Pcompose(ph):
    match = re.search(r"^(.+?)[aeiouxOU\@]+.*([0-4])$",ph)
    return(match.group(1),match.group(2))


##################################
class SylProp:
    form = ''
    phone = ''
    char = 0 ## no of char in a syllable
    dead = False  ##  dead or alive
    initC = '' ## initial consonant
    finalC = '' ## final consonant
    vowel = '' ## vowel form
    tonemark = 0 ## tone marker 1,2,3,4,5
    initPh = ''  ## initial sound
    finalPh = '' ## final sound
    vowelPh = '' ## vowel sound
    tone = 0 ## tone 1,2,3,4,5
    leading = False ##  leading syllable  e.g. สบาย  สห 
    cluster = False ## cluster consonant
    karan = ''  

class WordProp:
    form = ''
    phone = ''
    char = 0  ## no of characters in a word
    syl = 0   ## no of syllables
    corrtone = 0  ## no of the same tone markers and tones (include no tone marker for 0tone)
    incorrtone = 0  ## no of the different tone markers and tones
    corrfinal = 0  ## no of final consonant in its basic forms: กก กด กง กน กม เกย เกอว
    incorrfinal = 0  ## no of final consonant not in its basic forms: กก กด กง กน กม เกย เกอว
    karan = 0 ## no of karan
    cluster = 0  ## no of initial cluster
    lead = 0  ## no of leading syllables
    doubvowel = 0 ## no of double vowel
    syl_prop = []  ## a list of SylProp()

class TextProp:
    DesSpC = 0  ## no of DesSpC in a text
    DesChC = 0  ## text length  (character)
    DesPC = 0  ## no of paragraph
    DesEduC = 0  ## no of edu unit
    DesSymbC = 0 ## no of symbols or punctuation
    LdvTTR = 0. ## type/token ratio
    DesTotW = 0 ## total word in a text
    DesTotT = 0 ## total type in a text
    DesEduL = 0. ## mean of edu length (word)
    DesEduLd = 0. ## stdv of edu length (word)
    DesWrdL = 0. ## mean of word length (syllable)
    DesWrdLd = 0. ## stdv of word length (syllable)
    DesPL = 0. ## mean of paragraph length (word)
    #### property from WordProp  
    DesCorrToneC = 0  ## no of correct tone form and phone
    DesInCorrToneC = 0  ## no of incorrect tone form and phone
    DesCorrFinalC = 0  ## no of correct final consonant กก กด กง กน กม เกย เกอว
    DesInCorrFinalC = 0  ## no of incorrect final consonant กก กด กง กน กม เกย เกอว
    DesKaranC = 0 ## no of karan
    DesClusterC = 0  ## no of cluster
    DesLeadC = 0 ## no of leading syllable
    DesDoubVowelC = 0 ## no of double vowel
    DesNegC = 0 ## no. of negation
    DesNElC = 0 ## no. of NE location
    DesNEoC = 0 ## no. of NE organization
    DesNEpC = 0 ## no. of NE person
    WrdCorrTone = 0.  ## average of correct tone form and phone
    WrdInCorrTone = 0.  ## average of incorrect tone form and phone
    WrdCorrFinal = 0.  ## average of correct final consonant กก กด กง กน กม เกย เกอว
    WrdInCorrFinal = 0.  ## average of incorrect final consonant กก กด กง กน กม เกย เกอว
    WrdKaran = 0. ## average of karan
    WrdCluster = 0.  ## average of initial cluster
    WrdLead = 0. ## ratio of word with a leading syllable
    WrdDoubVowel = 0. ## average of double vowel
    WrdNEl = 0. ## avg. of named entity location
    WrdNEo = 0. ## avg. of named entity organization
    WrdNEp = 0. ## avg. of named entity person
    WrdNeg = 0.  ## avg. of negation
    DesTNCt1C = 0   ## no word in TNC tier1  50%
    DesTNCt2C  = 0   ## no word in TNC tier2  51-60%
    DesTNCt3C  = 0   ## no word in TNC tier3  61-70%
    DesTNCt4C  = 0   ## no word in TNC tier4  71-80%
    DesTTC1 = 0   ## no word in TTC level1 
    DesTTC2 = 0   ## no word in TTC level2
    DesTTC3 = 0   ## no word in TTC level3
    DesTTC4 = 0   ## no word in TTC level4
    WrdC = 0.  ## mean of relative frequency of content word from TTC
    WrdF = 0.  ## mean of relative frequency of function word from TTC
    WrdCF = 0. ## mean of relative frequency of content/function word from TTC 
    WrdFrmSing  = 0. ## mean of relative frequency of single word forms in TTC
    WrdFrmComp = 0. ## mean of relative frequency of complex/compound word forms in TTC 
    WrdFrmTran = 0. ## mean of relative frequency of transliteration words in TTC
    WrdSemSimp = 0. ## mean of relative frequency of simple word in TTC 
    WrdSemTran = 0. ## mean of relative frequency of transparent compound word in TTC
    WrdSemSemi = 0. ## mean of relative frequency of words in between transparent and opaque compound in TTC
    WrdSemOpaq = 0. ## mean of relative frequency of opaque compound word in TTC 
    WrdBasicM = 0. ## mean of relative frequency of word in basic vocab of ministry of Education
    WrdBasicT  = 0. ## mean of relative frequency of word in basic vocab from TNC & TTC < 2000
    WrdTfidf = 0. ## Sum of TNC-tfidf of a word 
    WrdTncDisp = 0. ## Sum of TNC-dispersion of a word
    WrdTtcDisp = 0. ## Sum of TTC-dispersion of a word 
    WrdArf = 0. ## Sum of averaged reduced frequency of a word
    WrdTNCt1 = 0.  ## ratio of words in TNC tier1
    WrdTNCt2 = 0.  ## ratio of words in TNC tier2
    WrdTNCt3 = 0.  ## ratio of words in TNC tier3
    WrdTNCt4 = 0.  ## ratio of words in TNC tier1
    WrdTTC1 = 0.  ## ratio of words in TTC level1
    WrdTTC2 = 0.  ## ratio of words in TTC level2
    WrdTTC3 = 0.  ## ratio of words in TTC level3
    WrdTTC4 = 0.  ## ratio of words in TTC level4
    WrdTfidf = 0.
    WrdTncDisp = 0.
    WrdTtcDisp = 0.
    WrdArf = 0.
    WrdNOUN = 0 ## mean of relative frequency of word with POS=NOUN
    WrdVERB = 0 ## mean of relative frequency of word with POS=VERB
    WrdADV = 0 ## mean of relative frequency of word with POS=ADV
    WrdDET = 0
    WrdADJ = 0
    WrdADP = 0
    WrdPUNCT = 0
    WrdAUX = 0
    WrdSYM = 0
    WrdINTJ = 0
    WrdCCONJ = 0
    WrdPROPN = 0
    WrdNUM = 0
    WrdPART = 0 	 
    WrdPRON = 0 	 
    WrdSCONJ = 0
    SynDepth = 0.  ## mean of syntactic depth
    CrfCWL = 0  ## mean of Coreference between segments (Y/N link) 
    CrfCTL = 0  ## mean of Corefence between segments, (no. of words overlapped) 
    CrfCNL = 0  ## mean of coreference of nouns between segments, (Y/N noun link) 
    CrfCVL = 0  ## mean of coreference of verbs between segments, (Y/N verb link) 

#    pos = defaultdict(int)  ## dict of { pos: freq}
    deprel = defaultdict(int)  ## dict of { deprel: freq}
    wrd = defaultdict(int)  ## dict of { word: freq}
    wrd_arf = defaultdict(float)  ## dict of { word: arf}
'''
* CrfCWG xxx ## proportion of explicit content words that overlap globally (all other edus)
* CncAll xxx ## all connective
* CncCaus xxx ## causual connective e.g. เพราะ ดังนั้น จึง 
* CncLogic xxx ## logical connective e.g. และ หรือ 
* CncAdC xxx ## adversative/contrastive e.g. แม้ว่า ถึงแม้ว่า กระนั้น
* CncTemp xxx ## Temporal connective e.g. จนกว่า  จนกระทั่ง แล้วจึง
* CncAdd xxx ## Additive connective e.g. ยิ่งกว่านั้น นอกจากนั้น นอกจากนี้
* CncNeg xxx ## Negative connective e.g. แต่ แต่ว่า 
'''

###################################
### Analyze all features of a syllable
### Input = a syllable
def SylAna(s,p):
    Maiaek = '่'
    Maitoo = '้'
    Maitri = '๊'
    Maijatawa = '๋'

    if len(p) < 1: return('')
    syl = SylProp()
    syl.char = len(s)
    syl.form = s
    syl.phone = p
    mt = re.search(r"[ก-ฮ]?([ก-ฮ]?์[ก-ฮ]?)",s)
    if mt:
        syl.karan = mt.group(1)
        s = re.sub(r"([ก-ฮ])?([ก-ฮ]?์[ก-ฮ]?)",r"\1",s)

    if DeadSyl(p) == 'D':
        syl.dead = True  ##  dead or alive
    else:
        syl.dead = False
    if Maiaek in s: 
        syl.tonemark = 'เอก'
    elif Maitoo in s:
        syl.tonemark = 'โท'
    elif Maitri in s:
        syl.tonemark = 'ตรี'
    elif Maijatawa in s:
        syl.tonemark = 'จัตวา'
    else:
        syl.tonemark = ''
    if "'" in p:     ## leading syllable, include irregular syllables e.g. วิต	wit3'ta1, วัฒน	wat3'tha3'na3 
        syl.leading = True
        return(syl)
    else:
        syl.leading = False       

    ## for normal syllable defined by syllable patterns, try to find init, final, vodel            
    mt = re.match(r"^(.*[^aeioux@OU])([aeioux@OU]+)(.*)([0-9])",p) ## แยกหา initial + vowel + final + tone  เก็บสิ่งที่แยกได้ใน $1 $2 $3 $4 ตามลำดับ
   ## map คัวอักษรของ initial, vowel, final
    syl.initPh = mt.group(1) 
    syl.vowelPh = mt.group(2)
    if mt.group(3): 
        syl.finalPh = mt.group(3)
    else:
        syl.finalPh = ''    
    syl.tone = mt.group(4)

    for f in PRON:
        if "(" not in f: continue
        f = "^"+f+"$"
#        print(f,s)    
        matchObj = re.match(f,s)
        if matchObj:
            keymatch = matchObj.group()
            try:
                matchObj.group(3)
                syl.initC = matchObj.group(1) + matchObj.group(2) 
                syl.finalC = matchObj.group(3)
#                print("3",matchObj.group(1),matchObj.group(2),matchObj.group(3))
                syl.vowel = re.sub(r"[ก-ฮ]","",s)
                break
            except IndexError:
                try:
                    matchObj.group(2)
                    if re.search(r".[rlw]",syl.initPh):
                        syl.initC = matchObj.group(1) + matchObj.group(2)
                        syl.finalC = ''
                        syl.cluster = True
                    else:    
                        syl.initC = matchObj.group(1)
                        syl.finalC = matchObj.group(2) 
#                    print("2",matchObj.group(1),matchObj.group(2))
                    syl.vowel = re.sub(r"[ก-ฮ]","",s)
                    break
                except IndexError:
                    matchObj.group(1)
                    syl.initC = matchObj.group(1) 
                    syl.finalC = ''
#                    print("1",matchObj.group(1))
                    syl.vowel = re.sub(r"[ก-ฮ่-๋์]","",s)
                    break
#    cluster = 0 ## cluster consonant
#    print(s,p,vars(syl))
    return(syl)

################################
### Analyze all features of a word
### Input = a word
def WordAna(w):
    syl = SylProp()
    w = w.replace(" ","")
    if w == '' or w == '\t': return('')
    wrd = WordProp()    
    wrd.char = len(w)
    GP = g2p(w)
    if "<Fail>" in GP: return('')
#    print("GP0",GP)
    GP = re.sub(r'\|<s/>$','',GP)
    GP = GP.replace("|","~")
#    print("w-GP",GP)   ####
    if GP.count('<tr/>') == 0 or GP.count('<tr/>') > 1:
        return('')
    (form,phone) = GP.split('<tr/>')
    if form == phone: return('')
    wrd.form = form
    wrd.phone = phone
#    wordlst = forms.split('|')
#    phonelst = phones.split('|')
#    for i in range(len(wordlst)):
    if '์' in form:
        wrd.karan += 1
    frmlst = form.split('~')
    phlst = phone.split('~')
    wrd.syl = len(frmlst)
    for i in range(wrd.syl):
        syl_form = frmlst[i]
        phon_form = phlst[i]
        if phon_form == '' or syl_form == 'ๆ' : continue
#        print(syl_form,phon_form)  
        syl = SylAna(syl_form,phon_form)
        wrd.syl_prop.append(syl)
#        wrd.syl_prop.append(SylAna(syl_form,phon_form))
#        print(wrd.syl_prop)  
        match = re.search(r"([\u0E48|\u0E49|\u0E4A|\u0E4B])",syl_form)
#        print("|",syl_form,"|",phon_form,"|")
        if match:
            if match.group() == "\u0E48" and '1' in phon_form:
                wrd.corrtone += 1
            elif match.group() == "\u0E49" and '2' in phon_form:
                wrd.corrtone += 1
            elif match.group() == "\u0E4A" and '3' in phon_form:
                wrd.corrtone += 1
            elif match.group() == "\u0E4B" and '4' in phon_form:
                wrd.corrtone += 1
            else:
                wrd.incorrtone += 1    
        elif '0' in phon_form:    ### no tone marker w/ tone 0
            wrd.corrtone += 1
        else:
            wrd.incorrtone += 1
        if re.search(r"[กงดนมยว]$",syl_form) and re.search(r"[ktnNjw][\d]$",phon_form):
            wrd.corrfinal += 1
        elif re.search(r"[^กงดนมยว]$",syl_form) and re.search(r"[ktnNjw][\d]$",phon_form):    
            wrd.incorrfinal += 1
#            print("*********final",wrd.corrfinal,phon_form,syl_form)
        if re.search(r"[iuU]a",phon_form):    
            wrd.doubvowel += 1
#            print("=====double",wrd.doubvowel,phon_form)
#        if re.search(r"^[bptk][rlw]",phon_form):
        if syl.cluster == True:
            wrd.cluster += 1
#            print(">>>>>cluster",wrd.cluster,phon_form)
#        if re.search(r"a[0-4]\'",phon_form):
        if syl.leading == True :
            wrd.lead += 1   
#            print("-----lead",wrd.lead,phon_form)
    return(wrd)
#    wrdfeats = {}
#    wrdfeats = vars(wrd)
#    wrdfeats.update(wrd.ling)
#    return(wrdfeats)
    

###################################
### tag transcription and POS for making TNC
def TNC_tag(txt,POS="Y"):
    parx = txt.split('\n')
    tag = ""
    for par in parx:
        for sent in re.sub('\s+', ' ', par).split():
            tx = g2p(sent)
            (wx,trx) = tx.split('<tr/>')
            w_lst = wx.split('|')
            tr_lst = trx.split('|')
            wpos_lst = pos_tag_wordlist(w_lst)
            for i in range(0,len(w_lst)):
                tr = tr_lst[i].replace("~","").replace("\'","").replace("^","")
                wrd = w_lst[i].replace("~","").replace("\'","").replace("^","")
                if POS=="Y":
                    tag += '<w tran="' + tr + '" POS="' + wpos_lst[i][1] +'">' + wrd + '</w>'
                else:
                    tag += '<w tran="' + tr + '">' + wrd + '</w>'
            tag += "<s/>"
    tag += '\n'
    return(tag)        


# find all indices of X in list_of_words, then get each D and calculate Average Reduced Frequency
def ARF(list_words,w):
    lst_idx = [idx for idx, value in enumerate(list_words) if value == w]
    if len(lst_idx) > 0:
        v = len(list_words)/len(lst_idx)
        sum = 0.
        pid=0
        for i in range(1, len(lst_idx)):
            sum += min(v,lst_idx[i]-lst_idx[i-1])  ## add d from pos 1-2-3-...n
        sum += min([v,lst_idx[0]+len(list_words)-lst_idx[-1]]) ## add d from pos n-0   
        return(sum/v)   
    else:
        return(0.)   
  
################################    

############################
## analyze all features of a text
def TextAna(alltext,TextOption="par",WordOption="colloc",UDParse="none"):
    global WRD
    global tagger
    try:
      tagger
    except NameError:
      pos_load()
    prev_tag_results = []  

    txt = TextProp()
    txt.DesChC = len(alltext)
#    chunk(alltext)

    eduwrd_lst = []
    wrdchar_lst = []
    wrdsyl_lst = []
    parwrd_lst = []
    wtype = defaultdict(int)
    parwrd = 0
    txt.wrd = {}
    txt.wrd_arf = {}
    txt.deprel = {}

    if TextOption == 'edu':
#        utext = chunk(alltext)
        utext = segment(alltext)
        txt.DesPC = len(re.findall(r'\n+', alltext))   #alltext.count("\n")+1
        txt.DesSpC = alltext.count(" ") + alltext.count("\t")
    elif TextOption == 'par':
        alltext = alltext.replace("\n","<u/>") 
        alltext = word_segment(alltext,method=WordOption)
        alltext = alltext.replace("<s/>","|<s/>|") 
        utext = alltext.replace("||","|")
        txt.DesPC = len(re.findall(r'\n+', alltext))   #alltext.count("\n")+1
        txt.DesSpC = alltext.count(" ") + alltext.count("\t")
    elif TextOption == "segmented":
        WordOption = "segmented"
        alltext = alltext.replace("<s>","|<s/>|")
        alltext = alltext.replace(" ","|<s/>|")
        alltext = alltext.replace("||","|")
        txt.DesPC = len(re.findall(r'<p>', alltext))   #alltext.count("\n")+1
        utext = alltext.replace("<p>","<u/>")  
        txt.DesSpC = alltext.count("<s/>") + alltext.count("\t")
    words_lst = []


##  u in utext must be a string w/ '|'
    txt.DesEduC = utext.count("<u/>")-1
    utts = utext.split("<u/>")
    no_Crf = max(len(utts)-1,1)    
    for i in range(0,len(utts)):
        u = utts[i]
#        print(i,no_Crf,u)    #pxxxx
#   for u in utext.split("<u/>"):
#        print("u=",u)
        if u == '' or u == '|': 
            no_Crf -= 1
            continue
        if WordOption == "segmented":
            tag_results = []
            sent = u.split('|')
            ## remove all '' from sent
            sent = list(filter(lambda a: a != '', sent))
#            print("sent=",sent)
            for (w,pos) in tagger.tag(sent):
                pos = change_tag(w,pos)
                tag_results.append((w,pos))    
            u = pack_ner(ner(tag_results))
#            print("uuuuuuu",u)
        else:
            sent = u.split('|')
            ## remove all '' from sent
            sent = list(filter(lambda a: a != '', sent))
            tag_results = pos_tag_wordlist(sent)
#            print("x=",x)
            u = pack_ner(ner(tag_results))  
#            print("u ner=",u) 

#       get d-tree and count deprel and its depth 
        if UDParse == "Malt":
#            print(sent) #Pxxxx    
            ud_parse = MaltParser_wordlist(sent)
#            print_dtree(ud_parse)       
            if ud_parse != "":
                txt.SynDepth += tree_max_depth(ud_parse)
                for word in ud_parse["words"]:
                    if word['id'] > 0:
                        if word['deprel'] in txt.deprel:
                            txt.deprel[word['deprel']] += 1
                        else:    
                            txt.deprel[word['deprel']] = 1

        ## find link of NOUN and the same word betweem two utterances        
        if Duplicate_word('NOUN',tag_results,prev_tag_results):
            txt.CrfCNL += 1
        if Duplicate_word('VERB',tag_results,prev_tag_results):
            txt.CrfCVL += 1
        prev_tag_results = tag_results

        txt.DesNElC += u.count("<NEl>") 
        txt.DesNEoC += u.count("<NEo>") 
        txt.DesNEpC += u.count("<NEp>") 
        u = re.sub(r"</?NE[lop]>","",u)
#        print("new u",u)
        wlst = u.split("|")

        parwrd += len(wlst)
#        txt.DesTotW += len(wlst)
        eduwrd_lst.append(len(wlst))
        for wp in wlst:
#            print(wp)   #####
            if re.search(r'[$#:;^@&%\*\+\-\(\)\"\']',wp):
                txt.DesSymbC += 1
                continue
            elif 'SYM' in wp or 'PUNCT' in wp:
                txt.DesSymbC += 1
                if 'SYM' in wp:
                    txt.WrdSYM += 1
                elif 'PUNCT' in wp:
                    txt.WrdPUNCT += 1
                continue
            if wp == '' or '/' not in wp or wp.count('/') > 1: continue
            (w,p) = wp.split('/')
            wtype[w] += 1
#            txt.pos[p] += 1
            if w in txt.wrd:
                txt.wrd[w] += 1
            else:
                txt.wrd[w] = 1    
            if p == 'NOUN':
                txt.WrdNOUN += 1
            elif p == 'VERB':
                txt.WrdVERB += 1
            elif p == 'ADV':
                txt.WrdADV += 1
            elif p == 'DET':
                txt.WrdDET += 1
            elif p == 'ADJ':
                txt.WrdADJ += 1
            elif p == 'ADP':
                txt.WrdADP += 1
            elif p == 'AUX':
                txt.WrdAUX += 1
            elif p == 'INTJ':
                txt.WrdINTJ += 1
            elif p == 'CCONJ':
                txt.WrdCCONJ += 1
            elif p == 'PROPN':
                txt.WrdPROPN += 1
            elif p == 'NUM':
                txt.WrdNUM += 1
            elif p == 'PART':
                txt.WrdPART += 1
            elif p == 'PRON':
                txt.WrdPRON += 1
            elif p == 'SCONJ':
                txt.WrdSCONJ += 1
            words_lst.append(w)

            if 'ไม่' in w : txt.DesNegC += 1 
#            print(WRD[w])
            if w in WRD: 
                if 'tier' in WRD[w]:
                    tx = WRD[w]['tier']
                    if tx == 'T1':
                        txt.DesTNCt1C += 1
                    elif tx == 'T2':
                        txt.DesTNCt2C += 1
                    elif tx == 'T3':
                        txt.DesTNCt3C += 1
                    elif tx == 'T4':
                        txt.DesTNCt4C += 1
                if 'level' in WRD[w]:
                    tx = WRD[w]['level']
                    if tx == 'L1':
                        txt.DesTTC1 += 1
                    elif tx == 'L2':
                        txt.DesTTC2 += 1
                    elif tx == 'L3':
                        txt.DesTTC3 += 1
                    elif tx == 'L4':
                        txt.DesTTC4 += 1
                if 'cont' in WRD[w]:
                    tx = WRD[w]['cont']
                    if tx == 'CF':
                        txt.WrdCF += 1
                    elif tx == 'C':
                        txt.WrdC += 1
                    elif tx == 'F':
                        txt.WrdF += 1
                if 'seman' in WRD[w]:
                    tx = WRD[w]['seman']
                    if tx == 'simp':
                        txt.WrdSemSimp += 1
                    elif tx == 'tranp':
                        txt.WrdSemTran += 1
                    elif tx == 'semi':
                        txt.WrdSemSemi += 1
                    elif tx == 'opaq':
                        txt.WrdSemOpaq += 1
                if 'form' in WRD[w]:
                    tx = WRD[w]['form']
                    if tx == 'sing':
                        txt.WrdFrmSing += 1
                    elif tx == 'tran':
                        txt.WrdFrmTran += 1
                    elif tx == 'comp':
                        txt.WrdFrmComp += 1
                if 'lvocab' in WRD[w]:
                    if WRD[w]['lvocab'] == 'L1':
                        txt.WrdBasicM += 1
                if 'bvocab' in WRD[w]:
                    if WRD[w]['bvocab'] == '2000':
                        txt.WrdBasicT += 1
#                if 'tnc-tfidf' in WRD[w]:
#                    txt.WrdTfidf += WRD[w]['tnc-tfidf']        
#                if 'tnc-disp' in WRD[w]:
#                    txt.tncdisp += WRD[w]['tnc-disp']        
#                if 'ttc-disp' in WRD[w]:
#                    txt.ttcdisp += WRD[w]['ttc-disp']        
            wrd = WordAna(w)
            if wrd == '': continue
#            print(w,vars(wrd))
            wrdchar_lst.append(wrd.char)
            wrdsyl_lst.append(wrd.syl)
            txt.DesCorrToneC += wrd.corrtone  ## no of correct tone form and phone
            txt.DesInCorrToneC += wrd.incorrtone  ## no of correct tone form and phone
            txt.DesCorrFinalC += wrd.corrfinal  ## no of correct final consonant กก กด กง กน กม เกย เกอว
            txt.DesInCorrFinalC += wrd.incorrfinal  ## no of incorrect final consonant กก กด กง กน กม เกย เกอว
            txt.DesKaranC += wrd.karan ## no of karan
            txt.DesClusterC += wrd.cluster  ## no of cluster
            txt.DesLeadC += wrd.lead ## no of leading syl
            txt.DesDoubVowelC += wrd.doubvowel ## no of double vowel
            txt.DesTotW += 1
        if i < no_Crf and len(utts)>i+1:
            sentn = utts[i+1].split('|')
            sentn = list(filter(lambda a: a != '', sentn))
            overlap = len(set(sent) & set(sentn))
            if overlap > 0:
                txt.CrfCWL += 1
                txt.CrfCTL += overlap

    txt.CrfCNL = txt.CrfCNL/no_Crf  # local same NOUN coherent content binary count
    txt.CrfCWL = txt.CrfCWL/no_Crf  # local coherent content binary count
    txt.CrfCTL = txt.CrfCTL/no_Crf  # local coherent content count no.of tokens overlap
    txt.SynDepth = txt.SynDepth / no_Crf  # mean of syntactic depth from root

    #### get average reduced frequency for each word in the text
    '''
    for w in WRD:
        if 'tnc-tfidf' in WRD[w]: txt.WrdTfidf += WRD[w]['tnc-tfidf']        
        if 'tnc-disp' in WRD[w]: txt.WrdTncDisp += WRD[w]['tnc-disp']        
        if 'ttc-disp' in WRD[w]: txt.WrdTtcDisp += WRD[w]['ttc-disp']        
    '''
    for w in txt.wrd:
#        print("wrd_lst",words_lst)
#        print("word",w)
        txt.wrd_arf[w] = ARF(words_lst,w)
        txt.WrdArf += txt.wrd_arf[w]
        if 'tnc-tfidf' in WRD[w]: txt.WrdTfidf += WRD[w]['tnc-tfidf']        
        if 'tnc-disp' in WRD[w]: txt.WrdTncDisp += WRD[w]['tnc-disp']        
        if 'ttc-disp' in WRD[w]: txt.WrdTtcDisp += WRD[w]['ttc-disp']        

    parwrd_lst.append(parwrd)
    txt.DesTotT = len(wtype)   
    txt.DesEduL = statistics.mean(eduwrd_lst) # sum(eduwrd_lst)/len(eduwrd_lst)     
    txt.DesEduLd = statistics.stdev(eduwrd_lst)
    txt.DesWrdL = statistics.mean(wrdsyl_lst)
    txt.DesWrdLd = statistics.stdev(wrdsyl_lst)
    txt.DesPL = statistics.mean(parwrd_lst)
    txt.LdvTTR = txt.DesTotT * 1000 /txt.DesTotW
    txt.WrdCorrTone = txt.DesCorrToneC * 1000 /txt.DesTotW  ## no of correct tone form and phone
    txt.WrdInCorrTone = txt.DesInCorrToneC * 1000 /txt.DesTotW  ## no of incorrect tone form and phone
    txt.WrdCorrFinal = txt.DesCorrFinalC * 1000 /txt.DesTotW  ## no of correct final consonant กก กด กง กน กม เกย เกอว
    txt.WrdInCorrFinal = txt.DesInCorrFinalC * 1000 /txt.DesTotW  ## no of correct final consonant กก กด กง กน กม เกย เกอว
    txt.WrdKaran = txt.DesKaranC * 1000 /txt.DesTotW ## no of karan
    txt.WrdCluster = txt.DesClusterC * 1000 /txt.DesTotW  ## no of DesClusterC
    txt.WrdLead = txt.DesLeadC * 1000 /txt.DesTotW  ## no of DesClusterC
    txt.WrdDoubVowel = txt.DesDoubVowelC * 1000 /txt.DesTotW ## no of double vowel

    txt.WrdNEl = txt.DesNElC * 1000 /txt.DesTotW  ## avg. of NEl
    txt.WrdNEo = txt.DesNEoC * 1000 /txt.DesTotW 
    txt.WrdNEp = txt.DesNEpC * 1000 /txt.DesTotW

    txt.WrdNeg = txt.DesNegC * 1000 /txt.DesTotW ## avg. of Negation

    txt.WrdTNCt1 = txt.DesTNCt1C * 1000 /txt.DesTotW
    txt.WrdTNCt2 = txt.DesTNCt2C * 1000 /txt.DesTotW
    txt.WrdTNCt3 = txt.DesTNCt3C * 1000 /txt.DesTotW
    txt.WrdTNCt4 = txt.DesTNCt4C * 1000 /txt.DesTotW

    txt.WrdTTC1 = txt.DesTTC1 * 1000 /txt.DesTotW
    txt.WrdTTC2 = txt.DesTTC2 * 1000 /txt.DesTotW
    txt.WrdTTC3 = txt.DesTTC3 * 1000 /txt.DesTotW
    txt.WrdTTC4 = txt.DesTTC4 * 1000 /txt.DesTotW

    txt.WrdBasicM = txt.WrdBasicM * 1000 /txt.DesTotW
    txt.WrdBasicT = txt.WrdBasicT * 1000 /txt.DesTotW

    txt.WrdC = txt.WrdC * 1000 /txt.DesTotW
    txt.WrdF = txt.WrdF * 1000 /txt.DesTotW
    txt.WrdCF = txt.WrdCF * 1000 /txt.DesTotW

    txt.WrdFrmSing = txt.WrdFrmSing * 1000 /txt.DesTotW
    txt.WrdFrmTran = txt.WrdFrmTran * 1000 /txt.DesTotW
    txt.WrdFrmComp = txt.WrdFrmComp * 1000 /txt.DesTotW

    txt.WrdSemSimp = txt.WrdSemSimp * 1000 /txt.DesTotW
    txt.WrdSemTran = txt.WrdSemTran * 1000 /txt.DesTotW
    txt.WrdSemSemi = txt.WrdSemSemi * 1000 /txt.DesTotW
    txt.WrdSemOpaq = txt.WrdSemOpaq * 1000 /txt.DesTotW

    txt.WrdTfidf = txt.WrdTfidf/txt.DesTotT
    txt.WrdTncDisp = txt.WrdTncDisp/txt.DesTotT
    txt.WrdTtcDisp = txt.WrdTtcDisp/txt.DesTotT
    txt.WrdArf = txt.WrdArf/txt.DesTotT

    txt.WrdNOUN = txt.WrdNOUN * 1000 /txt.DesTotW
    txt.WrdVERB = txt.WrdVERB * 1000 /txt.DesTotW
    txt.WrdADV = txt.WrdADV * 1000 /txt.DesTotW
    txt.WrdDET = txt.WrdDET * 1000 /txt.DesTotW
    txt.WrdADJ = txt.WrdADJ * 1000 /txt.DesTotW
    txt.WrdADP = txt.WrdADP * 1000 /txt.DesTotW
    txt.WrdPUNCT = txt.WrdPUNCT * 1000 /txt.DesTotW
    txt.WrdAUX = txt.WrdAUX * 1000 /txt.DesTotW
    txt.WrdSYM = txt.WrdSYM * 1000 /txt.DesTotW
    txt.WrdINTJ = txt.WrdINTJ * 1000 /txt.DesTotW
    txt.WrdCCONJ = txt.WrdCCONJ * 1000 /txt.DesTotW
    txt.WrdPROPN = txt.WrdPROPN * 1000 /txt.DesTotW
    txt.WrdNUM = txt.WrdNUM * 1000 /txt.DesTotW
    txt.WrdPART = txt.WrdPART * 1000 /txt.DesTotW
    txt.WrdPRON = txt.WrdPRON * 1000 /txt.DesTotW
    txt.WrdSCONJ = txt.WrdSCONJ * 1000 /txt.DesTotW

    ## create a dictionary output, cretae a dictionary from txt class and merge features dict in txt.pos
    txtfeats = {}
    txtfeats = vars(txt)
#    txtfeats.update(txt.pos)
    txtfeats.update({ 'wrd': txt.wrd})
    txtfeats.update({'wrd_arf': txt.wrd_arf})
    if UDParse != "none":
        txtfeats.update({'deprel': txt.deprel})
#    print(txtfeats)
    return(txtfeats)   


    ### find overlaps of the same word/pos between utterances
def Duplicate_word(pos,lst1,lst2):
    for elem1 in lst1:
        for elem2 in lst2:
            if elem1[0] == elem2[0] and elem1[1] == elem2[1]:
                if elem1[1] == pos:
                   return(True)     
    return(False)

############################################################################
#### save text features from TextAna into json file using option write|append
def TextAna2json(alltext,Filename,TextOption="par",WordOption="colloc", UDParse="none",Mode="write"):
#def TextAna2json(txtfeats,Filename):
    txtfeats = TextAna(alltext,TextOption,WordOption,UDParse)
    if Mode == "append":
        with open(Filename, "a", encoding='utf8') as outfile:
            outfile.write("\n")
            json.dump(txtfeats, outfile, ensure_ascii=False)
    else:        
        with open(Filename, "w", encoding='utf8') as outfile:
            json.dump(txtfeats, outfile, ensure_ascii=False)


##########################################################################
### clessaify text into level L1-L4 or genre
def TextClass(alltext,TextOption="par",WordOption="colloc", UDParse="Malt", Classifier="level"):
    out = {}
    global chk_genre_model
    global chk_level_model

    try:
        chk_genre_model
        chk_level_model
    except NameError:
        text_class_model_load()

    # Load the model from the file
    '''
    if Classifier == "all":

        text_class_model_load()
        filename = 'chklevel_rf.pkl'
        with open(filename, 'rb') as file:
            level_model = pickle.load(file)
        filename = 'chkgenre_rf.pkl'
        with open(filename, 'rb') as file:
            genre_model = pickle.load(file)
    # Load the model from the file
    elif Classifier == "level":
        filename = 'chklevel_rf.pkl'
        with open(filename, 'rb') as file:
            level_model = pickle.load(file)
    # Load the model from the file
    elif Classifier == "genre":
        filename = 'chkgenre_rf.pkl'
        with open(filename, 'rb') as file:
            genre_model = pickle.load(file)
#    elif Classifier == "genre":        
'''
    # Prepare the input data for prediction
    Maltparser_Path = "/Users/awirote/Dropbox/prog/maltparser-1.9.2"

#    print(TextOption,UDParse)
    txtfeatures = TextAna(alltext,TextOption=TextOption,WordOption=WordOption,UDParse=UDParse)

    if Classifier == "level" or Classifier == "all":
        input_df = TranformData_ChkLevel([txtfeatures])
        # Make predictions
        [predicted_level] = chk_level_model.predict(input_df)
        out['level'] = predicted_level
    if Classifier == "genre" or Classifier == "all":
        input_df = TranformData_ChkGenre([txtfeatures])
        [predicted_genre] = chk_genre_model.predict(input_df)
        out['genre'] = predicted_genre
    return(out)


#### and add features that are not in the entry 
def TranformData_ChkLevel(Dat):
    DatN = []
    #print(Dat[0])
    for x in Dat:
        feat = {}
        for y in x:
            if y != 'wrd' and y != 'wrd_arf' and y != 'deprel' :
                feat[y] = x[y] 
            elif y == 'deprel':
                nodeN = {}
                for r in x['deprel']:
                    nodeN[r] = x['deprel'][r]
                    feat.update( {'UD'+r:nodeN[r]} )
        DatN.append(feat)

    #### features useful for checking level
    used_feats = ['SynDepth','UDadvcl','UDamod','CrfCNL','CrfCTL','CrfCWL','DesCorrFinalC','DesEduC','DesEduL','DesEduLd','DesInCorrFinalC','DesTotT','DesTotW','DesTTC2','DesTTC3','DesTTC4','DesWrdL','DesWrdLd','LdvTTR','UDnmod','UDnummod','UDobj','WrdADJ','WrdADP','WrdADV','WrdArf','WrdBasicM','WrdBasicT','WrdC','WrdCF','WrdCorrTone','WrdDET','WrdFrmTran','WrdInCorrFinal','WrdLead','WrdNEo','WrdNUM','WrdPRON','WrdPROPN','WrdSYM','WrdTfidf','WrdTNCt1','WrdTTC1','WrdTTC2','WrdTTC3','WrdTTC4','WrdTtcDisp','WrdVERB','level']
    

    for f in DatN:
        diff_keys = used_feats ^ f.keys()  #### find features missing from the entry f
        for k in diff_keys:
            f.update({ k : 0 })   #### add missing feature with 0 value

    df = pd.DataFrame(DatN)
    df = df[df.columns.intersection(used_feats)]
    df = df.drop(['level'],axis=1, errors='ignore')
    df = df.sort_index(axis=1)

    return(df)    

#### and add features that are not in the entry 
def TranformData_ChkGenre(Dat):
    DatN = []
    #print(Dat[0])
    for x in Dat:
        feat = {}
        for y in x:
            if y != 'wrd' and y != 'wrd_arf' and y != 'deprel' :
                feat[y] = x[y] 
            elif y == 'deprel':
                nodeN = {}
                for r in x['deprel']:
                    nodeN[r] = x['deprel'][r]
                    feat.update( {'UD'+r:nodeN[r]} )
        DatN.append(feat)


    #### features useful for checking genre
    used_feats = ["SynDepth", "DesWrLd", "WrdPRON", "CrfNL", "DesEdul", "LvdTR", "WrdAfr", "WrdTcf1", "ROOT", "WrdNTC1", "WrdDET", "DesWrdLd", "WrdTtcDisp", "WrdBasicT", "WrdNUM", "WrdTidf", "WrdADP", "WrdLead", "WrdCorrTone", "CrfCWL", "DesEduc", "DesEduld", "WrdADV", "WrdPROPN", "CrfCTL", "UDpunct", "WrdFrmTran", "WrdBasicM", "WrdCF", "WrdADJ", "WrdNEI", "WrdSemTran", "WrdTtcDisp", "WrdPART", "UDnummod", "WrdInCorrFinal", "WrdCONJ", "WrdSYM", "WrdNOUN", "WrdFrmSing", "CrfCVL", "WrdSemSimp", "WrdNeo", "UDdet", "WrdAUX", "UDacl", "WrdlnCorrTone", "UDcase", "WrdPUNCT", "WrdKaran", "WrdF", "WrdNEp", "WrdSCONJ", "UDamod", "WrdTTC2", "DesTNTC2C", "WrdVERB", "DesLeadC", "WrdNeg", "WrdFrmComp", "WrdTTC3", "DesNEIC", "WrdC", "UDmark", "WrdTNTC3", "DesNegC", "WrdCluster", "DesNEpC", "WrdCorrFinal", "DesTNTC1C", "DesTNTC1C", "DesTNTC1C", "DesNOrC", "DesSymbC", "UDnsubj", "DesTIC2", "DesInCorrFinalC", "DesTotT", "UDcompound", "UDadvmod","ngenre"]

    for f in DatN:
        diff_keys = used_feats ^ f.keys()  #### find features missing from the entry f
        for k in diff_keys:
            f.update({ k : 0 })   #### add missing feature with 0 value

    df = pd.DataFrame(DatN)
    df = df[df.columns.intersection(used_feats)]
    df = df.drop(['ngenre'],axis=1, errors='ignore')
    df = df.sort_index(axis=1)
                      
    return(df)    


#### TransformDara use all feqatures 
def TranformData(Dat):
    DatN = []
    #print(Dat[0])
    for x in Dat:
        feat = {}
        for y in x:
            if y != 'wrd' and y != 'wrd_arf' and y != 'deprel' :
                feat[y] = x[y] 
            elif y == 'deprel':
                nodeN = {}
                for r in x['deprel']:
                    nodeN[r] = x['deprel'][r]
                    feat.update( {'UD'+r:nodeN[r]} )
        DatN.append(feat)

    all_features = ["DesChC", "DesPC", "DesSpC", "UDmark", "UDROOT", "UDxcomp", "UDobj", "UDacl", "UDcompound", "UDadvmod", "UDnmod", "UDcase", "UDobl", "UDdet", "UDnsubj", "UDaux", "UDcc", "UDconj", "UDadvcl", "UDamod", "UDnummod", "UDccomp", "UDpunct", "UDclf", "UDlist", "UDdislocated", "UDflat", "UDcop", "UDcsubj", "UDorphan", "DesEduC", "SynDepth", "DesNElC", "DesNEoC", "DesNEpC", "WrdSCONJ", "DesTNCt1C", "DesTTC1", "WrdF", "WrdSemSimp", "WrdFrmSing", "WrdBasicM", "WrdBasicT", "DesCorrToneC", "DesInCorrToneC", "DesCorrFinalC", "DesInCorrFinalC", "DesKaranC", "DesClusterC", "DesLeadC", "DesDoubVowelC", "DesTotW", "WrdVERB", "WrdC", "WrdNOUN", "WrdSemTran", "WrdFrmComp", "DesTNCt4C", "WrdADV", "WrdCF", "DesSymbC", "WrdPUNCT", "DesTNCt2C", "WrdADP", "WrdDET", "WrdAUX", "WrdPART", "DesNegC", "DesTNCt3C", "WrdCCONJ", "WrdSemSemi", "DesTTC2", "WrdADJ", "WrdNUM", "WrdPROPN", "DesTTC3", "WrdSemOpaq", "WrdPRON", "DesTTC4", "CrfCWL", "CrfCTL", "CrfCNL", "CrfCVL", "WrdArf", "WrdTfidf", "WrdTncDisp", "WrdTtcDisp", "DesTotT", "DesEduL", "DesEduLd", "DesWrdL", "DesWrdLd", "DesPL", "LdvTTR", "WrdCorrTone", "WrdInCorrTone", "WrdCorrFinal", "WrdInCorrFinal", "WrdKaran", "WrdCluster", "WrdLead", "WrdDoubVowel", "WrdNEl", "WrdNEo", "WrdNEp", "WrdNeg", "WrdTNCt1", "WrdTNCt2", "WrdTNCt3", "WrdTNCt4", "WrdTTC1", "WrdTTC2", "WrdTTC3", "WrdTTC4", "WrdFrmTran", "WrdSYM", "WrdINTJ", "UDvocative", "UDfixed", "UDX", "UDappos", "UDiobj", "UDdiscourse", "UDdep", "UDexpl", "UDmwe", "UDparataxis", "UDreparandum", "UDgoeswith"] 

    for f in DatN:
        diff_keys = all_features ^ f.keys()  #### find features missing from the entry f
        for k in diff_keys:
            f.update({ k : 0 })   #### add missing feature with 0 value

    df = pd.DataFrame(DatN)
    df = df[df.columns.intersection(all_features)]
#    df = df.drop(['ngenre'],axis=1, errors='ignore')
    df = df.sort_index(axis=1)
                      
    return(df)    

##########################################################################
### Create feature vector from text input   Option = name/value
### If "name" return list of feature names. If "value" return list of feature values
def txt2feat(alltext,Option="value",TextOption="par",WordOption="colloc", UDParse="Malt"):
    if Option == "name":
        all_features = ["DesChC", "DesPC", "DesSpC", "UDmark", "UDROOT", "UDxcomp", "UDobj", "UDacl", "UDcompound", "UDadvmod", "UDnmod", "UDcase", "UDobl", "UDdet", "UDnsubj", "UDaux", "UDcc", "UDconj", "UDadvcl", "UDamod", "UDnummod", "UDccomp", "UDpunct", "UDclf", "UDlist", "UDdislocated", "UDflat", "UDcop", "UDcsubj", "UDorphan", "DesEduC", "SynDepth", "DesNElC", "DesNEoC", "DesNEpC", "WrdSCONJ", "DesTNCt1C", "DesTTC1", "WrdF", "WrdSemSimp", "WrdFrmSing", "WrdBasicM", "WrdBasicT", "DesCorrToneC", "DesInCorrToneC", "DesCorrFinalC", "DesInCorrFinalC", "DesKaranC", "DesClusterC", "DesLeadC", "DesDoubVowelC", "DesTotW", "WrdVERB", "WrdC", "WrdNOUN", "WrdSemTran", "WrdFrmComp", "DesTNCt4C", "WrdADV", "WrdCF", "DesSymbC", "WrdPUNCT", "DesTNCt2C", "WrdADP", "WrdDET", "WrdAUX", "WrdPART", "DesNegC", "DesTNCt3C", "WrdCCONJ", "WrdSemSemi", "DesTTC2", "WrdADJ", "WrdNUM", "WrdPROPN", "DesTTC3", "WrdSemOpaq", "WrdPRON", "DesTTC4", "CrfCWL", "CrfCTL", "CrfCNL", "CrfCVL", "WrdArf", "WrdTfidf", "WrdTncDisp", "WrdTtcDisp", "DesTotT", "DesEduL", "DesEduLd", "DesWrdL", "DesWrdLd", "DesPL", "LdvTTR", "WrdCorrTone", "WrdInCorrTone", "WrdCorrFinal", "WrdInCorrFinal", "WrdKaran", "WrdCluster", "WrdLead", "WrdDoubVowel", "WrdNEl", "WrdNEo", "WrdNEp", "WrdNeg", "WrdTNCt1", "WrdTNCt2", "WrdTNCt3", "WrdTNCt4", "WrdTTC1", "WrdTTC2", "WrdTTC3", "WrdTTC4", "WrdFrmTran", "WrdSYM", "WrdINTJ", "UDvocative", "UDfixed", "UDX", "UDappos", "UDiobj", "UDdiscourse", "UDdep", "UDexpl", "UDmwe", "UDparataxis", "UDreparandum", "UDgoeswith"] 
        return(sorted(all_features))
    elif Option == "value":    
        Maltparser_Path = "/Users/awirote/Dropbox/prog/maltparser-1.9.2"
        txtfeatures = TextAna(alltext,TextOption="par",WordOption="colloc",UDParse="Malt")

        input_df = TranformData([txtfeatures])
#        df = pd.DataFrame(input_data)
#        input_df = df.sort_index(axis=1)
        return(input_df.iloc[0].tolist())




#############################################################################################################
### Thai grapheme to phoneme
### Input = a chunk of Thai texts
### orginal written in Perl, ported to Python on May 17, 2018
#############################################################################################################
def g2p(Input):
    global SegSep
    global SSegSep
    output = ""
    out = ""
    
    Input = preprocess(Input)
    sentLst = Input.split(SegSep)
    for s in sentLst:
        inLst = s.split(SSegSep)
        for inp in inLst:
            if inp == '': continue            
            objMatch = re.match(r"[^ก-์]+",inp)
            if objMatch:
                out = inp+'<tr/>'+inp
            else:
                y = sylparse(inp)
                out = wordparse(y)
            output = output+out+WordSep
        output = output+'<s/>'    ####write <s/> output for SegSep   
    return(output)        

## return all transcriptions based on syllable parse
def th2ipa_all(inp):
    output = []
    NORMALIZE_IPA = [ ('O', '\u1D10'), ('x', '\u025B'), ('@', '\u0264'), ('N', '\u014B'), ('?', '\u0294'),('U','\u026F'),('|',' '),('~','.'),('^','.'),("'",'.'),('4','5'), ('3','4'), ('2','3'), ('1','2'), ('0','1')]
    
    if inp == '': return([])            
    objMatch = re.match(r"[^ก-์]+$",inp)
    if objMatch:
        output = [(inp,inp)]
    else:
        lst = sylparse_all(inp)
        if lst == []: return([('','')])
        for (th,tran) in lst:
            tran = re.sub(r"([aeiouUxO@])\1",r"\1ː",tran)
            tran = re.sub(r"([ptkc])h",r"\1ʰ",tran)
            for k, v in NORMALIZE_IPA:
                tran = tran.replace(k, v)
            output.append((th,tran))
#            print(th,tran)
    return(output)        




#############################################################################################################
####### Segment syllable using trigram statistics, only strings matched with a defined syllable pattern will be created
###### all pronunciations of each syllable
def sylparse(Input):
    global SylSep
    global PRON
    global PRONUN
    
    PRONUN = defaultdict(list)
    schart = defaultdict(dict)
    probEnd = defaultdict(float)
    schartx = {}
    schart.clear()
    probEnd.clear()
    tmp = []
    
    EndOfInput = len(Input)
    for f in PRON:
        for i in range(EndOfInput):
            Inx = Input[i:]
            matchObj = re.match(f,Inx)
            if matchObj:
                keymatch = matchObj.group()
                try:
                    matchObj.group(3)
                    charmatch = matchObj.group(1) + ' ' + matchObj.group(2) + ' ' + matchObj.group(3)
                except IndexError:
                    try:
                        matchObj.group(2)
                        charmatch = matchObj.group(1) + ' ' + matchObj.group(2) 
                    except IndexError:
                        try:
                            matchObj.group(1)
                            charmatch = matchObj.group(1) 
                        except IndexError:
#                            PRONUN[matchObj.group()].append(PRON[f])
#                            print("ADD",PRON[f]) 
                            PRONUN[matchObj.group()].extend(PRON[f])
                k=i+len(matchObj.group())
                schart[i][k] = [matchObj.group()]
#                print("Match PRON",schart[i][k],i,k)   
                #### expand all pronunciations
                for PronF in PRON[f]:
#                    print(f,PronF) #....
                    codematch = re.sub(r"[^AKYDZCRX]","",PronF)
                    if codematch:
#                        print("code char",codematch,charmatch)            
                        phone = ReplaceSnd(PronF,codematch,charmatch)
#                        print("phone",phone)
                        if  NotExceptionSyl(codematch,charmatch,keymatch,phone):
                            (phone,tone) = ToneAssign(keymatch,phone,codematch,charmatch)
#                            print('assign tone',tone,' to',keymatch,phone) 
#                            if (tone < '5'): phone = re.sub(r'8',tone,phone)          
                            (keymatch,phone) = TransformSyl(keymatch,phone)         
                            if (tone < '5'): 
                                phone = re.sub(r'8',tone,phone)          
                                PRONUN[''.join(schart[i][k])].append(phone)
#                                print("Add",PronF,''.join(schart[i][k]), phone)  
                        if  re.match(r'ทร',keymatch)  and  re.match(r"thr",phone):            #### gen more syllable  ทร   thr => s
                            phone=re.sub(r"thr","s",phone) 
                            PRONUN[''.join(schart[i][k])].append(phone)
#                            print("Add2",PronF,''.join(schart[i][k]), phone)
                    else:
                        PRONUN[''.join(schart[i][k])].append(PronF)
#                        print('add',PronF)
                    probEnd[(i,k)] = prob_trisyl(schart[i][k])

#                codematch = PRON[f]
#                codematch = re.sub(r"[^AKYDZCRX]","",codematch)
#                if codematch:
#                    print("code char",codematch,charmatch)            
#                    phone = ReplaceSnd(PRON[f],codematch,charmatch)
#                    if  NotExceptionSyl(codematch,charmatch,keymatch,phone):
#                        (phone,tone) = ToneAssign(keymatch,phone,codematch,charmatch)
#                        print('assign tone',tone,' to',keymatch)
#                        if (tone < '5'): phone = re.sub(r'8',tone,phone)          
#                        (keymatch,phone) = TransformSyl(keymatch,phone)         
#                    PRONUN[''.join(schart[i][k])].append(phone)
#                    print("Add",PRON[f],''.join(schart[i][k]), phone)
#                    if  re.match(r'ทร',keymatch)  and  re.match(r"thr",phone):            #### gen more syllable  ทร   thr => s
#                        phone=re.sub(r"thr","s",phone) 
#                        PRONUN[''.join(schart[i][k])].append(phone)
#                        print("Add2",PRON[f],''.join(schart[i][k]), phone)
#                    probEnd[(i,k)] = prob_trisyl(schart[i][k])


    for j in range(EndOfInput):
        schartx = deepcopy(schart)
        if j in schart[0]:
            s1 = schart[0][j]
            for k in schart[j]:
                    s2 = schart[j][k]
                    tmp = mergekaran1(s1+s2)
                    if k not in schart[0]:                        
                        schartx[0][k] = tmp
                        probEnd[(0,k)] = prob_trisyl(tmp)
#                        print("Not Found K",tmp,probEnd[(0,k)])  
                    else:
                        p = prob_trisyl(tmp)
#                        print(p,"<>",probEnd[(0,k)])
#                        if p >= probEnd[(0,k)]:
                        if p > probEnd[(0,k)]:
                            schartx[0][k] = tmp 
                            probEnd[(0,k)] = p
#                            print("Found K new",tmp,probEnd[(0,k)])
        schart = deepcopy(schartx)
    if EndOfInput in schart[0]:    
        return(SylSep.join(schart[0][EndOfInput]))
    else:
        return('<Fail>'+Input+'</Fail>')

def sylparse_all(Input):
    global SylSep
    global PRON
    global PRONUN
    
    PRONUN = defaultdict(list)
    phchart = defaultdict(dict)
    schartx = {}
    phchart.clear()
    tmp = []
    
    EndOfInput = len(Input)
    for f in PRON:
        if f == '([ก-ฮ])' and PRON[f] == ['XOO']: continue
        for i in range(EndOfInput):
            Inx = Input[i:]
            matchObj = re.match(f,Inx)
            if matchObj:
                keymatch = matchObj.group()
                try:
                    matchObj.group(3)
                    charmatch = matchObj.group(1) + ' ' + matchObj.group(2) + ' ' + matchObj.group(3)
                except IndexError:
                    try:
                        matchObj.group(2)
                        charmatch = matchObj.group(1) + ' ' + matchObj.group(2) 
                    except IndexError:
                        try:
                            matchObj.group(1)
                            charmatch = matchObj.group(1) 
                        except IndexError:
#                            PRONUN[matchObj.group()].append(PRON[f])
                            PRONUN[matchObj.group()].extend(PRON[f])
                k=i+len(matchObj.group())
                frm = matchObj.group()

                for PronF in PRON[f]:
#                codematch = PRON[f]
                    codematch = re.sub(r"[^AKYDZCRX]","",PronF)
                    if codematch:
#                        print("code char",codematch,charmatch)            
                        phone = ReplaceSnd(PronF,codematch,charmatch)
                        if  NotExceptionSyl(codematch,charmatch,keymatch,phone):
                            (phone,tone) = ToneAssign(keymatch,phone,codematch,charmatch)
                            if (tone < '5'): phone = re.sub(r'8',tone,phone)          
                            (keymatch,phone) = TransformSyl(keymatch,phone)
    #                        phchart[0][k] = {frm+'/'+phone:1}
                            if k not in phchart[i]:
                                phchart[i][k] = {frm+'/'+phone:1}
                            else:
                                phchart[i][k].update({frm+'/'+phone:1})
    #                        print(i,k,frm,phone)     
                            if  re.match(r'ทร',keymatch)  and  re.match(r"thr",phone):            #### gen more syllable  ทร   thr => s
                                phone=re.sub(r"thr","s",phone) 
    #                            PRONUN[''.join(schart[i][k])].append(phone)
                    else:
                        frm = f
                        phone = PronF

                    if k not in phchart[i]:
                        phchart[i][k] = {frm+'/'+phone:1}
                    else:
                        phchart[i][k].update({frm+'/'+phone:1})
                        
    
    for j in range(EndOfInput):
        schartx = deepcopy(phchart)
        if j in phchart[0]:
            for s1 in phchart[0][j]:
                for k in phchart[j]:
                    for s2 in phchart[j][k]:
    #                    tmp = mergekaran1(s1+s2)
                        tmp = s1+'~'+s2
                        if k not in schartx[0]:
                            schartx[0][k] = {tmp:1}
                        else:
                            schartx[0][k].update({tmp:1})
        phchart = deepcopy(schartx)
        
    outlst = []
    if EndOfInput not in phchart[0]: return([])
    for out in phchart[0][EndOfInput]:
        form = []
        ph = []
        for x in out.split('~'):
            (f,p) = x.split('/')
            form.append(f)
            ph.append(p)
        outlst.append(('~'.join(form),'~'.join(ph)))
#        print(form,ph)
    return(outlst)    

def ReplaceSnd(phone,codematch,charmatch):
     global stable
     snd = phone
     tmp1Lst = charmatch.split(' ')   #get character
     i=0
     for x in list(codematch):
          s = stable[x][tmp1Lst[i]]
          snd = re.sub(x,s,snd)
          i += 1 
     snd += '8'
#     print('Sound',snd)
     return(snd)

def NotExceptionSyl(codematch,charmatch,form,phone):
    if re.search(r'\.',form):  return(True)
##  check pronunciation marked in syllable dict, if it exists and it is different from the current phone, disregard current phone.
    if 'CR' in codematch:        
#exception for CR = ถร  ผร  ดล  ตล ถล ทล บล ดว ตว ถว ทว บว ปว ผว สว
        if re.match(r'ผ ร|ด ล|ต ล|ท ล|ด ว|ต ว|ท ว|บ ว|ป ว|พ ว|ฟ ว|ผ ว|ส ล|ส ว|ร ร|ศ ล|ศ ว',charmatch):  return(False)
#exception for AK = กย กง ขง คง คม จง จน จก ฉย ชง ดย ดง ดน ดม ถย บย บง บน บม ปง ผม พง ฟย ฟง ฟน ฟม ซย ซง ซน ซม  ถร บล บว ปว พร พว นน ยด คว
    if 'AK' in codematch:  #check for leadnng and following consonant
        clst = charmatch.split(' ')
        if clst[1] not in AK[clst[0]]: return(False)

#Case 1 xัว with sound like "..aw"
    if re.search(r'\u0E31[\0E48-\u0E4B]?ว]',form) and 'aw' in phone: return(False)
#Case 5 check for speller ข Only 3 vowel forms can be used  ัุ   เ
    if re.search(r'[ก-ฮ] ข',charmatch) and not re.search(r'[\u0E38\u0E31\u0E40]',form): return(False)
    return(True)
# Case  xร - xon   except  Xรน (กรน ปรน)
'''    if re.search(r'[ก-ฮ] ร$',charmatch) and re.search(r'.an',phone):
        print(codematch,charmatch,form,phone) 
        sys.exit()
        return(False)
    return(True)
'''

#######################################
# Tone assign :  ม้าน, maan, codematch XY,  charmatch  ม น,  => return 3
# ToneAssign($keymatch,$phone,$codematch,$charmatch); 
#######################################
def ToneAssign(keymatch,phone,codematch,charmatch):
#    print("ToneAssign:",keymatch,phone,codematch,charmatch)
    if phone == '' : return('','9')
    lead = ''
    init = ''
    final = ''
    if re.search(r'[0-4]8',phone):   # tone is already assigned
        phone = re.sub(r'([0-4])8',r'\1',phone)
        return(phone,'')
    if 'X' in codematch or codematch == 'GH' or codematch == 'EF':
        lx = charmatch.split(' ')
        lead = ''
        init = lx[0]
        if len(lx) > 1:
            final = lx[1]
        else: final = ''    
    elif re.search(r'AK',codematch) or re.search(r'CR',codematch):
#        (lead, init, final) = charmatch.split(' ')
        lx = charmatch.split(' ')
        lead = lx[0]
        if len(lx) > 2:
            final = lx[2]
            init = lx[1]
        elif len(lx) >1:    
            init = lx[1]
            final = ''

    deadsyll = DeadSyl(phone)
#    print('dead syallble',phone,deadsyll,lead,init,final)

### change + for leading syllable
    if "+'" in phone:
#        print('found leading',phone,lead)
        if lead in 'ผฝถขสหฉศษ':
            phone = re.sub(r'\+','1',phone)
        elif lead in 'กจดตบปอ':
            phone = re.sub(r'\+','1',phone)
        else:    
            phone = re.sub(r'\+','3',phone)

#### normal syllable 
    if init in 'กจดตฎฏบปอ':   # middle consonant
        if deadsyll == 'L':
            if re.search(r'\u0E48',keymatch): return(phone,'1')   #Maiaek
            elif re.search(r'\u0E49',keymatch): return(phone,'2')  #Maitoo
            elif re.search(r'\u0E4A',keymatch): return(phone,'3')  #Maitri
            elif re.search(r'\u0E4B',keymatch): return(phone,'4')  #Maijatawa
            else: return(phone,'0')
        else:
            if re.search(r'\u0E48',keymatch): return(phone,'9')   #Maiaek
            elif re.search(r'\u0E49',keymatch): return(phone,'2')  #Maitoo
            elif re.search(r'\u0E4A',keymatch): return(phone,'3')  #Maitri
            elif re.search(r'\u0E4B',keymatch): return(phone,'4')  #Maijatawa
            else: return(phone,'1')
    elif init in 'ขฃฉฐถผฝสศษห':   # high consonant
        if deadsyll == 'L':
            if re.search(r'\u0E48',keymatch): return(phone,'1')   #Maiaek
            elif re.search(r'\u0E49',keymatch): return(phone,'2')  #Maitoo
            elif re.search(r'\u0E4A',keymatch): return(phone,'9')  #Maitri
            elif re.search(r'\u0E4B',keymatch): return(phone,'9')  #Maijatawa
            else: return(phone,'4')
        else:
            if re.search(r'\u0E48',keymatch): return(phone,'9')   #Maiaek
            elif re.search(r'\u0E49',keymatch): return(phone,'2')  #Maitoo
            elif re.search(r'\u0E4A',keymatch): return(phone,'9')  #Maitri
            elif re.search(r'\u0E4B',keymatch): return(phone,'9')  #Maijatawa
            else: return(phone,'1')
    elif init in 'งญณนมยรลวฬ' and lead != '' and lead in 'ขฃฉฐถผฝสศษห':  #low consonant single
#        if lead in 'ขฃฉฐถผฝสศษห':   # lead by high consonant
            if deadsyll == 'L':
                if re.search(r'\u0E48',keymatch): return(phone,'1')   #Maiaek
                elif re.search(r'\u0E49',keymatch): return(phone,'2')  #Maitoo
                elif re.search(r'\u0E4A',keymatch): return(phone,'9')  #Maitri
                elif re.search(r'\u0E4B',keymatch): return(phone,'9')  #Maijatawa
                else: return(phone,'4')
            else:
                if re.search(r'\u0E48',keymatch): return(phone,'9')   #Maiaek
                elif re.search(r'\u0E49',keymatch): return(phone,'2')  #Maitoo
                elif re.search(r'\u0E4A',keymatch): return(phone,'9')  #Maitri
                elif re.search(r'\u0E4B',keymatch): return(phone,'9')  #Maijatawa
                else: return(phone,'1')
    elif init in 'งญณนมยรลวฬ' and lead != '' and lead in 'กจดตฎฏบปอ':  #low consonant single
#        elif lead in 'กจดตฎฏบปอ':  #lead by middle consonant
            if deadsyll == 'L':
                if re.search(r'\u0E48',keymatch): return(phone,'1')   #Maiaek
                elif re.search(r'\u0E49',keymatch): return(phone,'2')  #Maitoo
                elif re.search(r'\u0E4A',keymatch): return(phone,'3')  #Maitri
                elif re.search(r'\u0E4B',keymatch): return(phone,'4')  #Maijatawa
                else: return(phone,'0')
            else:
                if re.search(r'\u0E48',keymatch): return(phone,'9')   #Maiaek
                elif re.search(r'\u0E49',keymatch): return(phone,'2')  #Maitoo
                elif re.search(r'\u0E4A',keymatch): return(phone,'3')  #Maitri
                elif re.search(r'\u0E4B',keymatch): return(phone,'4')  #Maijatawa
                else: return(phone,'1')
    elif init in 'คฅฆชฌซฑฒทธพภฟฮงญณนมยรลวฬฤฦ': #low consonant
        if deadsyll == 'L':
            if re.search(r'\u0E48',keymatch): return(phone,'2')   #Maiaek
            elif re.search(r'\u0E49',keymatch): return(phone,'3')  #Maitoo
            elif re.search(r'\u0E4A',keymatch): return(phone,'9')  #Maitri
            elif re.search(r'\u0E4B',keymatch): return(phone,'9')  #Maijatawa
            else: return(phone,'0')        
        elif re.search(r'[aeiouxOU\@][aeiouxOU\@]+',phone):  # long vowel
            if re.search(r'\u0E48',keymatch): return(phone,'9')   #Maiaek
            elif re.search(r'\u0E49',keymatch): return(phone,'3')  #Maitoo
            elif re.search(r'\u0E4A',keymatch): return(phone,'9')  #Maitri
            elif re.search(r'\u0E4B',keymatch): return(phone,'4')  #Maijatawa
            else: return(phone,'2')
        else:    # short vowel
            if re.search(r'\u0E48',keymatch): return(phone,'2')   #Maiaek
            elif re.search(r'\u0E49',keymatch): return(phone,'9')  #Maitoo
            elif re.search(r'\u0E4A',keymatch): return(phone,'9')  #Maitri
            elif re.search(r'\u0E4B',keymatch): return(phone,'4')  #Maijatawa
            else: return(phone,'3')

#########################################
# Check whether it's a dead syllable : input is a pronunciation, return 'D' or 'L'
##########################################
def DeadSyl(phone):
    inx = phone
    inx = re.sub('ch','C',inx)
    inx = re.sub(r'[0-4]','',inx)
    if re.search(r'[mnwjlN]8?$',inx):
        return('L')
    elif re.search(r'[pktfscC]8?$',inx):
        return('D')
    elif re.search(r'([aeiouxOU\@])\1',inx):  # vowel length > 1
        return('L')
    else:
        return('D')

def DeadSylx(phone):
    inx = phone
    inx = re.sub('ch','C',inx)
    inx = re.sub(r'[0-4]','',inx)
    if re.search(r'([aeiouxOU\@])\1',inx):  # vowel length > 1
        if re.search(r'[pktfscC]8?$',inx):  # end with p k t f s c ch
            return('Dl')
        else:
            return('Ll')
    else:            
        if re.search(r'[mnwjlN]8?$',inx):
            return('Ls')
        else:
            return('Ds')               

def TransformSyl(form,phone):
# xxY[12]  eeY[12] @@Y[12]  => ลดสระสั้น  ใน Y = [nmN]
    if re.search(r'xx[nmN][12]',phone):
        phone = re.sub(r'xx','x',phone)
    elif re.search(r'ee[nmN][12]',phone):
        phone = re.sub(r'ee','e',phone)
    elif re.search(r'\@\@[nmN][12]',phone):
        phone = re.sub(r'\@\@','\@',phone)
#Case 1 อยxxx change sound "?a1'jxxx" to "jxxx"
    if re.search(r'^อย่า$|^อยู่$|^อย่าง$|^อยาก$',form) and "'" in phone:
        x = phone.split("'")
        phone = x[-1]
#Case 2 หxxx change spund "ha1'xxx" to "xxx"
    elif 'ห' in form and 'ha1' in phone and not re.search(r'หนุ$|หก|หท|หพ|หฤ|หโ',form):
        x = phone.split("'")
        phone = x[-1]
#Case 3 arti-cluster sound, sound "r" is deleted
    elif re.search(r'[จซศส]ร',form) and re.search(r'[cs]r',phone) and re.search(r"[^']",phone):
        phone = re.sub('r','',phone)
    return (form,phone)
    
#### word segment and select the most likely pronunciation in a word    
def wordparse(Input):
    global TDICT
    global EndOfSent
    global chart
    global SegSep
    global WordSep
    global CollocSt
    
    maiyamok_find = r"(<tr/>|\|)" + r"([?a-zENOU0-9~'@^]+?)"  + r"[|~]ๆ"
    maiyamok_rep = r"\1\2" + WordSep + r"\2"

    part = []
    chart = defaultdict(dict)
    SylSep = '~'
    outx = ""
    chart.clear()
    CollocSt = defaultdict(float)
    
    part = Input.split(SegSep)
#    print('part',part,'xxx')
    for inx in part:
        SylLst = inx.split(SylSep)
        EndOfSent = len(SylLst)
        ######### Gen unknown word by set each syllable as a potential word
#        gen_unknown_thaiw(SylLst)
        for i in range(EndOfSent):
            chart[i][i+1] = [SylLst[i]]
#            print("sylchart",i,chart[i][i+1])
        ############################################################
        for i in range(EndOfSent):
            for j in range(i,EndOfSent+1):
                wrd = ''.join(SylLst[i:j])
#                if wrd in TDICT:
#                    chart[i][j] = [wrd]
                chart[i][j] = ['~'.join(SylLst[i:j])]
#                print("chart",i,j,chart[i][j])
                if j > i+1:   ### more than one syllable, compute St
                    St = 0.0
                    NoOfSyl = len(SylLst[i:j])
                    for ii in range(i,j-1):
                        St += compute_colloc("mi",SylLst[ii],SylLst[ii+1])
                    CollocSt[(i,j)] = St    #### Compute STrength of the word
                else:   ### one sylable word St = 0
                    CollocSt[(i,j)] = 0.0
        if chart_parse():
            outx += WordSep.join(chart[0][EndOfSent])
            outx = outx.replace('~ๆ','|ๆ')
            outx += '<tr/>'
            outp = []
            for  wx in chart[0][EndOfSent]:
                tmp = wx.split(SylSep)
                op = SelectPhones(tmp)    
                outp.append(op)
            outx += WordSep.join(outp)
### replace duplicate word for ๆ
            outx = re.sub(maiyamok_find,maiyamok_rep,outx)        
            return(outx)
        else:
            return("<Fail>"+Input+"</Fail>")
    
## input = list of syllables
## output = syl/pron-syl/pron-syl/pron
def SelectPhones(slst):
   global PRONUN 
   p=''
   out = []
   prmax = 0.

   slst = ['|'] + slst + ['|']
#   print('slist',slst)
   i = 1
   for i in range(1,len(slst)-1):
        outp = ''
        prmax = 0.
#        if slst[i] == '|': continue
        if len(PRONUN[slst[i]]) == 1:
            out.append(PRONUN[slst[i]][0])
            continue
        else:
            for p in PRONUN[slst[i]]:
                pr = ProbPhone(p, slst[i-1],slst[i],slst[i+1])
#                print(slst[i],' pronounce ',p,pr,prmax) 
                if pr > prmax:
                   prmax = pr
                   outp = p
                elif pr == prmax:
                   if re.search(r"'",p)  and len(p) > len(outp):
                      prmax = pr
                      outp = p
        out.append(outp)
#        print('out',slst[i],out)
        i += 1
#   print('Select Phone',out)       
   return('~'.join(out))


####################
def ProbPhone(p,pw,w,nw):
    global PhSTrigram
    global FrmSTrigram
    global PhSBigram
    global FrmSBigram
    global PhSUnigram
    global FrmSUnigram
    global AbsUnigram
    global AbsFrmSUnigram

    p3=0.
    p2=0.
    p1=0.
    p0=0.
    if PhSTrigram[(pw,w,nw,p)] > 0.:
        p3 = (1. + math.log(PhSTrigram[(pw,w,nw,p)])) / (1. + math.log(FrmSTrigram[(pw,w,nw)]))
#        print('Trigram',pw,w,nw,p,PhSTrigram[(pw,w,nw,p)],"=>",p3)
    if PhSBigram[(pw,w,p)] > 0.:
        p2 = (1. + math.log(PhSBigram[(pw,w,p)])) / (1. + math.log(FrmSBigram[(pw,w)])) * 0.25
#        print('Bigram1',pw,w,p,PhSBigram[(pw,w,p)],"=>",p2)
### check w and next w because following syllable is important to determine the linking sound  give it more weigth x 3/4
    if PhSBigram[(w,nw,p)] > 0.:
        p2 = p2 + (1. + math.log(PhSBigram[(w,nw,p)])) / (1. + math.log(FrmSBigram[(w,nw)])) * 0.75
#        print('Bigram2',w,nw,p,PhSBigram[(w,nw,p)],"=>",p2)
    if PhSUnigram[(w,p)] > 0.:
        p1 = (1 + math.log(PhSUnigram[(w,p)])) / (1. + math.log(FrmSUnigram[w]))
#        print('Unigram',w,p,PhSUnigram[(w,p)],"=>",p1)

#    prob =  0.8*p3 + 0.16*p2 + 0.03*p1 + 0.00000000001
#    return(prob)
### get abstract form of sounds

    abs_w = re.sub(r"[่้๊๋]","",w)
    abs_w = re.sub(r"[ก-ฮ]","C",abs_w)
    abs_p = re.sub(r"[0-9]","",p)
    abs_p = re.sub(r"[^aeio@OuxU]","C",abs_p)
    if AbsUnigram[(abs_w,abs_p)] > 0.:
        p0 = (1 + math.log(AbsUnigram[(abs_w,abs_p)])) / (1. + math.log(AbsFrmSUnigram[abs_w]))
#        print('AbsUnigram',p0)
    prob =  0.8*p3 + 0.16*p2 + 0.03*p1 + 0.00001*p0 + 0.00000000001
#    print(prob)
    return(prob)



#############
def th2read(txt):
    out = ''
    inx = g2p(txt)
    
    for seg in inx.split('<s/>'):
        if seg == '': continue
        (th, tran) = seg.split('<tr/>')
#        print(tran)
#        tran = re.sub(r"([aeiouUxO@])\1",r"\1ː",tran)
#        tran = re.sub(r"([ptkc])h",r"\1ʰ",tran)
#        for k, v in NORMALIZE_IPA:
#            tran = tran.replace(k, v)
        for syl in re.split("~|\||\^|\'",tran):
            if syl != '':
                thread = PhoneToThai(syl)
                out += thread + '-'
#                print(out)
    return(out)

def PhoneToThai(syl):
    Maiaek = '่'
    Maitoo = '้'
    Maitri = '๊'
    Maijatawa = '๋'
#    Pinthu ='ฺ'
#    print('syl',syl)
    InitCT = {'w':'ว','r':'ร','t':'ต','th':'ท','p':'ป','ph':'พ','s':'ซ','d':'ด','f':'ฟ','h':'ฮ','j':'ย','k':'ก','kh':'ค','l':'ล','c':'จ','ch':'ช','b':'บ','n':'น','N':'ง','m':'ม','?':'อ','br':"บ\u0E3Aร",'bl':"บ\u0E3Aล",'dr':"ด\u0E3Aร",'dl':"ด\u0E3Aล",'kr':"ก\u0E3Aร",'kl':"ก\u0E3Aล",'kw':"ก\u0E3Aว",'khr':"ค\u0E3Aร",'khl':"ค\u0E3Aล",'khw':"ค\u0E3Aว",'tr':"ต\u0E3Aร",'thr':"ท\u0E3Aร",'thl':"ท\u0E3Aล",'pr':"ป\u0E3Aร",'pl':"ป\u0E3Aล",'phr':"พ\u0E3Aร",'phl':"พ\u0E3Aล",'fr':"ฟ\u0E3Aร",'fl':"ฟ\u0E3Aล",'sr':"ส\u0E3Aร"}
    FinalCT = {'w':'ว','t':'ด','p':'บ','s':'ส','f':'ฟ','j':'ย','k':'ก','l':'ล','n':'น','N':'ง','m':'ม','c':'จ','ch':'ช'}
    VowelT = {'a':'xTะ','aa':'xTา','i':'xิT','ii':'xีT','e':'เxTะ','ee':'เxT','u':'xุT','uu':'xูT','o':'โxTะ','oo':'โxT','x':'แxTะ','xx':'แxT','O':'เxTาะ','OO':'xTอ','@':'เxTอะ','@@':'เxTอ','U':'xึT','UU':'xือT','ia':'เxีTยะ','iia':'เxีTย','ua':'xัTวะ','uua':'xัTว','Ua':'เxืTอะ','UUa':'เxืTอ'}

    mt = re.match(r"^(.+?)([aeioux@OU]+)(.*)([0-4])",syl) ## แยกหา initial + vowel + final + tone  เก็บสิ่งที่แยกได้ใน $1 $2 $3 $4 ตามลำดับ
   ## map คัวอักษรของ initial, vowel, final
    it = InitCT[mt.group(1)]    
    vt = VowelT[mt.group(2)]
    if mt.group(3): 
        ft = FinalCT[mt.group(3)]
    else:
        ft = ''    
    if  (it == '' or vt == '' or (ft == '' and mt.group(3) != '') ):
        return('?')
    tone = mt.group(4)
#    print('initial',it,'vowel',vt,'final',ft,tone)
   ##  set syllable = vowel form ที่ได้ ซึ่งมี x  แทนตำแหน่ง initial C,  T แทน tone marker
   ##  check ว่าเป็น dead syllable
    deadsyl = DeadSylx(syl)
   ### ผันวรรณยุกต์ตามกฎ  และใช้อักษรสูงช่วยผัน
    if 'L' in deadsyl:
        if re.search(r"[กจดตบปอ]",it ):
            if tone == '1':
                vt = vt.replace('T',Maiaek)
            elif tone == '2':
                vt = vt.replace('T',Maitoo)
            elif tone == '3':                 
                vt = vt.replace('T',Maitri)
            elif tone == '4':                 
                vt = vt.replace('T',Maijatawa)
            elif tone == '0':                 
                vt = vt.replace('T','')
        else:
            if tone == '1':
                it = it.replace('ค','ข')
                it = it.replace('ฟ','ฝ')
                it = it.replace('พ','ผ')
                it = it.replace('ซ','ส')
                it = it.replace('ฮ','ห')
                it = it.replace('ช','ฉ')
                it = it.replace('ท','ถ')
                it = it.replace('ย','หฺย')
                it = it.replace('น','หฺน')
                it = it.replace('ง','หฺง')
                it = it.replace('ม','หฺม')
                it = it.replace('ว','หฺว')
                it = it.replace('ล','หฺล')
                it = it.replace('ร','หฺร')
                vt = vt.replace('T',Maiaek)
            elif tone == '2':
                vt = vt.replace('T',Maiaek)
            elif tone == '3':
                vt = vt.replace('T',Maitoo)
            elif tone == '4':
                it = it.replace('ค','ข')
                it = it.replace('ฟ','ฝ')
                it = it.replace('พ','ผ')
                it = it.replace('ซ','ส')
                it = it.replace('ฮ','ห')
                it = it.replace('ช','ฉ')
                it = it.replace('ท','ถ')
                it = it.replace('ย','หฺย')
                it = it.replace('น','หฺน')
                it = it.replace('ง','หฺง')
                it = it.replace('ม','หฺม')
                it = it.replace('ว','หฺว')
                it = it.replace('ล','หฺล')
                it = it.replace('ร','หฺร')
                vt = vt.replace('T','')
            elif tone == '0':
                vt = vt.replace('T','')
    else:   ### dead syllable
        if re.search(r"[กจดตบปอ]",it):
            if tone == '1':
                vt = vt.replace('T','')
            elif tone == '2':
                vt = vt.replace('T',Maitoo)
            elif tone == '3':
                vt = vt.replace('T',Maitri)
            elif tone == '4':
                vt = vt.replace('T',Maijatawa)
            elif tone == '0':
                return('?')
        elif  deadsyl == 'Dl':  #$in =~ /[aeiouvxq\@][aeiouvxq\@]+/ )    ### สระยาว คำตาย
            if tone == '1':
                it = it.replace('ค','ข')
                it = it.replace('ฟ','ฝ')
                it = it.replace('พ','ผ')
                it = it.replace('ซ','ส')
                it = it.replace('ฮ','ห')
                it = it.replace('ช','ฉ')
                it = it.replace('ท','ถ')
                it = it.replace('ย','หฺย')
                it = it.replace('น','หฺน')
                it = it.replace('ง','หฺง')
                it = it.replace('ม','หฺม')
                it = it.replace('ว','หฺว')
                it = it.replace('ล','หฺล')
                it = it.replace('ร','หฺร')
                vt = vt.replace('T','')
            elif tone == '2':
                vt = vt.replace('T','')
            elif tone == '3':
                vt = vt.replace('T',Maitoo)
            elif tone == '4':
                vt = vt.replace('T',Maijatawa)
            elif tone == '0':
                return('?')
        else: ## สระสั้น คำตาย 
            if  tone == '1':   
                it = it.replace('ค','ข')
                it = it.replace('ฟ','ฝ')
                it = it.replace('พ','ผ')
                it = it.replace('ซ','ส')
                it = it.replace('ฮ','ห')
                it = it.replace('ช','ฉ')
                it = it.replace('ท','ถ')
                it = it.replace('ย','หฺย')
                it = it.replace('น','หฺน')
                it = it.replace('ง','หฺง')
                it = it.replace('ม','หฺม')
                it = it.replace('ว','หฺว')
                it = it.replace('ล','หฺล')
                it = it.replace('ร','หฺร')
                vt = vt.replace('T','')
            elif tone == '2':
                vt = vt.replace('T',Maiaek)
            elif tone == '3':
                vt = vt.replace('T','')
            elif tone == '4':
                vt = vt.replace('T',Maijatawa)
            elif tone == '0':
                return('?')
    vt = vt.replace('x',it)
    tsyl = vt + ft            
#    $syl = $syl.$ft;
### this is to present pronunciation in Thai word. However, to use the format that most people are familiar
### we have to ignore short,long vowel in some syllables    
    if  ft != '':
        tsyl = re.sub(r"แ([ก-ฮ]?\u0E3A?[ก-ฮ])([่-๋]?)ะ",r"แ\1็\2/",tsyl)   ##  แดะ + น =>  แด็น
        tsyl = re.sub(r"โ([ก-ฮ]?\u0E3A?[ก-ฮ])([่-๋]?)ะ",r"\1\2",tsyl)  ##  โดะ + น => ดน
        tsyl = re.sub(r"เ([ก-ฮ]?\u0E3A?[ก-ฮ])([่-๋]?)อะ",r"เ\1ิ\2",tsyl)    ## เดอะ + น    เดิน
        tsyl = re.sub(r"เ([ก-ฮ]?\u0E3A?[ก-ฮ])([่-๋]?)อ",r"เ\1ิ\2",tsyl)    ##  เดอ + น  จะยังคงเป็น   เดิน   ไม่มีวิธีเขียนปกติ แยก เออะ เออ ที่มีตัวสะกดในไทย
        tsyl = re.sub(r"เ([ก-ฮ]?\u0E3A?[ก-ฮ])([่-๋]?)าะ",r"\1็\2อ",tsyl)    ## เดาะ + น    ด็อน      
        tsyl = re.sub(r"^([ก-ฮ]?\u0E3A?[ก-ฮ])ื([่-๋]?)อ",r"\1ื\2",tsyl)   ##  ดือ + น =>  ดืน
        tsyl = re.sub(r"เ([ก-ฮ]?\u0E3A?[ก-ฮ])([่-๋]?)ะ",r"เ\1็\2",tsyl)    ##  เดะ + น  => เด็น
        tsyl = re.sub(r"([ก-ฮ]?\u0E3A?[ก-ฮ])([่-๋]?)ะย",r"ไ\1\2",tsyl)   ##  ดะ + ย  => ได
        if  'aw' not in syl:
            tsyl = re.sub(r"([ก-ฮ]?\u0E3A?[ก-ฮ])([่-๋]?)ะ",r"\1ั\2",tsyl)   ##  ดะ + น  => ดัน
        else:
            tsyl = re.sub(r"([ก-ฮ]?\u0E3A?[ก-ฮ])([่-๋]?)ะว",r"เ\1\2า",tsyl)   ##  ดะ + ว  => เดา
        tsyl = re.sub(r"([ก-ฮ]?\u0E3A?[ก-ฮ])ั([่-๋]?)ว([กดบมนยง])",r"\1\2ว\3",tsyl)   ##  ดัวง => ดวง
        tsyl = re.sub(r"็([่-๋])",r"\1",tsyl)   ## delete maikaikhoo if precede any tone marker  this will eliminate short/long difference, but it's the way people are familiar
         
    return(tsyl)



#####################    
def th2ipa(txt):
    out = ''
    NORMALIZE_IPA = [ ('O', '\u1D10'), ('x', '\u025B'), ('@', '\u0264'), ('N', '\u014B'), ('?', '\u0294'),('U','\u026F'),('|',' '),('~','.'),('^','.'),("'",'.'),('4','5'), ('3','4'), ('2','3'), ('1','2'), ('0','1')]
    inx = g2p(txt)
    for seg in inx.split('<s/>'):
        if seg == '': continue
        (th, tran) = seg.split('<tr/>')
        tran = re.sub(r"([aeiouUxO@])\1",r"\1ː",tran)
        tran = re.sub(r"([ptkc])h",r"\1ʰ",tran)
        for k, v in NORMALIZE_IPA:
            tran = tran.replace(k, v)
        out += tran+'<s/>'
    return(out)

def th2roman(txt):
    out = ''
    NORMALIZE_ROM = [ ('O', 'o'), ('x', 'ae'), ('@', 'oe'), ('N', 'ng'), ('U','ue'), ('aw','ao'), ('iw','io'), ('ew','eo'), ('?',''), ('|',' '), ('~','-'),('^','-'),("'",'-')]
    inx = g2p(txt)
    for seg in inx.split('<s/>'):
        if seg == '': continue
        (th, tran) = seg.split('<tr/>')
        tran = re.sub(r"([aeiouUxO@])\1",r"\1",tran)
        tran = re.sub(r"[0-9]",r"",tran)
        for k, v in NORMALIZE_ROM:
            tran = tran.replace(k, v)
        tran = re.sub(r"([aeiou])j",r"\1i",tran)
        tran = tran.replace('j','y')
        tran = re.sub(r"c([^h])",r"ch\1",tran)
        tran = re.sub(r"\-([^aeiou])",r"\1",tran)
        out += tran+'<s/>'
    return(out)
    
### end of modules used in g2p  ###############    
##############################################################################################################

    
####################################################################
##  spelling variant of the same pronunciation
####################################################################
def spell_variants(wrd,InDict='no',Karan='exclude'):
    global SYLVAR

    tmp = g2p(wrd)
    tmp = tmp.replace('<s/>','')
    tmp = tmp.replace('|','~')
    (syls, trans) = tmp.split('<tr/>')
    var = []
    out=[]
    tran_lst = trans.split('~')
    syl_lst = syls.split('~')
    for i in range(len(tran_lst)):
        if tran_lst[i] != '':
            if Karan == 'exclude':
                SYLVAR[tran_lst[i]] = [value for value in SYLVAR[tran_lst[i]] if '์' not in value]
            if syl_lst[i] in SYLVAR[tran_lst[i]]:
                var.append(SYLVAR[tran_lst[i]])
            else:    
                var.append([syl_lst[i]])
#    print('var',var)       
    la = var[0]
    for i in range(len(var)-1):
#        print('product',la,var[i+1])
        x = product(la,var[i+1])
        la = []
        for a in x:
            la.append(''.join(a))
    for x in la:
#        print(''.join(x))
        altwrd = ''.join(x)
        if InDict == 'yes':        
            if altwrd in TDICT:
                out.append(altwrd)
        else:        
            out.append(altwrd)
 
#    if len(var) == 2:
#        all_var = product(var[0],var[1])    
#    elif len(var) == 3:    
#        all_var = product(var[0],var[1],var[2])
#    elif len(var) == 4:    
#        all_var = product(var[0],var[1],var[2],var[3])
#    elif len(var) == 5:    
#        all_var = product(var[0],var[1],var[2],var[3],var[4])
#    elif len(var) == 6:    
#        all_var = product(var[0],var[1],var[2],var[3],var[4],var[5])
#    for x in all_var:
#        print('xxx',x)
#        altwrd = ''.join(x)
#        if InDict == 'yes':        
#            if altwrd in TDICT:
#                out.append(altwrd)
#        else:        
#            out.append(altwrd)
    return(out)        




#############################################################################################################


###################################################################
###### Thai word segmentation using maximum collocation approach
###### Input is a list of syllables
###### also add each syllable as a potential word
def wordseg_colloc(Input):
    global TDICT
    global EndOfSent
    global chart
    global SegSep
    global WordSep
    global CollocSt
    
    part = []
    chart = defaultdict(dict)
    SylSep = '~'
    outx = ""
    chart.clear()
    CollocSt = defaultdict(float)
    
    part = Input.split(SegSep)
    for inx in part:
        SylLst = syl_segment(inx).split('~')
        if SylLst[-1] == '<s/>': SylLst.pop()
#        SylLst = inx.split(SylSep)
        EndOfSent = len(SylLst)
        ######### Gen unknown word by set each syllable as a potential word
        gen_unknown_w(SylLst)
#        for i in range(EndOfSent):
#            chart[i][i+1] = [SylLst[i]]
        eng_abbr(SylLst)    
        ############################################################
        for i in range(EndOfSent):
            for j in range(i,EndOfSent+1):
                wrd = ''.join(SylLst[i:j])
                if wrd in TDICT:
                    chart[i][j] = [wrd]
                    if j > i+1:   ### more than one syllable, compute St
                        St = 0.0
                        NoOfSyl = len(SylLst[i:j])
                        for ii in range(i,j-1):
                            St += compute_colloc("mi",SylLst[ii],SylLst[ii+1])
#                            print (SylLst[ii],SylLst[ii+1],xx)
                        CollocSt[(i,j)] = St    #### Compute STrength of the word
#                        print(i,j,wrd,CollocSt[(i,j)])
                    else:   ### one sylable word St = 0
                        CollocSt[(i,j)] = 0.0
        if chart_parse():
#            return(chart[0][EndOfSent])
            outx += WordSep.join(chart[0][EndOfSent])
            return(outx)
        else:
            return("<Fail>"+Input+"</Fail>")
        

####################################################################
#### Word segmentation using Dictionary lookup 
#### Input = Thai string,  method = syl | word  output = n-best segmentations
#### n-best segmentation is determined from the number of words. The fewer the better.
#### Output is a list of n-best segmentation [ [seg1, seg2, seg3, seg4, .... ] ]
#### If input is a multiple chunks of text, the output is the list of chunks' outputs.
#### e.g. [ [c1seg1, c1seg2, c1seg3, c1seg4, .... ] , [c2seg1, c2seg2, c2seg3, c2seg4, .... ] ]
######################################################################
def word_segment_nbest(Input,nbest):
    global SegSep
    global SSegSep
    output = []
    out = []
    
    Input = preprocess(Input)
    sentLst = Input.split(SegSep)
    for s in sentLst:
        inLst = s.split(SSegSep)
        for inp in inLst:
            if inp == '': continue            
            objMatch = re.match(r"[^ก-์]+",inp)  ## not Thai text
            if objMatch:
                out = [inp]
            else:
                out = wordsegmm_bn(inp,nbest)
            output.append(out)    
    return(output)

def wordsegmm_bn(Input,nbest):    
    global TDICT
    global EndOfSent
    global chartnb
    global SegSep
    global WordSep


    part = []
    chartnb = defaultdict(dict)
    outx = []
    chartnb.clear()
    
    part = Input.split(SegSep)
    for inx in part:
        SylLst = list(inx)
        EndOfSent = len(SylLst)
        ## look for all possible words in the string input
        for i in range(EndOfSent):
            for j in range(i,EndOfSent+1):
                wrd = ''.join(SylLst[i:j])
                if wrd in TDICT and wrd != '':
#                    print('wrd',wrd,i,j,SylLst[i:j])
                    chartnb[(i,j)][wrd] = 1
        ## chart parse            
        if chartparse_mm_bn():
            i = 1
            for seg1 in sorted(chartnb[(0,EndOfSent)], key=chartnb[(0,EndOfSent)].get):
#                print(i,seg1)
                outx.append(seg1)
                i += 1
                if i > nbest:
                    break     
        else:
            outx += ["<Fail>"+Input+"</Fail>"]
    return(outx)        


def chartparse_mm_bn():
    global chartnb
    global WordSep
    
    for j in range(EndOfSent):
        chartx = deepcopy(chartnb)
        if j in [ key[1] for key in chartnb if key[0] == 0 ]:
            for s1 in chartnb[(0,j)]:  # get the first part
                for k in [ key[1] for key in chartnb if key[0] == j ]:  # connecting paths 
                     for s2 in chartnb[(j,k)]:  # get the second part
                        path = s1+WordSep+s2
                        if path not in chartnb[(0,k)]:
                            chartx[(0,k)][path] = chartx[(0,j)][s1] + chartx[(j,k)][s2]  ## sum the number of words from s1 and s2
#                            print("New =>",0,j,k,chartx[(0,k)])
        chartnb = deepcopy(chartx)
    if chartnb[(0,EndOfSent)]:
        return(1)
    else:
        return(0)



####################################################################
#### Word segmentation using Maximal Matching (minimal word) approach
#### Input = Thai string,  method = mm|colloc|ngram, 
####   spellchk=yes|no 
######################################################################
def word_segment(Input,method='colloc',spellchk='no'):
    global SegSep
    global SSegSep
    output = ""
    out = ""
    
    Input = preprocess(Input)
    sentLst = Input.split(SegSep)
    for s in sentLst:
#        print ("s:",s)
        inLst = s.split(SSegSep)
        for inp in inLst:
            if inp == '': continue            
            objMatch = re.match(r"[^ก-์]+",inp)
            if objMatch:
                out = inp
            else:
#                print('ss:',inp)
                if method == 'mm' or method == 'ngram':
                    out = wordseg_mm(inp,method,spellchk)
                elif method == 'colloc':
                    out =wordseg_colloc(inp)
#                elif method == 'ngram':
#                    out =wordseg_mm(inp,method,spellchk)
            output = output+out+WordSep
#        output = output.rstrip(WordSep)
        output = output+'<s/>'    ####write <s/> output for SegSep   
    return(output)

def word_segment_mm(Input):
    return(word_segment(Input,method='mm'))

def wordseg_mm(Input,method,spellchk):    
    global TDICT
    global EndOfSent
    global chart
    global SegSep
    global WordSep


    part = []
    chart = defaultdict(dict)
    outx = ""
    chart.clear()
    
    part = Input.split(SegSep)
    for inx in part:
        if method == 'ngram':
            SylLst = syl_segment(inx).split('~')
            SylLst.pop()
#            print('syl',SylLst)
        else:
            SylLst = list(inx)
        EndOfSent = len(SylLst)    
        if spellchk == 'yes' and method == 'ngram':            
            gen_unknown_thaiw(SylLst)
        eng_abbr(SylLst)    
        for i in range(EndOfSent):
            for j in range(i,EndOfSent+1):
                wrd = ''.join(SylLst[i:j])
                if wrd in TDICT:
                    chart[i][j] = [wrd]
                    
        if method == 'ngram':            
            if chartparse_ngram():
                outx += WordSep.join(chart[0][EndOfSent])
            else:
                outx += "<Fail>"+Input+"</Fail>"
        elif method == 'mm':        
            if chartparse_mm():
                outx += WordSep.join(chart[0][EndOfSent])
            else:
                outx += "<Fail>"+Input+"</Fail>"
    return(outx)        

#########  Chart Parsing, ceate a new edge from two connected edges, always start from 0 to connect {0-j} + {j+k}
#########  If minimal word appraoch is chosen, the sequence with fewest words will be selected
def chartparse_mm():
    global chart
    global EndOfSent
    
    for j in range(EndOfSent):
        chartx = deepcopy(chart)
        if j in chart[0]:
            s1 = chart[0][j]
            for k in chart[j]:
                    s2 = chart[j][k]
#                    print 0,j,k
                    if k not in chart[0]:                        
                        chartx[0][k] = s1+s2
                    else:
                        if len(s1)+len(s2) <= len(chart[0][k]):
                            chartx[0][k] = s1+s2
        chart = deepcopy(chartx)
    if EndOfSent in chart[0]:
        return(1)
    else:
        return(0)


### use bigram prob to select the best sequnece
def chartparse_ngram():
    global chart
    global CProb

    CProb.clear()


    for j in range(1,EndOfSent):
        chartx = deepcopy(chart)
        if j in chart[0]:
            s1 = chart[0][j]
            for k in chart[j]:
                    s2 = chart[j][k]
#                    print 0,j,k
                    if k not in chart[0]:                        
                        chartx[0][k] = s1+s2
                        CProb[k] = BigramProb(s1+s2)
#                        print(s1+s2,'new',CProb[k])
                    else:
#                        print(s1+s2,BigramProb(s1+s2),CProb[k])
                        if BigramProb(s1+s2) > CProb[k]:
                            chartx[0][k] = s1+s2
                            CProb[k] = BigramProb(s1+s2)
#                            print(s1+s2,'old',CProb[k])
        chart = deepcopy(chartx)
    if EndOfSent in chart[0]:
        return(1)
    else:
        return(0)

def BigramProb(WLst):
    global CProb

    p=1.
    for i in range(len(WLst)-1):
        cx = tltk.corpus.bigram(WLst[i],WLst[i+1])
        if cx > 0.:
            p += math.log(cx/1000000)
        else:
            p += math.log(0.0001/1000000)    

    return(p)

##########################################
# Compute Collocation Strength between w1,w2
# stat = chi2 | mi | ll
##########################################
def compute_colloc(stat,w1,w2):
    global TriCount
    global BiCount
    global Count
    global BiType
    global Type
    global TotalWord
    global TotalLex

    if BiCount[(w1,w2)] < 1 or Count[w1] < 1 or Count[w2] < 1:
        BiCount[(w1,w2)] +=1
        Count[w1] +=1
        Count[w2] +=1 
        TotalWord +=2
#    print(w1,w2,Count[w1],Count[w2],BiCount[(w1,w2)],TotalWord)    
###########################
##  Mutual Information
###########################
    if stat == "mi":
        mi = float(BiCount[(w1,w2)] * TotalWord) / float((Count[w1] * Count[w2]))
        value = abs(math.log(mi,2))
#########################
### Compute Chisquare
##########################
    if stat == "chi2":
        value=0
        O11 = BiCount[(w1,w2)]
        O21 = Count[w2] - BiCount[(w1,w2)]
        O12 = Count[w1] - BiCount[(w1,w2)]
        O22 = TotalWord - Count[w1] - Count[w2] +  BiCount[(w1,w2)]
        value = float(TotalWord * (O11*O22 - O12 * O21)**2) / float((O11+O12)*(O11+O21)*(O12+O22)*(O21+O22))

    return(value)
    
##############################################################################    
########  create each unit (char/syllable) as a possible edge for chart parsing
def gen_unknown_w(SylLst):
    global chart
    global EndOfSent

    for i in range(EndOfSent):
        chart[i][i+1] = [SylLst[i]]
        if SylLst[i] not in TDICT:
            for j in range(i+1,EndOfSent):
                if SylLst[j] not in TDICT:
                    newwrd = ''.join(SylLst[i:j+1])
                    chart[i][j+1] = [newwrd]
#                    print('Create',SylLst[i],SylLst[j],newwrd)
                else:
                    break    
    return(1)


def gen_unknown_thaiw(SylLst):
    global chart
    global EndOfSent

    for i in range(EndOfSent):
        chart[i][i+1] = [SylLst[i]]
### add one unit that might be misspelled
        if SylLst[i] not in TDICT:
            for newwrd in spell_candidates(SylLst[i]):
                    if newwrd in TDICT:
#                        print(SylLst[i],'1=>',newwrd)
                        chart[i][i+1] = [newwrd]            
### add two or three consecutive units that might be misspelled
        if ''.join(SylLst[i:i+2]) not in TDICT:
           for newwrd in spell_candidates(''.join(SylLst[i:i+2])):
                    if newwrd in TDICT:
#                        print(SylLst[i:i+2],'2=>',newwrd)
                        chart[i][i+2] = [newwrd]
        if ''.join(SylLst[i:i+3]) not in TDICT:
           for newwrd in spell_candidates(''.join(SylLst[i:i+3])):
                    if newwrd in TDICT:
#                        print(SylLst[i:i+3],'3=>',newwrd)
                        chart[i][i+3] = [newwrd]
                        
    return(1)

####  gen a word from a sequence of English abbreviation
####  e.g.  เอบีเอ็น เอ็นบีเค  
def eng_abbr(SylLst):
    global chart
    global EndOfSent
    global EngAbbr
    i=0
    while i < EndOfSent-1:
        if SylLst[i] in EngAbbr:
            j=i+1
            while j<EndOfSent and SylLst[j] in EngAbbr:
                j=j+1
            if j>i+1:
                chart[i][j] = [''.join(SylLst[i:j])]
#                print(SylLst[i:j],'=>EngAbbr')
                i=j+1
            i=i+1    
        else:
            i=i+1
    return(1)



#############################################################################################################
#########  Chart Parsing, ceate a new edge from two connected edges, always start from 0 to connect {0-j} + {j+k}
#########  If maximal collocation appraoch is chosen, the sequence with highest score will be selected
def chart_parse():
    global chart
    global CollocSt
    
    for j in range(EndOfSent):
        chartx = deepcopy(chart)
        if j in chart[0]:
            s1 = chart[0][j]
            for k in chart[j]:
                    s2 = chart[j][k]
                    if k not in chart[0]:                        
                        chartx[0][k] = s1+s2
#                        CollocSt[(0,k)] = (CollocSt[(0,j)] + CollocSt[(j,k)])/2.0
                        CollocSt[(0,k)] = CollocSt[(0,j)] + CollocSt[(j,k)]
                    else:
                        if CollocSt[(0,j)]+CollocSt[(j,k)] > CollocSt[(0,k)]:
#                            CollocSt[(0,k)] = (CollocSt[(0,j)] + CollocSt[(j,k)])/2.0
                            CollocSt[(0,k)] = CollocSt[(0,j)] + CollocSt[(j,k)]
                            chartx[0][k] = s1+s2
        chart = deepcopy(chartx)
    if EndOfSent in chart[0]:
        return(1)
    else:
        return(0)


#############################################################################################################
###  Syllable Segmentation for Thai texts
### Input = a paragraph of Thai texts
def syl_segment(Input):
    global SegSep
    global SSegSep
    output = ""
    out = ""
    
    Input = preprocess(Input)
    sentLst = Input.split(SegSep)
    for s in sentLst:
#        print "s:",s
        inLst = s.split(SSegSep)
        for inp in inLst:
            if inp == '': continue            
            objMatch = re.match(r"[^ก-์]+",inp)
            if objMatch:
                out = inp
            else:
                out = sylseg(inp)
            output = output+out+SylSep
#        output = output.rstrip(SylSep)
        output = output+'<s/>'    ####write <s/> output for SegSep   
    return(output)        

#############################################################################################################
####### Segment syllable using trigram statistics, only strings matched with a defined syllable pattern will be created
####  Input = Thai string
def sylseg(Input):
    global SylSep
    global PRON
    
    schart = defaultdict(dict)
    probEnd = defaultdict(float)
    schartx = {}
    schart.clear()
    probEnd.clear()
    tmp = []
    
    EndOfInput = len(Input)
    for f in PRON:
        for i in range(EndOfInput):
            Inx = Input[i:]
            matchObj = re.match(f,Inx)
            if matchObj:
                k=i+len(matchObj.group())
                schart[i][k] = [matchObj.group()]
                probEnd[(i,k)] = prob_trisyl([matchObj.group()])
#                print("match",i,k, matchObj.group(),f,probEnd[(i,k)])
    
    for j in range(EndOfInput):
        schartx = deepcopy(schart)
        if j in schart[0]:
            s1 = schart[0][j]
            for k in schart[j]:
                    s2 = schart[j][k]
                    ####****** change this to merge only form, need to do this, otherwise probtrisyl is not correct.
                    tmp = mergekaran(s1+s2)
                    if k not in schart[0]:                        
#                        schartx[0][k] = s1+s2
#                        probEnd[k] = prob_trisyl(s1+s2)
                        schartx[0][k] = tmp
                        probEnd[(0,k)] = prob_trisyl(tmp)
#                        print("new",tmp,probEnd[k])
                    else:
#                        p = prob_trisyl(s1+s2)
                        p = prob_trisyl(tmp)
                        if p > probEnd[(0,k)]:
#                            print("replace",tmp,p,probEnd[(0,k)])
#                            schartx[0][k] = s1+s2 
                            schartx[0][k] = tmp 
                            probEnd[(0,k)] = p
        schart = deepcopy(schartx)
    if EndOfInput in schart[0]:    
        return(SylSep.join(schart[0][EndOfInput]))
    else:
        return('<Fail>'+Input+'</Fail>')

######################
def mergekaran(Lst):
####  reconnect karan part to the previous syllable for SylSegment
   rs = []
   Found = 'n'
   Lst.reverse()
   for s in Lst:
        if re.search(r"(.+)[ิุ]์",s):    # anything + i or u + Karan
            if len(s) < 4:
                Found = 'y'
                x = s
                continue
        elif  re.search(r"(.+)์",s):  # anything + Karan
            if len(s) < 4:
                Found = 'y'
                x = s
                continue
        if Found == 'y':
            s += x
            rs.append(s)
            Found = 'n'
        else:
            rs.append(s)
   rs.reverse()
   return(rs)

def mergekaran1(Lst):
####  reconnect karan part to the previous syllable for SylSegment
#### include merhing pronunciation
   rs = []
   global MKaran
   MKaran.clear()
   Found = 'n'
   Lst.reverse()
   for s in Lst:
        if re.search(r"(.+)[ิุ]์",s):    # anything + i or u + Karan
            if len(s) < 4:
                Found = 'y'
                x = s
                continue
        elif  re.search(r"(.+)์",s):  # anything + Karan
            if len(s) < 4:
                Found = 'y'
                x = s
                continue
        if Found == 'y':
            for ph in PRONUN[s]:
                if (s+x,ph) not in MKaran:
                    PRONUN[s+x].append(ph)
                    MKaran[(s+x,ph)] = 1 
            s += x
            rs.append(s)
            Found = 'n'
        else:
            rs.append(s)
   rs.reverse()
   return(rs)

########################################
# calculate proability of each possible output
#  Version 1.6>  expect input = list of forms
########################################
def prob_trisyl(SylLst):
    global TriCount
    global BiCount
    global Count
    global BiType
    global Type
    global TotalWord
    global TotalLex
    global SegSep
    Prob = defaultdict(float)
    
#    SegSep = chr(127)

    pw2 = SegSep
    pw1 = SegSep
    Probx = 1.0
    
    for w in SylLst:
        if (w,pw1,pw2) in Prob:
            Proba = Prob[(w,pw1,pw2)]
        else:
            Prob[(w,pw1,pw2)] = prob_wb(w,pw1,pw2)
            Proba = Prob[(w,pw1,pw2)]
#        Probx *= Proba
        Probx += Proba    ## prob is changed to log
        pw2 = pw1
        pw1 = w
#    print("prob ",SylLst,Probx)
    
    return(Probx)

########################################
# p(w | pw2 pw1)   Smoothing trigram prob  Witten-Bell
#######################################
def prob_wb(w,pw1,pw2):
    global TriCount
    global BiCount
    global Count
    global BiType
    global Type
    global TotalWord
    global TotalLex
    
    p3 = 0.0
    p2 = 0.0
    p1 = 0.0
    p = 0.0
    px1 = 0.0
    
#    print("trigram ", '|',pw2,'|',pw1,'|',w)
#    print("count ",TriCount[(pw2,pw1,w)],BiCount[(pw1,w)],Count[w])
    if TriCount[(pw2,pw1,w)] > 0:
        p3 = float(TriCount[(pw2,pw1,w)]) / float( BiCount[(pw2,pw1)] + BiType[(pw2,pw1)])
    if BiCount[(pw1,w)] > 0:
        p2 = float( BiCount[(pw1,w)]) / float((Count[pw1] + Type[pw1]) )
    if Count[w] > 0:
        p1 = float( Count[w]) / float(TotalWord + TotalLex)
#    p = 0.8 * p3 + 0.15 * p2 + 0.04 * p1 + 1.0 / float((TotalWord + TotalLex)**2)
    p = 0.8 * p3 + 0.15 * p2 + 0.1 * p1 + 1.0 / float((TotalWord + TotalLex))
### change to log to prevent underflow value which can cause incorrect syllable segmentation
    p = math.log(p)
#    print('prob',p)

    return(p)

    

###### Read syllable pattern
def read_sylpattern(Filename):
    global PRON
    global stable
    global AK
    global MKaran
    global EngAbbr
    
    stable = defaultdict(defaultdict)
    AK = defaultdict(str)
    MKaran = defaultdict(int)
#    PRON = defaultdict(list)
#    PRON = defaultdict(str)
    
    tmp = [] 
    file1 = open(Filename,'r',encoding = 'cp874')
    for line in file1:
        if re.match(r'#',line):
            continue
        line = line.rstrip()
        tmp = line.split(',')
        tmp[0] = re.sub(r"X",u"([ก-ฮ])",tmp[0])
        tmp[0] = re.sub(r"C",u"([กขคจดตทบปผพฟสศซ])",tmp[0])
        tmp[0] = re.sub(r'Y',u"([ก-ฬฮ])",tmp[0])
        tmp[0] = re.sub(r'R',u"([รลว])",tmp[0])
        tmp[0] = re.sub(r'K',u"([ก-ฮ])",tmp[0])
        tmp[0] = re.sub(r'A',u"([กจฆดตบปอขฉฐถผฝศษสหคชพภทธมยรลวนณซญฑฏฌ])",tmp[0])
        tmp[0] = re.sub(r'Z',u"([กงดนมบรลฎฏจตณถพศทสชคภปญ])",tmp[0])
        tmp[0] = re.sub(r'D',u"([กงดนมบวยต])",tmp[0])
        tmp[0] = re.sub(r'W',u"[ก-ฮ]",tmp[0])
        tmp[0] = re.sub(r'\.',u"[\.]",tmp[0])
#        re.sub('Q',u"[\(\)\-\:\'\xCF\xE6]",tmp[0])
        if tmp[2] == "T":
            tmp[0] = re.sub(r"T",u"[่้๊๋]",tmp[0])
        else:
            tmp[0] = re.sub(r"T",u"[่้๊๋]*",tmp[0])
            
#       print tmp[0]
#        PRON[tmp[0]] = tmp[1]
        PRON[tmp[0]].append(tmp[1])
    
#    for f in PRON:
#        for x in PRON[f]:
#            print(f,x)
    stable['X'] = { 'ก' : 'k', 'ข' : 'kh' , 'ฃ':'kh', 'ค' : 'kh', 'ฅ' : 'kh','ฆ' : 'kh', 'ง' : 'N', 'จ' : 'c', 'ฉ' : 'ch', 'ช' : 'ch', 'ซ' : 's', 'ฌ' : 'ch','ญ' : 'j','ฎ' : 'd','ฏ' : 't','ฐ' : 'th','ฑ' : 'th','ฒ' : 'th','ณ' : 'n','ด' : 'd','ต' : 't','ถ' : 'th','ท' : 'th','ธ' : 'th','น' : 'n','บ' : 'b','ป' : 'p','ผ' : 'ph','ฝ' : 'f','พ' : 'ph','ฟ' : 'f','ภ' : 'ph','ม' : 'm','ย' : 'j','ร' : 'r','ฤ' : 'r','ล' : 'l','ฦ' : 'l','ว' : 'w','ศ' : 's','ษ' : 's','ส' : 's','ห' : 'h','ฬ' : 'l','อ' : '?','ฮ' : 'h' }
    stable['Y'] = { 'ก' : 'k', 'ข' : 'k' , 'ค' : 'k', 'ฆ' : 'k', 'ง' : 'N', 'จ' : 't', 'ฉ' : '-', 'ช' : 't', 'ซ' : 't', 'ฌ' : '-','ญ' : 'n','ฎ' : 't','ฏ' : 't','ฐ' : 't','ฑ' : 't','ฒ' : 't','ณ' : 'n','ด' : 't', 'ต' : 't','ถ' : 't','ท' : 't','ธ' : 't','น' : 'n','บ' : 'p','ป' : 'p','ผ' : '-','ฝ' : '-','พ' : 'p','ฟ' : 'p','ภ' : 'p','ม' : 'm','ย' : 'j','ร' : 'n','ฤ' : '-','ล' : 'n','ฦ' : '-','ว' : 'w','ศ' : 't','ษ' : 't','ส' : 't' ,'ห' : '-','ฬ' : 'n','อ' : '-','ฮ' : '-' }

    stable['A'] = stable['X']
    stable['K'] = stable['X']
    stable['C'] = stable['X']
    stable['R'] = stable['X']
    stable['G'] = stable['X']
    stable['E'] = stable['X']
    
    stable['D'] = stable['Y']
    stable['Z'] = stable['Y']
    stable['H'] = stable['Y']
    stable['F'] = stable['Y']

    AK['ก'] = "นฎฐณตถบปมรลวษสพหฬ"
    AK['ข'] = "จนณบมยรลฬดตทษภส"
    AK['ค'] = "กชดตนณปมทฑหบ"
    AK['ฆ'] = "กบรสช"
    AK['จ'] = "ณตนมรลทยกด"
    AK['ฉ'] = "กงนบพรลวทม"
    AK['ช'] = "กญนยรลวฎคทบมอ"
    AK['ซ'] = "ล"
    AK['ญ'] = "กภลญ"
    AK['ณ'] = "กร"
    AK['ด'] = "นรมวบ"
    AK['ต'] = "กตนภยรลฆงถบมวฤท"
    AK['ถ'] = "กนลวศพงมร"
    AK['ท'] = "กชนบมยรลวสหงศ"
    AK['ธ'] = "นภมยรวกพช"
    AK['น'] = "กทธฎภมยรวคขปลวห"
    AK['บ'] = "ดรทพม"
    AK['ป'] = "กฐฏณทนภรวศถฎตปยสหด"
    AK['ผ'] = "งจชดนลสวกคณทยรอ"
    AK['ฝ'] = "ร"
    AK['พ'] = "กญนมยลวสหณจธ"
    AK['ภ'] = "ยรคณมฤวน"
    AK['ม'] = "กณตนยรลหศดธมสฆว"
    AK['ย'] = "กดธภวสบศตมนถช"
    AK['ร'] = "กจณดพภมยวสหชตถนบ"
    AK['ล'] = "กคฆดตอบปพมลวห"
    AK['ว'] = "ชณดนพภรลสมยกจฏตทธปฤศหคธ"
    AK['ศ'] = "จณนบรลวศพดธกตมยส"
    AK['ษ'] = "ณฎบภรนคธม"
    AK['ส'] = "กคงดตถนบปพภมยรลวหอจฟสขทธฤ"
    AK['ห'] = "กงพทนรภญนมยรลวบต"
    AK['อ'] = "กงชณดตธนพภมยรลวสศคบฆจทปห"
    AK['ฑ'] = "มสรนค"
    AK['ฐ'] = "กจ"
    AK['ฏ'] = "ก"
    AK['ฌ'] = "ก"

    EngAbbr = ['เอ','บี','ซี','ดี','อี','เอฟ','จี','เจ','เอช','ไอ','เค','แอล','เอ็ม','เอ็น','โอ','พี','คิว','อาร์','เอส','ที','ยู','วี','เอ็กซ์','เอ็ก','วาย','แซด']
    ## cannot add 'ดับบลิว' because it has two syllables

    return(1)


##########  Read syllanle dict, pronunciation not conformed to sylrule is specified here
def read_syldict(Filename):
    global PRON
    
    file1 = open(Filename,'r',encoding='cp874')
    for line in file1:
        if re.match(r'#',line):
            continue
        line = line.rstrip()
        tmp = line.split("\t")
#        PRON[tmp[0]] = tmp[1]
        PRON[tmp[0]].append(tmp[1])
    return(1)

##########  Read syllable pattersn and pronunciation table
def read_PhSTrigram(File):
    global PhSTrigram
    global FrmSTrigram
    global PhSBigram
    global FrmSBigram
    global PhSUnigram
    global FrmSUnigram
    global AbsUnigram
    global AbsFrmSUnigram
    
    PhSTrigram = defaultdict(float)
    FrmSTrigram = defaultdict(float)
    PhSBigram = defaultdict(float)
    FrmSBigram = defaultdict(float)
    PhSUnigram = defaultdict(float)
    FrmSUnigram = defaultdict(float)
    AbsUnigram = defaultdict(float)
    AbsFrmSUnigram = defaultdict(float)
    
    IFile = open(File,'r',encoding='cp874')
    for line in IFile.readlines():
        line = line.rstrip()
        line = re.sub(r"<w>","|",line)
        (x, ct) = line.split('\t')
        (fs,p) = x.split('/')
        (x1,x2,x3) = fs.split('-')
#        print('read ',x1,x2,x3,p,ct)
        PhSTrigram[(x1,x2,x3,p)] += float(ct)
        FrmSTrigram[(x1,x2,x3)] += float(ct)
        PhSBigram[(x1,x2,p)] += float(ct)
        FrmSBigram[(x1,x2)] += float(ct)
        PhSBigram[(x2,x3,p)] += float(ct)
        FrmSBigram[(x2,x3)] += float(ct)
        PhSUnigram[(x2,p)] += float(ct)
        FrmSUnigram[x2] += float(ct)
        abs_x2 = re.sub(r"[่้๊๋]","",x2)
        abs_x2 = re.sub(r"[ก-ฮ]","C",abs_x2)
        abs_p = re.sub(r"[0-9]","",p)
        abs_p = re.sub(r"[^aeio@OuxU]","C",abs_p)
#        print(x2,'=>',abs_x2,':',p,'=>',abs_p)
        AbsUnigram[(abs_x2,abs_p)] += float(ct)
        AbsFrmSUnigram[abs_x2] += float(ct)
    IFile.close()

#### read syllable variants file
def read_sylvar(Filename):
    global SYLVAR

    f = bz2.BZ2File(Filename,'rb')
    SYLVAR = pickle.load(f)
    f.close()

#    fileObject = open(Filename,'rb')  
#    SYLVAR = pickle.load(fileObject)
#    fileObject.close()
    return(1)

#### Read word info from TTC and TNC
def read_wordtier(File):
    global WRD
    WRD = defaultdict(dict)

    f = bz2.BZ2File(File,'rb')
    WRD = pickle.load(f)
    f.close()

    return(1)

####  read trigram statistics file
def read_stat(Filename):
    global TriCount
    global BiCount
    global Count
    global BiType
    global Type
    global TotalWord
    global TotalLex
    global TotalWord
    global TotalLex

    TriCount = defaultdict(int)
    BiCount = defaultdict(int)
    BiType = defaultdict(int)
    Count = defaultdict(int)
    Type = defaultdict(int)
    
    TotalWord = 0
    TotalLex = 0
    TriCount.clear()
    BiCount.clear()
    Count.clear()
    BiType.clear()
    Type.clear()


    fileObject = open(Filename,'rb')  
    TriCount = pickle.load(fileObject)
    for (X,Y,Z) in TriCount:
        BiType[(X,Y)] += 1
        BiCount[(X,Y)] += TriCount[(X,Y,Z)]
        Count[Y] += TriCount[(X,Y,Z)]

    for (X,Y) in BiCount:
        Type[X] += 1
        
    for X in Count:
        TotalLex += 1
        TotalWord += Count[X]
        
    return(1)
    

########## Preprocess Thai texts  #### adding SegSep and <s> for speocal 
def preprocess(input):
    global SegSep
    global SSegSep

    input = re.sub(r" +ๆ",r"ๆ",input)
    input = re.sub(r"ๆ([^ ])",r"ๆ"+SegSep+r"\1",input)  ## add space after ๆ
#    print('adjust',input,'xxx')

#    input = re.sub(u"เเ",u"แ",input)
####### codes suggested by Arthit Suriyawongkul #####
    NORMALIZE_DICT = [
        ('\u0E40\u0E40', '\u0E41'), # Sara E + Sara E -> Sara AE
        ('\u0E4D\u0E32', '\u0E33'), # Nikhahit + Sara AA -> Sara AM
        ('\u0E24\u0E32', '\u0E24\u0E45'), # Ru + Sara AA -> Ru + Lakkhangyao
        ('\u0E26\u0E32', '\u0E26\u0E45'), # Lu + Sara AA -> Lu + Lakkhangyao
    ]
    for k, v in NORMALIZE_DICT:
        input = input.replace(k, v)
########################################################        
#    print input.encode('raw_unicode_escape')

  ###  handle Thai writing one character one space by deleting each space
#    pattern = re.compile(r'([ก-ฮเแาำะไใโฯๆ][\ุ\ู\ึ\ั\ี\๊\้\็\่\๋\ิ\ื\์]*) +([ก-ฮเแาำะไใโฯๆ\ุ\ู\ึ\ั\ี\๊\้\็\่\๋\ิ\ื\์]{,2}) +|([ก-ฮเแาำะไใโฯๆ][\ุ\ู\ึ\ั\ี\๊\้\็\่\๋\ิ\ื\์]*) +([ก-ฮเแาำะไใโฯๆ\ุ\ู\ึ\ั\ี\๊\้\็\่\๋\ิ\ื\์]{,2})$')
    pattern = re.compile(r'([ก-ฮเแาำะไใโฯๆ][\ุ\ู\ึ\ั\ี\๊\้\็\่\๋\ิ\ื\์]*) +([ก-ฮเแาำะไใโฯๆ][\ุ\ู\ึ\ั\ี\๊\้\็\่\๋\ิ\ื\์]*) +|([ก-ฮเแาำะไใโฯๆ][\ุ\ู\ึ\ั\ี\๊\้\็\่\๋\ิ\ื\์]*) +([ก-ฮเแาำะไใโฯๆ][\ุ\ู\ึ\ั\ี\๊\้\็\่\๋\ิ\ื\์]*)$')
#    while re.search(pattern, input):
#       input = re.sub(pattern, r"\1\2", input,count=1)
    input = re.sub(pattern, r"\1\2", input)

  ##### change space\tab between [ET][ET] and [ET]  to be SegSep
#    input = re.sub(r"([^\s\t\u00A0][\ุ\ู\ึ\ั\ี\๊\้\็\่\๋\ิ\ื\์]*[^\s\t\u00A0][\ุ\ู\ึ\ั\ี\๊\้\็\่\๋\ิ\ื\์]*)[\s\t\u00A0]+([^\s\t\u00A0])",r"\1"+SegSep+r"\2",input)
    input = re.sub(r"([^\s\t\u00A0]{3,})[\s\t\u00A0]+([^\s\t\u00A0]+?)",r"\1"+SegSep+r"\2",input)
#    print('1. ',input)
    
   ##### change space\tab between [ET] and [ET][ET]  to be SegSep
#    input = re.sub(r"([^\s\t\u00A0][\ุ\ู\ึ\ั\ี\๊\้\็\่\๋\ิ\ื\์]*)[\s\t\u00A0]+([^\s\t\u00A0][\ุ\ู\ึ\ั\ี\๊\้\็\่\๋\ิ\ื\์]*[^\s\t\u00A0][\ุ\ู\ึ\ั\ี\๊\้\็\่\๋\ิ\ื\์]*)",r"\1"+SegSep+r"\2",input)
    input = re.sub(r"([^\s\t\u00A0]+)[\s\t\u00A0]+([0-9]+)",r"\1"+SegSep+r"\2",input)
    input = re.sub(r"([^\s\t\u00A0]+?)[\s\t\u00A0]+([^\s\t\u00A0]{3,})",r"\1"+SegSep+r"\2",input)



        ### handle English and Thai mixed without a space inside $s by adding SSegSep (softSegSep)
    input = re.sub(r"([ก-์][ฯๆ])",r"\1"+SSegSep,input)
    input = re.sub(r"([\u0E01-\u0E5B]+\.?)([^\.\u0E01-\u0E5B\u001F]+)",r"\1"+SSegSep+r"\2",input)
    input = re.sub(r"([^\.\u0E01-\u0E5B\u001F]+)([\u0E01-\u0E5B]+)",r"\1"+SSegSep+r"\2",input)
    input = re.sub(r"(<.+?>)",SSegSep+r"\1",input)
    input = re.sub(r"([0-9a-zA-Z\.\-]{2,})([\u0E01-\u0E5B]+)",r"\1"+SSegSep+r"\2",input)
    input = re.sub(r"(\.\.\.+)",r""+SSegSep+r"\1"+SSegSep,input)    #  ....  add SSegSep after that
#    print("3. ",input)

    return(input)



#############################################################################################################
### initialization by read syllable patterns, syllable trigrams, and satndard dictionary
def initial():
    global SylSep
    global WordSep
    global SegSep
    global SSegSep
    global TDICT
    global PRON
    global CProb
    global SYLVAR

    PRON = defaultdict(list)
    SYLVAR = defaultdict(list)
#    PRON = {}    
    TDICT = {}
    CProb = defaultdict(float)
    
    SylSep = chr(126)    ## ~
    WordSep = chr(124)   ## |
    SSegSep = chr(30)
    SegSep = chr(31)

    path = os.path.abspath(__file__)
    ATA_PATH = os.path.dirname(path)
    
#    try:
#        ATA_PATH = pkg_resources.resource_filename('tltk', '/')
    
    read_sylpattern(ATA_PATH + '/sylrule.lts')
    read_syldict(ATA_PATH +  '/thaisyl.dict')
    read_stat(ATA_PATH + '/sylseg.3g')
    read_thdict(ATA_PATH +  '/thdict')
    read_sylvar(ATA_PATH + '/sylform_var.pklz')

    read_PhSTrigram(ATA_PATH +  '/PhSTrigram.sts')
#    read_wordtier(ATA_PATH +  '/wrdtier')
    read_wordtier(ATA_PATH +  '/word.pklz')

    return(1)


############ END OF GENERAL MODULES 
initial()


##########################################################################
## testing area


'''

x = 'หมัก'
print(g2p(x))
#print(syl_segment(x))

file = "/Users/awirote/Dropbox/Corpus/TTC/thtxt1.txt"
Maltparser_Path = "/Users/awirote/Dropbox/prog/maltparser-1.9.2"

with open(file,encoding="utf8") as f:
    contents = f.read()
#print(txt2feat(contents,Option="name"))
x = TextClass(contents, Classifier='all')
print(x)


Maltparser_Path = "/Users/awirote/Dropbox/prog/maltparser-1.9.2"

#dt = MaltParser("เมื่อเวลา 15.40 น. วันที่ 18 เมษายน 2566 ที่ สน.ลุมพินี เจ้าหน้าที่ตำรวจ สน.ลุมพินี ได้เบิกตัว นายธนายุทธ พลนาคู หรือ โจ นายณัฐพงษ์ ฆ้องคำ หรือ จูน นายศุภพล ฮาลมัน หรือ กาย หรือ บอส และ น.ส.สริตา ดอนม่วง หรือ ตา เพื่อนำตัวไปสอบปากคำที่ห้องพนักงานสอบสวน ชั้น 2 โดยมีทนายความ ซึ่งผู้ต้องหาทั้งหมดได้ร้องขอไว้ ทั้งนี้การสอบปากคำผู้ต้องหาทั้ง 4 คน เป็นการแยกสอบรายบุคคล ระหว่างที่เบิกตัวเข้าห้องพนักงานสอบสวน สื่อมวลชนพยายามสอบถามนายศุภพล ถึงเหตุการณ์ที่เกิดขึ้น แต่นายกายไม่ได้โต้ตอบแต่อย่างใด โดยมีสีหน้านิ่งเฉย ก่อนเดินเข้าห้องพนักงานสอบสวนไป")
#print_dtree(dt)
#print('===============')
lst = ['ที่', 'ดัก', 'ไขมัน', '<s/>', 'เป็น', 'อุปกรณ์', 'ที่', 'ใช้', 'ใน', 'การ', 'แยก', 'ไขมัน', 'ออก', 'จาก', 'น้ำเสีย', '<s/>', 'ก่อน', 'ที่', 'จะ', 'ระบาย', 'ต่อไป', 'ยัง', 'ที่', 'ที่', 'เหมาะสม', '<s/>', 'ท่อน้ำ', 'เสีย', 'จาก', 'อ่างล้างชาม', '<s/>', 'และ', 'ครัว', 'ของ', 'ภัตตาคาร', '<s/>', 'และ', 'โรงแรม', '<s/>', 'จะ', 'ต้อง', 'แยก', 'ออก', 'จาก', 'ท่อน้ำ', 'เสีย', 'อื่นๆ', '<s/>', 'เพื่อ', 'ทำ', 'การ', 'แยก', 'ไขมัน', 'ออก', 'เสียก่อน', '<s/>', 'โดยปกติ', 'แล้ว', 'ท่อน้ำ', 'เสีย', 'จาก', 'ครัว', 'ตาม', 'บ้าน', 'มี', 'ปริมาณ', 'น้ำเสีย', 'และ', 'ไขมัน', 'ไม่', 'มาก', 'นัก', 'ซึ่ง', 'ไม่', 'จำเป็น', 'ที่', 'จะ', 'ต้อง', 'ใช้', 'ที่', 'ดัก', 'ไขมัน', 'เพื่อ', 'แยก', 'ไขมัน', 'ออก', 'ก่อน', 'การ', 'ระบาย', 'น้ำทิ้ง', '<s/>', 'ที่', 'ดัก', 'ไขมัน', 'อาจ', 'จะ', 'ทำ', 'ด้วย', 'เหล็กหล่อ', 'หรือ', 'คอนกรีต', 'ก็ได้', '<s/>', 'ใน', 'กรณี', 'ที่', 'ใช้', 'เหล็กหล่อ', 'จะ', 'ต้อง', 'มี', 'การ', 'ป้องกัน', 'ผิว', 'โลหะ', 'มิให้', 'ผุกร่อน', 'เร็ว', '<s/>', 'เช่น', '<s/>', 'เคลือบผิว', 'ลงยา', '<s/>', 'หรือ', 'ทาสี', 'กันสนิม', 'เป็นต้น', '<s/>', 'รูป', 'ที่', '<s/>', '4.36', '<s/>', 'แสดงถึง', 'ที่', 'ดัก', 'ไขมัน', '<s/>', 'ซึ่ง', 'ทำ', 'ด้วย', 'คอนกรีต', '<s/>', 'ที่', 'ดัก', 'ไขมัน', 'ชนิด', 'นี้', 'เหมาะ', 'สำหรับ', 'ตั้ง', 'อยู่', 'นอก', 'อาคาร', 'และ', 'ใช้', 'ดัก', 'ไขมัน', 'ปริมาณ', 'มาก']
dt = MaltParser_wordlist(lst)

#'<s/>', 'ที่', '<s/>', 'สน.', 'ลุมพิ', 'นี', '<s/>', 'เจ้าหน้าที่ตำรวจ', '<s/>', 'สน.', 'ลุมพิ', 'นี', '<s/>', 'ได้', 'เบิกตัว', '<s/>', 'นาย', 'ธนา', 'ยุทธ', '<s/>', 'พล', 'นา', 'คู', '<s/>', 'หรือ', '<s/>', 'โจ', '<s/>', 'นาย', 'ณัฐพงษ์', '<s/>', 'ฆ้อง', 'คำ', '<s/>', 'หรือ', '<s/>', 'จูน', '<s/>', 'นาย', 'ศุภ', 'พล', '<s/>', 'ฮา', 'ลมัน', '<s/>', 'หรือ', '<s/>', 'กาย', '<s/>', 'หรือ', '<s/>', 'บอส', '<s/>', 'และ', '<s/>', 'น.ส.', 'สริ', 'ตา'
print_dtree(dt)

#sys.exit()


file = "/Users/awirote/Dropbox/Corpus/TTC/test/44.MP.00.13.N.wsg-re.txt"
Maltparser_Path = "/Users/awirote/Dropbox/prog/maltparser-1.9.2"

with open(file,encoding="cp874") as f:
    contents = f.read()
    contents = contents.replace("<NE>","")
    contents = contents.replace("</NE>","")
    contents = contents.replace("\n","")
    contents = contents.replace("<w>","")
print(TextClass(contents,TextOption="segmented"))


lst = ["แสงดี","แช่งมั่ง","นายก","คั่นกู","คั่นกลาง","พรรคแอบเลื่อน","พรรคว่าเราะ","พรรคหลงหลัว","พรรคไม่หลัว","พรรคหน้าลุง","พรรคร่าย","พรรคมาหาลา","พรรครบ","พรรคที่จะล้อม","พรรคที่จะล้อม","พรรคไม่ล่อ","พรรคใจย่อ","เชี่ยเธอนะนอบ","เจออยู่ที่ไทย","ล้าเธอนัก","เรอแต่ทัก","เบลอว่าชอบแถบ","เจออยู่ที่ไทย","เมาเป็นแฟนรา","ไหล่โดนจอ","เจอละไม","ฟันแกน","ชู้แต่เธอไม่รอบ","แขนเป็นฟอ","ไข้ที่ชล","ตากแดด","ดิสกว่าที่คีย์"]
for x in lst:
    print(x,'>',spoonerism(x))


print(spoonerism("เรอแต่ทัก"))


txt = '"|ฉัน|จำ|ได้|นะ|ว่า|ตอน|เธอ|จัด|งานเลี้ยง|ครั้งก่อน|ดึก|กว่า|นี้|อีก|"|นี|ซบ|อก|ด้วย|น้ำเสียง|ห้วน|แกม|รำคาญ|<s/>|ก่อน|จัด|งานเลี้ยง|ครั้งนี้|เธอ|ขอ|อนุญาต|<s/>|sub warden*|ประจำ|ตึก|แล้ว|<s/>|อีกทั้ง|ได้|บอก|เพื่อนบ้าน|ที่|เหลือ|รวมทั้ง|ยัย|ชิ|เอะอะ|นี่|ด้วย|'
lst = txt.split("|")
txt1 = ''.join(lst)
Maltparser_Path = "/Users/awirote/Dropbox/prog/maltparser-1.9.2"
dt = MaltParser(txt1)
print_dtree(dt)
sys.exit()


#text1 = 'เมื่อเวลา 15.40 น. วันที่ 18 เมษายน 2566 ที่ สน.ลุมพินี เจ้าหน้าที่ตำรวจ สน.ลุมพินี ได้เบิกตัว นายธนายุทธ พลนาคู หรือ โจ นายณัฐพงษ์ ฆ้องคำ หรือ จูน นายศุภพล ฮาลมัน หรือ กาย หรือ บอส และ น.ส.สริตา ดอนม่วง หรือ ตา เพื่อนำตัวไปสอบปากคำที่ห้องพนักงานสอบสวน ชั้น 2 โดยมีทนายความ ซึ่งผู้ต้องหาทั้งหมดได้ร้องขอไว้ ทั้งนี้การสอบปากคำผู้ต้องหาทั้ง 4 คน เป็นการแยกสอบรายบุคคล ระหว่างที่เบิกตัวเข้าห้องพนักงานสอบสวน สื่อมวลชนพยายามสอบถามนายศุภพล ถึงเหตุการณ์ที่เกิดขึ้น แต่นายกายไม่ได้โต้ตอบแต่อย่างใด โดยมีสีหน้านิ่งเฉย ก่อนเดินเข้าห้องพนักงานสอบสวนไป'


text1 = 'เมื่อเวลา 15.40 น. วันที่ 18 เมษายน 2566 ที่ สน.ลุมพินี เจ้าหน้าที่ตำรวจ สน.ลุมพินี ได้เบิกตัว นายธนายุทธ พลนาคู หรือ โจ นายณัฐพงษ์ ฆ้องคำ หรือ จูน นายศุภพล ฮาลมัน\n หรือ กาย หรือ บอส และ น.ส.สริตา ดอนม่วง หรือ ตา เพื่อนำตัวไปสอบปากคำที่ห้องพนักงานสอบสวน ชั้น 2'

res = TextAna(text1,UDParse="Malt")
print(json.dumps(res, indent=4, ensure_ascii=False))
sys.exit()


Maltparser_Path = "/Users/awirote/Dropbox/prog/maltparser-1.9.2"
dt = MaltParser("เขานั่งดูหนังอยู่ที่บ้าน")
print_dtree(dt)


dt = MaltParser("แล้วอย่ามาหาว่าไม่บอกอะไร")
print_dtree(dt)




Maltparser_Path = "/Users/awirote/Dropbox/prog/maltparser-1.9.2"
text1 = 'สำนักงานสลากศาสตร์เขตจตุจักรชี้แจงว่า เขาไม่นำป้ายประกาศเตือนปลิงไปปักตามแหล่งน้ำ ในเขตอำเภอเมือง จังหวัดอ่างทอง หลังจากนายสุกิจ อายุ 65 ปี ถูกปลิงกัดแล้วไม่ได้ไปพบแพทย์\nนายกรัฐมนตรีจังหวัดสกลนคร กล่าวกับคนขับรถประจำทางหลวงสายสองว่า อยากวิงวอนให้ใช้ความรอบคอบอย่าหลงเชื่อคำชักจูงหรือปลุกระดมของพวกหัวรุนแรงจากทางการไฟฟ้า\nนายกรัฐมนตรีจังหวัดสกลนคร กล่าวกับคนขับรถประจำทางหลวงสายสองว่า อยากวิงวอนให้ใช้ความรอบคอบอย่าหลงเชื่อคำชักจูงหรือปลุกระดมของพวกหัวรุนแรงจากทางการไฟฟ้า'
res = TextAna(text1,TextOption="edu",UDParse="Malt")
print(res)






Maltparser_Path = "/Users/awirote/Dropbox/prog/maltparser-1.9.2"

dt = MaltParser("เขานั่งดูหนังอยู่ที่บ้าน")
print_dtree(dt)

text1 = 'ท่าน|ไม่|สนใจ|เรื่อง|เกียรติประวัติ|ของ|ท่าน|<s/>|แต่|ก็|น่า|แปลก|ที่|สิ่ง|ซึ่ง|ท่าน|ไม่|สนใจ|นั้น|<s/>|กลับ|ติด|อยู่|กับ|ทุก|ริมฝีปาก'
Maltparser_Path = "/Users/awirote/Dropbox/prog/maltparser-1.9.2"
txt = 'นายกรัฐมนตรีกล่าวกับคนขับรถประจำทางหลวงสายสองว่า อยากวิงวอนให้ใช้ความรอบคอบอย่าหลงเชื่อคำชักจูงหรือปลุกระดมของพวกหัวรุนแรงจากทางการไฟฟ้า'

dt = MaltParser(txt)
print_dtree(dt)

dt = MaltParser_wordlist(text1.split('|'))
print_dtree(dt)
print(tree_max_depth(dt))

x = 'มหากษัตริย์'
w = WordAna(x)
print(vars(w))
for s in w.syl_prop:
    print(vars(s))





text1 = '<p>|เชิง|ผา|หิมพานต์|<p>|ควบ|จินต|นิยาย|อิง|หลัก|ธรรม|ทาง|พระพุทธศาสนา|<p>|	|สิ่ง|นั้น|เป็น|เพียง|ซาก|เจดีย์|ร้าง|<s>ไม่|มี|คำพูด|ไม่|มี|ตัวอักษร|ที่|จะ|ป่าวประกาศ|แก่|ใครๆ|ว่า|<s>เจดีย์|นี้|มี|กำเนิด|เมื่อ|กี่|พัน|ปี|มา|แล้ว|<s>สร้าง|ขึ้น|เพื่อ|เป็น|อนุสรณ์|ถึง|ใคร|<s>|และ|ใคร|ผู้นั้น|มี|คุณงาม|ความ|ดี|อย่างไร|<s>สิ่ง|นั้น|เป็น|เพียง|กอง|อิฐ|หัก|พัง|<s>ใคร|ผ่าน|ไป|มา|จะ|สนใจ|ไยดี|หรือ|ไม่|ก็ช่าง|ใคร|<s>แม้|ใคร|จะ|เข้า|ไป|กราบ|แสดง|คารวะ|อย่าง|สูง|<s>หรือ|ใคร|จะ|เบือน|หน้า|หนี|<s>|ก็|เป็น|เรื่อง|ของ|ผู้นั้น|<s>ไม่|มี|อาการ|ยินดี|ยินร้าย|ปรากฏ|ออก|มา|จาก|กอง|อิฐ|<s>แต่|ชาย|ชรา|คน|หนึ่ง|<s>กล่าว|ด้วย|น้ำตา|หนอง|หน้า|<s>ท่ามกลาง|ลุ่ม|ชน|ที่|พา|กัน|ไป|แห่|ห้อง|พระ|เจดีย์|ร้าง|นั้น|<s>ว่า|นี่แหละ|คือ|สิ่ง|อนุสรณ์|ถึง|ท่าน|ผู้|หนึ่ง|<s>ผู้|ชอบ|เดิน|ตาม|หลัง|<s>|ผู้|ไม่|รู้จัก|เหน็ดเหนื่อย|ใน|การ|รับใช้|<s>|เพื่อ|ประโยชน์|แห่ง|ผู้|ที่|ท่าน|จงรัก|อัน|มี|ผล|สะท้อน|มา|ถึง|ประโยชน์|ของ|มหาชน|<s>|ท่าน|คิดถึง|ประโยชน์|ส่วนตัว|ภายหลัง|ประโยชน์|ส่วนรวม|<s>|ทำ|ตน|เป็น|คน|เล็กน้อย|<s>ไม่|ชอบ|แสดง|ตน|เป็น|คน|เด่น|<s>|แต่|เมื่อ|ถึงคราว|คับขัน|ถึงคราว|ที่|จะ|ต้อง|สละ|ชีวิต|<s>ท่าน|จะ|ออก|น้ำหน้า|แม้|ผู้|ที่|ท่าน|เคย|ตาม|หลัง|<s>|พร้อม|ที่|จะ|ต่อสู้|กับ|ความ|ตาย|อัน|กำลัง|มา|ถึง|เฉพาะหน้า|<s>|ท่าน|เป็น|ยอด|ของ|ผู้|จงรักภักดี|ต่อ|ผู้|มี|พระคุณ|<s>|เป็น|ยอด|ของ|ผู้|รู้จัก|กาลเทศะ|<s>เป็น|ยอด|ของ|ผู้|มี|ความ|ทรงจำ|ดี|เลิศ|<s>และ|ใน|การ|ปฏิบัติงาน|อัน|น่า|สรรเสริญ|นั้น|<s>|แม้|บาง|ครั้ง|จะ|ถูก|ตำหนิ|ก็|ยอมรับ|ผิด|โดย|ไม่|เสีย|เวลา|นำ|ทิฐิ|มานะ|มา|ต่อสู้|<s>ท่าน|ผู้นั้น|คือ|ใคร|เล่า|<s>|ถ้า|มิใช่|<s>|บุคคล|ตัวอย่าง|<s>ผู้|มิได้|ฝาก|เกียรติประวัติ|ไว้|แก่|เจดีย์|หรือ|กอง|อิฐ|<s>มิได้|ฝาก|ไว้|แก่|อดีตกาล|นาน|ไกล|<s>ท่าน|ไม่|สนใจ|เรื่อง|เกียรติประวัติ|ของ|ท่าน|<s>แต่|ก็|น่า|แปลก|ที่|สิ่ง|ซึ่ง|ท่าน|ไม่|สนใจ|นั้น|<s>กลับ|ติด|อยู่|กับ|ทุก|ริมฝีปาก|ซึ่ง|ถ่ายทอด|ถ้อยคำ|อัน|ประเสริฐ|ที่|ท่าน|อุตส่าห์|จดจำ|ไว้|<s>|และ|กับ|ทุก|หัวใจ|ที่|ไตร่ตรอง|ข้อความ|<s>ซึ่ง|ท่าน|รับ|มา|แล้ว|<s>ก็|บอกกล่าว|ถ่อย|ทอด|สืบ|ต่อ|เป็น|ชั้นๆ|<s>|มา|จวน|จบ|ปัจจุบัน|<s>|จินต|นิยาย|อิง|หลัก|ธรรม|ทาง|พระพุทธศาสนา|เรื่อง|นี้|อาจ|จืดชืด|ไม่|มี|รสชาติ|<s>อาจ|ขาด|ความ|สมบูรณ์|ด้าน|นั้น|และ|ด้าน|นี้|<s>|อาจ|ขาด|ความ|กระปรี้กระเปร่า|ที่|จะ|ชักจูง|ใจ|ให้|ฮึกฮัก|<s>|อาจ|ขาด|ความ|สดชื่น|รื่นเริง|<s>แต่|ถ้า|ความ|ดี|อัน|ใด|<s>|ซึ่ง|อาจ|มี|แฝง|อยู่|บ้าง|แม้|เพียง|นิดหนึ่ง|<s>จน|มอง|เกือบ|ไม่|เห็น|<s>ความ|ดี|นั้น|ย่อม|เป็น|ประหนึ่ง|เครื่อง|สักการะ|ของ|คน|ยาก|<s>|เป็น|ดอกไม้|ธูป|เทียน|ที่|ด้อย|ราคา|<s>แต่|ไม่|ด้อย|ใน|เรื่อง|ความ|ตั้งใจ|และ|เต็มใจ|ที่|ถวาย|เป็น|เครื่องบูชา|แด่|ท่าน|ผู้|น่า|เคารพ|รัก|<s>|ท่าน|ผู้|เป็น|บุคคล|ตัวอย่าง|<s>|ท่าน|ผู้|ที่|ซาก|หัก|พัง|พระ|เจดีย์|ใน|เรื่อง|นี้|มี|ความหมาย|ถึง|<s>ท่าน|ผู้|ที่|กาลเวลา|ไม่|เคย|ทำให้|เกียรติคุณ|ของ|ท่าน|ลบเลือน|ไป|เลย|<p>|๑|.|สำนัก|วิศวามิตร|'

res = TextAna(text1,"segmented","segmented")
print(json.dumps(res, indent=4, ensure_ascii=False))



print(g2p('อรรถศาสตร์'))
xx = g2p("อรรถศาสตร์อรรถพลปรนเปรอสถาบันอุดมศึกษาเสาร์นี้ไม่สามารถก้าวให้ทันการเปลี่ยนแปลงวันจันทร์ของตลาดแรงงาน")
print(xx)


f = open('/Users/awirote/Dropbox/prog/python/TLTK/tltk/sent_segment.pick','rb')
model = pickle.load(f)
## save to a new version
filename = '/Users/awirote/Dropbox/prog/python/TLTK/tltk/sent_segment_new.pick'
pickle.dump(model, open(filename, 'wb')) 

f = open('/Users/awirote/Dropbox/prog/python/TLTK/tltk/sent_segment_new.pick','rb')
model = pickle.load(f)

f = bz2.BZ2File('/Users/awirote/Dropbox/prog/python/TLTK/tltk/sent_segmentx.pklz','wb')
pickle.dump(model,f)
f.close()
print("Write gzip pickle")
f = bz2.BZ2File('/Users/awirote/Dropbox/prog/python/TLTK/tltk/sent_segmentx.pklz','rb')
modelx = pickle.load(f)
f.close()
print("write load success")


res = TextAna2json(text1,'xxx.json',TextOption="segmented",Mode="append")


print(TNC_tag('ความอยากที่เกิดจากการศึกษา',POS='N'))

text1 = '<p>|เชิง|ผา|หิมพานต์|<p>|ควบ|จินต|นิยาย|อิง|หลัก|ธรรม|ทาง|พระพุทธศาสนา|<p>|	|สิ่ง|นั้น|เป็น|เพียง|ซาก|เจดีย์|ร้าง|<s>ไม่|มี|คำพูด|ไม่|มี|ตัวอักษร|ที่|จะ|ป่าวประกาศ|แก่|ใครๆ|ว่า|<s>เจดีย์|นี้|มี|กำเนิด|เมื่อ|กี่|พัน|ปี|มา|แล้ว|<s>สร้าง|ขึ้น|เพื่อ|เป็น|อนุสรณ์|ถึง|ใคร|<s>|และ|ใคร|ผู้นั้น|มี|คุณงาม|ความ|ดี|อย่างไร|<s>สิ่ง|นั้น|เป็น|เพียง|กอง|อิฐ|หัก|พัง|<s>ใคร|ผ่าน|ไป|มา|จะ|สนใจ|ไยดี|หรือ|ไม่|ก็ช่าง|ใคร|<s>แม้|ใคร|จะ|เข้า|ไป|กราบ|แสดง|คารวะ|อย่าง|สูง|<s>หรือ|ใคร|จะ|เบือน|หน้า|หนี|<s>|ก็|เป็น|เรื่อง|ของ|ผู้นั้น|<s>ไม่|มี|อาการ|ยินดี|ยินร้าย|ปรากฏ|ออก|มา|จาก|กอง|อิฐ|<s>แต่|ชาย|ชรา|คน|หนึ่ง|<s>กล่าว|ด้วย|น้ำตา|หนอง|หน้า|<s>ท่ามกลาง|ลุ่ม|ชน|ที่|พา|กัน|ไป|แห่|ห้อง|พระ|เจดีย์|ร้าง|นั้น|<s>ว่า|นี่แหละ|คือ|สิ่ง|อนุสรณ์|ถึง|ท่าน|ผู้|หนึ่ง|<s>ผู้|ชอบ|เดิน|ตาม|หลัง|<s>|ผู้|ไม่|รู้จัก|เหน็ดเหนื่อย|ใน|การ|รับใช้|<s>|เพื่อ|ประโยชน์|แห่ง|ผู้|ที่|ท่าน|จงรัก|อัน|มี|ผล|สะท้อน|มา|ถึง|ประโยชน์|ของ|มหาชน|<s>|ท่าน|คิดถึง|ประโยชน์|ส่วนตัว|ภายหลัง|ประโยชน์|ส่วนรวม|<s>|ทำ|ตน|เป็น|คน|เล็กน้อย|<s>ไม่|ชอบ|แสดง|ตน|เป็น|คน|เด่น|<s>|แต่|เมื่อ|ถึงคราว|คับขัน|ถึงคราว|ที่|จะ|ต้อง|สละ|ชีวิต|<s>ท่าน|จะ|ออก|น้ำหน้า|แม้|ผู้|ที่|ท่าน|เคย|ตาม|หลัง|<s>|พร้อม|ที่|จะ|ต่อสู้|กับ|ความ|ตาย|อัน|กำลัง|มา|ถึง|เฉพาะหน้า|<s>|ท่าน|เป็น|ยอด|ของ|ผู้|จงรักภักดี|ต่อ|ผู้|มี|พระคุณ|<s>|เป็น|ยอด|ของ|ผู้|รู้จัก|กาลเทศะ|<s>เป็น|ยอด|ของ|ผู้|มี|ความ|ทรงจำ|ดี|เลิศ|<s>และ|ใน|การ|ปฏิบัติงาน|อัน|น่า|สรรเสริญ|นั้น|<s>|แม้|บาง|ครั้ง|จะ|ถูก|ตำหนิ|ก็|ยอมรับ|ผิด|โดย|ไม่|เสีย|เวลา|นำ|ทิฐิ|มานะ|มา|ต่อสู้|<s>ท่าน|ผู้นั้น|คือ|ใคร|เล่า|<s>|ถ้า|มิใช่|<s>|บุคคล|ตัวอย่าง|<s>ผู้|มิได้|ฝาก|เกียรติประวัติ|ไว้|แก่|เจดีย์|หรือ|กอง|อิฐ|<s>มิได้|ฝาก|ไว้|แก่|อดีตกาล|นาน|ไกล|<s>ท่าน|ไม่|สนใจ|เรื่อง|เกียรติประวัติ|ของ|ท่าน|<s>แต่|ก็|น่า|แปลก|ที่|สิ่ง|ซึ่ง|ท่าน|ไม่|สนใจ|นั้น|<s>กลับ|ติด|อยู่|กับ|ทุก|ริมฝีปาก|ซึ่ง|ถ่ายทอด|ถ้อยคำ|อัน|ประเสริฐ|ที่|ท่าน|อุตส่าห์|จดจำ|ไว้|<s>|และ|กับ|ทุก|หัวใจ|ที่|ไตร่ตรอง|ข้อความ|<s>ซึ่ง|ท่าน|รับ|มา|แล้ว|<s>ก็|บอกกล่าว|ถ่อย|ทอด|สืบ|ต่อ|เป็น|ชั้นๆ|<s>|มา|จวน|จบ|ปัจจุบัน|<s>|จินต|นิยาย|อิง|หลัก|ธรรม|ทาง|พระพุทธศาสนา|เรื่อง|นี้|อาจ|จืดชืด|ไม่|มี|รสชาติ|<s>อาจ|ขาด|ความ|สมบูรณ์|ด้าน|นั้น|และ|ด้าน|นี้|<s>|อาจ|ขาด|ความ|กระปรี้กระเปร่า|ที่|จะ|ชักจูง|ใจ|ให้|ฮึกฮัก|<s>|อาจ|ขาด|ความ|สดชื่น|รื่นเริง|<s>แต่|ถ้า|ความ|ดี|อัน|ใด|<s>|ซึ่ง|อาจ|มี|แฝง|อยู่|บ้าง|แม้|เพียง|นิดหนึ่ง|<s>จน|มอง|เกือบ|ไม่|เห็น|<s>ความ|ดี|นั้น|ย่อม|เป็น|ประหนึ่ง|เครื่อง|สักการะ|ของ|คน|ยาก|<s>|เป็น|ดอกไม้|ธูป|เทียน|ที่|ด้อย|ราคา|<s>แต่|ไม่|ด้อย|ใน|เรื่อง|ความ|ตั้งใจ|และ|เต็มใจ|ที่|ถวาย|เป็น|เครื่องบูชา|แด่|ท่าน|ผู้|น่า|เคารพ|รัก|<s>|ท่าน|ผู้|เป็น|บุคคล|ตัวอย่าง|<s>|ท่าน|ผู้|ที่|ซาก|หัก|พัง|พระ|เจดีย์|ใน|เรื่อง|นี้|มี|ความหมาย|ถึง|<s>ท่าน|ผู้|ที่|กาลเวลา|ไม่|เคย|ทำให้|เกียรติคุณ|ของ|ท่าน|ลบเลือน|ไป|เลย|<p>|๑|.|สำนัก|วิศวามิตร|'

#res = TextAna(text1,"segmented","segmented")
res = TextAna(text1,TextOption="segmented")
print(res)
for w in res['wrd']:
    print(w, res['wrd'][w], res['wrd_arf'][w])




x = 'กราบบนกองทรายลี้หลี'
print(g2p_all(x))
print(th2read(x))
print(spell_variants(x))
    

f = open('/Users/macbook/Cloud/Dropbox/prog/python/TLTK/tltk/sent_segment.pick','rb')
model = pickle.load(f)
f = bz2.BZ2File('/Users/macbook/Cloud/Dropbox/prog/python/TLTK/tltk/sent_segmentx.pklz','wb')
pickle.dump(model,f)
f.close()
print("Write gzip pickle")
f = bz2.BZ2File('/Users/macbook/Cloud/Dropbox/prog/python/TLTK/tltk/sent_segmentx.pklz','rb')
modelx = pickle.load(f)
f.close()
print("write load success")


#import time

#start = time.time()
#tltk.corpus.TNC3g_load()
#tltk.corpus.TNC_load()
#end = time.time()
#print(end - start)

################# te
# sting area #######################################
#print(g2p('มาหรรษา'))
#print(len(SYLVAR))    
#print(spell_variants('โควิด',Karan='exclude'))
#cprint(g2p('ราคาค่าตัววันนี้ไอซ์แลนด์'))
#print(word_segment('คอยสังเกตดูอาการของตัวเองด้วยนะซาศโฏะจัง'))
#print(th2roman('เด็กอยากไปจุฬาเช้านี้ วันนี้ที่นี่เท่านั้น วันอื่นไม่ไป วันไหนก็ไม่ไป พรุ่งนี้ก็ไม่'))
#print(g2p('ใคร'))
#print(word_segment('ห ลั ก ก า ร เ รื่ อ ง นี้'))
#print(ner_tag("สำนักงานเขตจตุจักรชี้แจงว่า ได้นำป้ายประกาศเตือนปลิงไปปักตามแหล่งน้ำ ในเขตอำเภอเมือง จังหวัดอ่างทอง หลังจากนายสุกิจ อายุ 65 ปี ถูกปลิงกัดแล้วไม่ได้ไปพบแพทย์"))
#print(th2ipa('หลักความประพฤติ'))
#print(ner_tag('สำนักงานเขตจตุจักรชี้แจงว่า ได้นำป้ายประกาศเตือนปลิงไปปักตามแหล่งน้ำ ในเขตอำเภอเมือง จังหวัดอ่างทอง หลังจากนายสุกิจ อายุ 65 ปี ถูกปลิงกัดแล้วไม่ได้ไปพบแพทย์'))
#print(segment('ที่ทำให้ประชาชนชาวไทยเกิดความไม่สบายใจ'))
#print(word_segment_mm('นายกรัฐมนตรีกล่าวกับคนขับรถประจำทางหลวงสายสองว่า อยากวิงวอนให้ใช้ความรอบคอบอย่าหลงเชื่อคำชักจูงหรือปลุกระดมของพวกหัวรุนแรงจากทางการไฟฟ้า'))
#print(g2p('นายกรัฐมนตรีกล่าวกับคนขับรถประจำทางหลวงสายสองว่า อยากวิงวอนให้ใช้ความรอบคอบอย่าหลงเชื่อคำชักจูงหรือปลุกระดมของพวกหัวรุนแรงจากทางการไฟฟ้า'))

#print(word_segment('นายกรัฐมนตรีกล่าวกับคนขับรถประจำทางหลวงสายสองว่า อยากวิงวอนให้ใช้ความรอบคอบอย่าหลงเชื่อคำชักจูงหรือปลุกระดมของพวกหัวรุนแรงจากทางการไฟฟ้า'))

#print(word_segment('นายกรัฐมนตรีกล่าวกับสำนักข่าวซีซีบีและเอ็นบีดีวายว่า'))
#print(word_segment_mm('นายกรัฐมนตรีกล่าวกับผูสือข่าวว่า','prob'))
#print(word_segment_mm('นายกรัฐมนตรีกล่าวกับผู้สือข่าวว่า','prob'))
#start = time.time()
#print(word_segment('นายกรัฐมนตรีกล่าวกับคนขับรถประจำทางหลวงสายสองว่า อยากวิงวอนให้ใช้ความรอบคอบอย่าหลงเชื่อคำชักจูงหรือปลุกระดมของพวกหัวรุนแรงจากทางการไฟฟ้า'))
#end = time.time()
#print('colloc',end - start)


#start = time.time()
#print(word_segment('นายกรัฐมนตรีกล่าวกับคนขับรถประจำทางหลวงสายสองว่า อยากวิงวอนให้ใช้ความรอบคอบอย่าหลงเชื่อคำชักจูงหรือปลุกระดมของพวกหัวรุนแรงจากทางการไฟฟ้า','ngram'))
#end = time.time()
#print('ngram',end - start)

#start = time.time()
#print(word_segment('นายกรัฐมนตรีกล่าวกับคนขับรถประจำทางหลวงสายสองว่า อยากวิงวอนให้ใช้ความรอบคอบอย่าหลงเชื่อคำชักจูงหรือปลุกระดมของพวกหัวรุนแรงจากทางการไฟฟ้า','ngram',spellchk='yes'))
#end = time.time()
#print('ngram+spellchk',end - start)

#start = time.time()
#print(word_segment('นายกรัฐมนตรีกล่าวกับคนขับรถประจำทางหลวงสายสองว่า อยากวิงวอนให้ใช้ความรอบคอบอย่าหลงเชื่อคำชักจูงหรือปลุกระดมของพวกหัวรุนแรงจากทางการไฟฟ้า','mm'))
#end = time.time()
#print('colloc',end - start)

#print(word_segment('โปรแกรมสำหรับประมวลผลภาษาไทย'))
#print(word_segment('ผู้สือข่าวรายงานว่านายกรัฐนตรีไม่มาทำงานที่ทำเนียบรัฐบาล',method='ngram',spellchk='yes'))
#print(word_segment('ผู้สือข่าวรายงานว่านายกรัฐนตรีไม่มาทำงานที่ทำเนียบรัฐบาล',method='mm'))

#xx = syl_segment("ร้องโอดโอย")
#print(xx)
#xx = th2roman('ร้องโอยโดนเอาใจไปไหน')
#print(xx)
#xx = word_segment("สถาบันอุดมศึกษาเสาร์นี้ไม่สามารถก้าวให้ทันการเปลี่ยนแปลงวันจันทร์ของตลาดแรงงาน")
#print(xx)
#xx = th2roman('คือเขาเดินเลยลงไปรอในแม่น้ำสะอาดไปหามะปราง')
#print(xx)

#xx= word_segment_nbest('คนขับรถประจำทางหลวง',10)
#print(xx)

#print(syl_segment('นายกรัฐมนตรีกล่าวกับคนขับรถประจำทางหลวงสายสองว่า อยากวิงวอนให้ใช้ความรอบคอบอย่าหลงเชื่อคำชักจูงหรือปลุกระดมของพวกหัวรุนแรงจากทางการไฟฟ้า'))

#print(word_segment('นายกรัฐมนตรีกล่าวกับคนขับรถประจำทางหลวงสายสองว่า อยากวิงวอนให้ใช้ความรอบคอบอย่าหลงเชื่อคำชักจูงหรือปลุกระดมของพวกหัวรุนแรงจากทางการไฟฟ้า'))

'''