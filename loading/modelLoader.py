from git import Repo
from git import rmtree
import os
import subprocess
import mlflow
import datetime
import json


# the repoLocation is just a string of the URL to the repository
# this code checks out code from the given repolocation and branch name, and from
# the given commitId if specified (if not most recent commit) and then runs that
# version of the python script
def cloneRepo(
    repoLocation, branchName, fileName, commitId=None, fileDirectory=None, config=None
):
    dest = os.path.dirname(os.path.realpath(__file__)) + "/clonedRepo"
    commitSpecified = commitId != None and commitId != ""
    repo = Repo.clone_from(
        repoLocation, dest, branch=branchName, no_checkout=commitSpecified
    )

    file = open("modelConfig.json", "w")
    addParamsToJson(repo.head.commit, config)
    json.dump(config, file)
    file.close()

    if commitSpecified:
        repo.git.checkout(commitId)

    repo.close()


def addParamsToJson(commit, config):
    config.get("gitParams")["commitAuthor"] = str(commit.author)
    config.get("gitParams")["commitMessage"] = str(commit.message)


if __name__ == "__main__":
    try:
        file = open("modelConfig.json")
        config = json.load(file)
        file.close()

        cloneRepo(
            config.get("gitParams").get("repoLocation"),
            config.get("gitParams").get("branchName"),
            config.get("gitParams").get("fileName"),
            config.get("gitParams").get("commitId"),
            fileDirectory=config.get("gitParams").get("fileDirectory"),
            config=config,
        )

    except Exception as err:
        print(str(err.with_traceback()))
        f = open("error.txt", "w")
        f.write(str(err))
        f.close()
