#!/usr/bin/env python
'''
Created on Aug 2, 2012

@author: Ben Couturier
'''


import os
from time import time

lhcbreleasedir = os.environ['LHCBRELEASES']
apps = ["ALIGNMENT",
"ANALYSIS",
"BENDER",
"BOOLE",
"BRUNEL",
"CURIE",
"DAVINCI",
"GAUSS",
"HLT",
"LBCOM",
"LHCB",
"MOORE",
"ONLINE",
"PANORAMIX",
"PHYS",
"REC" ]

tobuild=[]
for a in apps:
    appdir = os.path.join(lhcbreleasedir, a)
    for d in os.listdir(appdir):
        path = os.path.join(appdir, d)
        try:
            mtime = os.path.getctime(path)
            ages = time() - mtime
            if ages  < 24 *3600*10:
                tobuild.append(path)
        except:
            # Need to to this otherwise we choke on bad links...
            pass


for p in tobuild:
    pversion = os.path.basename(p)
    project = os.path.basename(os.path.dirname(p))
    version = pversion.replace(project + "_", "")
    print "createProjectSourceRpm.py %s %s" % (project, version)
    print "createProjectRpmFromBuild.py %s" %p
