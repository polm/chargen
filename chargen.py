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
import gc
from collections import Counter

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

if __name__ == '__main__':
    arguments = docopt(__doc__, version='Character Generator 0.1')
    print "Reading file..."
    tagged = get_tagged_counts(arguments['<file>'])
    print "Tagging finished"
    # As a lazy stop word filter, remove the most common 10% of words.
    #tagged = tagged.most_common()[int(len(tagged.keys())/10):]
    tagged = tagged.keys()
    # Do some cleanup
    tagged = set(map(lambda x: (first(x).lower(), last(x)), tagged))
    tagged = filter(lambda x: not has_hypernym(first(x), 'number'),tagged)
    # Necessary if plaintext tables are around
    tagged = filter(lambda x: not '|' in first(x),tagged)
    print tagged[0:10]

    # Get the adjectives
    adjs = map(first, filter(lambda x: last(x) == 'JJ', tagged))
    nouns = map(first, filter(lambda x: last(x) == 'NN', tagged))
    print nouns[0:10]



    if not arguments['--event']:
        # Get the nouns that describe people
        is_person = lambda x: has_hypernym(x,'person')
        people = filter(is_person, nouns)

        for chars in range(0, int(arguments['--count'])):
            print (' '.join([pick(adjs) for x in range(0, int(arguments['--adjectives']))]) + 
                    ' ' + '-'.join([pick(people) for x in range(0, int(arguments['--nouns']))]) )

    else:
        print "getting locs"
        # Get nouns that are locations
        is_place = lambda x: has_hypernym(x,'location') or has_hypernym(x,'structure')
        locs = filter(is_place, nouns)

        # Get events
        is_event = lambda x: has_hypernym(x,'event')
        events = filter(is_event, nouns)
        
        for chars in range(0, int(arguments['--count'])):
            print (
                    ' '.join([pick(adjs) for x in range(0, int(arguments['--adjectives']))]) + 
                    ' ' + '-'.join([pick(events) for x in range(0, int(arguments['--nouns']))]) + ' in the ' +
                    ' '.join([pick(adjs) for x in range(0, int(arguments['--adjectives']))]) + 
                    ' ' + '-'.join([pick(locs) for x in range(0, int(arguments['--nouns']))]) )

