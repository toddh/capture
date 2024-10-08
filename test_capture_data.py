import json
import datetime
from capture_data import CaptureData

def test_capture_data_initialization():
    capture_data = CaptureData()
    
    assert capture_data.capture_time is not None
    assert capture_data.pir_fired is None
    assert capture_data.object_detected is None
    assert capture_data.detected_objects == []

def test_capture_data_to_json():
    capture_data = CaptureData()
    capture_data.pir_fired = True
    capture_data.object_detected = True
    capture_data.detected_objects = [[10, 20, 30, 40, 'person', 0.95]]

    json_str = capture_data.to_json()
    data_dict = json.loads(json_str)

    assert data_dict['capture_time'] is not None
    assert data_dict['pir_fired'] == True
    assert data_dict['object_detected'] == True
    assert data_dict['detected_objects'] == [[10, 20, 30, 40, 'person', 0.95]]

def test_capture_data_to_short_string():
    capture_data = CaptureData()
    capture_data.pir_fired = True
    capture_data.object_detected = True
    capture_data.detected_objects = [[10, 20, 30, 40, 'person', 0.95]]
    capture_data.detected_objects.append([11, 12, 13, 14, 'deer', 0.65])

    str = capture_data.to_short_string()
    assert str == "PIR - Object - Classes: person, deer" 