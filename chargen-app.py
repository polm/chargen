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
import Tkinter as tk
from ScrolledText import ScrolledText
import tkFileDialog as tkf
import ttk
from threading import Thread

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

def get_tagged_counts(fname):
    """Return a Counter with the token/tag pairs."""
    # Putting this in a function helps gc
    ff = open(fname)
    doc = ff.read()
    ff.close()
    sents = nltk.sent_tokenize(doc)
    return sum([Counter(nltk.pos_tag(nltk.word_tokenize(sent))) for sent in sents],Counter())

def pick(ll):
    """Pick a random element from a list"""
    return ll[int(random() * len(ll))]

def parse_source(filename, hypernyms):
    tagged = get_tagged_counts(filename).keys()
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
    data = {'adj': adjs}

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
            data[name] = list(set(data[name] + filter(find_hyper, nouns)))
    
    return data

def parse_sources(filenames, hypernyms, progressbar):
    data = {}
    for ff in filenames:
        newdata = parse_source(ff, hypernyms)
        for key in newdata:
            if not key in data: data[key] = []
            data[key] = sorted(list(set(data[key] + newdata[key])))
    # Ask where to save this
    output = tkf.asksaveasfile(mode='w',initialfile='chargen-data.json')
    output.write(json.dumps(data,indent=4,sort_keys=True))
    output.close()
    progressbar.destroy()

def analysis_wrapper(textbox):
    """A wrapper to get the textbox content and start analysis."""
    def doit():
        filenames = tkf.askopenfilenames()
        progress = ttk.Progressbar(orient=tk.HORIZONTAL, mode='indeterminate')
        thread = Thread(target=parse_sources,args=(filenames,textbox.get(1.0,tk.END), progress))
        thread.start()
        progress.pack()
        progress.start()
    return doit

if __name__ == '__main__':
    root = tk.Tk()
    w = tk.Label(root, text="Character Generator")
    w.pack()
    ex = tk.Label(root, text="""
            If you don't have something specific in mind, just leave the box below alone and choose a text file to use as input. 

            This program analyses a text and pulls out all the nouns and adjectives. It can classify the nouns into categories using "hypernyms", which are more general words - "animal" is a hypernym for "dog", "person" is a hypernym for "chef". To find out what hypernyms you can use, check WordNet online:

            http://wordnetweb.princeton.edu/perl/webwn

            The output file is JSON by default. Use the file on the site below to generate things or to convert it to Abulafia or other formats:

            xxx
            """)
    t = ScrolledText(root, height=5)
    t.insert(1.0, "person\nevent\nlocation,structure\nartefact,food")
    t.pack()
    bb = tk.Button(root, text='Choose Files to Analyze', command=analysis_wrapper(t)).pack()
    root.mainloop()
