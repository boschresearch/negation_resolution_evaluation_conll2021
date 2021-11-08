#  Copyright (c) 2021 Robert Bosch GmbH
#  All rights reserved.
#
#  This source code is licensed under the BSD 3-Clause license found in the
#  LICENSE file in the root directory of this source tree.
#
#  Author: Elizaveta Sineva

"""
Re-implementation and extension of 
*SEM Shared Task 2012 evaluation script for CD-SCO task.
"""

import argparse  # take args from a command line
import re        # check for punctuation


class Score:
    """
    Stores the number of instances in gold file (gold) and system output file (pred),
        as well as true positives (tp), false positives (fp) and 
        false negatives (fn) for a metric.
    For fp, two versions are stored:
        fp - all false positives (including elements that are also fn)
        fp_no_fn - only false positives that do not intersect with fn
    Calculates precision, recall and F1.
    """
    def __init__(self):
        """
        rounding specifes the number of digits after the decimal point.
        """
        self._tp = 0
        self._fp = 0
        self._fp_no_fn = 0
        self._fn = 0


    def __str__(self):
        final_str  = "Gold instances: " + str(self.get_gold()) + "\n"
        final_str += "Predicted instances: " + str(self.get_pred()) + "\n"
        final_str += "TP: " + str(self._tp) + "\n"
        final_str += "FP: " + str(self._fp) + "\n"
        if self._fp_no_fn:
            final_str += "FP (excluding intersection with FN): " + str(self._fp_no_fn) + "\n"
        final_str += "FN: " + str(self._fn) + "\n"
        return final_str


    def update_counter(self, counter_name, update_amount):
        if counter_name == 'tp':
            self._tp += update_amount
        elif counter_name == 'fp':
            self._fp += update_amount
        elif counter_name == 'fp_no_fn':
            self._fp_no_fn += update_amount
        elif counter_name == 'fn':
            self._fn += update_amount


    def get_gold(self):
        """
        Get the number of instances in gold file.
        """
        return self._tp + self._fn
#        return self._gold


    def get_pred(self):
        """
        Get the number of instances in gold file.
        """
        return self._tp + self._fp
#        return self._pred

    
    def get_tp(self):
        return self._tp


    def get_fn(self):
        return self._fn


    def get_fp(self, no_fn=False):
        if no_fn:
            return self._fp_no_fn
        else:
            return self._fp
       
        
    def get_precision(self, no_fn=False):
        """
        no_fn:
            True  - calculate precision as tp/(tp+fp-intersection(fp,fn))
            False - calculate precision as tp/(tp+fp) (B-score in *SEM 2012)
        """
        if no_fn:
            return self._tp / (self._tp + self._fp_no_fn) if (self._tp + self._fp_no_fn) else 0.0
        else:
            return self._tp / self.get_pred() if self.get_pred() else 0.0
#            return self._tp / (self._tp + self._fp) if (self._tp + self._fp) else 0.0


    def get_recall(self):
        return self._tp / self.get_gold() if self.get_gold() else 0.0
#        return self._tp / (self._tp + self._fn) if (self._tp + self._fn) else 0.0
    
    
    def get_f1(self, no_fn=False):
        precision = self.get_precision(no_fn=no_fn)
        recall = self.get_recall()
        return 2 * precision * recall / (precision + recall) if (precision + recall) else 0.0

    

def process_sent(gold_tokens, pred_tokens, line_num):
    """
    gold_tokens - a list of tokens from one sentence in the gold file
    pred_tokens - a list of tokens from the same sentence in the system file
    line_num - the number of the line the current sentence starts in both files
    
    Returns two lists of dictionaries (one for each file) in the form:
        [ {label : [list of tuples (token_num, word part)]} ]
        where label ∈ {CUE, S (scope), E (event)}
              every dictionary corresponds to a sentence
              length of the list = number of negation / speculation instances
    """
    
    gold_instances = []  # [ {label : [list of tuples (token_num, word part)]} ]
    pred_instances = []  # [ {label : [list of tuples (token_num, word part)]} ]
    
    gold_negspec_size = 0    # number of task instances in the gold sentence
    pred_negspec_size = 0    # number of task instances in the pred sentence


    def collect_col_info(instances, cols, negspec_size):
        """
        Adds negation / speculation column info to gold / pred instances.
        Modifies instances.
        """
        for pos_num in range(negspec_size):
            
            # 7 - start of the task info
            # every 3 cols - new instance
            starter_col = 7+3*pos_num
            
            cue = cols[starter_col]      # 1st col - cue
            scope = cols[starter_col+1]  # 2nd col - scope
            event = cols[starter_col+2]  # 3rd col - event
            
            # cases with words with dot at the end (e.g. Mr./Dr.)
            # remove the dot (*SEM 2012 gold files did not include dot in scope tokens)
            if len(scope) > 1 and scope.endswith("."):
                scope = scope[:-1]
            if len(event) > 1 and event.endswith("."):
                event = event[:-1]            
            
            if cue != "_":
                instances[pos_num].setdefault("Cue", [])
                instances[pos_num]["Cue"].append((cols[2], cue))
            if scope != "_":
                instances[pos_num].setdefault("Scope", [])
                instances[pos_num]["Scope"].append((cols[2], scope))
            if event != "_":
                instances[pos_num].setdefault("Event", [])
                instances[pos_num]["Event"].append((cols[2], event))


    for token_idx in range(len(gold_tokens)):
        gold_cols = gold_tokens[token_idx].split("\t")
        pred_cols = pred_tokens[token_idx].split("\t")
        
        gold_token_num = gold_cols[2]
        pred_token_num = pred_cols[2]
        gold_word = gold_cols[3].lower()
        pred_word = pred_cols[3].lower()

        # make sure the gold and pred tokens are the same
        assert_msg = "Mismatch between tokens in gold and system files "
        assert_msg += "at line " + str(line_num) + "."
        assert gold_token_num == pred_token_num, assert_msg
        assert gold_word == pred_word, assert_msg

        # make sure the task information is encoded correctly
        gold_size = 0 if len(gold_cols[7:]) == 1 else len(gold_cols[7:]) / 3
        assert_msg = "Incorrect number of columns at line " + str(line_num)
        assert_msg += " of the gold file. There should be 3 columns per negation cue."
        assert gold_size % 1 == 0, assert_msg

        pred_size = 0 if len(pred_cols[7:]) == 1 else len(pred_cols[7:]) / 3
        assert_msg = "Incorrect number of columns in line " + str(line_num)
        assert_msg += " of the system file. There should be 3 columns per negation cue."
        assert pred_size % 1 == 0, assert_msg
        
        # mark the number of task instances in the sents
        if token_idx == 0:
            gold_negspec_size = int(gold_size)
            pred_negspec_size = int(pred_size)
            gold_instances = [{} for _ in range(gold_negspec_size)]
            pred_instances = [{} for _ in range(pred_negspec_size)]
            
        # make sure the number of task instances stays the same
        else:
            assert_msg = "Inconsistency detected in the number of columns in line "
            assert_msg += str(line_num) + " of the gold file. All tokens in "
            assert_msg += "a sentence should have the same number of columns."
            assert gold_size == gold_negspec_size, assert_msg

            assert_msg = "Inconsistency detected in the number of columns in line "
            assert_msg += str(line_num) + " of the system file. All tokens in "
            assert_msg += "a sentence should have the same number of columns."
            assert pred_size == pred_negspec_size, assert_msg
        
        # collect all neg / spec instances
        collect_col_info(gold_instances, gold_cols, gold_negspec_size)
        collect_col_info(pred_instances, pred_cols, pred_negspec_size)
        
        line_num += 1
    
    return gold_instances, pred_instances


def evaluate(gold_str, system_str, task="negation"):
    """
    Main evaluation function.
    """
    scores = {"Token-level": {"Cue": {"": Score()},
                              "Scope": {"(full cue)": Score(),
                                        "(partial cue)": Score(),
                                        "(no cue)": Score(),
                                        "(binary labels)": Score(),
                                        "(full cue, no punct)": Score(),
                                        "(partial cue, no punct)": Score(),
                                        "(no cue, no punct)": Score(),
                                        "(binary labels, no punct)": Score()},
                              "Event": {"(full cue)": Score(),
                                        "(partial cue)": Score(),
                                        "(no cue)": Score(),
                                        "(binary labels)": Score()}}, 
              "Scope-level": {"Cue": {"": Score()},
                              "Scope": {"(full cue)": Score(),
                                        "(partial cue)": Score(),
                                        "(no cue)": Score(),
                                        "(full cue, no punct)": Score(),
                                        "(partial cue, no punct)": Score(),
                                        "(no cue, no punct)": Score()},
                              "Event": {"(full cue)": Score(),
                                        "(partial cue)": Score(),
                                        "(no cue)": Score()}, 
                              "Full "+task: {"": Score(),
                                             "(no punct)": Score()}}}
    
    gold_sents = gold_str.strip().split("\n\n")
    pred_sents = system_str.strip().split("\n\n")
    
    # the number of sentences with negation / speculation where it was predicted correctly
    correct_negspec_sent_num = {"": 0, "(no punct)": 0}
    # the number of sentences with negation / speculation
    negspec_sent_num = 0

    # the number of sentences where negation / speculation was predicted / not predicted correctly
    correct_sent_num = {"": 0, "(no punct)": 0}
    # the number of sentences overall
    all_sent_num = len(gold_sents)
    
    # make sure both files have the same number of sentences
    assert_msg = "The gold and system files have a different number of sentences."
    assert all_sent_num == len(pred_sents), assert_msg
    
    # keep track of lines for error messages
    line_num = 1
  

    def update_all(counter, scores, pred_instance):
        """
        counter - fn | fp
        Adds FNs / FPs (as specified in counter) for every metric 
        in predicted instance (except for cue-independent metrics (incl. cue itself)
        that are processed separately).
        Adds to instance counter for every metric.
        Modifies scores dictionary.
        """
        # update fp_no_fn for cue (the only cue-related part that is processed here)
#        if counter == "fp":
#            scores["Scope-level"]["Cue"][""].update_counter("fp_no_fn", 1)
        
        # update fp scores and number of predicted instances
        for metric in ["Scope", "Event", "Full "+task]:
            metric_tokens = pred_instance.get(metric, [])
        
            # token-level
            for token in metric_tokens:
                 for detail in scores["Token-level"].get(metric, {}):
                     
                     # if the current token is punctuation
                     if "punct" in detail and not re.search("\w", token[1]):
                         continue  # don't add fp for no punct metrics
                     
                     # cue-independent metrics are processed separately
                     if "no cue" in detail or "binary labels" in detail:
                         continue
                    
                     full_metric_name = scores["Token-level"][metric][detail]
                     full_metric_name.update_counter(counter, 1)
#                     if counter == "fn":
#                         full_metric_name.update_counter("gold", 1)
#                     if counter == "fp":
##                         full_metric_name.update_counter("pred", 1)
#                         # if tokens mismatched because of word mismatch only
#                         # --> NOT fp_no_fn (here only the ones not present in gold)
#                         full_metric_name.update_counter("fp_no_fn", 1)
            
            # scope-level
            if metric_tokens or metric == "Full "+task:
                for detail in scores["Scope-level"][metric]:
                    # cue-independent metrics are [mostly] processed separately
                    if "no cue" in detail:
                        continue
                    
                    full_metric_name = scores["Scope-level"][metric][detail]
                    full_metric_name.update_counter(counter, 1)
#                    if counter == "fn":
#                        full_metric_name.update_counter("gold", 1)
                    if counter == "fp":
#                        full_metric_name.update_counter("pred", 1)
                        full_metric_name.update_counter("fp_no_fn", 1)


    def process_inst(scores, gold_tokens, pred_tokens, metric, full_cue=True):
        """
        metric - Scope | Event
        full_cue - True if the cue of the current instance was predicted correctly.
        
        Processes one instance of negation / speculation in gold and pred.
        Returns a dictionary with two Booleans for including and excluding
        punctuation metrics, which are set to True if all pred tokens matched
        gold tokens, and False otherwise.
        Modifies scores dictionary.
        """
        # flag to check if gold matches pred fully for a given metric
        full_match = {"": True, "(no punct)": True}
        
        # if there are no instances in both gold and pred, return True for full match
        if not gold_tokens and not pred_tokens:
            return full_match
        
        # collect gold token ids
        gold_ids = []
        # flag for scope-level to see if there is an instance in the system
        pred = True if pred_tokens else False
        
        ## token-level ##
        for gold_token in gold_tokens:
            gold_ids.append(gold_token[0]) # collect gold token id
            
            # check if the current token is punctuation
            punct = False if re.search("\w", gold_token[1]) else True
            
            # if gold token matches system token --> tp
            if gold_token in pred_tokens:
                for detail in scores["Token-level"].get(metric, {}):
                    # if the current metric is excluding punctuation
                    if "punct" in detail and punct:
                        continue  # don't add anything
                    
                    # cue-independent metrics are processed separately
                    if "no cue" in detail or "binary labels" in detail:
                        continue

                    full_metric_name = scores["Token-level"][metric][detail]
                    full_metric_name.update_counter("gold", 1)
                    full_metric_name.update_counter("pred", 1)
                
                    # cases that do not allow partial cue match
                    if "full" in detail and not full_cue:
                        full_metric_name.update_counter("fp", 1)
                        full_metric_name.update_counter("fn", 1)
                    # cases that allow partial cue match
                    else:
                        full_metric_name.update_counter("tp", 1)
                
                pred_tokens.remove(gold_token) # get rid of the checked part
                
            # if not --> fn
            else:
                full_match[""] = False
                if not punct:
                    full_match["(no punct)"] = False 

                for detail in scores["Token-level"].get(metric, {}):
                    # if the current metric is excluding punctuation
                    if "punct" in detail and punct:
                        continue  # don't add anything

                    # cue-independent metrics are processed separately
                    if "no cue" in detail or "binary labels" in detail:
                        continue

                    full_metric_name = scores["Token-level"][metric][detail]
                    full_metric_name.update_counter("gold", 1)
                    full_metric_name.update_counter("fn", 1)
        
        # if there are tokens in pred that are not in gold --> fp
        for pred_token in pred_tokens:
            # check if the current token is punctuation
            punct = False if re.search("\w", pred_token[1]) else True

            full_match[""] = False
            if not punct:
                full_match["(no punct)"] = False 
            
            for detail in scores["Token-level"].get(metric, {}):
                # if the current metric is excluding punctuation
                if "punct" in detail and punct:
                    continue  # don't add anything

                # cue-independent metrics are processed separately
                if "no cue" in detail or "binary labels" in detail:
                    continue
                
                scores["Token-level"][metric][detail].update_counter("pred", 1)
                scores["Token-level"][metric][detail].update_counter("fp", 1)
                
                # don't update fp that exclude intersections with fn 
                # if the token was predicted, but the word boundaries were wrong
                if pred_token[0] not in gold_ids:
                    scores["Token-level"][metric][detail].update_counter("fp_no_fn", 1)
        
        ## scope-level ##
        for detail in scores["Scope-level"].get(metric, {}):
            # cue-independent metrics are processed separately
            if "no cue" in detail:
                continue

            full_metric_name = scores["Scope-level"][metric][detail]
            
            if gold_tokens:
                full_metric_name.update_counter("gold", 1)
            if pred:
                full_metric_name.update_counter("pred", 1)
            
            # cases that do not allow partial cue match
            if "full" in detail and not full_cue:
                if gold_tokens:
                    full_metric_name.update_counter("fn", 1)
                if pred:
                    full_metric_name.update_counter("fp", 1)
                if not gold_tokens:
                    full_metric_name.update_counter("fp_no_fn", 1)
            
            # cases that allow partial cue match and exclude punctuation
            elif "punct" in detail:
                # if all parts were correct (excluding punctuation) --> tp
                if full_match["(no punct)"]:
                    full_metric_name.update_counter("tp", 1)
                # if not --> fn | fp
                else:
                    if gold_tokens:
                        full_metric_name.update_counter("fn", 1)
                    if pred:
                        full_metric_name.update_counter("fp", 1)
                    if not gold_tokens:
                        full_metric_name.update_counter("fp_no_fn", 1)                        
            
            # cases that allow partial cue match and include punctuation
            else:
                # if all parts were correct --> tp
                if full_match[""]:
                    full_metric_name.update_counter("tp", 1)
                # if not --> fn | fp
                else:
                    if gold_tokens:
                        full_metric_name.update_counter("fn", 1)
                    if pred:
                        full_metric_name.update_counter("fp", 1)
                    if not gold_tokens:
                        full_metric_name.update_counter("fp_no_fn", 1)   
        
        # end of process_inst function
        return full_match
    
    
    def process_independent(scores, gold_insts, pred_insts):
        """
        gold_insts / pred_insts - a list of gold / predicted instances (dict) 
                                in the form:
                                [{label : [ (token_id, word), (...), ... ] }, {...}, ...]

        Processes all negation / speculation instances in gold and pred.
        Calculates token- and scope-level scores for cue-independent metrics 
            (including metrics for the cue itself).
        Modifies scores dictionary.
        """
        # collect predicted information
        all_pred_tokens = {"Cue": [], "Scope": [], "Event": []} # token-level
        full_pred_insts = {"Cue": [], "Scope": [], "Event": []} # scope-level
        nopunct_pred_insts = [] # exclude punctuation for scope's "no punct" metric
        
        # collect all tokens belonging to the given label from pred
        for pred in pred_insts:
            for label in all_pred_tokens:
                pred_tokens = list(pred.get(label, []))
                if not pred_tokens: # if there was no scope / no event in the instance
                    continue
                
                all_pred_tokens[label] += pred_tokens
                full_pred_insts[label].append(pred_tokens)

                # exclude punctuation for "no punct" scope metric
                if label == "Scope":             
                    nopunct_pred = []
                    for token_tuple in pred_tokens:
                        punct = False if re.search("\w", token_tuple[1]) else True
                        if not punct:
                            nopunct_pred.append(token_tuple)
                    nopunct_pred_insts.append(nopunct_pred)
                
        # binary
        pred_token_sets = {"Scope": set(all_pred_tokens["Scope"]), 
                           "Event": set(all_pred_tokens["Event"])}
        gold_token_sets = {"Scope": set(), 
                           "Event": set()}
        
        # keep track of non-tp gold (scope-level) to see later 
        # if there was a partial match (for fp_no_fn)
        not_tp_gold = {"Cue": [], "Scope": [], "Event": [], "no punct": []}
        
        # iterate through gold and find matching predictions
        for gold in gold_insts:
            for label in all_pred_tokens:
                # specify the detail name in for the scores dictionary
                detail_name = "(no cue)" if label != "Cue" else ""

                gold_tokens = gold.get(label, [])
                if not gold_tokens: # if there was no scope / no event in the instance
                    continue

                # exclude punctuation for "no punct" scope metric
                if label == "Scope":
                    nopunct_gold = []
                
                ## token-level
                for token_tuple in gold_tokens:
                    # add to token set
                    if label != "Cue":
                        gold_token_sets[label].add(token_tuple)
                    
                    # exclude punctuation for "no punct" scope metric
                    if label == "Scope":
                        punct = False if re.search("\w", token_tuple[1]) else True
                    
                    # if there is a predicted token matching gold --> tp
                    if token_tuple in all_pred_tokens[label]:
                        scores["Token-level"][label][detail_name].update_counter("tp", 1)
                        if label == "Scope" and not punct:
                            scores["Token-level"]["Scope"]["(no cue, no punct)"].update_counter("tp", 1)
                        all_pred_tokens[label].remove(token_tuple)
                        
                    # if no matching prediction --> fn
                    else:
                        scores["Token-level"][label][detail_name].update_counter("fn", 1)
                        if label == "Scope" and not punct:
                            scores["Token-level"]["Scope"]["(no cue, no punct)"].update_counter("fn", 1)
                        
                    # append non-punctuation tuples to punctuation-free gold instances
                    if label == "Scope" and not punct:
                        nopunct_gold.append(token_tuple)
            
            
                ## scope-level (incl. punct)
                # if there is a prediction matching gold in all elements --> tp
                if gold_tokens in full_pred_insts[label]:
                    scores["Scope-level"][label][detail_name].update_counter("tp", 1)
                    # remove the match from pred list
                    full_pred_insts[label].remove(gold_tokens)
                # if no matching prediction --> fn
                else:
                    scores["Scope-level"][label][detail_name].update_counter("fn", 1)
                    not_tp_gold[label].append([gold_id for gold_id, gold_word in gold_tokens])
                
                if label == "Scope": # scope-specific "no punct" metric
                    ## scope-level (excl. punct)
                    # if there is a prediction matching gold in all elements
                    # (not taking punctuation into account) --> tp
                    if nopunct_gold in nopunct_pred_insts:
                        scores["Scope-level"]["Scope"]["(no cue, no punct)"].update_counter("tp", 1)
                        # remove the match from pred list
                        nopunct_pred_insts.remove(nopunct_gold)
                    # if no matching prediction --> fn
                    else:
                        scores["Scope-level"]["Scope"]["(no cue, no punct)"].update_counter("fn", 1)
                        not_tp_gold["no punct"].append([gold_id for gold_id, gold_word in nopunct_gold])
                
        # add to fp for predicted instances that did not match to gold
        for label in all_pred_tokens:
            
            # specify the detail name in for the scores dictionary
            detail_name = "(no cue)" if label != "Cue" else ""

            ## token-level
            tokens_left = all_pred_tokens[label]
            
            for token_tuple in tokens_left:
                # exclude punctuation for "no punct" scope metric
                if label == "Scope":
                    punct = False if re.search("\w", token_tuple[1]) else True   
                    if not punct:
                        scores["Token-level"]["Scope"]["(no cue, no punct)"].update_counter("fp", 1)                        
                
                # metric including punct
                scores["Token-level"][label][detail_name].update_counter("fp", 1)
            
            ## scope-level
            insts_left = full_pred_insts[label]
            
            for inst in insts_left:               
                scores["Scope-level"][label][detail_name].update_counter("fp", 1)
                                
                # check for partial match, only add to fp_no_fn if there is no match
                partial_match = False
                for pred_id, pred_word in inst:
                    for gold_ids in not_tp_gold[label]:
                        if pred_id in gold_ids:
                            partial_match = True
                            not_tp_gold[label].remove(gold_ids)
                            break
                    # break the second loop when a match is found
                    if partial_match:
                        break
                
                if not partial_match:
                    scores["Scope-level"][label][detail_name].update_counter("fp_no_fn", 1)                
        
        # scope-level scope that excludes punctuation --> fp
        for inst in nopunct_pred_insts:
            scores["Scope-level"]["Scope"]["(no cue, no punct)"].update_counter("fp", 1)

            # check for partial match, only add to fp_no_fn if there is no match
            partial_match = False
            for pred_id, pred_word in inst:
                for gold_ids in not_tp_gold["no punct"]:
                    if pred_id in gold_ids:
                        partial_match = True
                        not_tp_gold["no punct"].remove(gold_ids)
                        break
                # break the second loop when a match is found
                if partial_match:
                    break
            
            if not partial_match:
                scores["Scope-level"][label][detail_name].update_counter("fp_no_fn", 1)

        # binary (every token is counted ONCE)
        for label in gold_token_sets:
            # collect tp and fn
            for gold_token in gold_token_sets[label]:
                if label == "Scope":
                    punct = False if re.search("\w", gold_token[1]) else True
                
                if gold_token in pred_token_sets[label]:
                    scores["Token-level"][label]["(binary labels)"].update_counter("tp", 1)
                    pred_token_sets[label].remove(gold_token)                    
                    if label == "Scope" and not punct:
                        scores["Token-level"]["Scope"]["(binary labels, no punct)"].update_counter("tp", 1)

                else:
                    scores["Token-level"][label]["(binary labels)"].update_counter("fn", 1)
                    if label == "Scope" and not punct:
                        scores["Token-level"]["Scope"]["(binary labels, no punct)"].update_counter("fn", 1)

        
            # collect fp
            for pred_token in pred_token_sets[label]:
                if label == "Scope":
                    punct = False if re.search("\w", pred_token[1]) else True                
                scores["Token-level"][label]["(binary labels)"].update_counter("fp", 1)        
                if label == "Scope" and not punct:
                    scores["Token-level"]["Scope"]["(binary labels, no punct)"].update_counter("fp", 1)
      
        ### END OF process_independent FUNCTION ###
    

    # process gold and prediction sentences
    for sent_idx in range(all_sent_num):
        gold_tokens = gold_sents[sent_idx].split("\n")
        pred_tokens = pred_sents[sent_idx].split("\n")
        
        assert_msg = "The sentences in gold file and system file starting at line " 
        assert_msg += str(line_num) + " are of different length."
        assert len(gold_tokens) == len(pred_tokens), assert_msg
        
        gold_instances, pred_instances = process_sent(gold_tokens, pred_tokens, 
                                                      line_num)
        
        # if both gold and system sentence have no neg/spec
        if gold_instances == pred_instances == []:
            for detail in correct_sent_num:
                correct_sent_num[detail] += 1
        
        
        # if gold has no neg/spec and system does --> fp
        elif not gold_instances and pred_instances:

            # process instances for cue-independent metrics (incl. all cue metrics)
            process_independent(scores, gold_instances, pred_instances)

            for pred_inst in pred_instances:
                update_all("fp", scores, pred_inst)
        
        
        # if gold neg/spec and system doesn't  --> fn
        elif gold_instances and not pred_instances:
            negspec_sent_num += 1

            # process instances for cue-independent metrics (incl. all cue metrics)
            process_independent(scores, gold_instances, pred_instances)
            
            for gold_inst in gold_instances:
                update_all("fn", scores, gold_inst)


        # if both gold and system sentence have neg/spec
        elif gold_instances and pred_instances:
            negspec_sent_num += 1
            
            # process instances for cue-independent metrics (incl. all cue metrics)
            process_independent(scores, gold_instances, pred_instances)
            
            # check if every instance in the sentence was fully correct
            sent_correct = {"": True, "(no punct)": True}
            
            for gold_inst in gold_instances:

                gold_cue = gold_inst.get("Cue", []) # [list of tuples (token_num, word_part)]
                pred_match = None
                full_cue_match = True # flag to check if the cue matches fully

                
                # find matching cue in pred
                for pred_idx in range(len(pred_instances)):
                    pred_inst = pred_instances[pred_idx]
                    pred_cue = pred_inst.get("Cue", [])
                    pred_cue_ids = [cue_tuple[0] for cue_tuple in pred_cue]
                    
                    # check every part of the gold cue for a match with predicted
                    for gold_cue_part in gold_cue:
                        if gold_cue_part[0] in pred_cue_ids:
                            # check for a full cue match
                            if sorted(gold_cue) != sorted(pred_cue):
                                full_cue_match = False
                            
                            # remove found instance from predicted to not process it again
                            pred_match = pred_instances.pop(pred_idx)
                            break
                    
                    # if a match was found - stop looking
                    if pred_match:
                        break
                
                # if no match with system --> all fn
                if not pred_match:
                    update_all("fn", scores, gold_inst)
                    continue                  
                
                # flags for full neg/spec to check if everything is correct
                full_score = {"": full_cue_match, "(no punct)": True}
                
                
                ## SCOPES ##
                gold_scope = gold_inst.get("Scope", [])
                pred_scope = pred_match.get("Scope", [])                
                new_score = process_inst(scores, gold_scope, pred_scope, 
                                         "Scope", full_cue=full_cue_match)
                
                # if the scope wasn't fully correct, 
                # update the flags for full neg / spec
                for detail in new_score:
                    if not new_score[detail]:
                        full_score[detail] = False
                
                
                ## EVENTS ##
                gold_event = gold_inst.get("Event", [])
                pred_event = pred_match.get("Event", [])                
                new_score = process_inst(scores, gold_event, pred_event, 
                                         "Event", full_cue=full_cue_match)
                
                # if the scope wasn't fully correct, 
                # update the flags for full neg / spec
                for detail in new_score:
                    if not new_score[detail]:
                        full_score[detail] = False                
                
    
                ## FULL NEG | SPEC ##
                for detail in scores["Scope-level"]["Full "+task]:
                    full_metric_name = scores["Scope-level"]["Full "+task][detail]
                    full_metric_name.update_counter("gold", 1)
                    full_metric_name.update_counter("pred", 1)
                    
                    # if not everything was correct --> fn / fp
                    if not full_score[detail]:
                        sent_correct[detail] =  False
                        full_metric_name.update_counter("fn", 1)
                        full_metric_name.update_counter("fp", 1)
                    else:
                        full_metric_name.update_counter("tp", 1)                

            # if there are predicted instances that were not in gold --> fp
            for pred_inst in pred_instances:
                sent_correct = {"": False, "(no punct)": False}
                update_all("fp", scores, pred_inst)
            
            # update the info about the sentence correctness
            for detail in correct_negspec_sent_num:
                if sent_correct[detail]:
                    correct_sent_num[detail] += 1
                    correct_negspec_sent_num[detail] += 1


                
        line_num += len(gold_tokens) + 1  # +1 for newline
        
    
    overall_scores = {"# sentences": all_sent_num,
                      "# sentences with errors": all_sent_num-correct_sent_num[""],
                      "% correct sentences": (correct_sent_num[""]/all_sent_num)*100,
                      "# sentences with errors (no punct)": all_sent_num-correct_sent_num["(no punct)"],
                      "% correct sentences (no punct)": (correct_sent_num["(no punct)"]/all_sent_num)*100,
                      "# "+task+" sentences": negspec_sent_num,
                      "# "+task+" sentences with errors": negspec_sent_num-correct_negspec_sent_num[""],
                      "% correct negation sentences": (correct_negspec_sent_num[""]/negspec_sent_num)*100 if negspec_sent_num else 0,
                      "# "+task+" sentences with errors (no punct)": negspec_sent_num-correct_negspec_sent_num["(no punct)"],
                      "% correct negation sentences (no punct)": (correct_negspec_sent_num["(no punct)"]/negspec_sent_num)*100  if negspec_sent_num else 0}

    return scores, overall_scores



def get_print_str(scores, overall_scores, rounding=2):
    """
    rounding specifies the number of digits after the decimal point.
    """
    rounding = str(rounding)
    print_str  = "--------------------------------+------+--------+------+------+------+---------------+------------+---------\n"
    print_str += "                                | gold | system | tp   | fp   | fn   | precision (%) | recall (%) | F1  (%) \n"
    print_str += "--------------------------------+------+--------+------+------+------+---------------+------------+---------\n"
    
    def add_level(header, level, metric_dict, no_fn=False):
        print_str  = "------------------------------------------------------------------------------------------------------------\n"
        print_str += " " + header + "\n"
        print_str += "------------------------------------------------------------------------------------------------------------\n"
        print_str += "--------------------------------+------+--------+------+------+------+---------------+------------+---------\n"
        for metric in metric_dict:
            
            for detail in metric_dict[metric]:                
                metric_score = metric_dict[metric][detail]
                metric_name = (metric + " " + detail).strip() + ":"
                metric_name += " "*(32-len(metric_name)+1)
                metric_name += " {:4d} |".format(metric_score.get_gold())
                metric_name += " {:6d} |".format(metric_score.get_pred())
                metric_name += " {:4d} |".format(metric_score.get_tp())
                metric_name += " {:4d} |".format(metric_score.get_fp(no_fn=no_fn))
                metric_name += " {:4d} |".format(metric_score.get_fn())
                precision_str = " {:13."+rounding+"f} |"
                metric_name += precision_str.format(metric_score.get_precision(no_fn=no_fn)*100)
                recall_str = " {:10."+rounding+"f} |"
                metric_name += recall_str.format(metric_score.get_recall()*100)
                f1_str = " {:7."+rounding+"f}"
                metric_name += f1_str.format(metric_score.get_f1(no_fn=no_fn)*100)
                print_str += metric_name + "\n"
        print_str += "--------------------------------+------+--------+------+------+------+---------------+------------+---------\n"    
        return print_str
        
    print_str += add_level("Token-level scores", "Token-level", scores["Token-level"])
    print_str += add_level("Scope-level scores (*SEM 2012's B-scores)", 
                           "Scope-level", scores["Scope-level"])
    print_str += add_level("Scope-level scores (*SEM 2012: exclude fp that intersect with fn)", 
                           "Scope-level", scores["Scope-level"], no_fn=True)
    
    print_str += "------------------------------------------------------------------------------------------------------------\n"
    
    for info in overall_scores:
        metric_name = " " + info + ": "
        if "%" in info:
            overall_str = "{:."+rounding+"f}\n"
            metric_name += overall_str.format(overall_scores[info])
            metric_name += "------------------------------------------------------------------------------------------------------------\n"
        else:
            metric_name+= f"{overall_scores[info]}\n"
        print_str += metric_name
    
#    print_str += "------------------------------------------------------------------------------------------------------------\n"
        
    return print_str



if __name__ == "__main__":
    argdesc = "*SEM Shared Task 2012 evaluation script"
    argparser = argparse.ArgumentParser(description=argdesc)
    argparser.add_argument("-g", "--gold", type=str, help="gold standard file path (required)")
    argparser.add_argument("-s", "--system", type=str, help="system output file path (required)")
    argparser.add_argument("-r", "--readme", action="store_true",
                           help="print a brief explanation about the evaluation output")
    argparser.add_argument("-t", "--task", type=str, default="negation",
                           help="task to be evaluated (negation/speculation), default: negation")
    argparser.add_argument("-o", "--rounding", type=int, default=2,
                           help="number of decimal points to round to, default: 2")
    gold_name = "../data/ConanDoyle-neg/reannotated/SEM-2012-SharedTask-CD-SCO-test-circle-cardboard-GOLD-reannotated.txt"
    pred_name = "../data/BioScope/Abstracts/pred/strasem2012_format/direct/STARSEM_test-parsed_neg_bio-abs_direct_0607_103656_conan.conll.pred"

    
#    args = argparser.parse_args(["-g", gold_name, 
#                                 "-s", pred_name])#,
##                                 "-o", "2"])#,
##                                 "-t", "speculation"])

    args = argparser.parse_args()
    
    if args.readme:
        readme_str = """
This evaluation script compares the output of a system versus a gold annotation and provides the following information:

--------------------------------+------+--------+------+------+------+---------------+------------+---------
                                | gold | system | tp   | fp   | fn   | precision (%) | recall (%) | F1  (%) 
--------------------------------+------+--------+------+------+------+---------------+------------+---------
------------------------------------------------------------------------------------------------------------
 Token-level scores
------------------------------------------------------------------------------------------------------------
--------------------------------+------+--------+------+------+------+---------------+------------+---------
Cue:                                   |        |      |      |      |               |            |        
Scope (full cue):                      |        |      |      |      |               |            |        
Scope (partial cue):                   |        |      |      |      |               |            |        
Scope (no cue):                        |        |      |      |      |               |            |        
Scope (binary labels):                 |        |      |      |      |               |            |        
Scope (full cue, no punct):            |        |      |      |      |               |            |        
Scope (partial cue, no punct):         |        |      |      |      |               |            |        
Scope (no cue, no punct):              |        |      |      |      |               |            |        
Scope (binary labels, no punct):       |        |      |      |      |               |            |        
Event (full cue):                      |        |      |      |      |               |            |        
Event (partial cue):                   |        |      |      |      |               |            |        
Event (no cue):                        |        |      |      |      |               |            |        
Event (binary labels):                 |        |      |      |      |               |            |        
--------------------------------+------+--------+------+------+------+---------------+------------+---------
------------------------------------------------------------------------------------------------------------
 Scope-level scores (*SEM 2012's B-scores)
------------------------------------------------------------------------------------------------------------
--------------------------------+------+--------+------+------+------+---------------+------------+---------
Cue:                                   |        |      |      |      |               |            |        
Scope (full cue):                      |        |      |      |      |               |            |        
Scope (partial cue):                   |        |      |      |      |               |            |        
Scope (no cue):                        |        |      |      |      |               |            |        
Scope (full cue, no punct):            |        |      |      |      |               |            |        
Scope (partial cue, no punct):         |        |      |      |      |               |            |        
Scope (no cue, no punct):              |        |      |      |      |               |            |        
Event (full cue):                      |        |      |      |      |               |            |        
Event (partial cue):                   |        |      |      |      |               |            |        
Event (no cue):                        |        |      |      |      |               |            |        
Full negation:                         |        |      |      |      |               |            |        
Full negation (no punct):              |        |      |      |      |               |            |        
--------------------------------+------+--------+------+------+------+---------------+------------+---------
------------------------------------------------------------------------------------------------------------
 Scope-level scores (*SEM 2012: exclude fp that intersect with fn)
------------------------------------------------------------------------------------------------------------
--------------------------------+------+--------+------+------+------+---------------+------------+---------
Cue:                                   |        |      |      |      |               |            |        
Scope (full cue):                      |        |      |      |      |               |            |        
Scope (partial cue):                   |        |      |      |      |               |            |        
Scope (full cue, no punct):            |        |      |      |      |               |            |        
Scope (partial cue, no punct):         |        |      |      |      |               |            |        
Event (full cue):                      |        |      |      |      |               |            |        
Event (partial cue):                   |        |      |      |      |               |            |        
Full negation:                         |        |      |      |      |               |            |        
Full negation (no punct):              |        |      |      |      |               |            |        
--------------------------------+------+--------+------+------+------+---------------+------------+---------
------------------------------------------------------------------------------------------------------------
 # sentences: 
 # sentences with errors: 
 % correct sentences: 
------------------------------------------------------------------------------------------------------------
 # sentences with errors (no punct): 
 % correct sentences (no punct): 
------------------------------------------------------------------------------------------------------------
 # negation sentences: 
 # negation sentences with errors: 
 % correct negation sentences: 
------------------------------------------------------------------------------------------------------------
 # negation sentences with errors (no punct): 
 % correct negation sentences (no punct): 
------------------------------------------------------------------------------------------------------------
        """
        print(readme_str)
        argparser.exit() 
    
    # handle cases when gold or system files are not provided
    elif not args.gold:
        print("Gold standard file is missing.\n")
        argparser.parse_args(["-h"])
    
    elif not args.system:
        print("System output file is missing.\n")
        argparser.parse_args(["-h"])
    
    # extract gold and system text
    with open(args.gold, encoding="utf-8") as f:
        gold_str = f.read()
    
    with open(args.system, encoding="utf-8") as f:
        system_str = f.read()    
    
    # get results and print them out
    scores, overall_scores = evaluate(gold_str, system_str, task=args.task)
    print(get_print_str(scores, overall_scores, rounding=args.rounding))
    
