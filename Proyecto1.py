import os
import hashlib

#Crea un directorio para guardar los archivos a indexar y supervisar
directorio = "confidencial"
path = os.path.join(os.getcwd(), directorio)
if (not os.path.exists(path)):
    os.mkdir(path)

#Crea el archivo de HIDS
filename = "confidencial/HIDS"
path = os.path.join(os.getcwd(), filename)
if (not os.path.exists(path)):
    with open(filename, "w") as file:
        file.write("")

#Crear mockfiles
for i in range(5):
    filename = "confidencial/mockfile"+str(i)
    path = os.path.join(os.getcwd(), filename)
    if (not os.path.exists(path)):
        with open(filename, "w") as file:
            file.write("Contenido del mockfile numero "+str(i))


directorio = os.path.join(os.getcwd(), "confidencial")
for fileIter in os.listdir(directorio):
    if (fileIter!="HIDS"):
        filename = "confidencial/"+fileIter
        path = os.path.join(os.getcwd(), filename)
        with open(path, "rb") as file:
            bytes = file.read()
            hash = hashlib.sha1(bytes).hexdigest()
        with open(directorio+"\HIDS", "a") as file:
            for line in file:
                parts = line.split(";")
            file.write(fileIter + ";" +hash + "\n")