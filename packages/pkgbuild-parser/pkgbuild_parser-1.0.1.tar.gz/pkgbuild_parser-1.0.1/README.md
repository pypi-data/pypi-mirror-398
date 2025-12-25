# pkgbuild_parser

[English documentation (GitHub)](https://github.com/KevinCrrl/pkgbuild_parser/blob/main/ingles.md)
[English documentation (Codeberg)](https://codeberg.org/KevinCrrl/pkgbuild_parser/src/branch/main/ingles.md)

## Introducción

**pkgbuild_parser** es un módulo escrito en **Python** (compatible con Python 3.x) diseñado para extraer información de un **PKGBUILD**. El propósito principal de este módulo es proporcionar un acceso sencillo y directo a los campos más importantes de un PKGBUILD sin depender de herramientas externas ni librerías adicionales.

- **Versión:** 1.0.1
- **Licencia:** MIT 2025 KevinCrrl
- **Dependencias:** Ninguna
- **Estilo:** Simplicidad, sin dependencias externas, fácil de usar

Este módulo permite obtener datos como el nombre del paquete, versión, descripción, licencia, URL y archivo fuente de manera rápida y directa.

---

## Funciones principales para el usuario

Aunque internamente el módulo tiene funciones de soporte (`get_base`), el **usuario solo necesita usar las funciones de alto nivel**, que son claras y directas:

| Función                               | Descripción                                                                                                      |
| -------------------------------------- | ----------------------------------------------------------------------------------------------------------------- |
| `get_pkgname()`                      | Retorna el nombre del paquete (`pkgname`) como string.                                                          |
| `get_pkgver()`                       | Retorna la versión del paquete (`pkgver`) como string.                                                         |
| `get_pkgrel()`                       | Retorna el número de release (`pkgrel`) como string.                                                           |
| `get_pkgdesc()`                      | Retorna la descripción del paquete (`pkgdesc`) como string, eliminando comentarios y paréntesis innecesarios. |
| `get_arch()`                         | Retorna la arquitectura del paquete (`arch`) como una lista de strings.                                         |
| `get_url()`                          | Retorna la URL principal del proyecto (`url`) como string.                                                      |
| `get_license()`                      | Retorna la licencia del paquete (`license`) como una lista de strings.                                          |
| `get_source()`                       | Retorna la(s) fuente(s) (`source`) del paquete como una lista de strings.                                       |
| `get_dict_base_info()`               | Retorna un diccionario con todos los campos anteriores en formato `{'pkgname': ..., 'pkgver': ..., ...}`.       |
| `base_info_to_json()`                | Retorna la información base en formato **JSON** con indentación y codificación UTF-8.                   |
| `write_base_info_to_json(json_name)` | Escribe la información base en un archivo JSON con nombre `json_name`.                                         |
| `get_epoch()`                        | Retorna la `epoch` del paquete.                                                                                 |
| `get_full_package_name()`            | Retorna el nombre completo del paquete, incluyendo `epoch`, versión y `pkgrel`.                              |
| `get_depends()`                      | Retorna una lista de las dependencias del paquete.                                                                |
| `get_makedepends()`                  | Retorna una lista de las dependencias de compilación del paquete.                                                |
| `get_optdepends()`                   | Retorna una lista de las dependencias opcionales del paquete.                                                     |
| `get_dict_optdepends()`              | Retorna un diccionario de las dependencias opcionales del paquete.                                                |
| `optdepends_to_json()`               | Retorna un JSON de las dependencias opcionales del paquete.                                                       |
| `write_optdepends_to_json()`         | Escribe en un JSON las dependencias opcionales del paquete.                                                       |
| `get_options()`                      | Retorna una lista de las opciones del paquete.                                                                    |
| `get_checkdepends()`                 | Retorna una lista de las dependencias de verificación del paquete.                                               |
| `get_sha256sums()`                   | Retorna una lista de las sumas de verificación sha256.                                                           |
| `get_sha512sums()`                   | Retorna una lista de las sumas de verificación sha512.                                                           |
| `get_validpgpkeys()`                 | Retorna una lista de las llaves PGP validas.                                                                      |

**Nota:** Las funciones internas (`get_base` y `multiline`) están pensadas para uso del módulo y **no necesitan ser usadas por el usuario**.

---

## Instalación y uso

### Opción 1: AUR

El módulo está disponible en el AUR como **`python-pkgbuild-parser`**:

### Opción 2: Construcción manual

Si deseas construirlo manualmente:

```bash
python -m build
pip install .
```

## Uso básico

```python
import pkgbuild_parser
import sys

try:
    mi_pkgbuild = pkgbuild_parser.Parser("PKGBUILD")
except pkgbuild_parser.ParserFileError as exc:
    print(exc)
    sys.exit(1)

# Obtener datos básicos
try:
    print(mi_pkgbuild.get_pkgname())
    print(mi_pkgbuild.get_pkgver())
    print(mi_pkgbuild.get_pkgrel())
    print(mi_pkgbuild.get_pkgdesc())
    print(mi_pkgbuild.get_arch())
    print(mi_pkgbuild.get_url())
    print(mi_pkgbuild.get_license())
    print(mi_pkgbuild.get_source())
    print(mi_pkgbuild.get_epoch())
    print(mi_pkgbuild.get_full_package_name())
    print(mi_pkgbuild.get_depends())
    print(mi_pkgbuild.get_makedepends())
    print(mi_pkgbuild.get_optdepends())
    print(mi_pkgbuild.get_dict_optdepends())
    print(mi_pkgbuild.optdepends_to_json())
    mi_pkgbuild.write_optdepends_to_json()
    print(mi_pkgbuild.get_options())
    print(mi_pkgbuild.get_checkdepends())
    print(mi_pkgbuild.get_sha256sums())
    print(mi_pkgbuild.get_sha512sums())
    print(mi_pkgbuild.get_validpgpkeys())


    # Obtener un diccionario de toda la info
    info = mi_pkgbuild.get_dict_base_info()
    print(info)

    # Mostrar en formato JSON
    print(mi_pkgbuild.base_info_to_json())

    # Obtener JSON y escribirlo a archivo
    mi_pkgbuild.write_base_info_to_json("info.json")
except (pkgbuild_parser.ParserKeyError, pkgbuild_parser.ParserNoneTypeError) as e:
    print(e)
```

## Manejo de errores

Si el archivo PKGBUILD no existe, se lanza un `ParserFileError`, que debe ser capturado para evitar que el programa falle.

También puede ocurrir que se lanza un `ParserKeyError` en caso de que la obtención de un valor del PKGBUILD falle, por ejemplo, si license no está bien declarado, y se hace get_license() se producirá dicha excepción.

Desde la versión 0.2.0, también se puede lanzar un `ParserNoneTypeError` si una función retorna `None` cuando no se esperaba.

## Limitaciones

- El objetivo del módulo es extraer únicamente **información básica** de PKGBUILD estándar, no puede reemplazar variables bash dentro de otra variable como por ejemplo si el source está declarado con el valor "$url/paquete.zip".
- Funciona mejor con PKGBUILD que siguen las normas de la **Arch Wiki**.
- Desde la versión 0.4.0, el módulo puede extraer información de arrays o listas, como `depends`, `makedepends`, `source`, `optdepends`, `license`, `options` y `checkdepends`.
- Desde la versión 1.0.0 las funciones que retornan un string, por defecto ya no incluyen las comillas
