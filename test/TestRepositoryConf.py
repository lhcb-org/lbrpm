'''
Created on Jul 23, 2012
@author: Ben Couturier
'''
import logging
import os
import unittest
from DependencyManager import LbYumClient, Requires

class TestRepository(unittest.TestCase):

    def setUp(self):
        FORMAT = '%(asctime)-15s %(message)s'
        logging.basicConfig(format=FORMAT)
        import DependencyManager
        DependencyManager.log.setLevel(logging.DEBUG)

    def tearDown(self):
        pass

    def testLoadConfigLocal(self):
        lbYumClient = LbYumClient(os.path.join(os.path.dirname(__file__), "testconfig"), False) # DO NOT CHECK FOR UPADTES
        self.checkClient(lbYumClient)

    def checkClient(self, lbYumClient):
        self.assertEqual(len(lbYumClient.repositories.keys()), 3)
        self.assertEqual(len([ p for p in  lbYumClient.listPackages("BRUNEL")]), 7)
        p = lbYumClient.findLatestMatchingName("ROOT_5.32.02_x86_64_slc5_gcc46_opt")
        self.assertEquals(p.version, "1.0.0")
        self.assertEquals(p.release, "1")

        b = lbYumClient.findLatestMatchingRequire(Requires("BRUNEL_v43r1p1_x86_64_slc5_gcc43_opt", "1.0.0", "1"))
        self.assertEquals(b.name, "BRUNEL_v43r1p1_x86_64_slc5_gcc43_opt")
        self.assertEquals(b.version, "1.0.0")
        self.assertEquals(b.release, "1")

        allrequired = set(['ROOT_5.34.00_x86_64_slc5_gcc43_opt', 'castor_2.1.9_9_x86_64_slc5_gcc43_opt', 'COMPAT', 'CMT',
         'libunwind_5c2cade_x86_64_slc5_gcc43_opt', 'lapack_3.4.0_x86_64_slc5_gcc43_opt',
         'neurobayes_expert_3.7.0_x86_64_slc5_gcc43_opt',
         'cernlib_2006a_x86_64_slc5_gcc43_opt', 'XercesC_3.1.1p1_x86_64_slc5_gcc43_opt', 'Grid_gfal_1.11.8_2_x86_64_slc5_gcc43_opt',
         'DBASE_TCK_L0TCK', 'GAUDI_v23r3_x86_64_slc5_gcc43_opt', 'expat_2.0.1_x86_64_slc5_gcc43_opt',
         'pygraphics_1.2p1_python2.6_x86_64_slc5_gcc43_opt', 'DBASE_TCK_HltTCK', 'CORAL_CORAL_2_3_23_x86_64_slc5_gcc43_opt',
         'qt_4.7.4_x86_64_slc5_gcc43_opt', 'Grid_voms-api-cpp_1.9.17_1_x86_64_slc5_gcc43_opt', 'sqlite_3070900_x86_64_slc5_gcc43_opt',
         'CppUnit_1.12.1_p1_x86_64_slc5_gcc43_opt', 'GSL_1.10_x86_64_slc5_gcc43_opt', 'uuid_1.42_x86_64_slc5_gcc43_opt',
         'QMtest_2.4.1_python2.6_x86_64_slc5_gcc43_opt', 'tcmalloc_1.7p1_x86_64_slc5_gcc43_opt',
         'xqilla_2.2.4_x86_64_slc5_gcc43_opt', 'REC_v14r1p1', 'BRUNEL_v43r1p1', 'gcc_4.3.5_x86_64_slc5',
         'COOL_COOL_2_8_14_x86_64_slc5_gcc43_opt', 'fftw3_3.1.2_x86_64_slc5_gcc43_opt', 'xrootd_3.1.0p2_x86_64_slc5_gcc43_opt',
         'AIDA_3.2.1_common', 'zlib_1.2.5_x86_64_slc5_gcc43_opt', 'LHCB_v35r1p1_x86_64_slc5_gcc43_opt',
         'Grid_cgsi-gsoap_1.3.3_1_x86_64_slc5_gcc43_opt', 'LCGCMT_64_x86_64_slc5_gcc43_opt',
         'Boost_1.48.0_python2.6_x86_64_slc5_gcc43_opt', 'DBASE_FieldMap', 'Python_2.6.5p2_x86_64_slc5_gcc43_opt',
         'PARAM_ParamFiles', 'LBCOM_v13r1p1', 'Grid_LFC_1.7.4_7sec_x86_64_slc5_gcc43_opt',
         'pytools_1.7_python2.6_x86_64_slc5_gcc43_opt', 'COOL_COOL_2_8_14_common', 'pyanalysis_1.3_python2.6_x86_64_slc5_gcc43_opt',
         'LBCOM_v13r1p1_x86_64_slc5_gcc43_opt', 'Grid_globus_4.0.7_VDT_1.10.1_x86_64_slc5_gcc43_opt',
         'RELAX_RELAX_1_3_0h_x86_64_slc5_gcc43_opt', 'oracle_11.2.0.1.0p3_x86_64_slc5_gcc43_opt',
         'dcache_client_2.47.5_0_x86_64_slc5_gcc43_opt', 'DBASE_AppConfig', 'PARAM_ChargedProtoANNPIDParam',
         'HepPDT_2.06.01_x86_64_slc5_gcc43_opt', 'clhep_1.9.4.7_x86_64_slc5_gcc43_opt',
         'Grid_voms-api-c_1.9.17_1_x86_64_slc5_gcc43_opt', 'DBASE_Det_SQLDDDB', 'LCGCMT_LCGCMT_64_common',
         'REC_v14r1p1_x86_64_slc5_gcc43_opt', 'LHCB_v35r1p1', 'GAUDI_v23r3', 'frontier_client_2.8.5_x86_64_slc5_gcc43_opt',
         'graphviz_2.28.0_x86_64_slc5_gcc43_opt', 'HepMC_2.06.05_x86_64_slc5_gcc43_opt', 'LBSCRIPTS', 'CORAL_CORAL_2_3_23_common',
         'fastjet_2.4.4_x86_64_slc5_gcc43_opt', 'Grid_lcg-dm-common_1.7.4_7sec_x86_64_slc5_gcc43_opt',
         'blas_20110419_x86_64_slc5_gcc43_opt',
         'gccxml_0.9.0_20110825_x86_64_slc5_gcc43_opt', 'gcc_4.3.5_x86_64_slc5_gcc43_opt', 'DBASE_FieldMap',
         'BRUNEL_v43r1p1_x86_64_slc5_gcc43_opt'])

        found = set([ p.name for p in lbYumClient.getAllPackagesRequired(b) ])
        self.assertEquals(found, allrequired)

    def testLoadConfigLocalXML(self):
        lbYumClient = LbYumClient(os.path.join(os.path.dirname(__file__), "testconfigNoSQLite"), False)
        self.checkClient(lbYumClient)


#    def testLoadConfigRemote(self):
#        import tempfile
#        import shutil
#        tmpdir = tempfile.mkdtemp()
#        newconf = os.path.join(tmpdir, "testconfig")
#        shutil.copytree(os.path.join(os.path.dirname(__file__), "testconfig"), newconf)
#        lbYumClient = LbYumClient(newconf)
#        self.checkClient(lbYumClient)

