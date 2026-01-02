# llm.py
from abc import ABC, abstractmethod
from transformers import pipeline
import torch

class LLMBackend(ABC):
    @abstractmethod
    def generate(self, prompt: str) -> str:
        pass

    def explain(self, prompt: str) -> str:
        """Return explanation as markdown"""
        return self.generate(prompt)


class StubLLM(LLMBackend):
    def generate(self, prompt: str) -> str:
        return (
            "# Purpose\nStub explanation (LLM disabled)\n\n"
            "# Inputs\n\n# Outputs\n\n# Assumptions\n\n"
            "# Side Effects\n\n# Failure Modes\n\n# Risk Level\nMedium"
        )


class LocalHFLLM(LLMBackend):
    def __init__(self, model_name: str, device: str = "cpu"):
        if device == "cuda" and torch.cuda.is_available():
            device_id = 0
        else:
            device_id = -1  # CPU fallback

        self.pipe = pipeline(
            "text-generation",
            model=model_name,
            device=device_id,
        )

    def generate(self, prompt: str) -> str:
        output = self.pipe(
            prompt,
            max_new_tokens=1024,
            do_sample=True,
            temperature=0.7,
            top_p=0.8,
            top_k=20,
        )[0]["generated_text"]
    
        if output.startswith(prompt):
            output = output[len(prompt):].strip()
        return output