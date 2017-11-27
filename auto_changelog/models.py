"""
The basic data structures used in the project.
"""

import datetime
import re
from collections import defaultdict


class Tag:
    def __init__(self, name, date, commit):
        self.name = 'Version ' + name if not name.lower().startswith('v') else name
        self.version = name
        self._commit = commit
        self.date = datetime.datetime.fromtimestamp(date)
        self.commits = []
        self.groups = defaultdict(list)
        
    def add_commit(self, commit):
        self.commits.append(commit)
        commit.tag = self
        self.groups[commit.category].append(commit)
        
    def __repr__(self):
        return '<{}: {!r}>'.format(
                self.__class__.__name__,
                self.name)
    
class Unreleased:
    def __init__(self, commits):
        self.name = 'Unreleased'
        self.groups = defaultdict(list)
        self.commits = commits
        
        for commit in commits:
            self.add_commit(commit)
            
    def add_commit(self, commit):
        self.groups[commit.category].append(commit)

    def __repr__(self):
        return '<{}: {!r}>'.format(
                self.__class__.__name__,
                self.name)        
        
class Commit:
    def __init__(self, commit):
        self._commit = commit
        self.date = datetime.datetime.fromtimestamp(commit.committed_date)
        self.commit_hash = commit.hexsha
        
        first_line = commit.message.splitlines()[0].strip()
        body = ('\n'.join(commit.message.splitlines()[1:])).strip()
        if first_line.startswith('Merge pull request') and body:
            first_line = body.splitlines()[0].strip()
            body = ('\n'.join(body.splitlines()[1:])).strip()

        self.first_line = first_line
        self.body = body.strip()
        self.message = commit.message
        self.tag = None
        
        self.category, self.extra_categories, self.specific, self.description = self.categorize()

        last_line = body.splitlines()[-1] if body else ''
        if re.search(r'ref[:. ]\s*(TPD|TIM)-\d+', last_line, re.IGNORECASE):
            self.ticket_refs = re.findall(r'(TPD-\d+|TIM-\d+)', last_line, re.IGNORECASE)

    def categorize(self):
        match = re.match(r'(\w+)(\([\w, ]+\))?:\s*(.*)', self.first_line)

        if match:
            categories, specific, description = match.groups()

            categories = [c.strip() for c in categories.lower().split(',')]

            if self.body and 'BREAKING' in self.body.splitlines()[0]:
                category = 'break'
                extra_categories = categories
                self.body = ('\n'.join(self.body.splitlines()[1:])).strip()
            else:
                category = categories[0]
                extra_categories = categories[1:]

            specific = specific[1:-1] if specific else None  # Remove surrounding brackets

            return category, extra_categories, specific, description
        else:
            return 'unformatted', [], None, self.first_line

    def __repr__(self):
        return '<{}: {} "{}">'.format(
                self.__class__.__name__,
                self.commit_hash[:7],
                self.date.strftime('%x %X'))

