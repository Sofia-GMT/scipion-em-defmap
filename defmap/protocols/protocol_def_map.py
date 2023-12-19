# -*- coding: utf-8 -*-
# **************************************************************************
# *
# * Authors:     Sofía González Matatoros (sofia.gonzalezm@estudiante.uam.es)
# *
# * Centro Nacional de Biotecnología CNB - Universidad Autónoma de Madrid UAM
# *
# * This program is free software; you can redistribute it and/or modify
# * it under the terms of the GNU General Public License as published by
# * the Free Software Foundation; either version 2 of the License, or
# * (at your option) any later version.
# *
# * This program is distributed in the hope that it will be useful,
# * but WITHOUT ANY WARRANTY; without even the implied warranty of
# * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# * GNU General Public License for more details.
# *
# * You should have received a copy of the GNU General Public License
# * along with this program; if not, write to the Free Software
# * Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA
# * 02111-1307  USA
# *
# *  All comments concerning this program package may be sent to the
# *  e-mail address 'scipion@cnb.csic.es'
# *
# **************************************************************************


"""
Protocol to run DefMap neural network
"""

from pyworkflow.protocol import Protocol, params, constants
from pyworkflow.utils import Message, logger
from os import path, rename, readlink, symlink
from pyworkflow import Config
from defmap import Plugin
from defmap.constants import *
from pwem.objects import AtomStruct
from pwem.convert.atom_struct import cifToPdb
from pwem.emlib.image import ImageHandler
import pyworkflow.utils as pwutils
from pathlib import Path


class DefMapNeuralNetwork(Protocol):

    @classmethod
    def getClassPackageName(cls):
        return "defmap"

    _label = 'Defmap prediction'
    _possibleOutputs = {'outputStructure': AtomStruct, 'outputStructureVoxel':AtomStruct}

    # -------------------------- INPUT PARAMETERS ----------------------
    def _defineParams(self, form):
        """ 
        Params:
            * form: this is the form to be populated with sections and params.
            * inputVolume: previously generated/imported volumes.
            * structure: imported atomic structure of the protein to analyse.
            * resolution: resolution model for the inference step. Options: 5A, 6A o 7A.
            * threshold: top threshold to drop sub-voxels with a standardized intensity.
        """
        form.addHidden(params.GPU_LIST, params.StringParam, default='',
                       expertLevel=constants.LEVEL_ADVANCED,
                       label='Choose GPU IDs',
                       help="GPU may have several cores. Set it to zero"
                            " if you do not know what we are talking about."
                            " First core index is 0, second 1 and so on.")

        form.addSection(label=Message.LABEL_INPUT)

        form.addParam('inputVolume', params.PointerParam,
                      label='Volume', important=True,
                      help='3D reconstruction of the microscopy images. They must be scaled.',
                      pointerClass="Volume",
                      allowsPointers=True)

        form.addParam('inputStructure', params.PointerParam,
                      label='Atomic structure', allowsNull=True,
                      help='Atomic structure of the molecule',
                      pointerClass="AtomStruct",
                      allowsPointers=True)

        form.addParam('inputResolution', params.EnumParam,
                      label='Resolution',
                      help='Resolution model for the inference step. There are three models according to three possible resolutions',
                      default=0, choices=["5 Å","6 Å","7 Å"]),
        
        # form.addParam('inputThreshold', params.FloatParam,
        #                 allowsNull=True, important = False,
        #                 label='Threshold',
        #                 help='Top threshold to drop voxels with a standardized intensity.\n'
        #                       'If not given, a threshold of 0 will be used for visualization.')

    # --------------------------- STEPS ------------------------------
    def _insertAllSteps(self):
        self._insertFunctionStep('validateFormats')
        self._insertFunctionStep('createDatasetStep')
        self._insertFunctionStep('inferenceStep')
        self._insertFunctionStep('postprocStepVoxel')
        self._insertFunctionStep('postprocStepPdb')
        self._insertFunctionStep('createOutputStep')

    def validateFormats(self):

        self.resultsFolder = path.abspath(self.getWorkingDir()) + "/extra"

        # validate volumes

        volumesName = self.inputVolume.get().getFileName()

        if self.checkExtension(volumesName, ".mrc"):
            self.obtainLink(self.volumesLocation, self.getResult('volumes') )
        else:
            raise Exception('The extension of the volumes is not supported')

        # validate atomic structure

        if self.inputStructure.hasValue() :
            filename = self.inputStructure.get().getFileName()
            if self.checkExtension(filename,".pdb"):
                self.obtainLink(self.structureLocation, self.getResult('atomic-structure') )

            else:
                raise Exception('The extension of the atomic structure is not suported')

    def createDatasetStep(self):

        # Set arguments to create-dataset command
        
        args = [
                '-m "%s"' % self.getResult('volumes'),
                '-o "%s"' % self.getResult('dataset'),
                '-p' 
                ]

        # if self.inputThreshold.hasValue():
        #     args.append('-t %f ' % self.inputThreshold)

        # Execute create-dataset
        createDatasetCommand ="python prep_dataset.py"
        
        self._enterDir(self.getScriptLocation("create-dataset-folder"))
        self.runJob(Plugin.getEnvActivationCommand() + "&& " + createDatasetCommand, ' '.join(args))

    def inferenceStep(self):

        # Get path to trained model

        trainedModelLocation = self.getScriptLocation(str(self.inputResolution))

        # Set arguments to infer command

        args = [
                'infer',
                '-t "%s"' % self.getResult('dataset'),
                '-p "%s"' % self.getResult('prediction'),
                '-o "%s"' % trainedModelLocation
                ]
        
        if self.gpuList.get() != '':
            args.append('-g "%s"' % self.gpuList.get())

        # execute inference

        inferenceCommand = "python " + self.getScriptLocation("inference")

        self._enterDir(self.getScriptLocation(""))
        self.runJob(Plugin.getEnvActivationCommand() + "&& " + inferenceCommand, ' '.join(args))

    def postprocStepVoxel(self):

        # Set arguments to Postprocessing command
        args = [
                '-m "%s"' % self.getResult('volumes'),
                '-p "%s"' % self.getResult('prediction')
                ]
        
        # if self.inputThreshold.hasValue():
        #     args.append('-t %f ' % self.inputThreshold)
        # else:
        args.append('-t 0.0')

        command = "python " + self.getScriptLocation("postprocessing-voxel")

        # call command

        self._enterDir(self.getScriptLocation("postprocessing-folder"))
        self.runJob(Plugin.getEnvActivationCommand() + "&& " + command, ' '.join(args))

        # move result to working directory

        rename("volumes.pdb", self.getResult('output-voxel'))


    def postprocStepPdb(self):

        if(self.inputStructure.hasValue()):

            # Prepare the file that points to the Atomic Structure and the Volumes

            pointerFileLocation = self.resultsFolder + "/sample_for_visual.list"

            with open(pointerFileLocation,"w") as pointerFile:
                pointerFile.write("structure.pdb volumes.mrc")

            # Set arguments to Postprocessing command
            args = [
                    '-l "%s"' % pointerFileLocation,
                    '-p "%s"' % self.getResult('prediction'),
                    '-n'
                    ]

            command = "python " + self.getScriptLocation("postprocessing-pdb")

            # call command

            self._enterDir(self.getScriptLocation("postprocessing-folder"))
            self.runJob(Plugin.getEnvActivationCommand() + "&& " + command, ' '.join(args))

            # move result to working directory

            rename(path.abspath('defmap_norm_model.pdb'), self.getResult('output-pdb'))
        
        else:
            logger.info("No Atomic Structure detected - only visualization by voxels")

        
    
    def createOutputStep(self):
        self.voxelFileName = self.getResult("output-voxel")
        self.pdbFileName = self.getResult("output-pdb")

        if path.exists(self.pdbFileName) and path.exists(self.voxelFileName):
            outputPdbVoxel = AtomStruct()
            outputPdbVoxel.setFileName(self.voxelFileName)
            self.definePdbOutput(outputPdbVoxel)

        elif path.exists(self.voxelFileName):
            outputPdbVoxel = AtomStruct()
            outputPdbVoxel.setFileName(self.voxelFileName)
            self._defineOutputs(outputStructure=None,outputStructureVoxel=outputPdbVoxel)

        elif path.exists(self.pdbFileName):
            self.definePdbOutput()

        else:
            self._defineOutputs(outputStructure=None, outputStructureVoxel=None)
        
        logger.info("Results in %s" % self.resultsFolder)

    def definePdbOutput(self,otherStructure = None):
        outputPdb = AtomStruct()
        outputPdb.setFileName(self.pdbFileName)
        self._defineOutputs(outputStructure=outputPdb,outputStructureVoxel=otherStructure)

        # create file with pymol commands:
        pointerFileLocation = self.resultsFolder + "/pointer_for_pymol.pml"

        with open(pointerFileLocation,"w") as pointerFile:
            pointerFile.write("load " + self.pdbFileName + "\n"
                                "spectrum b, blue_white_red \n"
                                "cartoon tube")

    
    # --------------------------- UTILS functions -----------------------------------

    def getScriptLocation(self,step=None):

        commonPath = Config.SCIPION_HOME + "/software/em/"+ DEFAULT_SCRIPT_FOLDER
        specificPath = ""

        if step == "create-dataset-folder":
            specificPath = "/preprocessing"

        elif step == "inference" :
            specificPath = "/3dcnn_main.py"

        elif step == "0":
            specificPath="/model/model_res5A.h5"

        elif step == "1":
            specificPath="/model/model_res6A.h5"

        elif step == "2":
            specificPath="/model/model_res7A.h5"

        elif step == "postprocessing-pdb":
            specificPath = "/postprocessing/rmsf_map2model_for_defmap.py"
        
        elif step == "postprocessing-voxel":
            specificPath = "/postprocessing/rmsf_map2grid.py"

        elif step == "postprocessing-folder":
            specificPath="/postprocessing"

        return commonPath + specificPath
    
    def obtainLink(self,location, destination):
        if path.islink(location):
            source = readlink(location)
            symlink(source, destination)
        else:
            symlink(location, destination)


    def getResult(self, name):
        if name == 'volumes':
            file = '/volumes.mrc'
        elif name == 'dataset':
            file = '/sample.jbl'
        elif name == 'prediction':
            file = '/prediction.jbl'
        elif name == 'atomic-structure':
            file = '/structure.pdb'
        elif name == 'output-voxel':
            file = '/voxel-visualization.pdb'
        elif name == 'output-pdb':
            file = '/defmap_norm_model.pdb'
        else:
            file = ''
        return  self.resultsFolder + file
    
    def checkExtension(self,file,extension):
        file_extension = path.splitext(file)[1]
        
        logger.info("file extension: " +file_extension)
        logger.info("extension: "+extension)
        
        if file_extension == extension:
            if extension == ".pdb":
                self.structureLocation = path.abspath(file) 
            else:
                self.volumesLocation = path.abspath(file)
            return True
        elif file_extension == '.cif' and extension == '.pdb':
            file_renamed = path.join(self.resultsFolder, path.splitext(path.split(file)[1])[0] + ".pdb")
            cifToPdb(file,file_renamed)
            self.structureLocation = path.abspath(file_renamed)
            return True
        elif extension == '.mrc':
            file_renamed = path.join(self.resultsFolder, path.splitext(path.split(file)[1])[0] + ".mrc")
            imgh = ImageHandler()
            imgh.convert(file,file_renamed)
            self.volumesLocation = path.abspath(file_renamed)
            return True
        else:
            return False


    # --------------------------- INFO functions -----------------------------------
    def _summary(self):
        summary = []

        if self.isFinished():
            sum1 = "This protocol has run DefMap Neural Network branch tf29, created by Shigeyuki Matsumoto and Shoichi Ishida."
            summary.append(sum1)
        return summary
    
    def _methods(self):
        methods = []

        if self.isFinished():
            methods.append("1. Create dataset to test")
            methods.append("2. Dynamics prediction")
            methods.append("3. Postprocessing")
        return methods
