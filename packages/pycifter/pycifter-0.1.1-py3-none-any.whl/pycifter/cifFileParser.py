import numpy as np
import matplotlib.pyplot as plt
from .atom import Atom
import os

class CIFParser:
  
  def __init__(self,filePath):
    #Stores the covalent radii of the metals of interest
    self.covalentRadii={  #Taken from some paper
      "Cu":1.32,
      "Ag":1.45,
      "Au":1.36,
      "Pt":1.36,
      "Pd":1.39,
      "Hg":1.32,
      "Fe":1.52, #high spin variant
      "Ru":1.46,
    }

    self.nonMetalRadii={ 
      "N":0.71,
      "S":1.05,
    }
  
    #S-N-S
    
    myfile=open(filePath,'r')
    self.fileName=myfile.name
    self.validFile=True
    self.cellvalues={}
    self.Atoms=[]
    alllines=myfile.read().split("\n")
    '''
    Below Try catch is used to validate the file.
    If file does not contain the _atom_site_fract_z, then the file is invalid.
    This particular keyword is in all CIF files that have a structure associated with them.
    '''
    try:
      startIndex=alllines.index("_atom_site_fract_z")+1
    except:
      self.validFile=False
      return
    
    #Parsing lines and retrieving cell properties
    for i in range(startIndex): 
      if("_diffrn_ambient_temperature" in alllines[i]):
        val=(alllines[i].split(" ")[1])
        if(val=="?"): #Some files do not have a temperature associated with them
          val=283
        self.cellvalues["structure_temperature"]=(float(val))
      if("_cell_length_a" in alllines[i]):
        val=(alllines[i].split(" ")[1])
        if("(" in val): #Used to deal with the uncertainty factor in the cell length
          val=val[:val.index("(")]
        self.cellvalues["cell_length_a"]=(float(val))

      if("_cell_length_b" in alllines[i]):
        val=(alllines[i].split(" ")[1])
        if("(" in val):
          val=val[:val.index("(")]
        self.cellvalues["cell_length_b"]=(float(val))

      if("_cell_length_c" in alllines[i]):
        val=(alllines[i].split(" ")[1])
        if("(" in val):
          val=val[:val.index("(")]
        self.cellvalues["cell_length_c"]=(float(val))

      if("_cell_angle_alpha" in alllines[i]):
        val=(alllines[i].split(" ")[1])
        if("(" in val):
          val=val[:val.index("(")]
        self.cellvalues["cell_angle_alpha"]=(float(val))

      if("_cell_angle_beta" in alllines[i]):
        val=(alllines[i].split(" ")[1])
        if("(" in val):
          val=val[:val.index("(")]
        self.cellvalues["cell_angle_beta"]=(float(val))

      if("_cell_angle_gamma" in alllines[i]):
        val=(alllines[i].split(" ")[1])
        if("(" in val):
          val=val[:val.index("(")]
        self.cellvalues["cell_angle_gamma"]=(float(val))
    
    #Loading up the rows of atom coordinates and symbols
    textofInterest=alllines[startIndex:alllines.index("#END")]

    '''
    The CIF coordinate system is different from the Cartesian coordinate system.
    The file uses a spherical coordinate system to represent the atoms.
    As a result, the spherical coordinates are multiplied with an invertible conversion matrix to get the Cartesian coordinates.
    The cell values are used in conjunction with an alpha* value to get the conversion matrix.
    The alpha* value is split into a numerator and a denominator for ease of use
    The ConversionMatrix variable stores the required matrix transformation.
    '''
    astarnum=self.alphaStarNumerator()
    astardenom=self.alphaStarDenominator()

    self.cellvalues["cell_astar"]=np.arccos(astarnum/astardenom)

    ConversionMatrix=[
      [self.a(),self.b() * self.cos(self.gamma()),self.c() * self.cos(self.beta())],
                      
      [0, self.b() * self.sin(self.gamma()), -1 * self.c() * self.sin(self.beta()) * self.cos(self.cellvalues["cell_astar"])],

      [0,0,self.c() * self.sin(self.beta()) * self.sin(self.cellvalues["cell_astar"])]
      
    ]
    self.ConversionMatrix=np.array(ConversionMatrix)

    #The conversion matrix is passed to each new atom object to convert the spherical coordinates to Cartesian coordinates
    #The reason the conversion matrix is not generated in each atom itself is because its unique to each CIF file's cell values.
    for j in textofInterest:
      self.Atoms.append(Atom(j.split(" "),self.ConversionMatrix,self.covalentRadii,self.nonMetalRadii))

  '''
  Start of auxilliary functions to help store values and conduct utility operations on all atoms of a given molecule.
  '''
  def getElementAtoms(self,symbol):
    output=[]
    for j in range(len(self.Atoms)):
      if(self.Atoms[j].symbol == symbol):
        output.append(self.Atoms[j])

    return output
  
  def containsAtom(self,symbol):
    atoms=self.getElementAtoms(symbol)
    return len(atoms)>0
  def getAtomsInARadius(self,targetAtom : Atom,radius: float):
    '''
    rtype: [[Atom, float]]
    float represents the distance between Atom and the target atom
    '''
    output=[]
    for atom in self.Atoms:
      dist=atom.getDistance(targetAtom)
      if(dist<=radius):
        output.append([atom,dist])
    return output
  
  def getParticularAtom(self,identifier):
    for atom in self.Atoms:
      if(atom.identifier==identifier):
        return atom
    return "Atom Not Found"
  
  '''
  Start of getter functions to make the matrix construction easier to read
  '''
  
  def cos(self,x):
    return np.cos(x)
  
  def sin(self,x):
    return np.sin(x)
  
  
  def alphaStarNumerator(self):
    return (self.cos(self.beta()) * self.cos(self.gamma())) - self.cos(self.alpha())
  
  def alphaStarDenominator(self):
    return self.sin(self.beta()) * self.sin(self.gamma())
  

  def b(self):
    return self.cellvalues["cell_length_b"]
  
  def a(self):
    return self.cellvalues["cell_length_a"]
  
  def c(self):
    return self.cellvalues["cell_length_c"]
  
  def gamma(self):
    return np.radians(self.cellvalues["cell_angle_gamma"])
  
  def beta(self):
    return np.radians(self.cellvalues["cell_angle_beta"])
  
  def alpha(self):
    return np.radians(self.cellvalues["cell_angle_alpha"])
  


  
