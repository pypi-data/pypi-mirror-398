import gymnasium as gym

from konic.agent import KonicAgent
from konic.runtime import register_agent

env = gym.make("CartPole-v1")
agent = KonicAgent(environment=env)

register_agent(agent, name="{{cookiecutter.name.replace(' ', '-').lower()}}")
