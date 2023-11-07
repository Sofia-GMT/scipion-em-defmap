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
    inferenceFolderLocation = ""

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

        form.addParam('inputResolution', params.EnumParam,
                      allowsNull=True,
                      label='Resolution',
                      help='Resolution model for the inference step. There are three models according to three possible resolutions',
                      default=0, choices=["5 Å","6 Å","7 Å"]),
        
        form.addParam('inputThreshold', params.FloatParam,
                        allowsNull=True, important = False,
                        label='Threshold',
                        help='Top threshold to drop sub-voxels with a standardized intensity')

    # --------------------------- STEPS ------------------------------
    def _insertAllSteps(self):
        self._insertFunctionStep('createDatasetStep')
        self._insertFunctionStep('inferenceStep')


    def createDatasetStep(self):

        logger.info("Create dataset step")

        # Get paths
        volumesLocation = os.path.abspath(self.inputVolume.get().getFileName())
        self.datasetFolderLocation=os.path.abspath(self._getExtraPath("sample.jbl"))

        # Set arguments to create-dataset command
        
        args = [
                '-m "%s"' % volumesLocation,
                '-o "%s"' % self.datasetFolderLocation,
                '-p' 
                ]

        if self.inputThreshold.hasValue():
            args.append('-t %f ' % self.inputThreshold)

        # Execute create-dataset
        createDatasetCommand ="python prep_dataset.py"
        
        self._enterDir(self.getScriptLocation("create-dataset-folder"))
        self.runJob(Plugin.getEnvActivationCommand() + "&& " + createDatasetCommand, ' '.join(args))

    def inferenceStep(self):

        logger.info("Inference step")

        # Get pahts

        resultsFolder = self.datasetFolderLocation

        self.inferenceFolderLocation = os.path.abspath(self._getExtraPath("prediction.jbl"))
        trainedModelLocation = self.getScriptLocation(str(self.inputResolution))

        # Set arguments to create-dataset command

        args = [
                '-t "%s"' % self.datasetFolderLocation,
                '-p "%s"' % self.inferenceFolderLocation,
                '-o "%s"' % trainedModelLocation
                ]

        # execute inference

        inferenceCommand = "python " + self.getScriptLocation("inference") +" infer"

        self._enterDir(self.getScriptLocation(""))
        self.runJob(inferenceCommand, ' '.join(args))


    
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

        return commonPath + specificPath

    # --------------------------- INFO functions -----------------------------------
    def _summary(self):
        summary = []

        if self.isFinished():
            sum1 = "This protocol has run DefMap Neural Network branch tf29, created by Shigeyuki Matsumoto and Shoichi Ishida."
            summary.append(sum1)
            sum2 = ("Prediction saved in %s " % self.inferenceFolderLocation)
            summary.append(sum2)
        return summary
    
    def _methods(self):
        methods = []

        if self.isFinished():
            methods.append("1. Create dataset to test")
            methods.append("2. Dynamics prediction")
        return methods
