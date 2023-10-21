# To install DefMap manually
Protocol adapted from https://github.com/clinfo/DEFMap/blob/master/doc/setup.md

**1. Download pyenv and EMAN2**  
```bash
git clone https://github.com/yyuu/pyenv.git $HOME/.pyenv
wget https://cryoem.bcm.edu/cryoem/static/software/release-2.3/eman2.3.linux64.sh
```

**2. Setup environment for pyenv and EMAN2**  
```bash
echo 'export PATH="$PATH:$HOME/EMAN2/bin"' >> $HOME/.bashrc
echo 'export PYENV_ROOT="$HOME/.pyenv"' >> $HOME/.bashrc
echo 'export PYENV_ROOT="$PYENV_ROOT/bin:$PATH"' >> $HOME/.bashrc
echo 'export PYENV_ROOT="$HOME/.pyenv"' >> $HOME/.bashrc
echo 'if command -v pyenv 1>/dev/null 2>&1; 
	then eval "$(pyenv init -)" 
fi' >> $HOME/.bashrc
```
```bash
source $HOME/.bashrc
```

**3. Install pyenv-virtualenv**
```bash
git clone https://github.com/pyenv/pyenv-virtualenv.git $(pyenv root)/plugins/pyenv-virtualenv
echo 'eval "$(pyenv virtualenv-init -)"' >> $HOME/.bashrc
echo 'eval "$(pyenv init --path)"' >> $HOME/.bashrc
```
```bash
source $HOME/.bashrc
```

**4. Install EMAN2** # voy por aquí

```bash 
conda activate defmap
bash eman2.3.linux64.sh -b # -u para actualizar en caso de ya tener instalado EMAN y previamente rm -r install_logs 
```
```bash
conda activate
conda create -n defmap python=3.6
pyenv install 3.6
pyenv shell 3.6

conda install -c acellera -c psi4 -c conda-forge htmd=1.15.2

# ver si tengo que instalar el solver classic, me he quedado por aquí.

conda config --set solver classic
conda install -c acellera -c psi4 -c conda-forge htmd=1.15.2

conda install keras-gpu=2.2.4 tensorflow-gpu=1.13.1 cudatoolkit=10.0
# if the version of CUDA Toolkit installed on your server is 9.0, please specify cudatoolkit=9.0
```