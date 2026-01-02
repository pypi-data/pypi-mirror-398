# Import necessary libraries
import cv2 as cv
import numpy as np
import matplotlib.pyplot as plt
import pandas as pd 
import seaborn as sns
sns.set(style="whitegrid")
from skimage.morphology import skeletonize
from scipy.spatial import distance
from typing import Tuple

import time
import os 

import random 
random.seed(42)


"""
PREPROCESSING STEPS
    1. Basic preprocessing -- preprocess (func)
    2. Connect endpoints closer than thres -- connect_endp_thres (func)
    3. Skeletonization -- skeletonization (func)
"""


def preprocess(
        IM, 
        GAUSSIAN_BLUR: Tuple[int, int] = (5,5), 
        CANNY_THRESH: Tuple[int, int] = (50, 150),
        morphologyEx_ite: int = 2       # put morphologyEx_ite to eliminate extra blob in segments
):
    gray = cv.cvtColor(IM, cv.COLOR_BGR2GRAY)
    blurred = cv.GaussianBlur(gray, GAUSSIAN_BLUR, 0)
    edges = cv.Canny(blurred, CANNY_THRESH[0], CANNY_THRESH[1])

    kernel = np.ones((3,3), np.uint8)
    edges = cv.morphologyEx(edges, cv.MORPH_CLOSE, kernel, iterations=morphologyEx_ite)
    
    return edges

def connect_endp_thres(
        edges,
        THRES_DIST: int = 10,
        mode = cv.RETR_TREE,
        method = cv.CHAIN_APPROX_SIMPLE,
        line_thinkness: int = 10,
        verbose: bool = False
):
    contours, hierarchy = cv.findContours(edges, mode, method)      # We currently don't use hierarchy here

    endpoints = []
    for cnt in contours:
        if len(cnt) > 1:
            # print(len(cnt))
            endpoints.append(cnt[0][0])
            endpoints.append(cnt[-1][0])
            # print(endpoints[-1])

    # Connect endpoints closer than threshold
    for i in range(len(endpoints)):
        for j in range(i+1, len(endpoints)):
            if distance.euclidean(endpoints[i], endpoints[j]) < THRES_DIST:
                if verbose: 
                    print(f"Connecting {endpoints[i]} and {endpoints[j]} of distance {distance.euclidean(endpoints[i], endpoints[j])}")
                cv.line(edges, tuple(endpoints[i]), tuple(endpoints[j]), 255, line_thinkness)

    return edges


def skeletonization(edges):
    # Convert to boolean: True = line, False = background
    img_bool = edges > 0
    skeleton = skeletonize(img_bool)
    skeleton = (skeleton * 255).astype(np.uint8)

    # # skeletonization
    # _, bw = cv.threshold(edges, 0, 255, cv.THRESH_BINARY + cv.THRESH_OTSU)
    # skeleton = cv.ximgproc.thinning(bw, thinningType=cv.ximgproc.THINNING_ZHANGSUEN)

    return skeleton


def shi_tomasi_corners(
        IM,
        max_corners: int = 100,
        quality_level: float = 0.01,
        min_distance: int = 10,
        block_size: int = 3,
        use_harris: bool = True,
        k: float = 0.04,
        verbose: bool = False
):
    gray = cv.cvtColor(IM, cv.COLOR_BGR2GRAY)
    corners = cv.goodFeaturesToTrack(
        # gray, 25, 0.01, 10,
        gray,
        maxCorners=max_corners, 
        qualityLevel=quality_level, 
        minDistance=min_distance, 
        blockSize=block_size, 
        useHarrisDetector=use_harris, 
        k=k
    )
    # corners = np.int0(corners)
    # corner_points = [tuple(pt[0]) for pt in corners]
    if verbose:
        print(f"Detected {len(corners)} corners using Shi-Tomasi method.")
    return corners

def full_preprocess(
        IM,
        GAUSSIAN_BLUR: Tuple[int, int] = (5,5), 
        CANNY_THRESH: Tuple[int, int] = (50, 150),
        morphologyEx_ite: int = 2,
        THRES_DIST: int = 10,
        line_thinkness: int = 10,
        use_shitomasi: bool = True,
        verbose: bool = False
):
    """
    TODO: test this function    
    """

    # If not using Shi-Tomasi, connect endpoints closer than threshold
    # Otherwise, skip this step, as Shi-Tomasi already connects close points + have higher accuracy on corners and vertices detection

    if not use_shitomasi:
        edges = preprocess(IM, GAUSSIAN_BLUR, CANNY_THRESH, morphologyEx_ite)
        
        edges_connected = connect_endp_thres(edges, THRES_DIST, line_thinkness=line_thinkness, verbose=verbose)

        skeleton = skeletonization(edges_connected)
        return None, skeleton
    else:
        # print("Using Shi-Tomasi corner detection, skipping endpoint connection step...")
        edges = preprocess(IM, GAUSSIAN_BLUR, CANNY_THRESH, morphologyEx_ite)

        edges_connected = shi_tomasi_corners(IM)
        skeleton = skeletonization(edges)
        return edges_connected, skeleton