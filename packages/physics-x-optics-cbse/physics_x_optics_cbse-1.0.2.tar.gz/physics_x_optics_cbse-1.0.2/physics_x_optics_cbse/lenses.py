def lens_formula(u, v):
    return 1 / ((1 / v) - (1 / u))

def magnification_lens(u=None, v=None, h_i=None, h_o=None):
    if u is not None and v is not None:
        return v / u
    if h_i is not None and h_o is not None:
        return h_i / h_o
    raise ValueError("Provide (u and v) OR (h_i and h_o)")

def power_of_lens(f_cm=None, f_m=None):
    if f_m is None:
        f_m = f_cm / 100
    return 1 / f_m
