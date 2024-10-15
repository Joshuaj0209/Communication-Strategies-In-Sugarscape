# constants.py
import math


GAME_WIDTH, HEIGHT = 750, 750
ANALYTICS_WIDTH = 300
WIDTH = GAME_WIDTH + ANALYTICS_WIDTH
SUGAR_RADIUS = 20
ANT_SIZE = 10
ANT_SPEED = 1
NUM_ANTS = 3
SUGAR_MAX = 81
SUGAR_REGENERATION_RATE = 0.0002
SQUARE_SIZE = 5
SUGAR_PATCH_RADIUS = 40  # Adjust as needed

FRAMES_PER_SECOND = 60
MILLISECONDS_PER_FRAME = 1000 / FRAMES_PER_SECOND  # Approximately 16.67 ms/frame
NEW_SUGAR_INTERVAL = int(10000 / MILLISECONDS_PER_FRAME)

COMMUNICATION_RADIUS = 7000
DETECTION_RADIUS = 65

TARGET_SELECTION_INTERVAL = int(8000 / MILLISECONDS_PER_FRAME)



grid_size = int(math.sqrt(SUGAR_MAX))  # Grid size for sugar patch
PATCH_RADIUS = math.sqrt((SQUARE_SIZE * grid_size) ** 2 + (SQUARE_SIZE * grid_size) ** 2)

# Ant health constants
INITIAL_HEALTH = 100
MAX_HEALTH = 150
HEALTH_DECREASE_RATE = 0.07
HEALTH_INCREASE_AMOUNT = 10

# Colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
YELLOW = (255, 255, 0)
GRAY = (200, 200, 200)