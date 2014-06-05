import re
import simplejson
import hashlib
import random

def success(message=None):
    if message:
        return {'messages': [message], 'success': True}
    else:
        return {'messages': [], 'success': True}

def failure(message=None):
    if message:
        return {'messages': [message], 'success': False}
    else:
        return {'messages': [], 'success': False}

def chunks(my_list, num_chunks):
    for index in xrange(0, len(my_list), num_chunks):
        yield my_list[index:index+num_chunks]+['']*(num_chunks-(len(my_list)-index))

def generate_hash(length=64):
    return hashlib.sha224(str(random.getrandbits(256))).hexdigest()[0:length]

def is_sequence(arg):
    return (not hasattr(arg, "strip") and
            hasattr(arg, "__getitem__") or
            hasattr(arg, "__iter__"))

def srepr(arg):
    if is_sequence(arg):
        return '<' + ", ".join(srepr(x) for x in arg) + '>'
    return repr(arg)

def place_call(number_or_numbers, message):
    if not is_sequence(number_or_numbers):
        number_loop = [number_or_numbers]
    else:
        number_loop = number_or_numbers

    # client = TwilioRestClient(app.config['TWILIO_ACCOUNT_SID'], app.config['TWILIO_AUTH_TOKEN'])
    for number in number_loop:
        pass

def camelcase_keys(data):
    """
    Converts all the keys in a dict to camelcase. It works recursively to convert any nested dicts as well.
    @param data: The dict to convert
    """
    return_dict = {}
    for key in data:
        if isinstance(data[key], dict):
            return_dict[underscore_to_camelcase(key)] = camelcase_keys(data[key])
        else:
            return_dict[underscore_to_camelcase(key)] = data[key]

    return return_dict

def camelcase_to_underscore(name):
    """
    Converts a string to underscore. (Typically from camelcase.)
    @param name: The string to convert.
    """
    return re.sub('([a-z0-9])([A-Z])', r'\1_\2', re.sub('(.)([A-Z][a-z]+)', r'\1_\2', name)).lower()

def json_dumps(python_object, dents=None, if_err=None):
    """Takes a value (list, dictionary, etc) that is JSON serializable, and
    dumps it as a string. Indentation is set to 4 spaces by default.
    >>> import decimal
    >>> from datetime import date, datetime, time
    >>> json_dumps({'lang': 'python'}, dents=4)
    '{\\n    "lang": "python"\\n}'
    >>> json_dumps([2, 3, 4, 5, None])
    '[2, 3, 4, 5, null]'
    >>> json_dumps({'adatetime': datetime(2012, 1, 1, 12, 1, 1)})
    '{"adatetime": "2012-01-01 12:01:01"}'
    >>> json_dumps({'adate': date(2012, 1, 1)})
    '{"adate": "2012-01-01"}'
    >>> json_dumps({'atime': time(12, 1, 1)})
    '{"atime": "12:01:01"}'
    >>> json_dumps({'adecimal': decimal.Decimal('1.01')})
    '{"adecimal": 1.01}'

    @param python_object: A native Python instance (list, dictionary, etc).
    @param dents: The number of spaces used for indentation in the
                  JSON-formatted string that is returned.
    @param if_err: What is returned if an error occurs.
    @return: A JSON-formatted string."""
    def to_json(an_object):
        """
        Adding in custom serialization for Date & Decimal objects.

        """
        from datetime import date, datetime, time
        if (isinstance(an_object, date)
            or isinstance(an_object, datetime)
            or isinstance(an_object, time)):
            return str(an_object)
        raise TypeError(repr(an_object) + ' is not JSON serializable')

    try:
        return simplejson.dumps(python_object, default=to_json, indent=dents)
    except (ValueError, TypeError):
        return simplejson.dumps(if_err or {})


def json_loads(json_str, if_err=None):
    """Takes a string that is Python serializable, and loads it as a
    native Python instance.
    >>> json_loads('{"name": "Ben"}')
    {'name': 'Ben'}
    >>> json_loads('{angoij', if_err='{"Was there a problem?": true}')
    {'Was there a problem?': True}
    >>> json_loads('[2, 3, 4, 5, null]')
    [2, 3, 4, 5, None]

    @param json_str: A JSON-formatted string.
    @param if_err: What is returned if an error occurs.
    @return: A native Python instance (list, dictionary, etc)."""
    try:
        return simplejson.loads(json_str)
    except (ValueError, TypeError):
        return simplejson.loads(if_err or '{}')

def underscore_to_camelcase(name):
    """
    Converts a string to camelcase. (Typically from underscore.)
    @param name: The string to convert.
    """
    return re.sub(r'_([a-z])', lambda m: (m.group(1).upper()), name)

def uuid():
    """Returns a string instance of an universally unique identifier (UUID).
    >>> from utils import UUID_REGEX
    >>> bool(UUID_REGEX.match(uuid()))
    True
    >>> bool(UUID_REGEX.match('notauuid'))
    False

    @return: String UUID."""
    from uuid import uuid4
    return str(uuid4())

