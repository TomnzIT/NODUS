import requests

def generate_justification_llm(source_req, target_reqs, model="mistral", api_url="http://localhost:11434/api/generate"):
    prompt = (
        "Given the following source cybersecurity control and a set of target controls, "
        "explain why they are conceptually aligned. Then, identify what is missing or different in the target controls "
        "compared to the source control (gap analysis). Be concise, clear, and professional.\n\n"
        f"Source Control:\n{str(source_req)}\n\n"
        "Target Controls:\n" +
        "\n".join([f"- {str(t)}" for t in target_reqs]) +
        "\n\nJustification and Gap Analysis:"
    )

    try:
        response = requests.post(
            api_url,
            json={"model": model, "prompt": prompt, "stream": False},
            timeout=15
        )
        response.raise_for_status()
        data = response.json()
        if "response" not in data:
            return "LLM Error: No 'response' field in LLM reply."
        return data["response"].strip()

    except requests.exceptions.RequestException as e:
        return f"LLM Network Error: {e}"
    except Exception as e:
        return f"LLM Internal Error: {e}"