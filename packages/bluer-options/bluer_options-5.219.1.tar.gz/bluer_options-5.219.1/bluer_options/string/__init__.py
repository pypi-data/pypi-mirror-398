import os
import time

from bluer_options.env import BLUER_OPTIONS_TIMEZONE

# https://en.wikipedia.org/wiki/List_of_tz_database_time_zones
os.environ["TZ"] = BLUER_OPTIONS_TIMEZONE
time.tzset()

from bluer_options.string.constants import unit_of
from bluer_options.string.functions import (
    after,
    before,
    between,
    pretty_bytes,
    pretty_date,
    pretty_duration,
    pretty_minimal_duration,
    pretty_frequency,
    pretty_param,
    pretty_range_of_matrix,
    pretty_shape,
    pretty_shape_of_matrix,
    random,
    timestamp,
    utc_timestamp,
)
