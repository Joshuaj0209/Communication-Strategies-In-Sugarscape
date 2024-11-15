This project contains multiple files split up into 2 sections "RL Simulation" and "Rule Based Simulation". 

To run these simulations, each folder contains a `run_simulation.py` file that you can run to view the visualisation of the Sugarscape environment. Initially, all simulations are set to run the Widespread Broadcasting simulation. To change this to Face-to-Face, please do the following:

In `Rule Based Simulation`:
1. In `constants.py`, change "COMMUNICATION_RADIUS" to 80

In `RL Simulation`:
1. In `constants.py`, change "COMMUNICATION_RADUIS" to 80
2. In `run_simulation.py`, change "Broadcast_trained.pth" to "Face_trained.pth"
