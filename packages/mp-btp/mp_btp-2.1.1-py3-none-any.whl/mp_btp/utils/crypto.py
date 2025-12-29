import base64
def encode_config(text: str) -> str:
    b64 = base64.b64encode(text.encode()).decode()
    return b64[::-1]
def decode_config(encoded: str) -> str:
    reversed_b64 = encoded[::-1]
    return base64.b64decode(reversed_b64).decode()
if __name__ == "__main__":
    password = "abcde0230@T"
    uri = "postgresql://postgres.qcndlgxehjvlzbwrkszh:abcde0230%40T@aws-1-ap-southeast-1.pooler.supabase.com:6543/postgres"
    print("加密后的密码:")
    print(encode_config(password))
    print("\n加密后的 URI:")
    print(encode_config(uri))