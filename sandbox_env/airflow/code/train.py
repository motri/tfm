import torch
import torch.nn as nn
import torch.optim as optim
import torchvision.transforms as transforms
import torchvision.datasets as datasets
from torch.utils.data import DataLoader
import os
import mlflow
import mlflow.pytorch

# Check if CUDA is available, but force CPU use
DEVICE = torch.device("cpu")
print(f"Using device: {DEVICE}")

mlflow.set_tracking_uri(uri="http://mlflow.zylk.mrrobot.vicomtech.es")
mlflow.set_experiment("MLflow Quickstart")

# Enable MLflow autologging for PyTorch
mlflow.pytorch.autolog()

# Define a simple CNN model
class SimpleCNN(nn.Module):
    def __init__(self):
        super(SimpleCNN, self).__init__()
        self.conv1 = nn.Conv2d(3, 16, kernel_size=3, padding=1)
        self.conv2 = nn.Conv2d(16, 32, kernel_size=3, padding=1)
        self.pool = nn.MaxPool2d(2, 2)
        self.fc1 = nn.Linear(32 * 8 * 8, 128)
        self.fc2 = nn.Linear(128, 10)
        self.relu = nn.ReLU()
        self.softmax = nn.LogSoftmax(dim=1)

    def forward(self, x):
        x = self.pool(self.relu(self.conv1(x)))
        x = self.pool(self.relu(self.conv2(x)))
        x = x.view(-1, 32 * 8 * 8)
        x = self.relu(self.fc1(x))
        x = self.softmax(self.fc2(x))
        return x

# Data transformations
transform = transforms.Compose([
    transforms.Resize((32, 32)),
    transforms.ToTensor(),
    transforms.Normalize((0.5, 0.5, 0.5), (0.5, 0.5, 0.5))
])

# Load dataset (CIFAR-10 as example)
train_dataset = datasets.CIFAR10(root='./data', train=True, download=True, transform=transform)
test_dataset = datasets.CIFAR10(root='./data', train=False, download=True, transform=transform)

train_loader = DataLoader(train_dataset, batch_size=32, shuffle=True)
test_loader = DataLoader(test_dataset, batch_size=32, shuffle=False)

# Initialize model, loss function, and optimizer
model = SimpleCNN().to(DEVICE)
criterion = nn.CrossEntropyLoss()
optimizer = optim.Adam(model.parameters(), lr=0.001)

# Training loop with MLflow logging
def train_model(num_epochs=1):
    with mlflow.start_run():  # Start a new MLflow run
        for epoch in range(num_epochs):
            running_loss = 0.0
            for images, labels in train_loader:
                images, labels = images.to(DEVICE), labels.to(DEVICE)
                optimizer.zero_grad()
                outputs = model(images)
                loss = criterion(outputs, labels)
                loss.backward()
                optimizer.step()
                running_loss += loss.item()

            avg_loss = running_loss / len(train_loader)
            print(f"Epoch {epoch+1}, Loss: {avg_loss:.4f}")
            mlflow.log_metric("loss", avg_loss, step=epoch)  # Log the loss for each epoch

        print("Training complete!")

        # Log the model with MLflow
        mlflow.pytorch.log_model(model, "model")

if __name__ == "__main__":
    train_model(5)
