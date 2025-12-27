from __future__ import annotations

from dataclasses import asdict
import threading
import time
from enum import Enum, auto
from typing import Optional

from mcpi.minecraft import Minecraft
from mcpi.vec3 import Vec3
from .MessageBus import MessageBus
from .Message import Message, utc_now_iso

class BotState(Enum):
    IDLE = auto()
    RUNNING = auto()
    STOPPED = auto()
    ERROR = auto()


class BaseAgent(threading.Thread):
    def __init__(
        self,
        mc: Minecraft,
        name: str,
        start_pos: Vec3,
        agent_id: int,
        bus: MessageBus,
        tick_time: float = 0.1,
    ):
        super().__init__(name=name, daemon=True)
        self.mc = mc
        self.name = name          # también sirve como target en el bus
        self.pos = start_pos
        self.tick_time = tick_time
        self.running = True
        self.mess_count = 0
        self.id = agent_id
        self.bus = bus
        self.state: BotState = BotState.IDLE

    # ---------- ciclo principal del hilo ----------

    def run(self):
        while(self.running):
            self._tick_state()
        

    def stop(self):
        self.state = BotState.STOPPED

    # ---------- máquina de estados ----------

    def set_state(self, new_state: BotState) -> None:
        self.state = new_state

    def _tick_state(self) -> None:
        handlers = {
            BotState.IDLE: self._on_idle,
            BotState.RUNNING: self._on_running,
            BotState.STOPPED: self._on_stopped,
            BotState.ERROR: self._on_error,
        }
        handler = handlers.get(self.state, self._on_error)
        handler()

    def _on_idle(self) -> None:
        self.handle_message(self.bus.poll_for(self.name))

    def _on_running(self) -> None:
        self.step()
        time.sleep(self.tick_time)

    def _on_stopped(self) -> None:
        print(f"[{self.name}] stopped")
        self.running = False
        self.stop()
        pass

    def _on_error(self) -> None:
        print(f"[{self.name}] error")
        pass

    # ---------- lógica de agente ----------

    def step(self):
        self.process_incoming()
        print(f"preceive {self.name}")
        obs = self.perceive()
        print(f"decide {self.name}")
        action = self.decide(obs)
        print(f"act {self.name}")
        self.act(action)

    def perceive(self):
        raise NotImplementedError

    def decide(self, obs):
        raise NotImplementedError

    def act(self, action):
        raise NotImplementedError

    # ---------- utilidades de entorno ----------

    def move_to(self, new_pos: Vec3):
        self.pos = new_pos

    def get_block(self, offset: Vec3):
        target = self.pos + offset
        return self.mc.getBlock(target.x, target.y, target.z)

    def set_block(self, offset: Vec3, block_id: int, data: int = 0):
        target = self.pos + offset
        self.mc.setBlock(target.x, target.y, target.z, block_id, data)

    # ---------- mensaes ----------

    def build_message(
        self,
        payload: dict,
        type: str,
        source: str,
        target: str,
        context: Optional[dict] = None,
    ) -> Message:
        self.mess_count += 1
        return Message(
            type=type,
            source=source,
            target=target,
            timestamp=utc_now_iso(),
            payload=payload,
            status="PENDING",
            context=context or {},
        )

    def process_incoming(self):
        """Lee mensajes dirigidos a este agente (por name) y los maneja."""
        while True:
            msg = self.bus.poll_for(self.name)
            if msg is None:
                break
            self.handle_message(msg)

    def send_message(self, msg: Message) -> None:
        """Atajo para publicar en el bus."""
        self.bus.publish(msg)

    def handle_message(self, msg: Message):
        if msg is None:
            return None
        print(f"MinerBot {self.id} received message: {msg}")

        msg_dict = asdict(msg)
        msg_type = str(msg_dict.get("type", ""))
        if msg_type.startswith("control"):
            self.handle_control_message(msg_dict)
        else:
            self.handle_priv_message(msg_dict)
            
    def handle_priv_message(self, msg_dict: dict) -> None:
        pass 

    def handle_control_message(self, msg_dict: dict):
        """Función general que distribuye los comandos a handlers específicos"""
        payload = msg_dict.get("payload", {})
        
        if isinstance(payload, dict):
            command = payload.get("command", "")
        else:
            command = str(payload)
        
        if command in ["HELP", "help"]:
            self._handle_common_help()
            
        elif command in ["STATUS", "status"]:  #printear por pantalla del juego
            print(f"[{self.name}] Estado actual: {self.state}")
            
        elif command in ["STOP", "stop"]:
            print(f"[{self.name}] Detenido desde mensaje de control")
            self.set_state(BotState.STOPPED)
            
        elif command in ["PAUSE", "pause"]:
            print(f"[{self.name}] Pausado desde mensaje de control")
            self.set_state(BotState.IDLE)
            
        elif command in ["RESUME", "resume"]:
            self._handle_common_resume(payload)
            
        else:
            self._handle_priv_command(command, payload)
    
    
    def _handle_priv_command(self, command: str, payload: dict):
        """Método que debe ser sobrescrito por cada agente específico"""
        print(f"[{self.name}] Comando no reconocido: {command}")