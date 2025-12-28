from .core import FreeLlama

__version__ = "1.0.0"
__author__ = "Free AI Community"
__doc__ = """
FreeLlama - The simplest way to use Llama-3.3-70B for free

Example:
    from freellama import FreeLlama
    bot = FreeLlama()
    print(bot.ask("Hello!"))
    print(bot.ask("What is my name?"))  # remembers!
"""
