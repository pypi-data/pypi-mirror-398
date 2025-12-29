import re
from datetime import datetime, timedelta


def parse_time_regex(fmt: str, base_time: datetime = None) -> str:
    """
    Replaces {%...} blocks in the input string with time values.

    Rules:
    1. Only content inside {...} is parsed.
    2. Within {...}, only tokens that:
       - start with '%'
       - end with one of [Y, m, d, H, i]
       are treated as time expressions.
    3. Time tokens support offset and rounding:
       - %+nX, %-nX  : add/subtract n units (X = Y/m/d/H/i)
       - %/nX        : floor to nearest n step
       - %+n/stepX   : shift by n and floor by step
    4. All other characters (including before % or invalid tokens) are treated as plain text.
    5. Returns the original string with {%...} blocks replaced by evaluated values.
    """
    if base_time is None:
        base_time = datetime.now()

    def replacer(match):
        expr = match.group(1)
        result = ''
        cursor = 0

        # Match only valid time tokens: starts with %, ends in Y/m/d/H/i
        token_pattern = re.compile(r'%([+-]?\d+)?(?:/(\d+))?([YmdHi])')

        for m in token_pattern.finditer(expr):
            start, end = m.span()

            # Add text before this token as literal
            if cursor < start:
                result += expr[cursor:start]

            offset = int(m.group(1)) if m.group(1) else 0
            step = int(m.group(2)) if m.group(2) else 1
            symbol = m.group(3)

            dt = base_time
            if symbol == 'Y':
                value = dt.year + offset
            elif symbol == 'm':
                year = dt.year
                month = dt.month + offset
                while month <= 0:
                    month += 12
                    year -= 1
                while month > 12:
                    month -= 12
                    year += 1
                value = month
            elif symbol == 'd':
                dt += timedelta(days=offset)
                value = dt.day
            elif symbol == 'H':
                dt += timedelta(hours=offset)
                value = dt.hour
            elif symbol == 'i':
                dt += timedelta(minutes=offset)
                value = dt.minute
            else:
                continue

            norm = (value // step) * step
            width = 4 if symbol == 'Y' else 2
            result += f'{norm:0{width}d}'

            cursor = end

        # Add remaining literal after last token
        if cursor < len(expr):
            result += expr[cursor:]

        return result

    return re.sub(r'\{(.*?)\}', replacer, fmt)


def parse_period(s: str) -> int:
    """
    Converts a duration string like '3d2h3m4s' into total seconds.

    Rules:
    1. Supports multiple time units: d (days), h (hours), m (minutes), s (seconds)
    2. Units can appear in any order
    3. If no unit, the whole string is treated as seconds
    4. Invalid input returns -1

    Examples:
        "5m" → 300
        "2h" → 7200
        "10" → 10
        "3d" → 259200
        "3d2h3m4s" → 277384
        "abc" → -1
    """
    if not s:
        return -1

    if s.isdigit():
        return int(s)

    pattern = re.compile(r'(\d+)([dhms])')
    matches = pattern.findall(s)

    if not matches:
        return -1

    total_seconds = 0
    unit_multipliers = {
        'd': 86400,
        'h': 3600,
        'm': 60,
        's': 1
    }

    for value, unit in matches:
        if unit in unit_multipliers:
            total_seconds += int(value) * unit_multipliers[unit]
        else:
            return -1

    return total_seconds


def parse_crontab_field(field: str, min_val: int, max_val: int) -> list[int]:
    """Parse a single crontab field and return a list of matching values."""
    values = set()
    parts = field.split(',')

    for part in parts:
        if part == '*':
            # Match all values in the allowed range
            values.update(range(min_val, max_val + 1))

        elif '/' in part:
            base, step = part.split('/')
            step = int(step)

            if base == '*':
                # Step across the entire range (e.g. */15)
                values.update(range(min_val, max_val + 1, step))
            elif '-' in base:
                # Step through a range (e.g. 1-10/2)
                start, end = map(int, base.split('-'))
                values.update(range(start, end + 1, step))
            else:
                # Handle uncommon format like 3/2 (from 3 every 2 steps)
                values.add(int(base))

        elif '-' in part:
            # Add all values in a range (e.g. 1-5)
            start, end = map(int, part.split('-'))
            values.update(range(start, end + 1))

        else:
            # Add a single integer value (e.g. 5)
            values.add(int(part))

    return sorted(values)


def parse_crontab(expr: str) -> dict[str, list[int]]:
    """Parse a full crontab expression and return each field as value list."""
    fields = expr.strip().split()

    if len(fields) != 5:
        raise ValueError("Crontab expression must contain 5 fields")

    return {
        "minute": parse_crontab_field(fields[0], 0, 59),
        "hour": parse_crontab_field(fields[1], 0, 23),
        "day": parse_crontab_field(fields[2], 1, 31),
        "month": parse_crontab_field(fields[3], 1, 12),
        "weekday": parse_crontab_field(fields[4], 0, 7),  # 0 or 7 = Sunday
    }


def is_now_matching_crontab(expr: str, dt: datetime = None) -> bool:
    """
    Check whether a given datetime matches the crontab rule.
    If no datetime is provided, uses the current time.
    """
    if dt is None:
        dt = datetime.now()

    cron = parse_crontab(expr)

    # Convert Python weekday (0=Mon ... 6=Sun) to crontab style
    weekday = dt.weekday()  # 0 = Monday
    if 7 in cron["weekday"]:
        cron_weekday = 0 if weekday == 6 else weekday + 1  # Support for both 0 and 7 as Sunday
    else:
        cron_weekday = weekday

    return (
        dt.minute in cron["minute"] and
        dt.hour in cron["hour"] and
        dt.day in cron["day"] and
        dt.month in cron["month"] and
        cron_weekday in cron["weekday"]
    )


# Example usage
if __name__ == "__main__":
    """
    #f = "PM10_{%Y%m%dT%-1/6H:%-10/5i}.txt"
    f = "{%Y%m%d%H%-5i}"
    print(parse_time_regex(f))
    print (parse_period("2m"))
    """

    crontab_expr = "*/15 0-6 * * 1-5"  # Every 15 min, between 0-6h, Mon-Fri
    now = datetime.now()

    if is_now_matching_crontab(crontab_expr, now):
        print(f"Now ({now}) matches the crontab rule.")
    else:
        print(f"Now ({now}) does not match the crontab rule.")


