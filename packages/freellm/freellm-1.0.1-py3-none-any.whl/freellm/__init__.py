from .core import FreeLLM

__version__ = "1.0.1"
__author__ = "Free AI Community"
__doc__ = """
FreeLLM - The simplest Python client for free access to top-tier AI models (GPT-4.1 Nano, DeepSeek, Gemini Flash, Claude Haiku

Example:
    from freellm import FreeLLM
    bot = FreeLLM()
    print(bot.ask("Hello!"))
    print(bot.ask("What is my name?"))  # remembers!
"""
