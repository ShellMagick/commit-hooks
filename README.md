# ShellMagick / commit-hooks

Commit hooks based on experience, needs in teams I have worked, and acquired taste.

This repository uses the [pre-commit](https://pre-commit.com/) framework
and is heavily influenced by their [out-of-the-box hooks](https://github.com/pre-commit/pre-commit-hooks/).

Notably, hooks in this repository do not support Python 3.8, only 3.9 and above.
This is, because [`str.removeprefix`](https://docs.python.org/3.9/library/stdtypes.html#str.removeprefix) is used,
which has been introduced with Python 3.9.

## Listing of hooks

* [`commiticketing`](#commiticketing)
* [`lint-commit-message`](#lint-commit-message)
* [`no-boms`](#no-boms)
* [`no-todos`](#no-todos)

## Using ShellMagick / commit-hooks with pre-commit

Add this to your `.pre-commit-config.yaml`:

```yaml
-   repo: https://github.com/ShellMagick/commit-hooks
    rev: v24.03  # Use the ref you want to point at
    hooks:
    -   id: no-todos
    # -   id: ...
```

### Suggested initial configuration for generic projects

In case you are working on a non-Python project (e.g., Java), you may find the following config useful:

```yaml
default_install_hook_types: [ commit-msg, pre-commit, prepare-commit-msg ]
default_stages: [ pre-commit ]
repos:
-   repo: https://github.com/ShellMagick/commit-hooks
    rev: v24.03
    hooks:
    -   id: commiticketing
        stages: [ prepare-commit-msg ]
    -   id: no-boms
    -   id: no-todos
    -   id: lint-commit-message
        stages: [ commit-msg ]
-   repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v4.5.0
    hooks:
    -   id: check-added-large-files
        args: [ --maxkb=128 ]
    -   id: check-case-conflict
    -   id: check-json
    -   id: check-merge-conflict
        args: [ --assume-in-merge ]
    -   id: check-toml
    -   id: check-xml
    -   id: check-yaml
    -   id: detect-private-key
    -   id: end-of-file-fixer
    -   id: forbid-submodules
    -   id: mixed-line-ending
    -   id: no-commit-to-branch
        args: [ --branch=develop, --branch=release, --branch=master ]
    -   id: pretty-format-json
    -   id: trailing-whitespace
```

## Available hooks

### `commiticketing`

Many projects working with Git have a pre-defined workflow; let it be
[Git-Flow](https://nvie.com/posts/a-successful-git-branching-model/),
[GitHub-Flow](https://docs.github.com/de/get-started/using-github/github-flow),
a derivation of them, or any other kind of flow.

What also is paramount that you have some kind of ticketing systems, and you want to correlate your work (i.e., commits)
to a ticket—exactly one ticket; it is usually considered an anti-pattern to work on multiple tickets simultaneously or
have commits, which do not correlate to any tickets.

In case you want to tie your commits to your tickets tightly, one
of the easiest things you could do is prefixing your tickets with a corresponding ticketing reference
(e.g., `ISSUE-42: Add new gizmo`).

This hook is aimed to help in this correlation work and remove the tedious chore of typing the prefix manually at each
commit. It works by parsing the current branch name and extracting the ticketing information from it with additional,
optional context. I.e.,

* commits on `feature/ISSUE-42` and `feature/ISSUE-42-human-readable-description` will be prefixed with `ISSUE-42:␣`
  * commits on branches `bugfix/ISSUE-42`, `bugfix/ISSUE-42-desc`, `hotfix/ISSUE-42`, `hotfix/ISSUE-42-desc` will be
    handled the same and receive the prefix `ISSUE-42:␣` by default.
  * commits on `user/username/ISSUE-42`, `user/username/ISSUE-42-desc`, `backup/username/ISSUE-42`,
    and `backup/username/ISSUE-42` are handled the same and receive the prefix `ISSUE-42:␣` by default.

Note that the extraction happens from either the second or the third level of the branch name and the prefix is anything
before a(n optional) second dash in the branch name, as well as `:␣` (colon and whitespace). Additionally, it will make
the very first character of your commit message upper case.

Please note that even though `feature`, `bugfix`, and `hotfix` are hinting towards using Git-Flow, the generic idea is
not tied to Git-Flow at all and can be used by many other workflows.

#### Example

You are working on the ticket `Fix the ODN relay` in the project `DSN` and it has the ticket number `47`.
Thus, you check out the branch `bugfix/DSN-47-fix-odn`. You do a commit with the commit message `open hatch`, and this
hook will automatically adjust your commit message to `DSN-47: Open hatch`.

#### Arguments

This hook has four optional arguments, three of them being repeatable:

* `-b/--branch`: branch name prefixes to be processed by this hook and extracting ticketing information from the
  second level; this argument is repeatable
  * If none given, the following are implicitly processed: `feature`, `bugfix`, `hotfix`.
* `-t/--two-level`: branch name prefixes to be processed by this hook and extracting ticketing information from the
  third level; this argument is repeatable
  * If none given, the following are implicitly processed: `user`, `backup`.
* `-l/--long-prefix`: use long-prefixing, unless on the exclusion list
  * By default, this is turned off (i.e., long-prefixing is _not_ used by default)
  * Long prefixing means infixing the first level of the branch name into the commit message, examples:
    * For the branch named `bugfix/DSN-47` the short prefix `DNS-47:␣` becomes the long prefix `DNS-47:␣(bugfix)␣`
    * For the branch named `hotfix/DSN-47` the short prefix `DNS-47:␣` becomes the long prefix `DNS-47:␣(hotfix)␣`
    * For the branch named `backup/miles/DSN-47` the short prefix `DNS-47:␣` becomes the long prefix `DNS-47:␣(backup)␣`
* `-e/--exclude-long-prefix`: in case long-prefixing is turned on, exclude branches starting with any of these; this
  argument is repeatable
  * In case long-prefixing is not used (and thus by default), this argument does nothing
  * If none given, the following are implicitly excluded from long-prefixing: `feature`, `user`, `backup`

#### Side effects

This hook changes your commit message, in case it does not already conform the guidelines of this hook.

Please note that basic precautions are taken against doubly-prefixing, but mixing short/long-prefix configurations
may cause surprises.

### `lint-commit-message`

A basic linter for commit messages, based on [How to Write a Git Commit Message](https://cbea.ms/git-commit/) by
Chris Beams.

The linter checks the following (corresponding the rules from the linked article):

<ol start="0">
    <li>✅ There must be a commit message.</li>
    <li>✅ The subject line and the body are separated by an empty line.</li>
    <li>✅ The subject line is limited to 72 characters.
        <ul>
            <li>Note: This is more relaxed than the proposed 50 characters by the article.
                      The reasoning behind this is that together with <code>commiticketing</code>,
                      it is sometimes hard to adhere to the limit of 50.</li>
            <li>Note: The limit is adjustable, see the arguments of this hook.</li>
        </ul>
    </li>
    <li>❌ Is not checked (would be "Capitilize the subject line"). Use <code>commiticketing</code> instead.</li>
    <li>✅ The subject line does not end with non-word character (i.e., non-alphanumeric character).
        <ul>
           <li>Note: This is stricter than the proposed rule "do not end the subject line with a period" by the
                     article.</li>
        </ul>
    </li>
    <li>❌ Is not checked (would be "Use imperative mood in the subject line"), because it would need NLP.</li>
    <li>✅ The lines of the body are limited to 120 characters.
        <ul>
            <li>Note: This is more relaxed than the proposed 72 characters by the article.</li>
            <li>Note: The limit is adjustable, see the arguments of this hook.</li>
        </ul>
    </li>
    <li>❌ Is not checked (would be "Use the body to explain <i>what</i> and <i>why</i> vs. <i>how</i>"),
        because it would need advanced NLP.</li>
</ol>

#### Arguments

This hook has two optional arguments:

* `-sl/--subject-line-length:` adjust the parameter of rule 2 (default value: 72).
* `-bl/--body-line-length:` adjust the parameter of rule 6 (default value: 120).

#### Side effects

This hook does not change your commit message, just reports violations and prevents the commit.

### `no-boms`

Prevent commits containing any files with [UTF BOMs](https://www.unicode.org/faq/utf_bom.html#BOM) of any kind.

#### Arguments

This hook does not have any arguments.

#### Side effects

This hook does not change any files, just reports violations and prevents the commit.

### `no-todos`

Prevent commits containing (pre-)defined "comment tags".

#### Arguments

This hook has two optional, repeatable arguments:

* `-t/--todo-tag`: defines a "comment tag" as forbidden. In case any of these strings is matched anywhere in any file
  being committed, the commit is prevented.
  * By default, the following strings are considered as tags: `TODO`, `FIXME`, `XXX`.
* `-e/--except-in`: defines _filenames_, which are excluded from the check.
  * The same could be achieved by an `exclude` in the hooks configuration, but this argument is useful together with
    `verbose`, as in this case it will log the excluded files containing any of the "comment tags" (as a quasi-warning).

#### Side effects

This hook does not change any files, just reports violations and prevents the commit.
