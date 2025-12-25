import enum


class AccessFlag(enum.IntFlag):
    """
    Access flags for Wialon API calls.

    `Access Flags Reference <https://sdk.wialon.com/wiki/en/sidebar/remoteapi/apiref/core/check_items_billing>`_

    """

    VIEW_ITEM_BASIC = 0x0001
    """View this item's basic properties"""
    VIEW_ITEM_DETAILED = 0x0002
    """View this item's detailed properties"""
    MANAGE_ITEM_ACCESS = 0x0004
    """Manage access to this item"""
    DELETE_ITEM = 0x0008
    """Delete this item"""
    RENAME_ITEM = 0x0010
    """Rename this item"""
    VIEW_CUSTOM_FIELDS = 0x0020
    """View this item's custom fields"""
    MANAGE_CUSTOM_FIELDS = 0x0040
    """Manage this item's custom fields"""
    MANAGE_UNMENTIONED_FIELDS = 0x0080
    """Manage this item's unmentioned properties"""
    MANAGE_ICON = 0x0100
    """Manage this item's icon"""
    QUERY_REPORTS = 0x0200
    """Query this item's reports or messages"""
    MANAGE_ACL = 0x0400
    """Manage this item's ACL propagated objects"""
    MANAGE_ITEM_LOG = 0x0800
    """Manage this item's log"""
    VIEW_ADMIN_FIELDS = 0x1000
    """View this item's administrative fields"""
    MANAGE_ADMIN_FIELDS = 0x2000
    """Manage this item's administrative fields"""
    VIEW_ATTACHED_FILES = 0x4000
    """View this item's attached files"""
    MANAGE_ATTACHED_FILES = 0x8000
    """Manage this item's attached files"""
    UNIT_MANAGE_CONNECTIVITY = 0x0000100000
    """Manage this unit/group's connectivity settings"""
    UNIT_MANAGE_SENSORS = 0x0000200000
    """Manage this unit/group's sensors"""
    UNIT_MANAGE_COUNTERS = 0x0000400000
    """Manage this unit/group's counters"""
    UNIT_DELETE_MESSAGES = 0x0000800000
    """Delete this unit/group's messages"""
    UNIT_EXECUTE_COMMANDS = 0x0001000000
    """Execute this unit/group's commands"""
    UNIT_REGISTER_EVENTS = 0x0002000000
    """Register this unit/group's events"""
    UNIT_VIEW_CONNECTIVITY = 0x0004000000
    """View this unit/group's connectivity settings"""
    UNIT_VIEW_SERVICE_INTERVALS = 0x0010000000
    """View this unit/group's service intervals"""
    UNIT_MANAGE_SERVICE_INTERVALS = 0x0020000000
    """Manage this unit/group's service intervals"""
    UNIT_IMPORT_MESSAGES = 0x0040000000
    """Import this unit/group's messages"""
    UNIT_EXPORT_MESSAGES = 0x0080000000
    """Export this unit/group's messages"""
    UNIT_VIEW_COMMANDS = 0x0400000000
    """View this unit/group's commands"""
    UNIT_MANAGE_COMMANDS = 0x0800000000
    """Manage this unit/group's commands"""
    UNIT_MANAGE_TRIP_DETECTOR = 0x4000000000
    """Manage this unit/group's trip detector and fuel consumption"""
    UNIT_MANAGE_ASSIGNMENTS = 0x8000000000
    """Manage this unit/group's job, notification, route, and retranslator assignments"""
    USER_MANAGE_ACCESS_RIGHTS = 0x100000
    """Manage this user's access rights"""
    USER_ACT_AS_OTHER = 0x200000
    """Can assume the identity of this user (login as)"""
    USER_MANAGE_FLAGS = 0x400000
    """Manage this user's access flags"""
    USER_VIEW_PUSH_MESSAGES = 0x800000
    """View this user's push messages"""
    USER_MANAGE_PUSH_MESSAGES = 0x1000000
    """Manage this user's push messages"""
    RETRANSLATOR_MANAGE_PROPERTIES = 0x100000
    """Manage this retranslator's properties (including start/stop)"""
    RETRANSLATOR_MANAGE_UNITS = 0x2000000
    """Manage this retranslator's available units"""
    RESOURCE_VIEW_NOTIFICATIONS = 0x0000000100000
    """View this resource's notifications"""
    RESOURCE_MANAGE_NOTIFICATIONS = 0x0000000200000
    """Manage this resource's notifications"""
    RESOURCE_VIEW_POIS = 0x0000000400000
    """View this resource's points of interest"""
    RESOURCE_MANAGE_POIS = 0x0000000800000
    """Manage this resource's points of interest"""
    RESOURCE_VIEW_GEOFENCES = 0x0000001000000
    """View this resource's geofences"""
    RESOURCE_MANAGE_GEOFENCES = 0x0000002000000
    """Manage this resource's geofences"""
    RESOURCE_VIEW_JOBS = 0x0000004000000
    """View this resource's jobs"""
    RESOURCE_MANAGE_JOBS = 0x0000008000000
    """Manage this resource's jobs"""
    RESOURCE_VIEW_REPORT_TEMPLATES = 0x0000010000000
    """View this resource's report templates"""
    RESOURCE_MANAGE_REPORT_TEMPLATES = 0x0000020000000
    """Manage this resource's report templates"""
    RESOURCE_VIEW_DRIVERS = 0x0000040000000
    """View this resource's drivers"""
    RESOURCE_MANAGE_DRIVERS = 0x0000080000000
    """Manage this resource's drivers"""
    RESOURCE_MANAGE_ACCOUNT = 0x0000100000000
    """Manage this resource's account"""
    RESOURCE_VIEW_ORDERS = 0x0000200000000
    """View this resource's orders"""
    RESOURCE_MANAGE_ORDERS = 0x0000400000000
    """Manage this resource's orders"""
    RESOURCE_VIEW_TRAILERS = 0x0100000000000
    """View this resource's trailers"""
    RESOURCE_MANAGE_TRAILERS = 0x0200000000000
    """Manage this resource's trailers"""
    ROUTE_MANAGE_ROUTE = 0x0000000100000
    """Manage this route's properties"""
    FULL_ACCESS = 0xFFFFFFFFFFFFFFF
    """Sets all possible access flags to an item"""


class DataFlag(enum.IntFlag):
    """
    Data flags for Wialon API calls.

    `Data Flags Reference <https://sdk.wialon.com/wiki/en/sidebar/remoteapi/apiref/format/format>`_

    """

    RESOURCE_BASE = 0x00000001
    """This resource's basic properties"""
    RESOURCE_CUSTOM_PROPERTIES = 0x00000002
    """This resource's custom properties"""
    RESOURCE_BILLING_PROPERTIES = 0x00000004
    """This resource's billing properties"""
    RESOURCE_CUSTOM_FIELDS = 0x00000008
    """This resource's custom fields"""
    RESOURCE_MESSAGES = 0x00000020
    """This resource's messages"""
    RESOURCE_GUID = 0x00000040
    """This resource's GUID"""
    RESOURCE_ADMIN_FIELDS = 0x00000080
    """This resources administrative fields"""
    RESOURCE_DRIVERS = 0x00000100
    """This resource's drivers"""
    RESOURCE_JOBS = 0x00000200
    """This resource's jobs"""
    RESOURCE_NOTIFICATIONS = 0x00000400
    """This resource's notifications"""
    RESOURCE_POIS = 0x00000800
    """This resouce's points of interest"""
    RESOURCE_GEOFENCES = 0x00001000
    """This resource's geofences"""
    RESOURCE_REPORT_TEMPLATES = 0x00002000
    """This resource's report templates"""
    RESOURCE_DRIVER_ATTACHABLE_UNITS = 0x00004000
    """This resource's units allowed for driver attachment"""
    RESOURCE_DRIVER_GROUPS = 0x00008000
    """This resource's driver groups"""
    RESOURCE_TRAILERS = 0x00010000
    """This resource's trailers"""
    RESOURCE_TRAILER_GROUPS = 0x00020000
    """This resource's trailer groups"""
    RESOURCE_TRAILER_ATTACHABLE_UNITS = 0x00040000
    """This resource's units allowed for trailer attachment"""
    RESOURCE_ORDERS = 0x00080000
    """This resource's orders"""
    RESOURCE_GEOFENCE_GROUPS = 0x00100000
    """This resource's geofence groups"""
    RESOURCE_TAGS = 0x00200000
    """This resource's tags (passengers)"""
    RESOURCE_TAG_ATTACHABLE_UNITS = 0x00400000
    """This resource's units allowed for tag attachment"""
    RESOURCE_TAG_GROUPS = 0x00800000
    """This resource's tag groups (passengers)"""
    RESOURCE_ALL = 4611686018427387903
    """All possible resource data flags"""
    RETRANSLATOR_BASE = 0x00000001
    """This retranslator's basic properties"""
    RETRANSLATOR_CUSTOM_PROPERTIES = 0x00000002
    """This retranslator's custom properties"""
    RETRANSLATOR_BILLING_PROPERTIES = 0x00000004
    """This retranslator's billing properties"""
    RETRANSLATOR_GUID = 0x00000040
    """This retranslator's GUID"""
    RETRANSLATOR_ADMIN_FIELDS = 0x00000080
    """This retranslator's admin fields"""
    RETRANSLATOR_CONFIGURATION = 0x00000100
    """This retranslator's state and configuration"""
    RETRANSLATOR_UNITS = 0x00000200
    """This retranslator's bound units"""
    RETRANSLATOR_ALL = 4611686018427387903
    """All possible retranslator data flags"""
    ROUTE_BASE = 0x00000001
    """This route's basic properties"""
    ROUTE_CUSTOM_PROPERTIES = 0x00000002
    """This route's custom properties"""
    ROUTE_BILLING_PROPERTIES = 0x00000004
    """This route's billing properties"""
    ROUTE_GUID = 0x00000040
    """This route's GUID"""
    ROUTE_ADMIN_FIELDS = 0x00000080
    """This route's administrative fields"""
    ROUTE_CONFIGURATION = 0x00000100
    """This route's configuration"""
    ROUTE_CHECKPOINTS = 0x00000200
    """This route's checkpoints"""
    ROUTE_SCHEDULES = 0x00000400
    """This route's schedules"""
    ROUTE_ROUNDS = 0x00000800
    """This route's rounds"""
    ROUTE_ALL = 4611686018427387903
    """All possible route data flags"""
    UNIT_BASE = 0x00000001
    """This unit's basic properties"""
    UNIT_CUSTOM_PROPERTIES = 0x00000002
    """This unit's custom properties"""
    UNIT_BILLING_PROPERTIES = 0x00000004
    """This unit's billing properties"""
    UNIT_CUSTOM_FIELDS = 0x00000008
    """This unit's custom fields"""
    UNIT_IMAGE = 0x00000010
    """This unit's image/icon"""
    UNIT_MESSAGES = 0x00000020
    """This unit's messages"""
    UNIT_GUID = 0x00000040
    """This unit's GUID"""
    UNIT_ADMIN_FIELDS = 0x00000080
    """This unit's administrative fields"""
    UNIT_ADVANCED_PROPERTIES = 0x00000100
    """This unit's advanced properties"""
    UNIT_CURRENT_MOMENT_COMMANDS = 0x00000200
    """This unit's available for current moment commands"""
    UNIT_LAST_MESSAGE = 0x00000400
    """This unit's last message and position"""
    UNIT_SENSORS = 0x00001000
    """This unit's sensors"""
    UNIT_COUNTERS = 0x00002000
    """This unit's counters"""
    UNIT_MAINTENANCE = 0x00008000
    """This unit's maintenance"""
    UNIT_REPORT_CONFIGURATION = 0x00020000
    """This unit's report configuration, trip detector, and fuel consumption"""
    UNIT_AVAILABLE_COMMANDS = 0x00080000
    """This unit's available commands"""
    UNIT_MESSAGE_PARAMETERS = 0x00100000
    """This unit's message parameters"""
    UNIT_CONNECTION_STATUS = 0x00200000
    """This unit's connection status"""
    UNIT_POSITION = 0x00400000
    """This unit's position"""
    UNIT_PROFILE_FIELDS = 0x00800000
    """This unit's profile files"""
    UNIT_ALL = 4611686018427387903
    """All possible unit data flags"""
    GROUP_BASE = 0x00000001
    """This group's basic properties"""
    GROUP_CUSTOM_PROPERTIES = 0x00000002
    """This group's custom properties"""
    GROUP_BILLING_PROPERTIES = 0x00000004
    """This group's billing properties"""
    GROUP_CUSTOM_FIELDS = 0x00000008
    """This group's custom fields"""
    GROUP_IMAGE = 0x00000010
    """This group's image/icon"""
    GROUP_GUID = 0x00000040
    """This group's GUID"""
    GROUP_ADMIN_FIELDS = 0x00000080
    """This group's administrative fields"""
    GROUP_ALL = 4611686018427387903
    """All possible group data flags"""
    USER_BASE = 0x00000001
    """This user's basic properties"""
    USER_CUSTOM_PROPERTIES = 0x00000002
    """This user's custom properties"""
    USER_BILLING_PROPERTIES = 0x00000004
    """This user's billing properties"""
    USER_CUSTOM_FIELDS = 0x00000008
    """This user's custom fields"""
    USER_MESSAGES = 0x00000020
    """This user's messages"""
    USER_GUID = 0x00000040
    """This user's GUID"""
    USER_ADMIN_FIELDS = 0x00000080
    """This user's administrative fields"""
    USER_OTHER_PROPERTIES = 0x00000100
    """This user's other properties"""
    USER_NOTIFICATIONS = 0x00000200
    """This user's notifications"""
    USER_ALL = 4611686018427387903
    """All possible user data flags"""


class SettingsFlag(enum.IntFlag):
    """
    User settings flags for Wialon API calls.

    `User Settings Flags Reference <https://sdk.wialon.com/wiki/en/sidebar/remoteapi/apiref/user/update_user_flags>`_

    """

    USER_DISABLED = 0x01
    """This user is disabled"""
    USER_CANNOT_CHANGE_PASSWORD = 0x02
    """This user cannot change their password"""
    USER_CAN_CREATE_ITEMS = 0x04
    """This user can create objects"""
    USER_CANNOT_CHANGE_SETTINGS = 0x10
    """This user cannot change settings"""
    USER_CAN_SEND_SMS = 0x20
    """This user can send SMS messages"""


class TokenFlag(enum.IntFlag):
    """
    Token flags for Wialon API calls.

    `Token Flags Reference <https://sdk.wialon.com/wiki/en/sidebar/remoteapi/apiref/token/login>`_

    """

    ONLINE_TRACKING = 0x100
    """Online tracking"""
    VIEW_ACCESS = 0x200
    """View access to most data"""
    MANAGE_NONSENSITIVE = 0x400
    """Modification of non-sensitive data"""
    MANAGE_SENSITIVE = 0x800
    """Modification of sensitive data"""
    MANAGE_CRITICAL = 0x1000
    """Modification of critical data, including message deletion"""
    COMMUNICATION = 0x2000
    """Modification of communication data"""
    MANAGE_ALL = -1
    """Unlimited operation as authorized user"""
