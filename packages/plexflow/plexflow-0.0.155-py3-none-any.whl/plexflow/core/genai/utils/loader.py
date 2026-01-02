

def load_preamble(name: str):
    with open(f"config/genai/{name}.txt", "r") as file:
        return file.read()