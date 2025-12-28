
from a2a_llm_tracker import Meter, PricingRegistry
from a2a_llm_tracker.sinks.sqlite import SQLiteSink
from a2a_llm_tracker.integrations.litellm import LiteLLM


def testing_registry():
    pricing = PricingRegistry()
    pricing.set_price("openai", "openai/gpt-4.1", input_per_million=2.0, output_per_million=8.0)
    llm = LiteLLM(meter=meter)




