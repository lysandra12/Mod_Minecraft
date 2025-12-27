# Import necessary modules
from mcpi.minecraft import Minecraft
import mcpi.block as block
import time
from mcpi.vec3 import Vec3

offsets = [Vec3(1,0,0), Vec3(0,0,1), Vec3(-1,0,0), Vec3(0, 0,-1)]
# Connect to the Minecraft game
mc = Minecraft.create ()

def place_block_beside_player():
    original_pos = mc.player.getTilePos()

    for offset in offsets:
        pos = original_pos + offset
        mc.postToChat(" Hello Minecraft World ")
        mc.setBlock(pos.x + 3, pos.y ,pos.z , block.STONE.id)


# Interact with the Minecraft world
while True:   
    place_block_beside_player()
    time.sleep(1)