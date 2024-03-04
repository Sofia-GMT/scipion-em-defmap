# -*- coding: utf-8 -*-
# **************************************************************************
# *
# * Authors:          
# *
# * Centro Nacional de Biotecnologia, CSIC
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

#from pwem.viewers import ChimeraViewer
from pyworkflow.viewer import ProtocolViewer
from pwem.viewers.plotter import EmPlotter
from defmap.protocols import DefMapNeuralNetwork, DefmapTestViewer
from pyworkflow.protocol import params
from pwchem.viewers import PyMolViewer
from os import path, readlink
from biopandas.pdb import PandasPdb
from pyworkflow.utils import logger
import numpy as np
from pwem.convert.atom_struct import AtomicStructHandler
import pandas as pd
from Bio.PDB.PDBParser import PDBParser


class DefmapViewer(ProtocolViewer):
  _targets = [DefMapNeuralNetwork, DefmapTestViewer]

  _label = 'Structure and predictions viewer'

  def _defineParams(self, form):
     form.addSection(label='Visualization')
     form.addParam('inputSecondStructure', params.PointerParam,
                      label='Atomic structure', allowsNull=True,
                      help='Atomic struture to compare with the output from Defmap. Only works with pdb extension.',
                      pointerClass="AtomStruct",
                      allowsPointers=True)
     form.addParam('inputLocalRes', params.PointerParam,
                      label='Local resolutions', allowsNull=True,
                      help='Local resolutions to compare with the output from Defmap. Only works with pdb extension.',
                      pointerClass="AtomStruct",
                      allowsPointers=True)
     form.addParam('openPymol', params.LabelParam,
                      label='See results in Pymol'
                      )
     form.addParam('makeGraph', params.LabelParam,
                      label='See a graph with b-factors'
                      )
  
  def _getVisualizeDict(self):
        return {'openPymol': self._viewPymol,
                'makeGraph': self._viewGraph}
  
  def _viewPymol(self, *args):
   folder = path.split(self.protocol.outputStructure.getFileName())[0]
   files = folder + "/pointer_for_pymol.pml"
   view = PyMolViewer(project=self.getProject())
   return view._visualize(pymolFile=files, cwd=folder)
  
  def _viewGraph(self,*args):
     
     handler = PDBParser()
     
     # set dataframe of defmap output
     if(self.protocol.outputStructure != None):
        defmapFile = self.protocol.outputStructure.getFileName()
     else:
        defmapFile = self.protocol.outputStructureVoxel.getFileName()
        
     logger.info("defmap structure: %s" % defmapFile)
     defmap_st =  handler.get_structure(id='DEFMAP',file=defmapFile)
     defmap_atoms_A = self.getAtomList(defmap_st[0],'A')
     defmap_atoms_B = self.getAtomList(defmap_st[0],'B')
     defmap_atoms = self.getAtomList(defmap_st[0])
     defmap_atoms_arr = np.array(object=defmap_atoms)

     # plot histogram

     plotter = EmPlotter()
     plotter.createSubPlot(title="Frequencies of RMS in Defmap output",
                           xlabel="RMS",ylabel="Frequencies")
     plotter.plotHist(yValues=defmap_atoms,nbins=100)

      # set dataframe of second structure
     folder = path.split(defmapFile)[0]
     secondPath = folder+"/structure.pdb"
     secondFile = None

     if self.inputSecondStructure.hasValue():
        secondFile = self.inputSecondStructure.get().getFileName()
     elif path.exists(secondPath) :
        secondFile = readlink(secondPath)

     if secondFile is not None:
      logger.info("second structure: %s" % secondFile)
      second_st =  handler.get_structure(id='SECOND',file=secondFile)
      second_atoms_A = self.getAtomList(second_st[0],'A')
      second_atoms_B = self.getAtomList(second_st[0],'B')
      second_atoms = self.getAtomList(second_st[0])
      second_atoms_arr = np.array(object=second_atoms)

      # plot RMS vs b-factor

      plotter = EmPlotter()

      plotter.createSubPlot(title="Defmap output vs Atomic Structure",
                              xlabel="RMS Defmap output",ylabel=" B-factors Atomic Structure")
      plotter.plotScatter(xValues=defmap_atoms_A, yValues=second_atoms_A,alpha=0.7, label='Chain A', edgecolors="gray",color='cyan')
      plotter.plotScatter(xValues=defmap_atoms_B, yValues=second_atoms_B,alpha=0.7, label='Chain B',edgecolors="gray",color='orange')
      plotter.legend()

      b, a = np.polyfit(x=defmap_atoms_arr,y=second_atoms_arr,deg=1)
      plotter.plotData(xValues=defmap_atoms_arr,yValues= a + b * defmap_atoms_arr,color="k", lw=1)

     # plot RMS vs local resolution

     if self.inputLocalRes.hasValue():
        # set dataframe of local resolutions
         localResFile = self.inputLocalRes.get().getFileName()
         localRes_st =  handler.get_structure(id='LOCALRES',file=localResFile)
         localRes_atoms_A = self.getAtomList(localRes_st[0],'A')
         localRes_atoms_B = self.getAtomList(localRes_st[0],'B')
         localRes_atoms = self.getAtomList(localRes_st[0])
         localRes_atoms_arr = np.array(object=localRes_atoms)

         plotter = EmPlotter()
         plotter.createSubPlot(title="Defmap output vs Local Resolution",
                                 xlabel="RMS Defmap output",ylabel="Local resolution")
         plotter.plotScatter(xValues=defmap_atoms_A, yValues=localRes_atoms_A,alpha=0.7, label='Chain A', edgecolors="gray",color='cyan')
         plotter.plotScatter(xValues=defmap_atoms_B, yValues=localRes_atoms_B,alpha=0.7, label='Chain B',edgecolors="gray",color='orange')
         plotter.legend()

         b, a = np.polyfit(x=defmap_atoms_arr,y=localRes_atoms_arr,deg=1)
         plotter.plotData(xValues=defmap_atoms_arr,yValues= a + b * defmap_atoms_arr,color="k", lw=1)

     return [plotter]
  
  def getAtomList(self,model,chain=None):
     if chain is None:
        atomList = model.get_atoms()
     else:
        atomList = model[chain].get_atoms()
     result = []
     for atom in atomList:
        if atom.get_name() == 'CA':
           result.append(atom.get_bfactor())
     return result


           

  
