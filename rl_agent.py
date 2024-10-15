import torch
import torch.nn as nn
import torch.optim as optim
import random
import numpy as np

# Set up the device
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
print("device: ", device)

class PolicyNetwork(nn.Module):
    def __init__(self, input_size):
        super(PolicyNetwork, self).__init__()
        self.fc1 = nn.Linear(input_size, 128)
        self.fc2 = nn.Linear(128, 128)
        self.fc3 = nn.Linear(128, 1)  # Output a scalar logit
        
    def forward(self, x):
        x = torch.relu(self.fc1(x))
        x = torch.relu(self.fc2(x))
        logit = self.fc3(x)
        return logit


class AntRLAgent:
    def __init__(self, input_size):
        self.is_eval = False
        self.policy_net = PolicyNetwork(input_size).to(device)
        self.optimizer = optim.Adam(self.policy_net.parameters(), lr=1e-3)
        self.memory = []
        self.gamma = 0.99
        self.batch_size = 128

    def select_action(self, state, possible_actions):
        state_tensor = torch.FloatTensor(state).to(device)
        action_logits = []
        for action in possible_actions:
            action_features = action['features']
            input_tensor = torch.cat([state_tensor, torch.FloatTensor(action_features).to(device)])
            logit = self.policy_net(input_tensor)
            action_logits.append(logit)
        action_logits = torch.stack(action_logits).squeeze()
        action_probs = torch.softmax(action_logits, dim=0)
        if self.is_eval:
            action_index = torch.argmax(action_probs).item()
            log_prob = None
        else:
            action_distribution = torch.distributions.Categorical(action_probs)
            action_index = action_distribution.sample()
            log_prob = action_distribution.log_prob(action_index)
            self.memory.append({'log_prob': log_prob, 'reward': None})
        return action_index, log_prob


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
