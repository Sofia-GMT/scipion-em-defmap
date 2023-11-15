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
from defmap.protocols import DefMapNeuralNetwork
from pyworkflow.protocol import params
from pwchem.viewers import PyMolViewer

from pwem.objects import AtomStruct

class DefmapViewer(ProtocolViewer):
  _targets = [DefMapNeuralNetwork, AtomStruct]

  _label = 'Structure and predictions viewer'

  def _defineParams(self, form):
     form.addSection(label='Visualization')
     form.addParam('openPymol', params.LabelParam,
                      label='See results in Pymol',
                      ),
    #  form.addParam('openChimeraX', params.LabelParam,
    #                   label="See results in Chimera")
  
  def _getVisualizeDict(self):
        return {'openPymol': self._viewPymol}
                #'openChimeraX': self._viewChimeraX}
  
  def _viewPymol(self, *args):
    if isinstance(self.protocol, DefMapNeuralNetwork):
       files = self.protocol.outputStructure.getFileName()
    else:
       files = self.protocol.getFileName()
    view = PyMolViewer(project=self.getProject())
    return view._visualize(files)
  
  # def _viewChimeraX(self):
  #   view = ChimeraViewer(project=self.getProject())
  #   return view._visualize(DefMapNeuralNetwork.getOutputFiles())
  
