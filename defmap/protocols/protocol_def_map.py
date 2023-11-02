# -*- coding: utf-8 -*-
# **************************************************************************
# *
# * Authors:     you (you@yourinstitution.email)
# *
# * your institution
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
# *  e-mail address 'you@yourinstitution.email'
# *
# **************************************************************************


"""
Protocol to run DefMap neural network
"""
from posixpath import basename
from pyworkflow.protocol import Protocol, params
from pyworkflow.utils import Message, logger
from os import system, mkdir
from datetime import datetime
from subprocess import call
import os
import pyworkflow.utils as pwutils
from pyworkflow import Config
from pyworkflow.utils import path

from defmap import Plugin
from defmap.constants import *


class DefMapNeuralNetwork(Protocol):

    @classmethod
    def getClassPackageName(cls):
        return "defmap"

    _label = 'Defmap prediction'
    # -------------------------- CONSTANTS ----------------------

    datasetFolderLocation = ""

    createDatasetCommand = "python prep_dataset.py -m /home/usuario/ScipionUserData/projects/defmap_prep/Runs/000390_XmippProtCropResizeVolumes/extra/output_volume.mrc -o ../data/sample.jbl -p -t 0.2"

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
        form.addSection(label=Message.LABEL_INPUT)

        form.addParam('inputVolume', params.PointerParam,
                      label='Volume', important=True,
                      help='3D reconstruction of the microscopy images. They must be scaled.',
                      pointerClass="Volume",
                      allowsPointers=True)

        # form.addParam('structure', params.PointerParam,
        #               label='Atomic structure', important=True,
        #               help='Atomic structure of the protein from PDB',
        #               pointerClass="Structure",
        #               allowsPointers=True)

        # form.addParam('resolution', params.EnumParam,
        #               allowsNull=True,
        #               label='Resolution',
        #               help='Resolution model for the inference step',
        #               default="5A", choices=["5A","6A","7A"]),
        
        form.addParam('inputThreshold', params.FloatParam,
                        allowsNull=True, important = False,
                        label='Threshold',
                        help='Top threshold to drop sub-voxels with a standardized intensity')

    # --------------------------- STEPS ------------------------------
    def _insertAllSteps(self):
        self._insertFunctionStep('createDatasetStep')
        #self._insertFunctionStep('inferenceStep')


    def createDatasetStep(self):
        volumesLocation = os.path.abspath(self.inputVolume.get().getFileName())
        newFolderName=os.path.abspath(self._getExtraPath("sample.jbl"))
        logger.info(newFolderName)

        #  Create folder with the dataset
        # if not os.path.exists(newFolderName):
        #     os.mkdir(newFolderName)
        self.datasetFolderLocation = os.path.abspath(newFolderName) #self.getWorkingDir())
        logger.info(self.datasetFolderLocation)

        # Set arguments to create-dataset command
        
        args = [
                '-m "%s"' % volumesLocation,
                '-o "%s"' % self.datasetFolderLocation,
                '-p' 
                ]

        if self.inputThreshold.hasValue():
            args.append('-t %f ' % self.inputThreshold)

        # Execute create-dataset
        createDatasetCommand ="python " + self.getScriptLocation("create-dataset")

        # print(createDatasetCommand)
        

        #system("pip install tqdm")
        self._enterDir(self.getScriptLocation())
        self.runJob(Plugin.getEnvActivationCommand() + "&& " + createDatasetCommand, ' '.join(args))
    
    # --------------------------- UTILS functions -----------------------------------

    def getScriptLocation(self,step=None):
        commonPath = Config.SCIPION_HOME + "/software/em/"+ DEFAULT_SCRIPT_FOLDER+"/DEFMap"
        specificPath = ""
        if step == "create-dataset":
            specificPath = "/preprocessing/prep_dataset.py"
        elif step == "inference" :
            specificPath = "/3dcnn_main.py"

        return commonPath + specificPath
    
    def setArgs(self, args):
        result=''
        for item in args:
            result+=item
        return result

    # --------------------------- INFO functions -----------------------------------
    def _summary(self):
        summary = []

        if self.isFinished():
            sum = "This protocol has run DefMap Neural Network branch tf29, created by Shigeyuki Matsumoto and Shoichi Ishida."
            summary.append(sum)
        return summary
    
    def _methods(self):
        methods = []

        if self.isFinished():
            methods.append("1. Activate or prepare DefMap env in conda")
            methods.append("2. Create dataset step")
            methods.append("3. Inferce step")
        return methods
