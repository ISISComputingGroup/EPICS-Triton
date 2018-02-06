import unittest
from unittest import skipIf

from utils.channel_access import ChannelAccess
from utils.ioc_launcher import IOCRegister
from utils.testing import get_running_lewis_and_ioc

DEVICE_PREFIX = "TRITON_01"

PID_TEST_VALUES = 0, 10**-5, 123.45, 10**5
TEMPERATURE_TEST_VALUES = 0, 10**-5, 5.4321, 250
PRESSURE_TEST_VALUES = TEMPERATURE_TEST_VALUES
HEATER_RANGE_TEST_VALUES = 0.001, 0.316, 1000
RESISTANCE_TEST_VALUES = 10, 3456
EXCITATION_TEST_VALUES = PID_TEST_VALUES
TIME_DELAY_TEST_VALUES = RESISTANCE_TEST_VALUES

VALID_TEMPERATURE_SENSORS = [i for i in range(0, 6)]


class TritonTests(unittest.TestCase):
    """
    Tests for the Triton IOC.
    """
    def setUp(self):
        self._lewis, self._ioc = get_running_lewis_and_ioc("triton")
        self.ca = ChannelAccess(device_prefix=DEVICE_PREFIX)

    def test_WHEN_device_is_started_THEN_it_is_not_disabled(self):
        self.ca.assert_that_pv_is("DISABLE", "COMMS ENABLED")

    def test_WHEN_P_setpoint_is_set_THEN_readback_updates(self):
        for value in PID_TEST_VALUES:
            self.ca.assert_setting_setpoint_sets_readback(value, "P")

    def test_WHEN_I_setpoint_is_set_THEN_readback_updates(self):
        for value in PID_TEST_VALUES:
            self.ca.assert_setting_setpoint_sets_readback(value, "I")

    def test_WHEN_D_setpoint_is_set_THEN_readback_updates(self):
        for value in PID_TEST_VALUES:
            self.ca.assert_setting_setpoint_sets_readback(value, "D")

    def test_WHEN_temperature_setpoint_is_set_THEN_readback_updates(self):
        for value in TEMPERATURE_TEST_VALUES:
            self.ca.assert_setting_setpoint_sets_readback(value, set_point_pv="TEMP:SP", readback_pv="TEMP:SP:RBV")

    def test_WHEN_heater_range_is_set_THEN_readback_updates(self):
        for value in HEATER_RANGE_TEST_VALUES:
            self.ca.assert_setting_setpoint_sets_readback(value, "HEATER:RANGE")

    @skipIf(IOCRegister.uses_rec_sim, "Lewis backdoor not available in recsim")
    def test_WHEN_heater_power_is_set_via_backdoor_THEN_pv_has_the_value_just_set(self):
        for value in HEATER_RANGE_TEST_VALUES:
            self._lewis.backdoor_set_on_device("heater_power", value)
            self.ca.assert_that_pv_is("HEATER:POWER", value)

    @skipIf(IOCRegister.uses_rec_sim, "Lewis backdoor not available in recsim")
    def test_WHEN_closed_loop_mode_is_set_via_backdoor_THEN_the_closed_loop_pv_updates_with_value_just_set(self):
        for value in [False, True, False]:  # Need to check both transitions work properly
            self._lewis.backdoor_set_on_device("closed_loop", value)
            self.ca.assert_that_pv_is("CLOSEDLOOP", "On" if value else "Off")

    @skipIf(IOCRegister.uses_rec_sim, "Lewis backdoor not available in recsim")
    def test_WHEN_valve_state_is_set_via_backdoor_THEN_valve_state_pvs_update_with_value_just_set(self):
        for valve in range(1, 11):
            for valve_state in [False, True, False]:
                self._lewis.backdoor_command(["device", "set_valve_state_backdoor", str(valve), str(valve_state)])
                self.ca.assert_that_pv_is("VALVES:V{}:STATE".format(valve), "OPEN" if valve_state else "CLOSED")

    @skipIf(IOCRegister.uses_rec_sim, "Behaviour too complex for recsim")
    def test_WHEN_channels_are_enabled_and_disabled_via_pv_THEN_the_readback_pv_updates_with_value_just_set(self):
        for chan in VALID_TEMPERATURE_SENSORS:
            for enabled in [False, True, False]:  # Need to check both transitions work properly
                self.ca.assert_setting_setpoint_sets_readback(
                    "ON" if enabled else "OFF", "CHANNELS:T{}:STATE".format(chan))

    @skipIf(IOCRegister.uses_rec_sim, "Lewis backdoor not available in recsim")
    def test_WHEN_a_short_status_is_set_on_device_THEN_displayed_status_is_identical(self):
        # Status message that could be contained in an EPICS string type
        short_status = "Device status"
        assert 0 < len(short_status) < 40

        # Status message that device is likely to return - longer than EPICS string type but reasonable for a protocol
        medium_status = "This is a device status that contains a bit more information"
        assert 40 < len(medium_status) < 256

        # Short and medium statuses should be displayed in full.
        for status in [short_status, medium_status]:
            self._lewis.backdoor_set_on_device("status", status)
            self.ca.assert_that_pv_is("STATUS", status)

    @skipIf(IOCRegister.uses_rec_sim, "Lewis backdoor not available in recsim")
    def test_WHEN_long_status_is_set_on_device_THEN_displayed_status_truncated_but_displays_at_least_500_chars(self):

        # Somewhat arbitrary, but decide on a minimum number of characters that should be displayed in a
        # status message to the user if the status message is very long. This seems to be a reasonable
        # number given the messages expected, but the manual does not provide an exhaustive list.
        minimum_characters_in_pv = 500

        # Very long status message, used to check that very long messages can be handled gracefully
        long_status = "This device status is quite long:" + " (here is a load of information)" * 50

        assert minimum_characters_in_pv < len(long_status)

        # Allow truncation for long status, but it should still display as many characters as possible
        self._lewis.backdoor_set_on_device("status", long_status)
        self.ca.assert_pv_value_causes_func_to_return_true(
            "STATUS", lambda val: long_status.startswith(val) and len(val) >= minimum_characters_in_pv)

    @skipIf(IOCRegister.uses_rec_sim, "Lewis backdoor not available in recsim")
    def test_WHEN_automation_is_set_on_device_THEN_displayed_automation_is_identical(self):
        automations = [
            "Warming up to 200K",
            "Cooling down to 1K",
        ]

        for automation in automations:
            self._lewis.backdoor_set_on_device("automation", automation)
            self.ca.assert_that_pv_is("AUTOMATION", automation)

    def _set_temp_via_backdoor(self, channel, temp):
        self._lewis.backdoor_command(["device", "set_temperature_backdoor", "'{}'".format(channel), "{}".format(temp)])

    @skipIf(IOCRegister.uses_rec_sim, "Lewis backdoor not available in recsim")
    def test_WHEN_stil_temp_is_set_via_backdoor_THEN_pv_updates(self):
        for temp in TEMPERATURE_TEST_VALUES:
            self._set_temp_via_backdoor("STIL", temp)
            self.ca.assert_that_pv_is("STIL:TEMP", temp)

    @skipIf(IOCRegister.uses_rec_sim, "Lewis backdoor not available in recsim")
    def test_WHEN_mc_temp_is_set_via_backdoor_THEN_pv_updates(self):
        for temp in TEMPERATURE_TEST_VALUES:
            self._set_temp_via_backdoor("MC", temp)
            self.ca.assert_that_pv_is("MC:TEMP", temp)

    @skipIf(IOCRegister.uses_rec_sim, "Lewis backdoor not available in recsim")
    def test_WHEN_sorb_temp_is_set_via_backdoor_THEN_pv_updates(self):
        for temp in TEMPERATURE_TEST_VALUES:
            self._set_temp_via_backdoor("SORB", temp)
            self.ca.assert_that_pv_is("SORB:TEMP", temp)

    @skipIf(IOCRegister.uses_rec_sim, "Lewis backdoor not available in recsim")
    def test_WHEN_4KHX_temp_is_set_via_backdoor_THEN_pv_updates(self):
        for temp in TEMPERATURE_TEST_VALUES:
            self._set_temp_via_backdoor("PT2", temp)
            self.ca.assert_that_pv_is("4KHX:TEMP", temp)

    @skipIf(IOCRegister.uses_rec_sim, "Lewis backdoor not available in recsim")
    def test_WHEN_jthx_temp_is_set_via_backdoor_THEN_pv_updates(self):
        for temp in TEMPERATURE_TEST_VALUES:
            self._set_temp_via_backdoor("PT1", temp)
            self.ca.assert_that_pv_is("JTHX:TEMP", temp)

    @skipIf(IOCRegister.uses_rec_sim, "Lewis backdoor not available in recsim")
    def test_WHEN_pressure_is_set_via_backdoor_THEN_pressure_pv_updates(self):
        for sensor in [1, 2, 3, 5]:
            for pressure in PRESSURE_TEST_VALUES:
                self._lewis.backdoor_command(["device", "set_pressure_backdoor", str(sensor), str(pressure)])
                self.ca.assert_that_pv_is("PRESSURE:P{}".format(sensor), pressure)

    def test_WHEN_closed_loop_is_set_via_pv_THEN_readback_updates(self):
        for state in [False, True, False]:
            self.ca.assert_setting_setpoint_sets_readback("On" if state else "Off", "CLOSEDLOOP")

    @skipIf(IOCRegister.uses_rec_sim, "Lewis backdoor not available in recsim")
    def test_WHEN_read_mc_id_is_issued_via_arbitrary_command_THEN_response_is_in_format_device_uses(self):
        self.ca.set_pv_value("ARBITRARY:SP", "READ:SYS:DR:CHAN:MC")
        self.ca.assert_pv_value_causes_func_to_return_true("ARBITRARY",
                                                           lambda val: val.startswith("STAT:SYS:DR:CHAN:MC:"))

    @skipIf(IOCRegister.uses_rec_sim, "Lewis backdoor not available in recsim")
    def test_WHEN_channel_temperature_is_set_via_backdoor_THEN_the_pvs_update_with_values_just_written(self):
        for chan in VALID_TEMPERATURE_SENSORS:
            for value in TEMPERATURE_TEST_VALUES:
                self._lewis.backdoor_command(
                    ["device", "set_sensor_property_backdoor", str(chan), "temperature", str(value)]
                )
                self.ca.assert_that_pv_is("CHANNELS:T{}:TEMP".format(chan), value)

    @skipIf(IOCRegister.uses_rec_sim, "Lewis backdoor not available in recsim")
    def test_WHEN_channel_resistance_is_set_via_backdoor_THEN_the_pvs_update_with_values_just_written(self):
        for chan in VALID_TEMPERATURE_SENSORS:
            for value in RESISTANCE_TEST_VALUES:
                self._lewis.backdoor_command(
                    ["device", "set_sensor_property_backdoor", str(chan), "resistance", str(value)]
                )
                self.ca.assert_that_pv_is("CHANNELS:T{}:RES".format(chan), value)

    @skipIf(IOCRegister.uses_rec_sim, "Lewis backdoor not available in recsim")
    def test_WHEN_channel_excitation_is_set_via_backdoor_THEN_the_pvs_update_with_values_just_written(self):
        for chan in VALID_TEMPERATURE_SENSORS:
            for value in EXCITATION_TEST_VALUES:
                self._lewis.backdoor_command(
                    ["device", "set_sensor_property_backdoor", str(chan), "excitation", str(value)]
                )
                self.ca.assert_that_pv_is("CHANNELS:T{}:EXCITATION".format(chan), value)

    @skipIf(IOCRegister.uses_rec_sim, "Lewis backdoor not available in recsim")
    def test_WHEN_channel_pause_is_set_via_backdoor_THEN_the_pvs_update_with_values_just_written(self):
        for chan in VALID_TEMPERATURE_SENSORS:
            for value in TIME_DELAY_TEST_VALUES:
                self._lewis.backdoor_command(
                    ["device", "set_sensor_property_backdoor", str(chan), "pause", str(value)]
                )
                self.ca.assert_that_pv_is("CHANNELS:T{}:PAUSE".format(chan), value)

    @skipIf(IOCRegister.uses_rec_sim, "Lewis backdoor not available in recsim")
    def test_WHEN_channel_dwell_is_set_via_backdoor_THEN_the_pvs_update_with_values_just_written(self):
        for chan in VALID_TEMPERATURE_SENSORS:
            for value in TIME_DELAY_TEST_VALUES:
                self._lewis.backdoor_command(
                    ["device", "set_sensor_property_backdoor", str(chan), "dwell", str(value)]
                )
                self.ca.assert_that_pv_is("CHANNELS:T{}:DWELL".format(chan), value)

    @skipIf(IOCRegister.uses_rec_sim, "Lewis backdoor not available in recsim")
    def test_WHEN_heater_heater_current_is_set_via_backdoor_THEN_pv_updates_with_new_value(self):
        for curr in HEATER_RANGE_TEST_VALUES:
            self._lewis.backdoor_set_on_device("heater_current", curr)
            self.ca.assert_that_pv_is_number("HEATER:CURR", curr)

    @skipIf(IOCRegister.uses_rec_sim, "Lewis backdoor not available in recsim")
    def test_WHEN_heater_power_and_range_are_changed_THEN_heater_percent_power_is_calculated_correctly(self):
        for heater_range in HEATER_RANGE_TEST_VALUES:
            for current in HEATER_RANGE_TEST_VALUES:
                self._lewis.backdoor_set_on_device("heater_current", current)
                self._lewis.backdoor_set_on_device("heater_range", heater_range)

                assert heater_range != 0, "Heater range of zero will cause a zero division error!"
                self.ca.assert_that_pv_is_number("HEATER:PERCENT", 100*current/heater_range, tolerance=0.05)
