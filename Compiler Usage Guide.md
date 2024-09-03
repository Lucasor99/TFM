## ASN.1 Compiler Usage Guide

This section provides detailed instructions on how to use the ASN.1 compiler commands. These commands are essential for creating and managing models, inserting telemetry and telecommand data, and generating telecommand CSV files.

### 1. Model Creation

To create a data model from ASN.1 files, use the `asn2dataModel.py` script. This command generates database tables based on the ASN.1 schema provided.

**Command:**

```bash
python3 /path/to/asn2dataModel.py <params> <DirALLfiles> <selectedFile1 selectedFile2 ...>
```

**Parameters:**

- `<DirALLfiles>`: Directory containing all necessary ASN.1 files.
- `<selectedFile1 selectedFile2 ...>`: List of specific ASN.1 files (within `<DirALLfiles>`) to be compiled into the model. Other files in the directory are used for imported fields.

**Optional Parameters:**

- `-help`: Displays command usage instructions.
- `-modulesTelecommand "module1,module2,...”`: Specifies which modules in the selected files are for telecommands. This is optional; the default is `null`.
- `-keyspace`: Defines the keyspace where the tables will be created. If it does not exist, it will be created.
- `-contact_points`: Comma-separated list of IP addresses or names of cluster nodes to connect with.
- `-clusterPort`: Specifies the port to connect to the cluster.

**Example:**

```bash
python3 /dmt/src/asn2dataModel.py -modulesTelecommand "DataTypes-Telecommands" -keyspace tfg -contact_points cassandra -clusterPort 9042 ./filesASN1 DataTypesTelecommands.asn DataTypes-Telemetries.asn
```

This command creates a table for each defined module in the specified ASN.1 files and generates CSV templates in the `/templatesCSV` directory.

### 2. Telemetry/Telecommand Data Insertion

To insert telemetry or telecommand data into the tables, use the `readCSV.py` script. This command reads data from CSV files and inserts it into the corresponding database tables.

**Command:**

```bash
python3 /path/to/readCSV.py <DirFilesCSV> <params>
```

**Parameters:**

- `<DirFilesCSV>`: Directory containing the CSV files, each corresponding to a table.

**Optional Parameters:**

- `-help`: Displays command usage instructions.
- `-keyspace`: Specifies the keyspace where the tables are located. If it doesn't exist, an error is thrown.
- `-contact_points`: Comma-separated list of IP addresses or names of cluster nodes to connect with.
- `-clusterPort`: Specifies the port to connect to the cluster.
- `-filesTelecommands "file1 file2 ..."`: Indicates which files in `<DirFilesCSV>` are for telecommands. This is optional; the default is `null`.

**Example:**

```bash
python3 /dmt/src/ReadWriteTMTC/readCSV.py ./filesCSV -keyspace tfg -contact_points cassandra -clusterPort 9042 -filesTelecommands datatypes_telecommands.csv
```

This command validates and inserts data into the tables, distinguishing between telemetry and telecommands. If a telemetry data field is invalid, a warning is logged, and the data is still stored. However, invalid telecommands are not inserted to prevent erroneous data from being sent.

### 3. Telecommand Creation

To generate CSV files for telecommands, use the `createCSV.py` script. This command creates CSV files based on existing tables and can optionally mark telecommands as sent.

**Command:**

```bash
python3 /path/to/createCSV.py <outputDir> <tables> <params>
```

**Parameters:**

- `<outputDir>`: Directory where the CSV files will be created. If it doesn't exist, it will be created.
- `<tables>`: Comma-separated list of tables from which to generate CSV files.

**Optional Parameters:**

- `-help`: Displays command usage instructions.
- `-keyspace`: Specifies the keyspace where the tables are located. If it doesn't exist, an error is thrown.
- `-contact_points`: Comma-separated list of IP addresses or names of cluster nodes to connect with.
- `-clusterPort`: Specifies the port to connect to the cluster.
- `-sendTelecommands`: If `True`, the command will mark the telecommands as sent after generating the CSV file. The default is `False`.

**Example:**

```bash
python3 /dmt/src/ReadWriteTMTC/createCSV.py ./filesTelecommand "datatypes_telecommands" -keyspace tfg -contact_points cassandra -clusterPort 9042 -sendTelecommands True
```

This command generates a CSV file for each specified table and, if `-sendTelecommands` is `True`, marks the telecommands as sent in the database.

### Table Format

The generated CSV files follow a specific format to ensure consistency and avoid ambiguity. Nested values are flattened with an underscore (`_`) separator, and repeated elements are removed while maintaining the order. Each table must have at least one primary key defined, which can only be a basic type (except boolean), and clustering keys can also be declared.

**Example:**

```asn1
BASIC-A-PRIMARY-KEY ::= INTEGER (0 .. 255)
BASIC-B-CLUSTERING-KEY-ASC ::= Epoch-Type
PRIMARY-KEY ::= SEQUENCE {
    BASIC-C-PRIMARY-KEY Epoch-Type,
    BASIC-D-CLUSTERING-KEY-DESC Heater-Power-Type
}
```

In this example, the table columns are named according to the structure of the ASN.1 schema, with underscores separating the nested fields.

This guide provides the necessary steps to work with the ASN.1 compiler in the context of a satellite ground station application. Proper understanding and use of these commands ensure the successful management of telemetry and telecommand data in the system.
