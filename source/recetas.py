from mcpi import block

RECETAS = {
    # --- BÁSICOS DE MADERA ---

    # 1 tronco -> 4 tablones
    "planks_from_log": {
        "outputs": [
            {"tipo": "item", "id": "planks", "data": 0, "cantidad": 4}
        ],
        "inputs": [
            {"tipo": "block", "id": block.WOOD.id, "data": 0, "cantidad": 1}
        ],
    },

    # 2 tablones -> 4 palos
    "sticks_from_planks": {
        "outputs": [
            {"tipo": "item", "id": "stick", "data": 0, "cantidad": 4}
        ],
        "inputs": [
            {"tipo": "item", "id": "planks", "data": 0, "cantidad": 2}
        ],
    },

    # --- LUZ / COMBUSTIBLE ---

    # 1 carbón + 1 palo -> 4 antorchas
    "torch_from_coal_and_stick": {
        "outputs": [
            {"tipo": "block", "id": block.TORCH.id, "data": 0, "cantidad": 4}
        ],
        "inputs": [
            {"tipo": "item", "id": "coal",  "data": 0, "cantidad": 1},
            {"tipo": "item", "id": "stick", "data": 0, "cantidad": 1},
        ],
    },

    # 1 tronco -> 4 carbón vegetal (charcoal)
    "charcoal_from_log": {
        "outputs": [
            {"tipo": "item", "id": "charcoal", "data": 0, "cantidad": 1}
        ],
        "inputs": [
            {"tipo": "block", "id": block.WOOD.id, "data": 0, "cantidad": 1},
            {"tipo": "item",  "id": "fuel", "data": 0, "cantidad": 1},
        ],
    },

    # --- BLOQUES DE UTILIDAD ---

    # 4 tablones -> 1 mesa de crafteo
    "crafting_table_from_planks": {
        "outputs": [
            {"tipo": "block", "id": block.CRAFTING_TABLE.id, "data": 0, "cantidad": 1}
        ],
        "inputs": [
            {"tipo": "item", "id": "planks", "data": 0, "cantidad": 4}
        ],
    },

    # 8 roca -> 1 horno
    "furnace_from_cobblestone": {
        "outputs": [
            {"tipo": "block", "id": block.FURNACE.id, "data": 0, "cantidad": 1}
        ],
        "inputs": [
            {"tipo": "block", "id": block.COBBLESTONE.id, "data": 0, "cantidad": 8}
        ],
    },

    # --- ALMACENAMIENTO Y MUEBLES BÁSICOS ---

    # 8 tablones -> 1 cofre
    "chest_from_planks": {
        "outputs": [
            {"tipo": "item", "id": "chest", "data": 0, "cantidad": 1}
        ],
        "inputs": [
            {"tipo": "item", "id": "planks", "data": 0, "cantidad": 8}
        ],
    },

    # 3 lana + 3 tablones -> 1 cama
    "bed_from_planks_and_wool": {
        "outputs": [
            {"tipo": "item", "id": "bed", "data": 0, "cantidad": 1}
        ],
        "inputs": [
            {"tipo": "item", "id": "wool",   "data": 0, "cantidad": 3},
            {"tipo": "item", "id": "planks", "data": 0, "cantidad": 3},
        ],
    },

    # --- PUERTAS, VENTANAS, ACCESO ---

    # 6 tablones -> 3 puertas de madera
    "door_wood_from_planks": {
        "outputs": [
            {"tipo": "item", "id": "door_wood", "data": 0, "cantidad": 3}
        ],
        "inputs": [
            {"tipo": "item", "id": "planks", "data": 0, "cantidad": 6}
        ],
    },

    # 6 bloques de vidrio -> 16 cristales
    "glass_pane_from_glass": {
        "outputs": [
            {"tipo": "item", "id": "glass_pane", "data": 0, "cantidad": 16}
        ],
        "inputs": [
            {"tipo": "block", "id": block.GLASS.id, "data": 0, "cantidad": 6}
        ],
    },

    # --- ESCALERAS, VALLAS, ETC. ---

    # 6 tablones -> 4 escaleras de madera
    "stairs_wood_from_planks": {
        "outputs": [
            {"tipo": "block", "id": block.WOOD_STAIRS.id, "data": 0, "cantidad": 4}
        ],
        "inputs": [
            {"tipo": "item", "id": "planks", "data": 0, "cantidad": 6}
        ],
    },

    # 4 tablones + 2 palos -> 3 vallas de madera
    "fence_wood_from_planks_and_sticks": {
        "outputs": [
            {"tipo": "item", "id": "fence_wood", "data": 0, "cantidad": 3}
        ],
        "inputs": [
            {"tipo": "item", "id": "planks", "data": 0, "cantidad": 4},
            {"tipo": "item", "id": "stick",  "data": 0, "cantidad": 2},
        ],
    },

    # 6 tablones -> 2 vallas-puerta (gate)
    "fence_gate_from_planks_and_sticks": {
        "outputs": [
            {"tipo": "item", "id": "fence_gate", "data": 0, "cantidad": 1}
        ],
        "inputs": [
            {"tipo": "item", "id": "planks", "data": 0, "cantidad": 4},
            {"tipo": "item", "id": "stick",  "data": 0, "cantidad": 2},
        ],
    },

    # --- REDSTONE SIMPLE / INTERACCIÓN ---

    # 2 bloques de madera -> 1 botón de madera
    "button_wood_from_planks": {
        "outputs": [
            {"tipo": "item", "id": "button_wood", "data": 0, "cantidad": 1}
        ],
        "inputs": [
            {"tipo": "item", "id": "planks", "data": 0, "cantidad": 1}
        ],
    },

    # 3 tablones + 2 palos -> 1 placa de presión de madera
    "pressure_plate_wood_from_planks": {
        "outputs": [
            {"tipo": "item", "id": "pressure_plate_wood", "data": 0, "cantidad": 1}
        ],
        "inputs": [
            {"tipo": "item", "id": "planks", "data": 0, "cantidad": 2}
        ],
    },

    # --- BLOQUES VARIOS ÚTILES ---

    # 3 bloques de piedra -> 1 piedra lisa (para simplificar)
    "stone_slab_from_stone": {
        "outputs": [
            {"tipo": "item", "id": "stone_slab", "data": 0, "cantidad": 6}
        ],
        "inputs": [
            {"tipo": "block", "id": block.STONE.id, "data": 0, "cantidad": 3}
        ],
    },

    # 3 bloques de arena -> 1 cristal (vidrio)
    "glass_from_sand": {
        "outputs": [
            {"tipo": "block", "id": block.GLASS.id, "data": 0, "cantidad": 1}
        ],
        "inputs": [
            {"tipo": "block", "id": block.SAND.id, "data": 0, "cantidad": 1},
            {"tipo": "item",  "id": "fuel",       "data": 0, "cantidad": 1},
        ],
    },
}