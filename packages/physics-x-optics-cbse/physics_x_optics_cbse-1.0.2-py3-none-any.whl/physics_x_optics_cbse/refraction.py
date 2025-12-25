import math
from .constants import C, N_AIR

def refractive_index_from_speed(v_medium, c=C):
    return c / v_medium

def speed_in_medium(n, c=C):
    return c / n

def snells_law_find_r(n1, i_deg, n2):
    i_rad = math.radians(i_deg)
    sin_r = (n1 * math.sin(i_rad)) / n2
    if abs(sin_r) > 1:
        raise ValueError("Total internal reflection")
    r_rad = math.asin(sin_r)
    return math.degrees(r_rad)

def critical_angle(n_dense, n_rare=N_AIR):
    C_rad = math.asin(n_rare / n_dense)
    return math.degrees(C_rad)

def apparent_depth(real_depth, n_medium):
    return real_depth / n_medium
