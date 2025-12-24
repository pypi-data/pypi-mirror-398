# TFSI Crystallography Analysis using PyCIFTer

This repository contains Python code for PyCIFTer, a program I made to analyze X-ray crystallographic data of bis(trifluoromethanesulfonyl)imide (TFSI) compounds. View at:

[Published Article](https://www.mdpi.com/1420-3049/31/1/18#B62-molecules-31-00018)

[Graphs Dashboard Here](https://tfsi-research.vercel.app/)

## Overview

Chemical data science is an emerging field within the broader field of chemistry that has numerous applications of high relevance to a variety of academic and industrial pursuits. With quantum computing and artificial intelligence becoming more mainstream, it is of great interest for not only the data scientist, but the chemist as well, to take advantage of these technologies to streamline data processing, analyze large data sets, and reveal new chemical insights that would be otherwise hidden by the sheer amount and depth/complexity of available data. In this project, modern computing and fundamental chemical analysis have been combined in order to pursue new insights into the structural behavior of the weakly coordinating anion bis(trifluoromethylsulfonyl)imide, otherwise known as TFSI. Taking a data science approach, published solid-state crystal structures available in the Cambridge Structural Database (CSD) including one or more TFSI species of interest were categorized and statistically analyzed using software built for this purpose. The goal of this project from a chemical perspective was to determine the structural characteristics displayed by TFSI as inferred from the structural data. The goal of this project from a data-science perspective was to develop a new software program using Python to parse Crystallographic Information Files (CIF) obtained from the CSD into statistically relevant information that could be compared across the individual structural data sets. This research endeavor aims to highlight the applications of data science to an otherwise foreign area of research (structural chemistry) and outline the capabilities of data processing for future structural and chemical investigations.

## Features

- Import and parse CIF (Crystallographic Information File) data
- Analyze TFSI bond lengths and angles
- Visualize TFSI molecular structure
- Perform statistical analysis on crystallographic parameters

## Requirements

The tool uses python. The latest version of the program was run using python 3.14 but anything above 3.10 will suffice. The requirements.txt file has all the packages required for running the tool.

Install the required packages using pip:

```bash
pip install pycifter
```

## Components of PyCIFTer

- `index.py` : Main script used in research to demonstrate effectiveness of pycifter. Executes the main analysis pipeline
- `cifFileParser.py`: TFSI structural analysis functions
- `render.py`: Plotting and visualization functions
- `heatmap.py`: Interactive rendering

## cifFileParser.py - Utility functions

- `getElementAtoms(self, symbol)` : Returns a list of atoms with a particular symbol after linearly searching through self.Atoms[].
- `containsAtom(self, symbol)` : Checks whether the current molecule contains an atom of given symbol.
- `getAtomsInARadius(self, targetAtom, radius)` : returns a list of atoms after performing a wave emanating search of size ‘radius’. The function looks for all atoms with a Euclidean distance of less than radius and returns a list.
- `getParticularAtom(self, identifier)` : Returns a particular atom object based on its identifier (ex. C57).

## Atom.py - Utility functions

- `getDistance(self,other)` : Returns the Euclidean distance between the position vectors of the current atom and the “other” atom.
- `__eq__(self,other)` : Operator overload for the “==” operator. Makes it so that if two atoms and compared using the “==” operator, the output depends on whether the two atoms have the exact same position vector, whereas otherwise the “==” would compare the two objects’ memory addresses.
- `__hash__(self)` : Defines what should the hashing input be when generating the hash of an atom. The position vector is unique to each atom and thus, is used as a hashing input.

The current version of the software is a pre-alpha version built for research purposes. I will continue working on this project adding more robust features to the CIFParser class. See my project on Crown Ethers for another example of molecular analysis with PyCIFTer.

## License

MIT License
