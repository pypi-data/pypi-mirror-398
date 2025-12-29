"""The content of the help screen and the key listing for pter

Not for qpter.
"""
from pter.tr import tr


SHORT_NAMES = {'quit': 'Quit',
               'cancel': 'Cancel',
               'select-item': 'Select',
               'next-item': 'Next item',
               'prev-item': 'Previous item',
               'page-up': 'Page up',
               'page-down': 'Page down',
               'search': 'Search',
               'open-url': 'Open URL',
               'edit-external': 'Open task in editor',
               'edit-file-external': 'Open file in editor',
               'load-template': 'Load task template',
               'save-template': 'Save task as template',
               'load-search': 'Load search',
               'save-search': 'Save search',
               'search-context': 'Search by task context',
               'search-project': 'Search by task project',
               'clear-search': 'Clear search',
               'first-item': 'First item',
               'last-item': 'Last item',
               'edit-task': 'Edit task',
               'create-task': 'New task',
               'edit-note': 'Edit note',
               'view-note': 'View note',
               'jump-to': 'Jump to item',
               'toggle-hidden': 'Toggle hidden',
               'toggle-done': 'Toggle done',
               'toggle-tracking': 'Toggle tracking',
               'show-help': 'Help',
               'open-manual': 'Read manual',
               'go-left': 'Go left',
               'go-right': 'Go right',
               'go-word-left': 'Go one word left',
               'go-word-right': 'Go one word right',
               'go-bol': 'Go to start of line',
               'go-eol': 'Go to end of line',
               'goto-empty': 'Go to the next empty key',
               'del-left': 'Delete left',
               'del-right': 'Delete right',
               'del-to-bol': 'Delete to start of line',
               'del-to-eol': 'Delete to end of line',
               'del-word-left': 'Delete one word left',
               'del-word-right': 'Delete one word right',
               'submit-input': 'Apply changes',
               'submit-without-template': 'Create task (no template)',
               'select-file': 'Select file',
               'delegate': 'Delegate task',
               'delete-task': 'Delete task',
               'archive': 'Archive task',
               'refresh-screen': 'Refresh screen',
               'reload-tasks': 'Reload todo file(s)',
               'comp-next': 'Next completion',
               'comp-prev': 'Previous completion',
               'comp-use': 'Use selected completion',
               'comp-close': 'Close completion list',
               'inc-due': 'Increase due date',
               'dec-due': 'Decrease due date',
               'clear-due': 'Clear due date',
               'prio-a': 'Set priority to (A)',
               'prio-b': 'Set priority to (B)',
               'prio-c': 'Set priority to (C)',
               'prio-d': 'Set priority to (D)',
               'prio-none': 'Remove priority',
               'prio-up': 'Increase priority',
               'prio-down': 'Decrease priority',
               'to-clipboard': 'Copy to clipboard',
               }


def compile_key_listing(app):
    nav_fncs = ['next-item', 'prev-item', 'page-up', 'page-down',
                'first-item', 'last-item', 'jump-to', 'select-item']
    edt_fncs = ['toggle-hidden', 'toggle-done', 'edit-task', 'create-task',
                'toggle-tracking', 'delegate', 'save-template', 'load-template',
                'archive', 'delete-task', 'prio-a', 'prio-b', 'prio-c', 'prio-d',
                'prio-none', 'prio-up', 'prio-down', 'edit-note', 'view-note',
                'inc-due', 'dec-due', 'clear-due',
                'edit-file-external', 'edit-external',
                'to-clipboard']
    search_fncs = ['search', 'load-search', 'save-search',
                   'search-context', 'search-project', 'clear-search']
    meta_fncs = ['show-help', 'open-manual', 'quit', 'cancel', 'refresh-screen',
                 'reload-tasks']
    other_fncs = ['open-url']

    lines = [(tr('TASK LIST'), '', ''), ('', '', '')]

    if nlines := [(name, key, fnc)
                  for name, key, fnc in collect_name_fnc(meta_fncs,
                                                         app.key_mapping)]:
        lines += [(tr('Program'), '', '')] + nlines

    if nlines := [(name, key, fnc)
                  for name, key, fnc in collect_name_fnc(nav_fncs,
                                                         app.key_mapping)]:
        lines += [('', '', ''), (tr('Navigation'), '', '')] + nlines

    if nlines := [(name, key, fnc)
                  for name, key, fnc in collect_name_fnc(search_fncs,
                                                         app.key_mapping)]:
        lines += [('', '', ''), (tr('Search'), '', '')] + nlines

    if nlines := [(name, key, fnc)
                  for name, key, fnc in collect_name_fnc(edt_fncs,
                                                         app.key_mapping)]:
        lines += [('', '', ''), (tr('Task actions'), '', '')] + nlines

    if nlines := [(name, key, fnc)
                  for name, key, fnc in collect_name_fnc(other_fncs,
                                                         app.key_mapping)]:
        lines += [('', '', ''), (tr('Other'), '', '')] + nlines

    edt_nav_fncs = ['go-left', 'go-right', 'go-bol', 'go-eol', 'goto-empty', 'go-word-left', 'go-word-right']
    edt_edt_fncs = ['del-left', 'del-right', 'del-to-bol', 'del-to-eol', 'del-word-left', 'del-word-right']
    edt_meta_fncs = ['cancel', 'submit-input', 'submit-without-template', 'select-file']
    edt_comp_fncs = ['comp-next', 'comp-prev', 'comp-use', 'comp-close']

    lines += [('', '', ''), ('', '', ''), (tr('TASK EDITING'), '', '')]

    if nlines := [(name, key, fnc)
                  for name, key, fnc in collect_name_fnc(edt_meta_fncs,
                                                         app.editor_key_mapping)]:
        lines += [('', '', ''), (tr('General'), '', '')] + nlines

    if nlines := [(name, key, fnc)
                  for name, key, fnc in collect_name_fnc(edt_nav_fncs,
                                                         app.editor_key_mapping)]:
        lines += [('', '', ''), (tr('Navigation'), '', '')] + nlines

    if nlines := [(name, key, fnc)
                  for name, key, fnc in collect_name_fnc(edt_edt_fncs,
                                                         app.editor_key_mapping)]:
        lines += [('', '', ''), (tr('Deletion'), '', '')] + nlines

    if nlines := [(name, key, fnc)
                  for name, key, fnc in collect_name_fnc(edt_comp_fncs,
                                                         app.completion_key_mapping)]:
        lines += [('', '', ''), (tr('Completion'), '', '')] + nlines

    return lines


def collect_name_fnc(fncs, mapping):
    for name, fnc in sorted([(v, k) for k, v in SHORT_NAMES.items() if k in fncs]):
        for key in [k for k, v in mapping.items() if v == fnc]:
            yield name, key, fnc
