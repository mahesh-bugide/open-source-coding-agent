from src.features.greeting import render_greeting


def test_greeting_default() -> None:
    assert render_greeting("Ava") == "Hello, Ava"


def test_greeting_excited() -> None:
    assert render_greeting("Ava", excited=True) == "Hello, Ava!"
