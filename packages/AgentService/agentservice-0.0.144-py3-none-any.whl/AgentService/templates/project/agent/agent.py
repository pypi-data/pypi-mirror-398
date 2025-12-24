
from AgentService.agent import Agent


class AgentModel(Agent):
    model = "gpt-4.1-nano"
    temperature = 1.0
    max_tokens = 2048
    top_p = 1.0

    system_prompt = "You are a helpful assistant"
    prompt = "{text}"

    is_one_shot = False
