#!/usr/bin/env python
'''
Created on Aug 2, 2012

@author: Ben Couturier
'''
import BuildDirHelpers
import sys
from LbConfiguration.Package import getPackage

if __name__ == '__main__':

    if len (sys.argv) < 3:
        print >> sys.stderr, "Please specify builddir and cmtconfig"
        exit(1)

    releasedir = sys.argv[1]
    cmtconfig = sys.argv[2]

    # First listing the dependencies
    ################################################################################
    allprojects = BuildDirHelpers.findCMTRequiredProjects(releasedir)
    allpackages = BuildDirHelpers.findCMTRequiredPackages(releasedir)
    datapackages = []
    for (pname, pver) in allpackages:
        p =  getPackage(pname, svn_fallback=True, raise_exception=False)
        if p != None:
            datapackages.append((p.tarBallName(), pver))


    # Now preparing the requires section
    ################################################################################
    alldeps = ""
    rpmconfig = cmtconfig.replace("-", "_")
    for (pname, pnamever) in allprojects:
        alldeps += "Requires: %s_%s\n" % (pnamever, rpmconfig)
    for (pname, pver) in datapackages:
        alldeps += "Requires: %s\n" % pname
    print alldeps
