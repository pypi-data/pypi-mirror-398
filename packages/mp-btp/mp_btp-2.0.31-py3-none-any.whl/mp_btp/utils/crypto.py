    b64 = base64.b64encode(text.encode()).decode()
    return b64[::-1]
def decode_config(encoded: str) -> str: