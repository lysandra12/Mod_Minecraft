from source import BaseAgent, BuilderBot, ExplorerBot, MinerBot
from source.read_schematic import read_blocks
from mcpi.minecraft import Minecraft
import mcpi.block as block
import time
from mcpi.vec3 import Vec3
import threading
from .MessageBus import MessageBus
from .Message import Message
from datetime import datetime, timezone


mc = Minecraft.create ()
datos = read_blocks(r"C:\URV\TAP\AdventuresInMinecraft-PC-master\AdventuresInMinecraft-PC-master\MyAdventures\Dream Survival House - (mcbuild_org).schematic")
"""
#def place_block():
original_pos = mc.player.getTilePos() + Vec3(5,0,0)
aa = mc.player.getTilePos() + Vec3(0,5,0)
print(f"height: {mc.getHeight(mc.player.getTilePos().x, mc.player.getTilePos().z)}")
agent = ExplorerBot(mc, mc.player.getTilePos(), stepp=5, radius=5)
agent.start()
agent.join()
agent.stop()
"""

"""
while(1):
    events = mc.events.pollChatPosts()
    if(events != 0):
        print(f"{events}")

for bloque in datos:
    pos = original_pos + bloque[0]
    tipo = bloque[1]
    print(f"pos: {bloque[0]} tipo: {bloque[1]}\n")

    mc.postToChat(" Hello Minecraft World ")
    mc.setBlock(pos.x + 3, pos.y ,pos.z , tipo)
"""

# Plan muy simple: una línea de 5 bloques de piedra delante del bot
bus = MessageBus()

plan = []
for dx in range(5):
    plan.append({
        "offset": Vec3(dx, 0, 0),
        "id": block.STONE.id,
        "data": 0,
    })

builder = BuilderBot(
    mc=mc,
    name="BuilderBot",
    start_pos=mc.player.getTilePos(),
    agent_id=2,  # ← AÑADIR ID ÚNICO (ej: 1 para miner, 2 para builder)
    bus=bus,
    build_plan=plan,
    tick_time=0.1
)

agent = ExplorerBot(
    mc=mc,
    start_pos=mc.player.getTilePos(),
    agent_id=3,  # ID único (ej: 3 para explorer)
    bus=bus,     # Necesitas el MessageBus
    stepp=5,
    radius=5
)
agent.start()
builder.start()
message = Message(
    payload={"command": "START"},  # Comando en el payload
    type="control",
    source="BuilderBot",
    target="ExplorerBot",
    timestamp=datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
    status="PENDING",
    context={"STOPPED"}
)
bus.publish(message)
builder.join()
agent.join()
agent.stop()
builder.stop()



"""# En tu main:

agent = MinerBot(mc, mc.player.getTilePos(),3,bus, 5)
agent.start()
print("message send")
message = Message(
    payload=[(3, 50), (1, 20)],
    type="materials.requierments.v1",
    source="BuilderBot",
    target="MinerBot",
    timestamp=datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
    status="PENDING",
    context={}
)
bus.publish(message)
time.sleep(10)
print("stopping agent")
message = Message(
    payload={"command": "STOP"},  # Comando en el payload
    type="control",
    source="BuilderBot",
    target="MinerBot",
    timestamp=datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
    status="PENDING",
    context={"STOPPED"}
)
bus.publish(message)
# más tarde, para pararlo:

agent.join()
agent.stop()"""







