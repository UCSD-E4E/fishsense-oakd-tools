# OAK-D Calibration Instructions
**Source:** https://docs.luxonis.com/en/latest/pages/calibration/

1. Run the following commands:
```
git clone https://github.com/luxonis/depthai.git
cd depthai
python3 install_requirements.py
```
2. Acquire a printed copy of the charuco board provided in the above link.
3. Run the calibration script for the OAK-D as follows with the specified parameters:
```
python3 calibrate.py -s [SQURE_SIZE_IN_CM] -brd bw1098obc -db -ih
```
4. Align the board with the displayed orientations and take the required 13 images to finish calibration.
