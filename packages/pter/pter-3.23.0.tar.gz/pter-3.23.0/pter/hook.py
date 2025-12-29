"""Integration with external programs"""
import shutil
import shlex
import subprocess
import logging


class Hook:
    def __init__(self, app, configuration):
        self.app = app
        self.program = ''
        self.parameters = []

        self.parse_configuration(configuration)

    def is_ok(self):
        return self.program is not None \
           and len(self.program) > 0

    def run(self, task):
        parameters = self.expand_parameters(task)
        command = ' '.join([self.program] + parameters)
        logging.debug(f"Running hook: {command}")

        result = subprocess.run(command,
                                stdout=subprocess.DEVNULL,
                                stderr=subprocess.PIPE,
                                shell=True,
                                check=False)
        return result

    def parse_configuration(self, text):
        parts = parse_hook_configuration(text)

        self.program = shutil.which(parts[0])
        if self.program is None:
            logging.error(f"Could not find program '{parts[0]}', "
                           "hook inactive")
        self.parameters = parts[1:]

    def expand_parameters(self, task):
        expanded = []
        contexts = [c for c in task.contexts if len(c) > 0]
        context = ''
        if len(contexts) > 0:
            context = contexts[0]
        projects = [p for p in task.projects if len(p) > 0]
        project = ''
        if len(projects) > 0:
            project = projects[0]
        taskid = ''
        if len(task.attributes.get('id', [])) > 0:
            taskid = task.attributes['id'][0]
        notes = [str(self.app.resolve_note(n))
                 for n in task.attributes.get('note', [])]
        if len(notes) == 0:
            notes = ['']

        mapping = [('{description}', shlex.quote(task.bare_description())),
                   ('{full}', shlex.quote(task.description)),
                   ('{raw}', shlex.quote(str(task))),
                   ('{context}', shlex.quote(context)),
                   ('{project}', shlex.quote(project)),
                   ('{id}', shlex.quote(taskid)),
                   ('{note}', shlex.quote(notes[0])),
                   ]

        for part in self.parameters:
            if isinstance(part, str):
                expanded.append(part)
                continue

            selector = part[-1]
            prefix = part[:-1]

            if '{contexts}' in selector or '{projects}' in selector:
                collection = contexts
                placeholder = '{contexts}'
                if '{projects}' in selector:
                    collection = projects
                    placeholder = '{projects}'

                for value in collection:
                    value = shlex.quote(value)
                    expanded += prefix \
                                + [selector.replace(placeholder, value)]
            elif '{*contexts}' in selector or '{*projects}' in selector:
                collection = contexts
                placeholder = '{*contexts}'
                if '{*projects}' in selector:
                    collection = projects
                    placeholder = '{*projects}'
                if len(collection) == 0:
                    continue
                expanded += prefix
                if selector != placeholder:
                    expanded += [selector.replace(placeholder,
                                                  shlex.quote(value))
                                 for value in collection]
                else:
                    expanded += list(collection)
            else:
                some_replacement = False
                for pattern, replacement in mapping:
                    if pattern not in selector:
                        continue
                    if len(replacement) == 0:
                        continue
                    selector = selector.replace(pattern, replacement)
                    some_replacement = True
                    break

                if len(selector) == 0 or not some_replacement:
                    continue

                expanded += prefix
                expanded += [selector]
        return expanded


def parse_hook_configuration(text):
    tokens = []
    token = ''
    group = []

    in_brace = 0
    quoted = ''
    escaped = False

    for letter in text:
        if escaped:
            token += letter
            escaped = False
        elif letter == quoted:
            quoted = ''
        elif letter == '\\':
            escaped = True
        elif len(quoted) > 0:
            token += letter
        elif in_brace > 0 and letter == '}':
            in_brace -= 1
            if in_brace == 0:
                if len(token) > 0:
                    group.append(token)
                tokens.append(group)
                group = []
                token = ''
            else:
                token += letter
        elif letter == '{':
            if in_brace > 0:
                token += letter
            else:
                group = []
            in_brace += 1
        elif letter in '"\'':
            quoted = letter
        elif letter == ' ':
            if len(token) > 0:
                if in_brace:
                    group.append(token)
                else:
                    tokens.append(token)
            token = ''
        else:
            token += letter

    if len(token) > 0:
        tokens.append(token)

    return tokens
