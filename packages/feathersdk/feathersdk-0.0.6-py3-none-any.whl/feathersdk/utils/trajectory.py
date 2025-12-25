def change_in_pos(v0, a0, jerk, t1, t2):
    """
    jerk = 0 if constant acceleration.
    """
    return v0 * (t2 - t1) + a0 * (t2 - t1)**2 / 2 + jerk * (t2 - t1)**3 / 6

def change_in_vel(a0, jerk, t1, t2):
    return a0 * (t2 - t1) + jerk * (t2 - t1)**2 / 2