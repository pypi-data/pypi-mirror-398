# num2ltr

[![en](https://img.shields.io/badge/lang-en-red.svg)](https://github.com/DanielMolina33/num2ltr/blob/main/README.md)

num2ltr es un paquete simple de Python para convertir números en palabras (letras).

Utiliza la nomenclatura estándar del español, lo que significa que se aplican la mayoría de las reglas gramaticales del idioma.

Este paquete aún se encuentra en **pruebas**, por lo que pueden presentarse algunas inconsistencias.

Este también es un proyecto personal para mejorar mis habilidades de programación.

## Instalación

Usa el gestor de paquetes [pip](https://pip.pypa.io/en/stable/)
para instalar num2ltr.

```bash
pip install num2ltr
```

O puedes usar el paquete de pruebas:

```bash
pip install -i https://test.pypi.org/simple/ num2ltr
```
## Uso

```python
import num2ltr

# devuelve 'treinta y tres'
num2ltr.number_to_letters('33') # La entrada debe ser una cadena de caracteres numérica
```

O también puedes usar:

```python
from num2ltr import number_to_letters

# devuelve 'treinta y tres'
number_to_letters('33') # La entrada debe ser una cadena de caracteres numérica
```

## Características

- Convierte cadenas numéricas a palabras en español
- Soporta números de hasta 15 dígitos (por ahora)

## Limitaciones

- Aún no soporta números decimales
- No soporta números negativos
- No soporta notación científica

## Hoja de ruta

- Soporte para números decimales
- Soporte para números negativos
- Soporte para números más grandes (hasta 50 dígitos)

## Contribuciones

Las pull requests son bienvenidas. Para cambios importantes, por favor abre un issue primero
para discutir qué te gustaría agregar o modificar.

Asegúrate de actualizar las pruebas según corresponda.

## Licencia

[MIT](https://choosealicense.com/licenses/mit/)