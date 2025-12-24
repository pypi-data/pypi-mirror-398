from setuptools import setup

setup(
    name="aetos",
    version="1.0.0",
    py_modules=["aetos"],  # Si tu script se llama mi_cli.py
    install_requires=[
        # tus dependencias aquí, ej: "requests"
    ],
    entry_points={
        "console_scripts": [
            "aetos=aetos:main",  # nombre_comando = modulo:funcion
        ],
    },
)