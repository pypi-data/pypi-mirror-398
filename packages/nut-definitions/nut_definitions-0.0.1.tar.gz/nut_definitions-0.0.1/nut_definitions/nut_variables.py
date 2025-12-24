"""
Possible NUT variables as specified in
https://networkupstools.org/docs/developer-guide.chunked/_variables.html
"""

from enum import Enum

from .nut_enums import BeeperStatus, DeviceType, UpsMode, UpsStatus


class NutVariable:
    def __init__(
        self,
        name: str,
        value: str | int | float | Enum,
        options: list[str] | None = None,
    ):
        """Never use this constructor outside this class!"""
        self.name = name
        self.value = value
        self.options = options

        if isinstance(value, str):
            self.vType = "STRING:30"
        if isinstance(value, int) or isinstance(value, float):
            self.vType = "NUMBER"
        if isinstance(value, Enum):
            self.vType = "ENUM"

    # region device

    @staticmethod
    def device_model(value: str):
        """Device model"""
        return NutVariable("device.model", value)

    @staticmethod
    def device_mfr(value: str):
        """Device manufacturer"""
        return NutVariable("device.mfr", value)

    @staticmethod
    def device_serial(value: str):
        """Device serial number (opaque string)"""
        return NutVariable("device.serial", value)

    @staticmethod
    def device_type(value: DeviceType):
        """Device type (ups, pdu, scd, psu, ats)"""
        return NutVariable("device.type", value.value)

    @staticmethod
    def device_description(value: str):
        """Device description (opaque string)"""
        return NutVariable("device.description", value)

    @staticmethod
    def device_contact(value: str):
        """Device administrator name (opaque string)"""
        return NutVariable("device.contact", value)

    @staticmethod
    def device_location(value: str):
        """Device physical location (opaque string)"""
        return NutVariable("device.location", value)

    @staticmethod
    def device_part(value: str):
        """Device part number (opaque string)"""
        return NutVariable("device.part", value)

    @staticmethod
    def device_macaddr(value: str):
        """Physical network address of the device"""
        return NutVariable("device.macaddr", value)

    @staticmethod
    def device_uptime(value: int):
        """Device uptime in seconds"""
        return NutVariable("device.uptime", value)

    @staticmethod
    def device_count(value: int):
        """Total number of daisychained devices"""
        return NutVariable("device.count", value)

    @staticmethod
    def device_usb_version(value: str):
        """Device (firmware-reported) USB version"""
        return NutVariable("device.usb.version", value)

    # endregion

    # region ups

    @staticmethod
    def ups_status(values: list[UpsStatus]):
        """UPS status (opaque string comprised of space-separated tokens; many of those are ascribed certain meanings)"""
        return NutVariable("ups.status", " ".join([v.value for v in values]))

    @staticmethod
    def ups_alarm(value: str):
        """UPS alarms (opaque string, may be a collection of whole sentences; separate entries may be enclosed in brackets for convenience)"""
        return NutVariable("ups.alarm", value)

    @staticmethod
    def ups_time(value: str):
        """Internal UPS clock time (opaque string)"""
        return NutVariable("ups.time", value)

    @staticmethod
    def ups_date(value: str):
        """Internal UPS clock date (opaque string)"""
        return NutVariable("ups.date", value)

    @staticmethod
    def ups_model(value: str):
        """UPS model"""
        return NutVariable("ups.model", value)

    @staticmethod
    def ups_mfr(value: str):
        """UPS manufacturer"""
        return NutVariable("ups.mfr", value)

    @staticmethod
    def ups_mfr_date(value: str):
        """UPS manufacturing date (opaque string)"""
        return NutVariable("ups.mfr.date", value)

    @staticmethod
    def ups_serial(value: str):
        """UPS serial number (opaque string)"""
        return NutVariable("ups.serial", value)

    @staticmethod
    def ups_vendorid(value: str):
        """Vendor ID for USB devices"""
        return NutVariable("ups.vendorid", value)

    @staticmethod
    def ups_productid(value: str):
        """Product ID for USB devices"""
        return NutVariable("ups.productid", value)

    @staticmethod
    def ups_firmware(value: str):
        """UPS firmware (opaque string)"""
        return NutVariable("ups.firmware", value)

    @staticmethod
    def ups_firmware_aux(value: str):
        """Auxiliary device firmware"""
        return NutVariable("ups.firmware.aux", value)

    @staticmethod
    def ups_temperature(value: float):
        """UPS temperature (degrees C)"""
        return NutVariable("ups.temperature", value)

    @staticmethod
    def ups_load(value: float):
        """Load on UPS (percent)"""
        return NutVariable("ups.load", value)

    @staticmethod
    def ups_load_high(value: float):
        """Load when UPS switches to overload condition ("OVER") (percent)"""
        return NutVariable("ups.load.high", value)

    @staticmethod
    def ups_id(value: str):
        """UPS system identifier (opaque string)"""
        return NutVariable("ups.id", value)

    @staticmethod
    def ups_delay_start(value: int):
        """Interval to wait before restarting the load (seconds)"""
        return NutVariable("ups.delay.start", value)

    @staticmethod
    def ups_delay_reboot(value: int):
        """Interval to wait before rebooting the UPS (seconds)"""
        return NutVariable("ups.delay.reboot", value)

    @staticmethod
    def ups_delay_shutdown(value: int):
        """Interval to wait after shutdown with delay command (seconds)"""
        return NutVariable("ups.delay.shutdown", value)

    @staticmethod
    def ups_timer_start(value: int):
        """Time before the load will be started (seconds)"""
        return NutVariable("ups.timer.start", value)

    @staticmethod
    def ups_timer_reboot(value: int):
        """Time before the load will be rebooted (seconds)"""
        return NutVariable("ups.timer.reboot", value)

    @staticmethod
    def ups_timer_shutdown(value: int):
        """Time before the load will be shutdown (seconds)"""
        return NutVariable("ups.timer.shutdown", value)

    @staticmethod
    def ups_test_interval(value: int):
        """Interval between self tests (seconds)"""
        return NutVariable("ups.test.interval", value)

    @staticmethod
    def ups_test_result(value: str):
        """Results of last self test (opaque string)"""
        return NutVariable("ups.test.result", value)

    @staticmethod
    def ups_test_date(value: str):
        """Date of last self test (opaque string)"""
        return NutVariable("ups.test.date", value)

    @staticmethod
    def ups_display_language(value: str):
        """Language to use on front panel (* opaque)"""
        return NutVariable("ups.display.language", value)

    @staticmethod
    def ups_contacts(value: str):
        """UPS external contact sensors (* opaque)"""
        return NutVariable("ups.contacts", value)

    @staticmethod
    def ups_efficiency(value: float):
        """Efficiency of the UPS (ratio of the output current on the input current) (percent)"""
        return NutVariable("ups.efficiency", value)

    @staticmethod
    def ups_power(value: float):
        """Current value of apparent power (Volt-Amps)"""
        return NutVariable("ups.power", value)

    @staticmethod
    def ups_power_nominal(value: float):
        """Nominal value of apparent power (Volt-Amps)"""
        return NutVariable("ups.power.nominal", value)

    @staticmethod
    def ups_realpower(value: float):
        """Current value of real power (Watts)"""
        return NutVariable("ups.realpower", value)

    @staticmethod
    def ups_realpower_nominal(value: float):
        """Nominal value of real power (Watts)"""
        return NutVariable("ups.realpower.nominal", value)

    @staticmethod
    def ups_beeper_status(value: BeeperStatus):
        """UPS beeper status (enabled, disabled or muted)"""
        return NutVariable("ups.beeper.status", value.value)

    @staticmethod
    def ups_type(value: str):
        """UPS type (* opaque)"""
        return NutVariable("ups.type", value)

    @staticmethod
    def ups_mode(value: UpsMode):
        """Current UPS mode"""
        return NutVariable("ups.mode", value.value)

    @staticmethod
    def ups_watchdog_status(value: str):
        """UPS watchdog status (enabled or disabled)"""
        return NutVariable("ups.watchdog.status", value)

    @staticmethod
    def ups_start_auto(value: str):
        """UPS starts when mains is (re)applied"""
        return NutVariable("ups.start.auto", value)

    @staticmethod
    def ups_start_battery(value: str):
        """Allow to start UPS from battery"""
        return NutVariable("ups.start.battery", value)

    @staticmethod
    def ups_start_reboot(value: str):
        """UPS coldstarts from battery (enabled or disabled)"""
        return NutVariable("ups.start.reboot", value)

    @staticmethod
    def ups_shutdown(value: str):
        """Enable or disable UPS shutdown ability (poweroff)"""
        return NutVariable("ups.shutdown", value)

    # endregion

    # region input

    # TODO

    # endregion

    # region output

    # TODO

    # endregion

    # region battery

    @staticmethod
    def battery_charge(value: float):
        """Battery charge (percent)"""
        return NutVariable("battery.charge", value)

    # TODO

    # endregion
