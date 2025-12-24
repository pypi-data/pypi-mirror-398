class Graph:
  def __init__(self,atomList,angle):
    self.left=atomList[0]
    self.center=atomList[1]
    self.right=atomList[2]
    self.bondAngle=angle
    self.structure={}
    for atom in atomList:
      self.structure[atom]=[]
      for j in atomList:
        if(atom!=j):
          self.structure[atom].append((j,atom.getDistance(j)))
    
  def __str__(self):
    output=""
    for key in self.structure.keys():
      output+=f"{key}|{key.symbol} : {self.structure[key]}\n"
    output+=f"Angle: {self.bondAngle}"
    return output
  
  def addBond(self,existingAtom,newAtom,distance):
    self.structure[existingAtom].append((newAtom,distance))
    self.structure[newAtom]=[]
    self.structure[newAtom].append((existingAtom,distance))
  
  def returnAtoms(self,symbol):
    output=[]
    keyList=list(self.structure.keys())
    for key in keyList:
      if(key.symbol==symbol):
        output.append(key)
    return output
