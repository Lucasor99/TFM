
from typing import Set, Union, Dict

from . import asnParser
from .asnAST import (
     AsnChoice, AsnSet, AsnSequenceOf, AsnSequence,
     AsnSetOf, AsnNode,AsnBasicNode
)
from  commonPy.utility import  panic
SetOfBadTypenames = Set[str]
possibleKeys = []
isPrimaryKey = False
def DiscoverBadTypes(g_nodesFile: Dict[str, AsnNode], g_modulesFilesSelected: Dict[str, str]) -> SetOfBadTypenames:
    '''
    This returns a dictionary that tells us which types to skip
    over during type mappings.It includes node Members
    and types which are referenced by members
    '''
    badTypes = set()  # type: SetOfBadTypenames
    cache = {}  # type: Dict[AsnNode, bool]
    global isPrimaryKey
    names = g_nodesFile

    def throwPimaryKeyError(module: asnParser.Module) -> None:
        error = " A PRIMARY KEY of  BASIC NODE  must be defined for  module '%s' with the next format: \n"
        error+=" id-PRIMARY-KEY ::=  basicTypeorReferenceType "  
        panic(error % module)     

    def CheckNodeForMetaMember(node_or_str: Union[AsnNode, str]) -> bool:
        global isPrimaryKey
        if isinstance(node_or_str, str):
            node = names[node_or_str]  # type: AsnNode
        else:
            node = node_or_str

        if node in cache:
            return cache[node] 

        if isinstance(node, (AsnSequenceOf,AsnSetOf)):
           nodeMember = node._containedType
           if nodeMember in keys:
            CheckNodeForMetaMember(names[nodeMember])
            badTypes.add(nodeMember)
        if isinstance(node, (AsnChoice, AsnSequence, AsnSet)):
            for child in node._members:
                key = child[1]._containedType  
                if  "PRIMARY-KEY" in child[0]:                
                  if   isinstance( asnParser.g_names[key], (AsnBasicNode)): # it is a basic node
                   isPrimaryKey = True 
                  else:
                   throwPimaryKeyError(module)

                #There is not basic members  in gnames
                # if there is , it means it a type referenced and has to be adding to badtypes
                if key in keys:
                    CheckNodeForMetaMember(names[key])
                    badTypes.add(child[1]._containedType)

      
  
    for module in g_modulesFilesSelected:    
      isPrimaryKey = False    
      keys = g_modulesFilesSelected[module]
      for key in keys:
        if  "PRIMARY-KEY" in key:
         if   isinstance( asnParser.g_names[key], (AsnBasicNode)): # it is a basic node
            possibleKeys.append(key) # only key if it is not referenced by other
         else:
            throwPimaryKeyError(module)
        nodeAST = names[key]
        if key not in badTypes:
          CheckNodeForMetaMember(nodeAST)        
      for pk in possibleKeys:
         if pk not in badTypes:
            isPrimaryKey = True
            continue
      if not isPrimaryKey:
          throwPimaryKeyError(module)         
    return badTypes      
    # Se busca eliminar a los subnodos members(para crear la table  es mejor ir recorriendo desde el primer nodo)
    """"
    for nodeName in possibleKeys:
       if(nodeName not in badTypes):
          isPrimaryKey = True
             
    if not isPrimaryKey:
        error = "A PRIMARY KEY of  BASIC TYPE or REFERENCE TYPE must be defined for  module '%s' with the next format: \n"
        error+=" id-PRIMARY-KEY ::=  basicTypeorReferenceType " 
        panic(error % module)
            
    return badTypes
    """



