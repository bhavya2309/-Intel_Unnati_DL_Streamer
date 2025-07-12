#!/usr/bin/env python3
import gi
gi.require_versions({
    'Gst': '1.0',
    'GstRtspServer': '1.0',
})
from gi.repository import Gst, GstRtspServer, GLib

Gst.init(None)
server = GstRtspServer.RTSPServer.new()
mounts = server.get_mount_points()
factory = GstRtspServer.RTSPMediaFactory.new()
factory.set_launch(
    "( filesrc location=$HOME/intel/models/test.mp4 ! decodebin ! "
    "videoconvert ! x264enc tune=zerolatency bitrate=512 speed-preset=superfast ! "
    "rtph264pay name=pay0 pt=96 )"
)
mounts.add_factory("/test", factory)
server.attach(None)
print("RTSP Server ready at rtsp://127.0.0.1:8554/test")
GLib.MainLoop().run()
