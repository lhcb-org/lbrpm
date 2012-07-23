'''
Created on Jun 29, 2012

@author: Ben Couturier
'''

import xml.dom.minidom
import logging
import gzip
import re

log = logging.getLogger()
logging.basicConfig()
log.setLevel(logging.DEBUG)

# Classes representing requirements and functionality provided by RPMs
###############################################################################
class BaseDependency(object):
    """ Ancestor for classes representing RPM Provides and Require"""
    
    def __init__(self, name, version, release, epoch, flags):
        self.name = name
        self.version = version
        self.release = release
        self.epoch = epoch
        self.flags = flags
 
        # If the version is of the form: x.y.z
        # self.standardVersion contains an array with version numbers,
        # e.g. [ 1, 23, 45 ]
        # None otherwise.
        # If it is defined it should be used for comparing versions,
        # otherwise the version strings will be compared
        if re.match('\d+(\.\d+)*$', self.version):
            self.standardVersion =  [ int(n) for n in self.version.split(".") ]      
        else:
            self.standardVersion = None
        

    def __cmp__(self, other):
        """ Comparison method for dependencies """
        print "=======> cmp called with ", other
        # First check the objects types and package names   
        if type(self) != type(other):
            return cmp(type(self), type(other))
        else:
            if self.name != other.name:
                return cmp(self.name, self.other)
            else:
                # At this point we can compare the versions
                if self.standardVersion == None or other.standardVersion == None:
                    # We couldn't parse the version as a standard x.y.z
                    # In this case we do string comparison
                    return cmp(self.version, other.version)
                else:
                    # In this case we can compare the version lists
                    zippedVers = zip(self.standardVersion, other.standardVersion)
                    cmplist = [  a-b for (a,b) in zippedVers if a-b != 0]
                    if len(cmplist) == 0:
                        return 0
                    else:
                        return cmplist[0]                

class Provides(BaseDependency):
    
    def __init__(self, name, version, release, epoch=None, flags=None):
        super( Provides, self ).__init__(name, version, release, epoch, flags)

class Requires(BaseDependency):
    
    def __init__(self, name, version, release, epoch=None, flags=None, pre=None):
        super( Requires, self ).__init__(name, version, release, epoch, flags)
        self.pre = pre
        
        
# Package: Class representing a package available for installation
###############################################################################
class Package(object):

    @classmethod
    def fromYumXML(cls, packageNode):
        """ Method that instantiates a correct package instance, based on
        the YUM Metadata XML structure"""

        # First checking the node passed, just in case
        if packageNode.nodeType == xml.dom.Node.ELEMENT_NODE and packageNode.tagName != "package":
            raise Exception("Trying to create Package from wrong node" + str(packageNode))

        p = Package()
        for cn in packageNode.childNodes:
            if cn.tagName == "name":
                p.name = Package._getNodeText(cn)
            elif cn.tagName == "arch":
                p.arch = Package._getNodeText(cn)
            elif cn.tagName == "version":
                p.version = cn.getAttribute("ver")
                p.rel = cn.getAttribute("rel")
                p.epoch = cn.getAttribute("epoch")
            elif cn.tagName == "location":
                p.location = cn.getAttribute("href")
            elif cn.tagName == "format":
                for fnode in cn.childNodes:
                    if fnode.tagName == "rpm:group":
                        p.group =  Package._getNodeText(fnode)
                    if fnode.tagName == "rpm:provides":
                        for dep in fnode.childNodes:
                            depname = dep.getAttribute("name")
                            depver = dep.getAttribute("ver")
                            deprel = dep.getAttribute("rel")
                            depepoch = dep.getAttribute("epoch")
                            depflags = dep.getAttribute("flags")
                            #p.provides.append((depname, depver, deprel, depepoch, depflags))
                            p.provides.append(Provides(depname, depver, deprel, 
                                                       depepoch, depflags))
                    if fnode.tagName == "rpm:requires":
                        for dep in fnode.childNodes:
                            depname = dep.getAttribute("name")
                            depver = dep.getAttribute("ver")
                            deprel = dep.getAttribute("rel")
                            depepoch = dep.getAttribute("epoch")
                            depflags = dep.getAttribute("flags")
                            deppre = dep.getAttribute("pre")
                            #p.requires.append((depname, depver, deprel, depepoch, deppre))
                            p.requires.append(Requires(depname, depver, deprel, 
                                                       depepoch, depflags, deppre))
                            
        # Finally return the newly create package
        return p

    @classmethod
    def _getNodeText(cls, node):
        """ Gets the value of the first child text node """
        for t in node.childNodes:
            if t.nodeType == xml.dom.Node.TEXT_NODE:
                return t.data


    def __init__(self):
        """ Default constructor """
        self.group = None
        self.name = None
        self.arch = None
        self.version = None
        self.release = None
        self.epoch = None
        self.location = None
        self.requires = []
        self.provides = []

    def getProvideVersion(self, provideName):
        """ Returns the version that the package provides for a given
        capability"""
        pversion = None
        for p in self.provides:
            if p[0] == provideName:
                pversion = p[1]
        return pversion

    def __repr__(self):
        return self.__str__()

    def __str__(self):
        """ Display function for the package instance """
        tmpstr = "=== %s-%s-%s\t%s" %( self.name, self.version, self.release, self.group)
        if len(self.provides) > 0:
            tmpstr += "\nProvides:\n"
            for p in self.provides:
                tmpstr += "\t%s-%s-%s\n" % (p.name, p.version, p.release)
        if len(self.requires) > 0:
            tmpstr += "\nRequires:\n"
            for p in self.requires:
                tmpstr += "\t%s-%s-%s\t%s\n" % (p.name, p.version, p.release, p.flags)
        return tmpstr


#
# Package: Class representing a remote repository of RPM package
###############################################################################
class Repository(object):
    """ Class representing a yum repository with all associated metadata"""
    def __init__(self):
        self.mPackages = {}
        self.mProvides = {}
        self.mIgnoredPackages = ["rpmlib(CompressedFileNames)", "/bin/sh", "rpmlib(PayloadFilesHavePrefix)", "rpmlib(PartialHardlinkSets)", "DBASE_Gen_DecFiles"]

    #
    # Method to load a primary.xml.gz YUM repository file
    ###########################################################################
    def loadYumMetadata(self, filename):
        """ Loads the yum XML package list """
        #f = open(filename, "r")
        # parsing the file
        f = gzip.open(filename, 'rb')
        try:
            dom = xml.dom.minidom.parse(f)

            # Finding all packages and adding then to the repository
            for n in dom.documentElement.childNodes:
                if n.nodeType == xml.dom.Node.ELEMENT_NODE:
                    # Generating the package object from the XML
                    p = Package.fromYumXML(n)

                    # Adding the package to the repository
                    self._addPackage(p)
                    self._addAllProvides(p)

                    log.debug("Added %s package <%s><%s><%s>" % (p.group, p.name, p.version, p.rel))

                    # Checking the Package type...
                    if n.getAttribute("type") != "rpm":
                        log.warning("Package type for %s is %s not RPM" % (p.name, n.getAttribute("type")))
        except Exception, e:
            log.error("Error while parsing file %s: %s" % (filename, str(e)))
            raise e
        f.close()

    #
    # Public method to lookup dependencies for a package
    ###########################################################################
    def getDependencies(self, packageName, version):

        log.info("Check dependencies for %s/%s" % (packageName, version))
        p = self._findPackageByNameVer(packageName, version)
        alldeps = self._getpackageDeps(p)
        return alldeps
    
    #
    # Private methods to update repository
    ###########################################################################
    def _addPackage(self, package):
        """ Adds a package to the repository global list """
        try:
            allversions = self.mPackages[package.name]
        except KeyError:
            allversions = []
        allversions.append(package)
        self.mPackages[package.name] = allversions

    def _addAllProvides(self, package):
        """ Adds a package to the map with the list of provides """
        for prov in package.provides:
            if prov.name not in self.mIgnoredPackages:
                try:
                    allprovides = self.mProvides[prov.name]
                except KeyError:
                    allprovides = []
                allprovides.append(package)
                self.mProvides[prov.name] = allprovides

    #
    # Private methods to track needed packages
    ###########################################################################
    def _findPackageByNameVer(self, packageName, version):
        """ Utility function to locate a package by name """

        package = None
        try:
            availableVersions = self.mPackages[packageName]
            if availableVersions != None:
                if (version == None or len(version)==0) and len(availableVersions) > 0:
                    # TODO: GET THE LASTEST instead of the first
                    package = availableVersions[0]
                for p in availableVersions:
                    if p.version == version:
                        package = p
        except KeyError:
            log.error("Could not find package %s-%s" % (packageName, version))
        return package

    #
    # Private methods to track needed packages
    ###########################################################################
    def _findPackageByProvide(self, provide, version, release = None):
        """ Utility function to locate a package providing a given functionality """

        package = None
        try:
            availableVersions = self.mProvides[provide]
            if availableVersions != None:
                if (version == None or len(version)==0) and len(availableVersions) > 0:
                    # To do: GET THE LASTEST instead of the first
                    package = availableVersions[0]
                for p in availableVersions:
                    if p.version == version:
                        package = p
        except KeyError:
            log.error("Could not find package providing %s-%s" % (provide, version))
        return package


    def _getpackageDeps(self, package):
        requires = []
        # These are hardwired dependencies in RPM.
        # we do not need to care about them...
        # Now iterating on all requires to find the matching requirement
        for r in package.requires:
            (reqPackage, reqVersion) = (r.name, r.version)
            if reqPackage not in self.mIgnoredPackages:
                log.debug("Processing deps %s/%s for package: %s/%s" % (reqPackage, reqVersion, package.name, package.version))
                p = self._findPackageByProvide(reqPackage, reqVersion)
                if p != None:
                    requires.append(p)
                    for subreq in self._getpackageDeps(p):
                        if subreq not in requires:
                            requires.append(subreq)
                else:
                    if reqPackage not in self.mIgnoredPackages:
                        raise Exception("Package %s-%s not found" % (p[0], p[1]))
        return requires

#
# Package: Class representing a remote repository of RPM package
###############################################################################
class LbYumClient(object):
    
    def __init__(self):
        
        # Setting up the variables
        self.repourl = "https://test-lbrpm.web.cern.ch/test-lbrpm/rpm/"
        self.remotePrimaryXml = self.repourl + "repodata/primary.xml.gz"
        self.localPrimaryXml = "/home/lben/primary.xml.gz"
        
        # Creating the repository, and loading the XML
        self.repository = Repository()
        self.repository.loadYumMetadata(self.localPrimaryXml)
        
    def getDependencies(self, packageName, version):
        alldeps = self.repository.getDependencies(packageName, version)
        for dep in alldeps:
            print "Need: %s %s" % (dep.name, dep.version)
        
if __name__ == '__main__':
    #r = Repository()
    #r.loadYumMetadata("/afs/cern.ch/work/b/bcouturi/www/rpm/repodata/primary.xml.gz")
    #r.loadYumMetadata("/home/lben/primary.xml.gz")
    
    client = LbYumClient()
    #client.getDependencies("DAVINCI_v30r2p3_x86_64_slc5_gcc46_opt", "1.0.0")
    r = client.repository
    for p in r.mProvides.keys():
        l = r.mProvides[p]
        if len(l) > 1:
            print len(l), p
            for pa in sorted(l):
                print "%s - %s\n" % (pa.name, pa.version)
                
        
        
    #r.getDependencies("DAVINCI_v30r2p3_x86_64_slc5_gcc46_opt", "1.0.0")
