#!/usr/bin/env python
"""Convenience functions and code used by ee/__init__.py.

These functions are in general re-exported from the "ee" module and should be
referenced from there (e.g. "ee.profilePrinting").
"""

# Using lowercase function naming to match the JavaScript names.
# pylint: disable=g-bad-name

# pylint: disable=g-bad-import-order
import contextlib
import json
import six
import sys

import oauth2client.client

from . import data
from . import oauth

from .apifunction import ApiFunction
from .ee_exception import EEException


def _GetPersistentCredentials():
  """Read persistent credentials from ~/.config/earthengine.

  Raises EEException with helpful explanation if credentials don't exist.

  Returns:
    OAuth2Credentials built from persistently stored refresh_token
  """
  try:
    tokens = json.load(open(oauth.get_credentials_path()))
    refresh_token = tokens['refresh_token']
    return oauth2client.client.OAuth2Credentials(
        None, oauth.CLIENT_ID, oauth.CLIENT_SECRET, refresh_token,
        None, 'https://accounts.google.com/o/oauth2/token', None)
  except IOError:
    raise EEException('Please authorize access to your Earth Engine account '
                      'by running\n\nearthengine authenticate\n\nin your '
                      'command line, and then retry.')


def ServiceAccountCredentials(email, key_file=None, key_data=None):
  """Configure OAuth2 credentials for a Google Service Account.

  Args:
    email: The email address of the account for which to configure credentials.
    key_file: The path to a file containing the private key associated with
        the service account.
    key_data: Raw key data to use, if key_file is not specified.

  Returns:
    An OAuth2 credentials object.
  """
  if key_file:
    key_data = open(key_file, 'rb').read()
  return oauth2client.client.SignedJwtAssertionCredentials(
      email, key_data, oauth.SCOPE)


def call(func, *args, **kwargs):
  """Invoke the given algorithm with the specified args.

  Args:
    func: The function to call. Either an ee.Function object or the name of
        an API function.
    *args: The positional arguments to pass to the function.
    **kwargs: The named arguments to pass to the function.

  Returns:
    A ComputedObject representing the called function. If the signature
    specifies a recognized return type, the returned value will be cast
    to that type.
  """
  if isinstance(func, six.string_types):
    func = ApiFunction.lookup(func)
  return func.call(*args, **kwargs)


def apply(func, named_args):  # pylint: disable=redefined-builtin
  """Call a function with a dictionary of named arguments.

  Args:
    func: The function to call. Either an ee.Function object or the name of
        an API function.
    named_args: A dictionary of arguments to the function.

  Returns:
    A ComputedObject representing the called function. If the signature
    specifies a recognized return type, the returned value will be cast
    to that type.
  """
  if isinstance(func, six.string_types):
    func = ApiFunction.lookup(func)
  return func.apply(named_args)


@contextlib.contextmanager
def profilePrinting(destination=sys.stderr):
  # pylint: disable=g-doc-return-or-yield
  """Returns a context manager that prints a profile of enclosed API calls.

  The profile will be printed when the context ends, whether or not any error
  occurred within the context.

  # Simple example:
  with ee.profilePrinting():
     print ee.Number(1).add(1).getInfo()

  Args:
    destination: A file-like object to which the profile text is written.
        Defaults to sys.stderr.

  """
  # TODO(user): Figure out why ee.Profile.getProfiles isn't generated and fix
  # that.
  getProfiles = ApiFunction.lookup('Profile.getProfiles')

  profile_ids = []
  try:
    with data.profiling(profile_ids.append):
      yield
  finally:
    profile_text = getProfiles.call(ids=profile_ids).getInfo()
    destination.write(profile_text)
