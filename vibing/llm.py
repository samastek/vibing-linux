import os


class LLMCorrector:
    SYSTEM_PROMPT = (
        "You are a text correction assistant. "
        "Fix grammar, punctuation, and capitalization in the user's transcribed speech. "
        "Do not change the meaning, tone, or intent. Do not add new content. "
        "Output only the corrected text, nothing else."
    )

    def __init__(self, model_path, n_gpu_layers=-1, n_ctx=2048):
        from llama_cpp import Llama

        model_path = os.path.expanduser(model_path)
        if not os.path.isfile(model_path):
            raise FileNotFoundError(
                f"LLM model not found: {model_path}\n"
                "Download a GGUF model and set llm.model_path in config."
            )

        print(f"Loading LLM: {model_path}...")
        self.llm = Llama(
            model_path=model_path,
            n_gpu_layers=n_gpu_layers,
            n_ctx=n_ctx,
            verbose=False,
        )
        print("LLM loaded.")

    def correct(self, text, temperature=0.3):
        if not text.strip():
            return text
        response = self.llm.create_chat_completion(
            messages=[
                {"role": "system", "content": self.SYSTEM_PROMPT},
                {"role": "user", "content": text},
            ],
            temperature=temperature,
            max_tokens=max(len(text.split()) * 3, 256),
        )
        corrected = response["choices"][0]["message"]["content"].strip()
        return corrected if corrected else text
