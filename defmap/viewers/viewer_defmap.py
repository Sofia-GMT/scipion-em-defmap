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
from pyworkflow.viewer import ProtocolViewer, DESKTOP_TKINTER, WEB_DJANGO
from pwem.viewers.plotter import EmPlotter
from defmap.protocols import DefMapNeuralNetwork, DefmapTestViewer
from pyworkflow.protocol import params
from pwchem.viewers import PyMolViewer
from os import path, readlink
from pyworkflow.utils import logger
import numpy as np
from Bio.PDB.PDBParser import PDBParser
from pwem.objects import AtomStruct
from scipy.stats import pearsonr, linregress
import os
from math import exp, pow
from decimal import Decimal

class DefmapViewer(ProtocolViewer):
  _targets = [DefMapNeuralNetwork, DefmapTestViewer, AtomStruct]
  _environments = [DESKTOP_TKINTER,WEB_DJANGO]

  _label = 'Structure and predictions viewer'

  def __init__(self, *args, **kwargs):
     ProtocolViewer.__init__(self, *args, **kwargs)  

  def _defineParams(self, form):
     form.addSection(label='Visualization')
     form.addParam('inputLocalRes', params.PointerParam,
                      label='Local resolutions', allowsNull=True,
                      help='Local resolutions to compare with the output from Defmap. Only works with pdb extension.',
                      pointerClass="AtomStruct",
                      allowsPointers=True)
     form.addParam('openPymol', params.LabelParam,
                      label='See results in Pymol'
                      )
     form.addParam('makeGraph', params.LabelParam,
                      label='See a graph with b-factors vs log(RMSF)'
                      )
     form.addParam('makeGraphExp', params.LabelParam,
                      label='See a graph with b-factors vs RMSF'
                      )
  
  def _getVisualizeDict(self):
        return {'openPymol': self._viewPymol,
                'makeGraph': self._viewGraph,
                'makeGraphExp': self._viewGraph}
  
  def _viewPymol(self, *args):
   folder = path.split(self.protocol.outputStructure.getFileName())[0]
   files = folder + "/pointer_for_pymol.pml"
   view = PyMolViewer(project=self.getProject())
   return view._visualize(pymolFile=files, cwd=folder)
  
  
  def _viewGraph(self,*args):
     
     if len(args) > 0 :
        exponential = args[0] == "makeGraphExp"
     else:
        exponential = False

     if exponential == True:
        header = "RMSF (Å)"
     else:
        header = "log(RMSF(Å))"
     
     handler = PDBParser()
     
     # set dataframe of defmap output
     if(self.protocol.outputStructure != None):
        defmapFile = self.protocol.outputStructure.getFileName()
     else:
        defmapFile = self.protocol.outputStructureVoxel.getFileName()
        
     logger.info("defmap structure: %s" % defmapFile)
     defmap_st =  handler.get_structure(id='DEFMAP',file=defmapFile)[0]
     defmap_chainList= self.getChainList(defmap_st)
     self.defmap_atoms = self.getAtomList(defmap_st,log=exponential)
     self.defmap_atoms_arr = self.getBfactors(self.defmap_atoms)

     # plot histogram

     plotter = EmPlotter()
     plotter.createSubPlot(title="Occurrences of Defmap output values",
                           xlabel=header,ylabel="Counts")

     plotter.plotHist(yValues=self.defmap_atoms_arr,nbins=100)

      # plot RMSF vs serial number
     plotter = EmPlotter()
   
     plotter.createSubPlot(title="Defmap vs Residue position",xlabel="residue",ylabel=header)
     for chain in defmap_chainList:  
        label = 'Chain %s' % chain
        color = self.getColor(chain)
        atomList = self.getAtomList(defmap_st, chain, exponential) 
        plotter.plotScatter(xValues=self.getAtomSerialNumbers(atomList), yValues=self.getBfactors(atomList),alpha=0.7, label=label, edgecolors="gray",color=color)
     
     plotter.legend()


      # set dataframe of second structure
     folder = path.split(defmapFile)[0]
     secondPath = folder+"/structure.pdb"
     secondFile = None

     if path.exists(secondPath) :
        secondFile = readlink(secondPath)

     if secondFile is not None:
      logger.info("second structure: %s" % secondFile)
      second_st =  handler.get_structure(id='SECOND',file=secondFile)[0]
      second_atoms = self.getAtomList(second_st)
      second_atoms_arr = self.checkAtomsSize(second_atoms)

      # plot RMSF vs b-factor

      plotter = EmPlotter()

      matrix = pearsonr(x=self.defmap_atoms_arr,y=second_atoms_arr )

      matrixSubtitle = 'Pearson correlation coefficient %f with pvalue %.2E.' % (matrix[0], Decimal(matrix[1]))

      regression = linregress(x=self.defmap_atoms_arr,y=second_atoms_arr)

      regressionSubtitle = """Linear regression: y = (%f ± %f) x + (%f ± %f); R2 %f; pvalue %.2E""" % (
         regression.slope, regression.stderr, regression.intercept, regression.intercept_stderr,
         pow(regression.rvalue,2), Decimal(regression.pvalue))

      subtitle = '%s %s' % (matrixSubtitle, regressionSubtitle)
      

      plotter.createSubPlot(title="Defmap output vs Atomic Structure", subtitle=subtitle,
         xlabel= "Defmap output "+header,ylabel="Atomic Structure B-factors (Å^2)")
      
      self.plotChains(plotter,defmap_chainList,defmap_st,second_st,exponential)
      plotter.legend()

      b = regression.slope
      a = regression.intercept

      plotter.plotData(xValues=self.defmap_atoms_arr,yValues=(a + b * np.array(self.defmap_atoms_arr)),color="k", lw=1)

   #   # plot RMSF vs local resolution 

     if self.inputLocalRes.hasValue():
        # set dataframe of local resolutions
         localResFile = self.inputLocalRes.get().getFileName()
         localRes_st =  handler.get_structure(id='LOCALRES',file=localResFile)[0]
         localRes_atoms = self.getAtomList(model=localRes_st)
         localRes_atoms_arr = self.checkAtomsSize(localRes_atoms)

         index_nonzero_localRes = np.nonzero(localRes_atoms_arr)[0]
         defmap_atoms_arr_cleaned = np.array(self.defmap_atoms_arr)[index_nonzero_localRes]
         localRes_atoms_arr = np.array(localRes_atoms_arr)[index_nonzero_localRes]

         matrix = pearsonr(x=defmap_atoms_arr_cleaned,y=localRes_atoms_arr)

         matrixSubtitle = 'Pearson correlation coefficient %f with pvalue %f.' % matrix

         regression = linregress(x=defmap_atoms_arr_cleaned,y=localRes_atoms_arr)

         regressionSubtitle = """Linear regression: y = (%f ± %f) x + (%f ± %f); R2 %f; pvalue %.2E""" % (
         regression.slope, regression.stderr, regression.intercept, regression.intercept_stderr,
         pow(regression.rvalue,2), Decimal(regression.pvalue))

         subtitle = '%s %s' % (matrixSubtitle, regressionSubtitle)


         b = regression.slope
         a = regression.intercept

         plotter = EmPlotter()
         plotter.createSubPlot(title="Defmap output vs Local Resolution", subtitle=subtitle,
                                 xlabel="Defmap output "+header,ylabel="Local resolution (Å)")
         self.plotChains(plotter,defmap_chainList,defmap_st,localRes_st,exponential,True)
         plotter.legend()

         
         plotter.plotData(xValues=self.defmap_atoms_arr,yValues= a + b * np.array(self.defmap_atoms_arr),color="k", lw=1)

     return [plotter]
  
  def plotChains(self, plotter, idList,defmapModel,extraModel,exp=False,localRes=False):
     for chain in idList:  
      defmap_atoms_chain = self.getAtomList(defmapModel, chain, exp)
      extra_atoms_chain = self.getAtomList(extraModel, chain)
      label = 'Chain %s' % chain
      color = self.getColor(chain)
      if(len(defmap_atoms_chain) == len(extra_atoms_chain)):
         defmap_bfactors = self.getBfactors(defmap_atoms_chain)
         extra_bfactors = self.getBfactors(extra_atoms_chain)

      elif (len(defmap_atoms_chain) > len(extra_atoms_chain)):
         defmap_bfactors = self.removeAtoms(defmap_atoms_chain, extra_atoms_chain)
         extra_bfactors = self.getBfactors(extra_atoms_chain)
      else:
         defmap_bfactors = self.getBfactors(defmap_atoms_chain)
         extra_bfactors = self.removeAtoms(extra_atoms_chain, defmap_atoms_chain)

      if localRes:
         index_nonzero_localRes = np.nonzero(extra_bfactors)[0]
         defmap_bfactors = defmap_bfactors[index_nonzero_localRes]
         extra_bfactors = extra_bfactors[index_nonzero_localRes]
         
      plotter.plotScatter(xValues=defmap_bfactors, yValues=extra_bfactors,alpha=0.7, label=label, edgecolors="gray",color=color)


  def checkAtomsSize(self,listToCompare):
     if len(listToCompare) == len(self.defmap_atoms):
        return self.getBfactors(listToCompare)
     elif len(listToCompare) > len(self.defmap_atoms):
        return self.removeAtoms(listToCompare,self.defmap_atoms)
     else:
        self.defmap_atoms_arr = self.removeAtoms(self.defmap_atoms,listToCompare)
        return self.getBfactors(listToCompare)
         


  def getBfactors(self, list):
     result = []
     for tuple in list:
        result.append(tuple[1])
     return result
  
  def getAtomSerialNumbers(self, list):
     result = []
     for tuple in list:
        result.append(tuple[2])
     return result


  def removeAtoms(self, listToChange, reference):
     result = []
     for i in range(len(reference)):
        if reference[i][0] != listToChange[i][0]:
           listToChange.remove(listToChange[i])

        if len(listToChange)>i:
           result.append(listToChange[i][1])

     return result

  def getColor(self, chain):
     if chain == 'A':
        return 'cyan'
     elif chain == 'B':
        return 'orange'
     elif chain == 'C':
        return 'yellowgreen'
     elif chain == 'D':
        return 'pink'
     elif chain == 'E':
        return 'steelblue'
     elif chain == 'F':
        return 'tomato'
     else :
        return 'blue'
     
  
  def getChainList(self,model):
     list = []
     for chain in model.get_chains():
        list.append(chain.get_id())
     return list
  
  def getAtomList(self,model,chain=None,log=False):
     if chain is None:
        atomList = model.get_atoms()
     else:
        atomList = model[chain].get_atoms()
     result = []
     for atom in atomList:
        if atom.get_name() == 'CA':
         if log:
            value = exp(atom.get_bfactor())
         else:
            value = atom.get_bfactor()
            
         residueIndex = atom.get_full_id()[3][1]
         result.append((atom.get_parent().get_resname(),value,residueIndex))
     return result


           

  
