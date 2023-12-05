# imports
import os

from pyworkflow.tests import BaseTest, setupTestProject, DataSet
from defmap.constants import *
from pyworkflow.utils import magentaStr
from defmap.protocols import DefMapNeuralNetwork
from pyworkflow import Config

from pwem.protocols import ProtImportVolumes, ProtImportPdb

class TestDefmap(BaseTest):

    @classmethod
    def setUpClass(cls):
        # setupTestProject(cls)
        # inputVolume = Config.SCIPION_HOME + "/software/em/"+ DEFAULT_SCRIPT_FOLDER + "/data/015_emd_3984_5A_rescaled.mrc"
        # inputAtomicStructure = Config.SCIPION_HOME + "/software/em/"+ DEFAULT_SCRIPT_FOLDER + "/data/015_6ez8.pdb"

        # cls.protImportVol = ProtImportVolumes(filesPath=inputVolume, samplingRate=1.35)
        # cls.launchProtocol(cls.protImportVol)

        # cls.protImportPdb = ProtImportPdb(inputPdbData=1, pdbFile=inputAtomicStructure)
        # cls.launchProtocol(cls.protImportPdb)

        ### 

        setupTestProject(cls)

        cls.ds = DataSet.getDataSet('nma_V2.0')
        # Import Target EM map
        cls.protImportVol = cls.newProtocol(ProtImportVolumes, importFrom=ProtImportVolumes.IMPORT_FROM_FILES,
                                       filesPath=cls.ds.getFile('1ake_vol'),  samplingRate=2.0)
        cls.protImportVol.setObjLabel('inputVolume')
        cls.launchProtocol(cls.protImportVol)

        cls.protImportPdb = cls.newProtocol(ProtImportPdb, inputPdbData=1,
                                         pdbFile=cls.ds.getFile('1ake_pdb'))
        cls.protImportPdb.setObjLabel('inputStructure')
        cls.launchProtocol(cls.protImportPdb)


    def testNothing(self):
        return
    
    def testDefmap1(self):
        # without atomic structure, threshold and resolution
        defmap = self.newProtocol(DefMapNeuralNetwork,
                                     inputVolume=self.protImportVol.outputVolume,
                                     # inputStructure=self.protImportPdb.outputPdb,
                                     )
        self.launchProtocol(defmap)
        self.assertFalse(hasattr(defmap, "outputStructure"))

    def testDefmap2(self):
        # with atomic structure, threshold and resolution
        defmap = self.newProtocol(DefMapNeuralNetwork,
                                     inputVolume=self.protImportVol.outputVolume,
                                     inputStructure=self.protImportPdb.outputPdb,
                                     inputResolution=1,
                                     inputThreshold=0.02
                                     )
        self.launchProtocol(defmap)
        self.assertTrue(hasattr(defmap, "outputStructure"))
