# Copyright 2025 Google LLC
#
#  Licensed under the Apache License, Version 2.0 (the "License");
#  you may not use this file except in compliance with the License.
#  You may obtain a copy of the License at
#
#      https://www.apache.org/licenses/LICENSE-2.0
#
#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS,
#  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#  See the License for the specific language governing permissions and
#  limitations under the License.

"""A class for non-blocking keyboard input capture."""

import atexit
import os
import select
import sys
import termios


class KeyboardInput:
  """A class for non-blocking keyboard input capture."""

  def __init__(self):
    if os.name == "nt":
      raise NotImplementedError("Not supporting Windows system right now.")
    else:
      # Save the terminal settings
      self._fd = sys.stdin.fileno()
      self._old_terminal = termios.tcgetattr(self._fd)
      self._new_terminal = termios.tcgetattr(self._fd)

      # New terminal setting unbuffered
      self._new_terminal[3] = (
          self._new_terminal[3] & ~termios.ICANON & ~termios.ECHO)
      termios.tcsetattr(self._fd, termios.TCSAFLUSH, self._new_terminal)

      # Support normal-terminal reset at exit
      atexit.register(self.set_normal_term)

  def set_normal_term(self):
    """Resets to normal terminal."""
    termios.tcsetattr(self._fd, termios.TCSAFLUSH, self._old_terminal)

  def get_input_character(self):
    """Returns a keyboard character after is_keyboard_hit() has been called."""
    return sys.stdin.read(1)

  def is_keyboard_hit(self):
    """Returns True if a key was hit, False otherwise."""
    stdin_ready, _, _ = select.select([sys.stdin], [], [], 0)
    if stdin_ready:
      return True
    else:
      return False
