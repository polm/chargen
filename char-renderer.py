#!/usr/bin/env python
"""Character renderer using previously generated files.

Usage:
    char-renderer <file> <template> [--number=N] [--japanese]

Template keywords begin with a colon and include nn, jj, person, event, location, and item. Following a colon with an exclamation point will capitalize the word.

Additionally, multiple input files can be specified by separating them with commas.

Japanese input mode removes all half-width spaces from the output. 

Options:
    -n N --number N   How many times to render the template [default: 1]
    -j   --japanese   Japanese mode (see help)
"""

import json
import os
from docopt import docopt
from random import random
from copy import deepcopy

# UTF8 magic
import sys
reload(sys)
sys.setdefaultencoding('utf-8')

#For convenience. Feel free to add.
mappings = {
        'jj': 'adjectives',
        'person': 'people',
        'loc': 'locations',
        'event': 'events',
        'item': 'items',
        'name': 'names'
        }

def pick(ll):
    """Pick a random element from a list"""
    return ll[int(random() * len(ll))]

def dictmerge(dicts):
    """Merge together a list of dictionaries, keeping all values."""
    # Each key maps to a list of strings.
    master = {}
    for dd in dicts:
        for key in dd:
            if not key in master:
                master[key] = []
            master[key] = list(set(master[key] + dd[key]))
    return master

def load_file(fname):
    input_file = open(fname)
    data = json.loads(input_file.read())
    input_file.close()
    return data

def render(token, data):
    if token[0:2] == "'s" or token in ',!?:;.':
        return "%%" + token
    # Pass through non-special tokens
    if token[0] not in '%:':
        return token

    # Can this word re-occur in a single output?
    unique = True if token[0] == '%' else False

    # Remove prefix 
    token = token[1:]
    
    capital = (token[0] == '!')
    if capital: token = token[1:]

    # Use a mapping if needed
    token = mappings[token] if (token in mappings) else token

    result = pick(data[token])
    if unique: data[token].remove(result)
    if capital: result = result.capitalize()

    return result

def render_sentence(joiner, template, filler):
    filler = deepcopy(filler) # Make a copy; we're going to modify it for unique results
    output = ''
    for word in template:
        output += joiner + render(word, filler)
    output = output.replace(' %%', '')
    return output

if __name__ == '__main__':
    arguments = docopt(__doc__, version='Character Renderer 0.1')
    files = arguments['<file>'].split(',')
    words = dictmerge(map(load_file, files))
    template = arguments['<template>'].split(' ')
    joiner = '' if arguments['--japanese'] else ' '

    for xx in range(0,int(arguments['--number'])):
        print(render_sentence(joiner, template, words))

