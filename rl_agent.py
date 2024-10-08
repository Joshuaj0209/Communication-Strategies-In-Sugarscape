import torch
import torch.nn as nn
import torch.optim as optim
import random
import numpy as np

# Set up the device
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
print("device: ", device)

class PolicyNetwork(nn.Module):
    def __init__(self, state_size, action_size):
        super(PolicyNetwork, self).__init__()
        self.fc1 = nn.Linear(state_size, 128)
        self.fc2 = nn.Linear(128, 128)
        self.fc3 = nn.Linear(128, action_size)
        
    def forward(self, x):
        x = torch.relu(self.fc1(x))
        x = torch.relu(self.fc2(x))
        action_scores = self.fc3(x)
        action_probs = torch.softmax(action_scores, dim=-1)
        return action_probs

class AntRLAgent:
    def __init__(self, state_size, action_size):
        self.is_eval = False
        self.state_size = state_size
        self.action_size = action_size
        self.policy_net = PolicyNetwork(state_size, action_size).to(device)
        self.optimizer = optim.Adam(self.policy_net.parameters(), lr=1e-3)
        self.memory = []  # Shared memory for all ants
        self.gamma = 0.99  # Discount factor
        self.batch_size = 128  # Number of experiences before updating policy

    def select_action(self, state):
        state_tensor = torch.FloatTensor(state).unsqueeze(0).to(device)
        action_probs = self.policy_net(state_tensor)
        if self.is_eval:
            action = torch.argmax(action_probs, dim=-1).item()
        else:
            action_distribution = torch.distributions.Categorical(action_probs)
            action = action_distribution.sample()
            log_prob = action_distribution.log_prob(action)
            # Store the log probability for later
            self.memory.append({'log_prob': log_prob, 'reward': None})
            action = action.item()
        return action

    def store_reward(self, reward):
        if self.is_eval:
            return  # Do not store rewards during evaluation
        if self.memory and self.memory[-1]['reward'] is None:
            self.memory[-1]['reward'] = reward

    def update_policy(self):
        if self.is_eval:
            return  # Do not update policy during evaluation
        if len(self.memory) < self.batch_size:
            return  # Not enough experiences to perform update
        # Check that all rewards are available
        if any(step['reward'] is None for step in self.memory):
            return  # Wait until all rewards are available
        # Proceed with policy update
        memory = self.memory
        R = 0
        returns = []
        for step in reversed(memory):
            R = step['reward'] + self.gamma * R
            returns.insert(0, R)
        returns = torch.tensor(returns).to(device)
        # Normalize returns
        returns = (returns - returns.mean()) / (returns.std() + 1e-9)
        # Compute policy loss
        policy_loss = []
        for i, step in enumerate(memory):
            log_prob = step['log_prob']
            R = returns[i]
            policy_loss.append(-log_prob * R)
        # Perform policy update
        self.optimizer.zero_grad()
        policy_loss = torch.cat(policy_loss).sum()
        policy_loss.backward()
        self.optimizer.step()
        # Clear memory
        self.memory = []


    def save_model(self, file_path):
        torch.save(self.policy_net.state_dict(), file_path)
        print(f"Model saved to {file_path}")

    def load_model(self, file_path):
        self.policy_net.load_state_dict(torch.load(file_path, map_location=device))
        self.policy_net.eval()  # Set the network to evaluation mode
        self.is_eval = True  # Set evaluation flag
        print(f"Model loaded from {file_path}")
