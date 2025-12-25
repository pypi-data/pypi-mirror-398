import os
import subprocess as sb
import platform
from .spec_err import *

def win_hide(file):
  if not file:
     mathy__BJS___NullfuncError()
  try:
    if not os.path.exists(file):
        mathy__BJS__FilenotcaughtError()
    else:
        sb.run(
            f'attrib +h "{file}"',
            capture_output=True,
            shell=True,
            encoding='utf-8',
            errors='ignore',
        )
  except Exception as err:
     raise err
def unix_hide(file):
        if not os.path.exists(file):
         mathy__BJS__FilenotcaughtError()
        else:
           sb.run(
            f'."{file}"',
            capture_output=True,
            shell=True,
            encoding='utf-8',
            errors='ignore',
        )