#!/usr/bin/env python3

# Standard libraries
from os import environ

# Modules libraries
from pexpect_executor import Executor

# Terminal
environ['PROMPT_TOOLKIT_NO_CPR'] = '1'

# Configure, pylint: disable=line-too-long
Executor.configure(
    host='preview',
    tool='pre-commit-crocodile',
)

# Show helper
Executor('pre-commit-crocodile --help',
         delay_init=0.1, delay_prompt=1.0).\
    wait(1).\
    finish()

# Install hooks
Executor('pre-commit-crocodile --install',
         delay_init=0.1, delay_prompt=1.0).\
    wait(1).\
    finish()

# Configure hooks
Executor('pre-commit-crocodile --configure',
         delay_init=0.1, delay_prompt=1.0).\
    wait(1).\
    finish()

# Enable hooks
Executor('pre-commit-crocodile --enable',
         delay_init=0.1, delay_prompt=1.0).\
    wait(1).\
    finish()

# Run hooks
Executor('pre-commit-crocodile --run',
         delay_init=0.1, delay_prompt=1.0).\
    wait(1).\
    finish()

# Clear terminal
Executor('clear',
         delay_init=0.1, delay_prompt=2.0).\
    finish()

# Add hooks changes
Executor('git add -v ./.cz.yaml ./.pre-commit-config.yaml',
         delay_init=0.1, delay_prompt=1.0).\
    wait(1).\
    finish()

# Commit hooks changes
Executor('git commit -m "chore(pre-commit): import \'pre-commit-crocodile\' configurations" -s',
         delay_init=0.1, delay_prompt=1.0).\
    wait(1).\
    finish()

# Clear terminal
Executor('clear',
         delay_init=0.1, delay_prompt=2.0).\
    finish()

# Add first changes
Executor('git add -p ./docs/',
         delay_init=0.1, delay_press=0.2, delay_prompt=1.0).\
    read().\
    press('y').\
    read().\
    press(Executor.KEY_ENTER).\
    read().\
    wait(1).\
    finish()

# Commit with commitizen
Executor('cz commit',
         delay_init=0.1, delay_press=0.2, delay_prompt=1.0).\
    read().\
    press(Executor.KEY_DOWN).\
    press(Executor.KEY_DOWN).\
    press(Executor.KEY_DOWN).\
    read().\
    wait(1).\
    press(Executor.KEY_ENTER).\
    read().\
    press('tutorial').\
    read().\
    press(Executor.KEY_ENTER).\
    read().\
    press('improve tutorial documentation').\
    read().\
    press(Executor.KEY_ENTER).\
    read().\
    press(f'{Executor.KEY_BACKSPACE}{Executor.KEY_BACKSPACE}{Executor.KEY_BACKSPACE}').\
    read().\
    press('12345').\
    read().\
    press(Executor.KEY_ENTER).\
    read().\
    press(Executor.KEY_ENTER).\
    read().\
    press(Executor.KEY_ENTER).\
    read().\
    wait(1).\
    read().\
    read().\
    finish()

# Show commit
Executor('git show',
         delay_init=0.1, delay_prompt=1.0).\
    wait(1).\
    finish()

# Clear terminal
Executor('clear',
         delay_init=0.1, delay_prompt=2.0).\
    finish()

# Add second changes
Executor('git add -p ./src/',
         delay_init=0.1, delay_press=0.2, delay_prompt=1.0).\
    read().\
    press('y').\
    read().\
    press(Executor.KEY_ENTER).\
    read().\
    press('y').\
    read().\
    press(Executor.KEY_ENTER).\
    read().\
    wait(1).\
    finish()

# Commit with git commit
Executor('git commit -s',
         delay_init=0.1, delay_press=0.2, delay_prompt=1.0).\
    read().\
    press(f'{Executor.KEY_DELETE}{Executor.KEY_DELETE}{Executor.KEY_DELETE}').\
    read().\
    press('feat').\
    read().\
    press(Executor.KEY_END).\
    read().\
    press('implement new sources feature').\
    read().\
    press(Executor.KEY_DOWN).\
    press(Executor.KEY_DOWN).\
    read().\
    press(Executor.KEY_END).\
    read().\
    press(f'{Executor.KEY_BACKSPACE}{Executor.KEY_BACKSPACE}{Executor.KEY_BACKSPACE}').\
    read().\
    press('12345').\
    read().\
    press(Executor.KEY_HOME).\
    read().\
    press(f'{Executor.KEY_DELETE}{Executor.KEY_DELETE}').\
    read().\
    press(Executor.KEY_DOWN).\
    read().\
    press(f'{Executor.KEY_DELETE}{Executor.KEY_DELETE}').\
    read().\
    press(Executor.KEY_CTRL_O).\
    read().\
    press(Executor.KEY_ENTER).\
    read().\
    press(Executor.KEY_CTRL_X).\
    read().\
    press(Executor.KEY_ENTER).\
    read().\
    wait(1).\
    read().\
    read().\
    finish()

# Show commit
Executor('git show',
         delay_init=0.1, delay_prompt=1.0).\
    wait(1).\
    finish()

# Prompt
Executor(delay_prompt=3.0, hold_prompt=True)
