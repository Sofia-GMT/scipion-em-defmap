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

        cls.ds = DataSet.getDataSet('resmap')
        # Import Target EM map
        cls.protImportVol = cls.newProtocol(ProtImportVolumes, importFrom=ProtImportVolumes.IMPORT_FROM_FILES,
                                       filesPath=cls.ds.getFile('betagal'),  samplingRate=2.0)
        cls.protImportVol.setObjLabel('EM map')
        cls.launchProtocol(cls.protImportVol)

        # cls.protImportVol = protImportVol
        # cls.protImportPdb = cls.newProtocol(ProtImportPdb, inputPdbData=1,
        #                                  pdbFile=cls.ds.getFile('pdb'))
        # cls.protImportPdb.setObjLabel('Input PDB')
        # cls.launchProtocol(cls.protImportPdb)


    def testNothing(self):
        return
    
    def testDefmapOk(self):
        defmap = self.newProtocol(DefMapNeuralNetwork,
                                     inputVolume=self.protImportVol.outputVolume,
                                     # inputStructure=self.protImportPdb.outputPdb,
                                     )
        self.launchProtocol(defmap)
        self.assertTrue(hasattr(defmap, "outputStructure"))
