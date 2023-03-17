import depthai as dai
import tempfile
import os

def main():
    pipeline = dai.Pipeline()

    camRgb, monoLeft, monoRight = setupCameras(pipeline)
    ve1, ve2, ve3 = setupEncoders(pipeline)
    ve1Out, ve2Out, ve3Out = setupLinks(pipeline)

    configureSockets(camRgb, monoLeft, monoRight)
    linkEncoders(ve1, ve2, ve3)

    ve1Out.setStreamName('ve1Out')
    ve2Out.setStreamName('ve2Out')
    ve3Out.setStreamName('ve3Out')

    tmpMono1 = tempfile.NamedTemporaryFile()
    tmpMono2 = tempfile.NamedTemporaryFile()
    tmpColor = tempfile.NamedTemporaryFile()

    incPath = '/home/e4e/FishSense/oakd/incFile.txt'
    
    # Linking
    monoLeft.out.link(ve1.input)
    camRgb.video.link(ve2.input)
    monoRight.out.link(ve3.input)
    ve1.bitstream.link(ve1Out.input)
    ve2.bitstream.link(ve2Out.input)
    ve3.bitstream.link(ve3Out.input)

    fNum = 0
    with open(incPath) as f:
        first_line = f.readline().strip()
        fNum = int(first_line)

    with open(incPath,'w') as f:
        f.writelines(str(fNum+1))

    # Connect to device and start pipeline
    with dai.Device(pipeline) as dev:

        # Output queues will be used to get the encoded data from the outputs defined above
        outQ1 = dev.getOutputQueue(name='ve1Out', maxSize=30, blocking=True)
        outQ2 = dev.getOutputQueue(name='ve2Out', maxSize=30, blocking=True)
        outQ3 = dev.getOutputQueue(name='ve3Out', maxSize=30, blocking=True)
        
        # The .h264 / .h265 files are raw stream files (not playable yet)
        with open(tmpMono1.name, 'wb') as fileMono1H264, open(tmpColor.name, 'wb') as fileColorH265, open(tmpMono2.name, 'wb') as fileMono2H264:
            print("Press Ctrl+C to stop encoding...")
            while True:
                try:
                    # Empty each queue
                    while outQ1.has():
                        outQ1.get().getData().tofile(fileMono1H264)

                    while outQ2.has():
                        outQ2.get().getData().tofile(fileColorH265)

                    while outQ3.has():
                        outQ3.get().getData().tofile(fileMono2H264)
                except KeyboardInterrupt:
                    # Keyboard interrupt (Ctrl + C) detected
                    break
        
        cmd = "ffmpeg -framerate 30 -i {} -c copy {}"
        os.system(cmd.format(tmpMono1.name, "/home/e4e/FishSense/oakd/" + str(fNum) + "mono1.mp4"))
        os.system(cmd.format(tmpMono2.name, "/home/e4e/FishSense/oakd/" + str(fNum) + "mono2.mp4"))
        os.system(cmd.format(tmpColor.name, "/home/e4e/FishSense/oakd/" + str(fNum) + "color.mp4"))

    tmpMono1.close()
    tmpMono2.close()
    tmpColor.close()

def setupCameras(pipeline):
    # Define sources and outputs
    camRgb = pipeline.create(dai.node.ColorCamera)
    monoLeft = pipeline.create(dai.node.MonoCamera)
    monoRight = pipeline.create(dai.node.MonoCamera)

    return camRgb, monoLeft, monoRight

def setupEncoders(pipeline):
    ve1 = pipeline.create(dai.node.VideoEncoder)
    ve2 = pipeline.create(dai.node.VideoEncoder)
    ve3 = pipeline.create(dai.node.VideoEncoder)
    
    return ve1, ve2, ve3

def setupLinks(pipeline):
    ve1Out = pipeline.create(dai.node.XLinkOut)
    ve2Out = pipeline.create(dai.node.XLinkOut)
    ve3Out = pipeline.create(dai.node.XLinkOut)

    return ve1Out, ve2Out, ve3Out

def configureSockets(camRgb, monoLeft, monoRight):
    # Properties
    camRgb.setBoardSocket(dai.CameraBoardSocket.RGB)
    monoLeft.setBoardSocket(dai.CameraBoardSocket.LEFT)
    monoRight.setBoardSocket(dai.CameraBoardSocket.RIGHT)

def linkEncoders(ve1, ve2, ve3):
    # Create encoders, one for each camera, consuming the frames and encoding them using H.264 / H.265 encoding
    ve1.setDefaultProfilePreset(30, dai.VideoEncoderProperties.Profile.H264_MAIN)
    ve2.setDefaultProfilePreset(30, dai.VideoEncoderProperties.Profile.H265_MAIN)
    ve3.setDefaultProfilePreset(30, dai.VideoEncoderProperties.Profile.H264_MAIN)

if __name__=="__main__":
    main()