# Risk-Averse Distributional Reinforcement Learning

This is a fork from [this repository](https://github.com/Silvicek/cvar-algorithms). We use their implementation of CVaR Policy Iteration (Chow. et. al. 2015) as baseline in some figures the paper. The figure display the CVaR(0.01) optimal path from the starting point (upper-left corner) to the goal (upper right corner) in an environment with probability of random action p (we use 0.05 and 0.1). Code to generate the figures is in ``results`` notebook, figures are in ``./figures`` folder and saved result used in the paper are in ``./cvar/gridworld/results folder``.

![Optimal Path](figures/CVAR_optimal_0.01_0.05.png)


## Installation

Install tensorflow by following instructions in https://www.tensorflow.org/install/
Using GPU during training is highly recommended (but not required)

    pip3 install tensorflow-gpu


Install the cvar package (from ./cvar-algorithms directory)

    pip3 install -e .

### CVaR Value Iteration

The fork aims to run on a LavaGridworld of 10x7 tiles with probability of random action p (either 0.1 or 0.05 in the figures).

For CVaR Value Iteration run (from ./cvar-algorithms/cvar/gridworld directory)

    python3 run_vi.py



