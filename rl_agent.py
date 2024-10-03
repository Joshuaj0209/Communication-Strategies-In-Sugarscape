import torch
import torch.nn as nn
import torch.optim as optim
import random
from collections import deque
import numpy as np

print(torch.cuda.is_available())
print(torch.cuda.get_device_name(0))

# Set up the device
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
print("device: ", device)

class NeuralNetwork(nn.Module):
    def __init__(self, state_size, action_size):
        super(NeuralNetwork, self).__init__()
        self.fc1 = nn.Linear(state_size, 128)
        self.fc2 = nn.Linear(128, 128)
        self.fc3 = nn.Linear(128, action_size)
    
    def forward(self, x):
        x = torch.relu(self.fc1(x))
        x = torch.relu(self.fc2(x))
        x = self.fc3(x)
        return x

class AntRLAgent:
    def __init__(self, state_size, action_size):
        self.is_eval = False  # Add this line

        self.state_size = state_size
        self.action_size = action_size

        # Move models to device
        self.policy_net = NeuralNetwork(state_size, action_size).to(device)
        self.target_net = NeuralNetwork(state_size, action_size).to(device)
        self.target_net.load_state_dict(self.policy_net.state_dict())
        self.target_net.eval()

        self.optimizer = optim.Adam(self.policy_net.parameters(), lr=1e-3)
        self.criterion = nn.MSELoss()

        self.memory = deque(maxlen=50000)  # Experience replay buffer
        self.batch_size = 128
        self.gamma = 0.99  # Discount factor
        self.epsilon = 1.0  # Exploration rate
        self.epsilon_min = 0.1
        self.epsilon_decay = 0.995
        self.update_target_every = 1000  # Steps
        self.steps_done = 0

    def select_action(self, state):
        if self.is_eval:
            epsilon = 0.0  # No exploration during evaluation
        else:
            epsilon = self.epsilon

        if random.random() < epsilon:
            # Explore: select a random action
            return random.randrange(self.action_size)
        else:
            # Exploit: select the action with max Q-value
            state_tensor = torch.FloatTensor(state).unsqueeze(0).to(device)
            with torch.no_grad():
                q_values = self.policy_net(state_tensor)
            action = torch.argmax(q_values).item()
            return action

    def store_experience(self, state, action, reward, next_state, done):
        if self.is_eval:
            return  # Do not store experiences during evaluation
        self.memory.append((state, action, reward, next_state, done))

    def update_policy(self):
        if self.is_eval:
            return  # Do not update policy during evaluation

        if len(self.memory) < self.batch_size:
            return  # Not enough experiences to train

        # Sample a batch of experiences
        batch = random.sample(self.memory, self.batch_size)
        states, actions, rewards, next_states, dones = zip(*batch)

        # Convert to tensors and move to device
        states = torch.FloatTensor(np.array(states)).to(device)
        actions = torch.LongTensor(actions).unsqueeze(1).to(device)
        rewards = torch.FloatTensor(rewards).unsqueeze(1).to(device)
        next_states = torch.FloatTensor(np.array(next_states)).to(device)
        dones = torch.FloatTensor(dones).unsqueeze(1).to(device)

        # Compute Q-values
        q_values = self.policy_net(states).gather(1, actions)

        # Compute target Q-values
        with torch.no_grad():
            next_q_values = self.target_net(next_states).max(1)[0].unsqueeze(1)
            target_q_values = rewards + (self.gamma * next_q_values * (1 - dones))

        # Compute loss
        loss = self.criterion(q_values, target_q_values)

        # Optimize the model
        self.optimizer.zero_grad()
        loss.backward()
        self.optimizer.step()

        # Update target network
        self.steps_done += 1  # Increment steps_done
        if self.steps_done % self.update_target_every == 0:
            self.target_net.load_state_dict(self.policy_net.state_dict())

        # Decay epsilon
        if self.epsilon > self.epsilon_min:
            self.epsilon *= self.epsilon_decay

    def save_model(self, file_path):
        torch.save(self.policy_net.state_dict(), file_path)
        print(f"Model saved to {file_path}")

    def load_model(self, file_path):
        self.policy_net.load_state_dict(torch.load(file_path, map_location=device))
        self.policy_net.eval()  # Set the network to evaluation mode
        self.is_eval = True  # Set evaluation flag
        print(f"Model loaded from {file_path}")
