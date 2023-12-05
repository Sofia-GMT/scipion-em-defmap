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
        protImportVol = cls.newProtocol(ProtImportVolumes, importFrom=ProtImportVolumes.IMPORT_FROM_FILES,
                                       filesPath=cls.ds.getFile('1ake_vol'),  samplingRate=2.0)
        protImportVol.setObjLabel('EM map')
        cls.launchProtocol(protImportVol)

        cls.protImportVol = protImportVol
        cls.protPdb4ake = cls.newProtocol(ProtImportPdb, inputPdbData=1,
                                         pdbFile=cls.ds.getFile('4ake_aa_pdb'))
        cls.protPdb4ake.setObjLabel('Input PDB')
        cls.launchProtocol(cls.protPdb4ake)


    def testNothing(self):
        return
    
    def testDefmapOk(self):
        defmap = self.newProtocol(DefMapNeuralNetwork,
                                     inputVolume=self.protImportVol.outputVolume,
                                     inputStructure=self.protImportPdb.outputPdb,
                                     )
        self.launchProtocol(defmap)
        self.assertTrue(hasattr(defmap, "outputStructure"))
