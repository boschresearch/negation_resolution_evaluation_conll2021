#  Copyright (c) 2021 Robert Bosch GmbH
#  All rights reserved.
#
#  This source code is licensed under the BSD 3-Clause license found in the
#  LICENSE file in the root directory of this source tree.
#
#  Author: Elizaveta Sineva

"""
*SEM 2012 evaluation script translation from Perl to Python 3.
"""

import argparse  # take args from a command line
import re


# globals

line_number = 0

fp_cue = 0
fp_scope = 0
fp_scope_nopunc = 0
fp_scope_tokens = 0
fp_negated = 0

fn_cue = 0
fn_scope = 0
fn_scope_nopunc = 0
fn_scope_tokens = 0
fn_negated = 0

tp_cue = 0
tp_scope = 0
tp_scope_nopunc = 0
tp_scope_tokens = 0
tp_negated = 0

fp_full_negation = 0
fn_full_negation = 0
tp_full_negation = 0

fp_negated_apart = 0
tp_negated_apart = 0
fn_negated_apart = 0

fp_scope_apart = 0
tp_scope_apart = 0
fn_scope_apart = 0

cues_g = 0
scopes_g = 0
negated_g = 0

cues_p = 0
scopes_p = 0
negated_p = 0

total_scope_tokens_g = 0
total_scope_tokens_p = 0

count_sentences = 0
count_sentences_negation = 0
count_error_sentences = 0
count_error_sentences_negation = 0



def get_info_sentence(st_tmp_lineg, st_tmp_linep):
    """
    get info per sentence per line
    
    takes two strings:
        st_tmp_lineg - gold line
        st_tmp_linep - system line
    
    ### reads the lines
    ### returns strings tmp_neg_g, tmp_neg_p 
    ### where the columns with negation information (7 to end) are stored
    ### and the POS tag
    ### g stands for gold file, p for system file
    """    
    tmp_lineg = st_tmp_lineg.split("\t")
    tmp_linep = st_tmp_linep.split("\t")
    
    max_lineg = len(tmp_lineg)-1
    max_linep = len(tmp_linep)-1
    
    tmp_neg_g = ""
    tmp_neg_p = ""
    
    POS_tag = tmp_lineg[5]
    
    for i in range(7, max_lineg+1):
        # if it's the first neg col signifying there is no negation
        if i == 7 and tmp_lineg[i] == "***":
            tmp_neg_g = tmp_lineg[i]
        # if it's the first neg col and there is negation
        elif i == 7:
            # separate elements of the same instance by space
            tmp_neg_g = tmp_lineg[i] + " "
        # if it's the last col
        elif i == max_lineg:
            # don't add a space
            tmp_neg_g += tmp_lineg[i]
        # if it's the end of one instance
        elif i % 3 == 0:
            # separate different instances by tab
            tmp_neg_g += tmp_lineg[i] + "\t"
        else:
            # separate elements of the same instance by space
            tmp_neg_g += tmp_lineg[i] + " "
        
    for i in range(7, max_linep+1):
        # if it's the first neg col signifying there is no negation
        if i == 7 and tmp_linep[i] == "***":
            tmp_neg_p = tmp_linep[i]
        # if it's the first neg col and there is negation
        elif i == 7:
            # separate elements of the same instance by space
            tmp_neg_p = tmp_linep[i] + " "
        # if it's the last col
        elif i == max_linep:
            # don't add a space
            tmp_neg_p += tmp_linep[i]
        # if it's the end of one instance
        elif i % 3 == 0:
            # separate different instances by tab
            tmp_neg_p += tmp_linep[i] + "\t"
        else:
            # separate elements of the same instance by space
            tmp_neg_p += tmp_linep[i] + " "
        
    return tmp_neg_g, tmp_neg_p, POS_tag



def process_sentence(neg_cols_g, neg_cols_p, POS, starsem_exact=False):
    """    
    process sentence
    
    ### processes information in arrays neg_cols_g, neg_cols_p
    ### the arrays contain as main elements as tokens in sentence
    ### each element of the array contains information per negation separated by tabs, 
    ### and information of each negation separated by blank space
    ### _ _ _\t_ _ _
    
    ### POS is the list of POS tags in the sentence
    
    ### Information is stored in the arrays below
    ### They have as many elements as negations there are in the sentence
    
    ### arrays of arrays
    
    ### neg_words_g 
    ### scope_words_g 
    ### scope_words_nopunc_g 
    ### negated_words_g 
    
    ### neg_tokens_g 
    ### scope_tokens_g 
    ### scope_tokens_nopunc_g
    ### negated_tokens_g 
    
    ### neg_words_p 
    ### scope_words_p 
    ### scope_words_nopunc_p
    ### negated_words_p 
    
    ### neg_tokens_p 
    ### scope_tokens_p 
    ### scope_tokens_nopunc_p 
    ### negated_tokens_p 
    
    ### arrays
    
    ### first_token_negs_g 
    ### first_token_negs_p 
    
    ### first_token_negated_g 
    ### first_token_negated_p 
    
    ### first_token_scope_g 
    ### first_token_scope_p
    """
    neg_words_g = []
    scope_words_g = []
    scope_words_nopunc_g = []
    negated_words_g = []
    
    neg_tokens_g = []
    neg_found_g = []
    scope_tokens_g = []
    scope_tokens_nopunc_g = []
    negated_tokens_g = []
    
    neg_words_p = []
    scope_words_p = []
    scope_words_nopunc_p = []
    negated_words_p = []
    
    neg_tokens_p = []
    neg_found_p = []
    scope_tokens_p = []
    scope_tokens_nopunc_p = []
    negated_tokens_p = []
    
    first_token_negs_g = []
    first_token_negs_p = []
    
    first_token_negated_g = []
    first_token_negated_p = []
    
    first_token_scope_g = []
    first_token_scope_p = []
    
    negated_found_g = []
    negated_found_p = []
    
    scope_found_g = []
    scope_found_p = []
    
    zero_negs_p = ""
    zero_negs_g = ""

    tmp_neg_cols_g = []
    neg_by_neg_cols_g = []
    
    tmp_neg_cols_p = []
    neg_by_neg_cols_p = []

    #############################
    ### 1. Process gold sentence
    #############################
    
    global count_sentences, count_sentences_negation
    global total_scope_tokens_g, cues_g, negated_g, scopes_g

#    count_sentences += 1    
    
    max_negs_g = 0
    max_negs_p = 0
        
    ### no negations in gold
    if neg_cols_g[0] == "***":
        zero_negs_g = "yes"
    
    ### negations in gold
    else:
        count_sentences_negation += 1
        zero_negs_g = "no"
        
        #### process gold file
        
        max_neg_cols_g = len(neg_cols_g)  # number of tokens in gold sentence
        
        # i count line number in gold sentence
        for i in range(max_neg_cols_g):
            # the gold negation columns
            tmp_neg_cols_g = neg_cols_g[i].split("\t")
            max_negs_g = len(tmp_neg_cols_g)  # number of negation instances
                        
            # z counts index of negation per line
            for z in range(max_negs_g):
                neg_by_neg_cols_g = tmp_neg_cols_g[z].split(" ")
                
                if i == 0:
                    # add necessary lists to create lists of lists
                    neg_words_g.append([])           # cue words
                    neg_tokens_g.append([])          # cue tokens
                    scope_words_g.append([])         # scope words
                    scope_tokens_g.append([])        # scope tokens
                    scope_words_nopunc_g.append([])  # scope words (no punct)
                    scope_tokens_nopunc_g.append([]) # scope tokens (no punct)
                    negated_words_g.append([])       # event words
                    negated_tokens_g.append([])      # event tokens

                    # put placeholders
                    neg_found_g.append(0)
                    scope_found_g.append(0)
                    negated_found_g.append(0)
                
                # if the current token is the cue
                if neg_by_neg_cols_g[0] != "_":
                    # save the cue word / affix
                    neg_words_g[z].append(neg_by_neg_cols_g[0])
                    # save the token idx
                    neg_tokens_g[z].append(i)
                
                # if the current token is the scope
                if neg_by_neg_cols_g[1] != "_":
                    # avoid punctuation
                    if (re.search("\w", POS[i]) and 
                        POS[i] != "-LRB-" and
                        POS[i] != "-RRB-"):
                        
                        # cases with a dot in the end like Mr. / Mrs. / Dr.
                        dot_regex = re.search("^(\w+)\.", neg_by_neg_cols_g[1])
                        if dot_regex:
                            # only keep the part without a dot
                            tmp_word = dot_regex.group(1)
                        else:
                            tmp_word = neg_by_neg_cols_g[1]
                        
                        # save the scope word
                        scope_words_g[z].append(tmp_word)
                        # save the token idx
                        scope_tokens_g[z].append(i)
                        
                        # used to be two different if statements? line 537
                        # save the scope word (no punct)
                        scope_words_nopunc_g[z].append(tmp_word)
                        # save the token idx (no punct)
                        scope_tokens_nopunc_g[z].append(i)
                        
                        total_scope_tokens_g += 1

                # if the current token is the event
                if neg_by_neg_cols_g[2] != "_":
                    # save the event word
                    negated_words_g[z].append(neg_by_neg_cols_g[2])
                    negated_tokens_g[z].append(i)
                

                
        
    for z in range(max_negs_g):
        # handle cues
        if neg_tokens_g[z]:
            first_token_negs_g.append(neg_tokens_g[z][0])
            cues_g += 1
        else:
            first_token_negs_g.append("_")
        
        # handle events
        if negated_tokens_g[z]:
            first_token_negated_g.append(negated_tokens_g[z][0])
            negated_g += 1
        else:
            first_token_negated_g.append("_")
        
        # handle scopes
        if scope_tokens_g[z]:
            first_token_scope_g.append(scope_tokens_g[z][0])
            scopes_g += 1
        else:
            first_token_scope_g.append("_")


    #############################
    ### 2. Process system sentence
    #############################
    
    global total_scope_tokens_p, cues_p, negated_p, scopes_p
    
    ### no negations in system
    if neg_cols_p[0] == "***":
        zero_negs_p = "yes"
    
    ### negations in system
    else:
        zero_negs_p = "no"
        
        #### process system file
        
        max_neg_cols_p = len(neg_cols_p)-1
        
        # i count line number in sentence
        for i in range(max_neg_cols_p+1):
            tmp_neg_cols_p = neg_cols_p[i].split("\t")
            max_negs_p = len(tmp_neg_cols_p)
            
            # z counts index of negation per line
            for z in range(max_negs_p):
                neg_by_neg_cols_p = tmp_neg_cols_p[z].split(" ")
                
                if i == 0:
                    # add necesscary lists to create lists of lists
                    neg_words_p.append([])           # cue words
                    neg_tokens_p.append([])          # cue tokens
                    scope_words_p.append([])         # scope words
                    scope_tokens_p.append([])        # scope tokens
                    scope_words_nopunc_p.append([])  # scope words (no punct)
                    scope_tokens_nopunc_p.append([]) # scope tokens (no punct)
                    negated_words_p.append([])       # event words
                    negated_tokens_p.append([])      # event tokens
 
                    # put placeholders
                    neg_found_p.append(0)
                    scope_found_p.append(0)
                    negated_found_p.append(0)

                # if the current token is the cue
                if neg_by_neg_cols_p[0] != "_":
                    # save the cue word / affix
                    neg_words_p[z].append(neg_by_neg_cols_p[0])
                    # save the token idx
                    neg_tokens_p[z].append(i)
                
                # if the current token is the scope
                if neg_by_neg_cols_p[1] != "_":
                    # avoid punctuation
                    if (re.search("\w", POS[i]) and 
                        POS[i] != "-LRB-" and
                        POS[i] != "-RRB-"):
                        
                        # cases like with a dot in the end like Mr. / Mrs. /Dr.
                        dot_regex = re.search("^(\w+)\.", neg_by_neg_cols_p[1])
                        if dot_regex:
                            # only keep the part without a dot
                            tmp_word = dot_regex.group(1)
                        else:
                            tmp_word = neg_by_neg_cols_p[1]
                        
                        # save the scope word
                        scope_words_p[z].append(tmp_word)
                        # save the token idx
                        scope_tokens_p[z].append(i)
                        
                        # used to be two different if statements? line 537
                        # save the scope word (no punct)
                        scope_words_nopunc_p[z].append(tmp_word)
                        # save the token idx (no punct)
                        scope_tokens_nopunc_p[z].append(i)
                        
                        total_scope_tokens_p += 1

                # if the current token is the event
                if neg_by_neg_cols_p[2] != "_":
                    # save the event word
                    negated_words_p[z].append(neg_by_neg_cols_p[2])
                    negated_tokens_p[z].append(i)
    
    
    for z in range(max_negs_p):
        # make sure a cue is predicted for the scope
        assert_msg = "Sentence before line " + str(line_number) + " lacks at least a negation cue."
        assert_msg += "The columns for negation where found without cue."
        assert_msg += "Fix this before proceedings to evaluate."
        assert neg_words_p[z], assert_msg
        
        # handle cues
        if neg_tokens_p[z]:
            first_token_negs_p.append(neg_tokens_p[z][0])
            cues_p += 1
        else:
            first_token_negs_p.append("_")
        
        # handle events
        if negated_tokens_p[z]:
            first_token_negated_p.append(negated_tokens_p[z][0])
            negated_p += 1
        else:
            first_token_negated_p.append("_")
        
        # handle scopes
        if scope_tokens_p[z]:
            first_token_scope_p.append(scope_tokens_p[z][0])
            scopes_p += 1
        else:
            first_token_scope_p.append("_")
            

    """
    update counts for eval

    ### Counting number of tp, fp, fn for:
    ### cue
    ### scope (tp requires that cue is correct)
    ### negated (tp requires that cue is correct)
    ### negated apart (calculated apart from cue and scope, tp does not require correct cue)
    ### for cue, scope and negated to be correct, both, the tokens and the words or part of words have to be
    ### correclty identified, else they count as fn
    ### example 1:
    ### gold: cue is "un" and  scope is "decided"
    ### if system identifies "und" as cue and "decided" as scope, it will be counted as false negative for cue, 
    ### and scope will also be false negative, because cue is incorrect;
    ### if system identifies "un" as cue and "undecided" as scope, cue will count as true positive
    ### and scope as false negative;
    ### example 2:
    ### gold: cue is "un" and  scope is "decided"
    ### system doesn't have a negation.
    ### cue and scope will be false negatives
    ### example 3:
    ### gold doesn't have a negation.
    ### system finds a negation with its scope, then cue and scope will count as false positives
    ### example 4:
    ### gold: cue is "never", scope is "Holmes entered in the house"
    ### system: cue is "never", scope is "entered in the house"
    ### cue will be true positive, but scope will be false negative because not all tokens have been found by system 
    
    
    ### false negatives are produced either by the system not identifying a negation and its elements present in gold
    ### or by identifying them incorrectly: not all tokens have been identified or the word forms are incorrect    
    """
    global fp_cue, fp_scope, fp_scope_tokens, fp_negated
    global fn_cue, fn_scope, fn_scope_tokens, fn_negated
    global tp_cue, tp_scope, tp_scope_tokens, tp_negated
    global fp_full_negation, fn_full_negation, tp_full_negation
    
    # handle gold cues number
    if first_token_negs_g:
        max_negs_g = len(first_token_negs_g)
    else:
        max_negs_g = -1

    # handle pred cues number
    if first_token_negs_p:
        max_negs_p = len(first_token_negs_p)
    else:
        max_negs_p = -1
    
    error_found = 0

    ####################################################
    ## gold has negations in sentence, system has
    ## not found negations in sentence
    ####################################################
    if zero_negs_g == "no" and zero_negs_p == "yes":
        error_found = 1
        
        for i in range(max_negs_g):
            # cue fn (scope-level)
            if neg_tokens_g[i]:
                fn_cue += 1
            
            # scope fn
            if scope_tokens_g[i]:
                # scope-level
                fn_scope += 1
                # token-level
                for z in range(len(scope_tokens_g[i])):
                    fn_scope_tokens += 1
            
            # event fn (scope-level)
            if negated_tokens_g[i]:
                fn_negated += 1
            
            # full negation fn
            fn_full_negation += 1
    
    
    ####################################################
    ## gold and system have negations in sentence
    ####################################################    
    elif zero_negs_g == "no" and zero_negs_p == "no":
        
        ## i iterates over negations in gold
        for i in range(max_negs_g):

            ## udpate variables with the string of negation cue, scope
            ## and negated in gold
            
            # gold cue words
            st_neg_words_g = " ".join(neg_words_g[i])
                
            # gold scope words
            st_scope_words_g = " ".join(scope_words_g[i])

            # gold event words
            st_negated_words_g = " ".join(negated_words_g[i])

            # gold cue tokens
            st_neg_tokens_g = " ".join(str(num) for num in neg_tokens_g[i])
            
            # gold scope tokens
            st_scope_tokens_g = " ".join(str(num) for num in scope_tokens_g[i])

            # gold event tokens
            st_negated_tokens_g = " ".join(str(num) for num in negated_tokens_g[i])


            # get the number of negation tokens in gold
            max_neg_tokens_g = len(neg_tokens_g[i])
            
            
            ## z iterates over negations in system
            for z in range(max_negs_p):

                ## udpate variables with the string of negation cue, scope and negated
                ## in system

                # pred cue words
                st_neg_words_p = " ".join(neg_words_p[z])

                # pred scope words
                st_scope_words_p = " ".join(scope_words_p[z])

                # pred event words
                st_negated_words_p = " ".join(negated_words_p[z])

                # pred cue tokens
                st_neg_tokens_p = " ".join(str(num) for num in neg_tokens_p[z])

                # pred scope tokens
                st_scope_tokens_p = " ".join(str(num) for num in scope_tokens_p[z])

                # pred event tokens
                st_negated_tokens_p = " ".join(str(num) for num in negated_tokens_p[z])
                
                
                # get the number of negation tokens in system
                max_neg_tokens_p = len(neg_tokens_p[z])
                
                found = 0
                
                # look for matching negation cues in gold and system
                for y in range(max_neg_tokens_g):
                    for x in range(max_neg_tokens_p):
                        if (neg_tokens_g[i][y] == neg_tokens_p[z][x] and
                            neg_found_p[z] == 0 and
                            neg_found_g[i] == 0):
                            found = 1
                            neg_found_p[z] = 1
                            neg_found_g[i] = 1
                            break
                
                
                ## if a negation in gold is also found in system
                if found == 1:
                    
                    ## update count for scope tokens (scope-level)
                    max_scope_tokens_g = len(scope_tokens_g[i])-1
                    max_scope_tokens_p = len(scope_tokens_p[z])-1
                    
                    ## iterate over gold tokens to find tp and fn
                    for y in range(max_scope_tokens_g+1):
                        found_scope_token = 0
                        for x in range(max_scope_tokens_p+1):
                            if scope_tokens_g[i][y] == scope_tokens_p[z][x]:
                                if scope_words_g[i][y] == scope_words_p[z][x]:
                                    found_scope_token = 1
                                break
                        
                        # scope (scope-level)
                        if found_scope_token == 1:
                            tp_scope_tokens += 1
                        else:
                            fn_scope_tokens += 1
                
                    ## iterate over system tokens to find fp
                    for x in range(max_scope_tokens_p+1):
                        found_scope_token = 0
                        for y in range(max_scope_tokens_g+1):
                            if scope_tokens_g[i][y] == scope_tokens_p[z][x]:
                                if scope_words_g[i][y] == scope_words_p[z][x]:
                                    found_scope_token = 1
                                break
                        
                        # scope (scope-level)
                        if found_scope_token == 0:
                            fp_scope_tokens += 1
                    
                    ## check whether full negation is correct
                    if (st_neg_tokens_g != "" and 
                        st_neg_tokens_g == st_neg_tokens_p  and 
                        st_neg_words_g == st_neg_words_p and 
                        st_scope_tokens_g == st_scope_tokens_p and
                        st_scope_words_g == st_scope_words_p and
                        st_negated_tokens_g == st_negated_tokens_p and
                        st_negated_words_g == st_negated_words_p):
                        tp_full_negation += 1
                    else:
                        fn_full_negation += 1
                        error_found = 1
                    
                    ## gold cue is correctly identified: 
                    ## both the token number and the word or part of a word
                    if (st_neg_tokens_g != "" and
                        st_neg_tokens_g == st_neg_tokens_p and
                        st_neg_words_g == st_neg_words_p):
                        tp_cue += 1
                        
                        ########### scope (scope-level, cue match)
                        # if no scope was marked for this cue in gold, 
                        # and system marks it, then it is fp
                        if st_scope_tokens_g == "" and st_scope_tokens_p != "":
                            fp_scope += 1
                            error_found = 1
                        
                        ## scope is correctly identified: 
                        ## both the token numbers and the words or parts of words
                        ## cue needs to have been correctly identified 
                        ## for scope to be counted as correct
                        elif (st_scope_tokens_g != "" and
                              st_scope_tokens_g == st_scope_tokens_p and
                              st_scope_words_g == st_scope_words_p):
                            tp_scope += 1
                        
                        ## gold marks a scope, in system either the tokens 
                        ## or words are incorrect
                        elif (st_scope_tokens_g != "" and 
                              (st_scope_tokens_p != st_scope_tokens_g or
                               st_scope_words_p != st_scope_words_g)):
                            fn_scope += 1
                            error_found = 1
                        
                        ########### negated [event] (scope-level)
                        # if no negated was marked for this cue in gold, 
                        # and system marks it, then it is fp
                        if (st_negated_tokens_g == "" and 
                            st_negated_tokens_p != ""):
                            fp_negated += 1
                            error_found = 1
                        
                        ## negated is correctly identified: 
                        ## both the token numbers and the words or parts of words
                        ## cue needs to have been correctly identified 
                        ## for negated to be counted as correct
                        elif (st_negated_tokens_g != "" and
                              st_negated_tokens_g == st_negated_tokens_p and
                              st_negated_words_g == st_negated_words_p):
                            tp_negated += 1
                        
                        ## gold marks a negated, in system either the tokens 
                        ## or words are incorrect
                        elif (st_negated_tokens_g != "" and
                              (st_negated_tokens_p != st_negated_tokens_g or
                               st_negated_words_p != st_negated_words_g)):
                            fn_negated += 1
                            error_found = 1
                    
                    ### well identified token number of negation,
                    ### but not well identified the word;
                    ### for example, in "unbrushed", "un" is the negation,
                    ### but not "unbrushed"
                    elif (st_neg_tokens_g != "" and
                          (st_neg_tokens_g != st_neg_tokens_p or
                           st_neg_words_g != st_neg_words_p)):
                        fn_cue += 1
                        
                        # scope (scope-level)
                        if st_scope_tokens_g != "":
                            fn_scope += 1
                        
                        # event (scope-level)
                        if st_negated_tokens_g != "":
                            fn_negated += 1
                        
                        error_found = 1
                    
                    ## gold negation found in system negations search stops
                    break
                
                
                ## iteration on system negations has finished and gold negation has not been found 
                elif z == max_negs_p-1:
                    error_found = 1
                    
                    # cues (scope-level)
                    if st_neg_tokens_g != "":
                        fn_cue += 1
                    
                    # scope
                    if st_scope_tokens_g != "":
                        fn_scope += 1 # scope-level
                        for y in range(len(scope_tokens_g[i])):
                            fn_scope_tokens += 1 # token-level
                    
                    # event (scope-level)
                    if st_negated_tokens_g != "":
                        fn_negated += 1
                    
                    fn_full_negation += 1
        
        
        ### iterate over negations in system if they are not found in gold, 
        ### then count false positives
        
        ## z iterates over negations in system
        for z in range(max_negs_p):

            ## udpate variables with the string of the negation cue 
            ## in system
            
            # cue words
            st_neg_words_p = " ".join(neg_words_p[z])
            
            # scope words
            st_scope_words_p = " ".join(scope_words_p[z])

            # event words
            st_negated_words_p = " ".join(negated_words_p[z])
            
            # cue tokens
            st_neg_tokens_p = " ".join(str(num) for num in neg_tokens_p[z])
            
            # scope tokens
            st_scope_tokens_p = " ".join(str(num) for num in scope_tokens_p[z])

            # event tokens
            st_negated_tokens_p = " ".join(str(num) for num in negated_tokens_p[z])

            
            max_neg_tokens_p = len(neg_tokens_p[z])
            
            
            ## i iterates over negations in gold
            for i in range(max_negs_g):
                
                max_neg_tokens_g = len(neg_tokens_g[i])
                
                found = 0                    
                
                # find matching negation instances in gold and system
                for x in range(max_neg_tokens_p):
                    for y in range(max_neg_tokens_g):
                        if (neg_tokens_g[i][y] == neg_tokens_p[z][x] and
                            neg_found_p[z] == 1):
                            found = 1
                            break
                
                ## negation in system is found in gold
                ## this has been treated above
                if found == 1:
                    break
                
                ## negation in system is not found in gold
                elif i == max_negs_g-1:
                    error_found = 1
                
                    # cues (scope-level)
                    if st_neg_tokens_p != "":
                        fp_cue += 1
                    
                    # scope
                    if st_scope_tokens_p != "":
                        fp_scope += 1 # scope-level
                        for y in range(len(scope_tokens_p[z])):
                            fp_scope_tokens += 1 # token-level
                    
                    # event (scope-level)
                    if st_negated_tokens_p != "":
                        fp_negated += 1
                    
                    fp_full_negation += 1                
    
    
    ####################################################
    ##  gold doesn't have negations and system has
    ####################################################
    elif zero_negs_g == "yes" and zero_negs_p == "no":
        error_found = 1
        
        for z in range(max_negs_p):
            # cue fp (scope-level)
            if neg_tokens_p[z]:
                fp_cue += 1
            
            # scope fp
            if scope_tokens_p[z]:
                # scope-level
                fp_scope += 1
                # token-level
                for y in range(len(scope_tokens_p[z])):
                    fp_scope_tokens += 1
            
            # event fp (scope-level)
            if negated_tokens_p[z]:
                fp_negated += 1
            
            # full negation fp
            fp_full_negation += 1
    
    
    
    #######################################################
    ###### update counts for negated apart from negation cues
    #######################################################
    global fp_negated_apart, fn_negated_apart, tp_negated_apart
    

    ####################################################
    ## gold has negations in sentence, system not
    ####################################################
    if zero_negs_g == "no" and zero_negs_p == "yes":
        for i in range(max_negs_g):
            if negated_tokens_g[i]:
                fn_negated_apart += 1  # original line 1684


    ####################################################
    ## gold and system have negations in sentence
    ####################################################
    elif zero_negs_g == "no" and zero_negs_p == "no":
        
        ### iterate over negations in gold
        
        ## i iterates over negations in gold
        for i in range(max_negs_g):

            ## update string of negated in gold

            # gold event words
            st_negated_words_g = " ".join(negated_words_g[i])

            # gold event tokens
            st_negated_tokens_g = " ".join(str(num) for num in negated_tokens_g[i])
            

            max_negated_tokens_g = len(negated_tokens_g[i])
            
            ## z iterates over negations in system
            for z in range(max_negs_p):
                
                ## update string of negated in system

                # pred event words
                st_negated_words_p = " ".join(negated_words_p[z])

                # pred event tokens
                st_negated_tokens_p = " ".join(str(num) for num in negated_tokens_p[z])

                
                max_negated_tokens_p = len(negated_tokens_p[z])
                max_neg_tokens_p = len(neg_tokens_p[z])
                
                found = 0 
                
                # code for events ***dependent*** on [partial] cue match (not in the original)
#                for y in range(max_neg_tokens_g):
#                    for x in range(max_neg_tokens_p):
#                        if (neg_tokens_g[i][y] == neg_tokens_p[z][x] and
#                            negated_found_p[z] == 0 and
#                            negated_found_g[i] == 0):
#                            found = 1
#                            negated_found_p[z] = 1
#                            negated_found_g[i] = 1
#                            break
                
                # iterate over events
                # find the ones that match (regardless of the cue)
                for y in range(max_negated_tokens_g):
                    for x in range(max_negated_tokens_p):
                        if (negated_tokens_g[i][y] == negated_tokens_p[z][x] and
                            negated_found_p[z] == 0 and
                            negated_found_g[i] == 0):
                            found = 1
                            negated_found_p[z] = 1
                            negated_found_g[i] = 1
                            break        
                
                
                ## if a negation in gold is also found in system
                if found == 1:
                    ## negated is correctly identified
                    ## both token number and word or part of word 
                    ## have to be correctly identified
                    if (st_negated_tokens_g != "" and 
                        st_negated_tokens_g == st_negated_tokens_p and 
                        st_negated_words_g == st_negated_words_p):
                        tp_negated_apart += 1
                        break    
                    
                    ## if negated is not correctly identified
                    elif (st_negated_tokens_g != "" and 
                          (st_negated_tokens_p != st_negated_tokens_g or 
                           st_negated_words_p != st_negated_words_g)):
                        
                        if starsem_exact:
                            # the loop in this if statement was omitted due to a bug
                            # --> did not add fn to fn_negated_apart whenever there 
                            # was a gold-pred match, but not full (not all words / tokens matched)
                            continue
                        
                        ## we need to check whether we are comparing 
                        ## negated elements of the same negation
                        found = 0
                        
                        # this loop is omitted in original due to a bug
                        # original iterated over range(max_negated_words_g)
                        # where max_negated_words_g was not [re]defined (alw set to -1)
                        # the loop looks checks if there is a word match and not only
                        # a token is match (affixational cues can have a part of a word
                        # as the event, and be events themselves, e.g. event 1: unlike,
                        # event 2: like (where cue is un), where the token id is the same)
                        for y in range(max_negated_tokens_g):  # original line 1777
                            for x in range(max_negated_tokens_p):
                                if negated_words_g[i][y] == negated_words_p[z][x]:
                                    found = 1
                                    break
                        
                        # fn if gold did match a prediction, but not fully
                        if found == 1:
                            fn_negated_apart += 1  # original line 1790
                            break
                        
                        # addition: set the instances to NOT found
                        else:
                            negated_found_p[z] = 0
                            negated_found_g[i] = 0                            
                        
            
                elif z == max_negs_p-1:
                    if st_negated_tokens_g != "":
                        # fn if gold didn't match any prediction
                        fn_negated_apart += 1 # original line 1800

    
        ### iterate over negations in system 
        ### if they are not found in gold, then count false positives

        ## z iterates over negations in system
        for z in range(max_negs_p):
            
            ## update string of negated in system
            
            # pred event words
            st_negated_words_p = " ".join(negated_words_p[z])

            # pred event tokens
            st_negated_tokens_p = " ".join(str(num) for num in negated_tokens_p[z])

            
            max_negated_tokens_p = len(negated_tokens_p[z])
            max_neg_tokens_p = len(neg_tokens_p[z])
            
            ## i iterates over negations in gold
            for i in range(max_negs_g):
                
                max_negated_tokens_g = len(negated_tokens_g[i])                
                max_neg_tokens_g = len(neg_tokens_g[i])
                
                found = 0

                # code for events ***dependent*** on [partial] cue match (not in the original)
#                for x in range(max_neg_tokens_p):
#                    for y in range(max_neg_tokens_g):
#                        if (neg_tokens_g[i][y] == neg_tokens_p[z][x] and
#                            negated_found_p[z] == 1):
#                            found = 1
#                            break
                
                for x in range(max_negated_tokens_p):
                    for y in range(max_negated_tokens_g):
                        if (negated_tokens_g[i][y] == negated_tokens_p[z][x] and
                            negated_found_p[z] == 1):
                            found = 1
                            break

                ## if a negation in gold is also found in system
                if found == 1:
                    break
                
                ## negation in system is not found in gold
                elif i == max_negs_g-1:
                    if st_negated_tokens_p != "":
                        fp_negated_apart += 1


    ####################################################
    ##  gold doesn't have negations and system has
    ####################################################
    elif zero_negs_g == "yes" and zero_negs_p == "no":
        for z in range(max_negs_p):
            if negated_tokens_p[z]:
                fp_negated_apart += 1



    #######################################################
    ###### update counts for scope apart from negation cues
    #######################################################
    global fp_scope_apart, fn_scope_apart, tp_scope_apart
    global fp_scope_nopunc, fn_scope_nopunc, tp_scope_nopunc
    
    ####################################################
    ## gold has negations in sentence, system has
    ## not found negations in sentence
    ####################################################
    if zero_negs_g == "no" and zero_negs_p == "yes":
        for i in range(max_negs_g):
            if scope_tokens_g[i]:
                fn_scope_apart += 1

            if scope_tokens_nopunc_g[i]:
                fn_scope_nopunc += 1
    
    
    ####################################################
    ## gold and system have negations in sentence
    ####################################################
    elif zero_negs_g == "no" and zero_negs_p == "no":
        
        ## i iterates over negations in gold
        for i in range(max_negs_g):

            ## udpate variables with the string of negation cue,
            ## scope and negated in gold

            # gold cue words
            st_neg_words_g = " ".join(neg_words_g[i])

            # gold scope words
            st_scope_words_g = " ".join(scope_words_g[i])

            # gold scope words (no punct)
            st_scope_words_nopunc_g = " ".join(scope_words_nopunc_g[i])

            # gold cue tokens
            st_neg_tokens_g = " ".join(str(num) for num in neg_tokens_g[i])

            # gold scope tokens
            st_scope_tokens_g = " ".join(str(num) for num in scope_tokens_g[i])

            # gold scope words (no punct)
            st_scope_tokens_nopunc_g = " ".join(str(num) for num in scope_tokens_nopunc_g[i])
            
            max_neg_tokens_g = len(neg_tokens_g[i])
            
            
            ## z iterates over negations in system
            for z in range(max_negs_p):
                
                ## udpate variables with the string of negation cue, scope and negated
                ## in system

                # pred scope words
                st_scope_words_p = " ".join(scope_words_p[z])

                # pred scope words (no punct)
                st_scope_words_nopunc_p = " ".join(scope_words_nopunc_p[z])

                # pred scope tokens
                st_scope_tokens_p = " ".join(str(num) for num in scope_tokens_p[z])

                # pred scope tokens (no punct)
                st_scope_tokens_nopunc_p = " ".join(str(num) for num in scope_tokens_nopunc_p[z])
                
                
                max_neg_tokens_p = len(neg_tokens_p[z])
                
                found = 0
                
                # look for matching negation cues in gold and system
                # check if negation is found in both system and gold
                for y in range(max_neg_tokens_g):
                    for x in range(max_neg_tokens_p):
                        if (neg_tokens_g[i][y] == neg_tokens_p[z][x] and
                            scope_found_p[z] == 0 and
                            scope_found_g[i] == 0):
                            found = 1
                            scope_found_p[z] = 1
                            scope_found_g[i] = 1
                            break
                
                ## if a negation in gold is also found in system
                if found == 1:
                    
                    ########### scope apart #####################
                    # if no scope was marked for this cue in gold,
                    # and system marks it, then it is fp
                    if st_scope_tokens_g == "" and st_scope_tokens_p != "":
                        fp_scope_apart += 1
                    
                    ## scope is correctly identified: 
                    ## both the token numbers and the words or parts of words
                    ## cue needs to have been correctly identified 
                    ## for scope to be counted as correct
                    elif (st_scope_tokens_g != "" and 
                          st_scope_tokens_g == st_scope_tokens_p and 
                          st_scope_words_g == st_scope_words_p):
                        tp_scope_apart += 1
        
                    ## gold marks a scope, in system either the tokens 
                    ## or words are incorrect
                    elif (st_scope_tokens_g != "" and 
                          (st_scope_tokens_p != st_scope_tokens_g or 
                           st_scope_words_p != st_scope_words_g)):
                        fn_scope_apart += 1
                    
                    
                    ########### scope no punctuation #####################
                    # if no scope was marked for this cue in gold,
                    # and system marks it, then it is fp
                    if (st_scope_tokens_nopunc_g == "" and 
                        st_scope_tokens_nopunc_p != ""):
                        fp_scope_nopunc += 1
                    
                    ## scope is correctly identified: boh the token numbers and the words or parts of words
                    ## cue needs to have been correctly identified for scope to be counted as correct
                    elif (st_scope_tokens_nopunc_g != "" and 
                          st_scope_tokens_nopunc_g == st_scope_tokens_nopunc_p and 
                          st_scope_words_nopunc_g == st_scope_words_nopunc_p):
                        tp_scope_nopunc += 1
                    
                    ## gold marks a scope, in system either the tokens or words are incorrect
                    elif (st_scope_tokens_nopunc_g != "" and 
                          (st_scope_tokens_nopunc_p != st_scope_tokens_nopunc_g or 
                           st_scope_words_nopunc_p != st_scope_words_nopunc_g)):
                        fn_scope_nopunc += 1
                    
                    
                    ## gold negation found in system negations search 
                    ## in system negations stops
                    break
                
                
                ## iteration on system negations has finished
                ## and gold negation has not been found 
                elif z == max_negs_p-1:
                    if st_scope_tokens_g != "":
                        fn_scope_apart += 1
                    if st_scope_tokens_nopunc_g!="":
                        fn_scope_nopunc += 1
        
        
        ### iterate over negations in system if they are not found in gold,
        ## then count false positives
        
        ## z iterates over negations in system
        for z in range(max_negs_p): 

            ## udpate variables with the string of the negation scope
            ## in system

            # pred scope tokens
            st_scope_tokens_p = " ".join(str(num) for num in scope_tokens_p[z])

            # pred scope tokens (no punct)
            st_scope_tokens_nopunc_p = " ".join(str(num) for num in scope_tokens_nopunc_p[z])
            
            
            max_neg_tokens_p = len(neg_tokens_p[z])
            
            ## i iterates over negations in gold
            for i in range(max_negs_g):

                max_neg_tokens_g = len(neg_tokens_g[i])
                                
                found = 0

                for x in range(max_neg_tokens_p):
                    for y in range(max_neg_tokens_g):
                        if (neg_tokens_g[i][y] == neg_tokens_p[z][x] and
                            scope_found_p[z] == 1):
                            found = 1
                            break
                
                ## negation in system is found in gold
                ## this has been treated above 
                if found == 1:
                    break
                
                ## negation in system is not found in gold
                elif i == max_negs_g-1:
                    if st_scope_tokens_p != "":
                        fp_scope_apart += 1
                    if st_scope_tokens_nopunc_p != "":
                        fp_scope_nopunc += 1
    
    
    ####################################################
    ##  gold doesn't have negations and system has
    ####################################################
    elif zero_negs_g == "yes" and zero_negs_p =="no":
        for z in range(max_negs_p):
            if scope_tokens_p[z]:
                fp_scope_apart += 1
            if scope_tokens_nopunc_p[z]:
                fp_scope_nopunc += 1


    # count error sentences
    global count_error_sentences, count_error_sentences_negation
    
    if error_found == 1:
        count_error_sentences += 1
                 
        if zero_negs_g == "no":
            count_error_sentences_negation += 1




def main(gold, system, starsem_exact=False):
    """
    This version differs from the original script in the following:
        - original omits some FNs for negated event that had a partial match
        - original counts as FN cases with one token being an event twice and 
          written in prediction in a diffferent order than in gold 
          (e.g. event 1: unlike, event 2: like (where the cue is un))
        - original outputs TP of Scope (cue match) when reporting results 
          for Scope (no cue match)
        - original rounds precision and recall before calculating f1
    
    To obtain exactly the same output as the original, set starsem_exact to True.
    """
    
    #######################################################################
    ##### 1. check that GOLD file and SYSTEM file have the same sentences
    ##### evaluation does not proceed if sentences are different
    ##### 2.1 Check that SYSTEM file annotates sentences without negation consistently 
    ##### All tokens in column 7 need to have "***"
    ##### 2.2 Check that all tokens of the same sentence have the same
    ##### number of columns and that the number of columns is 
    ##### either 7 (starting by 0) or, if larger, divisible by 3
    ######################################################################
    
    global count_sentences, line_number
    
    with open(gold) as f:
        # split into sentences
        GOLD = f.read().strip().split("\n\n")
    with open(system) as f:
        # split into sentences
        SYSTEM = f.read().strip().split("\n\n")

    col7_p = []
    max_tmp_linep = -1
    
    count_sentences = len(GOLD)
    current_sent_idx = 0
    
    while current_sent_idx < count_sentences:
        
        # add empty line to have the required format for the given code
        gold_sent = GOLD[current_sent_idx].split("\n") + [""]
        system_sent = SYSTEM[current_sent_idx].split("\n") + [""]
        
        current_sent_idx += 1
        
        for idx in range(len(gold_sent)):            
            st_tmp_lineg = gold_sent[idx].strip()
            st_tmp_linep = system_sent[idx].strip()

            line_number += 1
                    
            # if the sentence has ended
            if st_tmp_lineg == "":
                # 1. check if the sentence in SYSTEM has ended as well
                assert_msg = "Line " + str(line_number)
                assert_msg += ": Blank line in GOLD file is not blank line in SYSTEM file"
                assert st_tmp_linep == "", assert_msg
                
                # 2. check if all lines of the sentence without negation in SYSTEM
                # have *** in negation columns
                max_col7_p = len(col7_p)
                for i in range(0, max_col7_p-1):
                    if col7_p[i] == "***":
                        assert_msg = "Inconsistency detected in column 7 of SYSTEM's "
                        assert_msg += "file\nAll tokens should have value *** for this"
                        assert_msg += "column\nError in sentence that finishes before "
                        assert_msg += "line number " + str(line_number) + ", token "
                        assert_msg_end ="\nFix this before proceeding with evaluation"
                        if i > 0:
                            assert col7_p[i-1] == "***", assert_msg+str(i-1)+assert_msg_end
                        assert col7_p[i+1] == "***", assert_msg+str(i+1)+assert_msg_end
                        
                col7_p = []
                max_tmp_linep = -1            
        
                
            else:
                tmp_lineg = st_tmp_lineg.split("\t")
                tmp_linep = st_tmp_linep.split("\t")
                
                # 1. check for line mismatches
                assert_msg = "ATTENTION: mismatch between lines of GOLD file and "
                assert_msg += "SYSTEM file\nIn file: " + tmp_lineg[0] + ", sentence: "
                assert_msg += tmp_lineg[1] + ", word: " + tmp_lineg[2] + "\nThis "
                assert_msg += "needs to be fixed before evaluating\nProcess ended\n"
                
                assert tmp_linep[0] == tmp_lineg[0], assert_msg  # file name
                assert tmp_linep[1] == tmp_lineg[1], assert_msg  # sent number
                assert tmp_linep[2] == tmp_lineg[2], assert_msg  # token number
                assert tmp_linep[3] == tmp_lineg[3], assert_msg  # word
                
                # 2. check the annotation consistency
                col7_p.append(tmp_linep[7])
                
                if max_tmp_linep == -1:
                    max_tmp_linep = len(tmp_linep)-1
                
                # check if the number of negation columns is the same in all lines
                assert_msg = "Inconsistency detected in the number of columns at "
                assert_msg += "line number " + str(line_number) + "\nAll tokens in a "
                assert_msg += "sentence should have the same number of columns\n"
                assert max_tmp_linep == len(tmp_linep)-1, assert_msg
                
                # check if the number of columns is correct
                if max_tmp_linep != 7:
                    assert_msg = "Incorrect number of columns in line number " + str(line_number)
                    assert_msg += "\nThere should be 3 columns per negation cue\n"
                    assert_msg += "Fix this before proceeding to evaluation\n"
                    assert max_tmp_linep % 3 == 0, assert_msg
    
    tmp_lineg = []
    tmp_linep = []
    st_tmp_lineg = ""
    st_tmp_linep = ""
    max_tmp_linep = -1
    line_number = 0
    

    #######################################################################
    ###### 3. evaluate
    #######################################################################
    
    POS = []

    neg_cols_g = []
    neg_cols_p = []    

    current_sent_idx = 0
    
    while current_sent_idx < count_sentences:
        
        # add empty line to have the required format for the given code
        gold_sent = GOLD[current_sent_idx].split("\n") + [""]
        system_sent = SYSTEM[current_sent_idx].split("\n") + [""]
        
        current_sent_idx += 1
        
        for idx in range(len(gold_sent)):
            st_tmp_lineg = gold_sent[idx].strip()
            st_tmp_linep = system_sent[idx].strip()
            
            line_number += 1
            
            ### if line is blank or if end of file is reached
            ### process sentence
            if st_tmp_lineg == "":
                process_sentence(neg_cols_g, neg_cols_p, POS, starsem_exact=starsem_exact)
                         
                ###################################
                ## initialize variables 
                ## before processing next sentence
                ###################################
                POS = []
            
                neg_cols_g = []
                neg_cols_p = []
    
            ###################################
            ## get information about sentence
            ###################################
            else:
                tmp_neg_g, tmp_neg_p, POS_tag = get_info_sentence(st_tmp_lineg, 
                                                                  st_tmp_linep)
                
                POS.append(POS_tag)
                neg_cols_g.append(tmp_neg_g)
                neg_cols_p.append(tmp_neg_p)
    
    
    ######### calculate F measures

    def calculate_f1(precision, recall, starsem_exact=starsem_exact):
        """
        Calculates f1 from given precision and recall.
        """
        # original rounds precision and recall before calculating f1
        if starsem_exact:
            f1 = (2 * round(precision, 2) * round(recall, 2)) / (round(precision, 2) + round(recall, 2)) if (precision + recall) else 0.00
        else:
            f1 = (2 * precision * recall) / (precision + recall) if (precision + recall) else 0.00
        return f1
    
    
    ####### cues
    precision_cue = (tp_cue / (tp_cue + fp_cue)) * 100 if (tp_cue + fp_cue) else 0.00
    precision_cue_b = (tp_cue / (cues_p)) * 100 if cues_p else 0.00
    recall_cue = (tp_cue / (tp_cue + fn_cue)) * 100 if (tp_cue + fn_cue) else 0.00
    f1_cue = calculate_f1(precision_cue, recall_cue)
    f1_cue_b = calculate_f1(precision_cue_b, recall_cue)
    
    
    ###### scopes
    precision_scope = (tp_scope / (tp_scope + fp_scope)) * 100 if (tp_scope + fp_scope) else 0.00
    precision_scope_b = (tp_scope / (scopes_p)) * 100 if scopes_p else 0.00
    recall_scope = (tp_scope / (tp_scope + fn_scope)) * 100 if (tp_scope + fn_scope) else 0.00
    f1_scope = calculate_f1(precision_scope, recall_scope)
    f1_scope_b = calculate_f1(precision_scope_b, recall_scope)


    ###### scopes apart
    precision_scope_apart = (tp_scope_apart / (tp_scope_apart + fp_scope_apart)) * 100 if (tp_scope_apart + fp_scope_apart) else 0.00
    precision_scope_apart_b = (tp_scope_apart / scopes_p) * 100 if scopes_p else 0.00
    recall_scope_apart = (tp_scope_apart / (tp_scope_apart + fn_scope_apart)) * 100 if (tp_scope_apart + fn_scope_apart) else 0.00
    f1_scope_apart = calculate_f1(precision_scope_apart, recall_scope_apart)
    f1_scope_apart_b = calculate_f1(precision_scope_apart_b, recall_scope_apart)
    

    ###### scopes nopunc
#    precision_scope_nopunc = (tp_scope_nopunc / (tp_scope_nopunc + fp_scope_nopunc)) * 100 if (tp_scope_nopunc + fp_scope_nopunc) else 0.00
#    precision_scope_nopunc_b = (tp_scope_nopunc / scopes_p) * 100 if scopes_p else 0.00
#    recall_scope_nopunc = (tp_scope_nopunc / (tp_scope_nopunc + fn_scope_nopunc)) * 100 if (tp_scope_nopunc + fn_scope_nopunc) else 0.00
#    f1_scope_nopunc = calculate_f1(precision_scope_nopunc, recall_scope_nopunc)
#    f1_scope_nopunc_b = calculate_f1(precision_scope_nopunc_b, recall_scope_nopunc)

    
    ###### scope tokens
    precision_scope_tokens = (tp_scope_tokens / (tp_scope_tokens + fp_scope_tokens)) * 100 if (tp_scope_tokens + fp_scope_tokens) else 0.00
    recall_scope_tokens = (tp_scope_tokens / (tp_scope_tokens + fn_scope_tokens)) * 100 if (tp_scope_tokens + fn_scope_tokens) else 0.00
    f1_scope_tokens = calculate_f1(precision_scope_tokens, recall_scope_tokens)

    
    ###### negated apart
    precision_negated_apart = (tp_negated_apart / (tp_negated_apart + fp_negated_apart)) * 100 if (tp_negated_apart + fp_negated_apart) else 0.00    
    precision_negated_apart_b = (tp_negated_apart / negated_p) * 100 if negated_p else 0.00    
    recall_negated_apart = (tp_negated_apart / (tp_negated_apart + fn_negated_apart)) * 100 if (tp_negated_apart + fn_negated_apart) else 0.00    
    f1_negated_apart = calculate_f1(precision_negated_apart, recall_negated_apart)
    f1_negated_apart_b = calculate_f1(precision_negated_apart_b, recall_negated_apart)
    
    
    ##### full negation
    precision_full_negation = (tp_full_negation / (tp_full_negation + fp_full_negation)) * 100 if (tp_full_negation + fp_full_negation) else 0.00    
    precision_full_negation_b = (tp_full_negation / cues_p) * 100 if cues_p else 0.00    
    recall_full_negation = (tp_full_negation / (tp_full_negation + fn_full_negation)) * 100 if (tp_full_negation + fn_full_negation) else 0.00    
    f1_full_negation = calculate_f1(precision_full_negation, recall_full_negation)
    f1_full_negation_b = calculate_f1(precision_full_negation_b, recall_full_negation)
    
    
    ##### percentage sentences
    perc_error_sentences = (count_error_sentences * 100) /  count_sentences    
    perc_error_negation_sentences = (count_error_sentences_negation * 100) /  count_sentences_negation if count_sentences_negation else 0.00
    perc_correct_sentences = 100 - perc_error_sentences
    perc_correct_negation_sentences = 100 - perc_error_negation_sentences


    ######### print results
    print_str  = "----------------------------+------+--------+------+------+------+---------------+------------+---------\n"
    print_str += "                            | gold | system | tp   | fp   | fn   | precision (%) | recall (%) | F1  (%) \n"
    print_str += "----------------------------+------+--------+------+------+------+---------------+------------+---------\n"
    print_str += "Cues: {:28d} | {:6d} | {:4d} | {:4d} | {:4d} | {:13.2f} | {:10.2f} | {:7.2f}".format(cues_g, cues_p, tp_cue, fp_cue, fn_cue,  precision_cue, recall_cue, f1_cue) + "\n"
    print_str += "Scopes(cue match): {:15d} | {:6d} | {:4d} | {:4d} | {:4d} | {:13.2f} | {:10.2f} | {:7.2f}".format(scopes_g, scopes_p, tp_scope, fp_scope, fn_scope,  precision_scope, recall_scope, f1_scope) + "\n"
    if starsem_exact:
        # original outputs tp for partial cue match (original line 2397)
        print_str += "Scopes(no cue match): {:12d} | {:6d} | {:4d} | {:4d} | {:4d} | {:13.2f} | {:10.2f} | {:7.2f}".format(scopes_g, scopes_p, tp_scope, fp_scope_apart, fn_scope_apart,  precision_scope_apart, recall_scope_apart, f1_scope_apart) + "\n"
    else:   
        print_str += "Scopes(no cue match): {:12d} | {:6d} | {:4d} | {:4d} | {:4d} | {:13.2f} | {:10.2f} | {:7.2f}".format(scopes_g, scopes_p, tp_scope_apart, fp_scope_apart, fn_scope_apart,  precision_scope_apart, recall_scope_apart, f1_scope_apart) + "\n"
#    print_str += "Scopes(no cue match, no punc): {:3d} | {:6d} | {:4d} | {:4d} | {:4d} | {:13.2f} | {:10.2f} | {:7.2f}".format(scopes_g, scopes_p, tp_scope, fp_scope_nopunc, fn_scope_nopunc,  precision_scope_nopunc, recall_scope_nopunc, f1_scope_nopunc) + "\n"
    print_str += "Scope tokens(no cue match): {:6d} | {:6d} | {:4d} | {:4d} | {:4d} | {:13.2f} | {:10.2f} | {:7.2f}".format(total_scope_tokens_g, total_scope_tokens_p, tp_scope_tokens, fp_scope_tokens, fn_scope_tokens, precision_scope_tokens, recall_scope_tokens, f1_scope_tokens) + "\n"
    print_str += "Negated(no cue match): {:11d} | {:6d} | {:4d} | {:4d} | {:4d} | {:13.2f} | {:10.2f} | {:7.2f}".format(negated_g, negated_p, tp_negated_apart, fp_negated_apart, fn_negated_apart,  precision_negated_apart, recall_negated_apart, f1_negated_apart) + "\n"
    print_str += "Full negation: {:19d} | {:6d} | {:4d} | {:4d} | {:4d} | {:13.2f} | {:10.2f} | {:7.2f}".format(cues_g, cues_p, tp_full_negation, fp_full_negation, fn_full_negation,  precision_full_negation, recall_full_negation, f1_full_negation) + "\n"
    print_str += "---------------------------+------+--------+------+------+------+---------------+------------+---------\n"
    print_str += "Cues B: {:26d} | {:6d} | {:4d} | {:4d} | {:4d} | {:13.2f} | {:10.2f} | {:7.2f}".format(cues_g, cues_p, tp_cue, fp_cue, fn_cue,  precision_cue_b, recall_cue, f1_cue_b) + "\n"
    print_str += "Scopes B (cue match): {:12d} | {:6d} | {:4d} | {:4d} | {:4d} | {:13.2f} | {:10.2f} | {:7.2f}".format(scopes_g, scopes_p, tp_scope, fp_scope, fn_scope,  precision_scope_b, recall_scope, f1_scope_b) + "\n"
    print_str += "Scopes B (no cue match): {:9d} | {:6d} | {:4d} | {:4d} | {:4d} | {:13.2f} | {:10.2f} | {:7.2f}".format(scopes_g, scopes_p, tp_scope_apart, fp_scope_apart, fn_scope_apart,  precision_scope_apart_b, recall_scope_apart, f1_scope_apart_b) + "\n"
    print_str += "Negated B (no cue match): {:8d} | {:6d} | {:4d} | {:4d} | {:4d} | {:13.2f} | {:10.2f} | {:7.2f}".format(negated_g, negated_p, tp_negated_apart, fp_negated_apart, fn_negated_apart,  precision_negated_apart_b, recall_negated_apart, f1_negated_apart_b) + "\n"
    print_str += "Full negation B: {:17d} | {:6d} | {:4d} | {:4d} | {:4d} | {:13.2f} | {:10.2f} | {:7.2f}".format(cues_g, cues_p, tp_full_negation, fp_full_negation, fn_full_negation,  precision_full_negation_b, recall_full_negation, f1_full_negation_b) + "\n"
    print_str += "----------------------------+------+--------+------+------+------+---------------+------------+---------\n"
    print_str += f" # sentences: {count_sentences}\n"
    print_str += f" # negation sentences: {count_sentences_negation}\n"
    print_str += f" # negation sentences with errors: {count_error_sentences_negation}\n"
#    print_str += f" % sentences with errors: {perc_error_sentences:.2f}\n"
    print_str += f" % correct sentences: {perc_correct_sentences:.2f}\n"
    print_str += f" % correct negation sentences: {perc_correct_negation_sentences:.2f}\n"
    print_str += "--------------------------------------------------------------------------------------------------------\n"
    print(print_str)
    

if __name__ == "__main__":
    argdesc = "*SEM Shared Task 2012 evaluation script"
    argparser = argparse.ArgumentParser(description=argdesc)
    argparser.add_argument("-g", "--gold", type=str, help="gold standard file path (required)")
    argparser.add_argument("-s", "--system", type=str, help="system output file path (required)")
    argparser.add_argument("-r", "--readme", action="store_true",
                           help="print a brief explanation about the evaluation output") 
    argparser.add_argument("-e", "--starsem-exact", default=False, action="store_true", 
                           help="output the exact same results as the original (use -r for a readme that includes a description of differences between this evaluation script and the original)")


    gold_name = "../data/BioScope/Abstracts/created_splits/starsem2012_format/starsem2012.abstracts.negation.txt.test"
    pred_name = "../data/ConanDoyle-neg/pred/reannotated/starsem2012_format/direct_syntbert/STARSEM_test-parsed_neg-conan-reann_syntax_direct_0601_005256_bio-abs.conll.pred"

    
    args = argparser.parse_args(["-g", gold_name, 
                                 "-s", pred_name])#, 
##                                 "-e"])
#    args = argparser.parse_args(["-h"])
        
    if args.readme:
        readme_str = """
This evaluation script differs from the original script in the following:
    - original omits some FNs for negated event that had a partial match with the prediction written in file last out of all
    - original counts as FN cases with one token being an event twice and written in prediction
      in a diffferent order than in gold (e.g. event 1: unlike, event 2: like (where the cue is un))
    - original outputs TP of Scope (cue match) when reporting results for Scope (no cue match)
    - original rounds precision and recall before calculating f1

To obtain exactly the same output as the original, use -e (--starsem-exact) argument.

Following is the description provided by the original script.

This evaluation script compares the output of a system versus a gold annotation and provides the following information:

 ----------------------------+------+--------+------+------+------+---------------+------------+---------
                             | gold | system | tp   | fp   | fn   | precision (%) | recall (%) | F1  (%) 
 ----------------------------+------+--------+------+------+------+---------------+------------+---------
 Cues:                              |        |      |      |      |               |            |        
 Scopes(cue match):                 |        |      |      |      |               |            |        
 Scopes(no cue match):              |        |      |      |      |               |            |        
 Scope tokens(no cue match):        |        |      |      |      |               |            |        
 Negated(no cue match):             |        |      |      |      |               |            |        
 Full negation:                     |        |      |      |      |               |            |        
 ----------------------------+------+--------+------+------+------+---------------+------------+---------
 Cues B:                            |        |      |      |      |               |            |        
 Scopes B (cue match):              |        |      |      |      |               |            |        
 Scopes B (no cue match):           |        |      |      |      |               |            |        
 Negated B (no cue match):          |        |      |      |      |               |            |        
 Full negation B:                   |        |      |      |      |               |            |         
 ----------------------------+------+--------+------+------+------+---------------+------------+---------
 # sentences:  
 # negation sentences:  
 # negation sentences with errors: 
 % correct sentences:  
 % correct negation sentences:  
 --------------------------------------------------------------------------------------------------------


 The F measures for "cues", "scope", and "negated" are calculated at scope level.
 The F measures for "scope tokens" are calculated at token level counting as tokens the total number of scope tokens. If a sentence has 2 scopes, one with 5 tokens and another with 4, the total number of scope tokens is 9, 

 precision = tp / (tp + fp)
 recall = tp / (tp + fn)
 F1 = (2 * $precision_cue * $recall_cue) / ($precision_cue + $recall_cue)

 For cue, scope and negated to be correct, both, the tokens and the words or parts of words have to be
 correclty identified.


 - In "scopes(cue match)", for the scope to be correct, the cue has to be correct.
 - In "scopes(no cue match)", for the scope to be correct, the cue doesn't need to be completely correct, though there must be a token
     of overlap between the cue predicted by the system and the gold cue.
 - In "scope tokens(no cue match)", for the scope tokens to be correct, the cue doesn't need to be completely correct, though there must be a token of overlap between the cue predicted by the system and the gold cue.
 - In "negated(no cue match)", negated is evaluated apart from cue and scope.

 For a full negation to be correct, all elements have to be correct: cue, scope, and negated.

 False negatives are counted either by the system not identifying negation elements present in gold, or by identifying them partially, i.e., not all tokens have been correctly identified or the word forms are incorrect.

 False positives are counted when the system produces a negation element not present in gold.

 True positives are counted when the system produces negation elements exactly as they are in gold.

 Example 1:

 Gold annotation: cue is "un" and  scope is "decided".

 If system identifies "und" as cue and "decided" as scope, it will be counted as false negative for cue and for scope (in scopes cue match), 
 because cue is incorrect.
 If system identifies "un" as cue and "undecided" as scope, cue will count as true positive and scope as false negative.

 Example 2:

 Gold annotation: cue is "un" and  scope is "decided".
 System doesn't have a negation.
 Cue and scope will be false negatives (in scopes cue match).

 Example 3:

 Gold doesn't have a negation.
 System produces a negation, then the negation elements produced by system will count as false positives.

 Example 4:

 Gold annotation: cue is "never", scope is "Holmes entered in the house".
 System output: cue is "never", scope is "entered in the house".
 Cue will be true positive, but scope will be false negative because not all tokens have been produced by system.

 From v.2.1  the final periods in abbreviations are disregarded. If gold has value "Mr." and system "Mr", system is counted as correct.

 From v.2.2 punctuation tokens are *not* taken into account for evaluation. 

 From v2.2 the "B" variant for Cues, Scopes, Negated and Full Negation has been introduced. 
 The difference lies in how precision is calculated.
 In the "B" measures, precision = tp / system.

 EXAMPLE OF FORMAT EXPECTED

 Without negation: the 8th column is "***" for all tokens.

 Wisteria_ch1	49	0	"	"	PUNC"	(S(NPB*	***
 Wisteria_ch1	49	1	Your	your	PRP$	*	***
 Wisteria_ch1	49	2	telegram	telegram	NN	*NPB)	***
 Wisteria_ch1	49	3	was	be	VBD	(VP*	***
 Wisteria_ch1	49	4	dispatched	dispatch	VBN	(VP*	***
 Wisteria_ch1	49	5	about	about	RB	(QP*	***
 Wisteria_ch1	49	6	one	one	CD	*	***
 Wisteria_ch1	49	7	.	.	PUNC.	*QP)VP)VP)S)	***

 With negation: the columns for negation start at the 8th columns. There will be three columns for each negation (cue, scope, negated). A negation must have at least a negation cue annotated. 

 Wisteria_ch1	217	0	It	it	PRP	(S(S*	_	_	_
 Wisteria_ch1	217	1	is	be	VBZ	(VP*	_	_	_
 Wisteria_ch1	217	2	a	a	DT	(NPB*	_	_	_
 Wisteria_ch1	217	3	lonely	lonely	JJ	*	_	_	_
 Wisteria_ch1	217	4	corner	corner	NN	*	_	_	_
 Wisteria_ch1	217	5	,	,	PUNC,	*NPB)VP)S)	_	_	_
 Wisteria_ch1	217	6	and	and	CC	*	_	_	_
 Wisteria_ch1	217	7	there	there	EX	(S*	_	there	_
 Wisteria_ch1	217	8	is	be	VBZ	(VP*	_	is	_
 Wisteria_ch1	217	9	no	no	DT	(NP(NPB*	no	_	_
 Wisteria_ch1	217	10	house	house	NN	*NPB)	_	house	house
 Wisteria_ch1	217	11	within	within	IN	(PP*	_	within	_
 Wisteria_ch1	217	12	a	a	DT	(NP(NPB*	_	a	_
 Wisteria_ch1	217	13	quarter	quarter	NN	*NPB)	_	quarter	_
 Wisteria_ch1	217	14	of	of	IN	(PP*	_	of	_
 Wisteria_ch1	217	15	a	a	DT	(NP(NPB*	_	a	_
 Wisteria_ch1	217	16	mile	mile	NN	*NPB)	_	mile	_
 Wisteria_ch1	217	17	of	of	IN	(PP*	_	of	_
 Wisteria_ch1	217	18	the	the	DT	(NPB*	_	the	_
 Wisteria_ch1	217	19	spot	spot	NN	*	_	spot	_
 Wisteria_ch1	217	20	.	.	PUNC.	*NPB)PP)NP)PP)NP)PP)NP)VP)S)S)	_	_	_
        """
        print(readme_str)
        argparser.exit() 
    
    # handle cases when gold or system files are not provided
    elif not args.gold:
        print("Gold standard file (-g) missing\n")
        argparser.parse_args(["-h"])
    
    elif not args.system:
        print("System output file (-s) missing\n")
        argparser.parse_args(["-h"])
    
    # get results and print them out
    main(args.gold, args.system, starsem_exact=args.starsem_exact)
    
