from gymnasium.envs.registration import register
'''
This script registers the custom environment "SPaRC-Gym" with Gymnasium.
'''
register(
    id="SPaRC-Gym",  # Unique identifier for your environment
    entry_point="SPaRC_Gym.SPaRC_Gym:SPaRC_Gym",  # Path to your environment class
)