import os
from git import rmtree

dest = os.path.dirname(os.path.realpath(__file__)) + "/clonedRepo"
if os.path.isdir(dest):
    rmtree(dest)
