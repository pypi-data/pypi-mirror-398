import sys
import os
from typing import Union

def singularOrPlural( List: Union[list, dict] ) -> Union[ str, bool ]:

    try: 
        if not isinstance( List, ( list, dict ) ):
            raise Exception("")
        if len( List ) > 1: 
            return "s"
        return ""
    except Exception as e:
        return False


def safe_index( list , value ) -> int:
    """ Devuelve el índice de value en list o -1 si no se encuentra """
    try:
        return list.index( value )
    except ValueError:
        return -1

def auto_chunk_size(data, mode="balanced"):
    """
    mode:
        - "memory": chunks más pequeños para evitar RAM alta
        - "speed": chunks más grandes para procesar más rápido
        - "balanced": elección automática
        - "sqlite": óptimo para inserts en SQLite
    """
    n = len(data)
    if n == 0:
        return 1

    # tamaño promedio
    avg_size = sys.getsizeof(data[0])

    # 1) heurística general por tamaño
    if avg_size < 64:
        base = 5000
    elif avg_size < 256:
        base = 2000
    elif avg_size < 1024:
        base = 1000
    else:
        base = 200

    # 2) ajustes según modo
    if mode == "memory":
        return max(50, base // 2)

    if mode == "speed":
        return base * 2

    if mode == "sqlite":
        # SQLite va mejor entre 200–1000 por batch
        return max(200, min(base, 1000))

    # 3) modo equilibrado según cantidad total
    if n < 1000:
        return min(200, base)
    elif n < 10_000:
        return min(1000, base)
    else:
        return base
