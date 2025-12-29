import math

def calc(sumable: str = None):
    if sumable is None or sumable == "":
        return "0"

    # Supported replacements
    replacements = {
        'X': '*',
        '^': '**',
        '%': '/100',
        'pi': str(math.pi),
        'e': str(math.e),
        '√': 'math.sqrt',
        'sin': 'math.sin',
        'cos': 'math.cos',
        'tan': 'math.tan',
        'log': 'math.log10',
        'ln': 'math.log'
    }

    processed = sumable.lower()
    for old, new in replacements.items():
        processed = processed.replace(old.lower(), new)
    
    try:
        # Use a safe-ish dict for eval, though still eval
        allowed_names = {"math": math, "__builtins__": {}}
        answer = eval(processed, allowed_names)
        return str(round(answer, 8)) if isinstance(answer, (int, float)) else str(answer)
    except Exception as e:
        return f"Error: {e}"


if __name__ == '__main__':
    result = calc()
    if result:
        print(result)
