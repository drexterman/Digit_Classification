# -*- coding: utf-8 -*-
"""Multilayer Perceptron_CS213.ipynb

Automatically generated by Colab.

Original file is located at
    https://colab.research.google.com/drive/1pQgPl8jopU5w2V0wzYKK09SlOIPErAwQ

# 1 - Multilayer Perceptron

In this series, we'll be building machine learning models (specifically, neural networks) to perform image classification using PyTorch and Torchvision.

In this first notebook, we'll start with one of the most basic neural network architectures, a multilayer perceptron (MLP), also known as a feedforward network. The dataset we'll be using is the famous MNIST dataset, a dataset of 28x28 black and white images consisting of handwritten digits, 0 to 9.

![](https://github.com/bentrevett/pytorch-image-classification/blob/master/assets/mlp-mnist.png?raw=1)

We'll process the dataset, build our model, and then train our model. Afterwards, we'll do a short dive into what the model has actually learned.

### Data Processing

Let's start by importing all the modules we'll need. The main ones we need to import are:
- torch for general PyTorch functionality
- torch.nn and torch.nn.functional for neural network based functions
- torch.optim for our optimizer which will update the parameters of our neural network
- torch.utils.data for handling the dataset
- torchvision.transforms for data augmentation
- torchvision.datasets for loading the dataset
- sklearn's metrics for visualizing a confusion matrix
- sklearn's decomposition and manifold for visualizing the neural network's representations in two dimensions
- matplotlib for plotting
"""

import torch
import torch.nn as nn
import torch.nn.functional as F
import torch.optim as optim
import torch.utils.data as data

import torchvision.transforms as transforms
import torchvision.datasets as datasets

from sklearn import metrics
from sklearn import decomposition
from sklearn import manifold
from tqdm.notebook import trange, tqdm  #provides progress bars
import matplotlib.pyplot as plt
import numpy as np

import copy
import random
import time
import os

import cv2 
#whats a seed
seed=0
random.seed(seed)
np.random.seed(seed)
torch.manual_seed(seed)
torch.cuda.manual_seed(seed)
torch.backends.cudnn.deterministic = True

ROOT = '.data'
mean=0.1307
std=0.3801

# 784 -> 250 -> 100 -> 10 neural net wil Relu activation function at every junction
class MLP(nn.Module):
    def __init__(self, input_dim, output_dim):
        super().__init__()

        self.input_fc = nn.Linear(input_dim, 250)
        self.hidden_fc = nn.Linear(250, 100)
        self.output_fc = nn.Linear(100, output_dim)

    def forward(self, x):

        # x = [batch size, height, width]

        batch_size = x.shape[0]

        x = x.view(batch_size, -1)

        # x = [batch size, height * width]

        h_1 = F.relu(self.input_fc(x))

        # h_1 = [batch size, 250]

        h_2 = F.relu(self.hidden_fc(h_1))

        # h_2 = [batch size, 100]

        y_pred = self.output_fc(h_2)

        # y_pred = [batch size, output dim]

        return y_pred, h_2
    

"""A `transform` states how our data should be augmented and processed. Data augmentation involves manipulating the available training data in a way that artificially creates more training examples. We use `transforms.Compose` to built a list of transformations that will be applied to the image.

The transforms we use are:
- `RandomRotation` - randomly rotates the image between `(-x, +x)` degrees, where we have set `x = 5`. Note, the `fill=(0,)` is due to a [bug](https://github.com/pytorch/vision/issues/1759) in some versions of torchvision.
- `RandomCrop` - this first adds `padding` around our image, 2 pixels here, to artificially make it bigger, before taking a random `28x28` square crop of the image.
- `ToTensor()` - this converts the image from a PIL image into a PyTorch tensor.
- `Normalize` - this subtracts the mean and divides by the standard deviations given.

The first two transformations have to be applied before `ToTensor` as they should both be applied on a PIL image. `Normalize` should only be applied to the images after they have been converted into a tensor. See the Torchvision documentation for [transforms that should be applied to PIL images](https://pytorch.org/vision/stable/transforms.html#transforms-on-pil-image-only) and [transforms that should be applied on tensors](https://pytorch.org/vision/stable/transforms.html#transforms-on-torch-tensor-only).

We have two lists of transforms, a train and a test transform. The train transforms are to artificially create more examples for our model to train on. We do not augment our test data in the same way, as we want a consistent set of examples to evaluate our final model on. The test data, however, should still be normalized.
"""
train_transforms = transforms.Compose([
                            transforms.RandomRotation(5, fill=(0,)),
                            transforms.RandomCrop(28, padding=2),
                            transforms.ToTensor(),
                            transforms.Normalize(mean=[mean], std=[std])
                                      ])

test_transforms = transforms.Compose([
                           transforms.ToTensor(),
                           transforms.Normalize(mean=[mean], std=[std])
                                     ])

def showcase():
    train_data = datasets.MNIST(root=ROOT,
                                train=True,
                                download=True)
    print(train_data)



    train_data = datasets.MNIST(root=ROOT,
                                train=True,
                                download=True,
                                transform=train_transforms)

    test_data = datasets.MNIST(root=ROOT,
                            train=False,
                            download=True,
                            transform=test_transforms)


    print(f'Number of training examples: {len(train_data)}')
    print(f'Number of testing examples: {len(test_data)}')

    """We can get a look at some of the images within our dataset to see what we're working with. The function below plots a square grid of images. If you supply less than a complete square number of images it will ignore the last few.

    *p.s. I edited the code to plot all the images even if it's not a perfect square*
    """

    def plot_images(images):

        n_images = len(images)

        if (np.sqrt(n_images))%1.0==0:
            rows = int(np.sqrt(n_images))
            cols = int(np.sqrt(n_images))
        else:
            rows=1
            cols=n_images

        fig = plt.figure()
        for i in range(rows*cols):
            ax = fig.add_subplot(rows, cols, i+1)
            ax.imshow(images[i].view(28, 28).cpu().numpy(), cmap='bone')
            ax.axis('off')

    """Let's load 25 images. These will have been processed through our transforms, so will be randomly rotated and cropped.

    It's a good practice to see your data with your transforms applied, so you can ensure they look sensible. For example, it wouldn't make sense to flip the digits horizontally or vertically unless you are expecting to see what in your test data."""

    N_IMAGES = 100

    images = [image for image, label in [train_data[i] for i in range(N_IMAGES)] if label==6]

    plot_images(images)

    """The MNIST dataset comes with a training and test set, but not a validation set. We want to use a validation set to check how well our model performs on unseen data. Why don't we just use the test data? We should only be measuring our performance over the test set once, after all training is done. We can think of the validation set as a proxy test set we are allowed to look at as much as we want.

    Furthermore, we create a validation set, taking 10% of the training set. **Note:** ***the validation set should always be created from the training set. Never take the validation set from the test set.*** When researchers publish research papers they should be comparing performance across the test set and the only way to ensure this is a fair comparison is for all researchers to use the same test set. If the validation set is taken from the test set, then the test set is not the same as everyone else's and the results cannot be compared against each other.

    First, we have to define the exact number of examples that we want to be in each split of the training/validation sets.
    """

    VALID_RATIO = 0.9

    n_train_examples = int(len(train_data) * VALID_RATIO)
    n_valid_examples = len(train_data) - n_train_examples

    """Then, we use the `random_split` function to take a random 10% of the training set to use as a validation set. The remaining 90% will stay as the training set."""

    train_data, valid_data = data.random_split(train_data,
                                            [n_train_examples, n_valid_examples])

    """We can print out the number of examples again to check our splits are correct."""

    print(f'Number of training examples: {len(train_data)}')
    print(f'Number of validation examples: {len(valid_data)}')
    print(f'Number of testing examples: {len(test_data)}')

    """One thing to consider is that as the validation set has been created from the training set it has the same transforms as the training set, with the random rotating and cropping. As we want our validation set to act as a proxy for the test set, it should also be fixed, without any random augmentation.

    First, let's see what 25 of the images within the validation set look like with the training transforms:
    """

    N_IMAGES = 25

    images = [image for image, label in [valid_data[i] for i in range(N_IMAGES)]]

    plot_images(images)

    """We can now simply replace the validation set's transform by overwriting it with our test transforms from above.

    As the validation set is a `Subset` of the training set, if we change the transforms of one, then by default Torchvision will change the transforms of the other. To stop this from happening, we make a `deepcopy` of the validation data.
    """

    valid_data = copy.deepcopy(valid_data)
    valid_data.dataset.transform = test_transforms

    """To double check we've correctly replaced the training transforms, we can view the same set of images and notice how they're more central (no random cropping) and have a more standard orientation (no random rotations)."""

    N_IMAGES = 25

    images = [image for image, label in [valid_data[i] for i in range(N_IMAGES)]]

    plot_images(images)

    """Next, we'll define a `DataLoader` for each of the training/validation/test sets. We can iterate over these, and they will yield batches of images and labels which we can use to train our model.

    We only need to shuffle our training set as it will be used for stochastic gradient descent, and we want each batch to be different between epochs. As we aren't using the validation or test sets to update our model parameters, they do not need to be shuffled.

    Ideally, we want to use the biggest batch size that we can. The 64 here is relatively small and can be increased if our hardware can handle it.
    """

    BATCH_SIZE = 64

    train_iterator = data.DataLoader(train_data,
                                    shuffle=True,
                                    batch_size=BATCH_SIZE)

    valid_iterator = data.DataLoader(valid_data,
                                    batch_size=BATCH_SIZE)

    test_iterator = data.DataLoader(test_data,
                                    batch_size=BATCH_SIZE)


    INPUT_DIM = 28 * 28
    OUTPUT_DIM = 10

    model = MLP(INPUT_DIM, OUTPUT_DIM) # Defined Model here


    def count_parameters(model):
        return sum(p.numel() for p in model.parameters() if p.requires_grad)

    print(f'The model has {count_parameters(model):,} trainable parameters')

    """### Training the Model

    Next, we'll define our optimizer. This is the algorithm we will use to update the parameters of our model with respect to the loss calculated on the data.

    We aren't going to go into too much detail on how neural networks are trained (see [this](http://neuralnetworksanddeeplearning.com/) article if you want to know how) but the gist is:
    - pass a batch of data through your model
    - calculate the loss of your batch by comparing your model's predictions against the actual labels
    - calculate the gradient of each of your parameters with respect to the loss
    - update each of your parameters by subtracting their gradient multiplied by a small *learning rate* parameter

    We use the *Adam* algorithm with the default parameters to update our model. Improved results could be obtained by searching over different optimizers and learning rates, however default Adam is usually a good starting off point. Check out [this](https://ruder.io/optimizing-gradient-descent/) article if you want to learn more about the different optimization algorithms commonly used for neural networks.
    """

    optimizer = optim.Adam(model.parameters())

    """
    `CrossEntropyLoss` both computes the *softmax* activation function on the supplied predictions as well as the actual loss via *negative log likelihood*.
    """

    criterion = nn.CrossEntropyLoss()

    """We then define `device`. This is used to place your model and data on to a GPU, if you have one."""

    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')

    """We place our model and criterion on to the device by using the `.to` method."""

    model = model.to(device)
    criterion = criterion.to(device)

    """Next, we'll define a function to calculate the accuracy of our model. This takes the index of the highest value for your prediction and compares it against the actual class label. We then divide how many our model got correct by the amount in the batch to calculate accuracy across the batch."""

    def calculate_accuracy(y_pred, y):
        top_pred = y_pred.argmax(1, keepdim=True)
        correct = top_pred.eq(y.view_as(top_pred)).sum()
        acc = correct.float() / y.shape[0]
        return acc

    """We finally define our training loop.

    This will:
    - put our model into `train` mode
    - iterate over our dataloader, returning batches of (image, label)
    - place the batch on to our GPU, if we have one
    - clear the gradients calculated from the last batch
    - pass our batch of images, `x`, through to model to get predictions, `y_pred`
    - calculate the loss between our predictions and the actual labels
    - calculate the accuracy between our predictions and the actual labels
    - calculate the gradients of each parameter
    - update the parameters by taking an optimizer step
    - update our metrics

    Some layers act differently when training and evaluating the model that contains them, hence why we must tell our model we are in "training" mode. The model we are using here does not use any of those layers, however it is good practice to get used to putting your model in training mode.
    """

    def train(model, iterator, optimizer, criterion, device):

        epoch_loss = 0
        epoch_acc = 0

        model.train()

        for (x, y) in tqdm(iterator, desc="Training", leave=False):

            x = x.to(device)
            y = y.to(device)

            optimizer.zero_grad()

            y_pred, _ = model(x)

            loss = criterion(y_pred, y)

            acc = calculate_accuracy(y_pred, y)

            loss.backward()

            optimizer.step()

            epoch_loss += loss.item()
            epoch_acc += acc.item()

        return epoch_loss / len(iterator), epoch_acc / len(iterator)

    """The evaluation loop is similar to the training loop. The differences are:
    - we put our model into evaluation mode with `model.eval()`
    - we wrap the iterations inside a `with torch.no_grad()`
    - we do not zero gradients as we are not calculating any
    - we do not calculate gradients as we are not updating parameters
    - we do not take an optimizer step as we are not calculating gradients

    `torch.no_grad()` ensures that gradients are not calculated for whatever is inside the `with` block. As our model will not have to calculate gradients, it will be faster and use less memory.
    """

    def evaluate(model, iterator, criterion, device):

        epoch_loss = 0
        epoch_acc = 0

        model.eval()

        with torch.no_grad():

            for (x, y) in tqdm(iterator, desc="Evaluating", leave=False):

                x = x.to(device)
                y = y.to(device)

                y_pred, _ = model(x)

                loss = criterion(y_pred, y)

                acc = calculate_accuracy(y_pred, y)

                epoch_loss += loss.item()
                epoch_acc += acc.item()

        return epoch_loss / len(iterator), epoch_acc / len(iterator)

    """The final step before training is to define a small function to tell us how long an epoch took."""

    def epoch_time(start_time, end_time):
        elapsed_time = end_time - start_time
        elapsed_mins = int(elapsed_time / 60)
        elapsed_secs = int(elapsed_time - (elapsed_mins * 60))
        return elapsed_mins, elapsed_secs

    """We're finally ready to train!

    During each epoch we calculate the training loss and accuracy, followed by the validation loss and accuracy. We then check if the validation loss achieved is the best validation loss we have seen. If so, we save our model's parameters (called a `state_dict`).
    """

    EPOCHS = 10

    best_valid_loss = float('inf')
    x=[]
    tr=[]
    va=[]
    for epoch in trange(EPOCHS):

        start_time = time.monotonic()

        train_loss, train_acc = train(model, train_iterator, optimizer, criterion, device)
        valid_loss, valid_acc = evaluate(model, valid_iterator, criterion, device)

        if valid_loss < best_valid_loss:
            best_valid_loss = valid_loss
            torch.save(model.state_dict(), 'tut1-model.pt')

        end_time = time.monotonic()

        epoch_mins, epoch_secs = epoch_time(start_time, end_time)
        x.append(epoch)
        tr.append(train_acc*100)
        va.append(valid_acc*100)
        print(f'Epoch: {epoch+1:01} | Epoch Time: {epoch_mins}m {epoch_secs}s')
        print(f'\tTrain Loss: {train_loss:.3f} | Train Acc: {train_acc*100:.2f}%')
        print(f'\t Val. Loss: {valid_loss:.3f} |  Val. Acc: {valid_acc*100:.2f}%')

    """Afterwards, we load our the parameters of the model that achieved the best validation loss and then use this to evaluate our model on the test set."""

    model.load_state_dict(torch.load('tut1-model.pt',weights_only=True))

    test_loss, test_acc = evaluate(model, test_iterator, criterion, device)

    """Our model achieves 98% accuracy on the test set.

    This can be improved by tweaking hyperparameters, e.g. number of layers, number of neurons per layer, optimization algorithm used, learning rate, etc.
    """

    print(f'Test Loss: {test_loss:.3f} | Test Acc: {test_acc*100:.2f}%')

    plt.plot(x,tr)
    plt.plot(x,va)
    plt.scatter(x,tr)
    plt.scatter(x,va)
    plt.legend(["training","validation"])
    plt.xlabel("No. of epochs")
    plt.ylabel("Accuracy in %")
    plt.title("Accuracy vs epochs")
    plt.show()

def trial():
    # Load sample image
    print("Enter file path: ")
    file=input()
    #file = r'{path}'
    test_image = cv2.imread(file, cv2.IMREAD_GRAYSCALE)

    # Preview sample image
    plt.imshow(test_image, cmap='gray')

    # Format Image
    img_resized = cv2.resize(test_image, (28, 28), interpolation=cv2.INTER_LINEAR)
    img_resized = cv2.bitwise_not(img_resized)

    # Preview reformatted image
    plt.imshow(img_resized, cmap='gray')
    model=MLP(784,10)
    if os.path.exists('tut1-model.pt'):
        model.load_state_dict(torch.load('tut1-model.pt',weights_only=True))
    else:
        print("Model not found")
        return
    pred , _ = model(torch.from_numpy(img_resized).float().unsqueeze(0)) # Convert img_resized to a PyTorch tensor
    print(F.softmax(pred,dim=1).argmax(1).item())

while(True):
    action=input("Enter\n 1. to showcase the model\n 2. to try the model\n 3. to exit\n")
    if action=="1":
        showcase()
    elif action=="2":
        trial()
    elif action=="3":
        exit()
    else:
        print("Invalid input")
