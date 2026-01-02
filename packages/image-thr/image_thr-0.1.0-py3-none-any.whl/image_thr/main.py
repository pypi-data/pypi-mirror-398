import math
from numpy.fft import rfft, irfft
from scipy.spatial.distance import pdist, squareform
import cv2
import numpy as np
from skimage.filters import threshold_otsu, threshold_minimum, threshold_mean, threshold_isodata, threshold_li, threshold_triangle, threshold_yen
import time

class ContourObject:
    def __init__(self, dx_deg: float, dy_deg: float, 
                 width_deg: float, height_deg: float):
        self.id = id
        self.last_updated = time.time()
        self.dx_deg = dx_deg
        self.dy_deg = dy_deg
        self.width_deg = width_deg
        self.height_deg = height_deg
    
class ContourParams:
    def __init__(self, size_cm, center_x, center_y, w, h, dx_deg, dy_deg,  w_deg, h_deg):
        self.size_cm = size_cm
        self.center_x = center_x
        self.center_y = center_y
        self.w = w
        self.h = h
        self.dx_deg = dx_deg
        self.dy_deg = dy_deg
        self.w_deg = w_deg
        self.h_deg = h_deg

def pts_to_deg(pts, deg_range):
    return pts*deg_range

def deg_to_cm(angle_degrees, distance_meters):
    angle_rad = math.radians(angle_degrees)
    
    # Using tangent:
    # tan(angle/2) = (size/2) / distance
    # size = 2 * distance * tan(angle/2)
    
    size_meters = 2 * distance_meters * math.tan(angle_rad / 2)
    
    # Convert to centimeters
    size_cm = size_meters * 100
    
    return size_cm

def find_left_right_from_peak(arr):
    if len(arr) < 1:
        return []
    
    main_idx = np.argmax(arr)
    old_max = arr[main_idx]
    left_max1 = main_idx
    right_max1 = main_idx

    while left_max1>0 and arr[left_max1]>10:
        left_max1 = left_max1-1

    # Find two more peaks on the left before index 128
    MIN_RANGE = 128
    for i in range(2):

        #find the next peak index on the left
        if left_max1>MIN_RANGE:
            max_idx = left_max1
            max_val = arr[left_max1]
            new_left = left_max1
            while new_left>MIN_RANGE:
                if arr[new_left] > max_val:
                    max_val = arr[new_left]
                    max_idx = new_left
                new_left = new_left-1
            if new_left>=MIN_RANGE and max_val/old_max > 0.1:
                left_max1 = new_left
                old_max = max_val
            else:
                break

        #Find left border of the peak
        while left_max1>0 and arr[left_max1]>old_max*0.1:
            left_max1 = left_max1-1

    # Find right border
    while right_max1<len(arr) and arr[right_max1]>20:
        right_max1 = right_max1+1

    return (int(left_max1), int(right_max1))

def get_max_entropy_threshold(counts):
    cdf = counts.cumsum().astype(float)
    valid_idx = np.nonzero(counts)[0]
    first_bin = valid_idx[0]
    last_bin = valid_idx[-1]
    max_ent, threshold = 0, 0
    for it in range(first_bin, last_bin + 1):
        hist_range = counts[:it + 1]
        hist_range = hist_range[hist_range != 0] / cdf[it]
        tot_ent = -np.sum(hist_range * np.log(hist_range))
        hist_range = counts[it + 1:]
        hist_range = hist_range[hist_range != 0] / (cdf[last_bin] - cdf[it])
        tot_ent -= np.sum(hist_range * np.log(hist_range))
        if tot_ent > max_ent:
            max_ent, threshold = tot_ent, it
    return threshold

def get_min_error_threshold(counts, scaled_roi):
    total = np.sum(counts)
    l = np.arange(256)
    cdf = np.cumsum(counts)
    cdv = np.cumsum(counts * l)
    cdv2 = np.cumsum(counts * l**2)
    # Initial guess
    low = int(threshold_mean(scaled_roi))
    for _ in range(20):
        if cdf[low] == 0 or cdf[low] == total:
            break
        P1 = cdf[low] / total
        P2 = 1 - P1
        mu1 = cdv[low] / cdf[low]
        mu2 = (cdv[-1] - cdv[low]) / (total - cdf[low])
        sigma1_sq = (cdv2[low] / cdf[low]) - mu1**2
        sigma2_sq = (cdv2[-1] - cdv2[low]) / (total - cdf[low]) - mu2**2
        if sigma1_sq <= 0 or sigma2_sq <= 0:
            break
        sigma1 = np.sqrt(sigma1_sq)
        sigma2 = np.sqrt(sigma2_sq)
        A = 1 / (2 * sigma1_sq) - 1 / (2 * sigma2_sq)
        B = mu2 / sigma2_sq - mu1 / sigma1_sq
        C = (mu1**2 / (2 * sigma1_sq) - mu2**2 / (2 * sigma2_sq)) - np.log(sigma1 / sigma2) + np.log(P1 / P2)
        disc = B**2 - 4 * A * C
        if disc < 0:
            break
        sqrt_disc = np.sqrt(disc)
        t1 = (-B + sqrt_disc) / (2 * A)
        t2 = (-B - sqrt_disc) / (2 * A)
        t = t1 if (min(mu1, mu2) < t1 < max(mu1, mu2)) else t2
        if not (min(mu1, mu2) < t < max(mu1, mu2)):
            break
        new_low = int(t + 0.5)
        if new_low == low:
            break
        low = new_low
    return low

def get_moments_threshold(counts):
    total = np.sum(counts)
    l = np.arange(256)
    p = counts / total
    m0 = 1.0
    m1 = np.sum(p * l)
    m2 = np.sum(p * l**2)
    m3 = np.sum(p * l**3)
    cd = m0 * m2 - m1**2
    c0 = (-m2 * m2 + m3 * m1) / cd
    c1 = (m0 * -m3 + m1 * -m2) / cd
    discriminant = c1**2 - 4 * c0
    if discriminant < 0:
        return 128
    sqrt_d = np.sqrt(discriminant)
    z0 = 0.5 * (-c1 - sqrt_d)
    z1 = 0.5 * (-c1 + sqrt_d)
    p0 = (z1 - m1) / (z1 - z0)
    cdf = np.cumsum(p)
    low = np.argmin(np.abs(cdf - p0))
    return low

def get_intermodes_threshold(counts):
    h = counts.copy().astype(float)
    while True:
        maxima = []
        for i in range(1, 255):
            if h[i-1] < h[i] and h[i] > h[i+1]:
                maxima.append(i)
        if len(maxima) <= 2:
            break
        new_h = h.copy()
        for i in range(1, 255):
            new_h[i] = (h[i-1] + h[i] + h[i+1]) / 3
        h = new_h
    if len(maxima) < 2:
        return 128
    j = maxima[0]
    k = maxima[1]
    low = (j + k) // 2
    return low

def get_percentile_threshold(counts, p=0.5):
    total = np.sum(counts)
    cdf = np.cumsum(counts) / total
    low = np.argmin(np.abs(cdf - p))
    return low

def threshold_image(frame, position=(0,0), user_low=None, user_high=None, low_add=-5, method='fourier'):
    # scale the image to optimize the histogram calculation
    wid, hei = frame.shape
    max_side = max(wid, hei)
    scale_factor = 1 if max_side <= 300 else round(max_side/300)
    scaled_roi = frame[::scale_factor, ::scale_factor]
    counts = [i for i in range(256)]
    approx_counts = counts

    if method == 'fourier':

        counts = np.bincount(scaled_roi.flatten(), minlength=256)
        counts[255] = counts[255] * 0.05 #Remove the major white if the scene is overexposed

        # Compute Fourier approximation with multiple harmonics
        num_harmonics = 10
        freq = rfft(counts)
        freq[num_harmonics + 1:] = 0
        approx_counts = irfft(freq)
    
        (low, high) = find_left_right_from_peak(approx_counts)
        low = low+low_add
    elif method == 'otsu':
        low = threshold_otsu(frame)
        high = low
        approx_counts = counts
    elif method == 'minimum':
        try:
            low = threshold_minimum(frame)
        except RuntimeError as e:
            # Fallback: use mean or Otsu if minimum fails
            print(f"[WARNING] threshold_minimum failed: {e} ")
            low = 120  # or threshold_otsu(frame)
        high = low
        approx_counts = counts
    elif method == 'mean':
        low = threshold_mean(frame)
        high = low
        approx_counts = counts
    elif method == 'isodata':
        low = threshold_isodata(frame)
        high = low
        approx_counts = counts
    elif method == 'triangle':
        low = threshold_triangle(frame)
        high = low
        approx_counts = counts
    elif method == 'li':
        low = threshold_li(frame)
        high = low
        approx_counts = counts
    elif method == 'yen':
        low = threshold_yen(frame)
        high = low
        approx_counts = counts
    elif method == 'max_entropy':
        counts = np.bincount(scaled_roi.flatten(), minlength=256)
        low = get_max_entropy_threshold(counts)
        high = low
        approx_counts = counts
    elif method == 'min_error':
        low = get_min_error_threshold(counts, frame)
        high = low
        approx_counts = counts
    elif method == 'moments':
        counts = np.bincount(scaled_roi.flatten(), minlength=256)
        low = get_moments_threshold(counts)
        high = low
        approx_counts = counts
    elif method == 'intermodes':
        counts = np.bincount(scaled_roi.flatten(), minlength=256)
        low = get_intermodes_threshold(counts)
        high = low
        approx_counts = counts
    elif method == 'percentile':
        counts = np.bincount(scaled_roi.flatten(), minlength=256)
        low = get_percentile_threshold(counts)
        high = low
        approx_counts = counts
    else:
        raise ValueError("Unknown method")

    low = int(low)
    high = int(high)

    if user_low is not None:
        low = user_low
    if user_high is not None:
        high = user_high

    binary = cv2.inRange(frame, 0, low)
    contours, _ = cv2.findContours(binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    contour_boxes = []
    for contour in contours:
        x, y, w, h = cv2.boundingRect(contour)
        (offset_x, offset_y) = position
        contour_boxes.append([offset_x+x, offset_y+y, w, h, contour])
    return contour_boxes, counts, approx_counts, low, high

def getContourParams(contour_box, distance, cam_angle, frame_shape, roi_offset) -> ContourParams:
    (offset_x, offset_y) = roi_offset
    (cam_angle_x, cam_angle_y) = cam_angle
    height, width = frame_shape
    x, y, w, h = contour_box

    (center_x, center_y) = (x+w/2, y+h/2)

    center_x = center_x + offset_x
    center_y = center_y + offset_y

    w_deg = pts_to_deg(w/width, cam_angle_x)
    h_deg = pts_to_deg(h/height, cam_angle_y)
    wid_cm = deg_to_cm(w_deg, distance)
    hei_cm = deg_to_cm(h_deg, distance)
    size_cm = max(wid_cm, hei_cm)
    dx_deg = pts_to_deg((center_x - (width/2))/width, cam_angle_x)
    dy_deg = pts_to_deg((center_y - (height/2))/height, cam_angle_y)
    return ContourParams(size_cm, center_x, center_y, w, h, dx_deg, dy_deg,  w_deg, h_deg)

def contours_to_objects(contour_boxes, cam_angle, distance: float, frame_shape, min_obj_size, max_obj_size, roi_offset, ignore_size_and_clustering: bool = False):
    """
    Clusters nearby contours into single objects based on proximity and size constraints.
    
    Args:
        contours: List of contours from CV2
        cam_angle: Tuple of camera angles (cam_angle_x, cam_angle_y)
        distance: Distance to the object plane
        shape: Image shape (height, width)
    
    Returns:
        Tuple of (clustered_objects, clustered_contours)
    """
    (cam_angle_x, cam_angle_y) = cam_angle
    height, width = frame_shape
    
    # First filter contours by size constraints
    filtered_contour_boxes = []
    contour_centers = []
    
    unfiltered_uavs = []
    if contour_boxes is None: contour_boxes = []
    for contour_box in contour_boxes:
        (x, y, w, h, _) = contour_box
        box = (x, y, w, h)
        params = getContourParams(box, distance, cam_angle, frame_shape, roi_offset)
        
        if ignore_size_and_clustering==True:
            unfiltered_uavs.append(ContourObject(params.dx_deg, params.dy_deg, params.w_deg, params.h_deg))
        elif params.size_cm >= min_obj_size and params.size_cm <= max_obj_size:
            filtered_contour_boxes.append(box)
            contour_centers.append((params.center_x, params.center_y))
    
    if ignore_size_and_clustering==True:
        return unfiltered_uavs

    # If no contours meet the criteria, return empty lists
    if not filtered_contour_boxes:
        return []
    
    # Compute distance matrix between contour centers in image space
    centers_array = np.array(contour_centers)
    dist_matrix = squareform(pdist(centers_array))
    
    # Convert distance threshold to pixels - MAX_OBJECT_SIZE_CM/2
    # Assuming we know the relationship between cm and pixels at the given distance
    # This is an approximation and may need adjustment
    max_distance_px = max_obj_size * (width / deg_to_cm(cam_angle_x, distance)) / 2
 
    # Initialize clusters
    clusters = []
    visited = set()
    
    # Create clusters using a connected components approach
    for i in range(len(filtered_contour_boxes)):
        if i in visited:
            continue
        
        cluster = [i]
        visited.add(i)
        stack = [i]
        
        while stack:
            current = stack.pop()
            for j in range(len(filtered_contour_boxes)):
                if j not in visited:
                    if dist_matrix[current, j] <= max_distance_px:
                        cluster.append(j)
                        visited.add(j)
                        stack.append(j)
        
        clusters.append(cluster)
    
    # Create objects from clusters
    clustered_objects = []
    
    for cluster in clusters:
        # Combine contours in the cluster
        boxes = np.array([filtered_contour_boxes[i] for i in cluster])
        min_x = boxes[:, 0].min()
        min_y = boxes[:, 1].min()
        max_x = (boxes[:, 0] + boxes[:, 2]).max()
        max_y = (boxes[:, 1] + boxes[:, 3]).max()
        width = max_x - min_x
        height = max_y - min_y
        encapsulating_box = (min_x, min_y, width, height)
        
        # Calculate bounding box for the combined contour
        params = getContourParams(encapsulating_box, distance, cam_angle, frame_shape, roi_offset)
        
        # Create an object from the cluster
        if params.size_cm >= min_obj_size and params.size_cm <= max_obj_size:
            clustered_objects.append(ContourObject(params.dx_deg, params.dy_deg, params.w_deg, params.h_deg))
    
    return clustered_objects