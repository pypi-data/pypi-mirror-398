import datetime
import functools
import json
import math
import random
import re
import base64
import uuid
from dateutil import parser as dtparser
import pytz

from pyjexl.jexl import JEXL


class ExtendedGrammar:
    def __init__(self, jexl: JEXL):
        self.jexl = jexl

    """String functions"""

    @staticmethod
    def to_string(value, prettify=False):
        if isinstance(value, (dict, list)):
            value = (
                json.dumps(value)
                if prettify
                else json.dumps(value, separators=(",", ":"))
            )
        return str(value)

    @staticmethod
    def to_json(value):
        return json.loads(value)

    @staticmethod
    def length(value):
        return len(value)

    @staticmethod
    def substring(value: any, start: int, length: int = None):
        if not isinstance(value, str):
            value = json.dumps(value)
        start_num = start
        if start_num < 0:
            start_num = len(value) + start_num
            if start_num < 0:
                start_num = 0
        if length is None:
            return value[start_num:]
        fin = start_num + length
        if fin > len(value):
            fin = len(value)
        if fin < start_num:
            fin = start_num
        return value[start_num:fin]

    @staticmethod
    def substring_before(value: any, chars: any):
        if not isinstance(value, str):
            value = ExtendedGrammar.to_string(value)
        if not isinstance(chars, str):
            chars = ExtendedGrammar.to_string(chars)
        index = value.find(chars)
        if index == -1:
            return value
        return value[:index]

    @staticmethod
    def substring_after(value: any, chars: any):
        if not isinstance(value, str):
            value = ExtendedGrammar.to_string(value)
        if not isinstance(chars, str):
            chars = ExtendedGrammar.to_string(chars)
        index = value.find(chars)
        if index == -1:
            return ""
        ini = index + len(chars)
        return value[ini:]

    @staticmethod
    def uppercase(value):
        return ExtendedGrammar.to_string(value).upper()

    @staticmethod
    def lowercase(value):
        return ExtendedGrammar.to_string(value).lower()

    @staticmethod
    def camel_case(value):
        value = ExtendedGrammar.to_string(value)
        value = re.sub(
            r"(?<!^)(?=[A-Z])|[`~!@#%^&*()|+\\\-=?;:'.,\s_']+", "_", value
        ).lower()
        parts = value.split("_")
        camel_case_value = parts[0] + "".join(x.title() for x in parts[1:])
        return camel_case_value

    @staticmethod
    def pascal_case(value):
        value = ExtendedGrammar.to_string(value)
        value = re.sub(
            r"(?<!^)(?=[A-Z])|[`~!@#%^&*()|+\\\-=?;:'.,\s_']+", "_", value
        ).lower()
        parts = value.split("_")
        camel_case_value = "".join(x.title() for x in parts)
        return camel_case_value

    @staticmethod
    def trim(value, trim_char=" "):
        return ExtendedGrammar.to_string(value).strip(trim_char)

    @staticmethod
    def pad(value, width, char=" "):
        value = ExtendedGrammar.to_string(value)
        if not isinstance(char, str):
            char = str(char)
        if width > 0:
            return value.ljust(width, char)
        else:
            return value.rjust(-width, char)

    @staticmethod
    def contains(value, search):
        return search in value

    @staticmethod
    def starts_with(value, search):
        value = ExtendedGrammar.to_string(value)
        return value.startswith(search)

    @staticmethod
    def ends_with(value, search):
        value = ExtendedGrammar.to_string(value)
        return value.endswith(search)

    @staticmethod
    def split(value: str, sep=","):
        return value.split(sep)

    @staticmethod
    def join(value, sep=","):
        return sep.join(value)

    @staticmethod
    def replace(value: str, search: str, replace=""):
        return value.replace(search, replace)

    @staticmethod
    def base64_encode(input: str):
        return base64.b64encode(input.encode("utf-8")).decode("utf-8")

    @staticmethod
    def base64_decode(input: str):
        return base64.b64decode(input.encode("utf-8")).decode("utf-8")

    @staticmethod
    def form_url_encoded(value):
        if isinstance(value, str):
            import urllib.parse
            return urllib.parse.quote(value)
        elif isinstance(value, dict):
            import urllib.parse
            return urllib.parse.urlencode(value)
        return ""

    @staticmethod
    def switch_case(*args):
        if len(args) < 3:
            return None
        expression_result = args[0]
        # Iterate in pairs
        for i in range(1, len(args) - 1, 2):
            case_result = args[i]
            # Use JSON comparison for consistency with JS
            if json.dumps(expression_result, sort_keys=True) == json.dumps(
                case_result, sort_keys=True
            ):
                return args[i + 1]
        # Return default if exists (even number of args means default is provided)
        if len(args) % 2 == 0:
            return args[-1]
        return None

    """Number functions"""

    @staticmethod
    def to_number(value):
        return float(value)

    @staticmethod
    def to_int(value):
        if isinstance(value, str):
            value = value.strip('"')
        return int(float(value))

    @staticmethod
    def abs(value):
        return abs(value)

    @staticmethod
    def floor(value):
        return math.floor(value)

    @staticmethod
    def ceil(value):
        return math.ceil(value)

    @staticmethod
    def round(value, precision=0):
        return round(value, precision)

    @staticmethod
    def power(value, power=2):
        return math.pow(value, power)

    @staticmethod
    def sqrt(value):
        return math.sqrt(value)

    @staticmethod
    def random():
        return random.random()

    @staticmethod
    def format_number(value, format="0,0.000"):
        # Determine if we need to include commas
        if "," in format:
            format = format.replace(",", "")
            formatted_value = "{:,.{precision}f}".format(
                value, precision=len(format.split(".")[1])
            )
        else:
            formatted_value = "{:.{precision}f}".format(
                value, precision=len(format.split(".")[1])
            )

        return formatted_value

    @staticmethod
    def format_base(value, base=10):
        if base == 10:
            return str(value)
        elif base == 16:
            return hex(value)[2:]  # Remove the '0x' prefix
        elif base == 8:
            return oct(value)[2:]  # Remove the '0o' prefix
        elif base == 2:
            return bin(value)[2:]  # Remove the '0b' prefix
        else:
            # Custom implementation for other bases
            digits = "0123456789abcdefghijklmnopqrstuvwxyz"
            if base > len(digits):
                raise ValueError("Base too large")
            result = ""
            while value > 0:
                result = digits[value % base] + result
                value //= base
            return result or "0"

    @staticmethod
    def format_integer(value, format="0000000"):
        # Convert the value to an integer
        integer_value = int(float(value))

        # Format the integer value according to the specified format
        formatted_value = f"{integer_value:0{len(format)}d}"

        return formatted_value

    @staticmethod
    def sum(value, *rest):
        if not isinstance(value, list):
            value = [value]
        rest = [v for v in rest]
        if len(rest) > 0 and isinstance(rest[0], list):
            rest = [v for va in rest for v in va]
        values = value + rest
        return float(sum(values))

    @staticmethod
    def max(value, *rest):
        if not isinstance(value, list):
            value = [value]
        rest = [v for v in rest]
        if len(rest) > 0 and isinstance(rest[0], list):
            rest = [v for va in rest for v in va]
        values = value + rest
        return float(max(values))

    @staticmethod
    def min(value, *rest):
        if not isinstance(value, list):
            value = [value]
        rest = [v for v in rest]
        if len(rest) > 0 and isinstance(rest[0], list):
            rest = [v for va in rest for v in va]
        values = value + rest
        return float(min(values))

    @staticmethod
    def avg(value, *rest):
        if not isinstance(value, list):
            value = [value]
        rest = [v for v in rest]
        if len(rest) > 0 and isinstance(rest[0], list):
            rest = [v for va in rest for v in va]
        values = value + rest
        return float(sum(values) / len(values))

    @staticmethod
    def to_boolean(value):
        if isinstance(value, bool):
            return value
        if isinstance(value, int):
            return value != 0
        if isinstance(value, str):
            value = value.strip().lower()
            if value == "true" or value == "1":
                return True
            if value == "false" or value == "0":
                return False
            return None
        return bool(value)

    @staticmethod
    def not_(value):
        return not ExtendedGrammar.to_boolean(value)

    """ Array functions """

    @staticmethod
    def array_range(value, start, end=None):
        if not isinstance(value, list):
            return []
        return value[start:end]

    @staticmethod
    def array_append(value, *rest):
        if not isinstance(value, list):
            value = [value]
        rest = [v for v in rest]
        if len(rest) > 0 and isinstance(rest[0], list):
            rest = [v for va in rest for v in va]
        return value + rest

    @staticmethod
    def array_reverse(value, *rest):
        if not isinstance(value, list):
            value = [value]
        rest = [v for v in rest]
        if len(rest) > 0 and isinstance(rest[0], list):
            rest = [v for va in rest for v in va]
        return (value + rest)[::-1]

    @staticmethod
    def array_shuffle(value):
        if not isinstance(value, list):
            value = [value]
        random.shuffle(value)
        return value

    def array_sort(self, value, expression=None, descending=False):
        if not isinstance(value, list):
            value = [value]
        if not expression:
            return sorted(value, reverse=descending)
        expr = self.jexl.parse(expression)
        return sorted(
            value,
            key=lambda x: self.jexl.evaluate(expr, x),
            reverse=descending,
        )

    @staticmethod
    def array_distinct(value):
        if not isinstance(value, list):
            value = [value]
        return list(set(value))

    @staticmethod
    def array_to_object(input, val=None):
        if isinstance(input, str):
            return {input: val}
        if not isinstance(input, list):
            return {}
        return functools.reduce(
            lambda acc, kv: (
                acc.update({kv[0]: kv[1]}) or acc
                if isinstance(kv, list) and len(kv) == 2
                else acc.update({str(kv): val}) or acc
            ),
            input,
            {},
        )

    @staticmethod
    def array_mapfield(input, field):
        if not isinstance(input, list):
            return []
        return [item[field] for item in input]

    def array_map(self, input, expression):
        if not isinstance(input, list):
            return None
        expr = self.jexl.parse(expression)
        return [
            self.jexl.evaluate(expr, {"value": value, "index": index, "array": input})
            for index, value in enumerate(input)
        ]

    def array_any(self, input, expression):
        if not isinstance(input, list):
            return False
        expr = self.jexl.parse(expression)
        return any(
            [
                self.jexl.evaluate(expr, {"value": value, "index": index, "array": input})
                for index, value in enumerate(input)
            ]
        )

    def array_every(self, input, expression):
        if not isinstance(input, list):
            return False
        expr = self.jexl.parse(expression)
        return all(
            [
                self.jexl.evaluate(expr, {"value": value, "index": index, "array": input})
                for index, value in enumerate(input)
            ]
        )

    def array_filter(self, input, expression):
        if not isinstance(input, list):
            return []
        expr = self.jexl.parse(expression)
        return [
            value
            for index, value in enumerate(input)
            if self.jexl.evaluate(expr, {"value": value, "index": index, "array": input})
        ]

    def array_find(self, input, expression):
        if not isinstance(input, list):
            return None
        expr = self.jexl.parse(expression)
        return next(
            (
                value
                for index, value in enumerate(input)
                if self.jexl.evaluate(expr, {"value": value, "index": index, "array": input})
            ),
            None,
        )

    def array_find_index(self, input, expression):
        if not isinstance(input, list):
            return None
        expr = self.jexl.parse(expression)
        for index, value in enumerate(input):
            if self.jexl.evaluate(expr, {"value": value, "index": index, "array": input}):
                return index
        return -1

    def array_reduce(self, input, expression, initialValue=None):
        if not isinstance(input, list):
            return None
        expr = self.jexl.parse(expression)
        return functools.reduce(
            lambda acc, value: self.jexl.evaluate(
                expr, {"accumulator": acc, "value": value}
            ),
            input,
            initialValue,
        )

    """ Object functions """

    @staticmethod
    def object_keys(input):
        if isinstance(input, dict):
            return list(input.keys())
        return None

    @staticmethod
    def object_values(input):
        if isinstance(input, dict):
            return list(input.values())
        return None

    @staticmethod
    def object_entries(input):
        if isinstance(input, dict):
            return list(input.items())
        return None

    @staticmethod
    def object_merge(*args):
        result = {}
        for arg in args:
            if isinstance(arg, list):
                for obj in arg:
                    if isinstance(obj, dict):
                        result.update(obj)
            elif isinstance(arg, dict):
                result.update(arg)
        return result

    """ Date functions """

    @staticmethod
    def now():
        return datetime.datetime.isoformat(datetime.datetime.now())

    @staticmethod
    def millis():
        return datetime.datetime.now().timestamp() * 1000

    @staticmethod
    def to_datetime(input=None, format=None):
        if input is None:
            return datetime.datetime.now(pytz.UTC).isoformat()
        if isinstance(input, (int, float)):
            return datetime.datetime.fromtimestamp(input / 1000, tz=pytz.UTC).isoformat()
        if isinstance(input, str):
            if format:
                # Basic mapping for date-fns format tokens to strftime
                mapping = {
                    "yyyy": "%Y",
                    "MM": "%m",
                    "dd": "%d",
                    "HH": "%H",
                    "mm": "%M",
                    "ss": "%S",
                    "SSS": "%f",  # Not exact but close
                }
                py_format = format
                for js_token, py_token in mapping.items():
                    py_format = py_format.replace(js_token, py_token)
                dt = datetime.datetime.strptime(input, py_format)
                # strptime creates naive dt, assume UTC or handle if needed
                dt = dt.replace(tzinfo=pytz.UTC)
                return dt.isoformat()
            try:
                dt = dtparser.isoparse(input)
            except Exception:
                try:
                    dt = dtparser.parse(input)
                except Exception:
                    return None
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=pytz.UTC)
            return dt.isoformat()
        return None

    @staticmethod
    def to_millis(value):
        if isinstance(value, (int, float)):
            return float(value)
        try:
            dt = dtparser.isoparse(value)
        except Exception:
            try:
                dt = dtparser.parse(value)
            except Exception:
                return None
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=pytz.UTC)
        return dt.timestamp() * 1000

    @staticmethod
    def datetime_format(input, format_str):
        try:
            if isinstance(input, (int, float)):
                dt = datetime.datetime.fromtimestamp(input / 1000, tz=pytz.UTC)
            else:
                dt = dtparser.parse(input)
                if dt.tzinfo is None:
                    dt = dt.replace(tzinfo=pytz.UTC)
                else:
                    dt = dt.astimezone(pytz.UTC)

            # Very basic mapping for common tokens
            mapping = {
                "yyyy": "%Y",
                "MM": "%m",
                "dd": "%d",
                "HH": "%H",
                "mm": "%M",
                "ss": "%S",
            }
            py_format = format_str
            for js_token, py_token in mapping.items():
                py_format = py_format.replace(js_token, py_token)
            return dt.strftime(py_format)
        except Exception:
            return None

    @staticmethod
    def datetime_add(input, unit, value):
        input_datetime = datetime.datetime.fromisoformat(input)
        if not str.endswith(unit, "s"):
            unit = unit + "s"
        if unit == "years":
            return input_datetime + datetime.timedelta(days=365 * value)
        if unit == "months":
            return input_datetime + datetime.timedelta(days=30 * value)
        if unit == "days":
            return input_datetime + datetime.timedelta(days=value)
        if unit == "hours":
            return input_datetime + datetime.timedelta(hours=value)
        if unit == "minutes":
            return input_datetime + datetime.timedelta(minutes=value)
        if unit == "seconds":
            return input_datetime + datetime.timedelta(seconds=value)
        if unit == "milliseconds":
            return input_datetime + datetime.timedelta(milliseconds=value)
        return None

    @staticmethod
    def convert_time_zone(input, target_timezone):
        """
        Converts an ISO datetime string to a target timezone, handling daylight savings, and returns an ISO string with the correct offset.
        """
        # Minimal Windows to IANA mapping (extend as needed)
        WINDOWS_TZ_MAP = {
            "Pacific Standard Time": "America/Los_Angeles",
            "UTC": "UTC",
            # Add more mappings as needed
        }

        # Parse input datetime
        if not isinstance(input, str):
            input = ExtendedGrammar.to_string(input)
        try:
            dt = dtparser.isoparse(input)
        except Exception:
            return None

        # Ensure datetime is aware (UTC if Z or no offset)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=pytz.UTC)

        tz_str = ExtendedGrammar.to_string(target_timezone)

        # Check for fixed offset (e.g., +02:00, -08:00)
        offset_match = re.match(r"^([+-])(\d{2}):(\d{2})$", tz_str)
        if offset_match:
            sign = 1 if offset_match.group(1) == "+" else -1
            hours = int(offset_match.group(2))
            minutes = int(offset_match.group(3))
            offset = datetime.timedelta(hours=sign * hours, minutes=sign * minutes)
            tzinfo = datetime.timezone(offset)
            dt_converted = dt.astimezone(tzinfo)
        else:
            # Try Windows mapping
            iana_tz = WINDOWS_TZ_MAP.get(tz_str, tz_str)
            try:
                tzinfo = pytz.timezone(iana_tz)
            except Exception:
                # Try to find by case-insensitive match
                try:
                    tzinfo = next(
                        z
                        for z in map(pytz.timezone, pytz.all_timezones)
                        if z.zone.lower() == iana_tz.lower()
                    )
                except Exception:
                    return None
            dt_converted = dt.astimezone(tzinfo)

        # Format: ISO string with 7 digits microseconds and offset
        iso_str = dt_converted.strftime("%Y-%m-%dT%H:%M:%S.%f%z")
        # Insert colon in offset for ISO compliance
        if iso_str.endswith("+0000"):
            iso_str = iso_str[:-5] + "+00:00"
        elif iso_str[-5] in ["+", "-"]:
            iso_str = iso_str[:-5] + iso_str[-5:-2] + ":" + iso_str[-2:]
        # Truncate microseconds to 7 digits
        if "." in iso_str:
            ms = iso_str.split(".")[1][:7]
            iso_str = iso_str.split(".")[0] + "." + ms + iso_str[-6:]
        return iso_str

    @staticmethod
    def local_time_to_iso_with_offset(local_time, time_zone):
        """
        Converts a local time string in a specified timezone to an ISO datetime string with the correct offset.

        Example:
            local_time_to_iso_with_offset('2025-06-26 14:00:00', 'Europe/Amsterdam') -> '2025-06-26T14:00:00.0000000+02:00'
            local_time_to_iso_with_offset('2025-06-26 05:00:00', 'Pacific Standard Time') -> '2025-06-26T05:00:00.0000000-08:00'

        :param local_time: Local time string
        :param time_zone: Timezone (IANA or Windows ID or fixed offset)
        :return: ISO datetime string with correct offset, or None if conversion fails
        """
        # Minimal Windows to IANA mapping (extend as needed)
        WINDOWS_TZ_MAP = {
            "Pacific Standard Time": "America/Los_Angeles",
            "UTC": "UTC",
            # Add more mappings as needed
        }

        # Parse the local time string (assume naive)
        try:
            dt = dtparser.parse(local_time)
        except Exception:
            return None

        tz_str = str(time_zone)

        # Check for fixed offset (e.g., +02:00, -08:00)
        offset_match = re.match(r"^([+-])(\d{2}):(\d{2})$", tz_str)
        if offset_match:
            sign = 1 if offset_match.group(1) == "+" else -1
            hours = int(offset_match.group(2))
            minutes = int(offset_match.group(3))
            offset = datetime.timedelta(hours=sign * hours, minutes=sign * minutes)
            tzinfo = datetime.timezone(offset)
        else:
            # Try Windows mapping
            iana_tz = WINDOWS_TZ_MAP.get(tz_str, tz_str)
            try:
                tzinfo = pytz.timezone(iana_tz)
            except Exception:
                # Try to find by case-insensitive match
                try:
                    tzinfo = next(
                        z
                        for z in map(pytz.timezone, pytz.all_timezones)
                        if z.zone.lower() == iana_tz.lower()
                    )
                except Exception:
                    return None

        # Localize naive datetime to the timezone
        try:
            if hasattr(tzinfo, "localize"):
                dt_local = tzinfo.localize(dt)
            else:
                dt_local = dt.replace(tzinfo=tzinfo)
        except Exception:
            return None

        # Format: ISO string with 7 digits microseconds and offset
        iso_str = dt_local.strftime("%Y-%m-%dT%H:%M:%S.%f%z")
        # Insert colon in offset for ISO compliance
        if iso_str.endswith("+0000"):
            iso_str = iso_str[:-5] + "+00:00"
        elif iso_str[-5] in ["+", "-"]:
            iso_str = iso_str[:-5] + iso_str[-5:-2] + ":" + iso_str[-2:]
        # Truncate microseconds to 7 digits
        if "." in iso_str:
            ms = iso_str.split(".")[1][:7]
            iso_str = iso_str.split(".")[0] + "." + ms + iso_str[-6:]
        return iso_str

    """ Misc """

    def _eval(self, input, expression):
        if not isinstance(expression, str) and isinstance(input, str):
            return self.jexl.evaluate(expression)
        if isinstance(input, dict) and isinstance(expression, str):
            return self.jexl.evaluate(expression, input)
        return None

    @staticmethod
    def get_type(input):
        if input is None:
            return "null"
        if isinstance(input, bool):
            return "boolean"
        if isinstance(input, (int, float)):
            return "number"
        if isinstance(input, str):
            return "string"
        if isinstance(input, list):
            return "array"
        if isinstance(input, dict):
            return "object"
        if callable(input):
            return "function"
        return "undefined"

    def uuid(self):
        return str(uuid.uuid4())
