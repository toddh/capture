# To run this
# pytest -v test_stop_list.py

import pytest
from stop_list import StopList

def test_stop_list_initialization():
    stop_list = StopList()
    assert stop_list.stop_list is None

def test_set_stop_list():
    stop_list = StopList()
    test_list = ['stop', 'halt', 'cease']
    stop_list.set_stop_list(test_list)
    assert stop_list.stop_list == test_list

def test_in_stop_list():
    stop_list = StopList()
    stop_list.set_stop_list(['stop', 'halt', 'cease'])
    word = 'stop'
    assert stop_list.is_in_stop_list(word) == True

def test_not_in_stop_list():
    stop_list = StopList()
    stop_list.set_stop_list(['stop', 'halt', 'cease'])
    word = 'go'
    assert stop_list.is_in_stop_list(word) == False

