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
from pwem.objects import AtomStruct, Volume, Transform
from pwem.convert.atom_struct import cifToPdb
from pwem.emlib.image import ImageHandler
from pwem.convert import Ccp4Header

try:
    from xmipp3 import Plugin as xmipp3Plugin
    haveXmipp = True
except ImportError:
    haveXmipp = False


class DefMapNeuralNetwork(Protocol):

    @classmethod
    def getClassPackageName(cls):
        return "defmap"

    _label = 'Defmap prediction'
    _possibleOutputs = {'outputStructure': AtomStruct, 'outputStructureVoxel':AtomStruct, 'outputVolume':Volume}

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

        form.addHidden(params.GPU_LIST, params.StringParam,
                       expertLevel=constants.LEVEL_ADVANCED,
                       label='Constrain GPU',
                       default='1',
                       help="Constrain GPU usage at inference step")

        form.addParam('inputVolume', params.PointerParam,
                      label='Volume', important=True,
                      help='3D reconstruction of the microscopy images. They must be scaled.',
                      pointerClass="Volume",
                      allowsPointers=True)

        form.addParam('inputStructure', params.PointerParam,
                      label='Atomic structure', allowsNull=True,
                      help='Atomic structure of the molecule.',
                      pointerClass="AtomStruct",
                      allowsPointers=True)

        form.addParam('inputResolution', params.EnumParam,
                      label='Resolution',
                      help='Resolution model for the inference step. There are three models according to three possible resolutions.',
                      default=0, choices=["5 Å","6 Å","7 Å"]),
        
        form.addParam('inputPreprocess', params.BooleanParam, default=False,
                      condition=haveXmipp,
                      label='Whether to preprocess the volumes',
                      help="In case you want to preprocess, it will change the sampling rate to 1.5 A and the resolution to the one selected.")  
        
        form.addParam('inputThreshold', params.FloatParam,
                        allowsNull=True, important = False,
                        condition='inputPreprocess == True',
                        label='Threshold',
                        help='Top threshold to drop voxels with a standardized intensity.\n'
                              'If not given, a threshold of 0 will be used for preprocessing.')
        
        form.addParam('inputRunNeuralNetwork', params.BooleanParam, default=True,
                      condition='inputPreprocess == True',
                      label='Would you like to run also the neural network?',
                      help="Whether to only preprocess the volumes or also run the neural network")  

    # --------------------------- STEPS ------------------------------
    def _insertAllSteps(self):
        self._insertFunctionStep('validateFormats')
        if self.inputPreprocess:
            self._insertFunctionStep('preprocess')
        if self.inputRunNeuralNetwork:
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
            
    def preprocess(self):

        self.cropResizeVolumes()
        self.filterVolumes()
        self.create3dMask()
        self.apply3dMask()
        self.volumesThreshold()

    def createDatasetStep(self):

        # Set arguments to create-dataset command
        
        args = [
                '-o "%s"' % self.getResult('dataset'),
                '-p' 
                ]

        if self.inputPreprocess:
            args.append('-m "%s" ' % self.getResult('preprocessOutput'))
        else:
            args.append('-m "%s" ' % self.getResult('volumes'))

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
        
        if self.gpuList.get():
            args.append('-g %s' % self.gpuList.get())

        # execute inference

        inferenceCommand = "python " + self.getScriptLocation("inference")

        self._enterDir(self.getScriptLocation(""))
        self.runJob(Plugin.getEnvActivationCommand() + "&& " + inferenceCommand, ' '.join(args))

    def postprocStepVoxel(self):

        # Set arguments to Postprocessing command
        args = [
                '-p "%s"' % self.getResult('prediction'),
                '-t 0.0'
                ]
        
        name = ""
        
        if self.inputPreprocess:
            args.append('-m "%s" ' % self.getResult('preprocessOutput'))
            name = "output_volumeT.pdb"
        else:
            args.append('-m "%s" ' % self.getResult('volumes'))
            name = "volumes.pdb"

        command = "python " + self.getScriptLocation("postprocessing-voxel")

        # call command

        self._enterDir(self.getScriptLocation("postprocessing-folder"))
        self.runJob(Plugin.getEnvActivationCommand() + "&& " + command, ' '.join(args))

        # move result to working directory

        rename(name, self.getResult('output-voxel'))


    def postprocStepPdb(self):

        if(self.inputStructure.hasValue()):

            # Prepare the file that points to the Atomic Structure and the Volumes

            pointerFileLocation = self.resultsFolder + "/sample_for_visual.list"

            if self.inputPreprocess:
                with open(pointerFileLocation,"w") as pointerFile:
                    pointerFile.write("structure.pdb output_volumeT.mrc")
            else:
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

        voxelFileName = self.getResult("output-voxel")
        pdbFileName = self.getResult("output-pdb")
        extraVolumes = self.getResult("preprocessOutput")

        outputPdbVoxel = None
        outputPdb = None
        outputVolume = None

        if path.exists(voxelFileName):
            logger.info('Setting voxel file')
            outputPdbVoxel = AtomStruct(filename=voxelFileName)

        if path.exists(pdbFileName):
            logger.info('Setting pdb file')
            outputPdb = AtomStruct(filename=pdbFileName)

        if path.exists(extraVolumes): 
            logger.info('Setting volume')
            outputVolume = Volume(location=extraVolumes)
            x, y, z, n = ImageHandler.getDimensions(extraVolumes)

            logger.info(ImageHandler.getDimensions(extraVolumes))

            origin = Transform()
            origin.setShifts( x / -2.0 * 1.5, 
                             y / -2.0 * 1.5,
                             z / -2.0 * 1.5)
            outputVolume.setOrigin(origin)
            outputVolume.setSamplingRate(1.5)
            outputVolume.setObjComment(outputVolume.getBaseName())

        self._defineOutputs(outputStructure=outputPdb,outputStructureVoxel=outputPdbVoxel,outputVolume=outputVolume)

        self.createPymolFile()

    def createPymolFile(self):

        # create file with pymol commands:
        pointerFileLocation = self.resultsFolder + "/pointer_for_pymol.pml"

        with open(pointerFileLocation,"w") as pointerFile:
            pointerFile.write("load defmap_norm_model.pdb"+"\n"
                              "load structure.pdb" "\n"
                              "set grid_mode,1 \n"
                              "spectrum b, slate_orange_red, minimum=-1, maximum=2, selection=defmap_norm_model"+"\n"
                              "spectrum b, slate_orange_red, selection=structure"+"\n"
                              "as cartoon, defmap_norm_model"+"\n"
                              "as cartoon, structure"
                              )

    
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
        elif name == 'preprocessCrop':
            file = '/output_volumeC.mrc'
        elif name == 'preprocessFilter':
            file = '/output_volumeF.mrc'
        elif name == 'preprocessMask':
            file = '/output_volumeM.mrc'
        elif name == 'preprocessApplyMask':
            file = '/output_volumeA.mrc'
        elif name == 'preprocessOutput':
            file = '/output_volumeT.mrc'
        elif name == 'transformedMask':
            file = '/mask.vol'
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
        
    def getResolution(self, option):
        logger.info(type(option))
        if option == 0:
            return 5.0
        elif option == 1:
            return 6.0
        else:
            return 7.0
        
    # --------------------------- PREPROCESS functions ----------------------------------- 
        
    def cropResizeVolumes(self):

        samplingRate = float(self.inputVolume.get().getSamplingRate())

        factorTransform = samplingRate / 3

        self.transformFilter(self.volumesLocation,self.getResult('preprocessCrop'),factorTransform,None)

        factorResize = samplingRate / 1.5

        args = [
                '-i "%s"' % self.getResult('preprocessCrop'),
                '--factor %f' % factorResize
                ]
        
        xmipp3Plugin.runXmippProgram('xmipp_image_resize',' '.join(args))

        self.imageHeader(self.getResult('preprocessCrop'))

    def filterVolumes(self):
        factor1 = 1.5 / self.getResolution(self.inputResolution)
        factor2 = 1.5 / 100

        self.transformFilter(self.getResult('preprocessCrop'),self.getResult('preprocessFilter'),factor1,factor2)
        self.imageHeader(self.getResult('preprocessFilter'))

    def create3dMask(self):

        threshold = 0.0
        if self.inputThreshold.hasValue():
            threshold = self.inputThreshold

        self.transformThreshold(self.getResult('preprocessFilter'), self.getResult('preprocessMask'), "binarize", threshold)

        self.transformMorphology(self.getResult('preprocessMask'), "removeSmall 50", False)

        self.transformMorphology(self.getResult('preprocessMask'), "keepBiggest", False)

        self.transformMorphology(self.getResult('preprocessMask'), "dilation", True)

        self.imageHeader(self.getResult('preprocessMask'))

    def apply3dMask(self):

        self.transformMask()
        args = [
                '-i "%s"' % self.getResult('preprocessFilter'),
                '--mult "%s"' % self.getResult('transformedMask'),
                '-o "%s"' % self.getResult('preprocessApplyMask')
                ]
        
        xmipp3Plugin.runXmippProgram('xmipp_image_operate',' '.join(args))

        self.imageHeader(self.getResult('preprocessApplyMask'))

    def transformMask(self):
        ImageHandler().convert(self.getResult('preprocessMask'), self.getResult('transformedMask'))

    def volumesThreshold(self):

        self.transformThreshold(self.getResult('preprocessApplyMask'), self.getResult('preprocessOutput'), "value 0.0", 0.0)

        self.imageHeader(self.getResult('preprocessOutput'))


    def transformFilter(self, input, output, percentage1, percentage2):
        args = [
                '-i "%s"' % input,
                '-o "%s"' % output,
                '--fourier'
                ]
        
        if percentage2 != None:
            args.append('low_pass %f %f' % (percentage1, percentage2))
        else:
            args.append('low_pass %f' % percentage1)
        
        xmipp3Plugin.runXmippProgram('xmipp_transform_filter',' '.join(args))

    def imageHeader(self, input):
        args = [
                '-i "%s"' % input,
                '--sampling_rate %f' % 1.5
                ]
        
        xmipp3Plugin.runXmippProgram('xmipp_image_header',' '.join(args))

    def transformThreshold(self, input, output, substitute, threshold):
        args = [
                '-i "%s"' % input,
                '-o "%s"' % output,
                '--substitute %s' % substitute,
                '--select below %f' % threshold
                ]
        
        xmipp3Plugin.runXmippProgram('xmipp_transform_threshold',' '.join(args))

    def transformMorphology(self, input, operation, size):

        args = [
                '-i "%s"' % input,
                '--binaryOperation %s' % operation
                ]
        
        if size:
            args.append('--size 1')
        
        xmipp3Plugin.runXmippProgram('xmipp_transform_morphology',' '.join(args))



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
