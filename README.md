# The Incubator Case Study

The overall purpose of the system is to reach a certain temperature within a box and keep the temperature regardless of content.
![Incubator](figures/system.png)

An introduction to the incubator case study is given in the following publication: TODO
and the up-to-date documentation in generated in the docs folder.

# Generating and Viewing Documentation

Run/Read the script [./docs/build_docs.ps1](./docs/build_docs.ps1)

# Running the Unit Tests

## First-time setup
1. Open terminal in this folder.
2. Optional: create a virtual environment: `python -m venv venv`
3. Optional: activate the virtual environment (there are multiple possible activate scripts. Pick the one for your command line interface): 
   1. Windows Powershell:`.\venv\Scripts\Activate.ps1` 
   2. Linux/Mac: `source venv/bin/activate`
4. Install dependencies:
   1. `pip install -r ./requirements.txt`.
   
## After first time setup

Run/Read the script [./run_tests.ps1](./run_tests.ps1)

# Handling Datasets

1. Small datasets can be committed as csv files into the dataset folder.
2. Each dataset should come in its own folder, with some documentation explaining what it is all about, and a description of the physical setup.
3. Medium sized datasets should be zipped (same name as the csv file it contains, so it's easy to find when tests fail to load it).
4. Large datasets need to be put elsewhere (but a small version of the same dataset should be committed to this repo, with tests that exercise it)
