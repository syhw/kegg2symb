#!/usr/bin/python
# vim: set fileencoding=utf-8
# encoding=utf-8

#import re
#ex = re.compile('input_.*')

fr = open('glycopento.sol')
fw = open('glyco_pento.sol', 'w')
for line in fr: 
    tow = line.replace('pyruvate', 'pyr')
    tow = tow.replace('beta_d_frustose_1_6_bisphosphate', 'fdp')
    tow = tow.replace('d_frustose_6_phosphate', 'f6p')
#    tow = tow.replace('', 'glucose')
#    tow = tow.replace('', 'g6p')
#    tow = tow.replace('', 'gap')
#    tow = tow.replace('', 'pep')
#    tow = tow.replace('', '6pg')
#    tow = tow.replace('', 'g1p')
#    tow = tow.replace('', 'amp')
    #tow = tow.replace('', 'nadp')
    tow = tow.replace('nadp_plus', 'nadph')
    #tow = tow.replace('', 'nad')
    tow = tow.replace('nad_plus', 'nadh')
    fw.write(tow)
