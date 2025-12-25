from types import FunctionType

from settings_models import serialization
from settings_models._combat import SettingsModel
from settings_models.serialization import dump_setting, parse_setting
from settings_models.settings.common import GarageSettings
from tests.utils import TestCase


class ParsingTests(TestCase):
    def test_gates(self):
        setting_str = '{"gate1":{"gate":"gate1","name":"EF","type":"entry"},' \
                      '"gate2":{"gate":"gate2","name":"AF","type":"exit"}}'
        res = parse_setting("common/gates", setting_str)
        self.assert_result(setting_str, dump_setting(res))

    def test_rates(self):
        setting_str = ('{"7a50fafd-3426-42c8-bf3c-ca708638c327":{'
                       '"id":"7a50fafd-3426-42c8-bf3c-ca708638c327","name":"Kurzparktarif",'
                       '"rate_yaml":"!RateMatrix\\nconstraints: []\\ntables:\\n  - !RateTable\\n    '
                       'active_times: !OverallPeriod \\n      exception_periods: []\\n      '
                       'valid_periods: []\\n    constraints: []\\n    '
                       'id: 186ad735-6bcf-4c0c-9811-32bc8f502e17\\n    name: 3.30€ / Stunde\\n    '
                       'line_collections:\\n      - !RateLineCollection\\n        grace_period: 3m\\n        '
                       'max_value: 2500\\n        reset_duration: 1d\\n        lines:\\n          '
                       '- !RateLine\\n            value: 330\\n            increment_period: 1h\\n"}}')
        res = parse_setting("common/rates", setting_str)
        self.assert_result(setting_str, dump_setting(res))

    def test_parking_areas2(self):
        setting_str = ('{"0eec2445-15c3-4af8-b362-aeb1f278e3ac": {"default_cost_entries": '
                       '[{"entry_type": "rate_change", "group": "parking_default", '
                       '"value": "7a50fafd-3426-42c8-bf3c-ca708638c327", "account_id": "0", "source": null, '
                       '"source_id": null, "idempotency_key": null}], '
                       '"gates": ["gate1"], "id": "0eec2445-15c3-4af8-b362-aeb1f278e3ac", '
                       '"name": "Gesamter Parkplatz", "shortterm_gates": ["gate1"],'
                       '"shortterm_limit_type": "no_limit", "shortterm_limit": 0, "number_of_parking_spaces": 10}}')
        res = parse_setting("common/parking_areas2", setting_str)
        self.assert_result(setting_str, dump_setting(res))

        setting_str = ('{"0eec2445-15c3-4af8-b362-aeb1f278e3ac": {"default_cost_entries": '
                       '[{"entry_type": "rate_change", "group": "parking_default", '
                       '"value": "7a50fafd-3426-42c8-bf3c-ca708638c327", "account_id": "0", "source": null, '
                       '"source_id": null, "idempotency_key": null}], '
                       '"gates": ["gate1"], "id": "0eec2445-15c3-4af8-b362-aeb1f278e3ac", '
                       '"name": "Gesamter Parkplatz", "shortterm_gates": ["gate1"],'
                       '"shortterm_limit_type": "no_limit", "shortterm_limit": 0, "number_of_parking_spaces": 10,'
                       '"time_based_shortterm_limit": "some yaml"}}')
        res = parse_setting("common/parking_areas2", setting_str)
        self.assert_result(setting_str, dump_setting(res))

    def test_parksettings2(self):
        setting_str = ('{"654cb72d-545c-48e1-9de7-146528affb6c": {"name": "Dauerparker ohne Kosten", '
                       '"id": "654cb72d-545c-48e1-9de7-146528affb6c", "default_cost_entries": [], "gates": ["gate1"]}, '
                       '"70c3f84d-7408-487c-af0c-e41d8fe6c6ac": {"id": "70c3f84d-7408-487c-af0c-e41d8fe6c6ac", '
                       '"name": "Rabattparker", "gates": ["gate1", "gate2"], '
                       '"default_cost_entries": [{"entry_type": "rate_change", "group": "parking_default", '
                       '"value": "75dadac3-2362-4075-bae1-8a26e06f2d76", "account_id": "0", "source": null, '
                       '"source_id": null, "idempotency_key": null}]}}')
        res = parse_setting("common/parksettings2", setting_str)
        self.assert_result(setting_str, dump_setting(res))

    def test_privacy_settings(self):
        setting_str = ('{"paid": {"days": 1, "hours": 0, "minutes": 0}, '
                       '"unpaid": {"days": 90, "hours": 0, "minutes": 0}, '
                       '"registered_free": {"days": 30, "hours": 0, "minutes": 0}, '
                       '"pay_via_invoice": {"days": 30, "hours": 0, "minutes": 0}, '
                       '"open": {"days": 90, "hours": 0, "minutes": 0}, '
                       '"free": {"days": 0, "hours": 0, "minutes": 5}, '
                       '"honest_payment": {"days": 90, "hours": 0, "minutes": 0}, '
                       '"erroneous": {"days": 30, "hours": 0, "minutes": 0}, '
                       '"rejected": {"days": 7, "hours": 0, "minutes": 0}}')
        res = parse_setting("common/privacy_settings", setting_str)
        self.assert_result(setting_str, dump_setting(res))

    def test_cost_groups(self):
        setting_str = ('{"fine_no-ticket": {"account_id": "100", "id": "fine_no-ticket", '
                       '"name": "Strafe: Kein Ticket", "vat_rate": 0}, '
                       '"fine_parking-violation": {"account_id": "101", "id": "fine_parking-violation", '
                       '"name": "Strafe: Unerlaubter Stellplatz", "vat_rate": 0}, '
                       '"honest-payment_default": {"account_id": "300", "id": "honest-payment_default", '
                       '"name": "Ehrliche Zahlung", "vat_rate": 20}, '
                       '"parking_default": {"account_id": "0", "id": "parking_default", "name": '
                       '"Parkkosten", "vat_rate": 20}}')
        res = parse_setting("common/cost_groups", setting_str)
        self.assert_result(setting_str, dump_setting(res))

    def test_currency(self):
        setting_str = '"EUR"'
        res = parse_setting("common/currency", setting_str)
        self.assertEqual(setting_str.encode("utf8"), dump_setting(res))

    def test_language(self):
        setting_str = '"de"'
        res = parse_setting("common/language", setting_str)
        self.assertEqual(setting_str.encode("utf8"), dump_setting(res))

    def test_timezone(self):
        setting_str = '"Europe/Vienna"'
        res = parse_setting("common/timezone", setting_str)
        self.assertEqual(setting_str.encode("utf8"), dump_setting(res))

    def test_garage_settings(self):
        setting_str = '{"mode": "freeflow", "honest_payment_enabled": false}'
        res = parse_setting("common/garage_settings", setting_str)
        self.assert_result('{"mode": "freeflow", "honest_payment_enabled": true, "enforcement_enabled": true, '
                           '"payment_possible": true}', dump_setting(res))
        setting_str = '{"mode": "freeflow_surveillance"}'
        res = parse_setting("common/garage_settings", setting_str)
        self.assert_result('{"mode": "freeflow_surveillance", "honest_payment_enabled": false, '
                           '"enforcement_enabled": false, "payment_possible": false}', dump_setting(res))
        setting_str = '{"mode": "barrier"}'
        res = parse_setting("common/garage_settings", setting_str)
        self.assert_result('{"mode": "barrier", "honest_payment_enabled": false, "enforcement_enabled": false, '
                           '"payment_possible": true}', dump_setting(res))
        setting_str = '{"mode": "barrier_bypass"}'
        res = parse_setting("common/garage_settings", setting_str)
        self.assert_result('{"mode": "barrier_bypass", "honest_payment_enabled": false, "enforcement_enabled": false, '
                           '"payment_possible": false}', dump_setting(res))
        # only for the sake of coverage
        values = GarageSettings.data_validation("not-a-dictionary")
        self.assertEqual("not-a-dictionary", values)

    def test_location(self):
        setting_str = '{"name": "Garage", "street": "Garagestreet", "number": "12c", "floor": "2H", "door": "7a", ' \
                      '"supplements": "Frag nach Ines", "city": "Graz", "zip_code": "8020", "state": "Styria", ' \
                      '"country": "Österreich", "longitude": 15.441016366426302, "latitude": 47.041677687836156}'
        res = parse_setting("common/location", setting_str)
        self.assert_result(setting_str, dump_setting(res))

    def test_billing(self):
        setting_str = '{"billing_address": {"name": "Garage", "street": "Garagestreet", "number": "12c", ' \
                      '"floor": "2H", "door": "7a", "supplements": "Frag nach Ines", "city": "Graz", ' \
                      '"zip_code": "8020", "state": "Styria", "country": "Österreich"}, "vat_id": "ATU1234567890"}'
        res = parse_setting("common/billing", setting_str)
        self.assert_result(setting_str, dump_setting(res))

    def test_support(self):
        setting_str = '{"name": "ARIVO", "address": {"name": "Garage", "street": "Garagestreet", "number": "12c", ' \
                      '"floor": "2H", "door": "7a", "supplements": "Frag nach Ines", "city": "Graz", ' \
                      '"zip_code": "8020", "state": "Styria", "country": "Österreich"}, ' \
                      '"phone_number": "+43 123 456", "email_address": "ines@arivo.co"}'
        res = parse_setting("common/support", setting_str)
        self.assert_result(setting_str, dump_setting(res))

    def test_garage_name(self):
        setting_str = '{"name": "Testgarage", "technical_name": "at-8-test-garage", "slug": "testgarage"}'
        res = parse_setting("common/garage_name", setting_str)
        self.assert_result(setting_str, dump_setting(res))

    def test_urls(self):
        setting_str = '{"payapp_domain": "pay.arivo.fun", "payapp_short_url": "https://pay.arivo.fun/arivo-v2", ' \
                      '"receipt_domain": "beleg.arivo.fun"}'
        res = parse_setting("common/urls", setting_str)
        self.assert_result(setting_str, dump_setting(res))

    def test_gate_control_mode(self):
        setting_str = '"standard"'
        res = parse_setting("gate_control/mode", setting_str)
        self.assertEqual(setting_str.encode("utf8"), dump_setting(res))

    def test_gate_control_day_mode(self):
        setting_str = '{"enabled": true, "start": "10:00", "end": "23:59"}'
        res = parse_setting("gate_control/day_mode", setting_str)
        self.assert_result(setting_str, dump_setting(res))

    def test_enforcement_basic_settings(self):
        setting_str = '{"strictness": 2, "payment_deadline_hours": 48, "enabled": true, ' \
                      '"ai_enabled": true, "last_edited": "2023-03-08T08:48:37.184000"}'
        res = parse_setting("enforcement/basic_settings", setting_str)
        self.assert_result(setting_str, dump_setting(res))

    def test_intercom_basic_settings(self):
        setting_str = '{"enabled": true, "phone_number": "sip:12345"}'
        res = parse_setting("intercom/basic_settings", setting_str)
        self.assert_result(setting_str, dump_setting(res))

    def test_device_keys_pairing(self):
        setting_str = '{"key": "arivopairing:ayek97rblos", "created_at": "2023-03-08T08:48:37.184000", "revision": 0}'
        res = parse_setting("device_keys/pairing", setting_str)
        self.assert_result(setting_str, dump_setting(res))

    def test_device_keys_cert(self):
        setting_str = '{"cert": "asdf", "key": "asdf", "fingerprint": "asdf"}'
        res = parse_setting("device_keys/cert", setting_str)
        self.assert_result(setting_str, dump_setting(res))

    def test_device_keys_otp(self):
        setting_str = '{"secret": "arivopairing:ayek97rblos", "interval": 30}'
        res = parse_setting("device_keys/otp", setting_str)
        self.assert_result(setting_str, dump_setting(res))

    def test_feature_flags(self):
        setting_str = '{"flag1": true, "oebb": true}'
        res = parse_setting("feature_flags", setting_str)
        self.assert_result(setting_str, dump_setting(res))

    def test_refs(self):
        setting_str = '{"name": "Parking Management System", "keys": ["2e9932bf-9071-47ac-afc5-3855a2eb6147", ' \
                      '"1f04cbeb-7613-496c-a301-6578eb2dafcd"]}'
        res = parse_setting("common/parksettings/refs/digimon", setting_str)
        self.assert_result(setting_str, dump_setting(res))

    def test_io_signals(self):
        setting_str = \
        """
        {"entry-open": {"signal": "entry-open", "gate": "entry", "type": "open", "name": "Einfahrt offen"},
         "exit-present_decision": {"signal": "exit-present_decision", "gate": "exit", "type": "present_decision", 
                                   "name": "Ausfahrt Entscheidung"}, 
         "00000000-0000-0000-0000-000000000001-area_full": 
             {"signal": "00000000-0000-0000-0000-000000000001-area_full", "type": "area_full", 
              "parking_area_id": "00000000-0000-0000-0000-000000000001", "name": "Parkbereich 1 voll"}, 
         "parkinglot_full": {"signal": "parkinglot_full", "type": "parkinglot_full", "name": "Parkplatz voll"}, 
         "custom_signal": {"signal": "custom_signal", "type": "custom", "gate": "entry", 
                           "parking_area_id": "00000000-0000-0000-0000-000000000001", "name": "Custom Signal"}, 
         "custom-signal2": {"signal": "custom-signal2", "type": "custom", "name": "Custom Signal 2"}}
        """
        res = parse_setting("io/signals", setting_str)
        self.assert_result(setting_str, dump_setting(res))

    def test_io_inputs(self):
        setting_str = \
        """
        {"entry-safety_loop": {"input":"entry-safety_loop","type":"safety_loop","gate":"entry","name":"EF CLoop",
        "active":true}, 
         "custom_input": {"input": "custom_input", "type": "custom", "gate": "entry", "name": "Custom Input",
         "active":true}, 
         "custom_input2": {"input": "custom_input2", "type": "custom", "name": "Custom Input 2","active":false}}
        """
        res = parse_setting("io/inputs", setting_str)
        self.assert_result(setting_str, dump_setting(res))

    def test_assets_visuals(self):
        setting_str = \
            """
            {"logo": {"type": "logo", "value": "stuff", "created": "2024-12-31T11:59:59"}, 
             "pogo": {"type": "pogo", "value": "hobo", "created": "2024-12-31T12:59:59"}}
            """
        res = parse_setting("assets/visuals", setting_str)
        self.assert_result(setting_str, dump_setting(res))


class EnsureAllTests(TestCase):
    def test_ensure_all_parsed(self):
        """Making sure all known settings are parsed at least once."""
        tests = [name for name, obj in ParsingTests.__dict__.items()
                 if isinstance(obj, FunctionType) and name.startswith("test_")]
        settings_keys = list(serialization._model_mapping.keys())
        self.assertGreaterEqual(len(tests), len(settings_keys))
        for key in settings_keys:
            if key.startswith("common/"):
                self.assertIn(f"test_{key.replace('common/', '')}", tests)
            else:
                self.assertIn(f"test_{key.replace('/', '_')}", tests)

    def test_ensure_all_docstrings(self):
        """Making sure all settings have a custom docstring."""

        def custom_docstring(settings_model: SettingsModel):
            return settings_model.__module__.startswith("settings_models") and \
                not any(base.__doc__ == settings_model.__doc__ for base in settings_model.__bases__)

        for key, setting in list(serialization._model_mapping.items()):
            if setting.settings_doc != setting.settings_model.__doc__:
                continue
            self.assertNotEqual(setting.settings_doc, "An enumeration.")
            if isinstance(setting.settings_model, SettingsModel):
                self.assertTrue(custom_docstring(setting.settings_model), msg=f"Missing docstring for {key}")
