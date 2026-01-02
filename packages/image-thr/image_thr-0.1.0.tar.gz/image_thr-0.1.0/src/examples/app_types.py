
import time

class UAV:
    def __init__(self, cam_name, dx_deg: float, dy_deg: float, yaw_deg: float, pitch_deg: float, 
                 width_deg: float = 0, height_deg: float = 0, distance_m: float = 0, altitude_m: float = 0, confidence: float = 0, size_cm: float = None, class_name: str = None):
        self.id = id
        self.last_updated = time.time()
        self.cam_name = cam_name
        self.dx_deg = dx_deg
        self.dy_deg = dy_deg
        self.yaw_deg = yaw_deg
        self.pitch_deg = pitch_deg
        self.width_deg = width_deg
        self.height_deg = height_deg
        self.distance_m = distance_m
        self.altitude_m = altitude_m
        self.speedx_degs = 0
        self.speedy_degs = 0
        self.speedz_ms = 0
        self.speed_ms = 0
        self.confidence = confidence
        self.size_cm = size_cm
        self.class_name = class_name
    
class ContourParams:
    def __init__(self, size_cm, center_x, center_y, w, h, dx_deg, dy_deg,  w_deg, h_deg):
        self.size_cm = size_cm
        self.center_x = center_x
        self.center_y = center_y
        self.w = w
        self.h = h
        self.dx_deg = dx_deg
        self.dy_deg = dy_deg
        self.w_deg = w_deg
        self.h_deg = h_deg
