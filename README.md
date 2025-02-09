# Digit_Classification

This is a Python project that classifies hand-written digits using a Multilayer Perceptron (MLP) neural network. The project uses the MNIST dataset and is implemented with PyTorch and Torchvision.

## Installation

To run this project, you need to have Python installed along with the following libraries:
- PyTorch
- Torchvision
- NumPy
- Matplotlib
- scikit-learn
- tqdm

You can install these dependencies using pip:

```
pip install torch torchvision numpy matplotlib scikit-learn tqdm
```

## Usage

To use this project, run the `multilayer_perceptron_cs213.py` script. The script will load the MNIST dataset, preprocess the data, and set up the MLP model.

## Model Architecture

The model uses a Multilayer Perceptron with the following architecture:
- Input layer: 784 neurons (28x28 pixel images flattened)
- Hidden layer 1: 250 neurons with ReLU activation
- Hidden layer 2: 100 neurons with ReLU activation
- Output layer: 10 neurons (one for each digit)

The model includes data augmentation techniques such as random rotation and cropping for training data.