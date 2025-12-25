import enum

from . import flags

WialonMonthDayMask = enum.IntEnum(
    "WialonMonthDayMask",
    {
        f"DAY_{day}": mask
        for day, mask in {
            1: 2**0,
            2: 2**1,
            3: 2**2,
            4: 2**3,
            5: 2**4,
            6: 2**5,
            7: 2**6,
            8: 2**7,
            9: 2**8,
            10: 2**9,
            11: 2**10,
            12: 2**11,
            13: 2**12,
            14: 2**13,
            15: 2**14,
            16: 2**15,
            17: 2**16,
            18: 2**17,
            19: 2**18,
            20: 2**19,
            21: 2**20,
            22: 2**21,
            23: 2**22,
            24: 2**23,
            25: 2**24,
            26: 2**25,
            27: 2**26,
            28: 2**27,
            29: 2**28,
            30: 2**29,
            31: 2**30,
        }.items()
    },
)
"""
Wialon day of the month mask.

Usage:

.. code::
    
    # First of the month
    >> WialonMonthDayMask.DAY_1
    > 1
    # 16th day of the month
    >> WialonMonthDayMask.DAY_16
    > 32768

"""


class WialonMonthMask(enum.IntEnum):
    """Wialon month mask."""

    JANUARY = 2**0
    """January."""
    FEBRUARY = 2**1
    """February."""
    MARCH = 2**2
    """March."""
    APRIL = 2**3
    """April."""
    MAY = 2**4
    """May."""
    JUNE = 2**5
    """June."""
    JULY = 2**6
    """July."""
    AUGUST = 2**7
    """August."""
    SEPTEMBER = 2**8
    """September."""
    OCTOBER = 2**9
    """October."""
    NOVEMBER = 2**10
    """November."""
    DECEMBER = 2**11
    """December."""


class WialonWeekDayMask(enum.IntEnum):
    """Wialon day of the week mask."""

    MONDAY = 2**0
    """Monday."""
    TUESDAY = 2**1
    """Tuesday."""
    WEDNESDAY = 2**2
    """Wednesday."""
    THURSDAY = 2**3
    """Thursday."""
    FRIDAY = 2**4
    """Friday."""
    SATURDAY = 2**5
    """Saturday."""
    SUNDAY = 2**6
    """Sunday."""


class WialonLogAction(enum.StrEnum):
    """Wialon `log actions <https://wialon-help.link/28412fdb>`_."""

    CUSTOM_MSG = "custom_msg"
    """Manual record: '%s'."""
    CREATE_UNIT = "create_unit"
    """Unit '%s' created."""
    UPDATE_NAME = "update_name"
    """Name changed from '%s' to '%s'."""
    UPDATE_ACCESS = "update_access"
    """Access to %d '%s' changed."""
    UPDATE_UNIT_ICON = "update_unit_icon"
    """Unit icon changed."""
    UPDATE_UNIT_PASS = "update_unit_pass"
    """Access password changed."""
    UPDATE_UNIT_PHONE = "update_unit_phone"
    """Phone number changed from '%s' to '%s'."""
    UPDATE_UNIT_PHONE2 = "update_unit_phone2"
    """Second phone number changed from '%s' to '%s'."""
    UPDATE_UNIT_CALCFLAGS = "update_unit_calcflags"
    """Calculation flags changed."""
    UPDATE_UNIT_DRAT = "update_unit_drat"
    """Driver activity source changed."""
    UPDATE_UNIT_MILCOUNTER = "update_unit_milcounter"
    """Mileage counter changed from %d %s to %d %s."""
    UPDATE_UNIT_BYTECOUNTER = "update_unit_bytecounter"
    """GPRS traffic counter changed from %d KB to %d KB."""
    UPDATE_UNIT_EHCOUNTER = "update_unit_ehcounter"
    """Engine hours counter changed from %.2f h to %.2f h."""
    UPDATE_UNIT_UID = "update_unit_uid"
    """Unique ID changed from '%s' to '%s'."""
    UPDATE_UNIT_UID2 = "update_unit_uid2"
    """Second unique ID changed from '%s' to '%s'."""
    UPDATE_UNIT_HW = "update_unit_hw"
    """Device type changed from '%s' to '%s'."""
    UPDATE_UNIT_HW_CFG = "update_unit_hw_cfg"
    """Device configuration changed."""
    UPDATE_UNIT_FUEL_CFG = "udpate_unit_fuel_cfg"
    """Fuel consumption settings changed."""
    CREATE_SENSOR = "create_sensor"
    """Sensor '%s' created."""
    UPDATE_SENSOR = "update_sensor"
    """Sensor '%s' modified."""
    DELETE_SENSOR = "delete_sensor"
    """Sensor '%s' deleted."""
    CREATE_ALIAS = "create_alias"
    """Command '%s' created."""
    UPDATE_ALIAS = "update_alias"
    """Command '%s' modified."""
    DELETE_ALIAS = "delete_alias"
    """Command '%s' deleted."""
    CREATE_SERVICE_INTERVAL = "create_service_interval"
    """Service interval '%s' created."""
    UPDATE_SERVICE_INTERVAL = "update_service_interval"
    """Service interval '%s' modified."""
    DELETE_SERVICE_INTERVAL = "delete_service_interval"
    """Service interval '%s' deleted."""
    CREATE_CUSTOM_FIELD = "create_custom_field"
    """Custom field '%s' created."""
    UPDATE_CUSTOM_FIELD = "update_custom_field"
    """Custom field '%s' modified."""
    DELETE_CUSTOM_FIELD = "delete_custom_field"
    """Custom field '%s' deleted."""
    CREATE_ADMIN_FIELD = "create_admin_field"
    """Admin field '%s' created."""
    UPDATE_ADMIN_FIELD = "update_admin_field"
    """Admin field '%s' modified."""
    DELETE_ADMIN_FIELD = "delete_admin_field"
    """Admin field '%s' deleted."""
    UPDATE_PROFILE_FIELD = "update_profile_field"
    """Profile field '%s' modified."""
    DELETE_PROFILE_FIELD = "delete_profile_field"
    """Profile field '%s' deleted."""
    IMPORT_ITEM_CFG = "import_item_cfg"
    """Properties imported."""
    IMPORT_UNIT_CFG = "import_unit_cfg"
    """Properties imported."""
    EXPORT_UNIT_MSGS = "export_unit_msgs"
    """Messages exported."""
    IMPORT_UNIT_MSGS = "import_unit_msgs"
    """Messages imported."""
    DELETE_UNIT_MSG = "delete_unit_msg"
    """Deleted %d message dated %s."""
    DELETE_UNIT_MSGS = "delete_unit_msgs"
    """Deleted %s %d messages."""
    BIND_UNIT_DRIVER = "bind_unit_driver"
    """Driver '%s' was assigned at '%s'."""
    UNBIND_UNIT_DRIVER = "unbind_unit_driver"
    """Driver '%s' was separated at '%s'."""
    BIND_UNIT_TAG = "bind_unit_tag"
    """Passenger '%s' was assigned at '%s'."""
    UNBIND_UNIT_TAG = "unbind_unit_tag"
    """Passenger '%s' was separated at '%s'."""
    BIND_UNIT_TRAILER = "bind_unit_trailer"
    """Trailer '%s' was assigned at '%s'."""
    UNBIND_UNIT_TRAILER = "unbind_unit_trailer"
    """Trailer '%s' was separated at '%s'."""
    UPDATE_UNIT_REPORT_CFG = "update_unit_report_cfg"
    """Unit report settings changed."""
    UPDATE_MSGS_FILTER_CFG = "update_msgs_filter_cfg"
    """Message filtration settings changed."""
    DELETE_ITEM = "delete_item"
    """Item '%s' deleted."""
    CREATE_USER = "create_user"
    """User '%s' created."""
    UPDATE_HOSTS_MASK = "update_hosts_mask"
    """Host mask changed to '%s'."""
    UPDATE_USER_PASS = "update_user_pass"
    """User password changed."""
    UPDATE_USER_FLAGS = "update_user_flags"
    """User flags changed."""
    UPDATE_USER_LOCALE = "update_user_locale"
    """First day of week changed."""
    CREATE_USER_NOTIFY = "create_user_notify"
    """Notice to the user: '%s'."""
    DELETE_USER_NOTIFY = "delete_user_notify"
    """User notification '%s' deleted."""
    CREATE_GROUP = "create_group"
    """Unit group '%s' created."""
    UNITS_GROUP = "units_group"
    """
    Unit added to the group '%s'.
    Unit removed from the group '%s'.
    Units in group updated.
    """
    UPDATE_DRIVER_UNITS = "update_driver_units"
    """
    Unit attached to the resource of drivers '%s'.
    Unit removed from the resource of drivers '%s'.
    Automatic assignment list of drivers updated.
    """
    UPDATE_TRAILER_UNITS = "update_trailer_units"
    """
    Unit attached to the resource of trailers '%s'.
    Unit removed from the resource of trailers '%s'.
    Automatic assignment list of trailers updated.
    """
    CREATE_RESOURCE = "create_resource"
    """Resource '%s' created."""
    CREATE_ZONE = "create_zone"
    """Geofence '%s' created."""
    UPDATE_ZONE = "update_zone"
    """Geofence '%s' updated."""
    DELETE_ZONE = "delete_zone"
    """Geofence '%s' deleted."""
    UPDATE_TRACK_COLOR_SETTING = "update_track_color_setting"
    """
    Track colour settings changed to "By trips".
    Track colour settings changed to "Single".
    Track colour settings changed to "By speed".
    Track colour settings changed to "By sensor".
    """
    CREATE_JOB = "create_job"
    """Job '%s' created."""
    SWITCH_JOB = "switch_job"
    """Job '%s switched on/off."""
    UPDATE_JOB = "update_job"
    """Job '%s' updated."""
    DELETE_JOB = "delete_job"
    """Job '%s' deleted."""
    CREATE_NOTIFY = "create_notify"
    """Notification '%s' created."""
    SWITCH_NOTIFY = "switch_notify"
    """Notification '%s' switched on/off."""
    UPDATE_NOTIFY = "update_notify"
    """Notification '%s' updated."""
    DELETE_NOTIFY = "delete_notify"
    """Notification '%s' deleted."""
    CREATE_DRIVER = "create_driver"
    """Driver '%s' created."""
    UPDATE_DRIVER = "update_driver"
    """Driver '%s' updated."""
    DELETE_DRIVER = "delete_driver"
    """Driver '%s' deleted."""
    CREATE_TRAILER = "create_trailer"
    """Trailer '%s' created."""
    UPDATE_TRAILER = "update_trailer"
    """Trailer '%s' updated."""
    DELETE_TRAILER = "delete_trailer"
    """Trailer '%s' deleted."""
    CREATE_DRIVERS_GROUP = "create_drivers_group"
    """Group of drivers '%s' created."""
    UPDATE_DRIVERS_GROUP = "update_drivers_group"
    """Group of drivers '%s' updated."""
    DELETE_DRIVERS_GROUP = "delete_drivers_group"
    """Group of drivers '%s' deleted."""
    CREATE_TRAILERS_GROUP = "create_trailers_group"
    """Group of trailers '%s' created."""
    UPDATE_TRAILERS_GROUP = "update_trailers_group"
    """Group of trailers '%s' updated."""
    DELETE_TRAILERS_GROUP = "delete_trailers_group"
    """Group of trailers '%s' deleted."""
    CREATE_REPORT = "create_report"
    """Report template '%s' created."""
    UPDATE_REPORT = "update_report"
    """Report template '%s' updated."""
    DELETE_REPORT = "delete_report"
    """Report template '%s' deleted."""
    IMPORT_ZONES = "import_zones"
    """Geofences imported."""
    CREATE_RETRANSLATOR = "create_retranslator"
    """Retranslator '%s' created."""
    UPDATE_RETRANSLATOR = "update_retranslator"
    """Properties updated."""
    UNITS_RETRANSLATOR = "units_retranslator"
    """Units updated."""
    SWITCH_RETRANSLATOR = "switch_retranslator"
    """Started/stopped."""
    MSGS_HISTORY_RETRANSLATOR = "msgs_history_retranslator"
    """Past period retranslator started/stopped."""
    CREATE_ROUTE = "create_route"
    """Route '%s' created."""
    UPDATE_ROUTE_POINTS = "update_route_points"
    """Check points updated."""
    UPDATE_ROUTE_CFG = "update_route_cfg"
    """Properties updated."""
    CREATE_ROUND = "create_round"
    """Ride '%s' created."""
    UPDATE_ROUND = "update_round"
    """Ride '%s' updated."""
    DELETE_ROUND = "delete_round"
    """Ride '%s' deleted."""
    CREATE_SCHEDULE = "create_schedule"
    """Schedule '%s' created."""
    UPDATE_SCHEDULE = "update_schedule"
    """Schedule '%s' updated."""
    DELETE_SCHEDULE = "delete_schedule"
    """Schedule '%s' deleted."""
    CREATE_ACCOUNT = "create_account"
    """Account '%s' created."""
    DELETE_ACCOUNT = "delete_account"
    """Account '%s' deleted."""
    CHANGE_ACCOUNT = "change_account"
    """Account changed from '%s' to '%s'."""
    SWITCH_ACCOUNT = "switch_account"
    """Account blocked/unblocked."""
    UPDATE_DEALER_RIGHTS = "update_dealer_rights"
    """Dealer rights enabled/disabled."""
    DO_PAYMENT = "do_payment"
    """Payment or days registered."""
    UPDATE_ACCOUNT_FLAGS = "update_account_flags"
    """Account flags changed."""
    UPDATE_ACCOUNT_BLOCK_BALANCE = "update_account_block_balance"
    """Balance to block account changed."""
    UPDATE_ACCOUNT_DENY_BALANCE = "update_account_deny_balance"
    """Balance to limit activity changed."""
    UPDATE_ACCOUNT_MIN_DAYS = "update_account_min_days"
    """Minimum days counter changed."""
    UPDATE_ACCOUNT_PLAN = "update_account_plan"
    """Billing plan changed to '%s'."""
    UPDATE_ACCOUNT_HISTORY_PERIOD = "update_account_history_period"
    """History period changed to '%s'."""
    UPDATE_ACCOUNT_SUBPLANS = "update_account_subplans"
    """List of subplans changed."""
    UPDATE_SERVICE = "update_service"
    """Service '%s' updated."""
    DELETE_DRIVER_MSG = "delete_driver_msg"
    """Message dated %s from driver '%s' deleted."""
    DELETE_TRAILER_MSG = "delete_trailer_msg"
    """Message dated %s from trailer '%s' deleted."""
    CONVERT_MEASURE_UNITS = "convert_measure_units"
    """
    Measurement system changed to %s.
    Conversion to the %s.
    """
    DELETE_ZONES_GROUP = "delete_zones_group"
    """Group of geofences deleted."""
    CREATE_ZONES_GROUP = "create_zones_group"
    """Group of geofences '%s' created."""
    UPDATE_ZONES_GROUP = "update_zones_group"
    """Group of geofences '%s' updated."""
    TRAILER_RESET_IMAGE = "trailer_reset_image"
    """Trailer '%s' updated."""
    DRIVER_RESET_IMAGE = "driver_reset_image"
    """Driver '%s' updated."""
    ZONE_RESET_IMAGE = "zone_reset_image"
    """Geofence '%s' updated."""
    CREATE_ORDER = "create_order"
    """Order '%s' created."""
    UPDATE_ORDER = "update_order"
    """Order '%s' updated."""
    DELETE_ORDER = "delete_order"
    """Order '%s' deleted."""
    CREATE_ORDER_ROUTE = "create_order_route"
    """Order route '%s' created."""
    UPDATE_ORDER_ROUTE = "update_order_route"
    """Order route '%s' updated."""
    DELETE_ORDER_ROUTE = "delete_order_route"
    """Order route '%s' deleted."""
    CREATE_TAG = "create_tag"
    """Passenger '%s' created."""
    UPDATE_TAG = "update_tag"
    """Passenger '%s' updated."""
    TAG_RESET_IMAGE = "tag_reset_image"
    """Passenger '%s' updated."""
    DELETE_TAG = "delete_tag"
    """Passenger '%s' deleted."""
    DELETE_TAG_MSG = "delete_tag_msg"
    """Message dated %s from passenger '%s' deleted."""
    UPDATE_TAG_UNITS = "update_tag_units"
    """Automatic assignment list of passengers updated."""
    CRITERIA_UPDATED = "criteria_updated"
    """Criteria updated."""
    SET_ACTIVE = "set_active"
    """
    Unit was deactivated.
    Unit was activated.
    Unit was activated automatically.
    """


ACCESSMASK_RESOURCE_BASIC: int = (
    flags.AccessFlag.MANAGE_CUSTOM_FIELDS
    | flags.AccessFlag.RESOURCE_MANAGE_DRIVERS
    | flags.AccessFlag.RESOURCE_MANAGE_GEOFENCES
    | flags.AccessFlag.RESOURCE_MANAGE_NOTIFICATIONS
    | flags.AccessFlag.RESOURCE_VIEW_DRIVERS
    | flags.AccessFlag.RESOURCE_VIEW_GEOFENCES
    | flags.AccessFlag.RESOURCE_VIEW_NOTIFICATIONS
    | flags.AccessFlag.RESOURCE_VIEW_ORDERS
    | flags.AccessFlag.RESOURCE_VIEW_POIS
    | flags.AccessFlag.RESOURCE_VIEW_TRAILERS
    | flags.AccessFlag.VIEW_ADMIN_FIELDS
    | flags.AccessFlag.VIEW_CUSTOM_FIELDS
    | flags.AccessFlag.VIEW_ITEM_BASIC
)
"""Basic resource permissions"""

ACCESSMASK_UNIT_BASIC: int = (
    flags.AccessFlag.MANAGE_CUSTOM_FIELDS
    | flags.AccessFlag.MANAGE_ICON
    | flags.AccessFlag.QUERY_REPORTS
    | flags.AccessFlag.RENAME_ITEM
    | flags.AccessFlag.UNIT_EXECUTE_COMMANDS
    | flags.AccessFlag.UNIT_EXPORT_MESSAGES
    | flags.AccessFlag.UNIT_IMPORT_MESSAGES
    | flags.AccessFlag.UNIT_REGISTER_EVENTS
    | flags.AccessFlag.UNIT_VIEW_SERVICE_INTERVALS
    | flags.AccessFlag.VIEW_ATTACHED_FILES
    | flags.AccessFlag.VIEW_CUSTOM_FIELDS
    | flags.AccessFlag.VIEW_ITEM_BASIC
    | flags.AccessFlag.VIEW_ITEM_DETAILED
)
"""Basic unit permissions"""

ACCESSMASK_UNIT_MIGRATION: int = (
    flags.AccessFlag.DELETE_ITEM
    | flags.AccessFlag.MANAGE_ITEM_ACCESS
    | flags.AccessFlag.UNIT_DELETE_MESSAGES
    | flags.AccessFlag.UNIT_MANAGE_CONNECTIVITY
    | flags.AccessFlag.VIEW_ITEM_BASIC
)
"""Unit migration permissions"""
