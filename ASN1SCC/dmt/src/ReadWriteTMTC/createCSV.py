#from commonPy.configMT import session,keyspace
from cassandra.cluster import Cluster
from cassandracsv import CassandraCsv
import csv
import os
import sys

here = os.path.dirname(__file__)
sys.path.append(os.path.join(here, '..'))
import asn2dataModel
from  commonPy.utility import  panic

def createCSVFileModel(tableName: str,session):
    query=("""SELECT * FROM {keyspace}.{tableName} """.format( tableName=tableName,keyspace=session.keyspace))
    result=session.execute(query)
    header =result.column_names  
    if "ispending" in header:
        header.remove("ispending")
    outPutDir = './templatesCSV'    
    if not os.path.exists(outPutDir):
      os.makedirs(outPutDir)            
    with open(os.path.join(outPutDir, tableName+'.csv') , 'w', encoding='UTF8', newline='') as f:
        writer = csv.writer(f)

        # write the header
        writer.writerow(header) 


def main() -> None:
    def usage() -> None:
        '''Print usage instructions.'''
        msg = 'Usage: %s <options>    Directory to place generated CSV files and list of tablenames separated by comma for create a CSV for one of them\nWhere options are:\n'
        msg += '\t-keyspace where create the model\n'
        msg += '\t-contact_points\t\t IP or hostname to connect to cluster\n'
        msg += '\t-clusterPort\t\tport cluster to connect\n'      
        msg += '\t-sendTelecommands True for generated a CSV for send the telecommands pending to send in BBDD. Default False\n'
        panic(msg % sys.argv[0])    

    def isNumberOrBoolean(s):
        """ Returns True if string is a number. """
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

    cluster = Cluster([contact_points], port=clusterPort)

    #keyspace must be exists
    session = cluster.connect(keyspace)
    sendTelecommands = False
    if sys.argv.count("-sendTelecommands") != 0:
        idx = sys.argv.index("-sendTelecommands")
        sendTelecommands = sys.argv[idx + 1]
        del sys.argv[idx]
        del sys.argv[idx]

    outPutDir= sys.argv[1]
    if not os.path.exists(outPutDir):
      os.makedirs(outPutDir)

    tables = sys.argv[2:]
    tables = list(map(lambda table: table.strip(), tables))
    tablesName = "SELECT table_name from system_schema.tables WHERE keyspace_name='%s'" % keyspace
    tablesKeyspace = session.execute(tablesName)
    tablesKeyspace = list(map(lambda table: table.table_name, tablesKeyspace))



    for table in tables:
        if not table in tablesKeyspace:
            panic("'%s' is not a table!\n" % table)  

    tablesSelected= list(set(tables)) 

    def strip_end(text, suffix):
        if suffix and text.endswith(suffix):
            return text[:-len(suffix)]
        return text


    def createCSVFile(tableName: str):

        query=("""SELECT * FROM {keyspace}.{tableName} """.format( tableName=tableName,keyspace=keyspace))
        result=session.execute(query)

        if(len(result.current_rows) == 0):
            header =result.column_names  
            with open(os.path.join(outPutDir, tableName+'.csv'), 'w', encoding='UTF8', newline='') as f:
                writer = csv.writer(f)

                # write the header
                writer.writerow(header) 

        else:
            CassandraCsv.export(
                result,
                output_dir = outPutDir,
                filename = tableName
                    )
            
    def createCSVFileToSend(tableName: str):

        query=("""SELECT * FROM {keyspace}.{tableName} WHERE ispending = True ALLOW FILTERING""".format( tableName=tableName,keyspace=keyspace))
        pkQuery=("""SELECT column_name FROM system_schema.columns WHERE keyspace_name='{keyspace}'  AND table_name='{tableName}' AND kind = 'partition_key' ALLOW FILTERING 
    """.format( tableName=tableName,keyspace=keyspace))

        result=session.execute(query)
        primaryKeys = session.execute(pkQuery).current_rows 

        header =result.column_names
        rows =result.current_rows 


        indexIsPending = header.index("ispending")
        if "ispending" in header:
            header.remove("ispending")
        pks = {}


        for pk in primaryKeys:
          index = header.index(pk.column_name)
          pks[pk.column_name] =index

    
        with open(os.path.join(outPutDir, tableName+'.csv'), 'w', encoding='UTF8', newline='') as f:
            writer = csv.writer(f)

                # write the header
            writer.writerow(header) 

            for row in rows:
                clauseWhere = ''

                for key, value in pks.items():
                  id = str(row[value]) if isNumberOrBoolean(row[value]) else "'"+ row[value]+"'"
                  clauseWhere+=  key +"="+ id+ " AND"

                clauseWhere = strip_end(clauseWhere, "AND")  
                queryUpdate =" UPDATE "+ tableName+" SET ispending = false WHERE "+ clauseWhere 
                session.execute(queryUpdate)
                data = list(row)
                del data[indexIsPending]

                # write the data
                writer.writerow(data)

                    

    if sendTelecommands:
      for tableName in tablesSelected: 
        createCSVFileToSend(tableName)
    else:
      for tableName in tablesSelected: 
        createCSVFile(tableName) 

if __name__ == "__main__":
    main()    