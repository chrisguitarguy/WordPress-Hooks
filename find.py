import hashlib
import os
import re

import jinja2

DIR = os.path.abspath(os.path.dirname(__file__))
WP_DIR = os.path.join(DIR, 'trunk')
TEMPLATES = os.path.join(DIR, 'templates')

class Hook(object):
    """
    Container for the a WordPress hook.
    """
    trac_base = 'http://core.trac.wordpress.org/browser/trunk'
    
    def __init__(self, file, line, match_data):
        self._file = file
        self._line = line
        self.call = match_data[0]
        if 'do_action' == match_data[1].strip():
            self.type = 'action'
        else:
            self.type = 'filter'
        hookstuff = [i.strip() for i in match_data[-1].split(',')]
        self.hook = hookstuff[0].strip("'").strip('"')
        self.params = ', '.join(hookstuff[1:])
    
    def __repr__(self):
        return '<WordPress Hook({})>'.format(self.hook)
    
    @property
    def browse_link(self):
        return '{trac}{file}#L{line}'.format(trac=self.trac_base, 
                                       file=self._file, line=self._line)
    
    @property
    def hash_id(self):
        m = hashlib.md5('{}:{}:{}'.format(self.hook, self._file, self._line))
        return m.hexdigest()
        

def find_files():
    """
    Find all PHP files in our WP_DIR and put them into a list with a the
    full path.
    """
    rv = []
    for path, dirs, files in os.walk(WP_DIR):
        for f in files:
            if f.endswith('.php'):
                rv.append(os.path.join(path, f))
    return rv


def search_file(path):
    """
    Search a given file for do_action and apply_filters function calls.
    """
    regex = re.compile(r'((do_action|apply_filters)(_ref_array)?\((.+)\);)', re.I)
    rv = []
    with open(path) as f:
        for line, text in enumerate(f.readlines()):
            match = regex.search(text)
            if match is not None:
                _path = path.replace(WP_DIR, '')
                rv.append((_path, line+1, match.groups()))
    return rv


def find_hooks():
    """
    Combination of find_files() and search_files().  Find every hook, 
    put it into a big list, and return it.
    """
    rv = []
    for f in find_files():
        rv += search_file(f)
    return rv


def hooks_to_objects(hook_list):
    """
    Turn a list of hooks into a sorted list of Hook objects
    """
    rv = []
    for hook in hook_list:
        rv.append(Hook(*hook))
    rv.sort(key=lambda h: h.hook)
    return rv


def main():
    loader = jinja2.FileSystemLoader(TEMPLATES)
    env = jinja2.Environment(loader=loader)
    hooks = find_hooks()
    hooks = hooks_to_objects(hooks)
    t = env.get_template('list.html')
    out = t.render(hooks=hooks, total=len(hooks))
    with open('index.html', 'w') as f:
        f.write(out)


if __name__ == '__main__':
    main()
