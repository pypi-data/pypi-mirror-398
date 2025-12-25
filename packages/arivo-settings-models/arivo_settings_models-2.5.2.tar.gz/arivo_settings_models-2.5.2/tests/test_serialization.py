from decimal import Decimal

from settings_models._combat import SettingsModel
from settings_models.serialization import parse_setting, dump_setting, parse_setting_from_obj
from tests.utils import TestCase


class TestSerialization(TestCase):
    def test_unicode(self):
        setting_str = '{"name": "Testgarage ÄÖÜß", "technical_name": "at-8-test-garage", "slug": "testgarage"}'
        res = parse_setting("common/garage_name", setting_str)
        s = dump_setting(res)
        self.assertNotIn("Ä", s.decode())
        self.assertNotIn("Ö", s.decode())
        self.assertNotIn("Ü", s.decode())
        self.assertNotIn("ß", s.decode())
        res = parse_setting("common/garage_name", s)
        self.assertEqual(res.name, "Testgarage ÄÖÜß")

    def test_unicode_emoji(self):
        setting_str = '{"name": "Testgarage 😀", "technical_name": "at-8-test-garage", "slug": "testgarage"}'
        res = parse_setting("common/garage_name", setting_str)
        s = dump_setting(res)
        self.assertNotIn("😀", s.decode())
        res = parse_setting("common/garage_name", s)
        self.assertEqual(res.name, "Testgarage 😀")

    def test_custom_type(self):
        class CustomType(SettingsModel):
            name: str
            slug: str

        gt = dump_setting({"name": "Testgarage", "slug": "testgarage", "technical_name": "test"})
        res = parse_setting("common/garage_name", gt)
        self.assert_result(res, gt)

        res = parse_setting("common/garage_name", gt, custom_type=CustomType)
        self.assert_not_result(res, gt)
        self.assert_result(res, {"name": "Testgarage", "slug": "testgarage"})

    def test_parse_obj(self):
        gt = {"name": "Testgarage", "slug": "testgarage", "technical_name": "test"}
        with self.assertRaises(ValueError) as e:
            parse_setting("common/garage_name", gt)
        self.assertEqual(str(e.exception), "common/garage_name requires json decodable value")
        res = parse_setting_from_obj("common/garage_name", gt)
        self.assert_result(res, gt)

    def test_not_json_str(self):
        gt = "not json"
        with self.assertRaises(ValueError) as e:
            parse_setting("common/garage_name", gt)
        self.assertEqual(str(e.exception), "common/garage_name requires json decodable value")

    def test_unknown_setting(self):
        gt = '{"name": "Testgarage", "slug": "testgarage", "technical_name": "test"}'
        with self.assertRaises(KeyError) as e:
            parse_setting("common/unknown", gt)
        self.assertEqual(str(e.exception), "'No model for setting common/unknown found'")

    def test_parse_decimal(self):
        setting_val = {"parking_default": {
            "id": "parking_default", "name": "Default", "vat_rate": Decimal("0.19"), "account_id": Decimal(20)}}
        res = parse_setting("common/cost_groups", dump_setting(setting_val))
        self.assert_not_result(res, setting_val)
        self.assert_result(res, {"parking_default": {
            "id": "parking_default", "name": "Default", "vat_rate": 0.19, "account_id": "20"}})

    def test_not_json_dumpable(self):
        class CustomStr:
            def __init__(self, val):
                self.val = val

        setting_val = {"name": CustomStr("Testgarage"), "slug": "testgarage", "technical_name": "test"}
        with self.assertRaises(TypeError):
            dump_setting(setting_val)
