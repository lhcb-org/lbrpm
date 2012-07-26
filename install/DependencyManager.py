'''

DependencyManager

Parsing of YUM metadata files to retrieve the available packages
and their dependencies.

for example to list all versions of BRUNEL in the repository:

  client = LbYumClient(os.environ['MYSITEROOT'])
  for p in client.listRPMPackages("BRUNEL.*"):
        print "%s - %s" % (p.name, p.version)

Created on Jun 29, 2012
@author: Ben Couturier
'''

import xml.dom.minidom
import logging
import gzip
import inspect
import os
import pickle
import re
import urllib

# Constants for directory structure
SVAR = "var"
SCACHE="cache"
SLBYUM ="lbyum"
SETC = "etc"
SLBYUMCONF="lbyum.conf"

# Setting up the logger
log = logging.getLogger()

# Classes representing requirements and functionality provided by RPMs
###############################################################################
class VersionedObject(object):
    """ Ancestor for classes representing all versioned objects (Provides, Requires...)"""

    def __init__(self, name, version, release, epoch, flags):
        """ Constructor for the class """
        self.name = name
        self.version = version
        self.release = release
        self.epoch = epoch
        self.flags = flags
        self.standardVersion = VersionedObject.getStandardVersion(version)

    # Classes used for version comparison
    ###############################################################################
    def eq(self, x):
        return self == x
    def lt(self, x):
        return x < self
    def le(self, x):
        return x <= self
    def gt(self, x):
        return x > self
    def ge(self, x):
        return x >= self

    @classmethod
    def getStandardVersion(cls, version):
        """ parse the version and return the list of major, minor,etc version numbers """

        # First check parameters
        if version == None:
            return None

        # If the version is of the form: x.y.z
        # return an array with version numbers,
        # e.g. [ 1, 23, 45 ]
        # None otherwise.
        # If it is defined it should be used for comparing versions,
        # otherwise the version strings will be compared
        standardVersion = None
        if re.match('\d+(\.\d+)*$', version):
            standardVersion =  [ int(n) for n in version.split(".") ]
        return standardVersion

    @classmethod
    def cmpStandardVersion(cls, v1, v2):
        """ Common method for comparing standard versions as arrays of numbers """
        zippedVers = zip(v1, v2)
        cmplist = [  a-b for (a,b) in zippedVers if a-b != 0]
        if len(cmplist) == 0:
            return 0
        else:
            return cmplist[0]

    def provideMatches(self, provide):
        """ returns true if the provide passed in parameter matches the requirement """
        # Checking the name of course....
        if provide.name != self.name:
            return False

        allmethods = inspect.getmembers(self, predicate=inspect.ismethod)
        foundMethod = None
        for m in allmethods:
            if m[0].lower() == self.flags.lower():
                foundMethod = m[1]
        return(foundMethod(provide))

    def __cmp__(self, other):
        """ Comparison method for dependencies """
        #log.debug("Comparing %s with %s" % (self, other))

        if other == None:
            return -1

        if self.name != other.name:
            return cmp(self.name, other.name)
        else:
            # At this point we can compare the versions
            if self.standardVersion == None or other.standardVersion == None:
                # We couldn't parse the version as a standard x.y.z for both
                # In this case we do string comparison
                return cmp(self.version, other.version)
            else:
                # In this case we can compare the version lists
                cmpVers =  VersionedObject.cmpStandardVersion(self.standardVersion, other.standardVersion)
                if cmpVers != 0:
                    # Versions are different we do not need to compare release numbers
                    return cmpVers
                else:
                    # Comparing down to the release numbers
                    r1 = self.release
                    r2 = other.release

                        # If one is missing a release number they potentially match
                    if not r1 or not r2:
                        return 0

                    if r1.isdigit() and r2.isdigit():
                        return cmp(int(r1), int(r2))
                    else:
                        return cmp(r2, r2)

    # Pretty printing
    ###############################################################################
    def __str__(self):
        """ Display function for the package instance """
        return "%s(%s.%s-%s)" %(self.flags, self.name, self.version, self.release)

    def __repr__(self):
        return self.__str__()


# Classes actually representing the Require and Provide of the RPM Specs
###############################################################################
class Provides(VersionedObject):
    """ Class representing a functionality provided by a package """
    def __init__(self, name, version, release, epoch=None, flags=None, package=None):
        super( Provides, self ).__init__(name, version, release, epoch, flags)
        # Provides can actually know which package they provide for
        # This is useful for looking for packages in the repository
        self.package = package

class Requires(VersionedObject):

    """ Class representing a functionality required by a package """
    def __init__(self, name, version, release, epoch=None, flags="EQ", pre=None):
        super( Requires, self ).__init__(name, version, release, epoch, flags)
        self.pre = pre


# Package: Class representing a package available for installation
###############################################################################
class Package(VersionedObject):

    #
    # Constructor and public method
    ###########################################################################
    def __init__(self):
        """ Default constructor """
        super( Package, self ).__init__(None, None, None, None, None)
        self.group = None
        self.arch = None
        self.location = None
        self.requires = []
        self.provides = []
        self.repository = None

    def setRepository(self, repo):
        self.repository = repo

    def rpmName(self):
        """ Formats the name of the RPM package"""
        return "%s-%s-%s" %( self.name, self.version, self.release)

    def rpmFileName(self):
        """ Formats the name of the RPM package"""
        return "%s-%s-%s.rpm" %( self.name, self.version, self.release)

    def url(self):
        """ Returns the URL to download the file """
        return self.repository.repourl + "/" + self.location

    #
    # Methods for pretty display
    ###########################################################################
    def __repr__(self):
        return self.__str__()

    def __str__(self):
        """ Display function for the package instance """
        tmpstr = "Package: %s-%s-%s\t%s" %( self.name, self.version, self.release, self.group)
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
    # Dependency management
    ###########################################################################
    def getPackagesRequired(self):
        """ Get allpackages needed for installation (including the package itself)"""
        deps = self.getDependencies()
        deps.append(self)
        return deps

    def getDependencies(self):
        """ Get all dependencies for the package (excluding the package itself)"""
        log.info("Checking dependencies for %s.%s-%s" % (self.name, self.version, self.release))
        return self._getpackageDeps()

    def _getpackageDeps(self):
        requires = []
        # Now iterating on all requires to find the matching requirement
        for r in self.requires:
            (reqPackage, reqVersion, reqRelease) = (r.name, r.version, r.release)
            if reqPackage not in self.repository.mIgnoredPackages:
                log.debug("Processing deps %s.%s-%s" % (reqPackage, reqVersion, reqRelease))
                p = self.repository.findPackageMatchingRequire(r)
                if p != None:
                    requires.append(p)
                    for subreq in p._getpackageDeps():
                        if subreq not in requires:
                            requires.append(subreq)
                else:
                    if reqPackage not in self.repository.mIgnoredPackages:
                        log.error("Package %s.%s-%s not found" % (reqPackage, reqVersion, reqRelease))
                        #raise Exception("Package %s.%s-%s not found" % (reqPackage, reqVersion, reqRelease))
        return requires


#
# Package: Class representing a remote repository of RPM package
###############################################################################
class Repository(object):
    """ Class representing a yum repository with all associated metadata"""
    def __init__(self, url, repocachedir):
        # These are hardwired dependencies in RPM.
        # we do not need to care about them...
        self.ignoredPackages = ["rpmlib(CompressedFileNames)", "/bin/sh", "rpmlib(PayloadFilesHavePrefix)", "rpmlib(PartialHardlinkSets)", "DBASE_Gen_DecFiles"]

        # URL of the Yum repository and associated files
        self.repourl = url
        self.repomdurl = self.repourl + "/repodata/repomd.xml"
        self.primaryurl = self.repourl + "/repodata/primary.xml.gz"

        # Cache directory and file names
        self.cachedir = repocachedir
        self.localPrimaryXml = os.path.join(repocachedir, "primary.xml.gz")
        self.localRepomdXml = os.path.join(repocachedir, "repomd.xml")

        # Now initializing the backend
        self.backend = RepositoryXMLBackend(self.localPrimaryXml, self.ignoredPackages)


    # Tools to get the metadat and check whether it is up to date
    ###########################################################################
    def _getLatestPrimary(self):
        log.debug("Downloading latest version of primary.xml.gz")
        urllib.urlretrieve (self.primaryurl, self.localPrimaryXml)

    def _checkRepoUpdates(self):
        """ Checks whether the primary.xml.gz needs updating.
        For that purpose, we need to download and parse the
        file called repomd.xml """
        log.debug("Checking repo metadata for updates")

        if not os.path.exists(self.localPrimaryXml):
            return True

        # First getting the file content
        import urllib2
        response = urllib2.urlopen(self.repomdurl)
        data = response.read()
        response.close()

        # Now parsing to get
        (rchecksum, rtimestamp) = self._checkRepoMD(data)

        # Checking if we have a repomd file at all
        (lchecksum, ltimestamp) = (None, None)
        if os.path.exists(self.localRepomdXml):
            ftmp = open(self.localRepomdXml, 'r')
            (lchecksum, ltimestamp) = self._checkRepoMD( ftmp.read())
            ftmp.close()

        # Now checking if we have a
        needUpdate = False
        if (lchecksum != rchecksum) or  (ltimestamp != rtimestamp):
            needUpdate = True
            ftmp =  open(self.localRepomdXml, 'w')
            ftmp.write(data)
            ftmp.close()

        log.debug("Checking repo metadata for updates returned %s" % needUpdate)
        return needUpdate

    def _checkRepoMD(self, repomdxml, dbtype="primary"):
        """ Method to parse the Repository metadata XML file """
        checksum = None
        timestamp = None
        dom = xml.dom.minidom.parseString(repomdxml)
        for n in dom.documentElement.childNodes:
            if n.nodeType == xml.dom.Node.ELEMENT_NODE and n.tagName=="data":
                if n.getAttribute("type") == dbtype:
                    for nc in n.childNodes:
                        if nc.nodeType == xml.dom.Node.ELEMENT_NODE and nc.tagName=="checksum":
                            checksum = RepositoryXMLBackend._getNodeText(nc)
                        if nc.nodeType == xml.dom.Node.ELEMENT_NODE and nc.tagName=="timestamp":
                            timestamp = RepositoryXMLBackend._getNodeText(nc)
        return (checksum, timestamp)


    #
    # Methods implemented in the backend
    ###########################################################################
    def load(self):
        """ Loads required data into memory """
        self.backend.load()


    def findPackageByName(self, name, version, release=None):
        """ Utility function to locate a package by name """
        return self.backend.findPackageByName(name, version, release)

    def findPackageMatchingRequire(self, requirement):
        """ Utility function to locate a package providing a given functionality """
        return self.backend.findPackageMatchingRequire(requirement)


    def getAllPackages(self, nameMatch=None):
        """ Yields the list of all packages known by the repository """
        return self.backend.getAllPackages(nameMatch)


class RepositoryXMLBackend(object):
    """ Class interfacing with the XML interface provided by Yum repositories """

    #
    # Factory that parses the YUM XML and returns a configured package
    ###########################################################################
    @classmethod
    def fromYumXML(cls, packageNode):
        """ Method that instantiates a correct package instance, based on
        the YUM Metadata XML structure"""

        # First checking the node passed, just in case
        if packageNode.nodeType == xml.dom.Node.ELEMENT_NODE and packageNode.tagName != "package":
            raise Exception("Trying to create Package from wrong node" + str(packageNode))

        p = Package()
        for cn in packageNode.childNodes:
            if cn.nodeType != xml.dom.Node.ELEMENT_NODE:
                continue
            if cn.tagName == "name":
                p.name = RepositoryXMLBackend._getNodeText(cn)
            elif cn.tagName == "arch":
                p.arch = RepositoryXMLBackend._getNodeText(cn)
            elif cn.tagName == "version":
                p.version = cn.getAttribute("ver")
                p.release = cn.getAttribute("rel")
                p.epoch = cn.getAttribute("epoch")
            elif cn.tagName == "location":
                p.location = cn.getAttribute("href")
            elif cn.tagName == "format":
                for fnode in cn.childNodes:
                    if fnode.nodeType != xml.dom.Node.ELEMENT_NODE:
                        continue
                    if fnode.tagName == "rpm:group":
                        p.group =  RepositoryXMLBackend._getNodeText(fnode)
                    if fnode.tagName == "rpm:provides":
                        for dep in fnode.childNodes:
                            if dep.nodeType != xml.dom.Node.ELEMENT_NODE:
                                continue
                            depname = dep.getAttribute("name")
                            depver = dep.getAttribute("ver")
                            deprel = dep.getAttribute("rel")
                            depepoch = dep.getAttribute("epoch")
                            depflags = dep.getAttribute("flags")
                            #p.provides.append((depname, depver, deprel, depepoch, depflags))
                            p.provides.append(Provides(depname, depver, deprel,
                                                       depepoch, depflags, p))
                    if fnode.tagName == "rpm:requires":
                        for dep in fnode.childNodes:
                            if dep.nodeType != xml.dom.Node.ELEMENT_NODE:
                                continue
                            depname = dep.getAttribute("name")
                            depver = dep.getAttribute("ver")
                            deprel = dep.getAttribute("rel")
                            depepoch = dep.getAttribute("epoch")
                            depflags = dep.getAttribute("flags")
                            deppre = dep.getAttribute("pre")
                            #p.requires.append((depname, depver, deprel, depepoch, deppre))
                            p.requires.append(Requires(depname, depver, deprel,
                                                       depepoch, depflags, deppre))

        # Set the "standard version field, used for comparison
        p.standardVersion = VersionedObject.getStandardVersion(p.version)
        # Now return the object back...
        return p

    @classmethod
    def _getNodeText(cls, node):
        """ Gets the value of the first child text node """
        for t in node.childNodes:
            if t.nodeType == xml.dom.Node.TEXT_NODE:
                return t.data

    def __init__(self, primaryfile, ignoredPackages):
        self.mPackages = {}
        self.mProvides = {}
        self.mPackageCount = 0
        self.mPrimary = primaryfile
        self.mIgnoredPackages = ignoredPackages


    def load(self):
        """ Actually load the data """
        self.loadYumMetadataFile(self.mPrimary)

    # Method to load a primary.xml.gz YUM repository file
    ###########################################################################
    def loadYumMetadataFile(self, filename):
        """ Loads the yum XML package list """
        f = gzip.open(filename, 'rb')
        try:
            log.debug("Starting the parsing of the Metadata XML file")
            dom = xml.dom.minidom.parse(f)
            log.debug("Parsing of the Metadata XML file done")
            self.loadYumMetadataDOM(dom)
        except Exception, e:
            log.error("Error while parsing file %s: %s" % (filename, str(e)))
            raise e
        f.close()

    #
    # Method to load a primary.xml.gz YUM repository file
    ###########################################################################
    def loadYumMetadataDOM(self, dom):
        """ Loads the yum XML package list """
        # Finding all packages and adding then to the repository
        log.debug("Starting to iterate though Metadata DOM")
        for n in dom.documentElement.childNodes:
            if n.nodeType == xml.dom.Node.ELEMENT_NODE:
                # Generating the package object from the XML
                p = RepositoryXMLBackend.fromYumXML(n)
                p.setRepository(self)
                # Adding the package to the repository
                self._addPackage(p)
                self._addAllProvides(p)
                self.mPackageCount+= 1
                #log.debug("Added %s package <%s><%s><%s>" % (p.group, p.name, p.version, p.release))

                # Checking the Package type...
                if n.getAttribute("type") != "rpm":
                    log.warning("Package type for %s is %s not RPM" % (p.name, n.getAttribute("type")))

        log.debug("Finished to iterate though Metadata DOM")
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
                allprovides.append(prov)
                self.mProvides[prov.name] = allprovides


    #
    # Public method to look for packages
    ###########################################################################
    def findPackageByName(self, name, version, release=None):
        """ Utility function to locate a package by name """
        package = None
        try:
            availableVersions = self.mPackages[name]
            if availableVersions != None:
                if (version == None or len(version)==0) and len(availableVersions) > 0:
                    # returning latest
                    package = sorted(availableVersions)[-1]
                else:
                    # Trying to match the requirements and what is available
                    r = Requires(name, version, release)
                    matching = [ p for p in availableVersions if r.provideMatches(p) ]
                    if len(matching) > 0:
                        package = sorted(matching)[-1]

        except KeyError:
            log.error("Could not find package %s.%s-%s" % (name, version, release))

        # Checking whether we actually found something
        if package == None:
            log.error("Could not find package %s.%s-%s" % (name, version, release))

        return package

    def findPackageMatchingRequire(self, requirement):
        """ Utility function to locate a package providing a given functionality """

        log.debug("Looking for match for %s" % requirement)
        if requirement == None:
            raise Exception("_findPackageMatchingRequire passed Null requirement")

        package = None
        try:
            availableVersions = self.mProvides[requirement.name]
            if availableVersions != None:
                if (requirement.version == None or len(requirement.version)==0) and len(availableVersions) > 0:
                    availableVersions.sort()
                    # If no version is specified we just return the latest one
                    log.debug("Found %d versions - returning latest: %s" % (len(availableVersions), availableVersions[-1] ))
                    package = availableVersions[-1].package
                else:
                    # Trying to match the requirements and what is available
                    matching = [ p for p in availableVersions if requirement.provideMatches(p) ]
                    if len(matching) > 0:
                        matching.sort()
                        log.debug("Found %d version matching - returning latest: %s" % (len(matching),matching[-1] ))
                        package = matching[-1].package
        except KeyError:
            log.debug("Could not find package providing %s-%s" % (requirement.name, requirement.version))

        if package == None:
            log.debug("Could not find package providing %s-%s" % (requirement.name, requirement.version))
        return package


    def getAllPackages(self, nameMatch=None):
        """ Yields the list of all packages known by the repository """
        for pak_list_k in self.mPackages.keys():
            if nameMatch == None or (nameMatch != None and re.match(nameMatch, pak_list_k) != None):
                for p in self.mPackages[pak_list_k]:
                    yield p


#
# Package: Class representing a remote repository of RPM package
###############################################################################
class LbYumClient(object):

    def getRPMPackage(self, name, version=None, release=None):
        """ Main method for locating packages by RPM name"""
        return self.repository.findPackageByName(name, version, release)

    def listRPMPackages(self, nameRegexp=None, versionRegexp=None, releaseRegexp=None):
        """ List packages available"""
        for p in self.repository.getAllPackages():
                namematch = True
                versionmatch = True
                releasematch = True
                if nameRegexp != None and re.match(nameRegexp, p.name) == None:
                    namematch = False
                if versionRegexp != None and re.match(versionRegexp, p.name) == None:
                    versionmatch = False
                if releaseRegexp != None and re.match(releaseRegexp, p.name) == None:
                    releasematch = False
                if namematch and versionmatch and releasematch:
                    yield p

    def findPackageMatchingRequire(self, requirement):
        """ Main method for locating packages by RPM name"""
        return self.repository.findPackageMatchingRequire(requirement)

    def loadConfig(self):
        """ Look up the location of the yum repository """
        log.debug("Loading the configs from repository: %s" % self.yumreposdir)

        self.repourls = {}
        for f in os.listdir(self.yumreposdir):
            # Checking that we have a file indeed
            log.debug("Checkin config file: %s" % f)
            m = re.match("(.*)\.repo", f)
            if m != None:
                reponame = m.group(1)
                repourl = None
                log.debug("Opening config file for repo: %s" % reponame)
                ycf = open(os.path.join(self.yumreposdir, f), 'r')
                for l in ycf.readlines():
                    m = re.match("baseurl=\s*(.*)\s*$", l)
                    if m != None:
                        repourl = m.group(1)
                        break
                ycf.close()
                if repourl == None:
                    log.warning("Could not read repository URL from %s" % f)
                else:
                    log.info("Found repository %s URL: %s" % (reponame, repourl))
                    self.repourls[reponame] = repourl


        self.configured = True
        if len(self.repourls.keys())==None:
            raise Exception("Could not find repository config in %s" % self.yumreposdir)

        return self.repourls



    def __init__(self, localConfigRoot, checkForUpdates=True):
        """ Constructor for the client """
        # Setting up the variables
        self.localConfigRoot = localConfigRoot
        self.etcdir = os.path.join(localConfigRoot, SETC)
        if not os.path.exists(self.etcdir):
            os.makedirs(self.etcdir)
        self.lbyumcache = os.path.join(localConfigRoot, SVAR, SCACHE, SLBYUM)
        if not os.path.exists(self.lbyumcache):
            os.makedirs(self.lbyumcache)
        self.yumconf = os.path.join(self.etcdir, "yum.conf")
        self.yumreposdir = os.path.join(self.etcdir, "yum.repos.d")
        self.configured = False

        # Loading the config and setting URLs accordingly
        self.loadConfig()
        # At this point self.repourls is a map containing the list of repositories and their URLs

        self.repositories = {}
        for repo in self.repourls.keys():
            # Getting the main parameters for the repository:
            # URL and cache directory
            repourl = self.repourls[repo]
            repocachedir = os.path.join(self.lbyumcache, repo)
            if not os.path.exists(repocachedir):
                os.makedirs(repocachedir)


            r = Repository(repourl, repocachedir)
            if checkForUpdates and r._checkRepoUpdates():
                r._getLatestPrimary()

            # Creating the repository, and loading the XML
            log.debug("Loading the XML repository")
            r.load()

            # Now adding the repository to the map
            self.repositories[repo] = r

        # For compatibility for the moment
        # XXX
        self.repository = self.repositories['lhcb']


if __name__ == '__main__':
    FORMAT = '%(asctime)-15s %(message)s'
    logging.basicConfig(format=FORMAT)
    log.setLevel(logging.DEBUG)

    #client = LbYumClient(mysiteroot)
    #if not os.path.exists(os.path.join(mysiteroot, SETC, SLBYUMCONF)):
    #    client.createConfig("http://linuxsoft.cern.ch/cern/slc6X/x86_64/yum/os")
    #    client = LbYumClient(mysiteroot)

    client = LbYumClient("/scratch/rpmsiteroot")
    #client.createConfig("https://test-lbrpm.web.cern.ch/test-lbrpm/rpm/")
    for p in client.listRPMPackages("BRUNEL.*"):
        print "%s - %s" % (p.name, p.version)

    #p = client.getRPMPackage("BRUNEL_v42r2p1_x86_64_slc5_gcc43_opt", "1.0.0")
    #print p
    #alldeps = p.getDependencies()
    #for dep in alldeps:
        #print "Need: %s %s" % (dep.name, dep.version)
    #    print "Need: %s" % (dep.url())

    #print "There are %d packages in repository" % client.repository.mPackageCount
    #reqCount = 0
    #provCount = 0
    #for plist in client.repository.mPackages.values():
    #    for p in plist:
    #        reqCount += len(p.requires)
    #        provCount += len(p.provides)
    #print "There are %d requires" % reqCount
    #print "There are %d provides" % provCount
    #p = client.getPackage("castor-devel", "2.1.9")
    #alldeps = p.getDependencies()
    #for dep in alldeps:
    #    print "Need: %s %s" % (dep.name, dep.version)

