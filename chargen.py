#!/usr/bin/env python
"""Character generator.

Usage:
  chargen <file> [--count=N] [--adjectives=AN] [--nouns=NN] [--event]

Options:
  -c N --count N             How many characters to generate. [default: 100]
  -a AN --adjectives AN      How many adjectives to use. [default: 3]
  -n NN --nouns NN           How many person-nouns to use. [default: 1]
  -e --event                Generate events instead of characters. [default: False]
"""

from nltk.corpus import wordnet as wn
import nltk
from docopt import docopt
from itertools import groupby
from math import floor
from random import random

def has_hypernym(word, hyper):
    only_nouns = lambda x: x.pos == wn.NOUN
    syns = filter(only_nouns,wn.synsets(word))
    if not syns: return False
    syn = first(syns)
    while syn != first(syn.root_hypernyms()):
        syn = syn.hypernyms()
        if not syn: return False
        else: syn = first(syn)
        if syn in wn.synsets(hyper):
            return True
    return False

# Functional helpers.
def first(ll): return ll[0]
def last(ll): return ll[-1]
def lower(ss): return ss.lower()

def discard_common(ll, percent):
    """Discard first entries of a list based on percent parameters."""
    # Smash case (making a copy in the process)
    nl = map(lower,ll)
    nl.sort()
    # Get the counts of the sorted list
    nl= zip(set(nl),[len(list(group)) for key, group in groupby(nl)])
    nl.sort(key=last)
    # Throw out the first bits (presumably too common)
    return map(first, nl[int(floor(len(nl)*percent)):])

def pick(ll):
    """Pick a random element from a list"""
    return ll[int(floor(random() * len(ll)))]

if __name__ == '__main__':
    arguments = docopt(__doc__, version='Character Generator 0.1')
    print "Reading file..."
    doc = open(arguments['<file>']).read()
    print "Read file, tagging..."
    sents = nltk.sent_tokenize(doc)
    tagged = sum([nltk.pos_tag(nltk.word_tokenize(sent)) for sent in sents],[])
    print "Tagging finished"

    # Get the adjectives
    adjs = map(first, filter(lambda x: x[1] == 'JJ', tagged))
    adjs = discard_common(adjs, .1)

    nouns = map(first, filter(lambda x: x[1] == 'NN', tagged))

    if not arguments['--event']:
        # Get the nouns that describe people
        is_person = lambda x: has_hypernym(x,'person')
        nns = filter(is_person, nouns)
        nns = discard_common(nns, .2)

        for chars in range(0, int(arguments['--count'])):
            print (' '.join([pick(adjs) for x in range(0, int(arguments['--adjectives']))]) + 
                    ' ' + '-'.join([pick(nns) for x in range(0, int(arguments['--nouns']))]) )

    else:
        print "getting locs"
        # Get nouns that are locations
        is_place = lambda x: has_hypernym(x,'location') or has_hypernym(x,'structure')
        locs = filter(is_place, nouns)
        locs = discard_common(locs,.1)

        # Get events
        is_event = lambda x: has_hypernym(x,'event')
        events = filter(is_event, nouns)
        events = discard_common(events,.1)
        
        for chars in range(0, int(arguments['--count'])):
            print (
                    ' '.join([pick(adjs) for x in range(0, int(arguments['--adjectives']))]) + 
                    ' ' + '-'.join([pick(events) for x in range(0, int(arguments['--nouns']))]) + ' in the ' +
                    ' '.join([pick(adjs) for x in range(0, int(arguments['--adjectives']))]) + 
                    ' ' + '-'.join([pick(locs) for x in range(0, int(arguments['--nouns']))]) )

