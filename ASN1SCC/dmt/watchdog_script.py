import time
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import subprocess
import os

class Watcher:
    DIRECTORIES_TO_WATCH = [ "./filesCSV"]      #"./filesASN1",

    def __init__(self):
        self.observer = Observer()

    def run(self):
        print("Watcher iniciado. Buscando archivos en las siguientes carpetas:")
        for directory in self.DIRECTORIES_TO_WATCH:
            print(f"- {os.path.abspath(directory)}")
            event_handler = Handler(directory)
            self.observer.schedule(event_handler, directory, recursive=True)

        self.observer.start()
        try:
            while True:
                time.sleep(5)
        except KeyboardInterrupt:
            self.observer.stop()
            print("Watcher detenido.")

        self.observer.join()

class Handler(FileSystemEventHandler):
    def __init__(self, directory):
        self.directory = directory

    def on_created(self, event):
        if event.is_directory:
            return None

        if event.event_type == 'created':
            print(f"Archivo creado - {event.src_path}")
            file_name = os.path.basename(event.src_path)
            # Determina el comando a ejecutar en función del directorio
            #if self.directory == "./filesASN1" and event.src_path.endswith('.asn'):
            #    command = f"python3 src/asn2dataModel.py -keyspace tfm -contact_points cassandra -clusterPort 9042 ./filesASN1 {file_name}"
            #    print(f"python3 src/asn2dataModel.py -keyspace tfm -contact_points cassandra -clusterPort 9042 ./filesASN1 {file_name}")
                
            if self.directory == "./filesCSV" and event.src_path.endswith('.csv'):
                command = f"python3 src/ReadWriteTMTC/readCSV.py ./filesCSV -keyspace tfm -contact_points cassandra -clusterPort 9042 ./filesCSV"
            else:
                return
            
            # Ejecuta el comando
            subprocess.run(command, shell=True)

if __name__ == '__main__':
    w = Watcher()
    w.run()
