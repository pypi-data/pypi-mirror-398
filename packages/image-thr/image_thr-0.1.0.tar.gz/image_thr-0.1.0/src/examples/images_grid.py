import os
import math
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.image as mpimg
import scipy.ndimage as ndimage

# Folder containing the images
image_folder = 'all'

# Get list of image files (assuming common extensions)
image_files = [f for f in os.listdir(image_folder) if f.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.bmp'))]

# Number of images
n = len(image_files)

if n == 0:
    print("No images found in the folder.")
else:
    # Determine grid dimensions (aim for square-ish grid)
    rows = int(math.sqrt(n))
    cols = math.ceil(n / rows)

    # Calculate cell pixel sizes
    width = 1920
    height = 1080
    cell_width = width // cols
    cell_height = height // rows

    # Create figure with 1080p size (1920x1080 pixels)
    # figsize in inches, dpi=100 to get exact pixels: 19.2 in * 100 dpi = 1920 px
    fig, axs = plt.subplots(rows, cols, figsize=(19.2, 10.8))
    fig.subplots_adjust(hspace=0, wspace=0)  # Remove spacing between images

    # Flatten axs if it's multidimensional
    axs = axs.ravel() if n > 1 else [axs]

    # Set background and borders for all axes
    for ax in axs:
        ax.set_facecolor('darkgray')
        ax.set_xticks([])
        ax.set_yticks([])
        for spine in ax.spines.values():
            spine.set_visible(True)
            spine.set_color('darkgray')
            spine.set_linewidth(2)

    # Load, process, and display each image
    for i, file in enumerate(image_files):
        img_path = os.path.join(image_folder, file)
        img = mpimg.imread(img_path)
        
        # Assume RGB; skip alpha for simplicity
        if img.ndim == 2:
            img = np.stack((img,)*3, axis=-1)  # Convert grayscale to RGB
        
        img_h, img_w, _ = img.shape
        scale = max(cell_height / img_h, cell_width / img_w)
        new_h = math.ceil(img_h * scale)
        new_w = math.ceil(img_w * scale)
        
        # Resize with bicubic interpolation
        resized = ndimage.zoom(img, (scale, scale, 1), order=3)
        
        # Center crop to cell size
        crop_h = (new_h - cell_height) // 2
        crop_w = (new_w - cell_width) // 2
        cropped = resized[crop_h:crop_h + cell_height, crop_w:crop_w + cell_width, :]
        
        axs[i].imshow(cropped)

    # Hide any extra subplots (but keep borders)
    for j in range(i + 1, len(axs)):
        pass  # Already set to darkgray with borders

    # Save the grid as a 1080p image
    plt.savefig(f"{image_folder}_1080p.jpg", dpi=100, bbox_inches='tight', pad_inches=0)
    plt.close()  # Close the figure to free memory

    print("Grid image saved as 'output_1080p.jpg'")