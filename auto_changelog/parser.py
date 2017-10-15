"""
The parser module will traverse a git repository, gathering all the commits
that follow the AngularJS commit message convention, and linking them with
the releases they correspond to.
"""

import git

from .models import Commit, Tag, Unreleased



def group_commits(tags, commits):
    tags = sorted(tags, key=lambda t: t.date)

    # Adding the tag's commit manually because those seem to be skipped
    commits.extend([Commit(t._commit) for t in tags])

    # Sort the commits -and filter out those not formatted correctly-
    commits = sorted(commits, key=lambda c: c.date)
    # commits = list(filter(lambda c: c.category, commits))
    
    for index, tag in enumerate(tags):
        # Everything is sorted in ascending order (earliest to most recent), 
        # So everything before the first tag belongs to that one
        if index == 0:
            children = filter(lambda c: c.date <= tag.date, commits)
        else:
            prev_tag = tags[index-1]
            children = filter(lambda c: prev_tag.date < c.date <= tag.date, commits)
            
        for child in children:
            commits.remove(child)
            tag.add_commit(child)
            
    left_overs = list(filter(lambda c: c.date > tags[-1].date, commits))
    return left_overs


def traverse(base_dir):
    repo = git.Repo(base_dir)
    tags = repo.tags

    if len(tags) < 1:
        raise ValueError('Not enough tags to generate changelog')

    wrapped_tags = []
    for tagref in tags:        
        t = Tag(
            name=tagref.name, 
            date=tagref.commit.committed_date, 
            commit=tagref.commit)
        wrapped_tags.append(t)
    wrapped_tags = sorted(wrapped_tags, key=lambda t: t.date)

    for i, tag in enumerate(wrapped_tags):
        if i == 0:
            rev = tag.version
        else:
            rev = '{}..{}'.format(wrapped_tags[i - 1].version, tag.version)

        for commit in repo.iter_commits(rev, first_parent=True):
            tag.add_commit(Commit(commit))  # Convert to Commit object and add to the tag by group

    # get commits since the last tag
    left_overs = list(map(
            Commit,
            repo.iter_commits('{}..master'.format(tag.version), first_parent=True)
    ))

    # If there are any left over commits (i.e. commits created since 
    # the last release
    if left_overs:
        unreleased = Unreleased(left_overs)
    else:
        unreleased = None

    return wrapped_tags, unreleased
