#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script: Organizador de Fotos
Autor: Sheila Gomez
Descripción:
    Este script organiza imágenes en carpetas clasificadas por año y separa las fotos únicas 
    de las posibles duplicadas (idénticas o visualmente similares).
    - Las imágenes únicas se almacenan en /Fotos/AÑO/
    - Las duplicadas o similares se almacenan en /Posibles_Duplicados/AÑO/
    - Se genera un log con el detalle del proceso (rutas originales y destino).
    No se eliminan los archivos originales.
"""

import os, hashlib, shutil, imagehash
from PIL import Image, ExifTags
from datetime import datetime

# Extensiones válidas de imagen a procesar
EXT = (".jpg",".jpeg",".png",".bmp",".tiff",".gif",".heic")

def md5_hash(path):
    """
    Calcula el hash MD5 de un archivo.
    Este hash permite identificar duplicados exactos comparando su contenido binario.
    """
    h = hashlib.md5()
    with open(path,'rb') as f:
        for chunk in iter(lambda: f.read(4096), b""):  # Lee el archivo por bloques
            h.update(chunk)
    return h.hexdigest()

def phash(path):
    """
    Calcula el perceptual hash (pHash) de una imagen.
    Este hash permite detectar imágenes visualmente similares aunque no sean idénticas.
    Devuelve None si ocurre un error al procesar la imagen.
    """
    try:
        with Image.open(path) as img:
            return str(imagehash.phash(img))
    except:
        return None

def get_year(path):
    """
    Obtiene el año de creación de una imagen.
    Prioriza el metadato EXIF 'DateTimeOriginal'.
    Si no existe, usa la fecha de modificación del archivo.
    """
    try:
        with Image.open(path) as img:
            exif = img._getexif()
            if exif:
                for tag, val in exif.items():
                    if ExifTags.TAGS.get(tag) == 'DateTimeOriginal':
                        return val.split(":")[0]  # Extrae el año del formato 'YYYY:MM:DD'
    except:
        pass
    # Si no hay metadatos, usar la fecha del sistema de archivos
    return str(datetime.fromtimestamp(os.path.getmtime(path)).year)

def copy(src, dst):
    """
    Copia un archivo a la ruta destino, creando las carpetas necesarias si no existen.
    """
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    shutil.copy2(src, dst)  # Copia manteniendo metadatos (fecha, permisos)

def organize(src, dst):
    """
    Organiza las imágenes encontradas en la carpeta origen:
    - Imágenes únicas: /Fotos/AÑO/
    - Duplicadas o similares: /Posibles_Duplicados/AÑO/
    Además, genera un log con el detalle del proceso.
    """
    unique, similar = {}, {}  # Diccionario para almacenar hashes únicos y sus pHash
    log = []  # Lista para registrar el proceso

    # Recorrer recursivamente todas las subcarpetas
    for root, _, files in os.walk(src):
        for file in files:
            if file.lower().endswith(EXT):  # Filtra solo imágenes
                full = os.path.join(root, file)
                try:
                    year = get_year(full)
                    md5 = md5_hash(full)
                    p = phash(full)

                    # Determinar destino según duplicados exactos o similares
                    if md5 in unique:
                        # Imagen duplicada exacta
                        folder = os.path.join(dst, "Posibles_Duplicados", year)
                    elif any(abs(int(p,16) - int(h,16)) < 10 for h in unique.values() if h):
                        # Imagen similar (comparación de pHash con tolerancia <10)
                        folder = os.path.join(dst, "Posibles_Duplicados", year)
                    else:
                        # Imagen única
                        folder = os.path.join(dst, "Fotos", year)
                        unique[md5] = p  # Guardar hash para futuras comparaciones

                    # Copiar archivo a la carpeta correspondiente
                    copy(full, os.path.join(folder, file))
                    log.append(f"{full} => {folder}/{file}")

                except Exception as e:
                    print(f"Error {full}: {e}")

    # Guardar log del proceso
    with open(os.path.join(dst, "log_organizacion.txt"), "w") as f:
        f.write("\n".join(log))

if __name__ == "__main__":
    # Ejecución interactiva del script
    print("=== Organizador de Fotos (Linux) ===")
    source = input("Carpeta origen (ej: /home/usuario/Pictures): ").strip()
    target = input("Carpeta destino (ej: /home/usuario/Organizado): ").strip()
    organize(source, target)
    print("¡Completado! Revisa tu carpeta organizada.")
