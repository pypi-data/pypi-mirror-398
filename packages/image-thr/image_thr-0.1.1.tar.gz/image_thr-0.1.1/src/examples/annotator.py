import pygame
import os
import sys

# ----------------------------------------------------------------------
# Initialise Pygame
# ----------------------------------------------------------------------
pygame.init()
pygame.font.init()
font = pygame.font.SysFont("Arial", 28)          # for filename display

screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
screen_w, screen_h = screen.get_width(), screen.get_height()

# ----------------------------------------------------------------------
# Folders & image list
# ----------------------------------------------------------------------
IMAGE_FOLDER = "images"
TRAIN_FOLDER = "train"
os.makedirs(TRAIN_FOLDER, exist_ok=True)

images = sorted(
    [f for f in os.listdir(IMAGE_FOLDER)
     if f.lower().endswith(('.png', '.jpg', '.jpeg', '.bmp'))]
)
if not images:
    print("No images found in 'images' folder.")
    sys.exit()

current_idx = 0

# ----------------------------------------------------------------------
# Helper: load image + existing annotations
# ----------------------------------------------------------------------
def load_image_and_annotations():
    global orig_surf, scaled_surf, orig_w, orig_h
    global scale_x, scale_y, rects, current_filename

    img_name = images[current_idx]
    current_filename = os.path.splitext(img_name)[0]

    path = os.path.join(IMAGE_FOLDER, img_name)
    orig_surf = pygame.image.load(path).convert()
    orig_w, orig_h = orig_surf.get_size()

    # scale to full screen while preserving aspect ratio
    img_ratio = orig_w / orig_h
    scr_ratio = screen_w / screen_h
    if img_ratio > scr_ratio:                     # fit width
        new_w = screen_w
        new_h = int(screen_w / img_ratio)
    else:                                         # fit height
        new_h = screen_h
        new_w = int(screen_h * img_ratio)

    scaled_surf = pygame.transform.smoothscale(orig_surf, (new_w, new_h))
    # centre the image
    offset_x = (screen_w - new_w) // 2
    offset_y = (screen_h - new_h) // 2

    scale_x = orig_w / new_w
    scale_y = orig_h / new_h

    rects = load_annotations(current_filename)

    return scaled_surf, (offset_x, offset_y), (new_w, new_h)


def load_annotations(fname):
    """Return list of (ox1, oy1, ox2, oy2) in *original* pixel coordinates."""
    txt_path = os.path.join(TRAIN_FOLDER, fname + ".txt")
    if not os.path.exists(txt_path):
        return []

    rects = []
    with open(txt_path, "r") as f:
        lines = f.readlines()
        start = 0
        if lines:
            first_line = lines[0].strip().split()
            if len(first_line) == 3:
                try:
                    map(float, first_line)
                    start = 1
                except ValueError:
                    pass
        for line in lines[start:]:
            parts = line.strip().split()
            if len(parts) != 5 or parts[0] != "0":
                continue
            xc, yc, w, h = map(float, parts[1:])
            # YOLO → absolute pixels
            ox = (xc - w / 2) * orig_w
            oy = (yc - h / 2) * orig_h
            ow = w * orig_w
            oh = h * orig_h
            rects.append((ox, oy, ox + ow, oy + oh))
    return rects


def save_annotations(fname, rect_list):
    """Write YOLO‑format txt file."""
    txt_path = os.path.join(TRAIN_FOLDER, fname + ".txt")
    with open(txt_path, "w") as f:
        f.write("0.88 0.7 500\n")
        for ox1, oy1, ox2, oy2 in rect_list:
            w = (ox2 - ox1) / orig_w
            h = (oy2 - oy1) / orig_h
            xc = ((ox1 + ox2) / 2) / orig_w
            yc = ((oy1 + oy2) / 2) / orig_h
            f.write(f"0 {xc:.6f} {yc:.6f} {w:.6f} {h:.6f}\n")


# ----------------------------------------------------------------------
# Initial load
# ----------------------------------------------------------------------
scaled_surf, img_offset, img_size = load_image_and_annotations()
drawing = False
start_pos = None               # original coordinates while dragging
clock = pygame.time.Clock()

# ----------------------------------------------------------------------
# Main loop
# ----------------------------------------------------------------------
running = True
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            save_annotations(current_filename, rects)
            running = False

        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                save_annotations(current_filename, rects)
                running = False

            elif event.key == pygame.K_LEFT:
                save_annotations(current_filename, rects)
                current_idx = (current_idx - 1) % len(images)
                scaled_surf, img_offset, img_size = load_image_and_annotations()

            elif event.key == pygame.K_RIGHT:
                save_annotations(current_filename, rects)
                current_idx = (current_idx + 1) % len(images)
                scaled_surf, img_offset, img_size = load_image_and_annotations()

        elif event.type == pygame.MOUSEBUTTONDOWN:
            mx, my = pygame.mouse.get_pos()
            # translate mouse to *original* image coordinates
            ix = mx - img_offset[0]
            iy = my - img_offset[1]
            if not (0 <= ix < img_size[0] and 0 <= iy < img_size[1]):
                continue                     # click outside the image → ignore
            orig_mx = ix * scale_x
            orig_my = iy * scale_y

            if event.button == 1:            # LMB → start drawing
                drawing = True
                start_pos = (orig_mx, orig_my)

            elif event.button == 3:          # RMB → remove rectangle
                for i in range(len(rects) - 1, -1, -1):
                    r = rects[i]
                    if r[0] <= orig_mx <= r[2] and r[1] <= orig_my <= r[3]:
                        del rects[i]
                        break

        elif event.type == pygame.MOUSEBUTTONUP and event.button == 1 and drawing:
            mx, my = pygame.mouse.get_pos()
            ix = mx - img_offset[0]
            iy = my - img_offset[1]
            if 0 <= ix < img_size[0] and 0 <= iy < img_size[1]:
                end_x = ix * scale_x
                end_y = iy * scale_y
                ox1 = min(start_pos[0], end_x)
                oy1 = min(start_pos[1], end_y)
                ox2 = max(start_pos[0], end_x)
                oy2 = max(start_pos[1], end_y)
                if abs(ox2 - ox1) > 1 and abs(oy2 - oy1) > 1:   # avoid zero‑size
                    rects.append((ox1, oy1, ox2, oy2))
            drawing = False

    # ------------------------------------------------------------------
    # Rendering
    # ------------------------------------------------------------------
    screen.fill((30, 30, 30))                     # dark background
    screen.blit(scaled_surf, img_offset)

    # --- draw saved rectangles (red) ---------------------------------
    for ox1, oy1, ox2, oy2 in rects:
        sx1 = img_offset[0] + ox1 / scale_x
        sy1 = img_offset[1] + oy1 / scale_y
        sw  = (ox2 - ox1) / scale_x
        sh  = (oy2 - oy1) / scale_y
        pygame.draw.rect(screen, (255, 0, 0), (sx1, sy1, sw, sh), 2)

    # --- draw temporary rectangle while dragging (green) -------------
    if drawing:
        mx, my = pygame.mouse.get_pos()
        ix = mx - img_offset[0]
        iy = my - img_offset[1]
        if 0 <= ix < img_size[0] and 0 <= iy < img_size[1]:
            cur_x = ix * scale_x
            cur_y = iy * scale_y
            min_x = min(start_pos[0], cur_x) / scale_x + img_offset[0]
            min_y = min(start_pos[1], cur_y) / scale_y + img_offset[1]
            w = abs(start_pos[0] - cur_x) / scale_x
            h = abs(start_pos[1] - cur_y) / scale_y
            pygame.draw.rect(screen, (0, 255, 0), (min_x, min_y, w, h), 2)

    # --- filename in top‑left ----------------------------------------
    txt = f"{images[current_idx]}  ({current_idx + 1}/{len(images)})"
    txt_surf = font.render(txt, True, (255, 255, 255))
    screen.blit(txt_surf, (10, 10))

    pygame.display.flip()
    clock.tick(60)

# ----------------------------------------------------------------------
# Clean exit
# ----------------------------------------------------------------------
save_annotations(current_filename, rects)
pygame.quit()
sys.exit()