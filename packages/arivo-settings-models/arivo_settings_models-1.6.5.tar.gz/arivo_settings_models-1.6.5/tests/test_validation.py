import warnings
from datetime import datetime
from unittest.mock import patch

from pydantic import ValidationError

from settings_models.serialization import dump_setting, parse_setting
from settings_models.settings.common import Parksettings
from settings_models.settings.io import SignalType, InputType
from tests.utils import TestCase


class ValidationTests(TestCase):
    def test_gates_success(self):
        gt = dump_setting({"gate1": {"gate": "gate1", "name": "EF", "type": "entry", "opposite_gate": "gate2",
                                     "is_wide": None},
                           "gate2": {"gate": "gate2", "name": "AF", "type": "exit", "opposite_gate": "gate1",
                                     "is_wide": None}})
        res = parse_setting("common/gates", gt)
        self.assertEqual(dump_setting(res), gt)

    def test_gates_success_unknown_type(self):
        with self.assertRaises(ValidationError) as e:
            parse_setting("common/gates",
                          dump_setting({"gate1": {"gate": "gate1", "name": "EF", "type": "wrong"},
                                        "gate2": {"gate": "gate2", "name": "AF", "type": "exit"}}))
        self.assertEqual(str(e.exception).count("\n"), 2)
        self.assertIn("value is not a valid enumeration member; permitted", str(e.exception))

    def test_gates_success_key_does_not_match_field(self):
        with self.assertRaises(ValueError) as e:
            parse_setting("common/gates",
                          dump_setting({"gate1": {"gate": "gate3", "name": "EF", "type": "entry"},
                                        "gate2": {"gate": "gate2", "name": "AF", "type": "exit"}}))
        self.assertEqual(str(e.exception).count("\n"), 0)
        self.assertEqual("key must match field gate", str(e.exception))

    def test_gates_invalid_key(self):
        with self.assertRaises(ValidationError) as e:
            parse_setting("common/gates",
                          dump_setting({"gateß": {"gate": "gateß", "name": "EF", "type": "entry"}}))
        self.assertEqual(str(e.exception).count("\n"), 2)
        self.assertIn("string does not match regex", str(e.exception))

    def test_opposite_gate_error(self):
        with self.assertRaises(ValueError) as e:
            parse_setting("common/gates",
                          dump_setting({"gate1": {"gate": "gate1", "name": "EF", "type": "entry",
                                                  "opposite_gate": "gate2"},
                                        "gate2": {"gate": "gate2", "name": "AF", "type": "exit"}}))
        self.assertEqual(str(e.exception).count("\n"), 0)
        self.assertIn("gate gate1 and gate2 must reference each other", str(e.exception))

    def test_gates_none(self):
        with self.assertRaises(ValidationError) as e:
            parse_setting("common/gates", "null")
        self.assertEqual(len(e.exception.errors()), 1)
        self.assertIn("none is not an allowed value", str(e.exception))

    def test_parksettings_success(self):
        self.maxDiff = None
        gt = dump_setting({
            "896150c9-5616-4406-a544-84c3824cfea9": {
                "id": "896150c9-5616-4406-a544-84c3824cfea9", "name": "Dauerparker mit variablen Kosten",
                "gates": ["gate1"], "default_cost_entries": []},
            "12e8a7e2-be78-488e-8d1a-1486f7da2179": {
                "id": "12e8a7e2-be78-488e-8d1a-1486f7da2179", "name": "Dauerparker ohne Kosten",
                "gates": ["gate1"],
                "default_cost_entries": [{"entry_type": "static_cost", "value": 123,
                                          "group": "parking_default", "account_id": "0",
                                          "source": None, "source_id": None, "idempotency_key": None}]}
        })
        res = parse_setting("common/parksettings2", gt)
        self.assert_result(dump_setting(res), gt)

    def test_parksettings_gates_no_empty_list(self):
        self.maxDiff = None
        with self.assertRaises(ValidationError) as e:
            gt = dump_setting({
                "896150c9-5616-4406-a544-84c3824cfea9": {
                    "id": "896150c9-5616-4406-a544-84c3824cfea9", "name": "Dauerparker mit variablen Kosten",
                    "gates": [], "default_cost_entries": []}})
            parse_setting("common/parksettings2", gt)
        self.assertEqual(str(e.exception).count("\n"), 2)
        self.assertIn("ensure this value has at least 1 items", str(e.exception))

    def test_parksettings_not_a_uuid(self):
        with self.assertRaises(ValidationError) as e:
            parse_setting("common/parksettings2", dump_setting({
                "12e8a7e2-be78-488e-8d1a-1486f7da2179": {
                    "id": "123",
                    "name": "Dauerparker ohne Kosten",
                    "gates": ["gate1"],
                    "default_cost_entries": []}}))
        self.assertEqual(str(e.exception).count("\n"), 2)
        self.assertIn("must be a uuid string", str(e.exception))

    def test_parksettings_id_does_not_match_field(self):
        with self.assertRaises(ValueError) as e:
            parse_setting("common/parksettings2", dump_setting({
                "9999a7e2-be78-488e-8d1a-1486f7da9999": {
                    "id": "0000a7e2-be78-488e-8d1a-1486f7da0000",
                    "name": "Dauerparker ohne Kosten",
                    "gates": ["gate1"],
                    "default_cost_entries": []}}))
        self.assertEqual(str(e.exception).count("\n"), 0)
        self.assertEqual("key must match field id", str(e.exception))

        with self.assertRaises(ValueError) as e:
            parse_setting("common/parksettings2", dump_setting({
                "123": {
                    "id": "12e8a7e2-be78-488e-8d1a-1486f7da2179",
                    "name": "Dauerparker ohne Kosten",
                    "gates": ["gate1"],
                    "default_cost_entries": []}}))
        self.assertEqual(str(e.exception).count("\n"), 0)
        self.assertIn("key must match field id", str(e.exception))

    def test_parksettings_invalid_default_cost_entry_type(self):
        with self.assertRaises(ValidationError) as e:
            parse_setting("common/parksettings2", dump_setting({
                "0000a7e2-be78-488e-8d1a-1486f7da0000": {
                    "id": "0000a7e2-be78-488e-8d1a-1486f7da0000",
                    "name": "Dauerparker ohne Kosten",
                    "gates": ["gate1"],
                    "default_cost_entries": [
                        {"entry_type": "partial_rate_change", "value": 123,
                         "group": "parking_default", "account_id": "0", "source": "test",
                         "source_id": "1", "idempotency_key": "1234"}
                    ]}}))
        self.assertEqual(str(e.exception).count("\n"), 2)
        self.assertIn("is not allowed as default cost entry in parksetting", str(e.exception))

    def test_parksettings_none(self):
        with self.assertRaises(ValidationError) as e:
            parse_setting("common/parksettings2", "null")
        self.assertEqual(len(e.exception.errors()), 1)
        self.assertIn("none is not an allowed value", str(e.exception))

    def test_cost_entry_invalid_type(self):
        with self.assertRaises(ValidationError) as e:
            parse_setting("common/parksettings2", dump_setting({
                "12e8a7e2-be78-488e-8d1a-1486f7da2179": {
                    "id": "12e8a7e2-be78-488e-8d1a-1486f7da2179",
                    "name": "Dauerparker ohne Kosten",
                    "gates": ["gate1"],
                    "default_cost_entries": [
                        {"entry_type": "static_cost123", "value": 123,
                         "group": "parking_default", "account_id": "0", "source": "test",
                         "source_id": "1", "idempotency_key": "1234"}
                    ]}}))
        self.assertEqual(str(e.exception).count("\n"), 2)
        self.assertIn("value is not a valid enumeration member", str(e.exception))

    def test_cost_entry_invalid_value(self):
        with self.assertRaises(ValidationError) as e:
            parse_setting("common/parksettings2", dump_setting({
                "12e8a7e2-be78-488e-8d1a-1486f7da2179": {
                    "id": "12e8a7e2-be78-488e-8d1a-1486f7da2179",
                    "name": "Dauerparker ohne Kosten",
                    "gates": ["gate1"],
                    "default_cost_entries": [
                        {"entry_type": "static_cost", "value": "NaN",
                         "group": "parking_default", "account_id": "0", "source": "test",
                         "source_id": "1", "idempotency_key": "1234"}
                    ]}}))
        self.assertEqual(str(e.exception).count("\n"), 2)
        self.assertIn("value must be an integer greater 0", str(e.exception))

    def test_cost_entry_group_missing(self):
        with self.assertRaises(ValidationError) as e:
            parse_setting("common/parksettings2", dump_setting({
                "12e8a7e2-be78-488e-8d1a-1486f7da2179": {
                    "id": "12e8a7e2-be78-488e-8d1a-1486f7da2179",
                    "name": "Dauerparker ohne Kosten",
                    "gates": ["gate1"],
                    "default_cost_entries": [
                        {"entry_type": "static_cost", "value": 123,
                         "account_id": "0", "source": "test",
                         "source_id": "1", "idempotency_key": "1234"}
                    ]}}))
        self.assertEqual(str(e.exception).count("\n"), 2)
        self.assertIn("group must be set", str(e.exception))

    def test_cost_entry_group_unexpectedly_set(self):
        # entry_type cancel_remaining_costs/payoff_costs
        with self.assertRaises(ValidationError) as e:
            parse_setting("common/parksettings2", dump_setting({
                "12e8a7e2-be78-488e-8d1a-1486f7da2179": {
                    "id": "12e8a7e2-be78-488e-8d1a-1486f7da2179",
                    "name": "Dauerparker ohne Kosten",
                    "gates": ["gate1"],
                    "default_cost_entries": [
                        {"entry_type": "cancel_remaining_costs", "value": 123,
                         "account_id": "0", "source": "test", "group": "parking_default",
                         "source_id": "1", "idempotency_key": "1234"}
                    ]}}))
        self.assertEqual(str(e.exception).count("\n"), 2)
        self.assertIn("group must NOT be set", str(e.exception))

    def test_cost_entry_free_timerange(self):
        # entry_type free timerange
        res = parse_setting("common/parksettings2", dump_setting({
            "12e8a7e2-be78-488e-8d1a-1486f7da2179": {
                "id": "12e8a7e2-be78-488e-8d1a-1486f7da2179",
                "name": "Dauerparker ohne Kosten",
                "gates": ["gate1"],
                "default_cost_entries": [
                    {"entry_type": "free_timerange", "value": {"entry_start": "2021-01-01 00:00:00"},
                     "account_id": "0", "source": "test", "group": "parking_default",
                     "source_id": "1", "idempotency_key": "1234"}
                ]}}))
        self.assertDictEqual(dict(entry_start=datetime(2021, 1, 1, 0, 0, 0), entry_end=None),
                             res["12e8a7e2-be78-488e-8d1a-1486f7da2179"].default_cost_entries[0].value)
        with self.assertRaises(ValidationError) as e:
            parse_setting("common/parksettings2", dump_setting({
                "12e8a7e2-be78-488e-8d1a-1486f7da2179": {
                    "id": "12e8a7e2-be78-488e-8d1a-1486f7da2179",
                    "name": "Dauerparker ohne Kosten",
                    "gates": ["gate1"],
                    "default_cost_entries": [
                        {"entry_type": "free_timerange", "value": {"entry_start": "2021-01-01 00:00:00"},
                         "account_id": "0", "source": "test", "source_id": "1", "idempotency_key": "1234"}
                    ]}}))
        self.assertEqual(str(e.exception).count("\n"), 2)
        self.assertIn("group must be set", str(e.exception))

    def test_privacy_success(self):
        gt = dump_setting({"paid": {"days": 1, "hours": 0, "minutes": 0},
                           "unpaid": {"days": 90, "hours": 0, "minutes": 0},
                           "registered_free": {"days": 30, "hours": 0, "minutes": 0},
                           "pay_via_invoice": {"days": 30, "hours": 0, "minutes": 0},
                           "open": {"days": 90, "hours": 0, "minutes": 0},
                           "free": {"days": 0, "hours": 0, "minutes": 5},
                           "honest_payment": {"days": 90, "hours": 0, "minutes": 0},
                           "erroneous": {"days": 30, "hours": 0, "minutes": 0},
                           "rejected": {"days": 7, "hours": 0, "minutes": 0}})
        res = parse_setting("common/privacy_settings", gt)
        self.assert_result(res, gt)

    def test_privacy_paid_missing(self):
        with self.assertRaises(ValidationError) as e:
            parse_setting("common/privacy_settings",
                          dump_setting({"unpaid": {"days": 90, "hours": 0, "minutes": 0},
                                        "registered_free": {"days": 30, "hours": 0, "minutes": 0},
                                        "pay_via_invoice": {"days": 30, "hours": 0, "minutes": 0},
                                        "open": {"days": 90, "hours": 0, "minutes": 0},
                                        "free": {"days": 0, "hours": 0, "minutes": 5},
                                        "honest_payment": {"days": 90, "hours": 0, "minutes": 0},
                                        "erroneous": {"days": 30, "hours": 0, "minutes": 0},
                                        "rejected": {"days": 7, "hours": 0, "minutes": 0}}))
        self.assertEqual(str(e.exception).count("\n"), 2)
        self.assertIn("field required", str(e.exception))

    def test_privacy_require_gt_0(self):
        with self.assertRaises(ValidationError) as e:
            parse_setting("common/privacy_settings",
                          dump_setting({"paid": {"hours": 0},
                                        "unpaid": {"days": 90, "hours": 0, "minutes": 0},
                                        "registered_free": {"days": 30, "hours": 0, "minutes": 0},
                                        "pay_via_invoice": {"days": 30, "hours": 0, "minutes": 0},
                                        "open": {"days": 90, "hours": 0, "minutes": 0},
                                        "free": {"days": 0, "hours": 0, "minutes": 5},
                                        "honest_payment": {"days": 90, "hours": 0, "minutes": 0},
                                        "erroneous": {"days": 30, "hours": 0, "minutes": 0},
                                        "rejected": {"days": 7, "hours": 0, "minutes": 0}}))
        self.assertEqual(str(e.exception).count("\n"), 2)
        self.assertIn("At least one of minutes, hours or days must be > 0", str(e.exception))

    def test_privacy_negative_value(self):
        with self.assertRaises(ValidationError) as e:
            parse_setting("common/privacy_settings",
                          dump_setting({"paid": {"hours": 10},
                                        "unpaid": {"days": -90, "hours": 0, "minutes": 0},
                                        "registered_free": {"days": 30, "hours": 0, "minutes": 0},
                                        "pay_via_invoice": {"days": 30, "hours": 0, "minutes": 0},
                                        "open": {"days": 90, "hours": 0, "minutes": 0},
                                        "free": {"days": 0, "hours": 0, "minutes": 5},
                                        "honest_payment": {"days": 90, "hours": 0, "minutes": 0},
                                        "erroneous": {"days": 30, "hours": 0, "minutes": 0},
                                        "rejected": {"days": 7, "hours": 0, "minutes": 0}}))
        self.assertEqual(str(e.exception).count("\n"), 2)
        self.assertIn("ensure this value is greater than or equal to 0", str(e.exception))

    def test_privacy_none(self):
        with self.assertRaises(ValidationError) as e:
            parse_setting("common/privacy_settings", "null")
        self.assertEqual(len(e.exception.errors()), 1)
        self.assertIn("none is not an allowed value", str(e.exception))

    def test_cost_groups_success(self):
        gt = dump_setting({"honest-payment_default": {"account_id": "300", "id": "honest-payment_default",
                                                      "name": "Ehrliche Zahlung", "vat_rate": 20},
                           "parking_default": {"account_id": "0", "id": "parking_default", "name": "Parkkosten",
                                               "vat_rate": 20}})
        res = parse_setting("common/cost_groups", gt)
        self.assert_result(res, gt)

    def test_cost_groups_account_id_oob(self):
        with self.assertRaises(ValidationError) as e:
            parse_setting("common/cost_groups", dump_setting(
                {"honest-payment_default": {"account_id": 1234, "id": "honest-payment_default",
                                            "name": "Ehrliche Zahlung", "vat_rate": 20},
                 "parking_default": {"account_id": "0", "id": "parking_default",
                                     "name": "Parkkosten", "vat_rate": 20}}))
        self.assertEqual(str(e.exception).count("\n"), 2)
        self.assertIn('account_id must be a value between "0" and "999"', str(e.exception))

    def test_cost_groups_vat_over_100(self):
        with self.assertRaises(ValidationError) as e:
            parse_setting("common/cost_groups", dump_setting(
                {"honest-payment_default": {"account_id": "300", "id": "honest-payment_default",
                                            "name": "Ehrliche Zahlung", "vat_rate": 20},
                 "parking_default": {"account_id": "0", "id": "parking_default",
                                     "name": "Parkkosten", "vat_rate": 200}}))
        self.assertEqual(str(e.exception).count("\n"), 2)
        self.assertIn("ensure this value is less than or equal to 100.0", str(e.exception))

    def test_cost_groups_account_id_nan(self):
        with self.assertRaises(ValidationError) as e:
            parse_setting("common/cost_groups", dump_setting(
                {"honest-payment_default": {"account_id": "NaN", "id": "honest-payment_default",
                                            "name": "Ehrliche Zahlung", "vat_rate": 20},
                 "parking_default": {"account_id": "0", "id": "parking_default",
                                     "name": "Parkkosten", "vat_rate": 20}}))
        self.assertEqual(str(e.exception).count("\n"), 2)
        self.assertIn("account_id must be an integer as string", str(e.exception))

    def test_cost_groups_account_id_ranges(self):
        # 0-99 parking_*
        with self.assertRaises(ValidationError) as e:
            parse_setting("common/cost_groups", dump_setting(
                {"asdf_default": {"account_id": "50", "id": "asdf_default", "name": "Parkkosten", "vat_rate": 20}}))
        self.assertEqual(str(e.exception).count("\n"), 2)
        self.assertIn("account_ids from 0 to 99 must have cost_group id parking_*", str(e.exception))

        # 100-199 fine_*
        with self.assertRaises(ValidationError) as e:
            parse_setting("common/cost_groups", dump_setting(
                {"asdf_default": {"account_id": "150", "id": "asdf_default", "name": "Parkkosten", "vat_rate": 20}}))
        self.assertEqual(str(e.exception).count("\n"), 2)
        self.assertIn("account_ids from 100 to 199 must have cost_group id fine_*", str(e.exception))

        # 200-299 ev-charging_*
        with self.assertRaises(ValidationError) as e:
            parse_setting("common/cost_groups", dump_setting(
                {"asdf_default": {"account_id": "250", "id": "asdf_default", "name": "Parkkosten", "vat_rate": 20}}))
        self.assertEqual(str(e.exception).count("\n"), 2)
        self.assertIn("account_ids from 200 to 299 must have cost_group id ev-charging_*", str(e.exception))

        # 300-399 honest-payment_*
        with self.assertRaises(ValidationError) as e:
            parse_setting("common/cost_groups", dump_setting(
                {"asdf_default": {"account_id": "350", "id": "asdf_default", "name": "Parkkosten", "vat_rate": 20}}))
        self.assertEqual(str(e.exception).count("\n"), 2)
        self.assertIn("account_ids from 300 to 399 must have cost_group id honest-payment_*", str(e.exception))

        # 400-499 misc_*
        with self.assertRaises(ValidationError) as e:
            parse_setting("common/cost_groups", dump_setting(
                {"asdf_default": {"account_id": "450", "id": "asdf_default", "name": "Parkkosten", "vat_rate": 20}}))
        self.assertEqual(str(e.exception).count("\n"), 2)
        self.assertIn("account_ids from 400 to 499 must have cost_group id misc_*", str(e.exception))

        # 500+ any
        parse_setting("common/cost_groups", dump_setting(
            {"asdf_default": {"account_id": "550", "id": "asdf_default", "name": "Parkkosten", "vat_rate": 20}}))

    def test_cost_groups_none(self):
        with self.assertRaises(ValidationError) as e:
            parse_setting("common/cost_groups", "null")
        self.assertEqual(len(e.exception.errors()), 1)
        self.assertIn("none is not an allowed value", str(e.exception))

    def test_rates_success(self):
        gt = {"7a50fafd-3426-42c8-bf3c-ca708638c327": {
            "id": "7a50fafd-3426-42c8-bf3c-ca708638c327", "name": "Kurzparktarif",
            "rate_yaml": "!RateMatrix\\nconstraints: []\\ntables:\\n  - !RateTable\\n     \
                      active_times: !OverallPeriod \\n      exception_periods: []\\n       \
                      valid_periods: []\\n    constraints: []\\n     \
                      id: 186ad735-6bcf-4c0c-9811-32bc8f502e17\\n    name: 3.30€ / Stunde\\n     \
                      line_collections:\\n      - !RateLineCollection\\n        grace_period: 3m\\n         \
                      max_value: 2500\\n        reset_duration: 1d\\n        lines:\\n           \
                      - !RateLine\\n            value: 330\\n            increment_period: 1h\\n"}}
        res = parse_setting("common/rates", dump_setting(gt))
        self.assert_result(gt, res)

    def test_rates_id_does_not_match_field(self):
        with self.assertRaises(ValueError) as e:
            parse_setting("common/rates", dump_setting({"7a50fafd-3426-42c8-bf3c-ca708638c327": {
                "id": "0eec2445-15c3-4af8-b362-aeb1f278e3ac", "name": "Kurzparktarif",
                "rate_yaml": "!RateMatrix\\nconstraints: []\\ntables:\\n  - !RateTable\\n     \
                      active_times: !OverallPeriod \\n      exception_periods: []\\n       \
                      valid_periods: []\\n    constraints: []\\n     \
                      id: 186ad735-6bcf-4c0c-9811-32bc8f502e17\\n    name: 3.30€ / Stunde\\n     \
                      line_collections:\\n      - !RateLineCollection\\n        grace_period: 3m\\n         \
                      max_value: 2500\\n        reset_duration: 1d\\n        lines:\\n           \
                      - !RateLine\\n            value: 330\\n            increment_period: 1h\\n"}}))
        self.assertEqual(str(e.exception).count("\n"), 0)
        self.assertEqual("key must match field id", str(e.exception))

    def test_rates_not_a_uuid(self):
        with self.assertRaises(ValidationError) as e:
            parse_setting("common/rates", dump_setting({"123": {
                "id": "123", "name": "Kurzparktarif",
                "rate_yaml": "!RateMatrix\\nconstraints: []\\ntables:\\n  - !RateTable\\n     \
                     active_times: !OverallPeriod \\n      exception_periods: []\\n       \
                     valid_periods: []\\n    constraints: []\\n     \
                     id: 186ad735-6bcf-4c0c-9811-32bc8f502e17\\n    name: 3.30€ / Stunde\\n     \
                     line_collections:\\n      - !RateLineCollection\\n        grace_period: 3m\\n         \
                     max_value: 2500\\n        reset_duration: 1d\\n        lines:\\n           \
                     - !RateLine\\n            value: 330\\n            increment_period: 1h\\n"}}))
        self.assertEqual(str(e.exception).count("\n"), 2)
        self.assertIn("must be a uuid string", str(e.exception))

    def test_rates_none(self):
        with self.assertRaises(ValidationError) as e:
            parse_setting("common/rates", "null")
        self.assertEqual(len(e.exception.errors()), 1)
        self.assertIn("none is not an allowed value", str(e.exception))

    def test_parking_areas_success(self):
        self.maxDiff = None
        gt = dump_setting({"0eec2445-15c3-4af8-b362-aeb1f278e3ac": {
            "id": "0eec2445-15c3-4af8-b362-aeb1f278e3ac", "default_cost_entries":
                [{"entry_type": "rate_change", "group": "parking_default",
                  "value": "7a50fafd-3426-42c8-bf3c-ca708638c327", "account_id": "0", "source": None, "source_id": None,
                  "idempotency_key": None}],
            "pay_per_use_cost_entries":
                [{"entry_type": "rate_change", "group": "parking_default",
                  "value": "7a50fafd-3426-42c8-bf3c-ca708638c327", "account_id": "0", "source": None, "source_id": None,
                  "idempotency_key": None}],
            "gates": ["gate1"], "name": "Gesamter Parkplatz", "shortterm_gates": ["gate1"],
            "shortterm_limit_type": "no_limit", "shortterm_limit": 0}
        })
        res = parse_setting("common/parking_areas2", gt)
        self.assert_result(dump_setting(res), gt)

    def test_parking_areas_no_cost_entries_without_shortterm(self):
        self.maxDiff = None
        with self.assertRaises(ValidationError) as e:
            gt = dump_setting({"0eec2445-15c3-4af8-b362-aeb1f278e3ac": {
                "id": "0eec2445-15c3-4af8-b362-aeb1f278e3ac", "default_cost_entries":
                    [{"entry_type": "rate_change", "group": "parking_default",
                      "value": "7a50fafd-3426-42c8-bf3c-ca708638c327", "account_id": "0"}],
                "pay_per_use_cost_entries":
                    [{"entry_type": "rate_change", "group": "parking_default",
                      "value": "7a50fafd-3426-42c8-bf3c-ca708638c327", "account_id": "0"}],
                "gates": ["gate1"], "name": "Gesamter Parkplatz", "shortterm_gates": [],
                "shortterm_limit_type": "no_limit", "shortterm_limit": 0}
            })
            parse_setting("common/parking_areas2", gt)
        self.assertEqual(str(e.exception).count("\n"), 2)
        self.assertIn("If no shortterm gates are defined, no default cost entries are allowed", str(e.exception))

    def test_parking_areas_gates_no_empty_list(self):
        with self.assertRaises(ValidationError) as e:
            parse_setting("common/parking_areas2", dump_setting({
                "0eec2445-15c3-4af8-b362-aeb1f278e3ac": {
                    "id": "0eec2445-15c3-4af8-b362-aeb1f278e3ac", "default_cost_entries":
                        [{"entry_type": "rate_change", "group": "parking_default",
                          "value": "7a50fafd-3426-42c8-bf3c-ca708638c327", "account_id": "0"}],
                    "gates": [], "name": "Gesamter Parkplatz", "shortterm_gates": [],
                    "shortterm_limit_type": "no_limit", "shortterm_limit": 0}
            }))
        self.assertEqual(str(e.exception).count("\n"), 2)
        self.assertIn("ensure this value has at least 1 items", str(e.exception))

    def test_parking_areas_not_a_uuid(self):
        with self.assertRaises(ValidationError) as e:
            parse_setting("common/parking_areas2", dump_setting({
                "0eec2445-15c3-4af8-b362-aeb1f278e3ac": {
                    "id": "123", "default_cost_entries":
                        [{"entry_type": "rate_change", "group": "parking_default",
                          "value": "7a50fafd-3426-42c8-bf3c-ca708638c327", "account_id": "0"}],
                    "gates": ["gate1"], "name": "Gesamter Parkplatz", "shortterm_gates": [],
                    "shortterm_limit_type": "no_limit", "shortterm_limit": 0}
            }))
        self.assertEqual(str(e.exception).count("\n"), 2)
        self.assertIn("must be a uuid string", str(e.exception))

    def test_parking_areas_id_does_not_match_field(self):
        with self.assertRaises(ValueError) as e:
            parse_setting("common/parking_areas2", dump_setting({
                "7a50fafd-3426-42c8-bf3c-ca708638c327": {
                    "id": "0eec2445-15c3-4af8-b362-aeb1f278e3ac", "default_cost_entries":
                        [{"entry_type": "rate_change", "group": "parking_default",
                          "value": "7a50fafd-3426-42c8-bf3c-ca708638c327", "account_id": "0"}],
                    "gates": ["gate1"], "name": "Gesamter Parkplatz", "shortterm_gates": ["gate1"],
                    "shortterm_limit_type": "no_limit", "shortterm_limit": 0}
            }))
        self.assertEqual(str(e.exception).count("\n"), 0)
        self.assertEqual("key must match field id", str(e.exception))

        with self.assertRaises(ValueError) as e:
            parse_setting("common/parking_areas2", dump_setting({
                "123": {
                    "id": "0eec2445-15c3-4af8-b362-aeb1f278e3ac", "default_cost_entries":
                        [{"entry_type": "rate_change", "group": "parking_default",
                          "value": "7a50fafd-3426-42c8-bf3c-ca708638c327", "account_id": "0"}],
                    "gates": ["gate1"], "name": "Gesamter Parkplatz", "shortterm_gates": ["gate1"],
                    "shortterm_limit_type": "no_limit", "shortterm_limit": 0}
            }))
        self.assertEqual(str(e.exception).count("\n"), 0)
        self.assertIn("key must match field id", str(e.exception))

    def test_parking_areas_invalid_default_cost_entry_type(self):
        with self.assertRaises(ValidationError) as e:
            parse_setting("common/parking_areas2", dump_setting({
                "0eec2445-15c3-4af8-b362-aeb1f278e3ac": {
                    "id": "0eec2445-15c3-4af8-b362-aeb1f278e3ac", "default_cost_entries":
                        [{"entry_type": "partial_rate_change", "group": "parking_default",
                          "value": "7a50fafd-3426-42c8-bf3c-ca708638c327", "account_id": "0"}],
                    "gates": ["gate1"], "name": "Gesamter Parkplatz", "shortterm_gates": [],
                    "shortterm_limit_type": "no_limit", "shortterm_limit": 0}
            }))
        self.assertEqual(str(e.exception).count("\n"), 2)
        self.assertIn("is not allowed as default cost entry in parking area", str(e.exception))

    def test_parking_areas_invalid_pay_per_use_cost_entry_type(self):
        with self.assertRaises(ValidationError) as e:
            parse_setting("common/parking_areas2", dump_setting({
                "0eec2445-15c3-4af8-b362-aeb1f278e3ac": {
                    "id": "0eec2445-15c3-4af8-b362-aeb1f278e3ac", "default_cost_entries": [],
                    "pay_per_use_cost_entries":
                        [{"entry_type": "partial_rate_change", "group": "parking_default",
                          "value": "7a50fafd-3426-42c8-bf3c-ca708638c327", "account_id": "0"}],
                    "gates": ["gate1"], "name": "Gesamter Parkplatz", "shortterm_gates": [],
                    "shortterm_limit_type": "no_limit", "shortterm_limit": 0}
            }))
        self.assertEqual(str(e.exception).count("\n"), 2)
        self.assertIn("is not allowed as pay per use cost entry in parking area", str(e.exception))

    def test_parking_areas_shortterm_gates_not_in_gates(self):
        with self.assertRaises(ValidationError) as e:
            parse_setting("common/parking_areas2", dump_setting({
                "0eec2445-15c3-4af8-b362-aeb1f278e3ac": {
                    "id": "0eec2445-15c3-4af8-b362-aeb1f278e3ac", "default_cost_entries":
                        [{"entry_type": "rate_change", "group": "parking_default",
                          "value": "7a50fafd-3426-42c8-bf3c-ca708638c327", "account_id": "0"}],
                    "gates": ["gate1"], "name": "Gesamter Parkplatz", "shortterm_gates": ["gate1", "gate2"],
                    "shortterm_limit_type": "no_limit", "shortterm_limit": 0}
            }))
        self.assertEqual(str(e.exception).count("\n"), 2)

        self.assertIn("All shortterm gates must be in gates", str(e.exception))
        with self.assertRaises(ValidationError) as e:
            parse_setting("common/parking_areas2", dump_setting({
                "0eec2445-15c3-4af8-b362-aeb1f278e3ac": {
                    "id": "0eec2445-15c3-4af8-b362-aeb1f278e3ac", "default_cost_entries":
                        [{"entry_type": "rate_change", "group": "parking_default",
                          "value": "7a50fafd-3426-42c8-bf3c-ca708638c327", "account_id": "0"}],
                    "gates": ["gate1"], "name": "Gesamter Parkplatz", "shortterm_gates": ["gate2"],
                    "shortterm_limit_type": "no_limit", "shortterm_limit": 0}
            }))
        self.assertEqual(str(e.exception).count("\n"), 2)
        self.assertIn("All shortterm gates must be in gates", str(e.exception))

    def test_parking_areas_none(self):
        with self.assertRaises(ValidationError) as e:
            parse_setting("common/parking_areas2", "null")
        self.assertEqual(len(e.exception.errors()), 1)
        self.assertIn("none is not an allowed value", str(e.exception))

    def test_timezone(self):
        parse_setting("common/timezone", dump_setting("Europe/Berlin"))
        with self.assertRaises(ValueError) as e:
            parse_setting("common/timezone", dump_setting("Europe/Graz"))
        self.assertEqual(str(e.exception).count("\n"), 0)
        self.assertEqual("timezone Europe/Graz unknown", str(e.exception))
        with self.assertRaises(ValidationError) as e:
            parse_setting("common/timezone", "null")
        self.assertEqual(len(e.exception.errors()), 1)
        self.assertIn("none is not an allowed value", str(e.exception))

    def test_language(self):
        parse_setting("common/language", dump_setting("en"))
        with self.assertRaises(ValueError) as e:
            parse_setting("common/language", dump_setting("english"))
        self.assertEqual(str(e.exception).count("\n"), 0)
        self.assertEqual("english is no valid language code", str(e.exception))
        with self.assertRaises(ValidationError) as e:
            parse_setting("common/language", "null")
        self.assertEqual(len(e.exception.errors()), 1)
        self.assertIn("none is not an allowed value", str(e.exception))

    def test_currency(self):
        parse_setting("common/currency", dump_setting("EUR"))
        with self.assertRaises(ValueError) as e:
            parse_setting("common/currency", dump_setting("euros"))
        self.assertEqual(str(e.exception).count("\n"), 0)
        self.assertEqual("Currency must be 3 uppercase letters", str(e.exception))
        with self.assertRaises(ValidationError) as e:
            parse_setting("common/currency", "null")
        self.assertEqual(len(e.exception.errors()), 1)
        self.assertIn("none is not an allowed value", str(e.exception))

    def test_location_none(self):
        with self.assertRaises(ValidationError) as e:
            parse_setting("common/location", "null")
        self.assertEqual(len(e.exception.errors()), 1)
        self.assertIn("none is not an allowed value", str(e.exception))

    def test_billing_none(self):
        with self.assertRaises(ValidationError) as e:
            parse_setting("common/billing", "null")
        self.assertEqual(len(e.exception.errors()), 1)
        self.assertIn("none is not an allowed value", str(e.exception))

    def test_support_success(self):
        gt = dump_setting({
            "name": "Test", "address": {
                "name": "Garage", "street": "Garagestreet", "number": "12c",
                "floor": "2H", "door": "7a", "supplements": "Frag nach Ines", "city": "Graz",
                "zip_code": "8020", "state": "Styria", "country": "Österreich"},
            "phone_number": "+43 123 456 789", "email_address": "ines@arivo.co", "website": "https://arivo.co/support"
        })
        res = parse_setting("common/support", gt)
        self.assert_result(res, gt)

    def test_support_not_given(self):
        gt = dump_setting({"name": "Test", "phone_number": "+43 123 456 789"})
        res = parse_setting("common/support", gt)
        self.assert_result(res, gt)
        gt = dump_setting({"name": "Test", "website": "https://arivo.co"})
        res = parse_setting("common/support", gt)
        self.assert_result(res, gt)

        with self.assertRaises(ValidationError) as e:
            gt = dump_setting({"name": "Test"})
            res = parse_setting("common/support", gt)
            self.assert_result(res, gt)
        self.assertEqual(str(e.exception).count("\n"), 2)
        self.assertIn("At least one of address, phone_number, email_address or website must be given", str(e.exception))

    def test_support_invalid_email(self):
        with self.assertRaises(ValidationError) as e:
            parse_setting("common/support", dump_setting({
                "name": "Test", "address": {
                    "name": "Garage", "street": "Garagestreet", "number": "12c",
                    "floor": "2H", "door": "7a", "supplements": "Frag nach Ines", "city": "Graz",
                    "zip_code": "8020", "state": "Styria", "country": "Österreich"},
                "phone_number": "+43 123 456 789", "email_address": "my-great-email"
            }))
        self.assertEqual(str(e.exception).count("\n"), 2)
        self.assertIn("string does not match regex", str(e.exception))

        with self.assertRaises(ValidationError) as e:
            parse_setting("common/support", dump_setting({
                "name": "Test", "address": {
                    "name": "Garage", "street": "Garagestreet", "number": "12c",
                    "floor": "2H", "door": "7a", "supplements": "Frag nach Ines", "city": "Graz",
                    "zip_code": "8020", "state": "Styria", "country": "Österreich"},
                "phone_number": "+43 123 456 789", "email_address": ""
            }))
        self.assertEqual(str(e.exception).count("\n"), 2)
        self.assertIn("ensure this value has at least 3 characters", str(e.exception))

    def test_support_invalid_phone_number(self):
        with self.assertRaises(ValidationError) as e:
            parse_setting("common/support", dump_setting({
                "name": "Test", "address": {
                    "name": "Garage", "street": "Garagestreet", "number": "12c",
                    "floor": "2H", "door": "7a", "supplements": "Frag nach Ines", "city": "Graz",
                    "zip_code": "8020", "state": "Styria", "country": "Österreich"},
                "phone_number": "my phone number", "email_address": "ines@arivo.co"
            }))
        self.assertEqual(str(e.exception).count("\n"), 2)
        self.assertIn("string does not match regex", str(e.exception))

        with self.assertRaises(ValidationError) as e:
            parse_setting("common/support", dump_setting({
                "name": "Test", "address": {
                    "name": "Garage", "street": "Garagestreet", "number": "12c",
                    "floor": "2H", "door": "7a", "supplements": "Frag nach Ines", "city": "Graz",
                    "zip_code": "8020", "state": "Styria", "country": "Österreich"},
                "phone_number": "", "email_address": "ines@arivo.co"
            }))
        self.assertEqual(str(e.exception).count("\n"), 2)
        self.assertIn("ensure this value has at least 3 characters", str(e.exception))

    def test_support_none(self):
        with self.assertRaises(ValidationError) as e:
            parse_setting("common/support", "null")
        self.assertEqual(len(e.exception.errors()), 1)
        self.assertIn("none is not an allowed value", str(e.exception))

    def test_garage_name(self):
        gt = dump_setting({"name": "Test", "slug": "test_123ABC", "technical_name": "test"})
        res = parse_setting("common/garage_name", gt)
        self.assert_result(dump_setting(res), gt)

        with self.assertRaises(ValidationError) as e:
            parse_setting("common/garage_name", dump_setting({
                "name": "Test", "slug": "test", "technical_name": "TEST"
            }))
        self.assertEqual(str(e.exception).count("\n"), 2)
        self.assertIn("__root__ -> technical_name", str(e.exception))
        self.assertIn("string does not match regex", str(e.exception))

        with self.assertRaises(ValidationError) as e:
            parse_setting("common/garage_name", dump_setting({
                "name": "test", "slug": "test.123", "technical_name": "test"
            }))
        self.assertEqual(str(e.exception).count("\n"), 2)
        self.assertIn("__root__ -> slug", str(e.exception))
        self.assertIn("string does not match regex", str(e.exception))

        with self.assertRaises(ValidationError) as e:
            parse_setting("common/garage_name", dump_setting({
                "name": "test", "slug": "töst", "technical_name": "test"
            }))
        self.assertEqual(str(e.exception).count("\n"), 2)
        self.assertIn("__root__ -> slug", str(e.exception))
        self.assertIn("string does not match regex", str(e.exception))

        with self.assertRaises(ValidationError) as e:
            parse_setting("common/garage_name", dump_setting({
                "name": "test", "slug": "test/123", "technical_name": "test"
            }))
        self.assertEqual(str(e.exception).count("\n"), 2)
        self.assertIn("__root__ -> slug", str(e.exception))
        self.assertIn("string does not match regex", str(e.exception))
        with self.assertRaises(ValidationError) as e:
            parse_setting("common/garage_name", "null")
        self.assertEqual(len(e.exception.errors()), 1)
        self.assertIn("none is not an allowed value", str(e.exception))

    def test_garage_settings_freeflow(self):
        expected_gt = dump_setting({"mode": "freeflow", "honest_payment_enabled": True,
                                    "enforcement_enabled": True, "payment_possible": True})
        gt = dump_setting({"mode": "freeflow"})
        res = parse_setting("common/garage_settings", gt)
        self.assert_result(dump_setting(res), expected_gt)

        gt = dump_setting({"mode": "freeflow", "honest_payment_enabled": False,
                           "enforcement_enabled": False, "payment_possible": False})
        res = parse_setting("common/garage_settings", gt)
        self.assert_result(dump_setting(res), expected_gt)

    def test_garage_settings_freeflow_surveillance(self):
        expected_gt = dump_setting({"mode": "freeflow_surveillance", "honest_payment_enabled": False,
                                    "enforcement_enabled": False, "payment_possible": False})

        gt = dump_setting({"mode": "freeflow_surveillance"})
        res = parse_setting("common/garage_settings", gt)
        self.assert_result(dump_setting(res), expected_gt)

        gt = dump_setting({"mode": "freeflow_surveillance", "honest_payment_enabled": True,
                           "enforcement_enabled": True, "payment_possible": True})
        res = parse_setting("common/garage_settings", gt)
        self.assert_result(dump_setting(res), expected_gt)

    def test_garage_settings_barrier(self):
        expected_gt = dump_setting({"mode": "barrier", "honest_payment_enabled": False,
                                    "enforcement_enabled": False, "payment_possible": True})

        gt = dump_setting({"mode": "barrier"})
        res = parse_setting("common/garage_settings", gt)
        self.assert_result(dump_setting(res), expected_gt)

        gt = dump_setting({"mode": "barrier", "honest_payment_enabled": True,
                           "enforcement_enabled": True, "payment_possible": False})
        res = parse_setting("common/garage_settings", gt)
        self.assert_result(dump_setting(res), expected_gt)

    def test_garage_settings_none(self):
        with self.assertRaises(ValidationError) as e:
            parse_setting("common/garage_settings", "null")
        self.assertEqual(len(e.exception.errors()), 1)
        self.assertIn("none is not an allowed value", str(e.exception))

    def test_gate_control_day_mode_invalid_format(self):
        # start
        with self.assertRaises(ValidationError) as e:
            parse_setting("gate_control/day_mode", dump_setting({
                "start": "24", "end": "00:00", "enabled": True
            }))
        self.assertEqual(str(e.exception).count("\n"), 2)
        self.assertIn("Field must be string of form HH:MM", str(e.exception))

        # end
        with self.assertRaises(ValidationError) as e:
            parse_setting("gate_control/day_mode", dump_setting({
                "start": "00:00", "end": "24", "enabled": True
            }))
        self.assertEqual(str(e.exception).count("\n"), 2)
        self.assertIn("Field must be string of form HH:MM", str(e.exception))

    def test_gate_control_day_mode_none(self):
        res = parse_setting("gate_control/day_mode", "null")
        self.assert_result("null", dump_setting(res))

    def test_gate_control_mode(self):
        res = parse_setting("gate_control/mode", "null")
        self.assert_result("null", dump_setting(res))

    def test_device_keys_pairing(self):
        gt = {"key": "1234567890", "created_at": "2000-01-01 02:00:00+01:00", "revision": 1}
        res = parse_setting("device_keys/pairing", dump_setting(gt))
        self.assert_not_result(res, gt)
        self.assertNotEqual(str(res.created_at), gt["created_at"])
        self.assertEqual(str(res.created_at), "2000-01-01 01:00:00")

        with self.assertRaises(ValidationError) as e:
            parse_setting("device_keys/pairing", "null")
        self.assertEqual(len(e.exception.errors()), 1)
        self.assertIn("none is not an allowed value", str(e.exception))

    def test_device_keys_cert(self):
        res = parse_setting("device_keys/cert", "null")
        self.assert_result("null", dump_setting(res))

    def test_device_keys_otp(self):
        res = parse_setting("device_keys/otp", "null")
        self.assert_result("null", dump_setting(res))

    def test_urls(self):
        # payapp_domain
        with self.assertRaises(ValidationError) as e:
            parse_setting("common/urls", dump_setting({
                "payapp_short_url": "https://payapp.arivo.co/test",
                "payapp_domain": "https://payapp.arivo.co/",
                "receipt_domain": "https://receipt.arivo.co"
            }))
        self.assertEqual(str(e.exception).count("\n"), 2)
        self.assertIn("Domains must not have a trailing /", str(e.exception))

        # receipt_domain
        with self.assertRaises(ValidationError) as e:
            parse_setting("common/urls", dump_setting({
                "payapp_short_url": "https://payapp.arivo.co/test",
                "payapp_domain": "https://payapp.arivo.co",
                "receipt_domain": "https://receipt.arivo.co/"
            }))
        self.assertEqual(str(e.exception).count("\n"), 2)
        self.assertIn("Domains must not have a trailing /", str(e.exception))
        with self.assertRaises(ValidationError) as e:
            parse_setting("common/urls", "null")
        self.assertEqual(len(e.exception.errors()), 1)
        self.assertIn("none is not an allowed value", str(e.exception))

    def test_custom_type_not_validated(self):
        # id does not match key, but custom type is used
        gt = {"9999a7e2-be78-488e-8d1a-1486f7da9999": {
            "id": "0000a7e2-be78-488e-8d1a-1486f7da0000",
            "name": "Dauerparker ohne Kosten",
            "gates": ["gate1"],
            "default_cost_entries": []}}
        res = parse_setting("common/parksettings2", dump_setting(gt), custom_type=Parksettings)
        self.assert_result(res, gt)

    def test_intercom(self):
        setting_str = '{"enabled": false, "phone_number": null}'
        res = parse_setting("intercom/basic_settings", setting_str)
        self.assert_result(setting_str, dump_setting(res))

        setting_str = '{"enabled": true, "phone_number": null}'
        with self.assertRaises(ValidationError) as e:
            parse_setting("intercom/basic_settings", setting_str)
        self.assertEqual(str(e.exception).count("\n"), 2)
        self.assertIn("phone_number must be set if intercom is enabled", str(e.exception))
        with self.assertRaises(ValidationError) as e:
            parse_setting("intercom/basic_settings", "null")
        self.assertEqual(len(e.exception.errors()), 1)
        self.assertIn("none is not an allowed value", str(e.exception))

    def test_enforcement(self):
        setting_str = '{"strictness": 0, "payment_deadline_hours": 1, "enabled": true, ' \
                      '"ai_enabled": true, "last_edited": "2024-02-19T13:06:51.140075"}'
        res = parse_setting("enforcement/basic_settings", setting_str)
        self.assert_result(setting_str, dump_setting(res))

        setting_str = '{"strictness": 0, "payment_deadline_hours": 0, "enabled": true, ' \
                      '"ai_enabled": true, "last_edited": "2024-02-19T13:06:51.140075"}'
        with self.assertRaises(ValidationError) as e:
            parse_setting("enforcement/basic_settings", setting_str)
        self.assertIn("ensure this value is greater than 0", str(e.exception))

        setting_str = '{"strictness": 0, "payment_deadline_hours": 960, "enabled": true, ' \
                      '"ai_enabled": true, "last_edited": "2024-02-19T13:06:51.140075"}'  # 40 days * 24
        res = parse_setting("enforcement/basic_settings", setting_str)
        self.assert_result(setting_str, dump_setting(res))

        setting_str = '{"strictness": 0, "payment_deadline_hours": 961, "enabled": true, ' \
                      '"ai_enabled": true, "last_edited": "2024-02-19T13:06:51.140075"}'  # 40 days * 24 + 1
        with self.assertRaises(ValidationError) as e:
            parse_setting("enforcement/basic_settings", setting_str)
        self.assertIn("ensure this value is less than or equal to 960", str(e.exception))

        # test ai_enabled
        setting_str = '{"strictness": 0, "payment_deadline_hours": 1, "enabled": true, ' \
                      '"ai_enabled": false, "last_edited": "2027-11-11T11:11:11"}'
        setting = parse_setting("enforcement/basic_settings", setting_str)
        self.assertFalse(setting.ai_enabled)
        setting_str = '{"strictness": 0, "payment_deadline_hours": 1, "enabled": true, ' \
                      '"ai_enabled": true, "last_edited": "2027-11-11T11:11:11"}'
        setting = parse_setting("enforcement/basic_settings", setting_str)
        self.assertTrue(setting.ai_enabled)
        # if the value is not present, then the default value of activated should be used
        setting_str = '{"strictness": 0, "payment_deadline_hours": 1, "enabled": true, ' \
                      '"last_edited": "2027-11-11T11:11:11"}'
        setting = parse_setting("enforcement/basic_settings", setting_str)
        self.assertTrue(setting.ai_enabled)

        # test strictness is now optional and deprecated
        setting_str = '{"payment_deadline_hours": 1, "enabled": true, ' \
                      '"last_edited": "2027-11-11T11:11:11"}'
        setting = parse_setting("enforcement/basic_settings", setting_str)
        strictness = setting.strictness
        self.assertEqual(strictness, 2)
        # could not re-create the same behavior as in Pydantic v2,
        # so at least we have a validator which prints the warning
        setting_str = '{"strictness": 99, "payment_deadline_hours": 1, "enabled": true, ' \
                      '"last_edited": "2027-11-11T11:11:11"}'
        with warnings.catch_warnings(record=True) as w:
            setting = parse_setting("enforcement/basic_settings", setting_str)
        strictness = setting.strictness
        self.assertEqual(strictness, 99)
        self.assertEqual(len(w), 1)
        self.assertTrue(issubclass(w[-1].category, DeprecationWarning))
        self.assertIn("The field `EnforcementSettings.strictness` is deprecated "
                      "and will be removed in a future version.", str(w[-1].message))

    def test_io_signals_correct_fields_gate_related(self):
        for t in [SignalType.permanently_closed, SignalType.shortterm_full, SignalType.open, SignalType.close_pulse,
                  SignalType.present_raw, SignalType.present_decision, SignalType.traffic_light_green]:
            setting_str = (
                    '{"entry-open": {"signal":"entry-open","gate":"entry","type":"' + t.value + '","name":"EF open"}}')
            res = parse_setting("io/signals", setting_str)
            self.assert_result(setting_str, dump_setting(res))

            setting_str = '{"entry-open": {"signal":"entry-open","type":"' + t.value + '","name":"EF open"}}'
            with self.assertRaises(ValueError, msg=t) as e:
                res = parse_setting("io/signals", setting_str)
            self.assertIn("gate must not be None and parking_area_id must be None for gate related signal",
                          str(e.exception), t)

            setting_str = ('{"entry-open":{"signal":"entry-open","gate":"entry","parking_area_id":"pa1","type":"'
                           + t.value + '","name":"EF open"}}')
            with self.assertRaises(ValueError, msg=t) as e:
                res = parse_setting("io/signals", setting_str)
            self.assertIn("gate must not be None and parking_area_id must be None for gate related signal",
                          str(e.exception), t)

    def test_io_signals_correct_fields_area_related(self):
        setting_str = \
            '{"pa1-area_full": {"signal":"pa1-area_full","parking_area_id":"pa1","type":"area_full","name":"PA1 full"}}'
        res = parse_setting("io/signals", setting_str)
        self.assert_result(setting_str, dump_setting(res))

        setting_str = '{"pa1-area_full": {"signal":"pa1-area_full","type":"area_full","name":"PA1 full"}}'
        with self.assertRaises(ValueError) as e:
            res = parse_setting("io/signals", setting_str)
        self.assertIn("parking_area_id must not be None and gate must be None for area_full signal", str(e.exception))

        setting_str = ('{"pa1-area_full": {"signal":"pa1-area_full","parking_area_id":"pa1","type":"area_full",'
                       '"name":"PA1 full","gate":"entry"}}')
        with self.assertRaises(ValueError) as e:
            res = parse_setting("io/signals", setting_str)
        self.assertIn("parking_area_id must not be None and gate must be None for area_full signal", str(e.exception))

    def test_io_signals_correct_fields_parkinglot_full(self):
        setting_str = '{"parkinglot_full": {"signal":"parkinglot_full","type":"parkinglot_full","name":"Full"}}'
        res = parse_setting("io/signals", setting_str)
        self.assert_result(setting_str, dump_setting(res))

        setting_str = \
            '{"parkinglot_full": {"signal":"parkinglot_full","type":"parkinglot_full","name":"Full","gate":"entry"}}'
        with self.assertRaises(ValueError) as e:
            res = parse_setting("io/signals", setting_str)
        self.assertIn("gate and parking_area_id must be None for parkinglot_full signal", str(e.exception))

        setting_str = ('{"parkinglot_full": {"signal":"parkinglot_full","type":"parkinglot_full","name":"Full",'
                       '"parking_area_id":"pa1"}}')
        with self.assertRaises(ValueError) as e:
            res = parse_setting("io/signals", setting_str)
        self.assertIn("gate and parking_area_id must be None for parkinglot_full signal", str(e.exception))

        setting_str = '{"test": {"signal":"test","type":"parkinglot_full","name":"Full"}}'
        with self.assertRaises(ValueError) as e:
            res = parse_setting("io/signals", setting_str)
        self.assertIn("only signal parkinglot_full can be of type parkinglot_full", str(e.exception))

    def test_io_signals_key_does_not_match_field(self):
        with self.assertRaises(ValueError) as e:
            parse_setting("io/signals", '{"t": {"signal":"parkinglot_full","type":"parkinglot_full","name":"Full"}}')
        self.assertEqual(str(e.exception).count("\n"), 0)
        self.assertEqual("key must match field signal", str(e.exception))

    def test_io_inputs_correct_fields(self):
        for t in [InputType.presence_loop, InputType.presence_laserscanner, InputType.presence_narrow,
                  InputType.safety_loop, InputType.safety_laserscanner, InputType.safety_narrow]:
            setting_str = ('{"entry-t":{"input":"entry-t","type":"' + t.value +
                           '","gate":"entry","name":"EF CLoop","active":true}}')
            res = parse_setting("io/inputs", setting_str)
            self.assert_result(setting_str, dump_setting(res))

            setting_str = '{"entry-t":{"input":"entry-t","type":"' + t.value + '","name":"EF CLoop","active":true}}'
            with self.assertRaises(ValueError) as e:
                res = parse_setting("io/inputs", setting_str)
            self.assertIn("gate must not be None for inputs except of type custom", str(e.exception))

    def test_io_inputs_key_does_not_match_field(self):
        with self.assertRaises(ValueError) as e:
            parse_setting("io/inputs", '{"t":{"input":"entry-safety_loop","type":"safety_loop","gate":"entry",'
                                       '"name":"EF CLoop","active":true}}')
        self.assertEqual(str(e.exception).count("\n"), 0)
        self.assertEqual("key must match field input", str(e.exception))

    def test_enforcement_none(self):
        res = parse_setting("enforcement/basic_settings", "null")
        self.assert_result("null", dump_setting(res))

    def test_assets_visual_key_does_not_match_field(self):
        with self.assertRaises(ValueError) as e:
            parse_setting("assets/visuals", '{"x":{"type":"y","value":"z"}}')
        self.assertEqual(str(e.exception).count("\n"), 0)
        self.assertEqual("key must match field type", str(e.exception))

    def test_assets_visual_value(self):
        with self.assertRaises(ValueError) as e:
            parse_setting("assets/visuals", '{"logo":{"type":"logo","value":[]}}')
        self.assertIn("Field value must be a string (URL) for logo and marketing_image types", str(e.exception))

    @patch("settings_models.settings.assets.datetime")
    def test_assets_visual_auto_created(self, mock_datetime):
        t1 = datetime(2025, 1, 1, 12)
        t2 = datetime(2024, 12, 31, 12, 59, 59)
        mock_datetime.now.side_effect = [t1]
        res = parse_setting("assets/visuals", '{"x":{"type":"x","value":"y"},'
                                              '"a":{"type":"a","value":"b","created":"2024-12-31T12:59:59"}}')

        self.assertEqual(res["x"].created, t1)
        self.assertEqual(res["a"].created, t2)
