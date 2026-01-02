from scipy.spatial import distance
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
# from itertools import combinations
import seaborn as sns
sns.set(style="whitegrid")


def collect_all_vertices(corners, verbose=False):
    """
    Suppose corners is a list of detected corner points from Shi-Tomasi method.
    """
    # summarize all polygons element into 1 list
    all_vertices = [point.astype(int).tolist() for poly in corners for point in poly]
    if verbose:
        print(f"Total vertices located: {len(all_vertices)}")

    return all_vertices

def construct_matrices_dist(all_vertices, spath_csv="None", show_graph=False, savefig: str = None):
    """
    Construct distance matrices between all vertices.
    Input:
        all_vertices: list of (x, y) coordinates of all vertices
    Output:
        distances: dict of distances between all vertex pairs
        matrices: 2D numpy array of distances
    """

    N = len(all_vertices)

    distances = dict()
    matrices = []

    for i in range(N):
        tmp = []
        # for j in range(i + 1, N):
        for j in range(N):
            pt1 = all_vertices[i]
            pt2 = all_vertices[j]
            dist = distance.euclidean(pt1, pt2)
            distances[f'P{pt1}-P{pt2}'] = dist
            tmp.append(dist)
        matrices.append(tmp)

    if spath_csv != "None":
        df = pd.DataFrame(matrices)
        df.to_csv(spath_csv, index=False)
        print(f"Distance matrix saved at: {spath_csv}")

    if show_graph:
        df = pd.DataFrame(matrices)
        plt.figure(figsize=(20, 15))
        sns.heatmap(df, annot=True, fmt=".2f", cmap="YlGnBu")
        plt.title("Distance Matrix Heatmap")
        plt.xlabel("Point Index")
        
        if savefig is not None:
            plt.savefig(savefig)
            print(f"Distance matrix heatmap saved at: {savefig}")
            
        plt.show()

    return distances, np.array(matrices)

def hist_thres(df, verbose=False, show_plot=False, savefig: str = None):
    """
    Given a distance dataframe,locate the threshold distance to connect nearby vertices.
    Use histogram method to find the elbow point.
    """
    # after extracting 'values'
    dist = df.values.astype(float)

    values = dist[np.triu_indices_from(dist, k=1)]
    # remove zeros if they exist
    values = values[values > 0]

    hist, edges = np.histogram(values, bins=30)
    gap_index = np.argmax(hist == 0)  # first empty bin

    diff = np.diff(hist)
    # Look for big negative -> positive shift
    elbow = np.argmax(diff > np.mean(diff) + np.std(diff))
    threshold = edges[elbow]

    if verbose:
        print("Inflection point threshold:", threshold)

    # show histogram
    if show_plot:
        plt.hist(values, bins=30)
        plt.axvline(threshold, color='r', linestyle='--', label=f'Threshold: {threshold:.2f}')
        plt.legend()
        if savefig is not None:
            plt.savefig(savefig)
            if verbose:
                print(f"Histogram plot saved at: {savefig}")
        
        plt.show()

    return threshold


# ------------------------------
# VERTICES FILTERING METHODS
# ------------------------------

def filter_close_vertices(df, all_vertices, THRES_DIST: int = 50, verbose=False):
    """
    Suppose df is the distance dataframe between all vertices (calculated from all_vertices).
    Filter out vertices that are closer than threshold distance.
    Keep the first occurrence and remove the rest.
    """
    # Store all points with distance < THRES_DIST
    filtered_points = []
    for i in range(len(df)):
        tmp = []
        for j in range(len(df.columns)):
            if df.iat[i, j] < THRES_DIST:
                tmp.append(all_vertices[j])
        if tmp:
            filtered_points.append(tmp)
        else: 
            filtered_points.append([all_vertices[i]])

    if verbose:
        total_before = len(all_vertices)
        total_after = total_before - len(filtered_points)
        print(f"Total vertices before filtering: {total_before}")
        print(f"Total vertices after filtering: {total_after}")
    return filtered_points

def merge_close_vertices(filtered_points, verbose=False):
    """
    Merge close vertices into single vertex (average position).
    """
    data  = filtered_points

    # Convert lists to sets of tuples for merging logic
    sets = [set(map(tuple, group)) for group in data]

    merged = True
    while merged:
        merged = False
        new_sets = []
        while sets:
            first, *rest = sets
            first = set(first)
            changed = False
            
            for s in rest:
                if first & s:  # If they share any element
                    first |= s
                    rest.remove(s)
                    changed = True
            
            new_sets.append(first)
            sets = rest
            merged |= changed
        
        sets = new_sets

    # Convert back to list of lists
    result = [list(map(list, s)) for s in sets]

    # calculate mean point of each group
    final_points = []
    for group in result:
        xs = [pt[0] for pt in group]
        ys = [pt[1] for pt in group]
        mean_x = int(np.mean(xs))
        mean_y = int(np.mean(ys))
        final_points.append([mean_x, mean_y])

    return final_points