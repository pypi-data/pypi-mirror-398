import numpy as np
class Atom:
  def __init__(self, inputList,conversionMatrix,radii,nonMetalRadii):
    
    self.covalentRadius=0
    elemname=inputList.pop(0)
    self.identifier=elemname
    ind1,ind2=0,0
    for i in range(len(elemname)):
      if(str.isdecimal(elemname[i])):
        ind1=i
        break
    for i in range(len(elemname)-1,-1,-1):
      if(str.isdecimal(elemname[i])):
        ind2=i
        break
    
    if(ind1==0 and ind2==0):
      self.atomLetter=""
      self.atomNum=1
      self.element=elemname
    else:
      self.atomLetter=elemname[ind2+1:]
      self.element=elemname[:ind1]
      self.atomNum=elemname[ind1:ind2+1]



    self.symbol=inputList.pop(0)
    positionVector=[inputList.pop(0),inputList.pop(0),inputList.pop(0)]

    for v in range(3):
      elem=positionVector[v]
      if ('(' in elem ):
        positionVector[v]=float(elem[:elem.index("(")])
      else:
        positionVector[v]=float(elem)
      
    positionVector=np.array(positionVector)
    self.positionVector=np.matmul(conversionMatrix,positionVector)
    self.remainingNumbers=inputList

    if(self.symbol in radii):
      self.covalentRadius=radii[self.symbol]
    elif(self.symbol in nonMetalRadii):
      self.covalentRadius=nonMetalRadii[self.symbol]
  
  def __str__(self):
    return self.identifier
  
  def __repr__(self):
    return self.identifier
  

  def getDistance(self,other):
    distanceVector=[round(self.positionVector[i]-other.positionVector[i],6) for i in range(3)]
    output=0
    for j in distanceVector:
      output+=j**2
    
    return round(output**0.5,3)
  
  def __eq__(self, other):
    for i in range(3):
      if(self.positionVector[i]!=other.positionVector[i]):
        return False
    
    return True
  
  
  
  def __hash__(self):
    return hash(tuple(self.positionVector))
  


  