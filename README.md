# Intel DLStreamer Pipeline Benchmark

This repository hosts a benchmarking study evaluating Intel’s Deep Learning Streamer (DLStreamer) pipeline performance using Intel hardware acceleration (CPU, GPU, and NPU) for AI-driven video analytics.

---

## Project Overview

This project evaluates a two-stage AI pipeline featuring person detection and age classification models running on Intel’s Lunar Lake architecture. It compares performance across **CPU-only**, **GPU-accelerated**, and **NPU-accelerated** modes to determine optimal scalability and throughput for real-time video analytics targeting **15 FPS per stream**.

---

## Hardware

- **CPU:** Intel Core Ultra 2 256V (2 Performance cores, 6 Efficiency cores)  
- **GPU:** Intel Arc 140V (8 Xe-cores @ 1.95 GHz)  
- **NPU:** Intel AI Boost NPU (47 TOPS)  
- **Memory:** 32 GB LPDDR5X RAM  
- **System:** Asus Zenbook S14  

---

## Software

- **OS:** Ubuntu 24.04.2 LTS  
- **DLStreamer:** v2024.1  
- **OpenVINO™ Toolkit**  
- **GStreamer** Framework  
- **Python 3.8+**  
- **NumPy 1.26**  

---

## 3. Pipeline Stages

1. **Decode** – H.264/H.265 decode from RTSP/IP camera feeds  
2. **Detect** – SSD-MobileNet person detection (`person-detection-retail-0002`)  
3. **Classify** – Age/gender classification (`age-gender-recognition-retail-0013`)  
4. **Analytics** – Rule-based alerts, anomaly detection  
5. **Output** – Annotated video stream + alert logs  

---

## 4. Installation & Setup

### 4.1 Prepare Ubuntu Dual-Boot
1. Create a bootable USB for Ubuntu 24.04  
2. Disable Secure Boot in BIOS  
3. Install Ubuntu alongside your existing OS  

### 4.2 Create Python Virtual Environment
- sudo apt update  
- sudo apt install -y python3 python3-pip python3-venv  
- python3 -m venv dlstreamer_env  
- source dlstreamer_env/bin/activate  
- pip install --upgrade pip  
- pip install openvino numpy  

### 4.3 Install GStreamer & DLStreamer Plugins
- sudo apt install -y gstreamer1.0-tools gstreamer1.0-plugins-base gstreamer1.0-plugins-good gstreamer1.0-plugins-bad  

### 4.4 Clone This Repository
- git clone https://github.com/bhavya2309/-Intel_Unnati_DL_Streamer.git
- cd intel-dlstreamer-benchmark  

---

## 5. Implementation Videos

Walkthroughs covering environment setup, dual-boot configuration, Python venv setup, DLStreamer pipeline demos (CPU/GPU/NPU), and benchmarking scripts are located in the `Intel/Documentation/Implementation Videos` directory.

---

## Benchmark Results

*(See `Intel/Documentation` for detailed tables and graphs)*

---

## Conclusion

- **CPU-Only:** Best for low-density, compute-light scenarios  
- **GPU-Accelerated:** Ideal for high-density, high-throughput deployments  
- **NPU-Accelerated:** Optimal for power-efficient, moderate-density scenarios  

---

## Future Work

- Multi-stream batching  
- Hybrid GPU/NPU load balancing  
- Asynchronous pipeline processing  

---

## References

1. [Intel® Core™ Ultra 2 Processor Specifications](https://ark.intel.com/)  
2. [DLStreamer Developer Guide](https://dlstreamer.github.io/)  
3. [Ubuntu Documentation](https://help.ubuntu.com/)  
4. [OpenVINO™ Toolkit Documentation](https://docs.openvino.ai/)  
