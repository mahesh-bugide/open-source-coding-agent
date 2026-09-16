def render_greeting(name: str, excited: bool = False) -> str:
    base = f"Hello, {name}"
    if excited:
        return base + "!"
    return base
