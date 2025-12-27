from dataclasses import asdict
from mcpi import block
from .BaseAgent import BaseAgent, BotState
from mcpi.minecraft import Minecraft
from mcpi.vec3 import Vec3
from typing import List, Tuple
import time
import random
from .Message import Message
from .MessageBus import MessageBus
from datetime import datetime, timezone  # Asegúrate de tener esto
from typing import Optional  # Añadir también

class MinerBot(BaseAgent):
    def __init__(self, mc: Minecraft, start_pos: Vec3, id: int, bus: MessageBus, grid_size: int = 5):
        super().__init__(mc, "MinerBot", start_pos, id, bus)
        self.objetivos = []
        self.modo = 0
        self.inventario = []
        self.grid_size = grid_size
        self.pos_visitadas = []
        self.mess_count = 0

# MinerBot.py - Modificar estas funciones

    def perceive(self):
        """Observa el entorno: recursos disponibles, posición y estado de objetivos"""
        # 1. Verificar si tenemos objetivos pendientes
        has_objectives = len(self.objetivos) > 0
        
        # 2. Verificar si hemos completado todos los objetivos
        objectives_completed = self.check_objectives_completed()
        
        # 3. Observar el bloque actual debajo del minero
        current_block = self.mc.getBlock(self.pos.x, self.pos.y, self.pos.z)
        
        # 4. Verificar si estamos en bedrock (límite inferior)
        at_bedrock = current_block == 7
        
        # 5. Calcular progreso actual
        progress = self.calculate_progress()
        
        print(f"[MinerBot_{self.id}] perceive -> "
            f"Objetivos: {len(self.objetivos)}, "
            f"Completados: {objectives_completed}, "
            f"Bloque actual: {current_block}, "
            f"Bedrock: {at_bedrock}")
        
        # Retornar observaciones estructuradas
        return {
            "has_objectives": has_objectives,
            "objectives_completed": objectives_completed,
            "current_block": current_block,
            "at_bedrock": at_bedrock,
            "position": self.pos,
            "inventory": self.inventario,
            "progress": progress,
            "strategy": self.get_strategy_name(),
            "grid_size": self.grid_size,
            "visited_positions": len(self.pos_visitadas)
        }

    def decide(self, obs):
        """Decide qué estrategia de minería usar basado en las observaciones"""
        
        # Si no hay objetivos, esperar
        if not obs["has_objectives"]:
            print(f"[MinerBot_{self.id}] decide -> Sin objetivos, esperando...")
            return {
                "action": "WAIT_FOR_OBJECTIVES",
                "message": "Esperando lista de materiales requeridos"
            }
        
        # Si todos los objetivos están completados
        if obs["objectives_completed"]:
            print(f"[MinerBot_{self.id}] decide -> Todos los objetivos completados")
            return {
                "action": "MINING_COMPLETE",
                "inventory": self.inventario,
                "message": "Minería finalizada"
            }
        
        # Si estamos en bedrock, cambiar de posición
        if obs["at_bedrock"]:
            print(f"[MinerBot_{self.id}] decide -> Llegó al bedrock, cambiando posición")
            return {
                "action": "CHANGE_LOCATION",
                "reason": "bedrock_reached",
                "current_position": self.pos
            }
        
        # Decidir estrategia basada en objetivos y entorno
        # Si hay objetivos específicos y estamos en modo vertical
        if self.modo == 0:  # Vertical Search
            current_block = obs["current_block"]
            
            # Verificar si el bloque actual es uno de los objetivos
            target_blocks = [obj[0] for obj in self.objetivos]
            if current_block in target_blocks:
                print(f"[MinerBot_{self.id}] decide -> Bloque objetivo encontrado (ID: {current_block})")
                return {
                    "action": "MINE_TARGET_BLOCK",
                    "block_id": current_block,
                    "strategy": "vertical",
                    "position": self.pos
                }
            else:
                print(f"[MinerBot_{self.id}] decide -> Continuando búsqueda vertical")
                return {
                    "action": "CONTINUE_VERTICAL_SEARCH",
                    "strategy": "vertical",
                    "depth": self.pos.y
                }
        
        elif self.modo == 1:  # Grid Search
            print(f"[MinerBot_{self.id}] decide -> Búsqueda en grid ({self.grid_size}x{self.grid_size})")
            return {
                "action": "GRID_SEARCH",
                "grid_size": self.grid_size,
                "position": self.pos
            }
        
        elif self.modo == 2:  # Vein Search
            print(f"[MinerBot_{self.id}] decide -> Búsqueda de vetas")
            return {
                "action": "VEIN_SEARCH",
                "position": self.pos
            }
        
        # Estrategia por defecto
        print(f"[MinerBot_{self.id}] decide -> Usando estrategia por defecto (vertical)")
        return {
            "action": "CONTINUE_VERTICAL_SEARCH",
            "strategy": "vertical",
            "depth": self.pos.y
        }

    def act(self, decision):
        """Ejecuta la acción decidida"""
        action_type = decision.get("action", "WAIT")
        
        if action_type == "MINE_TARGET_BLOCK":
            block_id = decision["block_id"]
            position = decision.get("position", self.pos)
            
            print(f"[MinerBot_{self.id}] act -> Minando bloque objetivo ID {block_id} en {position}")
            
            # Minar el bloque
            self.mc.setBlock(position.x, position.y, position.z, 0)  # Reemplazar con aire
            
            # Recoger el recurso
            self.recoger_recurso(block_id)
            
            # Enviar update de inventario
            self.send_inventory_update()
            
            # Continuar hacia abajo
            self.pos.y -= 1
            
        elif action_type == "CONTINUE_VERTICAL_SEARCH":
            print(f"[MinerBot_{self.id}] act -> Continuando búsqueda vertical (profundidad: {self.pos.y})")
            
            # Minar el bloque actual (aunque no sea objetivo)
            current_block = self.mc.getBlock(self.pos.x, self.pos.y, self.pos.z)
            
            # Solo minar si no es bedrock
            if current_block != 7:
                self.mc.setBlock(self.pos.x, self.pos.y, self.pos.z, 0)
                
                # Verificar si era un bloque objetivo
                if any(obj[0] == current_block for obj in self.objetivos):
                    self.recoger_recurso(current_block)
                    self.send_inventory_update()
                
                # Mover hacia abajo
                self.pos.y -= 1
            else:
                print(f"[MinerBot_{self.id}] act -> ¡Bedrock alcanzado!")
                
        elif action_type == "GRID_SEARCH":
            grid_size = decision.get("grid_size", self.grid_size)
            print(f"[MinerBot_{self.id}] act -> Ejecutando búsqueda en grid {grid_size}x{grid_size}")
            
            self.grid_search_execute(grid_size)
            
        elif action_type == "CHANGE_LOCATION":
            print(f"[MinerBot_{self.id}] act -> Cambiando de ubicación (razón: {decision.get('reason')})")
            
            # Buscar nueva posición no visitada
            new_pos = self.find_new_location()
            if new_pos:
                print(f"[MinerBot_{self.id}] act -> Nueva posición: {new_pos}")
                self.move_to(new_pos)
                
                # Enviar mensaje de movimiento
                self.send_location_change_message(decision.get("current_position"), new_pos)
            else:
                print(f"[MinerBot_{self.id}] act -> No se encontró nueva ubicación disponible")
                
        elif action_type == "MINING_COMPLETE":
            print(f"[MinerBot_{self.id}] act -> Minería completada")
            print(f"  Inventario final: {self.inventario}")
            
            # Enviar mensaje de finalización
            self.send_mining_complete_message()
            
            # Cambiar a estado IDLE
            self.set_state(BotState.IDLE)
            
        elif action_type == "WAIT_FOR_OBJECTIVES":
            print(f"[MinerBot_{self.id}] act -> Esperando objetivos...")
            time.sleep(2)
            
        elif action_type == "WAIT":
            print(f"[MinerBot_{self.id}] act -> Esperando...")
            time.sleep(1)


    def vertical_search(self):

        bloque_debajo = self.mc.getBlock(self.pos.x, self.pos.y, self.pos.z)

        if bloque_debajo != 7: # si no hem arribat al final (7==bedrock)
            if any(tupla[0] == bloque_debajo for tupla in self.objetivos):
                self.recoger_recurso(bloque_debajo)
            self.mc.setBlock(self.pos.x, self.pos.y, self.pos.z, 20)

            self.pos.y = self.pos.y - 1 
        else:
            no_visitada = True
            while no_visitada:
                dx, dz = 0, 0
                while dx == 0 and dz == 0:
                    dx = random.randint(-1, 1)
                    dz = random.randint(-1, 1)

                self.pos.x += dx
                self.pos.z += dz
                self.pos.y = self.mc.getHeight(self.pos.x, self.pos.z) - 1

                if not self.pos_ya_visitada(self.pos):
                    no_visitada = False
        
    def grid_search(self):
        for i in range(self.grid_size):
            for j in range(self.grid_size):
                n_pos = Vec3(self.pos.x+i, self.pos.y+j, self.pos.z)
                bloque = self.get_block(n_pos)
                if bloque in self.objetivos:
                    self.recoger_recurso(bloque)
                self.set_block(n_pos, 0)
        
        self.move_to(Vec3(self.pos.x, self.pos.y, self.pos.z+1))

    def recoger_recurso(self, bloque_id: int):
        #buscamos indice
        idx = next(filter(
            lambda i: self.objetivos[i][0] == bloque_id,
            range(len(self.objetivos))
        ), None) 

        # sumamos un inventario
        bid, cant = self.inventario[idx]
        self.inventario[idx] = (bid, cant + 1)

        if(self.inventario[idx][1] == self.objetivos[idx][1]):
            del self.objetivos[idx]
                
    
    def objetivos_cumplidos(self) -> bool:
        if(self.objetivos.count()==0):
            return True
        
        return False
    
    
    def pos_ya_visitada(self, pos: Vec3) -> bool:
        clave = (pos.x, pos.z)

        if clave in self.pos_visitadas:
            return True

        self.pos_visitadas.append(clave)
        return False
    
    def build_message(self) -> Message:
        """Crea mensaje de inventario (mantener compatibilidad)"""
        payload = {
            "inventario": self.inventario,
            "objetivos": self.objetivos,
            "progress": self.calculate_progress()
        }
        
        # NO resetear inventario aquí - eso lo hace el BuilderBot cuando usa los materiales
        # self.inventario = list(map(lambda objetivo: (objetivo[0], 0), self.objetivos))
        
        return super().build_message(
            payload=payload,
            type="inventory.v" + str(self.mess_count),
            source="MinerBot_" + str(self.id),
            target="BuilderBot"
        )
    
    #mensajes
    def handle_priv_message(self, msg_dict: dict) -> None:
        msg_type = str(msg_dict.get("type", ""))
        if msg_type.startswith("materials.requierments"):
            self.objetivos = msg_dict.get("payload", [])
            self.inventario = list(
                map(lambda objetivo: (objetivo[0], 0), self.objetivos)
            )
            self.set_state(BotState.RUNNING)
            #response_msg = self.build_response_message(msg_dict.get("source", ""))
            #self.bus.publish(response_msg)

    def _handle_priv_command(self, command, payload):
                
        if command  == "start":
            pos = payload.get("start_pos", Vec3())
            self.start_pos = Vec3(pos[0], pos[1], pos[2])
            self.set_state(BotState.RUNNING)

        elif command == "set strategy":
            self.grid_size = payload.get("strategy",0)
            print(f"MinerBot {self.id} strategy set to a") 
        elif command == "fulfill":
            print("fulfill command received") #nose que hacer aqui hahs
        
    # MinerBot.py - Añadir al final de la clase

    def check_objectives_completed(self) -> bool:
        """Verifica si todos los objetivos han sido completados"""
        if not self.objetivos:
            return True
        
        # Verificar cada objetivo contra el inventario
        for i, (block_id, required) in enumerate(self.objetivos):
            if i < len(self.inventario):
                _, collected = self.inventario[i]
                if collected < required:
                    return False
            else:
                return False
        
        return True

    def calculate_progress(self) -> dict:
        """Calcula el progreso de minería"""
        progress = {}
        total_required = 0
        total_collected = 0
        
        for i, (block_id, required) in enumerate(self.objetivos):
            total_required += required
            
            if i < len(self.inventario):
                _, collected = self.inventario[i]
                total_collected += collected
                
                progress[block_id] = {
                    "required": required,
                    "collected": collected,
                    "percentage": (collected / required * 100) if required > 0 else 0
                }
        
        overall_percentage = (total_collected / total_required * 100) if total_required > 0 else 0
        
        return {
            "by_block": progress,
            "total_required": total_required,
            "total_collected": total_collected,
            "overall_percentage": overall_percentage
        }

    def get_strategy_name(self) -> str:
        """Devuelve el nombre de la estrategia actual"""
        strategies = {
            0: "vertical_search",
            1: "grid_search", 
            2: "vein_search"
        }
        return strategies.get(self.modo, "unknown")

    def grid_search_execute(self, grid_size: int):
        """Ejecuta búsqueda en grid"""
        for i in range(grid_size):
            for j in range(grid_size):
                n_pos = Vec3(self.pos.x + i, self.pos.y + j, self.pos.z)
                bloque = self.mc.getBlock(n_pos.x, n_pos.y, n_pos.z)
                
                # Verificar si es un bloque objetivo
                target_blocks = [obj[0] for obj in self.objetivos]
                if bloque in target_blocks:
                    print(f"[MinerBot_{self.id}] act -> Encontrado bloque objetivo {bloque} en grid")
                    self.recoger_recurso(bloque)
                
                # Minar el bloque
                self.mc.setBlock(n_pos.x, n_pos.y, n_pos.z, 0)
                
                # Pequeña pausa para simulación
                time.sleep(0.05)
        
        # Mover a siguiente posición en grid
        self.move_to(Vec3(self.pos.x, self.pos.y, self.pos.z + 1))

    def find_new_location(self, max_attempts: int = 20) -> Vec3:
        """Encuentra una nueva ubicación no visitada"""
        for _ in range(max_attempts):
            # Generar desplazamiento aleatorio
            dx, dz = 0, 0
            while dx == 0 and dz == 0:
                dx = random.randint(-5, 5)
                dz = random.randint(-5, 5)
            
            new_pos = Vec3(
                self.pos.x + dx,
                self.mc.getHeight(self.pos.x + dx, self.pos.z + dz) - 1,
                self.pos.z + dz
            )
            
            if not self.pos_ya_visitada(new_pos):
                return new_pos
        
        return None

    def send_inventory_update(self):
        """Envía actualización periódica del inventario"""
        progress = self.calculate_progress()
        
        msg = super().build_message(
            payload={
                "inventario": self.inventario,
                "objetivos": self.objetivos,
                "progress": progress,
                "position": {"x": self.pos.x, "y": self.pos.y, "z": self.pos.z},
                "strategy": self.get_strategy_name()
            },
            type="inventory.update.v1",
            source=f"MinerBot_{self.id}",
            target="BuilderBot"
        )
        
        print(f"[MinerBot_{self.id}] Enviando update de inventario")
        self.send_message(msg)

    def send_mining_complete_message(self):
        """Envía mensaje cuando termina la minería"""
        msg = super().build_message(
            payload={
                "status": "COMPLETED",
                "final_inventory": self.inventario,
                "objectives": self.objetivos,
                "message": "Todos los materiales han sido recolectados",
                "timestamp": datetime.now(timezone.utc).isoformat()
            },
            type="mining.completed.v1",
            source=f"MinerBot_{self.id}",
            target="BuilderBot"
        )
        
        print(f"[MinerBot_{self.id}] Enviando mensaje de finalización")
        self.send_message(msg)

    def send_location_change_message(self, old_pos: Vec3, new_pos: Vec3):
        """Envía mensaje de cambio de ubicación"""
        msg = super().build_message(
            payload={
                "old_position": {"x": old_pos.x, "y": old_pos.y, "z": old_pos.z},
                "new_position": {"x": new_pos.x, "y": new_pos.y, "z": new_pos.z},
                "reason": "bedrock_reached",
                "timestamp": datetime.now(timezone.utc).isoformat()
            },
            type="miner.movement.v1",
            source=f"MinerBot_{self.id}",
            target="System"
        )
        
        self.send_message(msg)

    def handle_priv_message(self, msg_dict: dict) -> None:
        """Maneja mensajes privados para el MinerBot"""
        msg_type = str(msg_dict.get("type", ""))
        
        if msg_type.startswith("materials.requirements") or msg_type.startswith("materials.requierments"):
            print(f"[MinerBot_{self.id}] Received material requirements")
            payload = dict(msg_dict.get("payload", {}))
            
            # Extraer requerimientos del payload
            requirements = payload.get("requirements", [])
            if isinstance(requirements, dict):
                # Convertir dict a lista de tuplas
                self.objetivos = [(block_id, qty) for block_id, qty in requirements.items()]
            elif isinstance(requirements, list):
                self.objetivos = requirements
            else:
                print(f"[MinerBot_{self.id}] Formato de requerimientos no reconocido")
                return
            
            # Inicializar inventario
            self.inventario = [(block_id, 0) for block_id, _ in self.objetivos]
            
            print(f"[MinerBot_{self.id}] Objetivos establecidos: {self.objetivos}")
            print(f"[MinerBot_{self.id}] Inventario inicializado: {self.inventario}")
            
            # Iniciar minería
            self.set_state(BotState.RUNNING)
            
            # Enviar acknowledgment
            self.send_acknowledgment(msg_dict.get("source", "unknown"), "requirements_received")