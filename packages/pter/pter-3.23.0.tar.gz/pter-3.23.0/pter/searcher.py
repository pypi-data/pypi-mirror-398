import datetime
import string

from pytodotxt import Task

from pter.common import SearchCaseBehaviour
from pter.utils import get_relative_date


class Searcher:
    def __init__(self,
                 text=None,
                 casesensitive=None,
                 default_threshold=None,
                 hide_sequential=True,
                 businessdays=None):
        self.words = set()
        self.not_words = set()
        self.lowercase_words = False
        self.projects = set()
        self.not_projects = set()
        self.lowercase_projects = False
        self.contexts = set()
        self.not_contexts = set()
        self.lowercase_contexts = False
        self.ids = set()
        self.not_ids = set()
        self.filenames = set()
        self.not_filenames = set()
        self.lowercase_filenames = False
        self.after = set()
        self.refs = set()
        self.lowercase_ids = False
        self.done = None
        self.show_hidden = False
        self.priority = None
        self.not_priority = False
        self.default_threshold = default_threshold
        self.hide_sequential = hide_sequential
        if default_threshold is None or len(default_threshold) == 0:
            self.default_threshold = 'today'
        self.threshold = self.default_threshold
        self.due = None
        self.created = None
        self.completed = None
        self.casesensitive = casesensitive or SearchCaseBehaviour.SENSITIVE
        self.sources = None
        self.task_by_id = None
        self.parents = None
        self.businessdays = businessdays

        self.text = text

        if text is not None:
            self.parse()

    def get_relative_date(self, *args, **kwargs):
        kwargs['businessdays'] = self.businessdays
        return get_relative_date(*args, **kwargs)

    def reset(self):
        self.words = set()
        self.not_words = set()
        self.lowercase_words = False
        self.projects = set()
        self.not_projects = set()
        self.lowercase_projects = False
        self.contexts = set()
        self.not_contexts = set()
        self.lowercase_contexts = False
        self.ids = set()
        self.not_ids = set()
        self.filenames = set()
        self.not_filenames = set()
        self.lowercase_filenames = False
        self.after = set()
        self.refs = set()
        self.lowercase_ids = False
        self.done = None
        self.show_hidden = False
        self.priority = None
        self.threshold = self.get_relative_date(self.default_threshold, Task.DATE_FMT) or \
                         self.default_threshold
        self.due = None
        self.created = None
        self.completed = None

    def update_sources(self, sources):
        self.sources = sources
        self.task_by_id = {}
        self.parents = {}
        with_sequence = set()
        for source in self.sources:
            for task in source.tasks:
                if len(task.attr_id) == 0:
                    continue
                if len(task.attr_after) > 0:
                    with_sequence.add(task)
                for taskid in task.attr_id:
                    if taskid not in self.task_by_id:
                        self.task_by_id[taskid] = set()
                    self.task_by_id[taskid].add(task)

        # for each task obtain a set of their direct and indirect parents
        for task in with_sequence:
            parents = self._parse_ids('after', task)
            queue = parents.copy()
            while len(queue) > 0:
                otherid = queue.pop()
                if otherid in self.parents:
                    parents |= self.parents[otherid]
                    break
                parents.add(otherid)

                if otherid not in self.task_by_id:
                    continue
                for other in self.task_by_id[otherid]:
                    queue |= self._parse_ids('after', other).difference(parents)
            if len(parents) > 0:
                for taskid in task.attr_id:
                    if taskid not in self.parents:
                        self.parents[taskid] = set()
                    self.parents[taskid] |= parents

    def _parse_ids(self, keyword, task):
        these = set()
        for value in task.attributes.get(keyword, []):
            these |= set(value.split(','))
        return these

    def parse(self):
        self.reset()
        if self.text is None:
            return

        text = self.text

        for part in text.split(' '):
            do_not = False
            partlower = part.lower()

            if partlower.startswith('sort:'):
                continue

            if partlower.startswith('not:'):
                if len(part) == 4:
                    self.words.add(part)
                    continue

                do_not = True
                part = part[4:]
                partlower = partlower[4:]
            elif part.startswith('-'):
                do_not = True
                part = part[1:]
                partlower = partlower[1:]

            if len(part) == 0:
                continue

            if part.startswith('@') and len(part) > 1:
                if do_not:
                    self.not_contexts.add(part[1:])
                else:
                    self.contexts.add(part[1:])

            elif part.startswith('+') and len(part) > 1:
                if do_not:
                    self.not_projects.add(part[1:])
                else:
                    self.projects.add(part[1:])

            elif partlower.startswith('done:'):
                _, value = part.split(':', 1)
                if len(value) == 0 or value.lower() == 'any':
                    self.done = None
                else:
                    self.done = value.lower() in ['y', 'yes']

            elif partlower.startswith('hidden:') or partlower.startswith('h:'):
                _, value = part.split(':', 1)
                if len(value) == 0 or value.lower() == 'any':
                    self.show_hidden = 'any'
                elif value in ['y', 'yes', '1']:
                    self.show_hidden = True

            elif partlower.startswith('pri:'):
                _, value = part.split(':', 1)
                self.priority = (value.upper(), value.upper())
                if do_not:
                    self.not_priority = True

            elif partlower.startswith('moreimportant:') or partlower.startswith('mi:'):
                _, value = part.split(':', 1)
                if not isinstance(self.priority, list):
                    # upper bound, lower bound
                    self.priority = [' ', 'ZZZZ']
                self.priority[1] = value.upper()
                if do_not:
                    self.not_priority = True

            elif partlower.startswith('lessimportant:') or partlower.startswith('li:'):
                _, value = part.split(':', 1)
                if not isinstance(self.priority, list):
                    # upper bound, lower bound
                    self.priority = [' ', 'ZZZZ']
                self.priority[0] = value.upper()
                if do_not:
                    self.not_priority = True

            elif partlower.startswith('due:'):
                _, value = part.split(':', 1)
                if len(value) == 0 or value.lower() in ['y', 'yes', 'any']:
                    self.due = ['0000-00-00', '9999-99-99']
                elif value.lower() in ['no', 'n']:
                    self.due = 'no'
                else:
                    value = self.get_relative_date(value, Task.DATE_FMT) or value
                    self.due = [value, value]

            elif partlower.startswith('duebefore:') or partlower.startswith('db:'):
                _, value = part.split(':', 1)
                if not isinstance(self.due, list):
                    self.due = ['0000-00-00', '9999-99-99']
                self.due[1] = self.get_relative_date(value, Task.DATE_FMT) or value

            elif partlower.startswith('dueafter:') or partlower.startswith('da:'):
                _, value = part.split(':', 1)
                if not isinstance(self.due, list):
                    self.due = ['0000-00-00', '9999-99-99']
                self.due[0] = self.get_relative_date(value, Task.DATE_FMT) or value

            elif partlower.startswith('created:'):
                _, value = part.split(':', 1)
                value = self.get_relative_date(value, Task.DATE_FMT) or value
                self.created = [value, value]

            elif partlower.startswith('createdbefore:') or partlower.startswith('crb:'):
                _, value = part.split(':', 1)
                if self.created is None:
                    self.created = ['0000-00-00', '9999-99-99']
                self.created[1] = self.get_relative_date(value, Task.DATE_FMT) or value

            elif partlower.startswith('createdafter:') or partlower.startswith('cra:'):
                _, value = part.split(':', 1)
                if self.created is None:
                    self.created = ['0000-00-00', '9999-99-99']
                self.created[0] = self.get_relative_date(value, Task.DATE_FMT) or value

            elif partlower.startswith('completed:'):
                _, value = part.split(':', 1)
                value = self.get_relative_date(value, Task.DATE_FMT) or value
                self.completed = [value, value]

            elif partlower.startswith('completedbefore:') or partlower.startswith('cob:'):
                _, value = part.split(':', 1)
                if self.completed is None:
                    self.completed = ['0000-00-00', '9999-99-99']
                self.completed[1] = self.get_relative_date(value, Task.DATE_FMT) or value

            elif partlower.startswith('completedafter:') or partlower.startswith('coa:'):
                _, value = part.split(':', 1)
                if self.completed is None:
                    self.completed = ['0000-00-00', '9999-99-99']
                self.completed[0] = self.get_relative_date(value, Task.DATE_FMT) or value

            elif partlower.startswith('t:') or \
                 partlower.startswith('tickler:') or \
                 partlower.startswith('threshold:'):
                _, value = part.split(':', 1)
                if len(value) == 0 or value.lower() == 'any':
                    self.threshold = None
                elif value.lower() in ['yes', 'no', 'y', 'n']:
                    self.threshold = value.lower()
                else:
                    self.threshold = self.get_relative_date(value, Task.DATE_FMT) or value

            elif partlower.startswith('id:'):
                _, value = part.split(':', 1)
                if len(value) > 0:
                    value = set(value.split(','))

                    if do_not:
                        self.not_ids |= value
                    else:
                        self.ids |= value
                else:
                    if do_not:
                        self.not_words.add(part)
                    else:
                        self.words.add(part)

            elif partlower.startswith('after:') and self.after is not None:
                _, value = part.split(':', 1)
                if len(value) == 0:
                    self.after = None
                else:
                    values = set(value.split(','))
                    if do_not:
                        pass
                    else:
                        self.after |= values

            elif partlower.startswith('ref:') and self.refs is not None:
                _, value = part.split(':', 1)
                if len(value) > 0:
                    values = set(value.split(','))
                    if do_not:
                        pass
                    else:
                        self.refs |= values

            elif partlower.startswith('file:'):
                _, value = part.split(':', 1)
                if len(value) > 0:
                    if do_not:
                        self.not_filenames.add(value)
                    else:
                        self.filenames.add(value)

            else:
                if do_not:
                    self.not_words.add(part)
                else:
                    self.words.add(part)

        if len(self.words) + len(self.not_words) > 0 and \
           self.casesensitive.can_lowercase(''.join(self.words | self.not_words)):
            self.lowercase_words = True
            self.words = {w.lower() for w in self.words}
            self.not_words = {w.lower() for w in self.not_words}
        if len(self.contexts) + len(self.not_contexts) > 0 and \
           self.casesensitive.can_lowercase(''.join(self.contexts | self.not_contexts)):
            self.lowercase_contexts = True
            self.contexts = {c.lower() for c in self.contexts}
            self.not_contexts = {c.lower() for c in self.not_contexts}
        if len(self.projects) + len(self.not_projects) > 0 and \
           self.casesensitive.can_lowercase(''.join(self.projects | self.not_projects)):
            self.lowercase_projects = True
            self.projects = {c.lower() for c in self.projects}
            self.not_projects = {c.lower() for c in self.not_projects}
        if len(self.filenames) + len(self.not_filenames) > 0 and \
           self.casesensitive.can_lowercase(''.join(self.filenames | self.not_filenames)):
            self.lowercase_filenames = True
            self.filenames = {f.lower() for f in self.filenames}
            self.not_filenames = {f.lower() for f in self.not_filenames}

        id_checks = set()
        if self.ids is not None:
            id_checks |= self.ids
        if self.not_ids is not None:
            id_checks |= self.not_ids
        if self.refs is not None:
            id_checks |= self.refs
        if self.after is not None:
            id_checks |= self.after
        if len(id_checks) > 0 and \
           self.casesensitive.can_lowercase(''.join(id_checks)):
            self.lowercase_ids = True
            self.ids = {i.lower() for i in self.ids}
            self.not_ids = {i.lower() for i in self.not_ids}
            self.refs = {i.lower() for i in self.refs}
            if self.after is not None:
                self.after = {i.lower() for i in self.after}

    def match(self, task):
        attrs = dict([(k if self.casesensitive else k.lower(), v)
                      for k, v in task.attributes.items()])
        return all([self.match_words(task),
                    self.match_contexts(task),
                    self.match_projects(task),
                    self.match_done(task),
                    self.match_hidden(attrs),
                    self.match_priority(task),
                    self.match_ids(task),
                    self.match_filenames(task),
                    self.match_refs(task),
                    self.match_after(task, attrs),
                    self.match_due(attrs),
                    self.match_created(task),
                    self.match_completed(task),
                    self.match_threshold(attrs)])

    def match_words(self, task):
        if len(self.words) == 0 and len(self.not_words) == 0:
            return True

        description = task.description
        if description is None:
            description = ''

        if self.lowercase_words:
            description = description.lower()

        return all([word in description for word in self.words]) \
                and not any([word in description for word in self.not_words])

    def match_contexts(self, task):
        if len(self.contexts) == 0 and len(self.not_contexts) == 0:
            return True

        contexts = task.contexts
        if self.lowercase_contexts:
            contexts = [context.lower() for context in contexts]

        return all([context in contexts for context in self.contexts]) \
                and not any([context in contexts for context in self.not_contexts])

    def match_projects(self, task):
        if len(self.projects) == 0 and len(self.not_projects) == 0:
            return True

        projects = task.projects
        if self.lowercase_projects:
            projects = [project.lower() for project in projects]

        return all([project in projects for project in self.projects]) \
                and not any([project in projects for project in self.not_projects])

    def match_hidden(self, attrs):
        if self.show_hidden == 'any':
            return True

        if self.show_hidden:
            return 'h' in attrs and any(v == '1' for v in attrs['h'])

        return 'h' not in attrs or all(v != '1' for v in attrs['h'])

    def match_done(self, task):
        return self.done is None or task.is_completed == self.done

    def match_priority(self, task):
        if self.priority is None:
            return True

        pri = 'ZZZ'
        upper, lower = (p.upper() for p in self.priority)
        if task.priority is not None:
            pri = task.priority.upper()

        # upper < pri < lower is counter-intuitive, but:
        # pri 'a' < pri 'b'
        result = (lower == upper and pri == lower) or \
                 upper < pri < lower
        if self.not_priority:
            return not result
        return result

    def match_threshold(self, attrs):
        if self.threshold is None:
            return True
        if self.threshold in ['n', 'no']:
            return 't' not in attrs
        if self.threshold in ['y', 'yes']:
            return 't' in attrs
        return 't' not in attrs or attrs['t'][0] <= self.threshold

    def match_due(self, attrs):
        if self.due is None:
            return True

        if self.due == 'no':
            return 'due' not in attrs

        if 'due' not in attrs:
            return False

        if self.due[0] == self.due[1]:
            return attrs['due'][0][:10] == self.due[0]

        return self.due[0] < attrs['due'][0][:10] < self.due[1]

    def match_created(self, task):
        if self.created is None:
            return True

        if task.creation_date is None:
            return False

        task_created = task.creation_date.strftime(Task.DATE_FMT)

        if self.created[0] == self.created[1]:
            return self.created[0] == task_created

        return self.created[0] < task_created < self.created[1]

    def match_completed(self, task):
        if self.completed is None:
            return True

        if task.completion_date is None:
            return False

        task_completed = task.completion_date.strftime(Task.DATE_FMT)

        if self.completed[0] == self.completed[1]:
            return self.completed[0] == task_completed

        return self.completed[0] < task_completed < self.completed[1]

    def match_ids(self, task):
        if len(self.not_ids) == 0 and len(self.ids) == 0:
            return True

        ids = self._parse_ids('id', task)

        if self.lowercase_ids:
            ids = {i.lower() for i in ids}

        return (len(self.ids) == 0 or len(self.ids.intersection(ids)) > 0) and \
               (len(self.not_ids) == 0 or len(self.not_ids.intersection(ids)) == 0)

    def match_refs(self, task):
        if len(self.refs) == 0:
            return True

        ids = self._parse_ids('after', task)
        ids |= self._parse_ids('ref', task)

        if self.lowercase_ids:
            ids = {i.lower() for i in ids}

        return len(ids) > 0 and \
               len(self.refs.intersection(ids)) > 0

    def match_filenames(self, task):
        if len(self.filenames) + len(self.not_filenames) == 0:
            return True

        return hasattr(task, 'todotxt') is not None and \
               task.todotxt is not None and \
               all([pattern in str(task.todotxt.filename) if not self.lowercase_filenames
                    else pattern.lower() in str(task.todotxt.filename).lower()
                    for pattern in self.filenames]) and \
               not any([pattern in str(task.todotxt.filename) if not self.lowercase_filenames
                        else pattern.lower() in str(task.todotxt.filename).lower()
                        for pattern in self.not_filenames])

    def match_after(self, task, attrs):
        if self.after is None:
            return True

        if len(self.after) == 0 and \
           len(attrs.get('after', [])) == 0:
            return True

        if self.task_by_id is None:
            return True

        parents = self._parse_ids('after', task)

        if len(self.after) == 0:
            # normal sequence behaviour
            return not self.hide_sequential or \
                   all([parentid not in self.task_by_id or
                        any([other.is_completed for other in self.task_by_id[parentid]]) 
                        for parentid in parents])
        else:
            # collect all indirect parents, too
            for taskid in task.attr_id:
                parents |= self.parents.get(taskid, set())
            if self.lowercase_ids:
                parents = {p.lower() for p in parents}
            return any([parent in parents for parent in self.after])

