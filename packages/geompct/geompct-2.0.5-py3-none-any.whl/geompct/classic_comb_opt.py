from itertools import combinations
import cv2 as cv
from shapely.geometry import Polygon
import os
import time
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
sns.set(style="whitegrid")

from geompct.pentagon import fix_polygon, is_convex, compute_angles, is_pentagon


def order_polygon(points):
    pts = np.asarray(points, dtype=np.float32)

    if pts.ndim != 2 or pts.shape[1] != 2:
        raise ValueError(f"Expected (N,2) points, got {pts.shape}")

    center = pts.mean(axis=0)
    angles = np.arctan2(pts[:, 1] - center[1],
                        pts[:, 0] - center[0])
    order = np.argsort(angles)
    return pts[order].astype(np.int32)

def classic_comb_opt(
        final_points,
        verbose: bool = False,
        show: bool = False,
        savefig: str = None
):
    """
    Suppose that final_points is the output of merge_close_vertices function (from src.preprocess).

    Evaluate the result of the PCT test of the patient drawing based on the following criteria:
    1. Each pentagon must have 5 vertices.
    2. Each pentagon must be convex.
    3. The sum of all the angles of the pentagon must be exactly 540 degrees (angle value tolerated due to dementia --> hard to force the patient to draw and follow the exact angle range, so we suppose that 40 is enough to evaluate).
    4. The length of each side must be roughly equal (within a certain tolerance of around 15 pixels).
    """
    tmp = list(combinations(final_points, 5))

    if verbose:
        print(f"Total combinations of 5 points from detected vertices: {len(tmp)}")

    # Construct convex pentagons list
    pentagon_list = []
    for comb in tmp:
        cnt = np.array(comb).reshape((-1,1,2))
        epsilon = 0.02 * cv.arcLength(cnt, True)
        approx = cv.approxPolyDP(cnt, epsilon, True)
        if len(approx) == 5:
            if cv.isContourConvex(approx):
                if verbose: 
                    print("Looks like a pentagon:", comb)
                if comb not in pentagon_list:
                    pentagon_list.append(comb)

    # Check valid pentagons
    valid_pent = []

    for i in range(len(pentagon_list)):
        comb = pentagon_list[i]
        pent = list(comb)
        # reorganize points in ordered way
        pent = order_polygon(pent)
        # poly = fix_polygon(pent)
        poly = np.array(pent, np.int32).reshape((-1,1,2))
        
        # if not poly.is_valid:
        #     if verbose:
        #         print(f"Combination index {i} is invalid polygon.")
        #     continue
        
        # if poly.shape[0] == 5 and cv.isContourConvex(poly) and is_pentagon(poly):
        if is_pentagon(pent):
            angles = compute_angles(pent)
            # print(sum(angles))
            if sum(angles) == 540:          # Following Geometric theory by Archimedes
                # if verbose:
                #     print(f"Valid convex pentagon found at index {i}: {pent} with angles {angles}")

                # # Check edge lengths
                # if not valid_edge_lengths(pent):
                #     continue
                # if regularity_score(pent) > 0.25:
                #     continue

                valid_pent.append(pent)

    if verbose:
        print(f"Total valid pentagons found: {len(valid_pent)}")


    # Construct intersection matrix
    if len(valid_pent) > 0: 
        matrices = np.zeros((len(valid_pent), len(valid_pent)))

        for i in range(len(valid_pent)):
            for j in range(len(valid_pent)):
                pent1 = valid_pent[i]
                pent2 = valid_pent[j]
                poly1 = fix_polygon(list(pent1))
                poly2 = fix_polygon(list(pent2))
                
                if poly1.equals(poly2):
                    if verbose:
                        print(f"Pentagon {i} is equal to Pentagon {j}")
                    matrices[i, j] = 0

                else: 
                    if poly1.intersects(poly2):
                        if verbose:
                            print(f"Pentagon {i} intersects with Pentagon {j}")
                        matrices[i, j] = 1
    else: 
        matrices = None

    if show: 
        # plot matrices heatmap
        if matrices is not None: 
            plt.figure(figsize=(10, 8))
            sns.heatmap(matrices, annot=False, cmap="YlGnBu")
            plt.title("Pentagon Intersection Matrix")
            plt.xlabel("Pentagon Index")
            plt.ylabel("Pentagon Index")

            if savefig is not None: 
                plt.savefig(savefig)
                if verbose: 
                    print(f"Pentagon intersection matrix heatmap saved at: {savefig}")

            plt.show()
        else: 
            print("No pentagons to evaluate for intersections.")

    # check if there are any value 1 in the matrices
    if np.any(matrices == 1):
        if verbose: 
            print("There are intersecting pentagons.")
        valid = 1
    else:
        if verbose:
            print("No intersecting pentagons found.")
        valid = 0

    return valid