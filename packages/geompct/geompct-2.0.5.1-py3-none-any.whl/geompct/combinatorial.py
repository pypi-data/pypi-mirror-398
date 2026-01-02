from itertools import combinations
import cv2 as cv
from shapely.geometry import Polygon
import os
import time

from geompct.preprocess import full_preprocess 
from geompct.utils import *
from geompct.classic_comb_opt import classic_comb_opt
from geompct.sim_metric import sim_metric_evaluation


# --------------------------------------------
# Classic Combination Optimization Evaluation (without similarity metrics)
# --------------------------------------------
def comb_opt(
        OUTPUT_DIR,
        IMG_SHAPE,
        fpath: str = None,
        img_code: str = None,
        DATA_DIR: str = None,
        use_shitomasi: bool = True,
        verbose: bool = False,
        show: bool = False,
        savefig: str = None,
        spath_csv: str = None,
        method: str = "default",     # "default" or "sim_metric"
        sim_metric: str = "chamfer",  # "chamfer", "iou", "ssim"
):
    # Define save dir
    # timestamp = time.strftime("%Y%m%d-%H%M%S")
    # SAVEDIR = os.path.join(OUTPUT_DIR, f"run-{timestamp}")
    SAVEDIR = OUTPUT_DIR
    os.makedirs(SAVEDIR, exist_ok=True)
    if verbose:
        print(f"Created save directory at: {SAVEDIR}")

    # Main processing
    if DATA_DIR is None or img_code is None:
        img_path = fpath
    else: 
        img_path = os.path.join(DATA_DIR, f"{img_code}.jpg")
    img = cv.imread(img_path)

    # Mostly, we will process with the first case (with fpath, as the img_code and DATA_DIR are only used when we have a dataset folder with specific image codes to process)
    if verbose: 
        print(f"Image shape: {img.shape}")  # (height, width, channels)

    # reshape the image to (500, 500)
    resized = cv.resize(img, IMG_SHAPE, interpolation=cv.INTER_AREA)
    if verbose:
        print(f"Resized image shape: {resized.shape}")  # (height, width, channels)

    corners, skel  = full_preprocess(resized, use_shitomasi=use_shitomasi, verbose=verbose)
    all_vertices = collect_all_vertices(corners)
    if verbose: 
        print(f"Total corners collected: {len(all_vertices)}")
        
    distances, matrices = construct_matrices_dist(all_vertices)
    if verbose:
        print(f"Distance matrix shape: {matrices.shape}")

    df = pd.DataFrame(matrices)
    thres = hist_thres(df)
    if verbose:
        print(f"Determined distance threshold: {thres}")

    filtered_points = filter_close_vertices(df, all_vertices)
    if verbose:
        print(f"Number of points after filtering: {len(filtered_points)}")  
    final_points = merge_close_vertices(filtered_points)
    if verbose:
        print(f"Number of points after merging: {len(final_points)}")
    
    if method == "default":
        return classic_comb_opt(final_points, show=show, savefig=os.path.join(SAVEDIR, "matrix_dist_comb_opt.png"))   # --> return the result of the Pentagon Copying Test evaluation from the MMSE test
    
    else: 
        if verbose:
            print(f"Using similarity metric evaluation with metric: {sim_metric}")
        return sim_metric_evaluation(
            resized,
            final_points,
            metric=sim_metric,
            verbose=verbose,
            show=show,
        )
