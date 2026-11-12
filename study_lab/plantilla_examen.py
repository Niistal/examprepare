"""Plantilla reutilizable; borra imports no empleados antes de entregar.

Ejecutar: python plantilla_examen.py
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline


def resolver() -> None:
    """Implementar aquí cada ejercicio, con entradas y resultados comprobables."""
    print("Laboratorio listo. Escribe tu solución y añade asserts.")


def main() -> int:
    resolver()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
