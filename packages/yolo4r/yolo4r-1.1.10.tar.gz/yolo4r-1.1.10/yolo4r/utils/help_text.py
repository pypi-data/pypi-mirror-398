# utils/help_text.py

def print_detect_help():
    print("""
YOLO4R Detection Help
=====================

Usage:
    yolo4r detect [sources] [flags]
          
----------------------------------

Source Selection:
    sources=<src1 src2 ...>
        One or more video or camera streams.
        Examples:
            usb0
            usb0 usb1
            video.mp4 other.mov

----------------------------------
          
Flags:
    test
        Use the test model directory (~/.yolo4r/runs/test).
        Helpful for debugging or running detection on small models.

    model
        Set a specific official YOLO model to use for detection.
        This could be used to test camera equipment or run off of the larger COCO or DOTA datasets.
        Examples (variants n, m, x, & l available):
            yolov8
            yolov8-obb
            yolo11
            yolo11-obb
            yolo12
            NOTE: OBB models are unavailable for YOLO12-obb.
            
----------------------------------
          
Examples:
    yolo4r detect usb0
    yolo4r detect sources=usb0 usb1
    yolo4r detect test trailcam.mp4 usb0
    yolo4r model=yolo12m source=usb0

----------------------------------
""")


def print_train_help():
    print("""
YOLO4R Training Help
====================

Usage:
  yolo4r train [options]

----------------------------------
          
Training modes:
    --train, -t
        Transfer-learning mode (default). Loads pretrained weights.
        Might as well specify the model with `model=<name>`!
    
    --scratch, -s
        Train from scratch using an architecture file.
        Might as well specify the architecture with `arch=<name>`!

    update=<run_name> (--update, -u)
        Resume a previous training run ONLY if new images were added.

    resume (--resume, -r)
        Resume from last.pt.

    test (--test, -T)
        Debug mode with reduced settings and output to runs/test/.

----------------------------------
          
Model / Weights:
    model=<name> (--model, -m)
        Use pretrained weights by family:
            yolo11n, yolo11s, yolo11m, yolo11x
            yolov8n, yolov8m, yolov8x
            yolo11-obb-n, etc.

----------------------------------
          
Architecture:
    architecture=<name>, arch=<name>, backbone=<name>, (--arch, -a, -b) 
        Architecture for scratch training.
        Examples:
            yolo11
            yolo11.yaml
            custom_birds.yaml

Dataset selection:
    dataset=<name>, data=<name> (--dataset, -d)
        Choose dataset from ./data/<name>/.

    label-studio=<project> (--labelstudio, -ls)
        Convert a Label Studio export into a YOLO dataset.

----------------------------------
          
Naming:
    name=<run_name> (--name, -n)
      Set output run folder name.

----------------------------------
          
Examples:
    yolo4r train model=yolo11n dataset=birds
    yolo4r train scratch arch=custom.yaml dataset=geckos
    yolo4r train update sparrows
    yolo4r train labelstudio=my_project train

----------------------------------
""")
