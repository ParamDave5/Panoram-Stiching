# Phase 1

```commandline
cd xyliu999_p1/Phase1/Code/
python Wrapper.py --BasePath "/home/sheriarty/CMSC 733/pdave_p1/Phase1" --ImageDataFolder "Data/Train/Set2" --SaveFolder "Code/results"
```

Here are parameters for Phase 1
```commandline
--BasePath: It is the location of Phase 1 folder
--ImageDataFolder: It is the location of image folder relative to Phase1 folder(BaseFolder)
--SaveFolder: It is the location of where you want to save the results
```
# Phase 2
## Train the Neural Network
In the train.py file, we provide methods to train neural network (supervised or unsupervised):
```commandline
cd xyliu999_p1/Phase2/Code/
python Train.py --ModelType Sup --GPUId 0
```
Here, we detail the options for the arguments of our command line:
```commandline
--ModelType: ["Sup", "Unsup"]
--GPUId: ["0", "1", "2", "3"] (if you have 4 GPUs)
--NumEpochs: an integer number
--BasePath:  Path to the COCO Dataset
```
After training the neural network, we can visualize the logs using the tensorboard with:
```commandline
cd xyliu999_p1/Phase2/Code/
tensorboard --logdir Logs/
```

## Test the Neural Network
Run the test.py file will give you the performance (confusion matrix and accuracy) on either the training set or the test set.
It can be called for example as:
```commandline
cd xyliu999_p1/Phase2/Code/
python Test.py --ModelName Sup --GPUId 0 --ModelPath xxx
```
Here, we detail the options for our command line:
```commandline
--ModelName: ["Sup", "Unsup]
--GPUId: ["0", "1", "2", "3"] (if you have 4 GPUs)
--BasePath:  Path to the COCO Dataset
--ModelPath: Path to the saved model file directory
```
## Image Stitching with Neural Network
```commandline
cd xyliu999_p1/Phase2/Code/
python Wrapper.py --ModelName Sup --GPUId 0 --ModelPath xxx
```
Here, we detail the options for our command line:
```commandline
--ModelName: ["Sup", "Unsup]
--GPUId: ["0", "1", "2", "3"] (if you have 4 GPUs)
--BasePath:  Path to Test Set you want to use
--ModelPath: Path to the saved model file directory
```

