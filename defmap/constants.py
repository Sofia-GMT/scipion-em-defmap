# **************************************************************************
# *
# * Authors:     Sofia Gonzalez Matatoros (sofia.gonzalezm@estudiante.uam.es)
# *
# * MRC Laboratory of Molecular Biology (MRC-LMB)
# *
# * This program is free software; you can redistribute it and/or modify
# * it under the terms of the GNU General Public License as published by
# * the Free Software Foundation; either version 3 of the License, or
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


# Versions

V1_0_1 = "1.0.1"
VERSIONS = [V1_0_1]
DEFAULT_VERSION = V1_0_1

def getEnvName(version):
    return "defmap-%s" % version


# Environment

DEFAULT_ENV_NAME = getEnvName(DEFAULT_VERSION)
DEFAULT_SCRIPT_FOLDER = getEnvName(DEFAULT_VERSION)

    
