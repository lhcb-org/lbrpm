'''
Created on Jul 31, 2012

@author: Ben Couturier
'''

import os
import re
import sys


def parseversion(version):

    m = re.match("v(\d+)r(\d+)$", version)
    if m != None:
        majv = m.group(1)
        minv = m.group(2)
        return  (int(majv), int(minv), None)
    else:
        m = re.match("v(\d+)r(\d+)p(\d+)$", version)
        if m != None:
            majv = m.group(1)
            minv = m.group(2)
            patch = m.group(3)
            return  (int(majv), int(minv), int(patch))
        else:
            raise Exception("Could not parse version %s" % version)

def tuplevertostr(version):
    (majv, minv, patchv) = version
    if patchv == None:
        return "v%dr%d" % (majv, minv)
    else:
        return  "v%dr%dp%d" % version


def parseFileName(fullfilename):
    """" Parse a filename and returns a tuple with teh components """

    # Checking file extension
    if "." in fullfilename:
        tmp = fullfilename.split(".")
        filename = tmp[0]
        extension = tmp[1]
    else:
        filename = fullfilename
        extension = None


    # Now splitting project/[hat]/package/version
    parts = filename.split("_")
    project = parts[0]
    version= parts[-1]

    if len(parts) == 3:
        hat = None
        package = parts[1]
    elif len(parts) ==4:
        hat = parts[1]
        package = parts[2]
    else:
        raise Exception("Could not parse filename: %s" % fullfilename)

    return (project, hat, package, version, extension)



def findAll(tardir):
    availableVersions = {}
    for f in os.listdir(tardir):
        if re.match(".*\.tar\.gz$", f):
            try:
                (project, hat, package, version, extension) = parseFileName(f)
                if hat == None:
                    tname = "_".join([ project, package ])
                else:
                    tname = "_".join([ project, hat,  package ])

                pver = parseversion(version)
                # Adding to the list
                try:
                    l = availableVersions[tname]
                    if l == None:
                        l = []
                    l.append(l.append(pver))
                    availableVersions[tname] = l
                except KeyError:
                    availableVersions[tname] = [ pver ]
            except Exception, e:
                print >> sys.stderr, 'Error with %s, ignoring' %f, e

    return availableVersions

if __name__ == '__main__':
    #list = [ "v1r3", "v2r4", "v10r1", "v2r4p1", "v6r7" ]
    #plist = [ parseversion(v) for v in list ]
    #print sorted(list)
    #print sorted(plist)
    tardir = os.path.join(os.environ['LHCBTAR'], 'DBASE')
    allversions = findAll(tardir)
    for k in allversions.keys():
        l = allversions[k]
        goodver = tuplevertostr(sorted(l)[-1])
        print "createDataPackageRpm %s %s" % (k.replace("_", " "), goodver)

    tardir = os.path.join(os.environ['LHCBTAR'], 'PARAM')
    allversions = findAll(tardir)
    for k in allversions.keys():
        l = allversions[k]
        goodver = tuplevertostr(sorted(l)[-1])
        print "createDataPackageRpm %s %s" % (k.replace("_", " "), goodver)
