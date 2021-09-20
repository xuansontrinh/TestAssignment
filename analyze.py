import os
import re
import shutil
import subprocess

from abc import ABC, abstractmethod

FILE_PATH = os.path.dirname(os.path.abspath(__file__))

REPOSITORIES = {
    "morphia": "git@github.com:MorphiaOrg/morphia.git",
    "astminer": "git@github.com:JetBrains-Research/astminer.git"
}

SPECIAL_COMMANDS = {
    "morphia": "mvn install -DskipTests && MONGODB=4.4.6 mvn surefire:test -Ddriver.version=4.2.3"
}

class CommonUtils():

    @staticmethod
    def cloneRepo(repoName):
        reposPath = os.path.join(FILE_PATH, "data")
        os.makedirs(reposPath, exist_ok=True)
        subprocess.run(f'cd {reposPath} && git clone {REPOSITORIES[repoName]}', shell=True, capture_output=True)

    @staticmethod
    def getLatestNCommits(path, N=100):
        proc = subprocess.run(f'cd {path} && (git log -{N} --pretty=format:"%h" | cat)', shell=True, capture_output=True)
        if proc.returncode == 0: return proc.stdout.decode("utf-8").splitlines()
        else: return []    

    @staticmethod
    def checkoutCommit(path, commit):
        subprocess.run(f'cd {path} && git checkout {commit}', shell=True, capture_output=True)

    @staticmethod
    def getRepoPath(repoName):
        return os.path.join(FILE_PATH, "data", repoName)

    @staticmethod
    def getBuildHandler(repoName):
        if os.path.isfile(os.path.join(CommonUtils.getRepoPath(repoName), "gradlew")):
            return GradleBuildHandler(repoName)
        elif os.path.isfile(os.path.join(CommonUtils.getRepoPath(repoName), "pom.xml")):
            return MavenBuildHandler(repoName)
        else:
            return None



class AbstractBuildHandler(ABC):
    def __init__(self, repoName) -> None:
        self.repoName = repoName
        self.repoPath = CommonUtils.getRepoPath(repoName)
    
    @abstractmethod
    def runBuild(self):
        pass


class GradleBuildHandler(AbstractBuildHandler):
    def runBuild(self):
        proc = subprocess.run(f'cd {self.repoPath} && {SPECIAL_COMMANDS[self.repoName] if self.repoName in SPECIAL_COMMANDS else "./gradlew :build"}', shell=True, capture_output=True)

        if proc.returncode != 0:
            errors = proc.stdout.decode("utf-8").splitlines()
            return proc.returncode, [error.split(" ")[-2] for error in errors if re.search(" > \w+ FAILED$", error)]
        else: return proc.returncode, []
            

class MavenBuildHandler(AbstractBuildHandler):
    def runBuild(self):
        proc = subprocess.run(f'cd {self.repoPath} && {SPECIAL_COMMANDS[self.repoName] if self.repoName in SPECIAL_COMMANDS else "mvn test"}', shell=True, capture_output=True)

        if proc.returncode != 0:
            errors = proc.stdout.decode("utf-8").splitlines()
            return proc.returncode, [error.split(" ")[0] for error in errors if re.search(" Time elapsed: .+ <<< FAILURE!$", error) and not error.startswith("Tests run")]
        else: return proc.returncode, []

# clone repositories
for repoName in REPOSITORIES:
    if not os.path.isdir(CommonUtils.getRepoPath(repoName)):
        print(f'Cloning repo {repoName} ...')
        CommonUtils.cloneRepo(repoName)

# Remove result folder from last time if exists
resPath = os.path.join(FILE_PATH, "result")
shutil.rmtree(resPath, ignore_errors=True)
            
for repoName in REPOSITORIES:
    repoPath = CommonUtils.getRepoPath(repoName)
    repoResPath = os.path.join(resPath, repoName)
    handler = CommonUtils.getBuildHandler(repoName)
    os.makedirs(repoResPath, exist_ok=True)

    NLatestCommits = CommonUtils.getLatestNCommits(repoPath)
    for count, commit in enumerate(NLatestCommits):
        print(f"Analyzing {count + 1}-th latest commit of repo {repoName} ({commit}) ...")
        CommonUtils.checkoutCommit(repoPath, commit)
        statusCode, errors = handler.runBuild()
        commitPath = os.path.join(repoResPath, commit)
        with open(commitPath, "w") as file:
            file.write(statusCode + '\n')
            for error in errors:
                file.write(error + '\n')

