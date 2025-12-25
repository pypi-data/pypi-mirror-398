import openai
import os
from .config import Config
from .pricing import PRICING_RATES

import datetime

class Agent:
    def __init__(self, system_prompt="You are a helpful assistant."):
        self.system_prompt = system_prompt
        self.model = Config.MODEL
        self.api_key = Config.API_KEY
        
        # Initialize the client based on provider
        if Config.PROVIDER == "openai":
            self.client = openai.OpenAI(api_key=self.api_key)
        else:
            # You can extend this for other providers like Anthropic, etc.
            raise ValueError(f"Unsupported provider: {Config.PROVIDER}")

    def process(self, user_instructions, content_to_manipulate):
        """
        Sends the instructions and content to the LLM.
        """
        # Construct the message
        # We present the user instructions and the content clearly to the model
        full_prompt = f"""
Instructions:
{user_instructions}

---
Content to Process:
{content_to_manipulate}
"""

        messages = [
            {"role": "system", "content": self.system_prompt},
            {"role": "user", "content": full_prompt}
        ]

        response = self.client.chat.completions.create(
            model=self.model,
            messages=messages
        )

        if response.usage:
            self._log_cost_analysis(response.usage)

        return response.choices[0].message.content

    def chat(self, context_files, initial_prompt=None):
        """
        Starts an interactive chat session with the provided files as context.
        """
        messages = [{"role": "system", "content": self.system_prompt}]
        
        # Build context from files
        if context_files:
            context_str = "Context:\n"
            for file_path, content in context_files.items():
                context_str += f"File: {file_path}\n```\n{content}\n```\n\n"
            messages.append({"role": "user", "content": f"Here is the context for our conversation:\n{context_str}"})
        
        # If there's an initial prompt, send it
        if initial_prompt:
             messages.append({"role": "user", "content": initial_prompt})
             self._chat_turn(messages)

        # Start REPL
        print("Starting chat session. Type 'exit' or 'quit' to end.")
        while True:
            try:
                user_input = input(">> ")
                if user_input.lower() in ['exit', 'quit']:
                    break
                
                messages.append({"role": "user", "content": user_input})
                self._chat_turn(messages)
                
            except KeyboardInterrupt:
                print("\nExiting chat...")
                break
            except EOFError:
                print("\nExiting chat...")
                break

    def _chat_turn(self, messages):
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages
            )
            
            if response.usage:
                self._log_cost_analysis(response.usage)
                
            content = response.choices[0].message.content
            print(f"\n{content}\n")
            messages.append({"role": "assistant", "content": content})
            
        except Exception as e:
            print(f"Error: {e}")

    def _log_cost_analysis(self, usage):
        # Pricing per 1M tokens (USD)
        pricing = PRICING_RATES

        # Handle model versions (e.g., gpt-4o-2024-05-13) by matching prefix
        model_key = self.model
        if model_key not in pricing:
            for key in pricing:
                if self.model.startswith(key):
                    model_key = key
                    break
        
        log_entry = [
            f"--- Usage Report ({datetime.datetime.now().isoformat()}) ---",
            f"Model: {self.model}",
            f"Input Tokens:  {usage.prompt_tokens}",
            f"Output Tokens: {usage.completion_tokens}",
            f"Total Tokens:  {usage.total_tokens}"
        ]

        if model_key in pricing:
            rates = pricing[model_key]
            input_cost = (usage.prompt_tokens / 1_000_000) * rates["input"]
            output_cost = (usage.completion_tokens / 1_000_000) * rates["output"]
            total_cost = input_cost + output_cost
            log_entry.append(f"Estimated Cost: ${total_cost:.6f}")
        else:
            log_entry.append("Cost estimation not available for this model.")
        
        log_entry.append("-" * 30 + "\n")

        try:
            log_dir = os.path.expanduser("~/.llm-editor/logs")
            os.makedirs(log_dir, exist_ok=True)
            log_file = os.path.join(log_dir, "usage.log")
            with open(log_file, "a", encoding="utf-8") as f:
                f.write("\n".join(log_entry))
        except Exception as e:
            print(f"DEBUG: Logging failed: {e}")
            # Fail silently on logging errors to avoid disrupting the main flow
        except Exception as e:
            # Fail silently on logging errors to avoid disrupting the main flow
            pass
