"""
This module initializes the SPaRC environment package.

It imports the `SPaRC_Gym` class and registers the environment for use with Gymnasium.

Modules:
    - gym_SPaRC: Contains the implementation of the SPaRC environment.
    - register_env: Handles the registration of the SPaRC environment with Gymnasium.
"""

from .SPaRC_Gym import SPaRC_Gym
from .register_env import *