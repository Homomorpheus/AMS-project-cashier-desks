# AMS-project-cashier-desks
ABM+DES simulation of supermarket cashier desks and their queues

An overview of the most important files contained in this repo:

In the directory Discrete Event Simulation:
- **/des_task1.py**: Discrete event simulation of the queue model
In the directory Agent_Based_Modelling:
- **agents.py** and **events.py**: Heart of the agent-based simulation, containing the logic
- **mc_statistics.py**: The best place to try out simulation parameters
- **sa.py**: Implementation of stochastic approximation
- **fitting.py**: Logic for calibration to [call center dataset](www.kaggle.com/datasets/donovanbangs/call-centre-queue-simulation)
