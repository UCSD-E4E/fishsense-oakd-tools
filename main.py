import cv2
import depthai as dai
from calc import HostSpatialsCalc
from utility import *
import numpy as np
import math
import os
# import tifffile as tiff

os.chdir(r"C:\Users\hnvul\Documents\GitHub\fishsense-oakd\Videos")

# Create pipeline
pipeline = dai.Pipeline()

# Define sources and outputs
monoLeft = pipeline.create(dai.node.MonoCamera)
monoRight = pipeline.create(dai.node.MonoCamera)
stereo = pipeline.create(dai.node.StereoDepth)

cam = pipeline.create(dai.node.ColorCamera)
cam.setPreviewSize(640, 400)
cam.setBoardSocket(dai.CameraBoardSocket.RGB)
cam.setResolution(dai.ColorCameraProperties.SensorResolution.THE_4_K)
cam.setInterleaved(True)
cam.setColorOrder(dai.ColorCameraProperties.ColorOrder.BGR)

# Properties
monoLeft.setResolution(dai.MonoCameraProperties.SensorResolution.THE_400_P)
monoLeft.setBoardSocket(dai.CameraBoardSocket.LEFT)
monoRight.setResolution(dai.MonoCameraProperties.SensorResolution.THE_400_P)
monoRight.setBoardSocket(dai.CameraBoardSocket.RIGHT)

stereo.initialConfig.setConfidenceThreshold(255)
stereo.setLeftRightCheck(True)
stereo.setSubpixel(False)

# Create a node that will produce the depth map (using disparity output as it's easier to visualize depth this way)
stereo.setDefaultProfilePreset(dai.node.StereoDepth.PresetMode.HIGH_DENSITY)
# Options: MEDIAN_OFF, KERNEL_3x3, KERNEL_5x5, KERNEL_7x7 (default)
stereo.initialConfig.setMedianFilter(dai.MedianFilter.KERNEL_7x7)


# config = stereo.initialConfig.get()
# config.postProcessing.speckleFilter.enable = True
# config.postProcessing.speckleFilter.speckleRange = 50
# config.postProcessing.temporalFilter.enable = True
# config.postProcessing.spatialFilter.enable = True
# config.postProcessing.spatialFilter.holeFillingRadius = 2
# config.postProcessing.spatialFilter.numIterations = 1
# stereo.initialConfig.set(config)


# Linking
monoLeft.out.link(stereo.left)
monoRight.out.link(stereo.right)

xoutDepth = pipeline.create(dai.node.XLinkOut)
xoutDepth.setStreamName("depth")
stereo.depth.link(xoutDepth.input)

xoutDepth = pipeline.create(dai.node.XLinkOut)
xoutDepth.setStreamName("disp")
stereo.disparity.link(xoutDepth.input)

xoutDepth = pipeline.create(dai.node.XLinkOut)
xoutDepth.setStreamName("rgb")
cam.preview.link(xoutDepth.input)

# Connect to device and start pipeline
with dai.Device(pipeline) as device:
    # Output queue will be used to get the depth frames from the outputs defined above
    depthQueue = device.getOutputQueue(name="depth")
    dispQ = device.getOutputQueue(name="disp")
    rgbQ = device.getOutputQueue(name="rgb")

    text = TextHelper()
    text2 = TextHelper()
    distanceText = TextHelper()
    hostSpatials = HostSpatialsCalc(device)
    hostSpatials2 = HostSpatialsCalc(device)

    y = 200
    x = 300
    step = 3
    delta = 5
    hostSpatials.setDeltaRoi(delta)

    hostSpatials2 = HostSpatialsCalc(device)
    yy = 200
    xx = 300
    step = 3
    delta = 5
    hostSpatials2.setDeltaRoi(delta)

    print("Use WASD keys to move ROI.\nUse 'r' and 'f' to change ROI size.")

    while True:
        depthFrame = depthQueue.get().getFrame()
        # Calculate spatial coordiantes from depth frame
        spatials, centroid = hostSpatials.calc_spatials(depthFrame, (x,y)) # centroid == x/y in our case
        spatials2, centroid2 = hostSpatials2.calc_spatials(depthFrame, (xx,yy)) # centroid == x/y in our case



        # Get disparity frame for nicer depth visualization
        disp = dispQ.get().getFrame()
        # tiff.imwrite('depth.tif', depthFrame, photometric='minisblack', append=True)
        # tiff.imwrite('disp.tif', disp, photometric='minisblack', append=True)
        disp = (disp * (255 / stereo.initialConfig.getMaxDisparity())).astype(np.uint8)
        disp = cv2.applyColorMap(disp, cv2.COLORMAP_JET)

        rgb = rgbQ.get().getFrame()

        output = disp

        text.rectangle(output, (x-delta, y-delta), (x+delta, y+delta))
        # text.putText(output, "X: " + ("{:.3f}m".format(spatials['x']/1000) if not math.isnan(spatials['x']) else "--"), (x + 10, y + 20))
        # text.putText(output, "Y: " + ("{:.3f}m".format(spatials['y']/1000) if not math.isnan(spatials['y']) else "--"), (x + 10, y + 35))
        text.putText(output, "Z: " + ("{:.2f}m".format(spatials['z']/1000) if not math.isnan(spatials['z']) else "--"), (x + 10, y + 35))
        
        text2.rectangle(output, (xx-delta, yy-delta), (xx+delta, yy+delta))
        # text2.putText(output, "X: " + ("{:.1f}m".format(spatials2['x']/1000) if not math.isnan(spatials2['x']) else "--"), (xx + 10, yy + 20))
        # text2.putText(output, "Y: " + ("{:.1f}m".format(spatials2['y']/1000) if not math.isnan(spatials2['y']) else "--"), (xx + 10, yy + 35))
        text2.putText(output, "Z: " + ("{:.2f}m".format(spatials2['z']/1000) if not math.isnan(spatials2['z']) else "--"), (xx + 10, yy + 50))

        sum = math.pow(spatials2['x']/1000 - spatials['x']/1000, 2) + math.pow(spatials2['y']/1000 - spatials['y']/1000, 2) + math.pow(spatials2['z']/1000 - spatials['z']/1000, 2)
        distance = math.sqrt(sum)
        distanceText.putText(output, "Distance: " + ("{:.3f}m".format(distance) if not math.isnan(distance) else "--"), (320, 100))

        # Show the frame
        cv2.imshow("rgb", rgb)
        cv2.imshow("depth", output)

        key = cv2.waitKey(1)
        if key == ord('q'):
            break
        elif key == ord('w'):
            y -= step
        elif key == ord('a'):
            x -= step
        elif key == ord('s'):
            y += step
        elif key == ord('d'):
            x += step
        elif key == ord('r'): # Increase Delta
            if delta < 50:
                delta += 1
                hostSpatials.setDeltaRoi(delta)
        elif key == ord('f'): # Decrease Delta
            if 3 < delta:
                delta -= 1
                hostSpatials.setDeltaRoi(delta)
        elif key == ord('o'):
            yy -= step
        elif key == ord('k'):
            xx -= step
        elif key == ord('l'):
            yy += step
        elif key == ord(';'):
            xx += step
        # elif key == ord('r'): # Increase Delta
        #     if delta < 50:
        #         delta += 1
        #         hostSpatials.setDeltaRoi(delta)
        # elif key == ord('f'): # Decrease Delta
        #     if 3 < delta:
        #         delta -= 1
        #         hostSpatials.setDeltaRoi(delta)