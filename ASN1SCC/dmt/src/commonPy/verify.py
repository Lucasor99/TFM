from typing import Dict, Union  # NOQA
from .utility import panic
#from commonPy.configMT import session
from . import asnAST
from .asnAST import AsnNode
from commonPy.asnParser import g_names
import re

session = None

def globalSession(modelSession):
    global session
    session=modelSession

def VerifyNodeRangeAndCreateTableConditions(node: AsnNode,name: str) -> None:

    if isinstance(node, asnAST.AsnInt):
        if not node._range:
            panic("INTEGER (in %s) must have a range constraint inside ASN.1,\n"
                  "or else we might lose accuracy during runtime!" % node.Location())
        condition='{{value}}>={min} and {{value}}<={max} '.format(min=node._range[0],max=node._range[1],name=name)

        session.execute(""" INSERT INTO DATA_VALIDATION (fieldName , condition) 
        VALUES ('{fieldName}' , '{condition}') ;
        """.format(fieldName=name,condition = condition)) 

    elif isinstance(node, asnAST.AsnReal):
        if not node._range:
            panic("REAL (in %s) must have a range constraint inside ASN.1,\n"
                  "or else we might lose accuracy during runtime!" % node.Location())
        else:
            # ASN1SCC uses C double for ASN.1 REAL.
            # this allows values from -1.7976931348623157E308 to 1.7976931348623157E308
            if node._range[0] < -1.7976931348623157E308:
                panic("REAL (in %s) must have a low limit >= -1.7976931348623157E308\n" %
                      node.Location())
            if node._range[1] > 1.7976931348623157E308:
                panic("REAL (in %s) must have a high limit <= 1.7976931348623157E308\n" %
                      node.Location())
            condition='{{value}}>={min} and {{value}}<={max} '.format(min=node._range[0],max=node._range[1],name=name)

            session.execute(""" INSERT INTO DATA_VALIDATION (fieldName , condition) 
            VALUES ('{fieldName}' , '{condition}') ;
            """.format(fieldName=name,condition = condition))         

    elif isinstance(node, asnAST.AsnString):
        if not node._range:
            panic("string (in %s) must have SIZE range set!\n" % node.Location())
        condition='len({{value}})>={min} and len({{value}})<={max} '.format(min=node._range[0],max=node._range[1],name=name)

        session.execute(""" INSERT INTO DATA_VALIDATION (fieldName , condition) 
        VALUES ('{fieldName}' , '{condition}') ;
        """.format(fieldName=name,condition = condition)) 

    elif isinstance(node, (asnAST.AsnSequenceOf, asnAST.AsnSetOf)):
        if not node._range:
            panic("SequenceOf (in %s) must have SIZE range set!\n" % node.Location())              
        nodeSeqOf = g_names[node._containedType]
        nameSeqOf = name
        if nodeSeqOf._leafType == "SEQUENCE" or nodeSeqOf._leafType == "SEQUENCEOF":
                VerifyRanges(nodeSeqOf, g_names,nameSeqOf)
        else:                 
            condition='{{value}}>={min} and {{value}}<={max} '.format(min=nodeSeqOf._range[0],max=nodeSeqOf._range[1],name=nameSeqOf)

            session.execute(""" INSERT INTO DATA_VALIDATION (fieldName , condition) 
            VALUES ('{fieldName}' , '{condition}') ;
            """.format(fieldName=nameSeqOf,condition = condition))       

    elif isinstance(node, asnAST.AsnEnumerated):
        if any(x[1] is None for x in node._members):
            panic("ENUMERATED must have integer value for each enum! (%s)" % node.Location())
        enum_values = [x[0] for x in node._members] 
        condition=' "{enum_values}".split(",")'.format(enum_values=','.join(enum_values))

        session.execute(""" INSERT INTO DATA_VALIDATION (fieldName , condition) 
        VALUES ('{fieldName}' , '{condition}');
        """.format(fieldName=name,condition = condition)) 
        
def VerifyRanges(node_or_str: Union[str, AsnNode], names: Dict[str, AsnNode],name: str) -> None:

    name = name.replace('-', '_').lower()
    if "primary_key" in name :
        name=re.sub('_primary_key.*', '', name)
    elif  "clustering_key" in name :
        name=re.sub('_clustering_key.*', '', name)   

    if isinstance(node_or_str, str):
        node = names[node_or_str]  # type: AsnNode
    else:
        node = node_or_str
   
    if isinstance(node, (asnAST.AsnMetaMember,asnAST.AsnMetaType) ): 
        node = names[node._containedType]   
    if isinstance(node, asnAST.AsnBasicNode):
        VerifyNodeRangeAndCreateTableConditions(node,name)
    elif isinstance(node, (asnAST.AsnSequence, asnAST.AsnChoice, asnAST.AsnSet)):
        for child in node._members:
            #if hasattr(child[1], "_containedType") and not child[1]._containedType in names:  
            if hasattr(child[1], "_containedType") and (not child[1]._containedType in names or isinstance(names[child[1]._containedType],(asnAST.AsnBasicNode, asnAST.AsnEnumerated,asnAST.AsnMetaType))) :
               name= '__'+ child[1]._containedType+'_'+child[0]
               name = name.replace('-', '_').lower()
               if( "primary_key" in name):
                   name=re.sub('_primary_key.*', '', name)
               elif( "clustering_key" in name):
                   name=re.sub('_clustering_key.*', '', name)       
            else:
              name = child[0]                   
            VerifyRanges(child[1], names,name)
            
    elif isinstance(node, (asnAST.AsnSequenceOf, asnAST.AsnSetOf)):
        VerifyNodeRangeAndCreateTableConditions(node,name)        
    elif isinstance(node, asnAST.AsnEnumerated):
        VerifyNodeRangeAndCreateTableConditions(node,name)
    else:
        panic("VerifyRanges: Unexpected %s\n" % str(node))

