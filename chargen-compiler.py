#!/usr/bin/env python
# encoding: utf-8

import nltk
import re
from nltk.corpus import wordnet as wn
from itertools import groupby
from math import floor
from random import random
import gc
from collections import Counter
import json
from datetime import datetime
import os


#TODO this is terrible, take a command-line option
JAPANESE = True if 'CHARGEN_JAPANESE' in os.environ else False

def ishiragana(word):
    return re.search('^[ぁ-ゞ]$', word)

def remove_parens(words):
    """Remove parentheticals from a string."""
    # Useful for edict definitions
    return re.sub(r'\([^)]*\)', '', words)

def strip_all(words):
    return map(lambda x: x.strip(), words)

def edict_setup(lines):
    EDICT = {}
    for line in lines:
        parts = remove_parens(line).split('/')
        if '[' in parts[0]:
            kana = re.sub(r'\].*$', '', re.sub(r'^.*\[', '', parts[0]))
            keys = parts[0].split('[')[0].split(';')
        else:
            keys = parts[0].split(';')
        keys = strip_all(keys)
        vals = strip_all(parts[1:-2]) # last one is a code of some kind
        for key in keys:
            if not key in EDICT: EDICT[key] = []
            EDICT[key] += vals
    return EDICT

if JAPANESE:
    # simple edict format, one entry per line
    with open('jp/edict2') as ff:
        EDICT = edict_setup(ff.read().split("\n"))

    # These are nouns that take "no" and are functionally adjectives
    # This has most everything that works that way, though "na" is preferred when reasonable
    # example: 黄金のXX,架空のXX
    # The list was made using wwwjdic
    with open('jp/noadj.txt') as ff:
        NO_ADJ = ff.read().split("\n")
    #TODO: get list of suru verbs

def edict_trans(word):
    """Get edict translations of a word"""
    # very poor as a translator, but good enough for wordnet
    if word in EDICT:
        return list(set(EDICT[word]))
    return []

# blacklists are important
BLACKLISTS = {
        # Quantifiers and ordinals aren't interesting
        'JJ': ["not", "no", "don't", 'some','many','quite','very','one','last','first','several','write','next','along'],
        # Besides racist terms, Wordnet considers most color words to represent people
        # These are usually obscure enough to be uninteresting, like "blue" and "gray" for soldiers in the American Civil War
        # Some of these are just weird, boring, or rarely intended in the sense that means person
        'NN': ['man', 'woman', 'person','queer', 'faggot', 'oriental', 'gay', 'jew', 'gyp', 'gypsy', 
            'negro', 'nigger', 'chink', 'nip', 'jap', 'pickaninny', 'black', 'red', 'white', 
            'yellow', 'pink', 'blue', 'grey', 'gray', 'screw']
}

def has_hypernym_jp(word, hyper):
    # optimistic in that *any* translation could work
    translations = edict_trans(word)
    for trans in translations:
        if has_hypernym_en(trans, hyper):
            return True 
    return False

def has_hypernym(word, hyper):
    if JAPANESE:
        return has_hypernym_jp(word, hyper)
    else:
        return has_hypernym_en(word, hyper)

def has_hypernym_en(word, hyper):
    # Can't use lowest common hypernym function here because it's broken
    # A chef is a person, but their lowest common hypernym is organism (through person).
    # It's a bug and has been fixed but not yet released.
    hypers = wn.synsets(hyper)
    only_nouns = lambda x: x.pos == wn.NOUN
    syns = filter(only_nouns,wn.synsets(word))
    if not syns: return False
    syn = first(syns)
    while syn != first(syn.root_hypernyms()):
        syn = syn.hypernyms()
        if not syn: return False
        else: syn = first(syn)
        if syn in hypers:
            return True
    return False

# Functional helpers.
def first(ll): return ll[0]
def last(ll): return ll[-1]
def lower(ss): return ss.lower()

def pick(ll):
    """Pick a random element from a list"""
    return ll[int(random() * len(ll))]

def pos_tagger(document):
    """Given a document, return token/POS pairs."""
    if JAPANESE:
        return pos_tagger_jp(document)
    return pos_tagger_en(document)

def pos_tagger_jp(document):
    """Get POS for Japanese words."""
    # Assume the document is mecab output
    pairs = []
    for line in document.split("\n"):
        line = line.strip()
        if line == 'EOS' or line == '': continue 
        word, _, info = line.partition("\t")

        # Split the info into useful data
        info = info.split(',')
        base_pos = info[0] # 名詞, 動詞, 形容詞など
        if len(info) < 2: print line
        detail_pos = info[1] # 形容動詞語幹, 一般

        pos = None
        if base_pos == '名詞':
            if detail_pos == '一般':
                pos = 'NN' # normal nouns
                if word in NO_ADJ: # no-adjectives 黄金
                    pos = 'JJ'
                    word = word + 'の'
            if detail_pos == '形容動詞語幹': # na-adjectives 綺麗
                pos = 'JJ'
                word = word + 'な'
        if base_pos == '形容詞' and detail_pos == '自立': # i-adjectives 新しい
            # っぽい is an example of a different detail_pos - rare and undesirable
            pos = 'JJ'
            word = info[6] # Base form, so 新しい even if 新しくis in the text
        
        # reject nouns that are only hiragana; most are bad
        if pos == 'NN' and ishiragana(word):
            pos = None

        if pos:
            pairs += [ (word, pos) ]
    return pairs

def pos_tagger_en(document):
    """English POS tagger. Sacrifices accuracy for speed."""
    sentences = document.split('.')
    pairs = []
    for sentence in sentences:
        words = nltk.word_tokenize(sentence)
        pairs += nltk.pos_tag(words)
    return pairs

def get_tagged_counts(text):
    """Return a Counter with the token/tag pairs."""
    # Putting this in a function helps gc
    #sents = nltk.sent_tokenize(text)
    #XXX we can lose some accuracy and this is much, much faster
    if JAPANESE: tagged_pairs = pos_tagger_jp(text)
    else: tagged_pairs = pos_tagger_en(text)
    return Counter(tagged_pairs)

def cleanup_tagged(tagged):
    """Remove unnecessary and garbage words from the tagger output."""
    # First make everything lowercase
    tagged = set(map(lambda x: (first(x).lower(), last(x)), tagged))
    # We don't need any numbers
    tagged = filter(lambda x: not has_hypernym(first(x), 'number'), tagged)
    # Remove any plaintext tables
    tagged = filter(lambda x: (not '|' in first(x)) and (not '_' in first(x)), tagged)
    # Single quotes are often not separated properly by the tagger, so aggressively remove them here
    tagged = filter(lambda x: "'" != first(x)[0] and "'" != first(x)[-1], tagged)
    return tagged

def select_by_tag(words, tag):
    result = map(first, filter(lambda x: last(x) == tag, words))
    if BLACKLISTS[tag]:
        result = [r for r in result if not r in BLACKLISTS[tag]]
    return result

def parse_source(text, hypernyms):
    # TODO - change smart quotes to plain quotes
    tagged = get_tagged_counts(text).keys()

    tagged = cleanup_tagged(tagged)

    adjs = select_by_tag(tagged, 'JJ')
    nouns = select_by_tag(tagged, 'NN')

    data = {'adjectives': sorted(adjs)}

    for key, vals in hypernyms.items():
        data[key] = []
        for val in vals:
            find_hyper = lambda x: has_hypernym(x, val)
            data[key] = data[key] + filter(find_hyper, nouns)
        data[key] = sorted(list(set(data[key])))

    # Locations get stupid stuff if you allow body parts
    if 'locations' in data:
        for word in data['locations']:
            if has_hypernym(word, 'body part'):
                data['locations'].remove(word)
    
    return data

#TODO take options, print help
import fileinput
source = ''
hypernyms = {
    'locations': ['location', 'structure'],
    'events': ['event'],
    'items': ['item', 'artifact'],
    'food': ['food'],
    'people': ['person'],
    'trait': ['trait'],
    'abstraction': ['abstraction']
    }

for line in fileinput.input():
    if JAPANESE:
        source += line # need to keep newlines
    else:
        source += line.strip() + ' '

print(json.dumps(parse_source(source, hypernyms)))
