from scipy.ndimage import distance_transform_edt
import numpy as np
import cv2 as cv
from itertools import combinations
from skimage.metrics import structural_similarity as ssim
from geompct.pentagon import fix_polygon, is_convex, compute_angles
from tqdm import tqdm
import matplotlib.pyplot as plt
import seaborn as sns
sns.set(style="whitegrid")

def sim_metric_evaluation(
        resized,
        final_points,
        metric: str = "chamfer",  # "chamfer", "iou", "ssim"
        verbose: bool = False,
        show: bool = False,
):
    """
    Evaluate the similarity between the candidate pentagon drawing and the reference pentagon drawing
    using the specified similarity metric.

    Args:
    - resized: The preprocessed image containing the drawing of size (500, 500, channels).
    - final_points: List of detected vertices points.
    - metric: Similarity metric to use. Options are "chamfer", "iou", "ssim".
    - verbose: If True, print detailed logs.
    - show: If True, display intermediate results.
    - savefig: If provided, save the figure to this path.
    """
    tmp = list(combinations(final_points, 5))

    _, binary = cv.threshold(
            resized,
            127,      # threshold
            255,
            cv.THRESH_BINARY
        )

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
        poly = fix_polygon(pent)
        
        if not poly.is_valid:
            if verbose:
                print(f"Combination index {i} is invalid polygon.")
            continue
        
        if is_convex(pent):
            angles = compute_angles(pent)
            if sum(angles) == 540:          # Following Geometric theory by Archimedes
                if verbose:
                    print(f"Valid convex pentagon found at index {i}: {pent} with angles {angles}")

                valid_pent.append(pent)

    if verbose: 
        print(f"Total valid pentagons found: {len(valid_pent)}")

    # Construct intersection matrix
    if len(valid_pent) > 0: 
        matrix = np.zeros((len(valid_pent), len(valid_pent)))
        all_chamfer_scores = []

        # for i in tqdm(range(len(valid_pent))):
        for i in range(len(valid_pent)):
            for j in range(i + 1, len(valid_pent)):
                pent1 = valid_pent[i]
                pent2 = valid_pent[j]
                cand_img = render_candidate([pent1, pent2], binary.shape)
                if metric == "chamfer":
                    score = chamfer_image(binary, cand_img)
                else: 
                    if verbose: 
                        print(f"WARNING: Metric {metric} not implemented yet. Defaulting to chamfer.")
                    score = chamfer_image(binary, cand_img)
                # print(f"Chamfer score between image and candidate pentagons {i} & {j}: {score}")
                matrix[i, j] = score
                matrix[j, i] = score  # Symmetric matrix

                all_chamfer_scores.append(score)

        if show: 
            plt.figure(figsize=(10, 8))
            sns.heatmap(matrix, annot=False, cmap="YlGnBu")
            plt.title("Pentagon Intersection Matrix")
            plt.xlabel("Pentagon Index")
            plt.ylabel("Pentagon Index")
            plt.show()


        # Apply thresholding to filter out high distances
        M = matrix.copy()

        # kill diagonal
        np.fill_diagonal(M, np.inf)

        # if you also want to ignore any remaining zeros
        M[M == 0] = np.inf

        flat_idx = np.argmin(M)
        i, j = np.unravel_index(flat_idx, M.shape)

        min_value = M[i, j]
        if verbose:
            print(f"Minimum chamfer score is between pentagons {i} and {j}: {min_value}")

        mask = np.triu(np.ones_like(M, dtype=bool), k=1)
        masked = np.where(mask, M, np.inf)

        i, j = np.unravel_index(np.argmin(masked), M.shape)
        min_value = masked[i, j]
        K = 5
        flat = M.flatten()
        idxs = np.argsort(flat)

        pairs = []
        for idx in idxs:
            if flat[idx] == np.inf:
                continue
            i, j = np.unravel_index(idx, M.shape)
            pairs.append((i, j, flat[idx]))
            if len(pairs) == K:
                break

        if verbose: 
            print(f"Best pair: {i}, {j}  |  Chamfer = {min_value:.2f}")

            if show: 
                # plot pair
                plt.figure(figsize=(5, 5))
                plt.imshow(resized, cmap='gray')
                pent1 = pentagon_list[i]
                pent2 = pentagon_list[j]
                pent1 = np.array(pent1)
                pent2 = np.array(pent2)
                plt.plot(*np.append(pent1, [pent1[0]], axis=0).T, marker='o',)  
                plt.plot(*np.append(pent2, [pent2[0]], axis=0).T, marker='o',)  # Close the pentagon
                plt.title(f"Best Pentagon Pair with Chamfer = {min_value:.2f}")
                plt.show()

        scores = np.array(all_chamfer_scores)
        H, W,_ = resized.shape

        if len(scores) == 0:
            best = 1e-6  # prevent division by zero
            second = best
            confidence = 0
            if verbose:
                print("No chamfer scores available.")
                print(f"Confidence score {confidence}")
            valid = 0
            return valid

        else: 
            best = scores.min()
            if verbose:
                print(f"Best chamfer score: {best}")
            if best == 0:
                best = 1e-6  # prevent division by zero

            if len(scores) < 2:
                second = best  # if only one score, set second to best to avoid error
                
            else: second = np.partition(scores, 1)[1]

            confidence = second / best
            if verbose:
                print(f"Confidence score {confidence}")

        if confidence < 1.0:
            valid = 0
            if verbose:
                print("Low confidence in pentagon detection.")
        else:
            valid = 1
            if verbose:
                print("High confidence in pentagon detection.")

        return valid












# ----------------------------------------
# UTILS FUNCTIONS
# ----------------------------------------

def order_polygon(points):
    pts = np.asarray(points, dtype=np.float32)

    if pts.ndim != 2 or pts.shape[1] != 2:
        raise ValueError(f"Expected (N,2) points, got {pts.shape}")

    center = pts.mean(axis=0)
    angles = np.arctan2(pts[:, 1] - center[1],
                        pts[:, 0] - center[0])
    order = np.argsort(angles)
    return pts[order].astype(np.int32)

def render_candidate(pentagons, shape):
    canvas = np.zeros(shape, dtype=np.uint8)

    for pent in pentagons:
        ordered = order_polygon(pent)
        pts = ordered.reshape((-1, 1, 2))
        cv.polylines(
            canvas,
            [pts],
            isClosed=True,
            color=255,
            thickness=2
        )

    return canvas




# ----------------------------------------
# CHAMFER DISTANCE
# ----------------------------------------
def chamfer_image(img1, img2):
    """
    Compute the chamfer distance between two binary images.
    Both images should be binary (0s and 255s).
    0 represents background, 255 represents edges.

    Note that lower chamfer distance indicates higher similarity.
    """
    dt1 = distance_transform_edt(255 - img1)
    dt2 = distance_transform_edt(255 - img2)

    e1 = img1 > 0
    e2 = img2 > 0

    return dt1[e2].mean() + dt2[e1].mean()


# TODO: test chamfer distance function comparing to these distance metrics
# ----------------------------------------
# IoU DISTANCE
# ----------------------------------------
def iou(a, b):
    inter = np.logical_and(a > 0, b > 0).sum()
    union = np.logical_or(a > 0, b > 0).sum()
    return 1 - inter / union

# ----------------------------------------
# Structural Similarity DISTANCE
# ----------------------------------------
def ssim_distance(img1, img2):
    """
    Compute the Structural Similarity Index (SSIM) distance between two images.
    Both images should be grayscale.

    Note that lower SSIM distance indicates higher similarity.
    """
    ssim_index, _ = ssim(img1, img2, full=True)
    return 1 - ssim_index
