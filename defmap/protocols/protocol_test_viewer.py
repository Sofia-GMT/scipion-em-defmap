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

from pyworkflow.protocol import Protocol, params
from pyworkflow.utils import Message, logger
from os import path, readlink, symlink
from defmap.constants import *
from pwem.objects import AtomStruct
from pwem.convert.atom_struct import cifToPdb
from shutil import copyfile



class DefmapTestViewer(Protocol):

    @classmethod
    def getClassPackageName(cls):
        return "defmap"

    _label = 'Defmap viewer'
    _possibleOutputs = {'outputStructure': AtomStruct, 'outputStructureVoxel':AtomStruct}

    # -------------------------- INPUT PARAMETERS ----------------------
    def _defineParams(self, form):
        """ 
        Params:
            * structureOne: first structure to compare.
            * structureTow: first structure to compare.
        """
        form.addSection(label=Message.LABEL_INPUT)
        form.addParam('structureOne', params.PointerParam,
                      label='Mandatory structure', allowsNull=False,
                      help='Mandatory structure',
                      pointerClass="AtomStruct",
                      allowsPointers=True)
        form.addParam('structureTwo', params.PointerParam,
                      label='Extra structure', allowsNull=True,
                      help='Extra structure',
                      pointerClass="AtomStruct",
                      allowsPointers=True)

    # --------------------------- STEPS ------------------------------
    def _insertAllSteps(self):
        self._insertFunctionStep('setPointers')
        self._insertFunctionStep('getPymolScript')
        self._insertFunctionStep('createOutput')

    def setPointers(self):
        self.resultsFolder = path.abspath(self.getWorkingDir()) + "/extra"
        logger.info("results folder: "+self.resultsFolder)

        firstStructure = self.structureOne.get().getFileName()
        logger.info("firstStructure: "+firstStructure)
        copyfile(firstStructure, self.getResult("structureOne") )
        logger.info("copy file")

        if self.structureTwo.hasValue() :
            filename = self.structureTwo.get().getFileName()
            logger.info("structureTwo "+filename)
            if self.checkExtension(filename,".pdb"):
                self.obtainLink(self.structureLocation, self.getResult("") )
            else:
                raise Exception('The extension of the atomic structure is not suported')
            
    def getPymolScript(self):
        pymolScript = self.resultsFolder + "/pointer_for_pymol.pml"
        with open(pymolScript,"w") as pointerFile:
            pointerFile.write("load defmap_norm_model.pdb"+"\n"
                              "load structure.pdb" "\n"
                              "set grid_mode,1 \n"
                              "spectrum b, slate_orange_red, minimum=-1, maximum=2, selection=defmap_norm_model"+"\n"
                              "spectrum b, slate_orange_red, selection=structure"
                              )

            

    def createOutput(self):
        if path.exists(self.getResult("structureOne")):
            output = AtomStruct()
            output.setFileName(self.getResult("structureOne"))
            self._defineOutputs(outputStructure=output)

    # --------------------------- UTILS ------------------------------
    
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
        else:
            return False
        
    def obtainLink(self,location, destination):
        if path.islink(location):
            source = readlink(location)
            symlink(source, destination)
        else:
            symlink(location, destination)
    
    def getResult(self,name):
        if name == "structureOne":
            file = '/defmap_norm_model.pdb'
        else:
            file = '/structure.pdb'
        return  self.resultsFolder + file


    # --------------------------- INFO functions -----------------------------------
    def _summary(self):
        summary = []

        if self.isFinished():
            sum1 = "Protocol to test DefmapViewer"
            summary.append(sum1)
        return summary
    
    def _methods(self):
        methods = []

        if self.isFinished():
            methods.append("To add pointers")
        return methods
