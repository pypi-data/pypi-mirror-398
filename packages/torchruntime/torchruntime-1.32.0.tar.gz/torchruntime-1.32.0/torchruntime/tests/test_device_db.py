from torchruntime.device_db import parse_windows_output, parse_linux_output, parse_macos_output


def test_parse_windows_output():
    output = """
    PCI\\VEN_8086&DEV_591B&SUBSYS_2212103C&REV_04
    PCI\\VEN_10DE&DEV_1C82&SUBSYS_37131462&REV_A1
    PCI\\VEN_10DE&DEV_2504&SUBSYS_881D1043&REV_A1\\4&22AF55FA&0&0008
    """
    expected = [("8086", "591b"), ("10de", "1c82"), ("10de", ("2504"))]
    assert sorted(parse_windows_output(output)) == sorted(expected)


def test_parse_linux_output():
    output = """
    00:02.0 VGA compatible controller: Intel Corporation HD Graphics 620 (rev 02) [8086:5916]
    01:00.0 3D controller: NVIDIA Corporation GP108M [GeForce MX150] (rev a1) [10de:1d10]
    """
    expected = [("8086", "5916"), ("10de", "1d10")]
    assert sorted(parse_linux_output(output)) == sorted(expected)


def test_parse_macos_output():
    output = """
    {
        "SPDisplaysDataType": [
            {
                "spdisplays_vendor": "Intel",
                "spdisplays_device-id": "0x5916"
            },
            {
                "spdisplays_vendor": "NVIDIA (0x10de)",
                "spdisplays_device-id": "0x1c82"
            }
        ]
    }
    """
    expected = [("8086", "5916"), ("10de", "1c82")]
    assert sorted(parse_macos_output(output)) == sorted(expected)


def test_parse_two_gpus_of_same_model_output():
    output = """
    00:02.0 3D controller: NVIDIA Corporation GP108M [GeForce MX150] (rev a1) [10de:1d10]
    01:00.0 3D controller: NVIDIA Corporation GP108M [GeForce MX150] (rev a1) [10de:1d10]
    """
    expected = [("10de", "1d10"), ("10de", "1d10")]
    assert sorted(parse_linux_output(output)) == sorted(expected)


def test_parse_macos_output_invalid_json():
    output = "{ invalid_json: true }"
    assert parse_macos_output(output) == []


def test_empty_outputs():
    assert parse_windows_output("") == []
    assert parse_linux_output("") == []
    assert parse_macos_output("") == []
