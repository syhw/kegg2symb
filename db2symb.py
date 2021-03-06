#!/usr/bin/python
"""
Always reads from stdin, and print output on stdout

Default behavior:
    Reads XML, outputs reaction nodes.
    Queries KEGG API (via SOAP) to convert KEGG IDs into names.

--offline:
    Don't use API, output {xxx:yyyy} instead of description.

--genes: 
    Don't use reaction names but genes that are involved in the reactions.
    Can be used online of offline.
    /!\ Genes and Reactions won't give the same output : 
        if there are two genes involved in one reaction,
        '--genes' will output two reactions, one for each gene
        [default] will output only one reaction with the rn:id

--convert:
    Convert any text containing {xxx:yyyy} entities, replacing each
    KEGG IDs with its readable descriptions.

  "python db2symb.py --offline < file | python db2symb.py --convert"

should have the very same behavior as

  "python db2symb.py < file"

for the full (online) version installation, SOAPpy is needed, see here:
http://www.diveintopython.org/soap_web_services/install.html#d0e30070

"""
# Copyright (C) 2009 
# Author: Gabriel Synnaeve (& Nicolas Dumazet)
# License: http://www.opensource.org/licenses/PythonSoftFoundation.php

import xml.sax
from xml.sax.handler import ContentHandler

import sys, re

enzymes = 0
light = 0
genes = 0

class DescFetcher(object):
    desc = re.compile('^\S* ([^;\n]*)(?:;.*|)$', re.MULTILINE)

    def __init__(self):
        from SOAPpy import WSDL
        wsdl = 'http://soap.genome.jp/KEGG.wsdl'
        self.serv = WSDL.Proxy(wsdl)

    def fetch(self, list, method):
        """
        Returns list of descriptions for kegg keywords list
        REQ: len(list) < 100
        """
        req = ' '.join(list)
        if method == 'btit':
            results = self.serv.btit(req)
        elif method == 'get_enzymes_by_reaction': ### TODO REFACTOR
            results = ''
            rname = req.split(' ')
            for i in range(len(rname)):
                enz = self.serv.get_enzymes_by_reaction(rname[i])
                results = results + rname[i] + ' ' + '-'.join(enz) + '\n'
            #sys.exit('Unfinished work')
        elif method == 'get_enzymes_by_gene': ### TODO REFACTOR
            results = ''
            rname = req.split(' ')
            print rname
            for i in range(len(rname)):
                enz = self.serv.get_enzymes_by_gene(rname[i])
                results = results + rname[i] + ' ' + '-'.join(enz) + '\n'
            #sys.exit('Unfinished work')
        return DescFetcher.desc.findall(results) 

    def bigFetch(self, list, method='btit'):
        results = []
        while len(list) > 100:
            results += self.fetch(list[:100], method)
            list = list[100:]
        return results + self.fetch(list, method)       

class AbstractHandler(ContentHandler):
    """
    Reactions parser
    """
    reacgenes = {} # map reaction -> list of genes

    def __init__(self):
        self.reset()

    def reset(self):
        self.reacname = []      # just a list which is a string !
        self.rev = 0            # reversible or not
        self.substrates = []    # string list
        self.products = []      # string list

    def onReactionGeneration(self):
        """ABSTRACT"""
        pass
        
    def startElement(self, name, attrs):
        if name == 'entry' and attrs['type'] == 'gene':
            for r in attrs['reaction'].split(' '):
                for n in attrs['name'].split(' '):
                    if self.reacgenes.has_key(r):
                        self.reacgenes[r].append(n)
                    else:
                        self.reacgenes[r] = [n]
        elif name == 'reaction':
            self.reacname = attrs['name']
            if attrs['type'] == "reversible":
                self.rev = 1
        elif name == 'substrate':
            self.substrates.append(attrs['name'])
        elif name == 'product':
            self.products.append(attrs['name'])

    def endElement(self, name):
        if name == 'reaction':
            self.onReactionGeneration()
            self.reset()

class OfflineHandler(AbstractHandler):
    def startDocument(self):
        self.result = ''

    format = '{%s}'

    def formatReact(self, args):
        nbSubs = len(self.substrates)
        nbPrds = len(self.products)
        if nbSubs > 1:
            subs = 'complex(' + ', '.join([OfflineHandler.format]*nbSubs) + ')'
        else:
            subs = OfflineHandler.format
        if nbPrds > 1:
            prds = 'complex(' + ', '.join([OfflineHandler.format]*nbPrds) + ')'
        else:
            prds = OfflineHandler.format
        formatted = 'reaction(' + subs + ', '+ OfflineHandler.format +', '\
                + prds + ', Km)\n'
        self.result += formatted % tuple(args)
        if self.rev:
            formatted = 'reaction(' + prds + ', '+ OfflineHandler.format +', '\
                    + subs + ', Km)\n'
            self.result += formatted % tuple(args[::-1])

    def onReactionGeneration(self):
        args = self.substrates + [self.reacname] + self.products
        self.formatReact(args)

    def getResult(self):
        return self.result.rstrip()
    
class GenesHandler(OfflineHandler):
    def onReactionGeneration(self):
        for rg in self.reacgenes[self.reacname] :
            args = self.substrates + [rg] + self.products
            self.formatReact(args)

def convert(text):
    """
    Assumes every string between { } in the original text is
    a compound code or a reaction code, and replaces { } by the description
    """
    if enzymes: # TODO REFACTOR
        fetcher = DescFetcher()
        braces = re.compile('{(cpd[^}]*)}')
        codes = braces.findall(text)
        descs = fetcher.bigFetch(codes)
        text = braces.sub('%s', text)
        ret = text % tuple(descs)
        if genes:
            braces = re.compile('{(sce[^}]*)}')
            codes = braces.findall(text)
            descs = fetcher.bigFetch(codes, 'get_enzymes_by_gene')
        else:
            braces = re.compile('{(rn[^}]*)}')
            codes = braces.findall(text)
            descs = fetcher.bigFetch(codes, 'get_enzymes_by_reaction')
        #descs = fetcher.bigFetch(codes)
        ret = braces.sub('%s', ret)
        ret = ret % tuple(descs)
    else: 
        braces = re.compile('{([^}]*)}')
        fetcher = DescFetcher()
        codes = braces.findall(text)
        descs = fetcher.bigFetch(codes)
        text = braces.sub('%s', text)
        ret = text % tuple(descs)
    ### TODO LIGHT
    if light:
        middle = re.compile('reaction\([^,()]*\(?[^()]*\)?')
    return ret

for a in sys.argv:
    if '--web' in a:
        d_url = a.replace('--web','')
        import urllib
        url2fetch = 'ftp://ftp.genome.jp/pub/kegg/xml/organisms/'\
                +d_url[:3]+'/'+d_url+'.xml'        
        print url2fetch
        urllib.urlretrieve(url2fetch, 'tmpfile')
        tmpfile = open('tmpfile', 'r')
        sys.stdin = tmpfile

if '--enzymes' in sys.argv:
    enzymes = 1

if '--light' in sys.argv:
    light = 1

if '--convert' in sys.argv:
    print convert(sys.stdin.read()).rstrip()
else:
    if '--offline' in sys.argv:
        if '--genes' in sys.argv:
            genes = 1
            handler = GenesHandler()
            xml.sax.parse(sys.stdin, handler)
            print handler.getResult()
        else:
            handler = OfflineHandler()
            xml.sax.parse(sys.stdin, handler)
            print handler.getResult()
    else:
        if '--genes' in sys.argv:
            genes = 1
            handler = GenesHandler()
            xml.sax.parse(sys.stdin, handler)
            print convert(handler.getResult())
        else:
            handler = OfflineHandler()
            xml.sax.parse(sys.stdin, handler)
            print convert(handler.getResult())

