#!/bin/bash
envName=template-env      # the name of the environment to create/update
ymlFile=templateEnv.yml     # the name of the yml file to use to update the environment
pythonFile=clonedRepo/model.py          # the name of the python file to run after the environment is updated

# update the environment with the name according to the yml file
# this command will also create an environment with that name if it doesn't exist
conda env update --name $envName --file $ymlFile --prune

# if successful, activate the environment and run the python script
if [ $? -eq 0 ]; then
    echo Environment successfully updated.
    # activate conda environment
    conda activate $envName
    python3 modelLoader.py
    bsub -m "gpu-a9-n002" -K -q "gpu" -gpu "num=4" python3 $pythonFile
    echo Cleaning up directory.
    python3 cleanup.py
    echo Deactivating conda environment.
    conda deactivate

else
    echo Failed to create/update environment.
fi
