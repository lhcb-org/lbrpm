#!/usr/bin/env python
"""
Command to create a test RPM
"""

import logging
import os
import subprocess
import sys

__RCSID__ = "$Id"

log = logging.getLogger()
log.addHandler(logging.StreamHandler())
log.setLevel(logging.INFO)

local_directory = os.path.dirname(__file__).strip()
os.environ['PATH'] =  os.pathsep.join([os.environ['PATH'], local_directory])

# Util method to prepare the command
################################################################################
def addDefine(param, val):
    """ Util method to add a define statement"""
    if val == None or val == '':
        val = '""'
    return " --define '%s %s' " % (param, val)


# Checking arguments
################################################################################
def usage():
    """ Display help"""
    print >> sys.stderr, "Usage: %s name version release" % sys.argv[0]
    sys.exit(2)

from optparse import OptionParser
parser = OptionParser()
parser.add_option("--requires", dest="requires", action="store",
                  help="Name the file with the list of requires",
                  metavar="REQUIRES", default = None)
parser.add_option("--buildarea", dest="buildarea", action="store",
                  help="Location where the RPM is build",
                  default = "/tmp/buildarea")
(options, args) = parser.parse_args()

if  len(args) < 3:
    print >> sys.stderr, "Missing arguments!"
    usage()

# We allow the hat and package name to be passed separated by
# spaces, this makes scripts invoking simpler in some cases
(name, version, release) = args[0:3]

log.info("Creating <%s> <%s> <%s>" % (name, version, release))
buildarea = options.buildarea

cmd = "rpmbuild -v"
cmd += addDefine("build_area", buildarea)
cmd += addDefine("name", name)
cmd += addDefine("version", version)
cmd += addDefine("release", release)
cmd += " -bb " + os.path.join(local_directory, "LHCb_TestRPM.spectemplate")

log.info("Running: %s" % cmd)
rc = subprocess.call(cmd, shell=True)



