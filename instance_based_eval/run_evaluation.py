#  Copyright (c) 2021 Robert Bosch GmbH
#  All rights reserved.
#
#  This source code is licensed under the BSD 3-Clause license found in the
#  LICENSE file in the root directory of this source tree.
#
#  Author: Stefan Grünewald

import argparse
import myconll

import numpy as np

import code

from negation_instance import NegationInstance, read_negation_instances_from_corpus
from eval_utils import EvaluationResult, get_matching_instances, scope_match_normalized, scope_match_tokens

def run_evaluation_single(gold_path, system_path, normalize_scopes=True):
    """Run evaluation on a single pair of (gold, system) corpora and return results as an EvaluationResult object.

    Args:
        gold_path: Path to the gold corpus file.
        system_path: Path to the system corpus file.
        normalize_scopes: Whether to normalize scope length when calculating scope metrics. Default: True.
    Returns: An EvaluationResult object containing the results of the evaluation.
    """
    gold_data = myconll.load_from_file(gold_path)
    system_data = myconll.load_from_file(system_path)

    neg_sents_gold = read_negation_instances_from_corpus(gold_data)
    neg_sents_system = read_negation_instances_from_corpus(system_data)

    eval_result = evaluate_sents(neg_sents_gold, neg_sents_system, normalize_scopes=normalize_scopes)

    return eval_result


def run_evaluation_multiple(gold_path, system_paths, normalize_scopes=True):
    """Run evaluations on a single gold corpus and multiple prediction files on the same data.
    Output results for individual evaluations as well as the average.

    Args:
        gold_path: Path to the gold corpus file.
        system_paths: List of paths to system corpus files.
        normalize_scopes: Whether to normalize scope length when calculating scope metrics. Default: True.
    """
    # Run individual evaluations on all provided system files
    eval_results = []
    for system_file in system_paths:
        curr_eval_results = run_evaluation_single(args.gold_file, system_file, normalize_scopes=normalize_scopes)
        eval_results.append(curr_eval_results)
        print(system_file)
        print(curr_eval_results)

    # If more than one system file was provided, average results and output
    if len(eval_results) > 1:
        pooled_eval_results = EvaluationResult.average(eval_results)
        print("AVERAGE")
        print(pooled_eval_results)


def evaluate_sents(neg_sents_gold, neg_sents_system, normalize_scopes=True):
    """Core function for evaluating one set of negation instances against another.

    Args:
        neg_sents_gold: List of negation sentences, each one being a list of gold NegationInstances.
        neg_sents_system: List of negation sentences, each one being a list of system-produced NegationInstances.
        normalize_scopes: Whether to normalize scope length when calculating scope metrics. Default: True.
    Returns: An EvaluationResult object containing the results of the evaluation.
    """
    num_instances_gold = len([inst for sent in neg_sents_gold for inst in sent])
    num_instances_system = len([inst for sent in neg_sents_system for inst in sent])

    num_instances_matched = 0

    scope_precision_numerator = 0.0
    scope_recall_numerator = 0.0

    for gold_sent, system_sent in zip(neg_sents_gold, neg_sents_system):
        for m_gold_inst, m_sys_inst in get_matching_instances(gold_sent, system_sent):
            num_instances_matched += 1

            if normalize_scopes:
                p, r, _ = scope_match_normalized(m_gold_inst, m_sys_inst)
                scope_precision_numerator += p
                scope_recall_numerator += r
            else:
                _, _, num_correct_tok = scope_match_tokens(m_gold_inst, m_sys_inst)
                scope_precision_numerator += num_correct_tok
                scope_recall_numerator += num_correct_tok

    if normalize_scopes:
        scope_precision_denominator = num_instances_system
        scope_recall_denominator = num_instances_gold
    else:
        scope_precision_denominator = sum([inst.scope_length for sent in neg_sents_system for inst in sent])
        scope_recall_denominator = sum([inst.scope_length for sent in neg_sents_gold for inst in sent])

    eval_result = EvaluationResult.from_counts(num_instances_gold, num_instances_system, num_instances_matched,
                                               scope_precision_numerator, scope_precision_denominator,
                                               scope_recall_numerator, scope_recall_denominator)

    return eval_result


if __name__ == "__main__":
    argparser = argparse.ArgumentParser(description='Negation resolution evaluation')

    # Required arguments
    argparser.add_argument('gold_file', type=str, help='path to gold corpus file (required)')
    argparser.add_argument('system_files', type=str, nargs='+', help='path(s) to system file(s) (required)')  

    # Optional arguments  
    argparser.add_argument('-t', '--token-eval', dest='normalize_scopes', action='store_false',
                           help='Evaluate scopes on a per-token basis (i.e., do not normalize scope lengths)')
    argparser.set_defaults(normalize_scopes=True)

    args = argparser.parse_args()

    if len(args.system_files) == 1:  # Evaluate exactly one system file
        system_file = args.system_files[0]
        eval_result = run_evaluation_single(args.gold_file, system_file, normalize_scopes=args.normalize_scopes)
        print(eval_result)
        exit()
    else:  # Evaluate multiple system files and average
        run_evaluation_multiple(args.gold_file, args.system_files,  normalize_scopes=args.normalize_scopes)
        exit()

