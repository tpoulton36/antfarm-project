# src/antfarm/config.py

GRID_W = 80
GRID_H = 50
CELL_SIZE = 14  # pixels

FPS = 60
SIM_TPS = 12  # simulation ticks per second (grid decisions)

NUM_ANTS = 20

# Visual tweaks
ANT_RADIUS = 4
FOOD_RADIUS = 5
NEST_RADIUS = 7

# Pheromones
PHER_DECAY = 0.95          # multiply pheromone by this each sim tick
PHER_DIFFUSE_EVERY = 2     # diffuse every N sim ticks (0 to disable)
PHER_DIFFUSE_RATE = 0.20   # how strongly it blends with neighbors

PHER_DEPOSIT_FOOD = 3.0    # deposit when carrying food
PHER_HOME_SOURCE = 6.0     # nest cell gets reinforced each tick

W_FOOD_PHER = 1.8          # how much ants follow food pheromone when searching
W_HOME_PHER = 2.0          # how much ants follow home pheromone when returning
W_RANDOM = 0.25            # randomness to prevent lock-in

