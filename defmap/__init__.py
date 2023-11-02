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
# *  e-mail address 'scipion@cnb.csic.es'
# *
# **************************************************************************

import pwem
from pyworkflow import Config
import pyworkflow.utils as pwutils
from defmap.constants import *
import os


_references = ['Matsumoto2021']
_logo = "defmap_logo.png"



class Plugin(pwem.Plugin):

    @classmethod
    def defineBinaries(cls, env): 
        # Clone external repository from Matsumoto2021
        cls.addDefmapPackage(env)

    
    # @classmethod
    # def _defineVariables(cls):
    #     Create a variable in scipion.config of the external repository
    #     cls._defineEmVar(DEFMAP_DIC['home'], DEFAULT_ENV_NAME)
    
    @classmethod
    def getEnvActivationCommand(cls, packageDictionary=None, condaHook=True):
        return '{}conda activate {}'.format(cls.getCondaActivationCmd(), DEFAULT_ENV_NAME)


    @classmethod
    def addDefmapPackage(cls, env):
        FLAG = f"defmap_{DEFAULT_VERSION}_installed"


        installCmds = [
            cls.getCondaActivationCmd(),
            f'conda create -y -n {DEFAULT_ENV_NAME} &&',
            f'conda update -n base -c conda-forge conda &&',
            f'conda activate {DEFAULT_ENV_NAME} &&',
            f'conda install numpy &&',
            f'conda install -c acellera moleculekit &&',
            f'conda install tqdm &&',
            f'conda install joblib &&',
            f'conda install scipy &&',
            f'conda install -c conda-forge tensorflow &&',
            f'touch {FLAG}'  # Flag installation finished
        ]

        envPath = os.environ.get('PATH', "")
        # keep path since conda likely in there
        installEnvVars = {'PATH': envPath} if envPath else None

        branch = "tf29"
        url = "https://github.com/clinfo/DEFMap.git"
        gitCmds = [
            'cd .. &&',
            f'git clone -b {branch} {url} defmap-{DEFAULT_VERSION} &&',
            f'cd defmap-{DEFAULT_VERSION};'
        ]
        gitCmds.extend(installCmds)
        defmapCmds = [(" ".join(gitCmds), FLAG)]
        env.addPackage('defmap', version=DEFAULT_VERSION,
                       tar='void.tgz',
                       commands=defmapCmds,
                       default=False,
                       vars=installEnvVars)
    

        
    
    
            