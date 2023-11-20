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
from os import path, rename, readlink,symlink
from pyworkflow import Config
from defmap import Plugin
from defmap.constants import *
from pwem.objects import AtomStruct
import pyworkflow.utils as pwutils


class DefMapNeuralNetwork(Protocol):

    @classmethod
    def getClassPackageName(cls):
        return "defmap"

    _label = 'Defmap prediction'
    _possibleOutputs = {'outputStructure': AtomStruct}

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
                      label='Atomic structure', important=True,
                      help='Atomic structure of the molecule',
                      pointerClass="AtomStruct",
                      allowsPointers=True)

        form.addParam('inputResolution', params.EnumParam,
                      allowsNull=True,
                      label='Resolution',
                      help='Resolution model for the inference step. There are three models according to three possible resolutions',
                      default=0, choices=["5 Å","6 Å","7 Å"]),
        
        form.addParam('inputThreshold', params.FloatParam,
                        allowsNull=True, important = False,
                        label='Threshold',
                        help='Top threshold to drop voxels with a standardized intensity.\n'
                              'If not given, a threshold of 0 will be used for visualization.')

    # --------------------------- STEPS ------------------------------
    def _insertAllSteps(self):
        self._insertFunctionStep('createDatasetStep')
        # self._insertFunctionStep('inferenceStep')
        # self._insertFunctionStep('postprocStep')
        # self._insertFunctionStep('createOutputStep')


    def createDatasetStep(self):

        # Get paths and create symbolic links
        
        self.resultsFolder = path.abspath(self.getWorkingDir()) + "/extra"
        volumesLink = self.getResult('volumes')
        volumesLocation = path.abspath(self.inputVolume.get().getFileName())

        if path.islink(volumesLocation):
            self.copyLink(volumesLocation, volumesLink)
        else:
            symlink(volumesLocation, volumesLink)

        # Set arguments to create-dataset command
        
        args = [
                '-m "%s"' % volumesLink,
                '-o "%s"' % self.getResult('dataset'),
                '-p' 
                ]

        if self.inputThreshold.hasValue():
            args.append('-t %f ' % self.inputThreshold)

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

    def postprocStep(self):

        # Create Atomic Structure link

        structureLocation = path.abspath(self.inputStructure.get().getFileName())
        structureLink = self.getResult('atomic-structure')

        if path.islink(structureLocation):
            self.copyLink(structureLocation, structureLink)
        else:
            symlink(structureLocation, structureLink)

        # Prepare the file that points to the Atomic Structure and the Volumes

        pointerFileLocation = self.resultsFolder + "/sample_for_visual.list"

        with open(pointerFileLocation,"w") as pointerFile:
            pointerFile.write(structureLink + " " +self.getResult('volumes'))

        # Set arguments to Postprocessing command
        args = [
                '-l "%s"' % pointerFileLocation,
                '-p "%s"' % self.getResult('prediction'),
                '-n'
                ]

        command = "python " + self.getScriptLocation("postprocessing-script")

        # call command

        self._enterDir(self.getScriptLocation("postprocessing-folder"))
        self.runJob(Plugin.getEnvActivationCommand() + "&& " + command, ' '.join(args))

        # move result to working directory

        # self.postprocResultName = path.split(self.volumesLocation)[1][:-4] + ".pdb"

        # rename(self.getScriptLocation("postprocResult"), self.getPdbFile())

        logger.info("Results in %s" % self.resultsFolder)
        

    
    def createOutputStep(self):
        self.pdbFileName = self.getResult()
        if path.exists(self.pdbFileName):
            outputPdb = AtomStruct()
            outputPdb.setFileName(self.pdbFileName)
            self._defineOutputs(outputStructure=outputPdb)

    
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

        elif step == "postprocessing-script":
            specificPath = "/postprocessing/rmsf_map2model_for_defmap.py"

        elif step == "postprocessing-folder":
            specificPath="/postprocessing"

        return commonPath + specificPath
    
    def copyLink(self, oldLink, destination):
        source = readlink(oldLink)
        symlink(source, destination)

    def getResult(self, name):
        if name == 'volumes':
            file = '/volumes.mrc'
        elif name == 'dataset':
            file = '/sample.jbl'
        elif name == 'prediction':
            file = '/prediction.jbl'
        elif name == 'atomic-structure':
            file = '/structure.pdb'
        else:
            file = 'visual_output.pdb'
        return  self.resultsFolder + file

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
