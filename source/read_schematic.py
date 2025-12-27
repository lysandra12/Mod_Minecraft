import nbtlib
from mcpi.minecraft import Minecraft
import mcpi.block as block
import time
from mcpi.vec3 import Vec3

def read_blocks(schematic_path):
    schem = nbtlib.load(schematic_path)
    blocks = schem['Blocks']
    width  = int(schem['Width'])
    height = int(schem['Height'])
    length = int(schem['Length'])

    # Recorrer todos los bloques
    datos = []
    for y in range(height):
        for z in range(length):
            for x in range(width):
                idx = y * length * width + z * width + x
                tipo = blocks[idx]
                # Ensure numeric types are plain ints for downstream use
                if hasattr(tipo, 'value'):  # nbtlib tag objects
                    tipo = int(tipo)
                else:
                    try:
                        tipo = int(tipo)
                    except Exception:
                        pass
                datos.append([Vec3(x,y,z), tipo])
    return datos