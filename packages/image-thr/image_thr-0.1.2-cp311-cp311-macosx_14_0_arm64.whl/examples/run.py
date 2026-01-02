import pygame
import sys
import numpy as np
import os
import time
import cv2
from image_thr import threshold_image, ContourObject, contours_to_objects

MIN_SIZE = 1
MAX_SIZE = 50
methods = ['fourier', 'otsu', 'minimum', 'mean', 'isodata', 'triangle', 'li', 'yen', 'max_entropy', 'min_error', 'moments', 'intermodes', 'percentile']

def load_image_files(image_dir):
    """Load and sort image files from the specified directory."""
    valid_extensions = (".png", ".jpg", ".jpeg", ".bmp")
    image_files = [f for f in os.listdir(image_dir) if f.lower().endswith(valid_extensions)]
    image_files.sort()  # Sort for consistent order
    return image_files

def get_display_size(image_path):
    """Get the display size for the image, scaled to fit within 640x480 if necessary."""
    img = pygame.image.load(image_path)
    ow, oh = img.get_size()
    sf = min(800 / ow, 600 / oh, 1.0)
    return int(ow * sf), int(oh * sf)

def rect_intersect(r1, r2):
    """Compute intersection area between two rectangles (x1,y1,x2,y2)."""
    x1 = max(r1[0], r2[0])
    y1 = max(r1[1], r2[1])
    x2 = min(r1[2], r2[2])
    y2 = min(r1[3], r2[3])
    if x1 < x2 and y1 < y2:
        return (x2 - x1) * (y2 - y1)
    return 0

def process_image(image_path, width=300, height=300, user_low=None, user_high=None, mode=0):
    print('----- ', image_path)
    """Process an image: load, scale, compute histogram, contours, and bounding boxes."""
    # Load the image
    original_image = pygame.image.load(image_path)
    
    # Scale to specified size for processing and display
    small_image = pygame.transform.scale(original_image, (width, height))
    
    # Convert to grayscale
    gray_image = pygame.transform.grayscale(small_image)

    start_time = time.time()
    gray_array = pygame.surfarray.pixels3d(gray_image)
    intensities = gray_array[:, :, 0]
    gray_cv = np.transpose(intensities, (1, 0)).astype(np.uint8)

    method = methods[mode]
    
    (contour_boxes, counts, approx_counts, low, high) = threshold_image(gray_cv, user_low=user_low, user_high=user_high, method=method)
    end_time = time.time()

    # Load per-image parameters if available
    original_name = os.path.basename(image_path)
    stem = os.path.splitext(original_name)[0]
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
    
    objects = contours_to_objects(contour_boxes, (local_fov_x, local_fov_y), local_distance, gray_cv.shape, MIN_SIZE, MAX_SIZE, (0,0))
    
    if user_low is None and user_high is None:
        mode_str = f" (auto {method})"
    elif user_low is not None and user_high is not None:
        mode_str = " (manual)"
    else:
        mode_str = " (mixed)"
    if method != 'fourier':
        ranges_text = f"Threshold: {low}{mode_str}"
    else:
        ranges_text = f"Dominant grayscale range: {low}-{high}{mode_str}"
    
    # Draw contours and bounding boxes
    contours = []
    for box in contour_boxes:
        (_,_,_,_,contour) = box
        contours.append(contour)

    output_cv = cv2.cvtColor(gray_cv, cv2.COLOR_GRAY2BGR)

    # Load and draw yellow annotation rectangles
    annos = []
    for line in anno_lines:
        parts = line.strip().split()
        if len(parts) == 5 and parts[0] == '0':
            xc, yc, w, h = map(float, parts[1:])
            x1 = (xc - w / 2) * gray_cv.shape[1]
            y1 = (yc - h / 2) * gray_cv.shape[0]
            x2 = (xc + w / 2) * gray_cv.shape[1]
            y2 = (yc + h / 2) * gray_cv.shape[0]
            annos.append((x1, y1, x2, y2))
    for a in annos:
        x1, y1, x2, y2 = map(int, a)
        cv2.rectangle(output_cv, (x1, y1), (x2, y2), (0, 255, 255), 3)

    cv2.drawContours(output_cv, contours, -1, (0, 255, 0), 2)
    for contour in contours:
        x, y, w, h = cv2.boundingRect(contour)
        cv2.rectangle(output_cv, (x, y), (x + w, y + h), (0, 0, 255), 2)

    detected_boxes = []
    for obj in objects:
        uav : ContourObject = obj
        (cv_height, cv_width) = gray_cv.shape
        x = round((cv_width/2) - (uav.width_deg*cv_width/(2*local_fov_x)) + (uav.dx_deg*cv_width/local_fov_x))
        y = round((cv_height/2) - (uav.height_deg*cv_height/(2*local_fov_y)) + (uav.dy_deg*cv_height/local_fov_y))
        box_w = round((uav.width_deg*cv_width/local_fov_x))
        box_h = round((uav.height_deg*cv_height/local_fov_y))
        print("obj",(x, y), (x + box_w, y + box_h))
        cv2.rectangle(output_cv, (x, y), (x + box_w, y + box_h), (255, 0, 0), 4)
        detected_boxes.append((x, y, x + box_w, y + box_h))
    print("res",gray_cv.shape)
    
    # === METRICS: One TP per yellow, multiple blues → only one used ===
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

    metrics_text = (
        f"TP: {tp_count}({tp_ratio_pct:.1f}%), FP: {fp_count}, Misses: {fn_count} ({misses_pct:.1f}%), "
        f"Hits: {hits_pct:.1f}%,"
        f"Avg Coverage: {avg_coverage:.1f}%"
    )
    
    # Convert to RGB and transpose for Pygame
    output_rgb = cv2.cvtColor(output_cv, cv2.COLOR_BGR2RGB)
    output_trans = np.transpose(output_rgb, (1, 0, 2))
    modified_image = pygame.surfarray.make_surface(output_trans)
    processing_time = end_time - start_time
    processing_time_us = int(processing_time * 1000000)
    processing_text = f"Processing time: {processing_time:.5f} seconds"
    print(processing_text)
    
    # Compute derivative for display
    interp_diff = np.zeros(256)
    interp_diff[:-1] = np.diff(approx_counts)

    # Save the processed image
    os.makedirs('processed', exist_ok=True)
    output_dir = os.path.join('processed', stem)
    os.makedirs(output_dir, exist_ok=True)
    num_blue = len(objects)
    filename = f"{method}_{num_blue}_{processing_time_us}us.png"
    filepath = os.path.join(output_dir, filename)
    filepath2 = os.path.join('processed', f"{method}_{stem}.png")
    pygame.image.save(modified_image, filepath)
    pygame.image.save(modified_image, filepath2)
    
    return (modified_image, gray_image, counts, approx_counts, interp_diff, 
            ranges_text, processing_text, low, high, metrics_text, local_fov_x, local_fov_y, local_distance)

def main():
    # Initialize Pygame
    pygame.init()
    
    # Directory containing images
    image_dir = "images"
    image_files = load_image_files(image_dir)
    if not image_files:
        print("No images found in the 'images' directory.")
        pygame.quit()
        sys.exit()
    
    current_image_index = 0
    current_mode = 0
    current_image_path = os.path.join(image_dir, image_files[current_image_index])
    
    # Get display size
    disp_w, disp_h = get_display_size(current_image_path)
    
    user_low = None
    user_high = None
    
    # Process the first image
    (modified_image, gray_image, counts, approx_counts, interp_diff, 
     ranges_text, processing_text, current_low, current_high, metrics_text,
     current_fov_x, current_fov_y, current_distance) = process_image(current_image_path, disp_w, disp_h, user_low, user_high, current_mode)
    
    # Create the screen
    info_height = 375
    screen = pygame.display.set_mode((disp_w, disp_h + info_height))
    pygame.display.set_caption(os.path.basename(current_image_path))
    
    # Font for text
    font = pygame.font.SysFont(None, 24)
    
    # Initial info text
    info_text = "Click on the image to get pixel info (from original). Use Left/Right arrows to switch images. Left/Right mouse on histogram to set low/high. Up/Down to switch algorithms."
    color_swatch_color = (255, 255, 255)
    
    # Histogram settings
    hist_height = 120
    pixel_per_unit = disp_w / 256.0
    amp = np.max(counts) if np.any(counts) else 1
    scale = hist_height / amp if amp > 0 else 1
    max_diff = np.max(interp_diff)
    min_diff = np.min(interp_diff)
    amp_diff = max(abs(max_diff), abs(min_diff))
    scale_diff = (hist_height / 2) / amp_diff if amp_diff > 0 else 1
    diff_zero_y = disp_h + 30 + hist_height // 2
    
    # Additional text
    modified_text = f"Displayed image has contours of dominant range drawn in green, bounding boxes in red, adjusted detections in blue, and annotations in yellow."
    formula_text1 = font.render(f"Fourier approximation using first 10 harmonics", True, (255, 255, 255))
    formula_text2 = font.render("Derivative of interpolation: forward difference approx_counts[i+1] - approx_counts[i]", True, (255, 255, 255))
    
    # Variables for key holding
    switch_direction = 0
    last_switch_time = 0
    switch_delay = 0.1
    
    def reprocess_image():
        nonlocal modified_image, gray_image, counts, approx_counts, interp_diff, ranges_text, processing_text, amp, scale, max_diff, min_diff, amp_diff, scale_diff, diff_zero_y, current_low, current_high, pixel_per_unit, metrics_text, current_fov_x, current_fov_y, current_distance
        (modified_image, gray_image, counts, approx_counts, interp_diff, 
         ranges_text, processing_text, current_low, current_high, metrics_text,
         current_fov_x, current_fov_y, current_distance) = process_image(current_image_path, disp_w, disp_h, user_low, user_high, current_mode)
        pixel_per_unit = disp_w / 256.0
        amp = np.max(counts) if np.any(counts) else 1
        scale = hist_height / amp if amp > 0 else 1
        max_diff = np.max(interp_diff)
        min_diff = np.min(interp_diff)
        amp_diff = max(abs(max_diff), abs(min_diff))
        scale_diff = (hist_height / 2) / amp_diff if amp_diff > 0 else 1
        diff_zero_y = disp_h + 30 + hist_height // 2
    
    def update_image():
        nonlocal current_image_path, disp_w, disp_h, screen, user_low, user_high
        user_low = None
        user_high = None
        current_image_path = os.path.join(image_dir, image_files[current_image_index])
        disp_w, disp_h = get_display_size(current_image_path)
        screen = pygame.display.set_mode((disp_w, disp_h + info_height))
        pygame.display.set_caption(os.path.basename(current_image_path))
        reprocess_image()
    
    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.MOUSEBUTTONDOWN:
                mouse_x, mouse_y = event.pos
                if mouse_y < disp_h:
                    color = gray_image.get_at((mouse_x, mouse_y))
                    value = color.r
                    hex_code = f"#{value:02x}{value:02x}{value:02x}"
                    info_text = f"Pixel at ({mouse_x}, {mouse_y}): Grayscale Value {value}, Hex {hex_code}"
                    color_swatch_color = (value, value, value)
                elif disp_h + 30 <= mouse_y <= disp_h + 30 + hist_height:
                    idx = max(0, min(255, int(mouse_x / pixel_per_unit)))
                    if event.button == 1:  # Left mouse button
                        user_low = idx
                        reprocess_image()
                    elif event.button == 3:  # Right mouse button
                        user_high = idx
                        reprocess_image()
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_RIGHT:
                    switch_direction = 1
                    current_image_index = (current_image_index + 1) % len(image_files)
                    update_image()
                    last_switch_time = time.time()
                elif event.key == pygame.K_LEFT:
                    switch_direction = -1
                    current_image_index = (current_image_index - 1) % len(image_files)
                    update_image()
                    last_switch_time = time.time()
                elif event.key == pygame.K_UP:
                    current_mode = (current_mode + 1) % len(methods)
                    reprocess_image()
                elif event.key == pygame.K_DOWN:
                    current_mode = (current_mode - 1) % len(methods)
                    reprocess_image()
            elif event.type == pygame.KEYUP:
                if event.key == pygame.K_RIGHT and switch_direction == 1:
                    switch_direction = 0
                elif event.key == pygame.K_LEFT and switch_direction == -1:
                    switch_direction = 0
        
        if switch_direction != 0:
            current_time = time.time()
            if current_time - last_switch_time >= switch_delay:
                user_low = None
                user_high = None
                current_image_index = (current_image_index + switch_direction) % len(image_files)
                update_image()
                last_switch_time = current_time
    
        # Clear screen
        screen.fill((0, 0, 0))
        
        # Draw the modified image
        screen.blit(modified_image, (0, 0))
        
        # Draw histogram title
        # hist_title = font.render("Histogram of Grayscale Values (0-255) from Original with Fourier approx (green), its derivative (blue), zero (red)", True, (255, 255, 255))
        # screen.blit(hist_title, (10, disp_h + 5))
        
        # Draw histogram bars
        for i in range(256):
            bar_height = counts[i] * scale
            bar_x = i * pixel_per_unit
            bar_w = pixel_per_unit
            bar_y = disp_h + 30 + (hist_height - bar_height)
            pygame.draw.rect(screen, (255, 255, 255), (bar_x, bar_y, max(1, bar_w), bar_height))
        
        # Draw Fourier approximation curve
        points = []
        for i in range(256):
            approx_freq = max(0, approx_counts[i])
            curve_height = approx_freq * scale
            curve_y = disp_h + 30 + (hist_height - curve_height)
            curve_x = i * pixel_per_unit + bar_w / 2
            points.append((curve_x, curve_y))
        pygame.draw.lines(screen, (0, 255, 0), False, points, 4)
        
        # Draw derivative zero line
        # pygame.draw.line(screen, (255, 0, 0), (0, diff_zero_y), (disp_w, diff_zero_y), 1)
        
        # Draw interpolation derivative curve
        # diff_points = []
        # for i in range(256):
        #     deriv = interp_diff[i]
        #     curve_height = deriv * scale_diff
        #     curve_y = diff_zero_y - curve_height
        #     curve_x = i * pixel_per_unit + bar_w / 2
        #     diff_points.append((curve_x, curve_y))
        # pygame.draw.lines(screen, (0, 0, 255), False, diff_points, 2)
        
        # Draw threshold lines
        low_x = current_low * pixel_per_unit
        pygame.draw.line(screen, (255, 0, 255), (low_x, disp_h + 30), (low_x, disp_h + 30 + hist_height), 2)
        high_x = current_high * pixel_per_unit
        pygame.draw.line(screen, (255, 0, 255), (high_x, disp_h + 30), (high_x, disp_h + 30 + hist_height), 2)
        
        # Draw x-axis labels
        label0 = font.render("0", True, (255, 255, 255))
        screen.blit(label0, (0, disp_h + 30 + hist_height + 5))
        
        label128 = font.render("128", True, (255, 255, 255))
        screen.blit(label128, (128 * pixel_per_unit - 10, disp_h + 30 + hist_height + 5))
        
        label255 = font.render("255", True, (255, 255, 255))
        screen.blit(label255, (255 * pixel_per_unit - 10, disp_h + 30 + hist_height + 5))
        
        # Draw the info text
        text_surface = font.render(info_text, True, (255, 255, 255))
        screen.blit(text_surface, (10, disp_h + 30 + hist_height + 25))
        
        # Draw dominant ranges text
        ranges_surface = font.render(ranges_text, True, (255, 255, 255))
        screen.blit(ranges_surface, (10, disp_h + 30 + hist_height + 50))
        
        # Draw modified text
        modified_surface = font.render(modified_text, True, (255, 255, 255))
        screen.blit(modified_surface, (10, disp_h + 30 + hist_height + 75))
        
        # Draw Fourier formula
        screen.blit(formula_text1, (10, disp_h + 30 + hist_height + 100))
        
        # Draw interpolation derivative formula
        screen.blit(formula_text2, (10, disp_h + 30 + hist_height + 125))
        
        # Draw processing time
        processing_surface = font.render(processing_text, True, (255, 255, 255))
        screen.blit(processing_surface, (10, disp_h + 30 + hist_height + 150))
        
        # Draw metrics
        metrics_surface = font.render(metrics_text, True, (255, 255, 255))
        screen.blit(metrics_surface, (10, disp_h  + 30 + hist_height + 175))
        
        # Draw parameters
        params_text = f"FOV_X: {current_fov_x}, FOV_Y: {current_fov_y}, DISTANCE: {current_distance}"
        params_surface = font.render(params_text, True, (255, 255, 255))
        screen.blit(params_surface, (10, disp_h + 30 + hist_height + 200))
        
        # Draw color swatch
        swatch_rect = pygame.Rect(disp_w - 120, disp_h + 30 + hist_height + 30, 100, 50)
        pygame.draw.rect(screen, color_swatch_color, swatch_rect)
        
        # Update display
        pygame.display.flip()
    
    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()