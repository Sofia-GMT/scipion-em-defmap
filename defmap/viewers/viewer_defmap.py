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
from defmap.protocols import DefMapNeuralNetwork
from pyworkflow.protocol import params
from pwchem.viewers import PyMolViewer
from os import path
from biopandas.pdb import PandasPdb
import matplotlib.pyplot as plt
from pandas import DataFrame
from pyworkflow.utils import logger


class DefmapViewer(ProtocolViewer):
  _targets = [DefMapNeuralNetwork]

  _label = 'Structure and predictions viewer'

  def _defineParams(self, form):
     form.addSection(label='Visualization')
     form.addParam('inputSecondStructure', params.PointerParam,
                      label='Atomic structure', allowsNull=True,
                      help='Atomic struture to compare withthe output from Defmap the graphs. Only works with pdb extension',
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
   return view._visualize(files)
  
  def _viewGraph(self,*args):
     # defmapFile = path.abspath(self.protocol.outputStructure.getFileName())
     defmapFile = self.inputSecondStructure.get().getFileName()
     defmap_df =  PandasPdb().read_pdb(defmapFile)
     defmap_atom_df = defmap_df.df['ATOM']

     second_atom_df = defmap_df.df['ATOM']

     plotter = EmPlotter()
     plotter.createSubPlot(title="Frequencies of B-Factors in Defmap output",
                           xlabel="B-factor",ylabel="Frequencies")
     plotter.plotHist(yValues=defmap_atom_df['b_factor'],nbins=100)

     plotter = EmPlotter()

     plotter.createSubPlot(title="B-Factors Defmap output vs Atomic Structure",
                           xlabel="Defmap output",ylabel="Atomic Structure")
     plotter.plotScatter(xValues=defmap_atom_df['b_factor'], yValues=second_atom_df['b_factor'])
     return [plotter]
  
