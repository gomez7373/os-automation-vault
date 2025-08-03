<#
.SYNOPSIS
    Organizador de Fotos - Windows PowerShell

.DESCRIPTION
    Este script organiza imágenes copiándolas a nuevas carpetas clasificadas por año y 
    separando las fotos únicas de las posibles duplicadas (basado en hash MD5).
    - Las imágenes únicas se almacenan en /Fotos/AÑO/
    - Las duplicadas se almacenan en /Posibles_Duplicados/AÑO/
    - Se genera un log con el detalle del proceso (rutas originales y destino).
    No se eliminan los archivos originales.

.AUTHOR
    Sheila Gomez

.VERSION
    1.0

.NOTES
    Requiere permisos de lectura sobre las carpetas de origen.
    Compatible con Windows PowerShell 5.1+.
#>

# Carga la librería .NET System.Drawing para trabajar con imágenes y leer sus metadatos EXIF
Add-Type -AssemblyName System.Drawing

# Función: Obtener el año de creación de una imagen
Function Get-ImageYear($path) {
    try {
        # Abre la imagen para acceder a sus metadatos
        $img = [System.Drawing.Image]::FromFile($path)
        foreach ($prop in $img.PropertyItems) {
            # ID 36867 corresponde a "DateTimeOriginal" en los metadatos EXIF
            if ($prop.Id -eq 36867) {
                # Convierte el valor EXIF a texto ASCII y elimina caracteres nulos
                $date = [System.Text.Encoding]::ASCII.GetString($prop.Value).Trim([char]0)
                # Extrae el año del formato "YYYY:MM:DD HH:MM:SS"
                return $date.Split(" ")[0].Split(":")[0]
            }
        }
        # Si no hay metadatos EXIF, devuelve el año de última modificación del archivo
        return (Get-Item $path).LastWriteTime.Year
    } catch { 
        # En caso de error, usa la fecha de modificación como alternativa
        return (Get-Item $path).LastWriteTime.Year 
    }
}

# Función: Calcular el hash MD5 de un archivo
Function Get-FileHashMD5($file) {
    # Inicializa el objeto MD5
    $md5 = [System.Security.Cryptography.MD5]::Create()
    # Abre el archivo como flujo binario
    $stream = [System.IO.File]::OpenRead($file)
    # Calcula el hash y lo convierte a una cadena hexadecimal
    $hash = ($md5.ComputeHash($stream) | ForEach-Object { $_.ToString("x2") }) -join ""
    $stream.Close()  # Cierra el flujo de lectura
    return $hash
}

# Extensiones de imagen soportadas
$ext = ".jpg",".jpeg",".png",".bmp",".tiff",".gif",".heic"

# Solicita al usuario la carpeta origen y destino
$src = Read-Host "Carpeta origen (ej: C:\Users\%USERNAME%\Pictures)"
$dst = Read-Host "Carpeta destino (ej: C:\Users\%USERNAME%\Organizado)"

# Diccionario para almacenar hashes únicos (control de duplicados)
$unique = @{}
# Lista para el log de acciones realizadas
$log = @()

# Recorre todos los archivos de la carpeta origen y subcarpetas
Get-ChildItem -Path $src -Recurse -File | Where-Object { $ext -contains $_.Extension.ToLower() } | ForEach-Object {
    try {
        # Obtiene el año de la imagen y su hash MD5
        $year = Get-ImageYear $_.FullName
        $md5 = Get-FileHashMD5 $_.FullName

        # Clasifica la imagen: si el hash ya existe, es duplicada
        if ($unique.ContainsKey($md5)) {
            $folder = Join-Path $dst "Posibles_Duplicados\$year"
        } else {
            $folder = Join-Path $dst "Fotos\$year"
            $unique[$md5] = $true  # Registra el hash como único
        }

        # Crea la carpeta destino si no existe
        New-Item -ItemType Directory -Path $folder -Force | Out-Null
        # Copia la imagen al destino conservando su nombre
        Copy-Item $_.FullName -Destination (Join-Path $folder $_.Name) -Force
        # Agrega la acción al log
        $log += "$($_.FullName) => $folder\$($_.Name)"
    } catch {
        # Manejo de errores: muestra un mensaje si algo falla
        Write-Host "Error con $($_.FullName): $_"
    }
}

# Guarda el log con el detalle del proceso
$log | Out-File -FilePath (Join-Path $dst "log_organizacion.txt") -Encoding UTF8

# Mensaje final al usuario
Write-Host "¡Completado! Revisa $dst"
