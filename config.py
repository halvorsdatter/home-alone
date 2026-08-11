from dotenv import load_dotenv
load_dotenv()

CAPTURE_WIDTH  = 640
CAPTURE_HEIGHT = 480

# Set after running find_roi.py on the Pi
DOOR_ROI  = (270,  50, 100, 380)   # PLACEHOLDER
DOOR_ZONE = (220,   0, 200, 480)   # PLACEHOLDER

# Direction detection
DIRECTION_MOVEMENT_THRESHOLD = 20   # min pixel distance-change before classifying

# Motion detection
MOTION_THRESHOLD       = 500
MOTION_COOLDOWN_FRAMES = 30

# Tracking
MAX_DISAPPEARED_FRAMES = 30
DIRECTION_HISTORY_LEN  = 30
DIRECTION_MIN_FRAMES   = 10
CENTROID_MATCH_DIST    = 80
FACE_TRACK_ASSOC_DIST  = 80

# InsightFace
INSIGHTFACE_MODEL       = "buffalo_s"
ARCFACE_MATCH_THRESHOLD = 0.55
IDENTITY_LOCK_VOTES     = 3

# Queue sizes
FACE_QUEUE_MAXSIZE  = 1    # size 1: FaceWorker always processes freshest frame
WRITE_QUEUE_MAXSIZE = 50

# Entry/Exit
EVENT_WINDOW_CLOSE_GRACE = 4.0
EVENT_COOLDOWN           = 30.0

# Firebase
FIREBASE_CREDENTIAL_PATH = "serviceAccountKey.json"
FIREBASE_COLLECTION      = "roommates"