from mcpi.minecraft import Minecraft
import mcpi.block as block
import time
from mcpi.vec3 import Vec3

# Definimos una base para estrategias
class BlockPlacementStrategy:
    def place(self, mc, original_pos):
        raise NotImplementedError

# Estrategia 1: colocar bloques junto al jugador en los offsets clásicos
class ClassicOffsetsStrategy(BlockPlacementStrategy):
    offsets = [Vec3(1,0,0), Vec3(0,0,1), Vec3(-1,0,0), Vec3(0, 0,-1)]

    def place(self, mc, original_pos):
        for offset in self.offsets:
            pos = original_pos + offset
            mc.postToChat(" Hello Minecraft World ")
            mc.setBlock(pos.x + 3, pos.y, pos.z, block.STONE.id)

# Ejemplo de una nueva estrategia extensible
class FloorStrategy(BlockPlacementStrategy):
    def place(self, mc, original_pos):
        for dx in range(-2, 3):
            for dz in range(-2, 3):
                pos = original_pos + Vec3(dx, -1, dz)
                mc.setBlock(pos.x, pos.y, pos.z, block.GRASS.id)

# Reflexivamente descubre todas las clases que heredan BlockPlacementStrategy
def discover_strategies():
    strategies = []
    for obj in globals().values():
        if isinstance(obj, type) and issubclass(obj, BlockPlacementStrategy) and obj is not BlockPlacementStrategy:
            strategies.append(obj())
    return strategies

# Conexión a Minecraft
mc = Minecraft.create()

# Main loop con todas las estrategias descubiertas
strategies = discover_strategies()
while True:
    pos = mc.player.getTilePos()
    for strategy in strategies:
        strategy.place(mc, pos)
    time.sleep(1)