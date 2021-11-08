#  Copyright (c) 2021 Robert Bosch GmbH
#  All rights reserved.
#
#  This source code is licensed under the BSD 3-Clause license found in the
#  LICENSE file in the root directory of this source tree.
#
#  Author: Stefan Grünewald

import re


class NegationInstance:
    """Class for representing a single negation instance.

    Cues, scopes and events are internally represented as lists of (index, word_form).
    """
    
    def __init__(self, i, sentence):
        self.id = i
        self.sentence = sentence
        
        # Collect tokens involved in the negation instance (cue, scope, event)
        self.cue = []
        self.affix_cue = False  # 
        self.scope = []
        self.event = []

        for token in sentence:
            for cue_neg_inst_id, cue_form in token.cue:
                if cue_neg_inst_id == self.id:
                    self.cue.append((token.id, cue_form))
                    if cue_form != token._form:  # affix negation!
                        self.affix_cue = True
            for scope_neg_inst_id, scope_form in token.scope:
                if scope_neg_inst_id == self.id and not ispunct(scope_form):
                    self.scope.append((token.id, scope_form))
            for event_neg_inst_id, event_form in token.event:
                if event_neg_inst_id == self.id:
                    self.event.append((token.id, event_form))
                
        # Compute some characteristics of the negation instance
        self.multiword_cue = len(self.cue) > 1
        self.multiword_event = len(self.event) > 1
        self.scope_length = len(self.scope)
        self.has_event = bool(self.event)
        
        assert self.cue
        # assert not (self.affix_cue and self.multiword_cue)

    def __str__(self):
        s = '*** NEGATION INSTANCE ***'
        s += '\n* sentence: ' + " ".join([t._form for t in self.sentence])
        s += '\n* cue:      ' + " ".join([c[1] for c in self.cue])
        if self.multiword_cue:
            s += ' (multiword cue)'
        if self.affix_cue:
            s += ' (affix cue)'
        s += '\n* scope:    ' + " ".join([s[1] for s in self.scope])
        if self.event:
            s += '\n* event:    ' + " ".join([e[1] for e in self.event])
            if self.multiword_event:
                s += ' (multiword event)'
        s += "\n* Some stats:"
        s += "\n* scope length: " + str(self.scope_length)
        s += "\n* sentence length: " + str(len(self.sentence))
        return s


def read_negation_instances_from_corpus(conll_data):
    """Method for reading in negation instances from a corpus file.
    
    Args:
        conll_data: PyConll representation of the given corpus.

    Returns: A list of lists, each of which contains the NegationInstances
      for the corresponding sentence. (The lists may also be empty if the corresponding
      sentence does not have a negation instance.)
    """
    all_neg_instances = []  # Negation instances, grouped into lists by sentence

    for sentence in conll_data:
        # Collect negation instance IDs
        neg_inst_ids = set()
        for token in sentence:
            if token.cue:
                for i, _ in token.cue:
                    neg_inst_ids.add(i)

        # Create actual negation instances
        curr_neg_instances = []
        for i in sorted(neg_inst_ids):
            curr_neg_instances.append(NegationInstance(i, sentence))

        all_neg_instances.append(curr_neg_instances)
    
    # Single negation instance in the sentence or several?
    for sentence_neg_instances in all_neg_instances:
        num_neg_instances_in_sent = len(sentence_neg_instances)
        for neg_instance in sentence_neg_instances:
            neg_instance.num_neg_instances_in_sent = num_neg_instances_in_sent
    
    return all_neg_instances


def ispunct(token):
    return not bool(re.search("\w", token))

