# Redu CLI

A command-line tool to authenticate against Redu Cloud

## Installation

## Download the .deb file
wget https://redu.cloud/redu_1.0.0_all.deb

## Fix any missing dependencies automatically
sudo apt-get install -f

redu --help

redu auth -u radmin
redu server list

## TO BUILD USING PYTHON 

pip install --upgrade build
python3 -m build
redu --help
## TO INSTALL USING PYTHON 

python3 -m venv ~/redu-cli-venv
source ~/redu-cli-venv/bin/activate
pip install --upgrade pip setuptools wheel
pip install -e .
redu --help


## TO BUILD USING .DEB
sudo rm -rf redu_1.0.0/opt/
mkdir redu_1.0.0/opt
mkdir redu_1.0.0/opt/redu
cp -r redu/ redu_1.0.0/opt/.
sudo chown -R root:root redu_1.0.0/opt/redu

dpkg-deb --build redu_1.0.0

## TO INSTALL USING .DEB
sudo dpkg -i redu_1.0.0.deb
