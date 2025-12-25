from gymnasium.envs.registration import register
'''
This script registers the custom environment "Witness-v0" with Gymnasium.
'''
register(
    id="SPaRC-Gym",  # Unique identifier for your environment
    entry_point="gymnasium_env_for_SPaRC.gym_env_for_SPaRC:GymEnvSPaRC",  # Path to your environment class
)