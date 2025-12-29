"""Auto templates"""
import configparser

from pter import common


class AutoTemplate:
    def __init__(self, name=None, triggers=None, template=None):
        self.name = name
        self.triggers = triggers or set()
        self.template = template or ""

    def can_trigger(self, text, casesensitive):
        can_lowercase = casesensitive.can_lowercase(''.join(self.triggers))
        triggers = self.triggers
        if can_lowercase:
            text = text.lower()
            self.triggers = {w.lower() for w in self.triggers}
        words = set(text.split(' '))
        return len(words.intersection(self.triggers)) == len(self.triggers)


def load_auto_templates():
    if not common.AUTO_TEMPLATES_FILE.is_file():
        return

    config = configparser.ConfigParser()
    config.read(str(common.AUTO_TEMPLATES_FILE))

    for sectionname in config.sections():
        section = config[sectionname]
        template = AutoTemplate()
        template.name = sectionname
        template.triggers = {part.strip()
                             for part in section.get('trigger', '').split(' ')
                             if len(part.strip()) > 0}
        template.template = section.get('template', '').strip()

        if len(template.template) > 0:
            yield template
