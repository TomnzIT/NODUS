import os
import requests

# URL de l'API Ollama (par défaut sur le service docker 'ollama')
OLLAMA_URL = os.getenv("OLLAMA_BASE_URL", "http://ollama:11434")

if "localhost" in os.environ.get("DEV_MODE", ""):
    OLLAMA_URL = "http://localhost:11434"

def generate_justification_llm(source_req, target_reqs, model="mistral"):
    prompt = (
        "Given the following source cybersecurity control and a set of target controls, "
        "briefly explain why they are conceptually aligned. Identify any notable gaps as well.\n\n"
        f"Source Control:\n{str(source_req)}\n\n"
        "Target Controls:\n" +
        "\n".join([f"- {str(t)}" for t in target_reqs]) +
        "\n\nJustification and Gap:"
    )

    headers = {"Content-Type": "application/json"}

    try:
        # Affiche dans les logs Docker que la requête est envoyée
        print(f"[LLM] Sending prompt to {OLLAMA_URL}")

        response = requests.post(
            f"{OLLAMA_URL}/api/generate",
            json={"model": model, "prompt": prompt, "stream": False},
            headers=headers,
            timeout=30
        )
        response.raise_for_status()
        return response.json().get("response", "").strip()

    except Exception as e:
        return f"LLM Network Error: {e}"