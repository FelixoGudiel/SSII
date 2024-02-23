import subprocess
import os
import psutil

# Nombre del script que se ejecutará
script_name = "Proceso.py"
import ctypes, os
try:
 is_admin = os.getuid() == 0
except AttributeError:
 is_admin = ctypes.windll.shell32.IsUserAnAdmin() != 0

# Función para iniciar el proceso
def start_process():
    global process
    process = subprocess.Popen(["python", script_name])
    print("Proceso iniciado. PID:", process.pid)

# Función para detener el proceso
def stop_process():
    global process
    if process:
        try:
            parent = psutil.Process(process.pid)
            for child in parent.children(recursive=True):
                child.terminate()
            parent.terminate()
            print("Proceso detenido.")
        except Exception as e:
            print("Error al detener el proceso:", e)
    else:
        print("El proceso no está en ejecución.")

# Verificar si el usuario tiene permisos de administrador
if not is_admin:
    print("Este script necesita permisos de administrador para detener el proceso.")
    exit()

# Iniciar el proceso
start_process()

# Loop para controlar el proceso
while True:
    command = input("Introduce 'stop' para detener el proceso: ")
    if command.strip().lower() == 'stop':
        stop_process()
        break
