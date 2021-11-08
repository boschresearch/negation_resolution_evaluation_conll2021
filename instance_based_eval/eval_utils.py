#  Copyright (c) 2021 Robert Bosch GmbH
#  All rights reserved.
#
#  This source code is licensed under the BSD 3-Clause license found in the
#  LICENSE file in the root directory of this source tree.
#
#  Author: Stefan Grünewald

import numpy as np


class EvaluationResult:
    """Class for representing the results of a negation evaluation run.
    As of now, the included metrics are precision, recall, F1 score for cues and scopes.
    """
    def __init__(self, cue_precision, cue_recall, cue_f1, scope_precision, scope_recall, scope_f1):
        self.cue_precision = cue_precision
        self.cue_recall = cue_recall
        self.cue_f1 = cue_f1

        self.scope_precision = scope_precision
        self.scope_recall = scope_recall
        self.scope_f1 = scope_f1

    @classmethod
    def from_counts(cls, num_instances_gold, num_instances_system, num_instances_matched,
                   scope_precision_numerator, scope_precision_denominator,
                   scope_recall_numerator, scope_recall_denominator):
        """Create an EvaluationResult instance from """
        cue_precision = num_instances_matched / num_instances_system
        cue_recall = num_instances_matched / num_instances_gold
        cue_f1 = (2 * cue_precision * cue_recall) / (cue_precision + cue_recall) if cue_precision+cue_recall else 0.0

        scope_precision = scope_precision_numerator / scope_precision_denominator
        scope_recall = scope_recall_numerator / scope_recall_denominator
        scope_f1 = (2 * scope_precision * scope_recall) / (scope_precision + scope_recall) if scope_precision + scope_recall else 0.0

        return cls(cue_precision, cue_recall, cue_f1, scope_precision, scope_recall, scope_f1)

    @classmethod
    def average(cls, eval_results):
        """Create an EvaluationResult instance representing the average of a list of EvaluationResults.

        Args:
            eval_results: An iterable of EvaluationResults.

        Returns: A new EvaluationResult instance containing the averages of all metrics.
        """
        avg_cue_precision = np.mean([e.cue_precision for e in eval_results])
        avg_cue_recall = np.mean([e.cue_recall for e in eval_results])
        avg_cue_f1 = np.mean([e.cue_f1 for e in eval_results])

        avg_scope_precision = np.mean([e.scope_precision for e in eval_results])
        avg_scope_recall = np.mean([e.scope_recall for e in eval_results])
        avg_scope_f1 = np.mean([e.scope_f1 for e in eval_results])

        return cls(avg_cue_precision, avg_cue_recall, avg_cue_f1, avg_scope_precision, avg_scope_recall, avg_scope_f1)

    def __str__(self):
        res = ""
        res += "Cue precision:    {:.1f}\n".format(self.cue_precision*100)
        res += "Cue recall:       {:.1f}\n".format(self.cue_recall*100)
        res += "Cue F1:           {:.1f}\n".format(self.cue_f1*100)
        res += "\n"
        res += "Scope precision:  {:.1f}\n".format(self.scope_precision*100)
        res += "Scope recall:     {:.1f}\n".format(self.scope_recall*100)
        res += "Scope F1:         {:.1f}\n".format(self.scope_f1*100)

        return res


def get_matching_instances(gold_sent, system_sent):
    """For a pair of negation-annotated sentences (gold, system), provide a list of NegationInstances
    that match between the two. A match is here defined as exact cue match (i.e., the set of cue tokens
    has to be exactly equal for the instances to be matched.)
 
    Args:
        gold_sent: The gold annotations (NegationInstances) for the underlying sentence.
        system_sent: The system annotations (NegationInstances) for the underlying sentence.

    Returns: A list of matched instances between the gold and sytem annotations.
    """
    consumed_gold_instances = set()
    # Keep track of which gold instances have already been matched up.
    # This is to prevent several system instances from matching up with the same gold instance
    # (which, admittedly, probably never happens in the first place).

    matched_instances = []
    for system_inst in system_sent:
        for gold_inst in gold_sent:
            if gold_inst.id not in consumed_gold_instances:  # Skip gold instances that have already been matched up
                if system_inst.cue == gold_inst.cue:  # Exact cue match detected
                    matched_instances.append((gold_inst, system_inst))
                    consumed_gold_instances.add(gold_inst.id)


    return matched_instances


def scope_match_tokens(gold_inst, system_inst):
    """Given a gold NegationInstance and matched system NegationInstance, count the number of matching
    scope tokens between them.

    Args:
        gold_inst: The gold NegationInstance.
        system_inst: The system NegationInstance.

    Returns: A triple consisting of
      1) the number of tokens in the gold scope;
      2) the number of tokens in the system scope;
      3) the number of tokens that match up between the two.
    """
    # Count tokens that match up between scopes
    num_matched_tokens = 0
    for token1 in gold_inst.scope:
        for token2 in system_inst.scope:
            if token1 == token2: # matching by position and word form
                num_matched_tokens += 1

    return len(gold_inst.scope), len(system_inst.scope), num_matched_tokens,   # Gold, predicted, correct


def scope_match_normalized(gold_inst, system_inst):
    """Given a gold NegationInstance and matched system NegationInstance, calcuate the overlap of scopes
    between them, normalizing by scope length.

    Args:
        gold_inst: The gold NegationInstance.
        system_inst: The system NegationInstance.

    Returns: A triple consisting of 
      1) scope precision, defined as num_matched_tokens / len(system_inst.scope);
      2) scope recall, defined as num_matched_tokens / len(gold_inst.scope);
      3) scope F1.
    """
    # Count tokens that match up between scopes
    num_matched_tokens = 0
    for token1 in gold_inst.scope:
        for token2 in system_inst.scope:
            if token1 == token2: # matching by position and word form
                num_matched_tokens += 1


    # Determine precision and recall for this scope
    if len(gold_inst.scope) == 0 and len(system_inst.scope) == 0:
        precision = 1.0
        recall = 1.0
    elif len(gold_inst.scope) == 0 and len(system_inst.scope) > 0:
        precision = 0.0
        recall = 1.0
    elif len(gold_inst.scope) > 0 and len(system_inst.scope) == 0:
        precision = 1.0
        recall = 0.0
    else:
        precision = num_matched_tokens / len(system_inst.scope)
        recall = num_matched_tokens / len(gold_inst.scope)
            
    f1 = 2*precision*recall/(precision+recall) if precision+recall else 0.0

    return precision, recall, f1

