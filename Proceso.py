import ctypes
import os
import hashlib
import shutil
import sched, time
from stat import FILE_ATTRIBUTE_HIDDEN
from datetime import datetime

AVISOS = 0
ACIERTOS = 0
REVISIONES = 0

DRIVE_LETTER = os.path.splitdrive(os.getcwd())[0]
SECCIONTIEMPO = 1
# Crea el fichero de configuración
def crearConfig():
    filename = "config"
    directorio = "confidencial"
    path = os.path.join(os.getcwd(), filename)
    dirpath = os.path.join(os.getcwd(), directorio)
    if not os.path.exists(path):
        with open(path, "w") as file:
            file.write("Rutas de carpetas a conservar: \n" + dirpath + "\n" +
                       "Tiempo entre comprobaciones (segundos): \n10 \n"+
                       "Correo electrónico (opcional): \nfelixangelgudiel@gmail.com")

#Lee el fichero de configuración
def leerConfig():
    filename = "config"
    path = os.path.join(os.getcwd(), filename)
    with open(path, "r") as file:
        lastCheckoint = ""
        seccionRutas = []
        for line in file:
            if not line.startswith("Rutas"):
                if lastCheckoint == "":
                    if line.startswith("Tiempo"):
                        lastCheckoint ="Tiempo entre comprobaciones (segundos): "
                    else:
                        seccionRutas.append(line.replace("\n", ""))
                if lastCheckoint =="Tiempo entre comprobaciones (segundos): ":
                    if line.startswith("Correo"):
                        lastCheckoint ="Correo electrónico (opcional): "
                    else:
                        seccionTiempo = line.replace("\n", "")
                if lastCheckoint =="Correo electrónico (opcional): ":
                    seccionCorreo = line.replace("\n", "")
        file.close()
    return(seccionRutas, int(seccionTiempo), seccionCorreo)
# Crea un directorio para guardar los archivos a indexar y supervisar
def crearDirectorioConfidencial():
    directorio = "confidencial"
    path = os.path.join(os.getcwd(), directorio)
    if not os.path.exists(path):
        os.mkdir(path)


# Crea el archivo de HIDS
def crearHIDS():
    filename = "confidencial/HIDS"
    path = os.path.join(os.getcwd(), filename)
    if not os.path.exists(path):
        with open(filename, "w") as file:
            file.write("")
            if os.name == "nt":
                ctypes.windll.kernel32.SetFileAttributesW(path, FILE_ATTRIBUTE_HIDDEN)


# Crea los mocks
def crearMocks():
    for i in range(5):
        filename = "confidencial/mockfile" + str(i)
        path = os.path.join(os.getcwd(), filename)
        if not os.path.exists(path):
            with open(filename, "w") as file:
                file.write("Contenido del mockfile numero " + str(i))


# Comprueba los ficheros actuales con el HIDS
def comprobarHIDS():
    directorio = os.path.join(os.getcwd(), "confidencial")
    with open(directorio + "/HIDS", "r+") as fileHIDS:
        for line in fileHIDS:
            parts = line.split(";")

            if os.path.exists(DRIVE_LETTER + "\\" + parts[0]):
                with open(DRIVE_LETTER + "\\" +parts[0], "rb") as fileCheck:
                    bytes = fileCheck.read()
                    hash = hashlib.sha1(bytes).hexdigest()
                    if not hash == parts[1].replace("\n", ""):
                        currentDate = datetime.now()
                        logName = "logs/avisos/log_" + currentDate.strftime("%d-%m-%Y")
                        logText = (
                            "ALERTA "
                            + str(currentDate.strftime("%d-%m-%Y %H:%M:%S"))
                            + ": El fichero "
                            + "[ "
                            + parts[0]
                            + " ]"
                            + " ha sido modificado"
                        )
                        with open(logName, "a") as logFile:
                            logFile.write(logText + "\n")
                        fileCheck.close()
                        global AVISOS
                        AVISOS += 1
                        restaurarFichero(parts[0])
                    else:
                        global ACIERTOS
                        ACIERTOS += 1
        global REVISIONES
        REVISIONES += 1


# Crea un informe cada 30 revisiones
def crearInforme():
    global AVISOS
    global REVISIONES
    global ACIERTOS

    currentDate = datetime.now()
    logName = "logs/informes/informe_" + currentDate.strftime("%d-%m-%Y %Hh%Mm%Ss")
    logText = (
        "INFORME "
        + str(currentDate.strftime("%d-%m-%Y %H:%M:%S"))
        + ": Se han realizado "
        + str(REVISIONES)
        + "\n"
        + "Avisos: "
        + str(AVISOS)
        + "\n"
        + "Aciertos: "
        + str(ACIERTOS)
        + "\n"
        + "Ratio de aciertos: "
        + str(round((ACIERTOS / (AVISOS + ACIERTOS)) * 100, 2))
        + "% \n"
    )
    with open(logName, "a") as logFile:
        logFile.write(logText + "\n")

    AVISOS = 0
    ACIERTOS = 0
    REVISIONES = 0


# Escribe en el HIDS los ficheros nuevos
def escribirHIDS(seccionRuta):
    for directorio in seccionRuta:
        for fileIter in os.listdir(directorio):
            if fileIter != "HIDS":
                filename = "confidencial\\" + fileIter
                path = os.path.join(os.getcwd(), filename)
                with open(path, "rb") as file:
                    bytes = file.read()
                    hash = hashlib.sha1(bytes).hexdigest()
                file.close()
                with open(directorio + "/HIDS", "r+") as fileHIDS:
                    alreadyPresent = False
                    for line in fileHIDS:
                        parts = line.split(";")
                        if parts[0] == os.path.join(os.getcwd(), filename).replace("C:\\", ""):
                            alreadyPresent = True
                    if not alreadyPresent:
                        fileHIDS.write(os.path.join(os.getcwd(),filename).replace("C:\\", "") + ";" + hash + "\n")
                fileHIDS.close()


# Restaura un fichero basándose en la carpeta backup
def restaurarFichero(filename):
    directorioBack = os.path.join(os.getcwd(), "backup")
    os.remove(DRIVE_LETTER +"\\" + filename)
    shutil.copyfile(directorioBack + "\\" + filename, DRIVE_LETTER +"\\" + filename)


# Crea la carpeta backup
def crearDirectorioBackup():
    directorio = "backup"
    path = os.path.join(os.getcwd(), directorio)
    if not os.path.exists(path):
        os.mkdir(path)
        if os.name == "nt":
            ctypes.windll.kernel32.SetFileAttributesW(path, FILE_ATTRIBUTE_HIDDEN)


# Llena la carpeta backup de los ficheros registrados
def crearBackups():
    crearDirectorioBackup()
    directorio = os.path.join(os.getcwd(), "confidencial")
    with open(directorio + "/HIDS", "r+") as fileHIDS:
        for line in fileHIDS:
            parts = line.split(";")
            if os.path.exists(DRIVE_LETTER + "\\" + parts[0]):
                currentFolder = os.path.join(os.getcwd(), "backup")
                for folder in parts[0].split("\\")[:-1]:
                    if not os.path.exists(os.path.join(currentFolder, folder)):
                        os.mkdir(os.path.join(currentFolder, folder))
                    currentFolder += "\\" +folder  
                shutil.copyfile(
                    DRIVE_LETTER+ "\\" + parts[0],
                    os.path.join(os.getcwd(), "backup") + "\\" + parts[0]
                )


# Crea la carpeta logs
def crearDirectorioLogs():
    directorio = "logs"
    directorios = ["avisos", "informes"]
    path = os.path.join(os.getcwd(), directorio)
    if not os.path.exists(path):
        os.mkdir(path)

    for dir in directorios:
        path = os.path.join(os.getcwd(), "logs", dir)
        if not os.path.exists(path):
            os.mkdir(path)


# Orden de eventos
def loopPrincipal(scheduler):
    crearConfig()
    seccionRuta, SECCIONTIEMPO, seccionCorreo = leerConfig()
    crearDirectorioConfidencial()
    crearDirectorioLogs()
    crearHIDS()
    crearMocks()
    comprobarHIDS()
    escribirHIDS(seccionRuta)
    crearBackups()
    if REVISIONES % 30 == 0:
        crearInforme()
    scheduler.enter(SECCIONTIEMPO, 1, loopPrincipal, (scheduler,))

print("=== HIDS STARTED ===")
my_scheduler = sched.scheduler(time.time, time.sleep)
my_scheduler.enter(1, 1, loopPrincipal, (my_scheduler,))
my_scheduler.run()
