#!/usr/bin/env python

import nltk
from nltk.corpus import wordnet as wn
from itertools import groupby
from math import floor
from random import random
import gc
from collections import Counter
import json
from datetime import datetime

# blacklists are important
adj_blacklist = ['some','many','quite','very','one','last','first','several','write','next','along']

def has_hypernym(word, hyper):
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

def get_tagged_counts(text):
    """Return a Counter with the token/tag pairs."""
    # Putting this in a function helps gc
    sents = nltk.sent_tokenize(text)
    return sum([Counter(nltk.pos_tag(nltk.word_tokenize(sent))) for sent in sents],Counter())

def pick(ll):
    """Pick a random element from a list"""
    return ll[int(random() * len(ll))]

def parse_source(text, hypernyms):
    tagged = get_tagged_counts(text).keys()
    # Do some cleanup
    tagged = set(map(lambda x: (first(x).lower(), last(x)), tagged))
    tagged = filter(lambda x: not has_hypernym(first(x), 'number'), tagged)
    # Necessary if plaintext tables or other garbage are around
    tagged = filter(lambda x: (not '|' in first(x)) and (not '_' in first(x)), tagged)
    # Single quotes are often not separated properly by the tagger, so aggressively remove them here
    tagged = filter(lambda x: "'" != first(x)[0] and "'" != first(x)[-1], tagged)

    # Get the adjectives and nouns
    adjs = map(first, filter(lambda x: last(x) == 'JJ', tagged))
    adjs = [x for x in adjs if not x in adj_blacklist]
    nouns = map(first, filter(lambda x: last(x) == 'NN', tagged))

    # Get the category words
    data = {'adj': sorted(adjs)}

    # Hypernyms come in a special format
    # - newlines divide unrelated entries
    # - entries on the same line are combined with OR

    hyperstruct = [x.split(',') for x in hypernyms.split("\n")]

    for hp in hyperstruct: 
        if hp == '': continue
        name = first(hp)
        data[name] = []
        for hh in hp:
            find_hyper = lambda x: has_hypernym(x, hh)
            data[name] = sorted(list(set(data[name] + filter(find_hyper, nouns))))
    
    return data

#TODO take options, print help
import fileinput
source = ''
hypernyms = "location,structure\nevent\nitem,artifact,food\nperson"
for line in fileinput.input():
    source += line.strip() + ' '

print json.dumps(parse_source(source, hypernyms))
