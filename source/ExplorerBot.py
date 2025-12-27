# source/agents/explorer_bot.py
import time
from mcpi.vec3 import Vec3
from mcpi.minecraft import Minecraft
from .BaseAgent import BaseAgent, BotState
import os, csv
import random
from .Message import Message
from datetime import datetime, timezone
from .MessageBus import MessageBus

class ExplorerBot(BaseAgent):
    def __init__(self, mc: Minecraft, start_pos: Vec3, agent_id: int, bus: MessageBus, stepp=5, radius=50):
        super().__init__(mc, "ExplorerBot", start_pos, agent_id, bus)
        self.stepp = stepp
        self.start_pos = start_pos
        self.radius = radius
        self.mapas = 0
        self.visited_starts = []
        self.min_dist = self.radius
        # Añadir timer para envío periódico
        self.last_map_sent = 0
        self.map_interval = 5  # Enviar mapa cada 5 ciclos
    

    def perceive(self):
        """Observa el terreno alrededor de la posición actual"""
        print(f"[{self.name}] Explorando área alrededor de {self.start_pos}")
        
        start_point = Vec3(self.start_pos.x - self.radius, 0, self.start_pos.z - self.radius)
        heights = []
        
        # Escanear área cuadrada
        for i in range(self.radius * 2):
            for j in range(self.radius * 2):
                x = start_point.x + i
                z = start_point.z + j
                h = self.mc.getHeight(x, z)
                
                # Marcar visualmente el área explorada (opcional)
                # self.mc.setBlock(x, int(h), z, 89)  # Luz de glowstone
                
                heights.append(Vec3(x, h, z))
        
        # Guardar esta posición como explorada
        self.visited_starts.append(self.start_pos)
        
        # Calcular estadísticas del terreno
        ys = [v.y for v in heights]
        min_height = min(ys)
        max_height = max(ys)
        avg_height = sum(ys) / len(ys)
        
        print(f"[{self.name}] Terreno: min={min_height}, max={max_height}, avg={avg_height:.1f}")
        
        # Retornar observaciones estructuradas
        return {
            "heights": heights,
            "center": self.start_pos,
            "radius": self.radius,
            "stats": {
                "min": min_height,
                "max": max_height,
                "avg": avg_height,
                "variance": max_height - min_height
            },
            "coverage": len(self.visited_starts),
            "timestamp": datetime.now(timezone.utc).isoformat()
        }

    def decide(self, obs):
        """Decide qué hacer basado en las observaciones del terreno"""
        
        # 1. Procesar y enviar mapa del área explorada
        mapa_json = self.mapa_alturas(obs["heights"])
        
        # 2. Analizar calidad del terreno
        variance = obs["stats"]["variance"]
        is_flat = variance <= 2  # Terreno plano si diferencia máxima ≤ 2 bloques
        
        # 3. Decidir próxima acción
        if len(self.visited_starts) < 5:  # Explorar al menos 5 áreas
            # Calcular nueva posición para explorar
            next_pos = self.nuevo_start_pos(50)
            
            print(f"[{self.name}] decide -> "
                f"Área explorada #{len(self.visited_starts)}, "
                f"variance={variance}, flat={is_flat}, "
                f"siguiente: {next_pos}")
            
            # Enviar mapa al BuilderBot
            self.send_map_update(mapa_json, is_flat)
            
            return {
                "action": "EXPLORE_NEW_AREA",
                "next_position": next_pos,
                "current_area_flat": is_flat,
                "variance": variance
            }
        
        else:
            # Ya exploramos suficiente
            print(f"[{self.name}] decide -> Exploración completada ({len(self.visited_starts)} áreas)")
            
            # Enviar mapa final
            self.send_map_update(mapa_json, is_flat)
            
            return {
                "action": "EXPLORATION_COMPLETE",
                "total_areas": len(self.visited_starts),
                "message": "Exploración terminada"
            }

    def act(self, decision):
        """Ejecuta la acción decidida"""
        action_type = decision.get("action", "WAIT")
        
        if action_type == "EXPLORE_NEW_AREA":
            next_pos = decision["next_position"]
            is_flat = decision["current_area_flat"]
            
            print(f"[{self.name}] act -> Moviendo a nueva área: {next_pos}")
            print(f"  Terreno actual: {'plano' if is_flat else 'montañoso'}")
            
            # Mover a la nueva posición (solo actualizar start_pos)
            old_pos = self.start_pos
            self.start_pos = next_pos
            
            # Opcional: marcar visualmente el movimiento
            # self.mc.setBlock(old_pos.x, old_pos.y + 1, old_pos.z, 0)  # Limpiar marca anterior
            # self.mc.setBlock(self.start_pos.x, self.start_pos.y + 1, self.start_pos.z, 41)  # Nueva marca
            
            # Enviar mensaje de movimiento
            self.send_movement_update(old_pos, next_pos)
            
            # Pequeña pausa entre exploraciones
            time.sleep(0.5)
            
        elif action_type == "EXPLORATION_COMPLETE":
            print(f"[{self.name}] act -> Exploración finalizada")
            print(f"  Total áreas exploradas: {decision['total_areas']}")
            
            # Enviar mensaje de finalización
            self.send_exploration_complete_message()
            
            # Cambiar a estado IDLE
            self.set_state(BotState.IDLE)
            
        elif action_type == "WAIT":
            print(f"[{self.name}] act -> Esperando...")
            time.sleep(1)
    

    def mapa_alturas(self,heights: list[Vec3]):
        lado = self.radius * 2

        # construir matriz de alturas (lista de listas de int)
        lines: list[list[int]] = []
        idx = 0
        for _ in range(lado):          # fila
            fila_vals: list[int] = []
            for _ in range(lado):      # columna
                v = heights[idx]
                fila_vals.append(int(v.y))
                idx += 1
            lines.append(fila_vals)

        # objeto "JSON" listo para json.dumps(...)
        mapa_json = {
            "heights": lines,
            "center": self.start_pos
        }

        return mapa_json

    def nuevo_start_pos(self, intentos=50):
        for _ in range(intentos):
            # generar candidato aleatorio alrededor de la zona ya explorada
            base = self.visited_starts[-1] if self.visited_starts else self.start_pos

            dx = random.randint(-1, 1) * self.radius *2
            dz = random.randint(-1, 1) * self.radius *2

            cand = Vec3(base.x + dx, base.y, base.z + dz)

            # comprobar que está lo bastante lejos de todos los ya usados
            ok = True
            for s in self.visited_starts:
                dist2 = (cand.x - s.x) ** 2 + (cand.z - s.z) ** 2
                if dist2 < (self.min_dist ** 2):
                    ok = False
                    break

            if ok:
                return cand

        # si no encuentra nada “bueno”, devuelve algo simple (fallback)
        return Vec3(self.start_pos.x + 2 * self.radius,
                    self.start_pos.y,
                    self.start_pos.z)

    def build_message(self, mapa_json) -> Message:
        return super().build_message(
            payload = mapa_json,

            type="map.v" + str(self.mapas),
            source="ExplorerBot",          # id único del bot
            target="BuilderBot"
        )

    def handle_priv_message(self, command, msg_dict):
        payload = dict(msg_dict.get("payload", {}))

        if command == "start":
            pos = payload.get("start_pos", Vec3())
            if pos != None:
                self.start_pos = Vec3(pos[0], pos[1], pos[2])
            else:
                self.start_pos = self.mc.player.getTilePos() + Vec3(20,0,20)
        elif command == "set range":
                pos = payload.get("range", self.radius)
                if pos != None:
                    self.radius = int(pos)
                else:
                    self.radius = int(10)
                print(f"[{self.name}] Range set to: {self.radius}")
        else:
            print(f"[{self.name}] Comando explorer incompleto")


    # ExplorerBot.py - Añadir al final de la clase

def send_map_update(self, mapa_json, is_flat: bool):
    """Envía actualización del mapa al BuilderBot"""
    # Añadir metadata adicional
    mapa_json["metadata"] = {
        "is_flat": is_flat,
        "explorer_id": self.id,
        "area_number": len(self.visited_starts),
        "timestamp": datetime.now(timezone.utc).isoformat()
    }
    
    msg = self.build_message(mapa_json)
    print(f"[{self.name}] Enviando mapa v{self.mapas} al BuilderBot")
    print(f"  Centro: {mapa_json['center']}, Plano: {is_flat}")
    
    self.send_message(msg)
    self.mapas += 1

def send_movement_update(self, from_pos: Vec3, to_pos: Vec3):
    """Envía mensaje de movimiento/posición"""
    msg = super().build_message(
        payload={
            "from": {"x": from_pos.x, "y": from_pos.y, "z": from_pos.z},
            "to": {"x": to_pos.x, "y": to_pos.y, "z": to_pos.z},
            "distance": self.calculate_distance(from_pos, to_pos),
            "timestamp": datetime.now(timezone.utc).isoformat()
        },
        type="explorer.movement.v1",
        source=self.name,
        target="System"  # O podría ser "Logger"
    )
    self.send_message(msg)

def send_exploration_complete_message(self):
    """Envía mensaje cuando termina la exploración"""
    msg = super().build_message(
        payload={
            "total_areas": len(self.visited_starts),
            "exploration_radius": self.radius,
            "visited_positions": [
                {"x": pos.x, "y": pos.y, "z": pos.z} 
                for pos in self.visited_starts
            ],
            "timestamp": datetime.now(timezone.utc).isoformat()
        },
        type="exploration.completed.v1",
        source=self.name,
        target="BuilderBot"  # También informar al Builder
    )
    self.send_message(msg)

def calculate_distance(self, pos1: Vec3, pos2: Vec3) -> float:
    """Calcula distancia entre dos puntos"""
    dx = pos2.x - pos1.x
    dz = pos2.z - pos1.z
    return (dx**2 + dz**2) ** 0.5

def handle_priv_message(self, msg_dict: dict):  # Corregir firma
    """Maneja mensajes privados para el ExplorerBot"""
    payload = dict(msg_dict.get("payload", {}))
    
    # Extraer comando del payload
    command = payload.get("command", "")
    
    if command == "start":
        pos = payload.get("start_pos", None)
        if pos is not None and isinstance(pos, (list, tuple)) and len(pos) >= 3:
            self.start_pos = Vec3(pos[0], pos[1], pos[2])
            print(f"[{self.name}] Posición inicial establecida: {self.start_pos}")
            
            # Iniciar exploración
            self.set_state(BotState.RUNNING)
        else:
            self.start_pos = self.mc.player.getTilePos() + Vec3(20, 0, 20)
            print(f"[{self.name}] Usando posición por defecto: {self.start_pos}")
            self.set_state(BotState.RUNNING)
            
    elif command == "set_range" or command == "set range":
        new_range = payload.get("range", self.radius)
        if new_range is not None:
            self.radius = int(new_range)
            print(f"[{self.name}] Rango de exploración cambiado a: {self.radius}")
        else:
            self.radius = 10
            print(f"[{self.name}] Rango establecido a valor por defecto: {self.radius}")
        
    elif command == "status":
        print(f"[{self.name}] Estado actual:")
        print(f"  - Posición: {self.start_pos}")
        print(f"  - Radio: {self.radius}")
        print(f"  - Áreas exploradas: {len(self.visited_starts)}")
        print(f"  - Estado: {self.state}")
        
    else:
        print(f"[{self.name}] Comando no reconocido: {command}")
        print(f"  Comandos disponibles: start, set_range, pause, resume, stop, status")
       