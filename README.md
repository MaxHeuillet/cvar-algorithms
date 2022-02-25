# Risk-Averse Distributional Reinforcement Learning

This is a fork from [this repository](https://github.com/Silvicek/cvar-algorithms) that contains an implementation of CVaR Policy Iteration (Chow. et. al. 2015) that was used in some figures the paper. See the figure:

![Optimal Path](figures/CVAR_optimal_0.01_0.05.png)


## Installation

Install tensorflow by following instructions in https://www.tensorflow.org/install/
Using GPU during training is highly recommended (but not required)

    pip3 install tensorflow-gpu


Install the cvar package (from ./cvar-algorithms directory)

    pip3 install -e .

### CVaR Value Iteration

The fork aims is ran on a LavaGridworld of 10x7 tiles with probability of random action p=0.1.

For CVaR Value Iteration run (from ./cvar-algorithms/cvar/gridworld directory)

    python3 run_vi.py



