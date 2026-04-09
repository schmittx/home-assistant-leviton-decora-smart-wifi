import importlib
import importlib.util
import sys
import unittest
from pathlib import Path
from types import SimpleNamespace

sys.modules.setdefault(
    "pyqrcode",
    SimpleNamespace(
        create=lambda *_args, **_kwargs: SimpleNamespace(png=lambda *a, **k: None)
    ),
)
sys.modules.setdefault(
    "requests",
    SimpleNamespace(Session=lambda: None, Response=object),
)

API_ROOT = (
    Path(__file__).resolve().parents[1]
    / "custom_components"
    / "leviton_decora_smart_wifi"
    / "api"
)

if "leviton_test_api" not in sys.modules:
    spec = importlib.util.spec_from_file_location(
        "leviton_test_api",
        API_ROOT / "__init__.py",
        submodule_search_locations=[str(API_ROOT)],
    )
    package = importlib.util.module_from_spec(spec)
    sys.modules["leviton_test_api"] = package
    spec.loader.exec_module(package)

Device = importlib.import_module("leviton_test_api.device").Device


def make_device(model: str, **data):
    residence = SimpleNamespace(id=1, rooms=[])
    base = {
        "id": 1,
        "model": model,
        "name": model,
        "power": "OFF",
        "canSetLevel": False,
        "connected": True,
    }
    base.update(data)
    return Device(
        api=SimpleNamespace(call=lambda **kwargs: None),
        residence=residence,
        data=base,
    )


class DeviceSupportTest(unittest.TestCase):
    def test_new_models_have_expected_primary_types(self):
        self.assertTrue(make_device("DN15S").is_switch)
        self.assertTrue(make_device("DN6HD", canSetLevel=True).is_light)
        self.assertFalse(make_device("MLWSB").is_supported)

    def test_gfci_and_bridge_are_not_primary_switches(self):
        self.assertFalse(make_device("D2GF2").is_switch)
        self.assertFalse(make_device("MLWSB").is_switch)

    def test_dn_devices_surface_bridge_linkage_metadata(self):
        switch = make_device("DN15S", iotBridgeSerial="1000_003F_F15A")
        dimmer = make_device("DN6HD", canSetLevel=True, iotBridgeSerial="1000_003F_F15A")

        self.assertEqual(switch.bridge_serial, "1000_003F_F15A")
        self.assertTrue(switch.has_bridge)
        self.assertEqual(dimmer.bridge_serial, "1000_003F_F15A")
        self.assertTrue(dimmer.has_bridge)
        self.assertTrue(dimmer.supports_auto_shutoff)
        self.assertTrue(dimmer.supports_status_led_behavior)
