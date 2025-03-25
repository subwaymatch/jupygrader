import base64


# Basic obfuscation by encoding the code in base64 and decoding it at runtime
def obfuscate_python_code(code: str) -> str:
    # Encode the code in base64
    encoded_code = base64.b64encode(code.encode("utf-8")).decode("utf-8")

    # Start building the obfuscated code
    obfuscated_code = "import base64 as _b64\n"

    # Create the base64 decoding part, with line breaks every 100 chars
    b64part = f"_64 = _b64.b64decode('{encoded_code}')\n"

    # Split long lines with continuation character
    chunks = [b64part[i : i + 100] for i in range(0, len(b64part), 100)]
    b64part = "\\\n".join(chunks)

    # Remove trailing backslash and newline if present
    if b64part.endswith("\\\n"):
        b64part = b64part[:-2] + "\n"

    obfuscated_code += b64part
    obfuscated_code += "eval(compile(_64, '<string>', 'exec'))"

    # Ensure each line ends with a newline
    obfuscated_code = "".join([line + "\n" for line in obfuscated_code.split("\n")])

    # Remove trailing whitespace
    obfuscated_code = obfuscated_code.rstrip()

    return obfuscated_code
