# Traffic_Optimisation

The code repo for paper "Multi-intersection Traffic Optimisation: A Benchmark Dataset and a Strong Baseline".

## Introduction

Traffic Signals optimisation for better road traffic handling using Deep Reinforcement Learning. The software SUMO ( Simulation of Urban MObility ) has been used to simulate traffic. To control the traffic signals system, the Traci, or Traffic Control Interface has been used which allows to retrieve values of simulated objects and to manipulate their behaviour "on-line".

## Setup Instructions

Install SUMO 0.32.0 using the command (newer version of SUMO is available, built from source may be required. The installation instruction of SUMO 0.32.0 is attached.): 

`sudo apt-get install sumo sumo-tools sumo-doc`

Create a virtual environment(install if not installed) using the command:

`virtualenv venv`

Activate the virtual environment:

`source venv/bin/activate`

Install requirements using:

`pip install -r requirements.txt`

Set the SUMO_HOME environment variable equal to the SUMO directory installed in your system ( /usr/share/sumo ).

Clone this repository using

`https://github.com/billhhh/Traffic_Optimisation.git`

This repo has been tested on pytorch 0.4.1.
If you are using Anaconda, follow the next command line to install pytorch 0.4.1

```
conda install pytorch=0.4.1 -c pytorch
```

More infomation please refer to https://pytorch.org/

## Training

Run train.py to train each RL algorithm

```commandline
python train.py
```

## Testing

test.py to test corresponding algorithm

```commandline
python test.py
```

The training/testing can be run in gui mode by changing sumo to sumo-gui in the sumo binary path in python files. The training results are stored in output.txt

## Appendix: SUMO 0.32.0 Setup Instruction

### 1. Install SUMO 0.32.0, which is a more up-to-date ubuntu version

ref: http://sumo.dlr.de/wiki/Installing#Linux

This version may be found in a separate ppa, which is added like this:

```
sudo add-apt-repository ppa:sumo/stable
sudo apt-get update
sudo apt-get install sumo sumo-tools sumo-doc
```

If the sumo version is not 0.32.0, please install from source code

#### Installing required tools and libraries

For the build infrastructure you will need a moderately recent g++ (4.8 will do) or clang++ together with cmake (recommended) or the autotools (autoconf / automake).
The library Xerces-C is always needed. To use **SUMO-GUI** you also need Fox Toolkit in version 1.6.x. It is highly recommended to also install Proj to have support for geo-conversion and referencing. Another common requirement is network import from shapefile (arcgis). This requires the GDAL libray. To compile you will need the devel versions of all packages. For openSUSE this means installing libxerces-c-devel, libproj-devel, libgdal-devel, and fox16-devel. There are some platform specific and manual build instructions for the libraries
Optionally you may want to add ffmpeg-devel (for video output), libOpenSceneGraph-devel (for the experimental 3D GUI) and python-devel (for running TraCI pythons scripts without a socket connection)

#### Getting the source code

For the correct setting of SUMO_HOME you have to remember the correct path, where you build your SUMO, the SUMO build path. This path is shown with pwd at the end of getting the source code

**release version or nightly tarball**
Download sumo-src-1.1.0.tar.gz or http://sumo.dlr.de/daily/sumo-src-git.tar.gz

```commandline
tar xzf sumo-src-<version>.tar.gz
cd sumo-<version>/
pwd
```

**repository checkout**
The following commands should be issued:

```commandline
git clone --recursive https://github.com/eclipse/sumo
cd sumo
git fetch origin refs/replace/*:refs/replace/*
pwd
```

The additional fetch of the replacements is necessary to get a full local project history.

**Definition of SUMO_HOME**

Before compiling is advisable (essential if you want to use Clang) to define the environment variable SUMO_HOME. SUMO_HOME must be set to the SUMO build path from the previous step. Assuming that you placed SUMO in the folder "/home/<user>/sumo-<version>", if you want to define only for the current session, type in the console

```commandline
export SUMO_HOME="/home/<user>/sumo-<version>"
```

If you want to define for all sessions (i.e. for every time that you run your Linux distribution), go to your HOME folder, and find one of the next three files (depending of your Linux distribution): .bash_profile, .bash_login or .profile (Note that these files can be hidden). Then edit the file, add the line from above at the end and restart your session.

You can check that SUMO_HOME was successfully set if you type

```commandline
echo $SUMO_HOME
```

#### Building the SUMO binaries

```commandline
./configure [options]
make
```

If you built the required libraries manually, you may need to tell the configure script where you installed them (e.g. `--with-xerces=...`). Please see the above instructions on installing required tools and libraries to find out how to do that.

Other common options to ./configure include `--prefix=$HOME` (so installing SUMO means copying the files somewhere in your home directory), `--enable-debug` (to build a version of SUMO that's easier to debug), and `--with-python` which enables the direct linking of python.

For additional options please see

```commandline
./configure --help
```

After doing make you will find all binaries in the bin subdir without the need for installation. You may of course do a make install to your intended destination as well, see below.

and console shows "/home/<user>/sumo-<version>"

For more information, which could refer to https://sumo.dlr.de/wiki/Installing/Linux_Build
