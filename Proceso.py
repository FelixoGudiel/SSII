import win32security
import ntsecuritycon
import ctypes
import os
import hashlib
import shutil
import sched, time
from stat import FILE_ATTRIBUTE_HIDDEN


#Crea un directorio para guardar los archivos a indexar y supervisar
def crearDirectorioConfidencial():
    directorio = "confidencial"
    path = os.path.join(os.getcwd(), directorio)
    if (not os.path.exists(path)):
        os.mkdir(path)
        
#Crea el archivo de HIDS
def crearHIDS():
    filename = "confidencial/HIDS"
    path = os.path.join(os.getcwd(), filename)
    if (not os.path.exists(path)):
        with open(filename, "w") as file:
            file.write("")
            if os.name == 'nt':
                ctypes.windll.kernel32.SetFileAttributesW(path,
                                                        FILE_ATTRIBUTE_HIDDEN)
            
#Crea los mocks
def crearMocks():
    for i in range(5):
        filename = "confidencial/mockfile"+str(i)
        path = os.path.join(os.getcwd(), filename)
        if (not os.path.exists(path)):
            with open(filename, "w") as file:
                file.write("Contenido del mockfile numero "+str(i))

#Comprueba los ficheros actuales con el HIDS
def comprobarHIDS():
    directorio = os.path.join(os.getcwd(), "confidencial")
    with open(directorio+"/HIDS", "r+") as fileHIDS:
        for line in fileHIDS:
            parts = line.split(";")
            if (os.path.exists(directorio+"\\"+parts[0])):
                with open(directorio+"\\"+parts[0], "rb") as fileCheck:
                    bytes = fileCheck.read()
                    hash = hashlib.sha1(bytes).hexdigest()
                    if (not hash==parts[1].replace("\n", "")):
                        print("alerta! :"+ parts[0])
                        fileCheck.close()
                        restaurarFichero(parts[0])

#Escribe en el HIDS los ficheros nuevos
def escribirHIDS():
    directorio = os.path.join(os.getcwd(), "confidencial")
    for fileIter in os.listdir(directorio):
        if (fileIter!="HIDS"):
            filename = "confidencial/"+fileIter
            path = os.path.join(os.getcwd(), filename)
            with open(path, "rb") as file:
                bytes = file.read()
                hash = hashlib.sha1(bytes).hexdigest()
            file.close()
            with open(directorio+"/HIDS", "r+") as fileHIDS:
                alreadyPresent = False
                for line in fileHIDS:
                    parts = line.split(";")
                    if parts[0]==fileIter: alreadyPresent=True
                if not alreadyPresent:
                    fileHIDS.write(fileIter + ";" +hash + "\n")
            fileHIDS.close()

#Restaura un fichero basándose en la carpeta backup
def restaurarFichero(filename):
    directorioConf = os.path.join(os.getcwd(), "confidencial")
    directorioBack = os.path.join(os.getcwd(), "backup")
    os.remove(directorioConf+"\\"+filename)
    shutil.copyfile( directorioBack+ "\\" +filename, directorioConf+"\\"+filename)
    
#Crea la carpeta backup
def crearDirectorioBackup():
    directorio = "backup"
    path = os.path.join(os.getcwd(), directorio)
    if (not os.path.exists(path)):
        os.mkdir(path)
        if os.name == 'nt':
                ctypes.windll.kernel32.SetFileAttributesW(path,
                                                        FILE_ATTRIBUTE_HIDDEN)

#Llena la carpeta backup de los ficheros registrados    
def crearBackups():
    crearDirectorioBackup()
    directorio = os.path.join(os.getcwd(), "confidencial")
    with open(directorio+"/HIDS", "r+") as fileHIDS:
        for line in fileHIDS:
            parts = line.split(";")
            if (os.path.exists(directorio+"\\"+parts[0])):
                shutil.copyfile(directorio+"\\"+parts[0], os.path.join(os.getcwd(), "backup")+ "\\" + parts[0])


#Orden de eventos
def loopPrincipal(scheduler):
    scheduler.enter(10, 1, loopPrincipal, (scheduler,))
    crearDirectorioConfidencial()
    crearHIDS()
    crearMocks()
    comprobarHIDS()
    escribirHIDS()
    crearBackups()
      

my_scheduler = sched.scheduler(time.time, time.sleep)
my_scheduler.enter(10, 1, loopPrincipal, (my_scheduler,))
my_scheduler.run()

