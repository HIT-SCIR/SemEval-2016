#!/usr/bin/env python
# -*- coding: utf-8 -*-

############################################################################################
#  Official Evaluation Script for Semeval2016 Task9 Chinese Semantic Dependency Parsing    #
#  Version : 1.0                                                                           #
#  Author  : Xu , Wei ( based on scripts for Dependency Parsing written by Liu , Yijia)    #
#  BUG Report : wxu@ir.hit.edu.cn                                                          #
############################################################################################

import sys
import re
import unicodedata
from argparse import ArgumentParser

INF = float('inf')
opts = None
engine = None
UNICODEPUNC = dict.fromkeys(i for i in xrange(sys.maxunicode)
        if unicodedata.category(unichr(i)).startswith('P'))

def stat_one_tree(lines) :
    stat_data = {}
    for line in lines :
        payload = line.strip().split("\t")
        if(len(payload) < 7) :
            print lines
        id_val = int(payload[0])
        form_val = payload[1]
        postag_val = payload[4]
        head_val = payload[6]
        deprel_val = payload[7]
        if not opts.punctuation and engine(form_val ,postag_val ) :
            continue
        if id_val not in stat_data :
            stat_data[id_val] = {
                            "id" : id_val ,
                            "form" : form_val ,
                            "heads" : [ head_val ] ,
                            "deprels" : [ deprel_val ]
                        }
        else :
            assert(form_val == stat_data[id_val]["form"])
            stat_data[id_val]["heads"].append(head_val)
            stat_data[id_val]['deprels'].append(deprel_val)
    return stat_data

def stat_one_node_heads_and_deprels(gold_heads , gold_deprels , test_heads , test_deprels) :
    gold_len = len(gold_heads) #! assert( len(gold_heads) == len(gold_deprels))
    test_len = len(test_heads)
    nr_right_heads = 0
    nr_right_deprels = 0

    nr_non_local_gold = 0
    nr_non_local_test = 0
    nr_non_local_right_heads = 0
    nr_non_local_right_deprels = 0
    
    is_head_right = True #! set default True . The default value is important : `if the state is not changed , we'll not set it value any more`
    is_deprel_right = True #! set default True
    assert(gold_len != 0 and test_len != 0 )
    if gold_len == 1 and test_len == 1 :
        #! normal situation
        if(gold_heads[0] == test_heads[0]) :
            nr_right_heads = 1
            if gold_deprels[0] == test_deprels[0] :
                nr_right_deprels = 1
            else :
                is_deprel_right = False
        else :
            is_head_right = False 
            is_deprel_right = False #! Attention . If head is wrong , deprel should be set to wrong .
    else :
        #! Non local  situation
        if gold_len > 1 :
            is_gold_non_local = True
        nr_non_local_gold = gold_len
        nr_non_local_test = test_len
        #! for Non local , if len(test_heads) !=  len(gold_heads) , the node 's head and deprels is  not right 
        if nr_non_local_gold != nr_non_local_test :
            is_deprel_right = False
            is_head_right = False
        #! find the right non-local head and deprel 
        #! if has wrong head or deprel , set the `is_head_right` or `is_deprel_right` to `False` 
        for gold_head , gold_deprel in zip(gold_heads , gold_deprels) :
            if gold_head in test_heads :
                nr_right_heads += 1
                head_idx = test_heads.index(gold_head)
                if gold_deprel == test_deprels[head_idx] : #!! head_idx == deprel_idx
                    nr_right_deprels += 1
                else :
                    is_deprel_right = False
            else :
                is_head_right = False
                is_deprel_right = False #! 
        #! here no local state equals to normal state
        nr_non_local_right_heads = nr_right_heads
        nr_non_local_right_deprels = nr_right_deprels

    return (gold_len , test_len , nr_right_heads , nr_right_deprels ,
           nr_non_local_gold , nr_non_local_test , nr_non_local_right_heads , nr_non_local_right_deprels ,
           is_head_right , is_deprel_right)

def stat_gold_and_test_data(gold_stat_data , test_stat_data) :
    nr_gold_rels = 0
    nr_test_rels = 0
    nr_head_right = 0
    nr_deprel_right = 0
    
    sentence_all_heads_is_right = True
    sentence_all_deprels_is_right = True
    
    nr_gold_non_local = 0
    nr_test_non_local = 0
    nr_head_non_local_right = 0
    nr_deprel_non_local_right = 0
    
    for idx in gold_stat_data.keys() :
        gold_node = gold_stat_data[idx]
        test_node = test_stat_data[idx]
        assert(gold_node['id'] == test_node['id'])
        
        (gold_rels_len , test_rels_len , nr_one_node_right_head , nr_one_node_right_deprel , 
        gold_non_local_rels , test_non_local_rels , nr_one_node_non_local_right_head , nr_one_node_non_local_right_deprel ,
        is_one_node_head_right , is_one_node_deprel_right) = ( 
        stat_one_node_heads_and_deprels(gold_node['heads'] , gold_node['deprels'] , 
                                        test_node['heads'] , test_node['deprels']) )

        nr_gold_rels += gold_rels_len 
        nr_test_rels += test_rels_len
        nr_head_right += nr_one_node_right_head 
        nr_deprel_right += nr_one_node_right_deprel 
        
        nr_gold_non_local += gold_non_local_rels
        nr_test_non_local += test_non_local_rels
        nr_head_non_local_right += nr_one_node_non_local_right_head
        nr_deprel_non_local_right += nr_one_node_non_local_right_deprel
        
        sentence_all_heads_is_right &= is_one_node_head_right
        sentence_all_deprels_is_right &= is_one_node_deprel_right
    
    return (nr_gold_rels , nr_test_rels , nr_head_right , nr_deprel_right , 
           nr_gold_non_local , nr_test_non_local , nr_head_non_local_right , nr_deprel_non_local_right ,
           sentence_all_heads_is_right , sentence_all_deprels_is_right)


if __name__ == "__main__" : 
    description = "Official Evaluation Script for Semeval2016 Task9 Chinese Semantic Dependency Parsing"
    parser = ArgumentParser(description=description)
    parser.add_argument("--reference", dest="reference", help="path to reference(gold) data" , required=True)
    parser.add_argument("--answer" , dest="answer" , help="path to answer(test) data" , required=True)
    parser.add_argument("--language", dest="language", default="universal" , help="specify language . 'universal' is defaulted. ")
    parser.add_argument("--punctuation", dest="punctuation", default=False, action="store_true", help="specify to include punctuation in evaluation. default ignored")
    parser.add_argument("--ignore", dest="ignore", default=None, help="ignore form . A char is a valid ignore form . default is None .")
    parser.add_argument("--debug", dest="debug", default=False, action="store_true", help="if set , statistic info will be output . default not set.")
    opts = parser.parse_args()
    
    if opts.language == "en":
        # English punctuation list is obtained from http://en.wikipedia.org/wiki/Punctuation_of_English
        engine = lambda x, y: x in ("'", "''", # apostrophe
                "(", ")", "[", "]", "{", "}", "-LRB-", "-RRB-", "-LSB-", "-RSB-", "-LCB-", "-RCB-", # brackets
                ":", # colon
                ",", # comma
                "-", "--", # dash
                "...", # ellipsis
                "!", # exclamation mark
                ".", # full stop
                "\"", "``", "`", # quotation marks
                ";", # semicolon
                "?" # question mark
                ) or x == opts.ignore
    elif opts.language == "ch":
        engine = lambda x, y: x in (
                "锛�", "锛�",
                "銆�", "銆�", "锛�",
                "锛�",
                "锛�",
                "鈥�", "锛�", "锛�", "锛�", "锛�",
                "鈥�", "鈥�", "鈥�", "鈥�", 
                "銆�", "銆�", "銆�", "銆�", "銆�", "銆�", "銆�", "銆�",
                "涓€涓€", "鈥曗€�", "鈥�", 
                ) or x == opts.ignore
    elif opts.language == "universal":
        engine = lambda x, y: len(x.decode("utf-8").translate(UNICODEPUNC)) == 0 or x == opts.ignore
    elif opts.language == "chen2014en":
        engine = lambda x, y: y in set(["''", "``", ",", ".", ":"])
    elif opts.language == "chen2014ch":
        engine = lambda x, y: y in set(['PU'])
    else:
        print >> sys.stderr, "Unknown language"
        print >> sys.stderr, "valid language : { universal[default] , en , ch , chen2014en , chen2014ch }"
        sys.exit(1)
    
    reference_dataset = open( opts.reference , "r").read().strip().split("\n\n")
    answer_dataset = open(opts.answer , "r").read().strip().split("\n\n")
    
    assert len(reference_dataset) == len(answer_dataset), "Number of instance unequal."
    
    nr_total_gold_rels = 0
    nr_total_test_rels = 0
    nr_total_right_heads = 0
    nr_total_right_deprels = 0

    nr_sentence = len(reference_dataset)
    nr_right_sentence_head = 0
    nr_right_sentence_deprel = 0
    
    nr_total_gold_non_local = 0
    nr_total_test_non_local = 0
    nr_total_right_heads_non_local = 0
    nr_total_right_deprel_non_local = 0
    
    for reference_data, answer_data in zip(reference_dataset, answer_dataset):
        reference_lines = reference_data.split("\n")
        answer_lines = answer_data.split("\n")
    
        reference_lines_len = len(reference_lines)
        answer_lines_len = len(answer_lines)
    
        reference_stat_data = stat_one_tree(reference_lines)
        answer_stat_data = stat_one_tree(answer_lines)
        #print "ref len:{},ans len:{}".format(len(reference_stat_data),len(answer_stat_data))
        assert(len(reference_stat_data) == len(answer_stat_data))
        
        (nr_one_gold_rels , nr_one_test_rels , nr_one_head_right , nr_one_deprel_right ,
        nr_one_gold_non_local , nr_one_test_non_local , nr_one_head_non_local_right , nr_one_deprel_non_local_right ,
        sentence_all_heads_is_right , sentence_all_deprels_is_right)  = stat_gold_and_test_data(reference_stat_data , answer_stat_data)
        
        nr_total_gold_rels += nr_one_gold_rels 
        nr_total_test_rels += nr_one_test_rels
        nr_total_right_heads += nr_one_head_right 
        nr_total_right_deprels += nr_one_deprel_right
        
        nr_total_gold_non_local += nr_one_gold_non_local 
        nr_total_test_non_local += nr_one_test_non_local
        nr_total_right_heads_non_local += nr_one_head_non_local_right
        nr_total_right_deprel_non_local += nr_one_deprel_non_local_right

        if sentence_all_heads_is_right :
            nr_right_sentence_head += 1
        if sentence_all_deprels_is_right :
            nr_right_sentence_deprel += 1

    
    LP = float(nr_total_right_deprels) / nr_total_test_rels if nr_total_test_rels != 0 else  INF 
    LR = float(nr_total_right_deprels) / nr_total_gold_rels if nr_total_gold_rels != 0 else INF
    LF = float(2 * nr_total_right_deprels) / (nr_total_test_rels + nr_total_gold_rels) if (nr_total_gold_rels + nr_total_test_rels) != 0 else INF
    
    NLP = float(nr_total_right_deprel_non_local ) / nr_total_test_non_local if nr_total_test_non_local != 0 else INF
    NLR = float(nr_total_right_deprel_non_local) / nr_total_gold_non_local if nr_total_gold_non_local != 0 else INF
    NLF = float( 2 * nr_total_right_deprel_non_local ) / (nr_total_test_non_local + nr_total_gold_non_local) if (nr_total_test_non_local + nr_total_gold_non_local) != 0 else INF


    UP = float(nr_total_right_heads) / nr_total_test_rels if nr_total_test_rels != 0 else INF
    UR = float(nr_total_right_heads) / nr_total_gold_rels if nr_total_gold_rels != 0 else INF
    UF = float(2 * nr_total_right_heads) / (nr_total_test_rels + nr_total_gold_rels) if (nr_total_gold_rels + nr_total_test_rels ) != 0 else INF
    
    NUP = float(nr_total_right_heads_non_local) / nr_total_test_non_local if nr_total_test_non_local != 0 else INF
    NUR = float(nr_total_right_heads_non_local) / nr_total_gold_non_local if nr_total_gold_non_local != 0 else INF
    NUF = float(2 * nr_total_right_heads_non_local) / (nr_total_test_non_local + nr_total_gold_non_local) if (nr_total_test_non_local + nr_total_gold_non_local) != 0 else INF

    LM = float(nr_right_sentence_deprel) / nr_sentence if nr_sentence != 0 else INF
    UM = float(nr_right_sentence_head) / nr_sentence if nr_sentence != 0 else INF
    if opts.debug : 
        print "{0}{1}{0}".format("-"*15 , "statistic info")
        print "puncuation ingoring mode  : {0}".format(opts.language)
        print "total gold rels : {0}".format(nr_total_gold_rels)
        print "total test rels : {0}".format(nr_total_test_rels)
        print "total right heads : {0}".format(nr_total_right_heads)
        print "total right deprels : {0}".format(nr_total_right_deprels)
        print "total gold non-local : {0}".format(nr_total_gold_non_local)
        print "total test non-local : {0}".format(nr_total_test_non_local)
        print "total right head(non-local) : {0}".format(nr_total_right_heads_non_local)
        print "total right deprels(non-local) : {0}".format(nr_total_right_deprel_non_local)
        print "total sentence : {0}".format(nr_sentence)
        print "total sentence with right head : {0}".format(nr_right_sentence_head)
        print "total sentence with right label : {0}".format(nr_right_sentence_deprel)
        print "{0}{0}{0}".format("-"*15)

    print "{0:^10}{1:^10}{2:^10}{3:^10}{4:^10}{5:^10}{6:^10}{7:^10}{8:^10}{9:^10}".format(
            "LP" , "LR" , "LF" , "NLF" , "UP" , "UR" , "UF" , "NUF" , "LM" , "UM")
    print "{0[0]:^10}{0[1]:^10}{0[2]:^10}{0[3]:^10}{0[4]:^10}{0[5]:^10}{0[6]:^10}{0[7]:^10}{0[8]:^10}{0[9]:^10}".format(
            map(lambda x : "{:.2f}%".format(x*100) ,  [LP , LR , LF , NLF , UP , UR , UF , NUF , LM , UM]))
