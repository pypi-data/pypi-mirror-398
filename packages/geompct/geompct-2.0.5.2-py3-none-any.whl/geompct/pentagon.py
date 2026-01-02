import math
from shapely.geometry import Polygon

# Base functions
def distance(p1, p2):
    """Calculate Euclidean distance between two points."""
    # return math.sqrt((p1[0] - p2[0]) ** 2 + (p1[1] - p2[1]) ** 2)
    return math.hypot(p2[0] - p1[0], p2[1] - p1[1])     # --> better numerical stability and overflow handling

def angle(a, b, c):
    """
    Angle at point b formed by points (a, b, c).
    Uses the law of cosines.
    """
    ab = distance(a, b)
    bc = distance(b, c)
    ac = distance(a, c)
    if ab * bc == 0:
        return 0
    
    cos_theta = (ab**2 + bc**2 - ac**2) / (2 * ab * bc)
    cos_theta = max(-1, min(1, cos_theta))  # Clamp to avoid numerical issues
    return math.degrees(math.acos(cos_theta))

import numpy as np

def order_polygon(points):
    pts = np.asarray(points, dtype=np.float32)
    center = pts.mean(axis=0)
    angles = np.arctan2(pts[:, 1] - center[1],
                        pts[:, 0] - center[0])
    return pts[np.argsort(angles)]

def is_pentagon(
    points,
    LENGTH_RATIO_TOL=3.0,              # max_len / min_len
    ANGLE_RANGE=(60, 160),              # hard bounds
    REF_ANGLE=108,
    MEAN_ERR_TOL=20,
    TURN_SUM_TOL=15
):
    """
    Robust pentagon validity check for human-drawn shapes (PCT).
    """

    if len(points) != 5:
        return False

    pts = order_polygon(points)

    # ---- Edge length check (weak constraint) ----
    edges = [distance(pts[i], pts[(i+1) % 5]) for i in range(5)]
    min_len, max_len = min(edges), max(edges)

    if min_len <= 1e-6:
        return False

    if max_len / min_len > LENGTH_RATIO_TOL:
        return False

    # ---- Angle computation ----
    angles = [
        angle(pts[i-1], pts[i], pts[(i+1) % 5])
        for i in range(5)
    ]

    angles = np.array(angles)

    # ---- Absolute kill rules ----
    if np.any(angles < 45) or np.any(angles > 170):
        return False

    # ---- Hard per-angle bounds ----
    if np.any(angles < ANGLE_RANGE[0]) or np.any(angles > ANGLE_RANGE[1]):
        return False

    # ---- Mean deviation from regular pentagon ----
    mean_err = np.mean(np.abs(angles - REF_ANGLE))
    if mean_err > MEAN_ERR_TOL:
        return False

    # ---- Turning angle consistency ----
    turning_sum = np.sum(180 - angles)
    if abs(turning_sum - 360) > TURN_SUM_TOL:
        return False

    return True




# ----------------------------------------
# Helper functions
# TODO: test these functions
# ----------------------------------------

def fix_polygon(coords):
    # --- Helper: fix invalid polygons (self-intersections) ---
    poly = Polygon(coords)
    if not poly.is_valid:
        poly = poly.buffer(0)
    return poly

def is_convex(coords):
    if len(coords) < 4:
        return False

    direction = 0
    n = len(coords)

    for i in range(n):
        p0 = coords[i]
        p1 = coords[(i+1) % n]
        p2 = coords[(i+2) % n]

        dx1, dy1 = p1[0]-p0[0], p1[1]-p0[1]
        dx2, dy2 = p2[0]-p1[0], p2[1]-p1[1]

        cross = dx1 * dy2 - dy1 * dx2  # 2D cross product

        if cross != 0:  # ignore collinear
            if direction == 0:
                direction = 1 if cross > 0 else -1
            elif direction * cross < 0:
                return False

    return True

def compute_angles(coords):
    angles = []
    n = len(coords)
    for i in range(n):
        p_prev = coords[(i-1) % n]
        p = coords[i]
        p_next = coords[(i+1) % n]

        # vectors
        v1 = (p_prev[0]-p[0], p_prev[1]-p[1])
        v2 = (p_next[0]-p[0], p_next[1]-p[1])

        # dot product & magnitudes
        dot = v1[0]*v2[0] + v1[1]*v2[1]
        mag1 = math.sqrt(v1[0]**2 + v1[1]**2)
        mag2 = math.sqrt(v2[0]**2 + v2[1]**2)

        if mag1 * mag2 == 0:
            angles.append(None)
        else:
            cos_angle = max(-1, min(1, dot / (mag1*mag2)))
            angle_deg = math.degrees(math.acos(cos_angle))
            angles.append(angle_deg)

    return angles