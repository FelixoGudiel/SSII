import ctypes
import os
import hashlib
import shutil
import sched, time
from stat import FILE_ATTRIBUTE_HIDDEN
from datetime import datetime
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail

AVISOS = 0
ACIERTOS = 0
REVISIONES = 0
SENDGRID_API_KEY = ""
DRIVE_LETTER = os.path.splitdrive(os.getcwd())[0]


# Crea el fichero de configuración
def crearConfig():
    filename = "config"
    directorio = "confidencial"
    path = os.path.join(os.getcwd(), filename)
    dirpath = os.path.join(os.getcwd(), directorio)
    if not os.path.exists(path):
        with open(path, "w", encoding="utf-8") as file:
            file.write(
                "Rutas de carpetas a conservar: \n"
                + dirpath
                + "\n"
                + "Tiempo entre revisiones (segundos): \n10 \n"
                + "Número de revisiones por informe: \n30 \n"
                + "Correo electrónico (opcional): \ntest@gmail.com\n"
            )


# Lee el fichero de configuración
def leerConfig():
    filename = "config"
    path = os.path.join(os.getcwd(), filename)
    with open(path, "r", encoding="utf-8") as file:
        lastCheckoint = ""
        seccionRutas = []
        seccionTiempo = 0
        for line in file:
            if not line.startswith("Rutas"):
                if lastCheckoint == "":
                    if line.startswith("T"):
                        lastCheckoint = "Tiempo entre revisiones (segundos): "
                    else:
                        seccionRutas.append(line.replace("\n", ""))
                elif lastCheckoint == "Tiempo entre revisiones (segundos): ":
                    if line.startswith("N"):
                        lastCheckoint = "Número de revisiones por informe: "
                    else:
                        seccionTiempo = line.replace("\n", "")
                elif lastCheckoint == "Número de revisiones por informe: ":
                    if line.startswith("C"):
                        lastCheckoint = "Correo electrónico (opcional): "
                    else:
                        seccionRevisiones = line.replace("\n", "")
                elif lastCheckoint == "Correo electrónico (opcional): ":
                    seccionCorreo = line.replace("\n", "")
        file.close()
    return (seccionRutas, int(seccionTiempo), int(seccionRevisiones), seccionCorreo)


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
        with open(filename, "w", encoding="utf-8") as file:
            file.write("")
            if os.name == "nt":
                ctypes.windll.kernel32.SetFileAttributesW(path, FILE_ATTRIBUTE_HIDDEN)


# Crea los mocks
def crearMocks():
    for i in range(5):
        filename = "confidencial/mockfile" + str(i)
        path = os.path.join(os.getcwd(), filename)
        if not os.path.exists(path):
            with open(filename, "w", encoding="utf-8") as file:
                file.write("Contenido del mockfile numero " + str(i))


def crearLogFile(parts, text):
    currentDate = datetime.now()
    logName = "logs/avisos/log_" + currentDate.strftime("%d-%m-%Y")
    logText = (
        "ALERTA "
        + str(currentDate.strftime("%d-%m-%Y %H:%M:%S"))
        + ": El fichero "
        + "[ "
        + parts[0]
        + " ]"
        + text
    )
    with open(logName, "a", encoding="utf-8") as logFile:
        logFile.write(logText + "\n")


# Comprueba los ficheros actuales con el HIDS
def comprobarHIDS():
    directorio = os.path.join(os.getcwd(), "confidencial")
    with open(directorio + "/HIDS", "r+", encoding="utf-8") as fileHIDS:
        for line in fileHIDS:
            parts = line.split(";")
            if os.path.exists(DRIVE_LETTER + "\\" + parts[0]):
                with open(
                    DRIVE_LETTER + "\\" + parts[0],
                    "rb",
                ) as fileCheck:
                    bytes = fileCheck.read()
                    hash = hashlib.sha1(bytes).hexdigest()
                    if not hash == parts[1].replace("\n", ""):
                        mandarCorreo(seccionCorreo, DRIVE_LETTER + "\\" + parts[0])
                        crearLogFile(parts, " ha sido modificado")
                        fileCheck.close()
                        global AVISOS
                        AVISOS += 1
                        restaurarFichero(parts[0])
                    else:
                        global ACIERTOS
                        ACIERTOS += 1
            else:
                mandarCorreo(seccionCorreo, DRIVE_LETTER + "\\" + parts[0])
                crearLogFile(parts, " ha sido eliminado")
                AVISOS += 1
                restaurarFichero(parts[0])
        global REVISIONES
        REVISIONES += 1


# Crea un informe cada x revisiones
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
        + " revisiones"
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
    with open(logName, "a", encoding="utf-8") as logFile:
        logFile.write(logText + "\n")

    AVISOS = 0
    ACIERTOS = 0
    REVISIONES = 0


# Escribe en el HIDS los ficheros nuevos
def escribirHIDS(seccionRuta):
    for directorio in seccionRuta:
        for fileIter in os.listdir(directorio):
            filename = directorio + "\\" + fileIter
            path = os.path.join(os.getcwd(), filename)
            if fileIter != "HIDS" and not os.path.isdir(path):
                with open(path, "rb") as file:
                    bytes = file.read()
                    hash = hashlib.sha1(bytes).hexdigest()
                file.close()
                with open(
                    os.getcwd() + "\confidencial\HIDS", "r+", encoding="utf-8"
                ) as fileHIDS:
                    alreadyPresent = False
                    for line in fileHIDS:
                        parts = line.split(";")
                        if parts[0] == os.path.join(os.getcwd(), filename).replace(
                            "C:\\", ""
                        ):
                            alreadyPresent = True
                    if not alreadyPresent:
                        fileHIDS.write(
                            os.path.join(os.getcwd(), filename).replace("C:\\", "")
                            + ";"
                            + hash
                            + "\n"
                        )
                fileHIDS.close()


# Restaura un fichero basándose en la carpeta backup
def restaurarFichero(filename):
    directorioBack = os.path.join(os.getcwd(), "backup")
    if os.path.exists(DRIVE_LETTER + "\\" + filename):
        os.remove(DRIVE_LETTER + "\\" + filename)
    shutil.copyfile(directorioBack + "\\" + filename, DRIVE_LETTER + "\\" + filename)


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
    with open(directorio + "/HIDS", "r+", encoding="utf-8") as fileHIDS:
        for line in fileHIDS:
            parts = line.split(";")
            if os.path.exists(DRIVE_LETTER + "\\" + parts[0]):
                currentFolder = os.path.join(os.getcwd(), "backup")
                for folder in parts[0].split("\\")[:-1]:
                    if not os.path.exists(os.path.join(currentFolder, folder)):
                        os.mkdir(os.path.join(currentFolder, folder))
                    currentFolder += "\\" + folder
                shutil.copyfile(
                    DRIVE_LETTER + "\\" + parts[0],
                    os.path.join(os.getcwd(), "backup") + "\\" + parts[0],
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
            
# Manda el correo a la dirección especificada
def mandarCorreo(seccionCorreo, fichero):
    if (SENDGRID_API_KEY!= "" and seccionCorreo!=""):
        mailMessage = Mail(
            from_email="insegusg13@gmail.com",
            to_emails=seccionCorreo,
            )

        mailMessage.dynamic_template_data = {
                    "fichero": fichero,
                        }
        mailMessage.template_id = "d-b9296865163946669d4e3239b89b50f4"
        sg = SendGridAPIClient(SENDGRID_API_KEY)
        sg.send(mailMessage)
    
# Orden de eventos
def loopPrincipal(scheduler):
    scheduler.enter(seccionTiempo, 1, loopPrincipal, (scheduler,))

    crearHIDS()
    comprobarHIDS()
    escribirHIDS(seccionRuta)
    crearBackups()
    if REVISIONES % seccionRevisiones == 0:
        crearInforme()


print("=== HIDS STARTED ===")
crearDirectorioLogs()
crearConfig()
crearDirectorioConfidencial()
crearMocks()
seccionRuta, seccionTiempo, seccionRevisiones, seccionCorreo = leerConfig()
my_scheduler = sched.scheduler(time.time, time.sleep)
my_scheduler.enter(1, 1, loopPrincipal, (my_scheduler,))
my_scheduler.run()
