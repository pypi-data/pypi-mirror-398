import base64


def save_temp_file(file_name: str, data: str) -> str:
    file_bytes = base64.b64decode(data)

    with open(file_name, "wb") as f:
        f.write(file_bytes)