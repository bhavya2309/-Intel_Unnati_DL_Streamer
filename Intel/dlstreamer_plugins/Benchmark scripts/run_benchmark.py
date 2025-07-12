#!/usr/bin/env python3
"""
run_benchmark.py

Benchmark DLStreamer (person→age) over CPU, GPU & NPU via an RTSP feed.
Appends results to a CSV and prints a summary.

Requirements (once):
  sudo apt update
  sudo apt install -y python3-psutil python3-gi gir1.2-gstreamer-1.0
"""
import os
import time
import argparse
import csv
import psutil
import gi

gi.require_version("Gst", "1.0")
from gi.repository import Gst, GLib

Gst.init(None)


def read_gpu_percent():
    base = "/sys/class/drm"
    for d in os.listdir(base):
        p = os.path.join(base, d, "device", "gpu_busy_percent")
        if os.path.isfile(p):
            try:
                return float(open(p).read().strip())
            except:
                pass
    return None


def read_npu_percent():
    # Stub: implement if your NPU exports a sysfs busy-percent
    return None


def read_net_bytes(interface="lo"):
    nic = psutil.net_io_counters(pernic=True).get(interface)
    if nic:
        return nic.bytes_recv
    # fallback sum
    return sum(n.bytes_recv for n in psutil.net_io_counters(pernic=True).values())


class StreamCounter:
    def __init__(self, idx, rtsp, device, mdl1, mdl2):
        self.count = 0
        desc = (
            f"rtspsrc location={rtsp} latency=200 ! "
            "rtph264depay ! h264parse ! avdec_h264 ! "
            "videoconvert ! videoscale ! "
            f"gvadetect model={mdl1} device={device} ! "
            f"gvaclassify model={mdl2} device={device} ! "
            "gvawatermark ! videoconvert ! "
            f"identity name=ctr{idx} signal-handoffs=true ! fakesink"
        )
        self.pipe = Gst.parse_launch(desc)
        ident = self.pipe.get_by_name(f"ctr{idx}")
        ident.connect("handoff", self._on_frame)

    def _on_frame(self, ident, buf):
        self.count += 1

    def start(self):
        self.pipe.set_state(Gst.State.PLAYING)

    def stop(self):
        self.pipe.set_state(Gst.State.NULL)


def detect_bottleneck(cpu, mem, gpu, npu):
    metrics = {"CPU": cpu, "Memory": mem}
    if gpu is not None: metrics["GPU"] = gpu
    if npu is not None: metrics["NPU"] = npu
    return max(metrics, key=metrics.get)


def run_trial(device, n_streams, args):
    counters = [
        StreamCounter(i, args.rtsp, device, args.person, args.age)
        for i in range(n_streams)
    ]
    for c in counters: c.start()
    loop = GLib.MainLoop()
    GLib.timeout_add_seconds(args.duration, loop.quit)
    loop.run()
    for c in counters: c.stop()

    total = sum(c.count for c in counters)
    combined = total / args.duration if args.duration else 0.0
    per = combined / n_streams if n_streams else 0.0
    return combined, per


def main():
    p = argparse.ArgumentParser(description="DLStreamer RTSP benchmark")
    p.add_argument("--devices",     default="CPU,GPU,NPU",
                   help="Comma-separated list of devices")
    p.add_argument("--step",        type=int,   default=2,
                   help="Increment streams by this")
    p.add_argument("--max-streams", type=int,   default=10,
                   help="Max concurrent streams")
    p.add_argument("--duration",    type=int,   default=20,
                   help="Seconds per trial")
    p.add_argument("--rtsp",        required=True,
                   help="RTSP URL, e.g. rtsp://127.0.0.1:8554/test")
    p.add_argument("--person",      required=True,
                   help="Path to person-detection XML")
    p.add_argument("--age",         required=True,
                   help="Path to age-gender XML")
    p.add_argument("--net-interface", default="lo",
                   help="Interface for network sampling (default lo)")
    p.add_argument("--target-fps",  type=float, default=15.0,
                   help="Stop adding streams when per-stream FPS < this")
    p.add_argument("--output",      default="benchmark_results.csv",
                   help="CSV file to append results")
    args = p.parse_args()

    devices = [d.strip() for d in args.devices.split(",")]

    # Prepare CSV
    first = not os.path.exists(args.output)
    f = open(args.output, "a", newline="")
    w = csv.writer(f)
    if first:
        w.writerow([
            "Streams","Device","Combined_FPS","Per_Stream_FPS",
            "CPU_pct","Memory_pct","GPU_pct","NPU_pct","Network_Mbps","Bottleneck"
        ])

    # Console header
    hdr = ("Streams  Device  C-FPS  S-FPS  CPU%   MEM%   GPU%   NPU%   NET(Mbps)  Bottleneck")
    print(hdr)
    print("-"*len(hdr))

    for dev in devices:
        for n in range(1, args.max_streams+1, args.step):
            # sample before
            cpu0 = psutil.cpu_percent(None)
            mem0 = psutil.virtual_memory().percent
            net0 = read_net_bytes(args.net_interface)
            gpu0 = read_gpu_percent()
            npu0 = read_npu_percent()

            cmb, per = run_trial(dev, n, args)

            # sample after
            cpu1 = psutil.cpu_percent(None)
            mem1 = psutil.virtual_memory().percent
            net1 = read_net_bytes(args.net_interface)
            gpu1 = read_gpu_percent()
            npu1 = read_npu_percent()

            # compute MB/s
            bytes_per_s = (net1 - net0) / args.duration
            net_mbps    = bytes_per_s * 8.0 / 1e6

            bneck = detect_bottleneck(cpu1, mem1, gpu1, npu1)

            # print
            print(f"{n:>7d}  {dev:>6s}  {cmb:6.2f}  {per:6.2f}  "
                  f"{cpu1:5.1f}  {mem1:5.1f}  "
                  f"{(gpu1 or 0):5.1f}  {(npu1 or 0):5.1f}  "
                  f"{net_mbps:10.1f}  {bneck}")

            # log CSV
            w.writerow([
                n, dev,
                f"{cmb:.2f}", f"{per:.2f}",
                f"{cpu1:.1f}", f"{mem1:.1f}",
                (f"{gpu1:.1f}" if gpu1 is not None else "N/A"),
                (f"{npu1:.1f}" if npu1 is not None else "N/A"),
                f"{net_mbps:.1f}",
                bneck
            ])
            f.flush()

            if n > args.step and per < args.target_fps:
                break

    f.close()
    print(f"\n✅ Results appended to {args.output}")


if __name__ == "__main__":
    main()




"""
cd ~/intel/dlstreamer_plugins

# (re)configure, build, install
meson setup build --prefix=/usr
ninja -C build
sudo ninja -C build install

# Force GStreamer to re-scan its plugin folder
export GST_PLUGIN_PATH=/usr/lib/gstreamer-1.0:$GST_PLUGIN_PATH
rm -f ~/.cache/gstreamer-1.0/registry.*.bin

cd ~/intel/dlstreamer_plugins
chmod +x run_benchmark.py

./run_benchmark.py \
  --devices     CPU,GPU,NPU \
  --step        2 \
  --max-streams 10 \
  --duration    30 \
  --rtsp        rtsp://127.0.0.1:8554/test \
  --person      /home/bhavya/intel/models/intel/person-detection-retail-0013/FP32/person-detection-retail-0013.xml \
  --age         /home/bhavya/intel/models/intel/age-gender-recognition-retail-0013/FP32/age-gender-recognition-retail-0013.xml \
  --target-fps  15.0 \
  --output      benchmark_results.csv"""
"""

bhavya@bhavyas-zenbook:~/intel/rtsp$ # serve a 640×360 SMPTE color bar at rtsp://0.0.0.0:8554/test
~/intel/rtsp/test-launch \
  "( videotestsrc is-live=true pattern=smpte \
     ! video/x-raw,format=I420,width=640,height=360,framerate=30/1 \
     ! x264enc tune=zerolatency bitrate=500 speed-preset=superfast \
     ! rtph264pay name=pay0 pt=96 )"

"""
