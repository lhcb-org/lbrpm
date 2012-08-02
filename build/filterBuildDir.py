#!/usr/bin/env python
"""
Command to convert a LHCb project tar ball in a RPM file
"""

import logging
import os
import sys
import BuildDirHelpers


log = logging.getLogger()
log.addHandler(logging.StreamHandler())
log.setLevel(logging.INFO)


# Checking arguments
################################################################################
def usage():
    print >> sys.stderr, "Usage: %s builddir config" % sys.argv[0]
    sys.exit(2)


from optparse import OptionParser
parser = OptionParser()
parser.add_option("--excludes", dest="exludes", action="store_true",
                  help="List files to exclude instead",
                  metavar="excludes", default = False)
(options, args) = parser.parse_args()


maxarg = len(args)
if  maxarg < 2:
    print >> sys.stderr, "Missing arguments!"
    usage()

builddir = args[0]
cmtconfig = args[1]

# First checking the config
(prefix, project, version) = BuildDirHelpers.parseBuildDirName(builddir)

filelist = BuildDirHelpers.filterBuildDir(builddir, cmtconfig)
for f in filelist:
    print f.replace(prefix + os.sep, "/opt/lhcb/lhcb/")



