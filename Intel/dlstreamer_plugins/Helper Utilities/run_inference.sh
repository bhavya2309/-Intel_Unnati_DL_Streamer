#!/usr/bin/env bash

# Models
PERSON_MODEL="$HOME/intel/models/intel/person-detection-retail-0013/FP32/person-detection-retail-0013.xml"
AGE_MODEL="$HOME/intel/models/intel/age-gender-recognition-retail-0013/FP32/age-gender-recognition-retail-0013.xml"

# Make sure GStreamer finds DL Streamer plugins
export GST_PLUGIN_PATH=/usr/lib/gstreamer-1.0:$GST_PLUGIN_PATH

run_test() {
  local DEVICE=$1
  echo
  echo "===== Testing on $DEVICE (300 frames) ====="
  gst-launch-1.0 -q \
    videotestsrc is-live=true num-buffers=300 pattern=smpte ! \
      video/x-raw,format=I420,width=640,height=360,framerate=30/1 ! \
      videoconvert ! videoscale ! \
      gvadetect model="$PERSON_MODEL" device="$DEVICE" ! \
      gvaclassify model="$AGE_MODEL"  device="$DEVICE" ! \
      gvawatermark ! \
      videoconvert ! queue ! \
      fpsdisplaysink video-sink=fakesink sync=false text-overlay=false
}

# CPU
run_test CPU

# GPU
run_test GPU

# NPU (enable the Intel NPU driver)
export ZE_ENABLE_ALT_DRIVERS=libze_intel_npu.so
run_test NPU

echo
echo "All tests complete."
