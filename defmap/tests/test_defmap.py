# imports

from pyworkflow.tests import BaseTest, setupTestProject
from defmap.constants import *
from defmap.protocols import DefMapNeuralNetwork
from pyworkflow import Config

from pwem.protocols import ProtImportVolumes, ProtImportPdb

class TestDefmap(BaseTest):

    @classmethod
    def setUpClass(cls):
        pdbFile = Config.SCIPION_HOME + "/plugins/scipion-em-defmap/defmap/tests/5lij.pdb"
        mrcFile = Config.SCIPION_HOME + "/plugins/scipion-em-defmap/defmap/tests/emd_4054.mrc"

        setupTestProject(cls)

        # Imports for test 1 and  2

        cls.protImportMap = cls.newProtocol(ProtImportVolumes, importFrom=ProtImportVolumes.IMPORT_FROM_EMDB,
                                       emdbId='4054')
        cls.protImportMap.setObjLabel('inputVolume - map')
        cls.launchProtocol(cls.protImportMap)

        cls.protImportCif = cls.newProtocol(ProtImportPdb, inputPdbData=0,
                                         pdbId='5lij')
        cls.protImportCif.setObjLabel('inputStructure - cif')
        cls.launchProtocol(cls.protImportCif)

        # Imports for test 3

        cls.protImportMrc = cls.newProtocol(ProtImportVolumes, importFrom=ProtImportVolumes.IMPORT_FROM_FILES,
                                       filesPath=mrcFile, samplingRate="1.38")
        cls.protImportMrc.setObjLabel('inputVolume - mrc')
        cls.launchProtocol(cls.protImportMrc)


        cls.protImportPdb = cls.newProtocol(ProtImportPdb, inputPdbData=1,
                                         pdbFile=pdbFile)
        cls.protImportPdb.setObjLabel('inputStructure - pdb')
        cls.launchProtocol(cls.protImportPdb)


    def testNothing(self):
        return
    
    def testDefmap1(self):
        defmap = self.newProtocol(DefMapNeuralNetwork,
                                     inputVolume=self.protImportMap.outputVolume,
                                    #  inputThreshold=0.02
                                     )
        self.launchProtocol(defmap)
        self.assertTrue(hasattr(defmap, "outputStructureVoxel"))
        self.assertFalse(hasattr(defmap, "outputStructure"))

    def testDefmap2(self):
        defmap = self.newProtocol(DefMapNeuralNetwork,
                                     inputVolume=self.protImportMap.outputVolume,
                                     inputStructure=self.protImportCif.outputPdb
                                     )
        self.launchProtocol(defmap)
        self.assertTrue(hasattr(defmap, "outputStructureVoxel"))
        self.assertTrue(hasattr(defmap, "outputStructure"))

    def testDefmap3(self):
        defmap = self.newProtocol(DefMapNeuralNetwork,
                                     inputVolume=self.protImportMrc.outputVolume,
                                     inputStructure=self.protImportPdb.outputPdb,
                                     inputResolution=1
                                     )
        self.launchProtocol(defmap)
        self.assertTrue(hasattr(defmap, "outputStructureVoxel"))
        self.assertTrue(hasattr(defmap, "outputStructure"))
