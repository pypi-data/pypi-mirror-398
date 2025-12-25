"""
When you install and import this library, it will automatically hook
openai.ChatCompletion.create using wrapt, and log token usage after
each request. You can customize or extend this logging logic later
to add user or organization metadata for metering purposes.
"""
from .middleware import create_wrapper