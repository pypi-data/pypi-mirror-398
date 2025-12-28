import math

dtr = math.pi / 180

def sind(x: float) -> float:
    return math.sin(dtr * x)

def cosd(x: float) -> float:
    return math.cos(dtr * x)

def tand(x: float) -> float:
    return math.tan(dtr * x)

def asind(x: float) -> float:
    return math.asin(x) / dtr

def acosd(x: float) -> float:
    return math.acos(x) / dtr

def atand(x: float) -> float:
    return math.atan(x) / dtr

def norm360(x: float) -> float:
    return x % 360

def norm24(x: float) -> float:
    return x % 24

