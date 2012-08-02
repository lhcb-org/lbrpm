#!/usr/bin/env python
"""
LHCb Software installer using RPM and YUM
Ben Couturier <ben.couturier@cern.ch>
2012/04/20

Version 1.0

"""
import getopt
import logging
import os
import re
import subprocess
import sys
import time
import traceback
from string import Template

__RCSID__ = "$Id$"


# Checking whether the MYSITEROOT is set correctly
###############################################################################
class LbInstallConfig(object):
    """ Configuration object for the installer. All options and defaults
    should be kept in an isntance of this class """
    
    def __init__(self):
        """ Constructor for the config oobject """
        # Check the mysiteroot
        if not os.environ.has_key("MYSITEROOT"):
            raise LbInstallException("Missing MYSITEROOT variable in the environment.")
        else:
            self.siteroot = os.environ["MYSITEROOT"]
        
        # Debug mode defaults to false
        self.debug = False
        # Default log width
        self.line_size = 120
        # Checking python versions
        self.python_version = sys.version_info[:3]
        self.txt_python_version = ".".join([str(k) for k in self.python_version])
        # version of teh script itself
        self.script_version = '120419'
        # Simple logger by default
        self.log = logging.getLogger()


    def setLogger(self):
        """ Defines a custom logger """
        # Setting the logger
        thelog = logging.getLogger()
        thelog.setLevel(logging.DEBUG)
        console = logging.StreamHandler()
        if self.python_version < (2, 5, 1) :
            console.setFormatter(logging.Formatter("%(levelname)-8s: %(message)s"))
        else :
            if self.debug:
                console.setFormatter(logging.Formatter("%(levelname)-8s: %(funcName)-25s - %(message)s"))
            else :
                console.setFormatter(logging.Formatter("%(levelname)-8s: %(message)s"))
        if self.debug:
            console.setLevel(logging.DEBUG)
        else :
            console.setLevel(logging.INFO)
        thelog.addHandler(console)
        self.log = thelog
        return thelog

# Utility to run a command
###############################################################################
def call(command):
    """ Wraps up subprocess call and return caches and returns rc, stderr, stdout """
    pc = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
    out, err = pc.communicate()
    rc = pc.returncode
    return (rc, out, err)

# Utility to run a command
###############################################################################
def callSimple(command):
    """ Simpler wrapper for subprocess """
    rc = subprocess.call(command, shell=True)
    return rc

# Check for binary in path
###############################################################################
def checkForCommand(command):
    """ Check whether a command is in the path using which """
    whichcmd = "which %s" % command
    rc, out, err = call(whichcmd)
    return rc, out

# Utilities for log printout
###############################################################################
def printHeader(config):
    """ Prints the standard header as in install_project """
    # Start banner
    thelog = config.log
    start_time = time.strftime("%a, %d %b %Y %H:%M:%S", time.localtime())
    thelog.info('=' * config.line_size)
    thelog.info(('<<< %s - Start of lb-install.py %s with python %s >>>' \
                 % (start_time, config.script_version, config.txt_python_version)).center(config.line_size))
    thelog.info('=' * config.line_size)
    thelog.debug("Command line arguments: %s" % " ".join(sys.argv))


def printTrailer(config):
    """ Prints the standard trailer as in install_project """
    # Trailer
    thelog = config.log
    end_time = time.strftime("%a, %d %b %Y %H:%M:%S", time.localtime())
    thelog.info('=' * config.line_size)
    thelog.info(('<<< %s - End of lb-install.py %s >>>' % (end_time, config.script_version)).center(config.line_size))
    thelog.info('=' * config.line_size)

        
# Checking the command line options
###############################################################################
def parseArgs(config):
    """ Process the command line arguments """
    pname = None
    pversion = None
    binary = None
    
    arguments = sys.argv[1:]

    if not arguments :
        raise LbInstallException("Not enough argument passed")

    try:
        opts, args = getopt.getopt(arguments, 'hdb',
            ['help', 'debug', 'binary=', 'repo='])
    except getopt.GetoptError, err:
        raise LbInstallException("Error parsing arguments: " + str(err))


    for key, value in opts:
        if key in ('-d', '--debug'):
            config.debug = True
        if key in ('-h', '--help'):
            usage(sys.argv[0])
        if key == '-b':
            binary = os.environ.get('CMTCONFIG', None)
            if binary == None:
                raise LbInstallException("CMTCONFIG environment variable must be defined if -b is used")
        if key == '--binary':
            binary = value
        if key == '--repo':
            config.repourl = value

    if not pname and len(args) > 0 :
        pname = args[0]
    if pname and pname.find("/") != -1 :
        plist = pname.split("/")
        pname = "/".join(plist[1:])

    if not pversion and len(args) > 1 :
        pversion = args[1]

    return pname, pversion, binary


# Class representing the repository
###############################################################################


class InstallArea(object):
    """ Class representing the software InstallArea,
    with all related actions"""

    # Initialization of the area
    ##########################################################################
    def __init__(self, config):
        """ Init of the InstallArea, check that all directories and config files
        are present.
        """
        
        # Setting the siteroot
        self.siteroot = config.siteroot
        self.config = config
        self.log = config.log

        # Setting the main repository URL
        self.repourl = REPOURL
        self.extrasurl = "/".join([self.repourl, "extras"])
        self.rpmsurl = "/".join([self.repourl, "rpm"])
        
        # prefix for the RPMs
        self.rpmprefix = "/opt/lhcb"
        
        # Making sure the db is initialized
        self.dbpath = os.path.join(self.siteroot, SVAR, SLIB, SRPM)
        self.initRPMDB()

        # Initializing yum config
        self.etc = os.path.join(self.siteroot, SETC)
        self.yumconf = os.path.join(self.etc, "yum.conf")
        self.yumreposd = os.path.join(self.etc, "yum.repos.d")
        self.yumrepolhcb = os.path.join(self.yumreposd, "lhcb.repo")
        self.initYUM()
        
        # tmp directory
        self.tmpdir = os.path.join(self.siteroot, STMP) 
        if not os.path.exists(self.tmpdir):
            os.makedirs(self.tmpdir)            

        # Local bin directory
        self.usrbin =  os.path.join(self.siteroot, SUSR, SBIN)
        if not os.path.exists(self.usrbin):
            os.makedirs(self.usrbin)
        # Add the local bin to the path
        os.environ['PATH'] = os.pathsep.join([os.environ['PATH'], self.usrbin])

        # Defining structures and
        # Checking if all needed tools are available
        self.externalStatus = {}
        self.requiredExternals = [ 'yum', 'rpm', 'yumdownloader' ]
        self.externalFix = {}
        self.externalFix['yumdownloader']  = self._getYumdownloader
        self.checkPrerequisites()
        
        # And if all the software is there
        self.initfile = None
        self.checkRepository()


    def initRPMDB(self):
        """ Initialize RPM database """
        log = self.log
        log.info("RPM DB in %s" % self.dbpath)
        if not os.path.exists(self.dbpath):
            log.info("Creating directory %s for RPM db" % self.dbpath)
            os.makedirs(self.dbpath)
            
        if not os.path.exists(os.path.join(self.dbpath, "Packages")):
            log.info("Initializing RPM db")
            cmd = "rpm --dbpath %s --initdb" % self.dbpath
            log.debug("Command: %s" % cmd)
            rc, stdout, stderr = call(cmd)
            log.debug(stdout)
            log.debug(stderr)
            if rc != 0:
                raise Exception("Error initilializing RPM DB: %s" % stderr)

        
    def initYUM(self):
        """ Initializes yum DB """
        if not os.path.exists(self.etc):
            os.makedirs(self.etc)
        if not os.path.exists(self.yumconf):
            ycf = open(self.yumconf, 'w')
            ycf.write(getYumConf(self.siteroot))
            ycf.close()

        if not os.path.exists(self.yumreposd):
            os.makedirs(self.yumreposd)
        if not os.path.exists(self.yumrepolhcb):
            yplf = open(self.yumrepolhcb, 'w')
            yplf.write(getYumRepo(self.siteroot, self.rpmsurl))
            yplf.close()


    def _getYumdownloader(self):
        """ Downloads the version of yumdownloader from the extras directory
        for systems that miss it """
    
        yumcmd = "yumdownloader"
        url = "/".join([ self.extrasurl, yumcmd])
        ydpath = os.path.join(self.usrbin, yumcmd)
        self.log.info("Downloading %s to %s" % ( url, ydpath) )
        import urllib
        urllib.urlretrieve (url, ydpath)
        os.chmod(ydpath, 0755)

    def checkPrerequisites(self):
        """ Checks that external tools required by this tool to perform
        the installation """

        # Flag indicating whether a crucial external is missing and we cannot run
        externalMissing = False
        
        for e in self.requiredExternals:
            rc, out = checkForCommand(e)
            self.externalStatus[e] = (rc, out)

        for key, val in self.externalStatus.items():
            rc, exefile = val
            if rc == 0:
                self.log.info("%s: Found %s", key, exefile.strip())
            else:
                self.log.info("%s: Missing - trying compensatory measure", key)
                fix = self.externalFix[key]
                if fix != None:
                    fix()
                    rc2, out2 = checkForCommand(key)
                    self.externalStatus[key] = (rc2, out2)
                    if rc2 == 0:
                        self.log.info("%s: Found %s", key, out2)
                    else:
                        self.log.error("%s: missing", key)
                        externalMissing = True
                else:
                    externalMissing = True
        return externalMissing
    

    def checkRepository(self):
        """ Checks whether the repository was initialized """
        self.initfile = os.path.join(self.etc, "repoinit")
        if not os.path.exists(self.initfile):
            self.installRpm("LBSCRIPTS")
            fini = open(self.initfile, "w")
            fini.write(time.strftime("%a, %d %b %Y %H:%M:%S", time.localtime()))
            fini.close()
        else:
            self._yumcheckupdate()
            
    # Pass through commands to RPM and yum
    ##########################################################################    
    def rpm(self, args):
        """ Wrapper for invocation of RPM """
        install_mode = False
        query_mode = False
        for arg in args:
            if arg.startswith("-i"):
                install_mode = True
            if arg.startswith("-q"):
                query_mode = True

        rpmcmd = "rpm --dbpath %s " % self.dbpath
        if not query_mode and install_mode :
            rpmcmd += " --prefix %s " % self.siteroot
        rpmcmd += " ".join(args)

        self.log.info("RPM command:")
        self.log.info(rpmcmd)

        rc = callSimple(rpmcmd)
        return rc

    def yum(self, args, yumusercommand="yum"):
        """ Wrapper for invocation of YUM  """
        yumcmd = "%s -c %s  " % (yumusercommand, self.yumconf)
        yumcmd += " ".join(args)
        print yumcmd
        rc, stdout, stderr = call(yumcmd)
        print stdout
        print stderr
        return rc

    # Various utility methods to download/check RPMs
    ##########################################################################
    def _checkRpmFile(self, filename):
        """ Checks the integrity of an RPM file """
        ret = False
        rpmcmd = "rpm -K %s " % filename
        self.log.debug("RPM command:")
        self.log.debug(rpmcmd)
        rc, stdout, stderr = call(rpmcmd)
        self.log.debug("Call returned %s %s" % (stdout, stderr))
        if rc == 0:
            ret = True
        return ret

        
    def _parseyumoutputline(self, line):
        """ Parse a line with the format:
        DBASE_Det_SQLDDDB.noarch           7.5.0-0    lhcb"""
        ret = None
        ma = re.match("\s*([\w\.\_\-]+)\s+([\w\.\_\-]+)\s+([\w\.\_\-]+)\s*", line)
        if ma != None:
            tmp = ma.group(1)
            version = ma.group(2)
            group = ma.group(3)
            name, arch = tmp.rsplit('.', 1)
            ret = [name, version, arch, group]
        return ret
        
    def _yumcheckupdate(self):
        """ Check if updates are available using yum check-update"""
        ydcmd = "yum -c %s  " % self.yumconf
        ydcmd += " check-update"

        self.log.debug("Running: %s" % ydcmd)
        rc, stdout, stderr = call(ydcmd)

        updates = []
        if rc == 100:
            # This means we have files to get,
            # parse the output...
            for li in stdout.splitlines():
                # Hack checking whether we have the used group names
                # lhcb or lcg in the list
                if li.find("lhcb") > 0 or li.find("lcg")>0:
                    ma = self._parseyumoutputline(li)
                    if ma != None:
                        self.log.info("Need to update to %s %s %s" % (ma[0], ma[1], ma[2]))
                        updates.append("%s-%s.%s" %(ma[0], ma[1], ma[2]))
        elif rc != 0:
            self.log.error(stderr)
            raise Exception("Problem checking for updates: %s" % stderr)

        if len(updates) > 0:
            print "#### Planning to update:"
            for updt in updates:
                print "#### %s" % updt
        

    def _yumfindpackage(self, name, version, cmtconfig):
        """ Find all the packages matching a triplet name, version, config """

        # Preparing command
        ydcmd = "yum -c %s  " % self.yumconf
        ydcmd += " list"
        ydcmd = ["yum", "-c", self.yumconf, "list" ]

        # making sure CMTCONFIG is in right format
        if cmtconfig != None:
            cmtconfig = cmtconfig.replace("-", "_")

        # Now calling the command and finding matches
        matches = []
        pc = subprocess.Popen(ydcmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        for line in pc.stdout:
            line = line.strip()
            self.log.debug("yum list: %s" % line)
            name_match = False
            version_match = False
            config_match = False
            if re.search(name, line, re.IGNORECASE) != None:
                name_match = True
                
            if version == None or (version != None and re.search(version, line, re.IGNORECASE) != None):
                version_match = True
            
            if cmtconfig == None or (cmtconfig != None and re.search(cmtconfig, line, re.IGNORECASE) != None):
                config_match = True

            self.log.debug("Match: %s %s %s" % ( name_match, version_match, config_match))
            if name_match and version_match and config_match:
                ma = self._parseyumoutputline(line)
                if ma != None:
                    self.log.debug("Foun match %s %s %s" % (ma[0], ma[1], ma[2]))
                    matches.append("%s-%s.%s" %(ma[0], ma[1], ma[2]))

        # Sorting and checking which one to install
        if len(matches) > 1:
            # First case, we need to eliminate all the entries with a cmt config !
            # in this case the rpm name should be NAME_version-X.Y.Z....
            m2 = [ x for x in matches if re.match("%s_%s-" % (name, version), x, re.IGNORECASE) != None ]
            if len(m2) > 0:
                matches = [ sorted(m2)[-1] ]
            else:
                matches = m2
                
        return matches

    def _getdownloadurls(self, filename):
        """ Uses yum to list the URLs for RPMs to download """
        ydcmd = "yumdownloader -c %s  " % self.yumconf
        ydcmd += " --quiet --resolve --urls --destdir=%s " % self.tmpdir
        ydcmd += filename
        self.log.debug("Running: %s" % ydcmd)
        rc, stdout, stderr = call(ydcmd)
        
        if rc != 0:
            if len(stderr) > 0:
                self.log.error(stderr)
                raise Exception("Problem finding dependency: %s" % stderr)
            else:
                # Case if the file just wasn't found
                raise LbInstallException("Could not find file %s in repository" % filename)

        # Normally yumdownloader will return the list of urls
        urls = []
        for li in stdout.splitlines():
            # Ignore lines starting with "-" as they are logs
            # printed out, even in quiet mode.
            # Only keeps URLs, starting with http or file, in practice
            url = li.strip()
            if url.startswith("http") or url.startswith("ftp"):
                urls.append(url.strip())
        return urls

    def _filterUrlsAlreadyInstalled(self, urls):
        """ Filter out RPMs already installed """
        toinstall = []
        for url in urls:
            # Establishing the filename
            (pre, filename) = url.rsplit("/", 1)
            self.log.debug("Prefix: %s" % pre)
            name, suffix = filename.rsplit(".", 1)
            self.log.debug("Suffix: %s" % suffix)
            self.log.info("Checking for installation of: %s", name)
            if not self._isRpmInstalled(name):
                toinstall.append(url)
            else:
                self.log.warning("Already installed: %s will not download and install again" % name)
        return toinstall

    def _downloadfiles(self, urls, location):
        """ Downloads a list of files """
        import urllib
        files = []
        for url in urls:
            # Establishing the filename
            (pre, filename) = url.rsplit("/", 1)
            self.log.debug("Prefix: %s" % pre)            
            full_filename = os.path.join(location, filename)
            files.append(filename)

            # Checking if file is there and is ok
            needs_download = True
            if os.path.exists(full_filename):
                fileisok = self._checkRpmFile(full_filename)
                if fileisok:
                    needs_download = False

            # Now doing the download
            if not needs_download:
                self.log.warn("%s already exists, will not download" % filename)
            else:
                self.log.info("Downloading %s to %s" % (url, full_filename))
                urllib.urlretrieve (url, full_filename)
        return files

    def _installfiles(self, files, rpmloc):
        """ Install some rpm files given the location of the RPM DB """
        fulllist = [ os.path.join(rpmloc, f) for f in files ]
        args = [ "-ivh " ] + fulllist
        rc = self.rpm(args)
        if rc != 0:
            raise Exception("Error installing rpms")


    def _isRpmInstalled(self, rpmname):
        """ Checks whether a given RPM apckage is already installed """
        installed = False
        rpmcmd = [ 'rpm',  '--dbpath', self.dbpath, '-q', rpmname ]
        self.log.debug("RPM command:" + " ".join(rpmcmd))
        rc, stdout, stderr = call(" ".join(rpmcmd))
        self.log.debug("rpm -q out/err: %s / %s" % ( stdout, stderr))
        if rc == 0:
            installed = True
        return installed

    # Methods to download/install RPMs (replacement for yum install)
    ##########################################################################
    def install(self, project, version, cmtconfig):
        """ Perform the whole download/install procedure (equivalent to
        yum install """
        # Looking for the package
        rpmname = None
        matches = self._yumfindpackage(project, version, cmtconfig)
        self.log.info("Found %d matches" % len(matches))
        for ma in matches:
            self.log.info("Found RPM: %s" % ma)
        if len(matches) == 0:
            self.log.error("No matching file found - EXITING")
            raise LbInstallException("No matching file found")
        if len(matches) > 1:
            self.log.error("Multiple files found - EXITING")
            raise LbInstallException("Too many matching file found")

        # Taking the first (and only) entry from the list
        rpmname = matches[0]
                  
        # Now installing the RPM
        if self._isRpmInstalled(rpmname):
            self.log.warning("%s already installed" % rpmname)
        else:
            self.installRpm(rpmname)
                
    def installRpm(self, rpmname):
        """ install a specific RPM, checking if not installed already """
        self.log.info("Installing %s and dependencies" % rpmname)

        # Checking what files shoudl be downlaoded using yumdownloader
        urls = self._getdownloadurls(rpmname)
        self.log.info("Found %d RPMs to install" % len(urls))
        if len(urls) == 0:
            raise Exception("Error: No files to download")

        # Now filtering the urls to only keep the onles not already
        # installed. This shouldn't happen but it seems that this
        # happens sometimes with yum...
        furls = self._filterUrlsAlreadyInstalled(urls)

        # Now getting the files...
        files = self._downloadfiles(furls, self.tmpdir)
        
        # And installing
        self._installfiles(files, self.tmpdir)    


# Generators for the YumConfigurations
##########################################################################
def getYumConf(siteroot):
    """ Builds the Yum configuration from template """
    cfile = Template("""
[main]
#CONFVERSION 0001
cachedir=/var/cache/yum
debuglevel=2
logfile=/var/log/yum.log
pkgpolicy=newest
distroverpkg=redhat-release
tolerant=1
exactarch=1
obsoletes=1
plugins=1
gpgcheck=0
installroot=${siteroot}
reposdir=/etc/yum.repos.d
""").substitute(siteroot=siteroot)
    return cfile

def getYumRepo(siteroot, url):
    """ Builds the Yum repository configuration from template """
    cfile = Template("""
[lhcb]
#REPOVERSION 0001
name=LHCb
baseurl=$url
enabled=1
""").substitute(siteroot=siteroot, url=url)
    return cfile


# Usage for the script
###############################################################################
def usage(cmd) :
    """ Prints out how to use the script... """
    cmd = os.path.basename(cmd)
    print """\n%(cmd)s -  install a project in the MYSITEROOT directory'
    
Th environment variable MYSITEROOT MUST be set for this script to work.
It can be used in the followoing way:

%(cmd)s [-d][-b] <project> <version>
This installs a LHCb project, with the binaries if -b is specified.

%(cmd)s install <rpmname>
Installs a RPM from the yum repository

%(cmd)s rpm <rpm options>
Pass through mode where the command is delegated to RPM (with the correct DB)

%(cmd)s yum <yum options>
Pass through mode where the command is delegated to YUM (with the correct DB)

""" % { "cmd" : cmd } 


# Buil RPM name from triplet project, version, cmtconfig
###############################################################################
def buildRPMName(project, version, cmtconfig):
    """ Builds the name of the RPM file based on the install_project equivalent
    parameters """
    
    name = None
    if cmtconfig == None:
        name = project.upper() + "_" + version
    else:
        name = project.upper() + "_" + version + "_" + cmtconfig.replace("-", "_")
    return name

# Class for known install exceptions
###############################################################################
class LbInstallException(Exception):
    """ Custom exception for lb-install """
    
    def __init__(self, msg):
        """ Constructor for the exception """
        super(LbInstallException, self).__init__(msg)


# Main method for the tool  
###############################################################################
MODE_INSTALL = "install"
MODE_INSTALLRPM = "installrpm"
MODE_RPM     = "rpm"
MODE_YUM     = "yum"

# Constants for the dir names
SVAR = "var"
SLIB = "lib"
SRPM = "rpm"
SETC = "etc"
STMP = "tmp"
SUSR = "usr"
SBIN = "bin"

# Default repository URL
REPOURL = "http://test-lbrpm.web.cern.ch/test-lbrpm/"

def main():
    """ Main method for the comamnd """
    rc = 0
    mode = MODE_INSTALL 
    try:
        # Creating the config object
        config = LbInstallConfig()


        # Parsing first argument to check the mode
        args = sys.argv
        yumusercommand = "yum"
        if len(args) > 1:
            if args[1].lower() == "rpm":
                mode = MODE_RPM
            elif args[1].lower().startswith("yum"):
                # This mode allows passthough of yum util comands (like
                # yumdownloader)
                mode = MODE_YUM
                yumusercommand = args[1]
            elif args[1].lower() == "install":
                mode = MODE_INSTALLRPM
            
        # Now executing the command
        if mode == MODE_RPM:
            # Mode that passes the arguments to the local RPM
            log = config.setLogger()
            installArea = InstallArea(config)
            rc = installArea.rpm(args[2:])
        elif mode == MODE_YUM:
            # Mode that passes the arguments to the local YUM
            log = config.setLogger()
            installArea = InstallArea(config)
            rc = installArea.yum(args[2:], yumusercommand)
        elif mode == MODE_INSTALLRPM:
            # Mode where the comamnds are installed by name
            log = config.setLogger()
            installArea = InstallArea(config)
            rc = installArea.installRpm(args[2])
        else:
            # In this case we are in normal install mode
            pname, pversion, binary = parseArgs(config)

            # Initializing the logger, Printing the log header
            log = config.setLogger()
            printHeader(config)

            # Lg
            log.info("Proceeding to the installation of %s/%s/%s" % (pname, pversion, binary))
            
            # Creating the install area object
            installArea = InstallArea(config)
            installArea.install(pname, pversion, binary)
            printTrailer(config)
    except LbInstallException, lie:
        print >> sys.stderr, "ERROR: " + str(lie)
        usage(sys.argv[0])
        rc = 1
    except:
        print >> sys.stderr, "Exception in lb-install:"
        print >> sys.stderr, '-'*60
        traceback.print_exc(file=sys.stderr)
        print >> sys.stderr, '-'*60
        rc = 1
    return rc



if __name__ == "__main__":
    sys.exit(main())

