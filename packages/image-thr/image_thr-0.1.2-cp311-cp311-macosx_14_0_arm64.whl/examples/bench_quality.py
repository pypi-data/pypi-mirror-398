import cv2
import os
import time
import csv
import pandas as pd
from image_thr import threshold_image, contours_to_objects, ContourObject

MIN_SIZE = 1
MAX_SIZE = 50
methods = ['fourier', 'otsu', 'minimum', 'mean', 'isodata', 'triangle', 'li', 'yen', 'max_entropy', 'min_error', 'moments', 'intermodes', 'percentile']

def load_image_files(image_dir):
    """Load and sort image files from the specified directory."""
    valid_extensions = (".png", ".jpg", ".jpeg", ".bmp")
    image_files = [f for f in os.listdir(image_dir) if f.lower().endswith(valid_extensions)]
    image_files.sort()  # Sort for consistent order
    return image_files

def rect_intersect(r1, r2):
    """Compute intersection area between two rectangles (x1,y1,x2,y2)."""
    x1 = max(r1[0], r2[0])
    y1 = max(r1[1], r2[1])
    x2 = min(r1[2], r2[2])
    y2 = min(r1[3], r2[3])
    if x1 < x2 and y1 < y2:
        return (x2 - x1) * (y2 - y1)
    return 0

def process_benchmark(image_path, method):
    print('----- ', image_path, method)
    # Load image with OpenCV
    original_image = cv2.imread(image_path, cv2.IMREAD_COLOR)
    if original_image is None:
        print("Failed to load image:", image_path)
        return None
    
    oh, ow = original_image.shape[:2]
    sf = min(800 / ow, 600 / oh, 1.0)
    width = int(ow * sf)
    height = int(oh * sf)
    
    # Resize image
    small_image = cv2.resize(original_image, (width, height))
    
    # Convert to grayscale
    gray_cv = cv2.cvtColor(small_image, cv2.COLOR_BGR2GRAY)
    
    start_time = time.time()
    (contour_boxes, counts, approx_counts, low, high) = threshold_image(gray_cv, user_low=None, user_high=None, method=method)
    end_time = time.time()
    processing_time = end_time - start_time
    
    # Load per-image parameters if available
    stem = os.path.splitext(os.path.basename(image_path))[0]
    anno_path = os.path.join("train", stem + ".txt")
    local_fov_x = 0.88
    local_fov_y = 0.7
    local_distance = 300
    anno_lines = []
    if os.path.exists(anno_path):
        with open(anno_path, 'r') as f:
            lines = f.readlines()
        if lines:
            first_line = lines[0].strip().split()
            if len(first_line) == 3:
                try:
                    local_fov_x = float(first_line[0])
                    local_fov_y = float(first_line[1])
                    local_distance = float(first_line[2])
                    anno_lines = lines[1:]
                except ValueError:
                    anno_lines = lines
            else:
                anno_lines = lines
    
    # Convert contours to objects
    objects = contours_to_objects(contour_boxes, (local_fov_x, local_fov_y), local_distance, gray_cv.shape, MIN_SIZE, MAX_SIZE, (0,0))
    
    # Compute detected boxes
    detected_boxes = []
    cv_height, cv_width = gray_cv.shape
    for obj in objects:
        uav: ContourObject = obj
        x = round((cv_width / 2) - (uav.width_deg * cv_width / (2 * local_fov_x)) + (uav.dx_deg * cv_width / local_fov_x))
        y = round((cv_height / 2) - (uav.height_deg * cv_height / (2 * local_fov_y)) + (uav.dy_deg * cv_height / local_fov_y))
        box_w = round((uav.width_deg * cv_width / local_fov_x))
        box_h = round((uav.height_deg * cv_height / local_fov_y))
        detected_boxes.append((x, y, x + box_w, y + box_h))
    
    # Load annotations
    annos = []
    for line in anno_lines:
        parts = line.strip().split()
        if len(parts) == 5 and parts[0] == '0':
            xc, yc, w, h = map(float, parts[1:])
            x1 = (xc - w / 2) * cv_width
            y1 = (yc - h / 2) * cv_height
            x2 = (xc + w / 2) * cv_width
            y2 = (yc + h / 2) * cv_height
            annos.append((x1, y1, x2, y2))
    
    # Compute metrics
    pairs = []
    for y_idx, yellow in enumerate(annos):
        yellow_area = (yellow[2] - yellow[0]) * (yellow[3] - yellow[1])
        if yellow_area == 0:
            continue
        for b_idx, blue in enumerate(detected_boxes):
            inter_area = rect_intersect(blue, yellow)
            if inter_area > 0:
                blue_area = (blue[2] - blue[0]) * (blue[3] - blue[1])
                union_area = blue_area + yellow_area - inter_area
                iou = inter_area / union_area if union_area > 0 else 0
                pairs.append((iou, y_idx, b_idx))
    
    pairs.sort(reverse=True)  # Highest IoU first
    
    matched_yellows = set()
    matched_blues = set()
    coverages = []
    
    for iou, y_idx, b_idx in pairs:
        if y_idx not in matched_yellows and b_idx not in matched_blues:
            matched_yellows.add(y_idx)
            matched_blues.add(b_idx)
            coverages.append(iou * 100)
    
    tp_count = len(matched_yellows)
    fn_count = len(annos) - tp_count
    fp_count = len(detected_boxes) - len(matched_blues)
    
    avg_coverage = sum(coverages) / tp_count if tp_count > 0 else 0
    
    # Percentages
    num_annos = len(annos)
    misses_pct = (fn_count / num_annos * 100) if num_annos > 0 else 0
    hits_pct = (tp_count / num_annos * 100) if num_annos > 0 else 0
    tp_ratio_pct = (tp_count / (tp_count + fp_count) * 100) if (tp_count + fp_count) > 0 else 0
    
    return {
        'TP': tp_count,
        'TP_ratio': tp_ratio_pct,
        'FP': fp_count,
        'Misses_count': fn_count,
        'Misses_pct': misses_pct,
        'Hits_pct': hits_pct,
        'Coverage_pct': avg_coverage,
        'Processing_time_s': processing_time
    }

def main():
    image_dir = "images"
    image_files = load_image_files(image_dir)
    if not image_files:
        print("No images found in the 'images' directory.")
        return
    
    results = []
    for img_file in image_files:
        image_path = os.path.join(image_dir, img_file)
        for method in methods:
            metrics = process_benchmark(image_path, method)
            if metrics:
                row = {'Image': img_file, 'Method': method, **metrics}
                results.append(row)
    
    # Save detailed benchmark to CSV
    csv_filename = 'benchmark_quality.csv'
    with open(csv_filename, 'w', newline='') as csvfile:
        fieldnames = ['Image', 'Method', 'TP', 'TP_ratio', 'FP', 'Misses_count', 'Misses_pct', 'Hits_pct', 'Coverage_pct', 'Processing_time_s']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(results)
    
    print(f"Benchmark results saved to {csv_filename}")
    
    # Compute averages per method
    df = pd.DataFrame(results)
    avg_df = df.groupby('Method').mean(numeric_only=True).reset_index()
    
    # Save averages to another CSV
    avg_csv_filename = 'benchmark_quality_averages.csv'
    avg_df.to_csv(avg_csv_filename, index=False)
    
    print(f"Average results saved to {avg_csv_filename}")

if __name__ == "__main__":
    main()