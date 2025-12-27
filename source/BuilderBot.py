from datetime import time
from mcpi import block
from .BaseAgent import BaseAgent, BotState
from mcpi.minecraft import Minecraft
from mcpi.vec3 import Vec3
from .Message import Message
from .MessageBus import MessageBus
from dataclasses import asdict
import random

class BuilderBot(BaseAgent):
    def __init__(self, mc, name, start_pos: Vec3, agent_id: int, bus: MessageBus, build_plan, tick_time=0.05):
        super().__init__(mc, "BuilderBot", start_pos, agent_id, bus, tick_time=tick_time)
        self.build_plan = list(build_plan)
        self.index = 0
        self.map_database = {}
        self.aviable_sites = []
        self.bom = {}
        self.inventory = {}
        self.construction_going = False


    def perceive(self):
        """Observa el entorno: inventario, sitios disponibles y estado de construcción"""
        # 1. Verificar si tenemos todos los materiales
        has_materials = self.check_inventory_against_requirements()
        
        # 2. Verificar si hay sitios disponibles
        has_sites = len(self.aviable_sites) > 0
        
        # 3. Verificar si ya terminamos el plan actual
        plan_completed = self.index >= len(self.build_plan)
        
        # 4. Verificar si estamos en medio de una construcción
        currently_building = self.construction_going
        
        print(f"[{self.name}] perceive -> materials: {has_materials}, sites: {has_sites}, "
            f"completed: {plan_completed}, building: {currently_building}")
        
        # Retornar observaciones como dict
        return {
            "has_materials": has_materials,
            "has_sites": has_sites,
            "plan_completed": plan_completed,
            "construction_going": currently_building,
            "current_index": self.index,
            "total_blocks": len(self.build_plan)
        }

    def decide(self, obs):
        """Decide qué acción tomar basado en las observaciones"""
        
        # Si no tenemos materiales, solicitar más
        if not obs["has_materials"]:
            print(f"[{self.name}] decide -> Faltan materiales, solicitando...")
            self.send_material_request()
            return {"action": "REQUEST_MATERIALS"}
        
        # Si no tenemos sitios, esperar exploración
        if not obs["has_sites"]:
            print(f"[{self.name}] decide -> Esperando sitios disponibles...")
            return {"action": "WAIT_FOR_SITES"}
        
        # Si no estamos construyendo pero podemos empezar
        if not obs["construction_going"] and obs["has_materials"] and obs["has_sites"]:
            print(f"[{self.name}] decide -> Iniciando construcción...")
            self.construction_going = True
            self.current_site = self.choose_random_site()
            
            if self.current_site:
                print(f"[{self.name}] decide -> Sitio seleccionado: {self.current_site}")
                # Resetear índice para nueva construcción
                self.index = 0
                return {"action": "START_CONSTRUCTION", "site": self.current_site}
            else:
                return {"action": "WAIT_FOR_SITES"}
        
        # Si estamos construyendo y no hemos terminado
        if obs["construction_going"] and not obs["plan_completed"]:
            # Obtener la siguiente acción del plan
            next_action = self.build_plan[self.index]
            print(f"[{self.name}] decide -> Próximo bloque: {self.index}/{len(self.build_plan)}")
            return {"action": "PLACE_BLOCK", "block_data": next_action, "site": self.current_site}
        
        # Si terminamos la construcción
        if obs["construction_going"] and obs["plan_completed"]:
            print(f"[{self.name}] decide -> Construcción completada!")
            self.construction_going = False
            self.deduct_inventory()
            self.send_build_completion_message(self.current_site)
            return {"action": "CONSTRUCTION_COMPLETE"}
        
        # Caso por defecto: esperar
        print(f"[{self.name}] decide -> Esperando...")
        return {"action": "WAIT"}

    def act(self, decision):
        """Ejecuta la acción decidida"""
        action_type = decision.get("action", "WAIT")
        
        if action_type == "PLACE_BLOCK":
            block_data = decision["block_data"]
            site = decision.get("site", self.current_site)
            
            offset = block_data["offset"]
            block_id = block_data["id"]
            data = block_data.get("data", 0)
            
            # Calcular posición absoluta (sitio + offset relativo)
            abs_pos = Vec3(
                site.x + offset.x,
                site.y + offset.y,
                site.z + offset.z
            )
            
            print(f"[{self.name}] act -> Colocando bloque ID {block_id} en {abs_pos}")
            print(f"  Offset: {offset}, Sitio base: {site}")
            
            # Colocar el bloque (descomentar para acción real)
            # self.mc.setBlock(abs_pos.x, abs_pos.y, abs_pos.z, block_id, data)
            
            # Actualizar progreso
            self.index += 1
            
            # Enviar progreso cada 5 bloques
            if self.index % 5 == 0:
                self.send_build_progress(self.index, len(self.build_plan), site)
            
        elif action_type == "START_CONSTRUCTION":
            site = decision.get("site")
            if site:
                print(f"[{self.name}] act -> Comenzando construcción en sitio {site}")
                self.send_build_start_message(site)
            
        elif action_type == "CONSTRUCTION_COMPLETE":
            print(f"[{self.name}] act -> Construcción finalizada")
            self.current_site = None
            
        elif action_type == "REQUEST_MATERIALS":
            print(f"[{self.name}] act -> Solicitando materiales...")
            self.send_material_request()
            
        elif action_type == "WAIT_FOR_SITES":
            print(f"[{self.name}] act -> Esperando exploración de sitios...")
            time.sleep(2)  # Pequeña pausa
            
        elif action_type == "WAIT":
            print(f"[{self.name}] act -> Esperando condiciones...")
            time.sleep(1)
            
    def build_message(self, x: int,z: int,
    ) -> Message:

        payload = {
            self.get_inventory()
        }

        return super().build_message(
            payload=payload,
            type="materials.requirements.v" + str(self.mess_count),
            source="BuilderBot",          # id único del bot
            target="MinerBot"
        )
    
    def get_inventory(self):
        all_ids = list(map(lambda b: b["id"], self.build_plan))
        unique_ids = list(set(all_ids))
        counts = list(
            map(
                lambda block_id: (
                    block_id,
                    len(list(filter(lambda b: b["id"] == block_id, self.build_plan)))
                ),
                unique_ids
            )
        )
        self.bom = counts
        return counts
    
        #mensajes
    def handle_priv_message(self, msg_dict: dict) -> None:
        msg_type = str(msg_dict.get("type", ""))
        
        if msg_type.startswith("map.v"):
            print(f"[{self.name}] Received map from ExplorerBot")
            payload = dict(msg_dict.get("payload", {}))
            
            center = payload.get("center", Vec3())
            map_key = center.x + center.y + center.z
            
            # Guardar TODO el mapa
            heights = payload.get("heights", {})
            print(f"map received: \n{heights}")
            self.map_database[map_key] = payload.get("heights", {})
            
            # Guardar también las regiones planas por separado
            if(self.poca_diferencia(
                list(
                    map(
                        lambda row: Vec3(center.x + row[0], row[1], center.z + row[2]),
                        payload.get("heights", [])
                    )
                ),
                max_diff=2
            )):
                self.aviable_sites.append(center)
            
            print(f"[{self.name}] Map saved to database. Key: {map_key}")
            print(f"[{self.name}] Available sites: {len(self.aviable_sites)}")

    
    def poca_diferencia(self, heights: list[Vec3], max_diff: int) -> bool:
        ys = list(map(lambda v: v.y, heights))   
        return (max(ys) - min(ys)) <= max_diff
    

    def _handle_priv_command(self, command: str, payload: dict):
        parts = command.lower().split()
        
        if len(parts) >= 2:
            subcommand = parts[1]
            
            if subcommand == "plan":
                if len(parts) >= 3 and parts[
                    
                     2] == "list":
                    print("plan list:")
                elif len(parts) >= 4 and parts[2] == "set":
                    template = parts[3]
                    self.build_plan = payload.get("plan", [])
                    print(f"plan set to: {template} with plan: {self.build_plan}")  
        elif command == "bom":
                print(f"bom: {self.bom}\n")
        elif command == "build":
                self.set_state(BotState.RUNNING) #contruir aunk no se tengn los materiales
        else:
            print(f"[{self.name}] Comando builder incompleto")


    def choose_random_site(self) -> Vec3:

        if self.aviable_sites:
            site = random.choice(self.aviable_sites)
            print(f"[{self.name}] Sitio seleccionado para construir: {site}")
            return site
        else:
            print(f"[{self.name}] No hay sitios disponibles para construir.")
            return None
        
    def check_inventory_against_requirements(self) -> bool:
        # Verificar cada material
        for block_id, required in self.bom.items():
            available = self.inventory.get(block_id, 0)
            if available < required:
                print(f"[{self.name}] Material insuficiente: ID {block_id} (requiere {required}, tiene {available})")
                return False
        print(f"[{self.name}] Inventario suficiente para construir")
        return True        





            