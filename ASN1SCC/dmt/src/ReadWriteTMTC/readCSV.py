import csv 
#from commonPy.configMT import session,keyspace
from cassandra.cluster import Cluster
from cassandra.auth import PlainTextAuthProvider
import sys
import re
import os

here = os.path.dirname(__file__)
sys.path.append(os.path.join(here, '..'))
import asn2dataModel
from  commonPy.utility import  panic , warn

def usage() -> None:
    '''Print usage instructions.'''
    msg = 'Usage:  Directory which contains file CSV from telemetries or telecommands to insert to BBDD %s <options>\nWhere options are:\n  '
    msg += '\t-keyspace where create the model\n'
    msg += '\t-contact_points\t\t IP or hostname to connect to cluster\n'
    msg += '\t-clusterPort\t\tport cluster to connect\n'    
    msg += '\t-filesTelecommands list of name of  the files in directory which is for telecommands.Default = None\n'   
    panic(msg % sys.argv[0])
 


def isNumberOrBoolean(s):
    """ Returns True if string is a number or boolean. """
    try:
        float(s)
        return True
    except ValueError:
        return False

if len(sys.argv) < 2 or sys.argv.count("-help") != 0:
    usage()    

sys.argv = list(map(lambda argv: argv.strip(), sys.argv))   
keyspace= asn2dataModel.getParam("-keyspace")
contact_points= asn2dataModel.getParam("-contact_points")
clusterPort= asn2dataModel.getParam("-clusterPort")

auth_provider = PlainTextAuthProvider(username=os.getenv('CASSANDRA_USER', 'cassandra'), password=os.getenv('CASSANDRA_PASSWORD'))
cluster = Cluster([contact_points], port=clusterPort, auth_provider=auth_provider)

#keyspace must be exists
session = cluster.connect(keyspace) 

files = asn2dataModel.getFilesDir(sys.argv[1])    
filesTelecommand = []

if sys.argv.count("-filesTelecommands") != 0:
    idx = sys.argv.index("-filesTelecommands")
    filesSelected = sys.argv[idx+1:]
    filesTelecommand = asn2dataModel.getFiles(filesSelected) 


#Get tables with its colummns
tablesDict={}     #Dict[str,List[str]]
tablesName = "SELECT table_name from system_schema.tables WHERE keyspace_name='%s'" % keyspace
tables = session.execute(tablesName)
for table in tables:
    table=table.table_name
    strCCQL = "SELECT column_name FROM system_schema.columns WHERE table_name='%s' ALLOW FILTERING" % table
    crows = session.execute(strCCQL)
    fields = list(map(lambda crow: crow.column_name, crows))
    tablesDict[table]= sorted(fields)


 #Get conditions
conditionDict={}     #Dict[str,str]  
fieldsCondition = session.execute('select fieldname , condition from data_validation')

for row in fieldsCondition:
    name = row.fieldname.split("__")[-1] 
    if name in conditionDict.keys(): 
        name =  row.fieldname 
    condition = row.condition
    conditionDict[name] = condition  


for file in files:
    isTelecommand =  False
    with open(file, 'r') as file:
        csvreader = csv.reader(file)
        header = next(csvreader)
        headerClean = list(map(lambda v: v.replace('-', '_').lower(), header))
        if file.name in filesTelecommand:
          isTelecommand =  True
          headerClean.append("ispending")
 
        table = [key for key, values in tablesDict.items() if values == sorted(headerClean)]

        if len(table) == 0:
            panic("there is no table for the fields in file %s" %file)
        else:
          # we check the value of the fields before insert            
            nameTable=table[0]   
            for row in csvreader:
                values= ''
                for index in range(len(row)):
                    insert = False
                    key = header[index]
                    key = key.split("__")[-1] 
                    keyCondition = key
                    # for sequenceof type
                    if "_" in key :
                       keyCondition = re.sub('_\d+', '', key)                       
                    value = row[index].split("__")[-1].strip() 
                    if value == '':
                        values+= "null ,"
                        continue
                    values+= f"{value},"   if isNumberOrBoolean(value) else f"\'{value}\'," 
                    condition = conditionDict[keyCondition].format(value=value)
                    #check if there is an enumerated.In cassandra there is no exist that type
                    if 'split(",")' in condition:
                        condition=any(value == c for c in eval(condition))
                    else:
                       condition = eval(condition)   
                    if  condition:
                        insert = True
                    else:
                        if isTelecommand:
                          message= f'Operation INSERT ABORTED!!\n  {key} contains wrong value: {value} \n {key} must be in  {conditionDict[keyCondition]}  '
                          panic(message)
                        else:    
                          message= f'WARNING!!\n {key} contains wrong value: {value} \n {key} must be in  {conditionDict[keyCondition]}  ' 
                          #warnings.warn(message) 
                          warn(message)
                
                # padding null values if there is not value
                listValues = values.split(',')[:-1]
                if len(headerClean) > len(listValues):
                    starIndex = len(listValues)
                    endIndex = len(headerClean) -1 if isTelecommand else len(headerClean) 
                    for i in range(starIndex, endIndex):
                       values+= "null ,"
                elif len(headerClean) <  len(listValues):
                    panic(" CSV file is not correct. Left columns in the file")  

                #if insert telecommands is always pending to send:
                if isTelecommand:
                  values+= "True ,"
                #delete final ',' 
                values = ''.join(values.rsplit(',', 1)) 

                # convert list of string to format (nombrevalor1,nombrevalor2,..) values ('valor1','valor2',entero1,entero2,boolean1,...)
                insertQuery = 'INSERT INTO {nameTable} ({keys}) values ({values})'.format(nameTable=nameTable,keys= ','.join(headerClean),values= values)
                print(insertQuery)
                session.execute(insertQuery )
      