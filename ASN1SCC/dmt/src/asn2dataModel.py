import os
import sys
import copy

from typing import  Dict, Tuple, List,Set  
#from commonPy.configMT import  session
from  commonPy import cleanupNodes , asnParser , verify  
from  commonPy.utility import  panic
from commonPy.asnParser import Filename, AST_Lookup, AST_Leaftypes  
from commonPy.asnAST import AsnNode 
import cqlMapper.cql_mapper as cql_mapper
from cassandra.cluster import Cluster
from cassandra.auth import PlainTextAuthProvider


def usage() -> None:
    '''Print usage instructions.'''
    msg = 'Usage: %s <options> directory which contains file ASN1  and files you want read (input1.asn1 [input2.asn1]...)\nWhere options are:\n'
    msg += '\t-modulesTelecommand : modules  of  the files selected  which are for telecommands.format is in one param ("module1,module2,..") Default = None \n '
    msg += '\t-keyspace where create the model\n'
    msg += '\t-contact_points\t\t IP or hostname to connect to cluster\n'
    msg += '\t-clusterPort\t\tport cluster to connect\n'
    panic(msg % sys.argv[0])




#This form is to read files in a directory
def getFilesDir(directory: str)  -> List[str]:
    directory = directory.strip() 
    files = os.listdir(directory)   
    files = list(map(lambda file: os.path.join(directory, file.strip()), files))    
    for f in files:
        if not os.path.isfile(f):
            panic("'%s' is not a file!\n" % f) 
    uniqueFilenames = list(set(files))
    return uniqueFilenames

#This form is to read files in a directory
def getFiles(files: List[str])  -> List[str]:
    directory = sys.argv[1].strip()    
    files = list(map(lambda file: os.path.join(directory, file.strip()), files))   
    for file in files:
        if not os.path.isfile(file):
            panic("there is no file: '%s' in files selected " %file)
    uniqueFilenames = list(set(files))
    return uniqueFilenames

def getParam(param: str,optional: bool = False)  -> str:
    if sys.argv.count(param) != 0:
        idx = sys.argv.index(param)
        param = sys.argv[idx + 1]
        del sys.argv[idx]
        del sys.argv[idx]
        return param
    elif optional:
        return None
    else:
        panic(" param '%s' must be defined " % param)
        usage() 

def createSession(keyspace: str,contact_points: str,clusterPort: int) -> Cluster:
    auth_provider = PlainTextAuthProvider(username=os.getenv('CASSANDRA_USER', 'cassandra'), password=os.getenv('CASSANDRA_PASSWORD'))
    cluster = Cluster([contact_points], port=clusterPort, auth_provider=auth_provider)
    session=cluster.connect()
    session.execute("CREATE KEYSPACE IF NOT EXISTS %s WITH REPLICATION = { 'class' : 'SimpleStrategy', 'replication_factor' : '3' }"  % keyspace)
    session.set_keyspace(keyspace)
    cql_mapper.globalSession(session)
    verify.globalSession(session)
    return session

session = None

def main() -> None:

    sys.argv = list(map(lambda argv: argv.strip(), sys.argv))   
    if sys.argv.count("-help") != 0 or len(sys.argv) < 3:
        usage()

    global session
    modulesTelecommand  =  getParam("-modulesTelecommand",True)
    keyspace= getParam("-keyspace")
    contact_points= getParam("-contact_points")
    clusterPort= getParam("-clusterPort")

    session = createSession(keyspace,contact_points,int(clusterPort))   
    if len(sys.argv) < 3:
        usage()
    
    uniqueFilenames = getFilesDir(sys.argv[1])

    filesSelected= getFiles(sys.argv[2:])  
    
    asnParser.ParseAsnFileList(uniqueFilenames) 

    badTypes = Set[str]
    g_namesFilesSelected = {}  # type: AST_Lookup
    g_modulesFilesSelected = {}  # type: AST_Lookup
    createTableValidation = '''CREATE TABLE IF NOT EXISTS DATA_VALIDATION (
        fieldName text PRIMARY KEY ,
        condition text ); '''
    session.execute(createTableValidation)
    dictModules = asnParser.g_modules
    uniqueASNfiles = {}  # type: Dict[Filename, Tuple[AST_Lookup, List[AsnNode], AST_Leaftypes]]
    for asnFile in filesSelected:
        for name in asnParser.g_typesOfFile[asnFile]:
            g_namesFilesSelected[name] = asnParser.g_names[name]
            for module in asnParser.g_modulesOfFile[asnFile]:
               g_modulesFilesSelected[module] = dictModules[module]
      
        uniqueASNfiles[asnFile] = ( copy.copy(g_namesFilesSelected) , copy.copy(g_modulesFilesSelected))
        badTypes = cleanupNodes.DiscoverBadTypes(g_namesFilesSelected,g_modulesFilesSelected)

        #Create table with conditions
        for node in list(g_namesFilesSelected):
            if not node in badTypes:
             verify.VerifyRanges(g_namesFilesSelected[node], asnParser.g_names,node)

    if  modulesTelecommand is not None:
        for module in  modulesTelecommand.split(','):
            if module.strip() not in g_modulesFilesSelected:
                panic("module for telecommands '%s' not found" % module) 

    for asnFile in filesSelected:
        g_namesFilesSelected = uniqueASNfiles[asnFile][0]
        g_modulesFilesSelected = uniqueASNfiles[asnFile][1]
        for module in g_modulesFilesSelected.items():
          cql_mapper.createCQLTables(badTypes,module,modulesTelecommand)
    session.shutdown()    
if __name__ == "__main__":
    main()
