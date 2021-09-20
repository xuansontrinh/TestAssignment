# TestAssignment
This script is to attempt to build and log the failed tests from the two repositories:
- `astminer`: git@github.com:JetBrains-Research/astminer.git
- `morphia`: git@github.com:MorphiaOrg/morphia.git

## Prerequisites
- Maven
- Python3.8

## Running the script
- Use the command `python analyze.py` to start the process
- The result can be found at `result/{repo_name}/`. Inside this folder is the list of files with the name to be the commit id. The content of each file includes: the first line is the result code (whether the build is successful or not), the remaining lines are the names of the tests that failed (if there are).
