import json
import datetime
from capture_data import CaptureData

# To run this
# pytest -v test_capture_data.py

def test_capture_data_initialization():
    capture_data = CaptureData()
    
    assert capture_data.capture_time is not None
    assert capture_data.pir_fired is None
    assert capture_data.object_detected is None
    assert capture_data.rectangles == []
    assert capture_data.scores == []
    assert capture_data.classes == []

def test_capture_data_to_json():
    capture_data = CaptureData()
    capture_data.pir_fired = True
    capture_data.object_detected = True

    capture_data.rectangles.append([10, 20, 30, 40])
    capture_data.scores.append(0.95)
    capture_data.classes.append('person')

    capture_data.rectangles.append([11, 12, 13, 14])
    capture_data.scores.append(0.85)
    capture_data.classes.append('deer')

    json_str = capture_data.to_json()
    data_dict = json.loads(json_str)

    assert data_dict['capture_time'] is not None
    assert data_dict['pir_fired'] == True
    assert data_dict['object_detected'] == True
    assert data_dict['rectangles'] == [[10, 20, 30, 40], [11, 12, 13, 14]]
    assert data_dict['scores'] == [0.95, 0.85]
    assert data_dict['classes'] == ['person', 'deer']

def test_capture_data_to_short_string():
    capture_data = CaptureData()
    capture_data.pir_fired = True
    capture_data.object_detected = True

    capture_data.rectangles.append([10, 20, 30, 40])
    capture_data.scores.append(0.95)
    capture_data.classes.append('person')

    capture_data.rectangles.append([11, 12, 13, 14])
    capture_data.scores.append(0.85)
    capture_data.classes.append('deer')

    str = capture_data.to_short_string()
    assert str == "PIR - Object - Classes: ['person', 'deer']"