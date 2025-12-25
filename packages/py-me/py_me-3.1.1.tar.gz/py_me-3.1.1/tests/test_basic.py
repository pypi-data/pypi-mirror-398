import pytest
from py_me import music_me

def test_import_music_me():
    # Testa se o módulo importa sem erros
    assert music_me is not None

def test_dummy_function():
    # Teste exemplo de função simples
    x = 2 + 2
    assert x == 4