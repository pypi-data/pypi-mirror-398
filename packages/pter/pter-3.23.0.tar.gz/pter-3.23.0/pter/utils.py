import datetime
import string
import re
import webbrowser
import pathlib
import urllib.request
import urllib.parse
import sys
import os

import pytodotxt
from pytodotxt import Task, TodoTxt

from pter import common
from pter.source import Source


DATETIME_FMT = '%Y-%m-%d-%H-%M-%S'
FORMAT_TOKEN_RE = re.compile(r'^([^a-z]*)([a-z][a-z-]*)(.*)$')
EMPTY_FIELD_RE = re.compile(r'([a-z]+[:])(?:\s|$)')


def duration_as_str(duration):
    seconds = int(duration.total_seconds())
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    
    result = ''
    if hours > 0:
        result += f'{hours}h'
    if minutes > 0:
        result += f'{minutes}m'

    return result


def parse_duration(text):
    duration = datetime.timedelta(0)

    sign = 1
    if text.startswith('-'):
        sign = -1
        text = text[1:]
    elif text.startswith('+'):
        text = text[1:]

    value = ''
    for char in text.lower():
        if char in string.digits:
            value += char
        elif char == 'h' and len(value) > 0:
            duration += datetime.timedelta(hours=int(value))
            value = ''
        elif char == 'm' and len(value) > 0:
            duration += datetime.timedelta(minutes=int(value))
            value = ''
        elif char == 's' and len(value) > 0:
            duration += datetime.timedelta(seconds=int(value))
            value = ''
        elif char == 'd' and len(value) > 0:
            duration += datetime.timedelta(days=int(value))
            value = ''
        elif char == 'w' and len(value) > 0:
            duration += datetime.timedelta(days=int(value)*7)
            value = ''
        else:
            # parse error
            return None

    if len(value) > 0:
        duration += datetime.timedelta(minutes=int(value))
    
    duration *= sign

    return duration


def task_parse_due(task):
    try:
        return datetime.datetime.strptime(task.attr_due[0], Task.DATE_FMT).date()
    except (ValueError, IndexError):
        return None


def task_due_in_days(task, default=None):
    if len(task.attr_due) == 0:
        return default
    today = datetime.datetime.now().date()
    then = task_parse_due(task)
    if then is None:
        return default
    return (then-today).days


def task_change_due(task, due, newdue):
    if isinstance(due, datetime.date):
        due = due.strftime(Task.DATE_FMT)
    if isinstance(newdue, datetime.date):
        newdue = newdue.strftime(Task.DATE_FMT)
    task.replace_attribute('due', due, newdue)


def dehumanize_dates(text, tags=None, businessdays=None):
    """Replace occurrences of relative dates in tags"""
    if tags is None:
        tags = ['due', 't']

    offset = 0
    found_any = True

    while found_any and offset < len(text):
        found_any = False
        for match in Task.KEYVALUE_RE.finditer(text, offset):
            if match is None:
                offset = len(text)
                break
            found_any = True
            if match.group(2) in tags and not Task.DATE_RE.match(match.group(3)):
                then = get_relative_date(match.group(3),
                                         businessdays=businessdays)
                if then is not None:
                    then = then.strftime(Task.DATE_FMT)
                    text = text[:match.start(3)] + \
                           then + \
                           text[match.end(3):]
                    offset = match.start(3) + len(then)
                    break
            offset = match.end(3) + 1
    return text


def ensure_up_to_date(task):
    ok = True
    if task.todotxt.refresh():
        task.todotxt.parse()
        tasks = [other
                 for other in task.todotxt.tasks
                 if str(other).strip() == str(task).strip()]
        ok = len(tasks) > 0
        if ok:
            task = tasks[0]

    if ok:
        return task

    return None


def toggle_tracking(task):
    if 'tracking' in task.attributes:
        return update_spent(task)
    task.add_attribute('tracking', datetime.datetime.now().strftime(DATETIME_FMT))
    return True


def toggle_done(task, clear_contexts, reuse_recurring, safe_save, force_completion_date, fix_priority):
    """Toggle the "done" status of the given task

    This may, in case of 'rec:' tags, create a follow-up task in the future
    and thus update the corresponding todo.txt file.
    """
    is_recurring = 'rec' in task.attributes

    if not task.is_completed and is_recurring:
        interval = task.attributes['rec']
        has_due = task.attributes.get('due')
        has_t = task.attributes.get('t')

        assert len(interval) > 0
        interval = interval[0]

        is_strict = interval.startswith('+')
        base_date = datetime.date.today()

        if is_strict:
            if has_due is not None:
                base_date = datetime.datetime.strptime(has_due[0], Task.DATE_FMT).date()
            elif has_t is not None:
                base_date = datetime.datetime.strptime(has_t[0], Task.DATE_FMT).date()

        next_due = get_relative_date(interval, None, base_date)

        if reuse_recurring:
            followup = task
        else:
            followup = Task(str(task), len(task.todotxt.tasks)+1, todotxt=task.todotxt)
            task.todotxt.tasks.append(followup)

        # update attributes
        followup.creation_date = datetime.date.today()

        if has_due is not None:
            followup.replace_attribute('due', has_due[0], next_due.strftime(Task.DATE_FMT))
        elif has_t is not None:
            followup.replace_attribute('t', has_t[0], next_due.strftime(Task.DATE_FMT))

        if None not in [has_t, has_due]:
            time_between_t_and_due = datetime.datetime.strptime(has_due[0], Task.DATE_FMT).date() \
                                      - datetime.datetime.strptime(has_t[0], Task.DATE_FMT).date()
            next_t = next_due - time_between_t_and_due
            followup.replace_attribute('t', has_t[0], next_t.strftime(Task.DATE_FMT))

        if reuse_recurring:
            task.parse(str(task))
            return

        # create the new task in the same todotxt file
        task.todotxt.save(safe_save)

    task.is_completed = not task.is_completed
    if task.is_completed:
        if task.creation_date is not None or force_completion_date:
            task.completion_date = datetime.datetime.now().date()
        if task.priority is not None and fix_priority:
            task.add_attribute('pri', task.priority)
            task.priority = None
        if len(clear_contexts) > 0 and task.description is not None:
            for context in clear_contexts:
                while f'@{context}' in task.description:
                    task.remove_context(context)
    else:
        task.completion_date = None
        attrs = task.attributes
        if 'pri' in attrs:
            task.priority = attrs['pri'][0]
            task.remove_attribute('pri')
    task.parse(str(task))


def toggle_hidden(task):
    is_hidden = len(task.attr_h) > 0 and task.attr_h[0] == '1'
    if len(task.attr_h) > 0:
        is_hidden = task.attr_h[0] == '1'
        task.remove_attribute('h', '1')
        if not is_hidden:
            task.add_attribute('h', '1')
    else:
        task.add_attribute('h', '1')


def set_priority(task, prio):
    if task.is_completed:
        return
    task.priority = prio
    task.parse(str(task))


def increase_priority(task):
    """Increase the priority of `task`

    Will do nothing if the task already has priority `(A)`.

    Returns True if the priority has been increased, False otherwise."""
    if task.priority is None:
        next_prio = 'Z'
    else:
        next_prio = max('A', min('Z', chr(ord(task.priority) - 1)))
    if task.priority != next_prio:
        set_priority(task, next_prio)
        return True
    return False


def decrease_priority(task):
    """Decrease the priority of `task`

    Will do nothing if the task has no priority.

    Returns True if the priority has been decreased, False otherwise."""
    if task.priority == 'Z' or task.priority == None:
        next_prio = None
    else:
        next_prio = max('A', min('Z', chr(ord(task.priority) + 1)))
    if task.priority != next_prio:
        set_priority(task, next_prio)
        return True
    return False


def sign(n):
    if n < 0:
        return -1
    elif n > 0:
        return 1
    return 0


def build_sort_order(order):
    sort_order = []
    for part in order.split(','):
        if part == common.TF_COMPLETED:
            sort_order.append(lambda t: t.is_completed is None or t.is_completed)
        elif part == common.TF_COMPLETED_DATE:
            sort_order.append(lambda t: sortable_completion_date(t))
        elif part in ['due_in', common.TF_DUEDAYS]:
            sort_order.append(lambda t: task_due_in_days(t, sys.maxsize))
        elif part in ['priority', common.TF_PRIORITY]:
            sort_order.append(lambda t: t.priority or 'ZZZ')
        elif part == common.TF_LINENR:
            sort_order.append(lambda t: t.linenr)
        elif part == common.TF_CREATED:
            sort_order.append(lambda t: t.creation_date or datetime.date.min)
        elif part == common.TF_FILE:
            sort_order.append(lambda t: t.todotxt.displayname.lower())
        elif part == 'project':
            sort_order.append(lambda t: sorted(t.projects)[0].lower() if len(t.projects) > 0 else 'zzzzz')
        elif part == 'context':
            sort_order.append(lambda t: sorted(t.contexts)[0].lower() if len(t.contexts) > 0 else 'zzzzz')
    return sort_order


def sortable_completion_date(task):
    if not task.is_completed:
        return datetime.date.max
    if task.completion_date is None:
        return datetime.date.min
    return task.completion_date


def sort_fnc(a, order):
    if isinstance(a, tuple):
        task, _ = a
    else:
        task = a
    return [fnc(task) for fnc in order]


def update_spent(task):
    now = datetime.datetime.now()
    tracking = task.attr_tracking
    raw_spent = task.attr_spent

    if len(tracking) == 0:
        return False

    try:
        then = datetime.datetime.strptime(tracking[0], DATETIME_FMT)
    except ValueError:
        return False

    if len(raw_spent) > 0:
        spent = parse_duration(raw_spent[0])
        if spent is None:
            return False
    else:
        spent = datetime.timedelta(0)
    
    diff = now - then
    if diff <= datetime.timedelta(minutes=1):
        diff = datetime.timedelta(0)

    task.remove_attribute('tracking', tracking[0])

    # TODO: make the minimal duration configurable
    if diff >= datetime.timedelta(minutes=1):
        spent = duration_as_str(spent + diff)
        if len(raw_spent) == 0:
            task.add_attribute('spent', spent)
        else:
            task.replace_attribute('spent', raw_spent[0], spent)

        return True

    return True


def human_friendly_date(text):
    if isinstance(text, datetime.datetime):
        then = text.date()
    elif isinstance(text, datetime.date):
        then = text
    elif isinstance(text, str):
        try:
            then = datetime.datetime.strptime(text, Task.DATE_FMT).date()
        except ValueError:
            return text
    else:
        return text
    today = datetime.date.today()
    diff = abs((then - today).days)
    then_wd = ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday',
               'Friday', 'Saturday', 'Sunday'][then.isoweekday()]

    if today == then:
        return 'today'
    if diff == 1:
        if then > today:
            return 'tomorrow'
        return 'yesterday'
    if diff == 2:
        if then > today:
            return 'in 2 days'
        return '2 days ago'
    if diff == 3:
        if then > today:
            return 'in 3 days'
    if diff < 8:
        if then > today:
            return 'next ' + then_wd
        return 'last ' + then_wd
    if diff < 34:
        diff_wk = diff//7
        plural = '' if diff_wk == 1 else 's'
        if then > today:
            return f'in {diff_wk} week{plural}'
        return f'{diff_wk} week{plural} ago'
    if diff < 180:
        diff_mnth = diff//30
        plural = '' if diff_mnth == 1 else 's'
        if then > today:
            return f'in {diff_mnth} month{plural}'
        return f'{diff_mnth} month{plural} ago'
    if diff < 350:
        if then > today:
            return 'in half a year'
        return 'half a year ago'
    return then.strftime(Task.DATE_FMT)


def parse_task_format(text):
    rawtokens = []
    token = ''
    in_block = False
    
    for char in text:
        if in_block:
            if char == '}':
                token += char
                rawtokens.append(token)
                token = ''
                in_block = False
                continue
        elif char == '{':
            if len(token) > 0:
                rawtokens.append(token)
            token = char
            in_block = True
            continue
        token += char

    if len(token) > 0:
        rawtokens.append(token)

    tokens = []
    for token in rawtokens:
        if len(token) > 2 and token.startswith('{') and token.endswith('}'):
            align = None
            token = token[1:-1]
            extra_left = None
            extra_right = None
            if ':' in token and len(token) > 3:
                token, align = token.split(':')

            match = FORMAT_TOKEN_RE.match(token)

            if match is None:
                continue

            if len(match.group(1)) > 0:
                extra_left = match.group(1)
            token = match.group(2)
            if len(match.group(3)) > 0:
                extra_right = match.group(3)

            tokens.append((token, align, extra_left, extra_right))
        else:
            tokens.append(token)

    return tokens


def unquote(text):
    if len(text) <= 1:
        return text
    if text[0] in '"\'' and text[0] == text[-1]:
        return text[1:-1]
    return text


def open_manual():
    docloc = common.HERE / "docs" / "pter.html"

    if docloc.exists():
        webbrowser.open('file://' + str(docloc))


def parse_searches():
    if not common.SEARCHES_FILE.exists():
        return {}

    searches = {}
    with open(common.SEARCHES_FILE, 'rt', encoding="utf-8") as fd:
        for line in fd.readlines():
            if '=' not in line:
                continue
            name, searchdef = line.split("=", 1)
            name = name.strip()
            searchdef = searchdef.strip()
            if len(name) == 0 or len(searchdef) == 0:
                continue
            searches[name.strip()] = searchdef.strip()

    return searches


def parse_templates():
    if not common.TEMPLATES_FILE.exists():
        return {}

    templates = {}
    with open(common.TEMPLATES_FILE, 'rt', encoding="utf-8") as fd:
        for line in fd.readlines():
            if '=' not in line:
                continue
            name, templatedef = line.split("=", 1)
            name = name.strip()
            templatedef = templatedef.strip()
            if len(name) == 0 or len(templatedef) == 0:
                continue
            templates[name.strip()] = templatedef.strip()

    return templates


def save_searches(searches):
    common.SEARCHES_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(common.SEARCHES_FILE, 'wt', encoding="utf-8") as fd:
        for name in sorted(searches.keys()):
            value = searches[name].strip()
            if len(value) == 0:
                continue
            fd.write(f"{name} = {value}\n")


def save_templates(templates):
    common.TEMPLATES_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(common.TEMPLATES_FILE, 'wt', encoding="utf-8") as fd:
        for name in sorted(templates.keys()):
            value = templates[name].strip()
            if len(value) == 0:
                continue
            fd.write(f"{name} = {value}\n")


def update_displaynames(sources):
    if len(sources) == 0:
        return

    pos = 2
    while True:
        displaynames = {source.displayname for source in sources}
        if len(displaynames) == len(sources):
            return
        for source in sources:
            source.displayname = os.sep.join(str(source.filename).split(os.sep)[-1*pos:])
        pos += 1


def delegate_task(task, marker):
    if task.description is None:
        task.description = ''
    task.description += ' ' + marker


def execute_delegate_action(task, to_attr, marker, action):
    if action == common.DELEGATE_ACTION_NONE:
        return

    recipient = ''
    if len(to_attr) > 0 and to_attr in task.attributes:
        recipient = ','.join(task.attributes[to_attr])

    if action == common.DELEGATE_ACTION_MAIL:
        # filter out "to:" (to_attr) and the delegation marker
        text = ' '.join([word for word in str(task).split(' ')
                         if word != marker
                            and (len(to_attr) == 0
                                 or not word.startswith(to_attr + ':'))])
        uri = 'mailto:' + urllib.parse.quote(recipient) + '?Subject=' + urllib.parse.quote(text)
        webbrowser.open(uri)


def new_task_id(sources, prefix=""):
    """Generate a new unique task ID
    The task ID will be unique for the given sources, and with the given prefix.
    """
    existing_ids = set()
    for source in sources:
        existing_ids |= {int(key[len(prefix):]) for key in source.task_ids
                         if key.startswith(prefix) and key[len(prefix):].isnumeric()}

    if len(existing_ids) > 0:
        highest = max(existing_ids)
    else:
        highest = 0

    return prefix + str(highest+1)


def query_latest_version():
    try:
        response = urllib.request.urlopen('https://vonshednob.cc/pter/latest')
        version = str(response.read(), 'ascii')
        if version.startswith('v'):
            version = version[1:]
        return version.strip()
    except:
        return ''


def open_sources(args, config):
    files = [pathlib.Path(fn).expanduser().resolve() for fn in args.filename]
    if len(files) == 0:
        files = [pathlib.Path(fn.strip()).expanduser().resolve()
                 for fn in config.list(common.SETTING_GROUP_GENERAL,
                                       common.SETTING_FILES,
                                       sep="\n")
                 if len(fn.strip()) > 0]
    serializer = pytodotxt.serialize_pedantic
    ffopt = config.get(common.SETTING_GROUP_GENERAL, common.SETTING_FILE_FORMAT)
    if ffopt == common.FORMAT_OPTION_RELAXED:
        serializer = pytodotxt.serialize_relaxed
    sources = [Source(TodoTxt(fn, serializer=serializer)) for fn in files]
    for source in sources:
        if source.filename.exists():
            source.parse()
    return sources


def create_from_search(searcher):
    text = []
    for group, prefix in [('contexts', '@'), ('projects', '+'), ('words', '')]:
        text += [prefix+word for word in getattr(searcher, group, set())]
    return ' '.join(text)


def auto_task_id(sources, text):
    words = []
    for word in text.split(' '):
        if word.startswith('id:'):
            _, base = word.split(':', 1)
            if '#' in base:
                base, keyword = base.split('#', 1)
                if keyword in ['', 'auto']:
                    word = 'id:{}'.format(new_task_id(sources, base))
        words.append(word)
    return ' '.join(words)


def clean_description(text):
    """Clean the given text from non-printing characters

    Replaces the characters 0 through 31 with ' ' (space)
    """
    return ''.join([letter if ord(letter) > 31 else ' '
                    for letter in text])


# Create an index of weekday name to its ISO weekday number
DAYNAMES = {'mon': 1, 'tue': 2, 'wed': 3, 'thu': 4, 'fri': 5, 'sat': 6, 'sun': 7,
            'monday': 1, 'tuesday': 2, 'wednesday': 3, 'thursday': 4, 'friday': 5,
            'saturday': 6, 'sunday': 7}


def get_relative_date(text, fmt=None, base=None, businessdays=None):
    text = text.replace('+', '')
    days = 0
    weeks = 0
    months = 0
    years = 0
    value = ''
    is_business_day_mode_enabled = False
    bday_sign = 1
    today = datetime.datetime.now()
    if base is not None:
        assert isinstance(base, datetime.date)
        today = base

    if not isinstance(businessdays, (list, tuple, set)):
        businessdays = {1, 2, 3, 4, 5}

    then = None
    if text.lower() == 'today':
        then = today
    if text.lower() == 'tomorrow':
        then = today + datetime.timedelta(days=1)
    if text.lower() == 'yesterday':
        then = today - datetime.timedelta(days=1)
    if text.lower() in ['next-week', 'week']:
        then = today + datetime.timedelta(weeks=1)
    if text.lower() in DAYNAMES:
        isoweekday = DAYNAMES[text.lower()]
        days = ((isoweekday-1) - today.weekday()) % 7
        if days == 0:
            days = 7
        then = today + datetime.timedelta(days=days)
    if then is not None:
        if fmt is not None:
            return then.strftime(fmt)
        return then

    for char in text.lower():
        if char in string.digits:
            value += char
        elif char in '+-' and len(value) == 0:
            if char == '-':
                value = char
        elif len(value) == 0 or \
             value.isnumeric() or \
             (value.startswith('-') and value[1:].isnumeric()):
            if len(value) == 0:
                value = '1'

            if char == 'd':
                days += int(value)
            elif char == 'b':
                days += int(value)
                is_business_day_mode_enabled = True
                if value.startswith('-'):
                    bday_sign = -1
            elif char == 'w':
                weeks += int(value)
            elif char == 'm':
                months += int(value)
            elif char == 'y':
                years += int(value)
            else:
                # parse error
                return None
            value = ''
        else:
            # parse error
            return None

    if value.isnumeric() or (value.startswith('-') and value[1:].isnumeric()):
        days += int(value)

    month = today.month + months
    if month > 12:
        years += month // 12
        month = month % 12

    year = today.year + years

    if year + years > datetime.MAXYEAR:
        year = datetime.MAXYEAR

    then = datetime.date(year, month, 1) + \
           datetime.timedelta(days=today.day + days - 1,
                              weeks=weeks)

    if is_business_day_mode_enabled and len(businessdays) > 0:
        step = datetime.timedelta(days=bday_sign)
        while then.isoweekday() not in businessdays:
            then = then + step

    if fmt is not None:
        then = then.strftime(fmt)
    return then
