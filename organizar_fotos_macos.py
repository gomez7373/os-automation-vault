#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script: Organizador de Fotos (macOS)
Autor: Sheila Gomez
Descripción:
    Este script organiza imágenes copiándolas a nuevas carpetas clasificadas por año 
    y separando las fotos únicas de las posibles duplicadas (basado en hash MD5).
    - Las imágenes únicas se almacenan en /Fotos/AÑO/
    - Las duplicadas se almacenan en /Posibles_Duplicados/AÑO/
    - Se genera un log con el detalle del proceso (rutas originales y destino).
    No se eliminan los archivos originales.
Compatibilidad:
    macOS con Python 3.7+ y librerías Pillow, imagehash.
"""

import os, hashlib, shutil, imagehash
from PIL import Image, ExifTags
from datetime import datetime

# Extensiones de imagen soportadas
EXT = (".jpg", ".jpeg", ".png", ".bmp", ".tiff", ".gif", ".heic")

def md5_hash(path):
    """
    Calcula el hash MD5 de un archivo.
    Permite identificar duplicados exactos comparando su contenido binario.
    """
    h = hashlib.md5()
    with open(path, 'rb') as f:
        for chunk in iter(lambda: f.read(4096), b""):  # Lectura por bloques para mayor eficiencia
            h.update(chunk)
    return h.hexdigest()

def phash(path):
    """
    Calcula el perceptual hash (pHash) de una imagen.
    Útil para detectar imágenes visualmente similares (no se usa aquí para clasificación final, pero se mantiene para futuras mejoras).
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
    Si no existe, usa la fecha de modificación del archivo en el sistema.
    """
    try:
        with Image.open(path) as img:
            exif = img._getexif()
            if exif:
                for tag, val in exif.items():
                    if ExifTags.TAGS.get(tag) == 'DateTimeOriginal':
                        return val.split(":")[0]  # Extrae solo el año del formato 'YYYY:MM:DD'
    except:
        pass
    # Si no hay EXIF, devolver año de modificación
    return str(datetime.fromtimestamp(os.path.getmtime(path)).year)

def copy(src, dst):
    """
    Copia un archivo desde el origen al destino, 
    creando la carpeta si no existe y manteniendo metadatos (fecha, permisos).
    """
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    shutil.copy2(src, dst)

def organize(src, dst):
    """
    Recorre todas las imágenes en la carpeta origen y las organiza en:
    - /Fotos/AÑO/ si son únicas (según MD5)
    - /Posibles_Duplicados/AÑO/ si ya existe un duplicado exacto
    Además, genera un archivo log con el detalle de las acciones.
    """
    unique, log = {}, []  # Diccionario de hashes únicos y lista de acciones realizadas

    for root, _, files in os.walk(src):
        for file in files:
            if file.lower().endswith(EXT):  # Filtrar solo imágenes
                full = os.path.join(root, file)
                try:
                    year = get_year(full)      # Obtener año
                    md5 = md5_hash(full)       # Calcular hash MD5
                    if md5 in unique:
                        # Imagen duplicada exacta
                        folder = os.path.join(dst, "Posibles_Duplicados", year)
                    else:
                        # Imagen única
                        folder = os.path.join(dst, "Fotos", year)
                        unique[md5] = True
                    # Copiar la imagen a la carpeta correspondiente
                    copy(full, os.path.join(folder, file))
                    log.append(f"{full} => {folder}/{file}")
                except Exception as e:
                    print(f"Error {full}: {e}")

    # Guardar log del proceso
    with open(os.path.join(dst, "log_organizacion.txt"), "w") as f:
        f.write("\n".join(log))

if __name__ == "__main__":
    # Entrada de usuario y ejecución principal
    print("=== Organizador de Fotos (macOS) ===")
    source = input("Carpeta origen (ej: /Users/TuUsuario/Pictures): ").strip()
    target = input("Carpeta destino (ej: /Users/TuUsuario/Organizado): ").strip()
    organize(source, target)
    print("¡Completado! Revisa tu carpeta organizada.")
