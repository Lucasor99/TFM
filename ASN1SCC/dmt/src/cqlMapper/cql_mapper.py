import re
from typing import List, Union,Tuple 
from commonPy.asnAST import (
    AsnChoice, AsnSet, AsnSequence, AsnSequenceOf,
    AsnSetOf, AsnBasicNode, AsnSequenceOrSet,AsnMetaType,
    AsnSequenceOrSetOf, AsnEnumerated)
from commonPy.asnParser import g_names, g_leafTypeDict, AST_Leaftypes
from commonPy.utility import  warn
from commonPy.cleanupNodes import SetOfBadTypenames
import ReadWriteTMTC.createCSV  as createCSV

createTable = ''
primaryKey = ''
cleanTypenameFull=""
clusteringKey = ''
clusteringKeyList = []
session = None

def globalSession(modelSession):
    global session
    session=modelSession

def CleanName(fieldName: str) -> str:
    return re.sub(r'[^a-zA-Z0-9_]', '_', fieldName)

def CleanFullName(cleanTypenameFull: str) -> str:
    cleanTypenameFullSplit = cleanTypenameFull.split('_')
    cleanTypenameFullSorted = list(dict.fromkeys(cleanTypenameFullSplit))
    return '_'.join(cleanTypenameFullSorted)


def CommonSeqSetChoice(nodeTypename: str,
                       node: Union[AsnSet, AsnSequence, AsnChoice],
                       cleanTypenameFull = "") -> None: 
    
    cleanTypename = CleanName(nodeTypename) 
    global createTable
    global primaryKey   
    global clusteringKey
    global clusteringKeyList
   
    cleanTypenameFull= cleanTypenameFull+'_'+  cleanTypename if  cleanTypenameFull != ""  and cleanTypename !=""  else cleanTypenameFull+ cleanTypename    
    baseCqlType = {
        'INTEGER': 'int',
        'REAL': 'float',
        'BOOLEAN': 'boolean',
        'OCTET STRING': 'text',
        'ENUMERATED' : 'text'
    }    

    if isinstance(node, (AsnSequenceOf, AsnSetOf)):
        baseType = g_leafTypeDict[node._containedType] 
        for i in range(node._range[-1]):
          cleanTypenameFullSplit = cleanTypenameFull.split('_')
          cleanFieldname = '_'.join(cleanTypenameFullSplit[:-1])
          cleanFieldname = CleanFullName(cleanFieldname)+'__'+ cleanTypenameFullSplit[-1] +'_'+str(i+1)
          if baseType in baseCqlType.keys():
              createTable+=(
                '''{cleanFieldname}  {baseCqlType},    
    '''.format(cleanFieldname=cleanFieldname ,baseCqlType=baseCqlType[baseType]))  
            
          else:
            containedTypename = node._containedType
            nodeMenber = g_names[containedTypename]
            CommonSeqSetChoice('_'+str(i+1)+'_'+containedTypename,nodeMenber,cleanTypenameFull) 
    else:          
        for c in node._members:
            baseType = g_leafTypeDict[c[1]._leafType] 
            #Concatenar la primera parte del cleantypename (sequencia padre del nodo para evitar ambiguedad en los campos que se llaman igual)
            if baseType in baseCqlType.keys():
                if( "PRIMARY-KEY" in c[0]):
                     pk=re.sub('-PRIMARY-KEY.*', '', c[0])
                     primaryKey+= CleanFullName(cleanTypenameFull)+ '__'+ CleanName(c[1]._containedType)+'_'+CleanName(pk)+','
                     cleanFieldname = CleanFullName(cleanTypenameFull)+ '__'+  CleanName(c[1]._containedType)+'_'+ CleanFullName(CleanName(pk))
                elif ("CLUSTERING-KEY" in c[0]):  
                   pk=re.sub('-CLUSTERING-KEY.*', '', c[0])
                   mode = re.sub('-CLUSTERING-KEY', '', c[0]).split('-')[-1]
                   clusteringKey+= CleanFullName(cleanTypenameFull)+ '__'+CleanName(c[1]._containedType)+'_'+CleanName(pk)+'  '+mode+','
                   cleanFieldname =  CleanFullName(cleanTypenameFull)+ '__'+ CleanName(c[1]._containedType)+'_'+ CleanFullName(CleanName(pk))
                   clusteringKeyList.append(cleanFieldname)
                else:     
                 cleanFieldname =   CleanFullName(cleanTypenameFull)+ '__'+ CleanName(c[1]._containedType)+'_'+CleanName(c[0])
                createTable+=(
                '''{cleanFieldname}  {baseCqlType},  
    '''.format(cleanFieldname=cleanFieldname,baseCqlType=baseCqlType[baseType]))  
                
            elif baseType == 'SEQUENCE' or baseType == 'SEQUENCEOF':
                listMember = []
                # si fueran del mismo tipo los miembros de una suquence hay que añadir un id para diferenciarlos
                for m in node._members:
                    listMember.append(m[1]._containedType )
                if len(listMember)!=len(set(listMember)):
                        cleanTypenameFull+='_'+ CleanName(c[0])

                containedTypename = c[1]._containedType 
                nodeMenber = g_names[containedTypename]
                if(baseType == 'SEQUENCEOF' and len(CleanName(c[0]).split('_'))>1 ):
                    cleanTypenameFull+='__'+ CleanName(c[0])
                elif(baseType == 'SEQUENCE' and nodeMenber._members.__len__() == 0):
                   cleanTypenameFull+='_'+ CleanName(c[0])
                   cleanFieldname = CleanFullName(cleanTypenameFull)
                   createTable+=(
                   ''' {cleanFieldname} text,
         '''.format(cleanFieldname=cleanFieldname)) 

                else:
                 CommonSeqSetChoice(containedTypename,nodeMenber,cleanTypenameFull)   


def CreateSequence(nodeTypename: str, node: AsnSequenceOrSet) -> None:
    CommonSeqSetChoice(nodeTypename, node)

def CreateSequenceOf(nodeTypename: str, node: AsnSequenceOrSetOf) -> None:
    global createTable
    baseType = g_leafTypeDict[node._containedType]
    baseCqlType = {
    'INTEGER': 'int',
    'REAL': 'float',
    'BOOLEAN': 'boolean',
    'OCTET STRING': 'text',
    'ENUMERATED' : 'text'
    }
    cleanTypename = CleanName(nodeTypename)
     
    for i in range(node._range[-1]):
        if baseType in baseCqlType.keys():        
            cleanFieldname = cleanTypename+'_'+ str(i+1)
            createTable+=(
            '''{cleanFieldname}  {baseCqlType},    
'''.format(cleanFieldname=cleanFieldname ,baseCqlType=baseCqlType[baseType]))     
        else:
         nodeMenber = g_names[node._containedType]
         CommonSeqSetChoice(nodeTypename+'_'+str(i+1), nodeMenber )

def CreateBasic(nodeTypename: str, node: Union[AsnBasicNode, AsnEnumerated,AsnMetaType], leafTypeDict: AST_Leaftypes) -> None:
    global createTable
    global primaryKey
    global clusteringKey
    global clusteringKeyList
    baseType = node._leafType if isinstance(node, AsnEnumerated) else leafTypeDict[node._leafType]
    baseCqlType = {
    'INTEGER': 'int',
    'REAL': 'float',
    'BOOLEAN': 'boolean',
    'OCTET STRING': 'text',
    'ENUMERATED' : 'text'
    }[baseType]  
    cleanTypename = CleanName(nodeTypename)
    if( "PRIMARY_KEY" in cleanTypename):
        cleanTypename=re.sub('_PRIMARY_KEY.*', '', cleanTypename)
        primaryKey+=  cleanTypename+','

    elif ("CLUSTERING_KEY" in cleanTypename): 
        mode = re.sub('_CLUSTERING_KEY', '', cleanTypename).split('-')[-1] 
        cleanTypename=re.sub('_CLUSTERING_KEY.*', '', cleanTypename)
        clusteringKey+= cleanTypename+'  '+mode+','
        clusteringKeyList.append(cleanTypename)
    createTable+= (
            ''' {cleanTypename}  {baseCqlType}, 
    '''.format(cleanTypename=cleanTypename,baseCqlType=baseCqlType ))     


def createCQLTables(badTypes: SetOfBadTypenames,g_typesModule: Tuple[str, List[str]],moduleTelecommand: str) -> None:

    global createTable
    global primaryKey
    global clusteringKey
    global clusteringKeyList
    global session

    clusteringKey = ''
    clusteringKeyList = []
    primaryKey = ''
    createTable = ''
    typenameList = []  # type: List[str]

    for nodeTypename in sorted( g_typesModule[1]):           
        if nodeTypename in badTypes:
            continue
        if nodeTypename not in typenameList:
            typenameList.append(nodeTypename)
    
    primaryKey = ''
    tableName = CleanName(g_typesModule[0])
    createTable = ('''CREATE TABLE IF NOT EXISTS {tableName}( 
    ''' .format(tableName=tableName))

      
    for nodeTypename in typenameList:
            node = g_names[nodeTypename]
            assert nodeTypename in g_leafTypeDict
            leafType = g_leafTypeDict[nodeTypename]
            if isinstance(node, (AsnBasicNode,AsnEnumerated)):
                CreateBasic(nodeTypename, node, g_leafTypeDict)
            elif isinstance(node, (AsnSequence, AsnSet,AsnChoice)):
                CreateSequence(nodeTypename, node)
            elif isinstance(node, (AsnSequenceOf, AsnSetOf)):
                CreateSequenceOf(nodeTypename, node)
            else: 
                warn("Ignoring unsupported node type: %s (%s)" % (leafType, nodeTypename))  
    if moduleTelecommand ==   g_typesModule[0]:
           createTable += "isPending boolean , "       
    if clusteringKey == '':
        primaryKey = ''.join(primaryKey.rsplit(',', 1))             
        createTable += 'PRIMARY KEY (('+primaryKey+')) );'     
    else:
        addClusterKeys = ''
        clusteringKey = ''.join(clusteringKey.rsplit(',', 1)) 
        for ck in clusteringKeyList:
          addClusterKeys+= ck + ' , '  
        addClusterKeys = ''.join(addClusterKeys.rsplit(',', 1)) 
        createTable += 'PRIMARY KEY (('+primaryKey[:-1]+') , '+addClusterKeys +'  ) )\n'  
        createTable+= 'WITH CLUSTERING ORDER BY ('+clusteringKey +');'

    session.execute(createTable)   
    createCSV.createCSVFileModel(tableName,session)  

