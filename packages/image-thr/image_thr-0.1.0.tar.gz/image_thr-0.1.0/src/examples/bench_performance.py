#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
benchmark_detection.py

Measures processing time of the three drone-detection algorithms
(fourier, otsu, minimum) on different image resolutions.

Place this file next to the original project (it imports the same
detector_utils and app_types modules).

Run:
    python benchmark_detection.py
"""

import os
import time
import numpy as np
import cv2
import pandas as pd
from typing import List, Tuple

# ----------------------------------------------------------------------
# 1. Import the detection function (exactly the same as in the GUI)
# ----------------------------------------------------------------------
from detector_utils import detect_contrast_v2, contoursToObjects
from app_types import UAV

# ----------------------------------------------------------------------
# 2. Configuration
# ----------------------------------------------------------------------
IMAGE_DIR = "images"                     # folder with test images
OUTPUT_CSV = "benchmark_perf.csv"    # set to None to skip CSV export

# Resolutions to test (width, height).  Feel free to extend.
RESOLUTIONS = [
    (160, 120),
    (320, 240),
    (640, 480),
    (800, 600),
    (1024, 768),
    (1280, 1024),
    (1600, 1200),
    (2560, 1440),
    (3840, 2160),
]

# How many repetitions per (image, resolution, method) pair
WARMUP_ROUNDS = 3      # discard – let the JIT / cache warm up
MEASURE_ROUNDS = 5    # actual measured runs
REPEAT_EXPERIMENTS = 3  # how many independent experiments (mean±std)

# ----------------------------------------------------------------------
# 3. Helper utilities
# ----------------------------------------------------------------------
def load_image_paths() -> List[str]:
    """Return sorted list of image files in IMAGE_DIR."""
    exts = {".png", ".jpg", ".jpeg", ".bmp", ".tiff"}
    files = [
        os.path.join(IMAGE_DIR, f)
        for f in os.listdir(IMAGE_DIR)
        if os.path.splitext(f.lower())[1] in exts
    ]
    files.sort()
    if not files:
        raise RuntimeError(f"No images found in {IMAGE_DIR}")
    return files


def resize_frame_cv2(path: str, size: Tuple[int, int]) -> np.ndarray:
    """Load with OpenCV (fast) and resize to exact size."""
    img = cv2.imread(path, cv2.IMREAD_GRAYSCALE)
    if img is None:
        raise RuntimeError(f"Failed to load {path}")
    return cv2.resize(img, size, interpolation=cv2.INTER_AREA)


def run_detection(frame: np.ndarray, method: str):
    """
    Run ONLY the detection part (detect_contrast_v2) – the part that
    dominates the runtime.  The clustering step is *not* timed because
    it is identical for all three methods.
    """
    # user_low / user_high = None → auto mode
    contour_boxes, counts, approx_counts, low, high = detect_contrast_v2(
        frame, user_low=None, user_high=None, method=method
    )
    # Return something so the call is not optimised away
    return len(contour_boxes)


# ----------------------------------------------------------------------
# 4. Benchmark core
# ----------------------------------------------------------------------
def benchmark_one_image(image_path: str):
    results = []

    for w, h in RESOLUTIONS:
        frame = resize_frame_cv2(image_path, (w, h))

        for method in ['fourier', 'otsu', 'minimum', 'mean', 'isodata', 'triangle', 'li', 'yen', 'max_entropy', 'min_error', 'moments', 'intermodes', 'percentile']:
            # ---- warm-up -------------------------------------------------
            for _ in range(WARMUP_ROUNDS):
                run_detection(frame, method)

            # ---- measurement ---------------------------------------------
            timings = []
            for _ in range(REPEAT_EXPERIMENTS):
                start = time.perf_counter()
                for _ in range(MEASURE_ROUNDS):
                    run_detection(frame, method)
                end = time.perf_counter()
                timings.append((end - start) / MEASURE_ROUNDS * 1e6)  # µs

            mean_us = np.mean(timings)
            std_us  = np.std(timings)

            results.append({
                "image": os.path.basename(image_path),
                "width": w,
                "height": h,
                "method": method,
                "mean_us": mean_us,
                "std_us": std_us,
                "total_pixels": w * h,
            })

    return results


def main():
    image_paths = load_image_paths()
    print(f"Found {len(image_paths)} image(s) in '{IMAGE_DIR}'")
    print(f"Testing resolutions: {RESOLUTIONS}")
    print(f"Rounds per measurement: warm-up {WARMUP_ROUNDS}, "
          f"measure {MEASURE_ROUNDS}, repeats {REPEAT_EXPERIMENTS}\n")

    all_results = []
    for idx, path in enumerate(image_paths, 1):
        print(f"[{idx}/{len(image_paths)}] Benchmarking {os.path.basename(path)} ...")
        all_results.extend(benchmark_one_image(path))

    # ------------------------------------------------------------------
    # 5. Pretty table + CSV export
    # ------------------------------------------------------------------
    df = pd.DataFrame(all_results)

    # Pivot for a readable table (method × resolution)
    table = df.pivot_table(
        index=["width", "height", "total_pixels"],
        columns="method",
        values=["mean_us", "std_us"],
        aggfunc="first",
    )
    table = table.swaplevel(axis=1).sort_index(axis=1)
    pd.set_option('display.float_format', '{:.3f}'.format)
    print("\n=== BENCHMARK RESULTS (mean ± std  [µs]) ===")
    print(table)

    if OUTPUT_CSV:
        df.to_csv(OUTPUT_CSV, index=False)
        print(f"\nDetailed CSV written to {OUTPUT_CSV}")

    # ------------------------------------------------------------------
    # 6. Quick summary (average over all images)
    # ------------------------------------------------------------------
    summary = df.groupby(["width", "height", "method"]).agg(
        mean_us=("mean_us", "mean"),
        std_us=("std_us", "mean")
    ).reset_index()
    summary_pivot = summary.pivot(index=["width", "height"], columns="method",
                                  values=["mean_us", "std_us"]).round(3)
    print("\n=== AVERAGE OVER ALL IMAGES ===")
    print(summary_pivot)

    if OUTPUT_CSV:
        average_csv = os.path.splitext(OUTPUT_CSV)[0] + "_average.csv"
        summary_pivot.to_csv(average_csv)
        print(f"\nAverage CSV written to {average_csv}")


if __name__ == "__main__":
    main()