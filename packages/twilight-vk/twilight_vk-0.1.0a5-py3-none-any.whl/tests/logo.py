import pytest

from twilight_vk.components.logo import LogoComponent

def test_logo():
    logo = LogoComponent()
    logo.printAll()