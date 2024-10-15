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
        self.memory = {}  # Use a dictionary to store experiences per ant
        self.gamma = 0.99
        # self.batch_size = 100

    def select_action(self, ant_id, state, possible_actions):
        state_tensor = torch.FloatTensor(state).to(device)
        action_logits = []
        for action in possible_actions:
            action_features = action['features']
            input_tensor = torch.cat([state_tensor, torch.FloatTensor(action_features).to(device)])
            logit = self.policy_net(input_tensor)
            action_logits.append(logit)
        action_logits = torch.stack(action_logits).squeeze(-1)
        action_probs = torch.softmax(action_logits, dim=0)
        if self.is_eval:
            action_index = torch.argmax(action_probs).item()
            log_prob = None
        else:
            action_distribution = torch.distributions.Categorical(action_probs)
            action_index = action_distribution.sample()
            log_prob = action_distribution.log_prob(action_index)
            # Store action in the ant's own memory
            if ant_id not in self.memory:
                self.memory[ant_id] = []
            self.memory[ant_id].append({'log_prob': log_prob, 'reward': None})
            # print(f"[Debug] Ant {ant_id}: Stored action {action_index} with log_prob {log_prob.item():.4f}")
        return action_index, log_prob

    def store_reward(self, ant_id, reward):
        if self.is_eval:
            return  # Do not store rewards during evaluation
        if ant_id in self.memory and self.memory[ant_id] and self.memory[ant_id][-1]['reward'] is None:
            self.memory[ant_id][-1]['reward'] = reward
            # print(f"[Debug] Ant {ant_id}: Stored reward {reward} for action at index {len(self.memory[ant_id]) - 1}")
        # else:
        #     print(f"[Debug] Ant {ant_id}: No action to assign reward to, or the reward is already assigned.")

    def update_policy(self):
        if self.is_eval:
            return  # Do not update policy during evaluation
        
        # Combine experiences from all ants
        combined_memory = []
        for ant_id, ant_memory in self.memory.items():
            combined_memory.extend(ant_memory)
        
        # Proceed only if there are any experiences
        if not combined_memory:
            print("[Debug] No experiences to update policy.")
            return
            
        # Filter out steps with no rewards
        filtered_memory = [step for step in combined_memory if step['reward'] is not None]
        if not filtered_memory:
            print("[Debug] No valid experiences with rewards. Skipping update.")
            return  # If no steps have rewards, skip the update

        print(f"[Debug] Proceeding with {len(filtered_memory)} valid experiences for policy update.")
        
        # Proceed with policy update
        R = 0
        returns = []
        for step in reversed(filtered_memory):
            R = step['reward'] + self.gamma * R
            returns.insert(0, R)
        returns = torch.tensor(returns).to(device)
        
        # Normalize returns
        returns = (returns - returns.mean()) / (returns.std() + 1e-9)
        
        # Compute policy loss
        policy_loss = []
        for i, step in enumerate(filtered_memory):
            log_prob = step['log_prob']
            if log_prob is not None:
                R = returns[i]
                # Make sure log_prob is a 1-dimensional tensor
                log_prob = log_prob.view(1)
                policy_loss.append(-log_prob * R)
        
        if policy_loss:
            # Perform policy update
            self.optimizer.zero_grad()
            policy_loss = torch.cat(policy_loss).sum()
            policy_loss.backward()
            self.optimizer.step()
            print(f"[Debug] Policy updated. Loss: {policy_loss.item():.4f}")
        else:
            print("[Debug] No valid policy loss to update.")
        
        # Clear memory
        self.memory = {}






    def save_model(self, file_path):
        torch.save(self.policy_net.state_dict(), file_path)
        print(f"Model saved to {file_path}")

    def load_model(self, file_path):
        self.policy_net.load_state_dict(torch.load(file_path, map_location=device))
        self.policy_net.eval()  # Set the network to evaluation mode
        self.is_eval = True  # Set evaluation flag
        print(f"Model loaded from {file_path}")
