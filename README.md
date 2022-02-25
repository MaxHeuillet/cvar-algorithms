# Risk-Averse Distributional Reinforcement Learning

This is a fork from [this repository](https://github.com/Silvicek/cvar-algorithms). It contains an implementation of CVaR Policy Iteration (Chow. et. al. 2015) that was used in some figures the paper.

## Installation

Install tensorflow by following instructions in https://www.tensorflow.org/install/
Using GPU during training is highly recommended (but not required)

    pip3 install tensorflow-gpu

Next install [OpenAI baselines](https://github.com/Silvicek/baselines)

    git clone https://github.com/Silvicek/baselines.git
    cd PyGame-Learning-Environment/
    pip3 install -e .

Next install the [Pygame Learning Environment](https://github.com/ntasfi/PyGame-Learning-Environment)
    
    git clone https://github.com/ntasfi/PyGame-Learning-Environment.git
    cd PyGame-Learning-Environment/
    pip3 install -e .

Lastly, install the cvar package (from cvar-algorithms)

    pip3 install -e .

### CVaR Value Iteration

The fork aims is ran on a LavaGridworld of 10x7 tiles with probability of random action p=0.1.

For CVaR Value Iteration run

    python3 run_vi.py



