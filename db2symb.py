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
            
class DescFetcher(object):
    desc = re.compile('^\S* ([^;\n]*)(?:;.*|)$', re.MULTILINE)

    def __init__(self):
        from SOAPpy import WSDL
        wsdl = 'http://soap.genome.jp/KEGG.wsdl'
        self.serv = WSDL.Proxy(wsdl)

    def fetch(self, list):
        """
        Returns list of descriptions for kegg keywords list
        REQ: len(list) < 100
        """
        req = ' '.join(list)
        results = self.serv.btit(req)
        return DescFetcher.desc.findall(results) 

    def bigFetch(self, list):
        results = []
        while len(list) > 100:
            results += self.fetch(list[:100])
            list = list[100:]
        return results + self.fetch(list)       

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
                + prds + ', Km, Vm)\n'
        self.result += formatted % tuple(args)
        if self.rev:
            formatted = 'reaction(' + prds + ', '+ OfflineHandler.format +', '\
                    + subs + ', Km, Vm)\n'
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

def convert(text, light=0):
    """
    Assumes every string between { } in the original text is
    a compound code or a reaction code, and replaces { } by the description
    """
    braces = re.compile('{([^}]*)}')
    fetcher = DescFetcher()
        
    codes = braces.findall(text)
    descs = fetcher.bigFetch(codes)
    text = braces.sub('%s', text)
    ret = text % tuple(descs)
    ### TODO light
    if light:
        #spaces = re.compile('^[^, ]|[^,]\n')
        middle = re.compile('reaction\([^,()]*\(?[^()]*\)?')
        #ret = re.sub('reaction\([^,]*|[^,]*\)\n', '___________', ret)
        #print spaces.search(ret)
        #print spaces.findall(ret).strip(' ')
    ### TODO enzyme codes
    return ret

if '--convert' in sys.argv:
    print convert(sys.stdin.read()).rstrip()
else:
    if '--offline' in sys.argv:
        if '--genes' in sys.argv:
            handler = GenesHandler()
            xml.sax.parse(sys.stdin, handler)
            print handler.getResult()
        else:
            handler = OfflineHandler()
            xml.sax.parse(sys.stdin, handler)
            print handler.getResult()
    else:
        if '--genes' in sys.argv:
            handler = GenesHandler()
            xml.sax.parse(sys.stdin, handler)
            print convert(handler.getResult())
        elif '--light' in sys.argv:
            handler = OfflineHandler()
            xml.sax.parse(sys.stdin, handler)
            print convert(handler.getResult(), 1)
        else:
            handler = OfflineHandler()
            xml.sax.parse(sys.stdin, handler)
            print convert(handler.getResult())

