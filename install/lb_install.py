#!/usr/bin/env python
"""
LHCb Software installer using RPM and YUM
Ben Couturier <ben.couturier@cern.ch>
2012/04/20

Version 1.0

"""
import inspect
import logging
import optparse
import os
import subprocess
import sys
import time
import traceback

# Constants for the dir names
SVAR = "var"
SLIB = "lib"
SRPM = "rpm"
SETC = "etc"
STMP = "tmp"
SUSR = "usr"
SBIN = "bin"

__RCSID__ = "$Id$"

# Default repository URL
REPOURL = "http://test-lbrpm.web.cern.ch/test-lbrpm"

# Checking whether the MYSITEROOT is set correctly
###############################################################################
class LbInstallConfig(object): #IGNORE:R0903
    """ Configuration object for the installer. All options and defaults
    should be kept in an instance of this class """

    def __init__(self):
        """ Constructor for the config object """
        # Get the default siteroot
        self.siteroot = os.environ.get("MYSITEROOT", None)
        # And the default repository URL
        self.repourl = REPOURL
        # Debug mode defaults to false
        self.debug = False
        # Version of the scripts
        self.script_version = "080812"
        # Default log width
        self.line_size = 120
        # Checking python versions
        self.python_version = sys.version_info[:3]
        self.txt_python_version = ".".join([str(k) for k in self.python_version])
        # Simple logger by default
        self.log = logging.getLogger()

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
    rc, out, err = call(whichcmd) #@UnusedVariable IGNORE:W0612
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

# Class representing the repository
###############################################################################
class InstallArea(object): # IGNORE:R0902
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
        self.log = logging.getLogger(__name__)

        # Setting the main repository URL
        self.repourl = config.repourl
        self.extrasurl = "/".join([self.repourl, "extras"])
        self.rpmsurl = "/".join([self.repourl, "rpm"])
        self.lcgsurl = "/".join([self.repourl, "lcg"])
        self.lhcbsurl = "/".join([self.repourl, "lhcb"])

        self.log.info("Repository is: %s" % self.repourl)

        # prefix for the RPMs
        self.rpmprefix = "/opt/lhcb"

        # Making sure the db is initialized
        self.dbpath = os.path.join(self.siteroot, SVAR, SLIB, SRPM)
        self._initRPMDB()

        # Initializing yum config
        self.etc = os.path.join(self.siteroot, SETC)
        self.yumconf = os.path.join(self.etc, "yum.conf")
        self.yumreposd = os.path.join(self.etc, "yum.repos.d")
        self.yumrepolhcb = os.path.join(self.yumreposd, "lhcb.repo")
        self.yumrepolcg = os.path.join(self.yumreposd, "lcg.repo")

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

        # Local lib directory
        self.lib =  os.path.join(self.siteroot, SLIB)
        if not os.path.exists(self.lib):
            os.makedirs(self.lib)
        # Add the local bin to the path
        sys.path.append(self.lib)
        # We keep config files compatible with YUM,
        # even though we use the DependencyManager client
        self._initYUM()
        from DependencyManager import LbYumClient
        self.lbYumClient = LbYumClient(self.siteroot)

        # Defining structures and
        # Checking if all needed tools are available
        self.externalStatus = {}
        self.requiredExternals = [ 'rpm' ]
        self.externalFix = {}
        self._checkPrerequisites()

        # And if all the software is there
        self.initfile = None
        self._checkRepository()

    def _initRPMDB(self):
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
                raise Exception("Error initializing RPM DB: %s" % stderr)

    def _initYUM(self):
        """ Initializes yum configuration.
        Still in use as LbYum uses a compatible configuration """
        if not os.path.exists(self.etc):
            os.makedirs(self.etc)
        if not os.path.exists(self.yumconf):
            ycf = open(self.yumconf, 'w')
            ycf.write(InstallArea._getYumConf(self.siteroot))
            ycf.close()

        if not os.path.exists(self.yumreposd):
            os.makedirs(self.yumreposd)
        if not os.path.exists(self.yumrepolhcb):
            yplf = open(self.yumrepolhcb, 'w')
            yplf.write(InstallArea._getYumRepo("lhcbold", self.rpmsurl))
            yplf.write(InstallArea._getYumRepo("lhcb", self.lhcbsurl))
            yplf.close()
        if not os.path.exists(self.yumrepolcg):
            yplf = open(self.yumrepolcg, 'w')
            yplf.write(InstallArea._getYumRepo("lcg", self.lcgsurl))
            yplf.close()

    def _checkPrerequisites(self):
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

    def _checkRepository(self):
        """ Checks whether the repository was initialized """
        self.initfile = os.path.join(self.etc, "repoinit")
        if not os.path.exists(self.initfile):
            self.installRpm("LBSCRIPTS")
            fini = open(self.initfile, "w")
            fini.write(time.strftime("%a, %d %b %Y %H:%M:%S", time.localtime()))
            fini.close()
        else:
            self._checkupdate()

    # Pass through commands to RPM and lbYum
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

    def listpackages(self, args):
        """ Wrapper for invocation of RPM """
        nameRegexp = None
        if len(args) > 0:
            nameRegexp = args[0]

        totalMatching = 0
        for pa in self.lbYumClient.listPackages(nameRegexp):
            print pa.rpmName()
            totalMatching += 1
        print "Total Matching: %d" % totalMatching

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

    def _findpackage(self, name, version, cmtconfig):
        """ Find all the packages matching a triplet name, version, config """
        pname = name.upper()
        pnameVer = None
        pnameVerConfig = None
        if version != None:
            pnameVer = pname + "_" + version
        else:
            pnameVer = pname
        if cmtconfig != None:
            pnameVerConfig = pnameVer + "_" + cmtconfig.replace("-", "_")
        else:
            pnameVerConfig = pnameVer

        from DependencyManager import Requires
        req = Requires(pnameVerConfig, None, None, None, "GT", None)
        pack = self.lbYumClient.findLatestMatchingRequire(req)
        return [ pack ]

    def _filterUrlsAlreadyInstalled(self, packages):
        """ Filter out RPMs already installed """
        toinstall = []
        for pack  in packages:
            # Establishing the filename
            self.log.info("Checking for installation of: %s", pack.rpmName())
            if not self._isRpmInstalled(pack.rpmName()):
                toinstall.append(pack)
            else:
                self.log.warning("Already installed: %s will not download and install again" % pack.rpmName())
        return toinstall

    def _downloadfiles(self, installlist, location):
        """ Downloads a list of files """
        import urllib
        files = []
        for pack in installlist:
            filename = pack.rpmFileName()
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
                self.log.info("Downloading %s to %s" % (pack.url(), full_filename))
                urllib.urlretrieve (pack.url(), full_filename)
        return files

    def _installfiles(self, files, rpmloc, forceInstall=False):
        """ Install some rpm files given the location of the RPM DB """
        fulllist = [ os.path.join(rpmloc, f) for f in files ]
        args = [ "-ivh --oldpackage " ]
        if forceInstall:
            args.append("--force ")
        args = args + fulllist
        rc = self.rpm(args)
        if rc != 0:
            raise Exception("Error installing rpms")

    def _isRpmInstalled(self, rpmname, rpmversion=None):
        """ Checks whether a given RPM apckage is already installed """
        installed = False
        fullname = rpmname
        if rpmversion != None:
            fullname = rpmname + "." + rpmversion
        rpmcmd = [ 'rpm',  '--dbpath', self.dbpath, '-q', fullname  ]
        self.log.debug("RPM command:" + " ".join(rpmcmd))
        rc, stdout, stderr = call(" ".join(rpmcmd))
        self.log.debug("rpm -q out/err: %s / %s" % ( stdout, stderr))
        if rc == 0:
            installed = True
        return installed

    def _listInstalledPackages(self):
        """ Checks whether a given RPM apckage is already installed """
        rpmcmd = [ 'rpm',  '--dbpath', self.dbpath, '-qa',  '--queryformat',  '%{NAME} %{VERSION} %{RELEASE}\n'  ]
        self.log.debug("RPM command:" + " ".join(rpmcmd))

        # Shold be improved to yield line per line instead of reading it all in block
        pc = subprocess.Popen(rpmcmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        out, err = pc.communicate() #@UnusedVariable IGNORE:W0612
        rc = pc.returncode

        if rc != 0:
            raise LbInstallException("Error reading the list of packages from RPM DB")
        return [ l.split(" ") for l in out.splitlines() ] #IGNORE:E1103

    def _checkupdate(self):
        """ Check whether packages could be updated in the repository """
        from DependencyManager import Requires
        for lp in self._listInstalledPackages():
            (name, version, release) = lp
            # Creating a RPM requirement and checking whether we have a match...
            req = Requires(name, version, release, None, "GT", None)
            update = self.lbYumClient.findLatestMatchingRequire(req)
            if update != None:
                self.log.warning("%s.%s-%s could be updated to %s" % (name, version, release, update.rpmName()))

    # Methods to download/install RPMs (replacement for yum install)
    ##########################################################################
    def install(self, project, version, cmtconfig):
        """ Perform the whole download/install procedure (equivalent to
        yum install """
        # Looking for the package
        self.log.info("Installing %s/%s/%s" % (project, version, cmtconfig))
        matches = self._findpackage(project, version, cmtconfig)
        self.log.info("Found %d matches" % len(matches))
        for ma in matches:
            self.log.info("Found RPM: %s" % ma.rpmName())
        if len(matches) == 0:
            self.log.error("No matching file found - EXITING")
            raise LbInstallException("No matching file found")
        if len(matches) > 1:
            self.log.error("Multiple files found - EXITING")
            raise LbInstallException("Too many matching file found")

        # Taking the first (and only) entry from the list
        package = matches[0]
        # Now installing the RPM
        if self._isRpmInstalled(package.rpmName()):
            self.log.warning("%s already installed" % package.rpmName())
        else:
            self.installPackage(package)

    def installRpm(self, rpmname, version=None, forceInstall=False):
        """ Install an RPM by name """
        pack = self.lbYumClient.findLatestMatchingName(rpmname, version)
        if pack == None:
            raise Exception("Package %s/%s not found" % (rpmname, version))

        self.installPackage(pack, forceInstall)

    def installPackage(self, package, forceInstall = False):
        """ install a specific RPM, checking if not installed already """
        self.log.info("Installing %s and dependencies" % package.rpmName())

        # Checking what files should be downloaded
        installlist = self.lbYumClient.getAllPackagesRequired(package)
        self.log.info("Found %d RPMs to install" % len(installlist))
        if len(installlist) == 0:
            raise Exception("Error: No files to download")

        # Now filtering the urls to only keep the onles not already
        # installed. This shouldn't happen but it seems that this
        # happens sometimes with yum...
        finstalllist = self._filterUrlsAlreadyInstalled(installlist)

        # Now getting the files...
        files = self._downloadfiles(finstalllist, self.tmpdir)

        # And installing
        self._installfiles(files, self.tmpdir, forceInstall)

    # Generators for the YumConfigurations
    ##########################################################################
    @classmethod
    def _getYumConf(cls, siteroot):
        """ Builds the Yum configuration from template """
        cfile = """
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
installroot={siteroot}
reposdir=/etc/yum.repos.d
    """.format(siteroot=siteroot)
        return cfile

    @classmethod
    def _getYumRepo(cls, name, url):
        """ Builds the Yum repository configuration from template """
        cfile = """
[{name}]
#REPOVERSION 0001
name={name}
baseurl={url}
enabled=1
""".format( url=url, name=name )
        return cfile

# Class for known install exceptions
###############################################################################
class LbInstallException(Exception):
    """ Custom exception for lb-install """

    def __init__(self, msg):
        """ Constructor for the exception """
        super(LbInstallException, self).__init__(msg)

# Classes and method for command line parsing
###############################################################################
class LbInstallOptionParser(optparse.OptionParser): #IGNORE:R0904
    """ Custom OptionParser to intercept the errors and rethrow
    them as lbInstallExceptions """

    def error(self, msg):
        raise LbInstallException("Error parsing arguments: " + str(msg))

    def exit(self, status=0, msg=None):
        raise LbInstallException("Error parsing arguments: " + str(msg))

class MainClient(object):
    """ Ancestor for both clients, the new one and the one
    compatible with install project arguments """
    def __init__(self, arguments=None, dryrun=False):
        """ Common setup for both clients """
        self.config = LbInstallConfig()
        self.log = logging.getLogger(__name__)
        self.arguments = arguments
        self.dryrun = dryrun
        self.installArea = None
        self.runMethod = None
        self.runArgs = None

        parser = LbInstallOptionParser()
        parser.add_option('-d', '--debug',
                            dest="debug",
                            default=False,
                            action="store_true",
                            help="Show debug information")
        parser.add_option('--repo',
                            dest="repourl",
                            default=None,
                            action="store",
                            help="Specify repository URL")
        parser.add_option('--root',
                            dest="siteroot",
                            default=None,
                            action="store",
                            help="Specify MYSITEROOT on the command line")
        parser.add_option('--dryrun',
                            dest="dryrun",
                            default=False,
                            action="store",
                            help="Only print the command that will be run")
        self.parser = parser

    def main(self):
        """ Main method for the ancestor:
        call parse and run in sequence """
        rc = 0
        try:
            opts, args = self.parser.parse_args(self.arguments)
            # Checkint the siteroot and URL
            # to choose the siteroot
            if opts.siteroot != None:
                self.config.siteroot = opts.siteroot
                os.environ['MYSITEROOT'] = self.config.siteroot

            if opts.repourl != None:
                self.config.repourl = opts.repourl

            # Now setting the logging depending on debug mode...
            if self.config.debug:
                logging.basicConfig(format="%(levelname)-8s: %(funcName)-25s - %(message)s")
                logging.getLogger().setLevel(logging.DEBUG)

            # Checking if we should do a dry-run
            self.dryrun = self.dryrun or opts.dryrun

            # Getting the function to be invoked
            (runMethod, runArgs) = self.prepareRun(opts, args)
            self.runMethod = runMethod
            self.runArgs = runArgs

            if not self.dryrun:
                # Initializing the install area
                self.installArea = InstallArea(self.config)
                # Find the method instance in the InstallArea
                allmethods = inspect.getmembers(self.installArea, inspect.ismethod)
                found = [ m[1] for m in allmethods if m[0] == runMethod ]
                if len(found) != 1:
                    raise LbInstallException("Could not find method %s in InstallArea" % runMethod)
                # And invoke it...
                found[0](*runArgs) #IGNORE:W0142
            else:
                self.log.info("DRYRUN: %s %s" % (runMethod, " ".join(args)))
            self.postRun()

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

    def prepareRun(self, opts, args):
        """ Hook called before invocation """
        raise NotImplementedError()

    def postRun(self):
        """ Hook called after invocation """
        raise NotImplementedError()

class LbInstallClient(MainClient):
    """ Client following new syntax """

    MODE_INSTALLRPM = "install"
    MODE_RPM     = "rpm"
    MODE_LIST    = "list"
    MODES = [    MODE_INSTALLRPM, MODE_RPM, MODE_LIST ]

    def __init__(self, arguments=None, dryrun=False):
        super(LbInstallClient, self).__init__(arguments, dryrun)
        self.parser.disable_interspersed_args()
        self.log = logging.getLogger(__name__)

    def prepareRun(self, opts, args):
        """ Main method for the command """

        runMethod = None
        runArgs = []

        # Parsing first argument to check the mode
        if len(args) > 0:
            cmd = args[0].lower()
            if cmd in LbInstallClient.MODES:
                mode = cmd
            else:
                raise LbInstallException("Unrecognized command: %s" % args)
        else:
            raise LbInstallException("Argument list too short")

        # Now executing the command
        if mode == LbInstallClient.MODE_RPM:
            # Mode that passes the arguments to the local RPM
            runMethod = "rpm"
            runArgs = [ args[1:] ]
        elif mode == LbInstallClient.MODE_LIST:

            # Mode that list packages according to a regexp
            runMethod = "listpackages"
            runArgs = [ args[1:] ]
        elif mode == LbInstallClient.MODE_INSTALLRPM:
            # Mode where the comamnds are installed by name
            rpmname = args[1]
            version = None
            if len(args) > 2:
                version = args[2]
            runMethod = "installRpm"
            runArgs =  [rpmname, version ]
        return (runMethod, runArgs)

    def postRun(self):
        # No callback needed in this case
        pass

class InstallProjectClient(MainClient):
    """ Backwards compatibility for install_project """

    def __init__(self, arguments=None, dryrun=False):
        super(InstallProjectClient, self).__init__(arguments, dryrun)
        self.log = logging.getLogger(__name__)
        # Adding the binary option for install project compatibility
        self.parser.add_option('--binary',
                        dest="binary",
                        default=None,
                        action="store",
                        help="Download binary package as well as source")
        self.parser.add_option('-b',
                        dest="useCMTCONFIG",
                        default=False,
                        action="store_true",
                        help="Download binary package matching environment CMTCONFIG")

    def prepareRun(self, opts, args):
        """ Main method for the command """

        (pname, pversion, pconfig) = (None, None, None)
        # Check options to see whether we need the binary packages
        if opts.binary != None:
            pconfig = opts.binary
        elif opts.useCMTCONFIG:
            cmtconfig = os.environ.get('CMTCONFIG', None)
            if cmtconfig != None:
                pconfig = cmtconfig
            else:
                raise LbInstallException("CMTCONFIG environment variable must be defined if -b is used")

        # Check the arguments to see if we have project/package and version
        if len(args) == 0:
            raise LbInstallException("Please specify project [version]")
        else:
            pname = args[0]
        if len(args) > 1:
            pversion = args[1]

        # Starting normal install project output
        printHeader(self.config)
        log = self.log
        log.info("Proceeding to the installation of %s/%s/%s" % (pname, pversion, pconfig))
        # Creating the install area object
        runMethod = "install"
        runArgs = [ pname, pversion, pconfig ]
        return (runMethod, runArgs)

    def postRun(self):
        """ Callback after actual execution """
        printTrailer(self.config)

def selectClient(args):
    """ Chooses which client to select depending on coomand name and command line"""
    retclient = LbInstallClient

    if len(args) > 0 and args[0] == "install_project.py":
        retclient = InstallProjectClient
    else:
        cmdlist = [cmd for cmd in args if cmd in LbInstallClient.MODES]
        if len(cmdlist) == 0:
            retclient = InstallProjectClient
    return retclient

# Usage for the script
###############################################################################
def usage(cmd) :
    """ Prints out how to use the script... """
    cmd = os.path.basename(cmd)
    print """\n%(cmd)s -  install a project in the MYSITEROOT directory'

Th environment variable MYSITEROOT MUST be set for this script to work.
It can be used in the following way:

%(cmd)s [-d][-b] <project> <version>
This installs a LHCb project, with the binaries if -b is specified.

%(cmd)s install <rpmname>
Installs a RPM from the yum repository

%(cmd)s rpm <rpm options>
Pass through mode where the command is delegated to RPM (with the correct DB)

%(cmd)s yum <yum options>
Pass through mode where the command is delegated to YUM (with the correct DB)

""" % { "cmd" : cmd }

# Main just chooses the client and starts it
if __name__ == "__main__":
    logging.basicConfig(format="%(levelname)-8s: %(message)s")
    logging.getLogger().setLevel(logging.INFO)
    client = selectClient(sys.argv)
    sys.exit(client().main())
