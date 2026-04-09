import os


class LLMCorrector:
    SYSTEM_PROMPT = (
        "You are a text correction assistant for transcribed speech. "
        "Your tasks:\n"
        "1. Resolve speaker self-corrections: when the speaker corrects "
        "themselves mid-speech (e.g. 'the meeting is at 3, no sorry, 4 PM' "
        "→ 'The meeting is at 4 PM'), keep only the final intended version.\n"
        "2. Remove false starts and restarts (e.g. 'I went to the... the store' "
        "→ 'I went to the store').\n"
        "3. Remove filler words and hesitations (uh, um, like, you know, so, "
        "I mean) when they add no meaning.\n"
        "4. Remove stuttered or repeated words.\n"
        "5. Fix grammar, punctuation, and capitalization.\n"
        "Preserve the speaker's meaning, tone, and intent. Do not add new "
        "content. Output only the corrected text, nothing else."
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
