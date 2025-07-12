#!/usr/bin/env python3
"""
benchmark_models_fps.py

For each model in MODEL_LIST:
  1. Downloads its IR via the OMZ downloader.py
  2. Measures throughput: executes N inferences back-to-back and computes FPS = N / total_time
  3. Prints a sorted Top‐10 list by highest FPS (best throughput)
"""

import subprocess, os, time, glob
import numpy as np
from openvino import Core

# Only Intel-preconverted IR models
MODEL_LIST = [
    "person-detection-retail-0002",
    "face-detection-adas-0001",
    "age-gender-recognition-retail-0013",
    "head-pose-estimation-adas-0001",
    "facial-landmarks-35-adas-0002",
    "emotion-recognition-retail-0003",
    "vehicle-detection-adas-0002",
    "license-plate-recognition-barrier-0001",
    "pedestrian-detection-adas-0002",
    "semantic-segmentation-adas-0001",
    "human-pose-estimation-0001"
]

DEVICE = "CPU"         
OUT_DIR = "models"
OMZ_DIR = "open_model_zoo"

os.makedirs(OUT_DIR, exist_ok=True)

# Auto-locate downloader.py
downloader_paths = glob.glob(os.path.join(OMZ_DIR, "**", "downloader.py"), recursive=True)
if not downloader_paths:
    raise FileNotFoundError(f"downloader.py not found under {OMZ_DIR}")
DOWNLOADER = downloader_paths[0]

def download_ir(name):
    print(f"\n>> Downloading IR for {name}")
    subprocess.run([
        "python3", DOWNLOADER,
        "--name", name,
        "--precisions", "FP32",
        "--output_dir", OUT_DIR
    ], check=True)

def find_ir(name):
    xmls = glob.glob(os.path.join(OUT_DIR, "**", name, "FP32", "*.xml"), recursive=True)
    if not xmls:
        raise FileNotFoundError(f"No IR found for {name}")
    return xmls[0]

def measure_fps(ir_path, runs=20):
    core = Core()
    model = core.read_model(model=ir_path)
    exec_net = core.compile_model(model, DEVICE)
    inp = exec_net.input(0)
    dummy = np.random.randn(*inp.shape).astype(np.float32)

    # warm-up
    for _ in range(runs):
        exec_net(dummy)

    # timed
    start = time.time()
    for _ in range(runs):
        exec_net(dummy)
    total = time.time() - start
    return runs / total  # frames per second

if __name__ == "__main__":
    # Clone OMZ if missing
    if not os.path.isdir(OMZ_DIR):
        subprocess.run(["git", "clone", "https://github.com/openvinotoolkit/open_model_zoo.git", OMZ_DIR], check=True)

    results = []
    for m in MODEL_LIST:
        try:
            download_ir(m)
            xml = find_ir(m)
            fps = measure_fps(xml, runs=20)
            print(f"{m:30s} → {fps:6.1f} FPS")
            results.append((m, fps))
        except Exception as e:
            print(f"✗ {m:30s} error: {e}")

    # Sort by FPS descending
    results.sort(key=lambda x: x[1], reverse=True)
    print(f"\n=== Top 10 models by throughput on {DEVICE} ===")
    for name, fps in results[:10]:
        print(f"{name:30s} {fps:6.1f} FPS")
