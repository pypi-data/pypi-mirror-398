import cachetools as ct
import functools as ft
import json
import logging
import operator
import re
import requests
import sys
import weblogin
import weblogin.kth

from rich import print
import typer
import typing
import kthutils.credentials

def get_name_desc(group):
  """
  Returns a tuple (name, desc) containing the name and description, if it 
  exists, for the group `group`. If the group doesn't have a description, the 
  second value is None.
  """
  name = group["name"]

  try:
    desc = group["description"]["en"]
  except KeyError:
    desc = None

  return name, desc

class UGsession:
  """
  Maintains a session to the UG Editor APIs.
  """
  BASE_URL = "https://app.kth.se/ug-gruppeditor/"

  def __init__(self, username, password):
    """
    Requires `username` and `password` which are the normal credentials for 
    logging in through https://login.ug.kth.se.

    All API requests are performed as this user.
    """
    self.__session = weblogin.AutologinSession([
          weblogin.kth.UGlogin(username, password,
                               self.BASE_URL)
      ])
    self.cache = {}

  @ct.cachedmethod(operator.attrgetter("cache"),
    key=ft.partial(ct.keys.hashkey, "list_editable_groups"))
  def list_editable_groups(self):
    """
    Lists all groups that are editable by the logged in user.
    Returns list of JSON objects (from `list_editable_groups()`).
    """
    response = self.__session.get(
        f"{self.BASE_URL}/api/ug/groups?editableBySelf=true")
    return response.json()
  def find_group_by_name(self, name_regex):
    """
    Searches for a group from `list_editable_groups()` whose name matches the regex 
    `name_regex`.
    Returns a list of matching groups.
    """
    return filter(lambda group: re.search(name_regex, group["name"]),
                  self.list_editable_groups())
  def find_user_by_username(self, username):
    """
    Finds a user by username.
    Returns a list of matching user objects.
    """
    response = self.__session.get(f"{self.BASE_URL}/api/ug/users"
      f"?$filter=username eq '{username}' or emailAliases eq '{username}'")
    return response.json()
  def group_name_to_kthid(self, name):
    """
    Takes `name` (e.g. edu.courses.DD.DD1317.20222.1.courseresponsible) and
    returns KTH ID (e.g. u25w6fyq).

    Raises KeyError if no group named `name` is found.
    """
    for group in self.list_editable_groups():
      if group["name"] == name:
        return group["kthid"]
    
    raise KeyError(f"{name} could not be found.")
  def usernames_to_kthids(self, usernames):
    """
    Takes a list of usernames,
    returns a list of KTH IDs for the users.
    """
    kthids = []

    for username in usernames:
      try:
        user = self.find_user_by_username(username)[0]
      except IndexError as err:
        err = ValueError(f"Can't find user {username}")
        err.username = username
        raise err
      else:
        kthids.append(user["kthid"])

    return kthids
  def list_group_members(self, group_kthid):
    """
    Returns a list of the members of a group.
    The list contains JSON objects.
    """
    response = self.__session.get(
      f"{self.BASE_URL}/api/ug/users?$filter=memberOf eq '{group_kthid}'")
    return response.json()
  def set_group_members(self, members, group_kthid):
    """
    Sets the group members of group identified by `group_kthid` to be the list of 
    users (strings of kthid for users) `members`.

    Returns the updated group data, JSON format.
    """
    headers = self.__session.headers
    headers["content-type"] = "application/merge-patch+json"
    data = {
      "kthid": group_kthid,
      "members": members if isinstance(members, list) \
                         else list(members)
    }

    response = self.__session.patch(
      f"{self.BASE_URL}/api/ug/groups/{group_kthid}",
      data=json.dumps(data), headers=headers)

    if response.status_code != requests.codes.ok:
      raise Exception(f"failed to set members: {response.status_code}: "
                      f"{response.text}")

    return response.json()
  def add_group_members(self, new_members, group_kthid):
    """
    Adds list of members in `new_members` (kthids of users) to group with kthid 
    `group_kthid`.

    Returns the updated group data, JSON format.
    """
    current_members = [x["kthid"] for x in self.list_group_members(group_kthid)]
    return self.set_group_members(
              set(current_members + new_members),
              group_kthid)
  def remove_group_members(self, members, group_kthid):
    """
    Removes the users in `members` (list of kthids) from the group identified by 
    kthid `group_kthid`.

    Returns the updated group data, JSON format.
    """
    current_members = [x["kthid"] for x in self.list_group_members(group_kthid)]
    return self.set_group_members(
              set(current_members) - set(members),
              group_kthid)

cli = typer.Typer(name="ug", help="Interacts with the KTH UG Editor")

@cli.command(name="ls")
def cli_list_groups():
  """
  Lists all groups that are editable by the logged in user.
  Returns list of JSON objects (from `list_editable_groups()`).
  """
  ug = UGsession(*kthutils.credentials.get_credentials())
  for group in ug.list_editable_groups():
    name, desc = get_name_desc(group)
    print(f"{name}\t{desc}")
def complete_group(incomplete: str) -> [str]:
  """
  Returns list of strings (group names) that can complete `incomplete`.
  """
  ug = UGsession(*kthutils.credentials.get_credentials())
  names = []

  for group in ug.find_group_by_name(incomplete):
    names.append(get_name_desc(group))

  return names

@cli.command(name="group")
def cli_group(name_regex: str = typer.Argument(...,
                                               help="Regex for group name",
                                               autocompletion=complete_group)):
  """
  Searches for a group from `list_editable_groups()` whose name matches the regex 
  `name_regex`.
  Returns a list of matching groups.
  """
  ug = UGsession(*kthutils.credentials.get_credentials())
  print(list(ug.find_group_by_name(name_regex)))
@cli.command(name="user")
def cli_user(username: str):
  """
  Prints info about user with username `username`.
  """
  ug = UGsession(*kthutils.credentials.get_credentials())

  try:
    user_data = ug.find_user_by_username(username)[0]
  except IndexError as err:
    logging.error(f"Can't find user {username}.")
    sys.exit(1)

  del user_data["memberOf"]
  print(user_data)
members = typer.Typer(name="members",
                      help="Operations on the members of a group")
cli.add_typer(members)

group_regex_arg = typer.Argument(..., help="Regex for the group's name",
                                autocompletion=complete_group)
user_list_arg = typer.Argument(..., help="List of usernames")
@members.command(name="ls")
def cli_list_members(group_regex: str = group_regex_arg):
  """
  Returns a list of the members of a group.
  The list contains JSON objects.
  """
  ug = UGsession(*kthutils.credentials.get_credentials())
  groups = ug.find_group_by_name(group_regex)
  group_kthids = []
  for group in groups:
    group_name = group["name"]
    group_kthid = ug.group_name_to_kthid(group_name)
    group_kthids.append(group_kthid)
  for group_kthid in group_kthids:
    for member in ug.list_group_members(group_kthid):
      try:
        title = member['title']['en'][0]
      except IndexError:
        title = None
      print(f"{member['username']}"
            f"\t{member['kthid']}"
            f"\t{member['givenName']}"
            f"\t{member['surname']}"
            f"\t{title}")
@members.command(name="set")
def cli_set_members(group_regex: str = group_regex_arg,
                    users: typing.List[str] = user_list_arg):
  """
  Sets the members of a group. Any existing members not in the list will be 
  removed.
  """
  ug = UGsession(*kthutils.credentials.get_credentials())
  groups = ug.find_group_by_name(group_regex)
  group_kthids = []
  for group in groups:
    group_name = group["name"]
    group_kthid = ug.group_name_to_kthid(group_name)
    group_kthids.append(group_kthid)
  for group_kthid in group_kthids:
    try:
      ug.set_group_members(ug.usernames_to_kthids(users), group_kthid)
    except ValueError as err:
      logging.error(f"Couldn't set users for {group_kthid}: {err}")
@members.command(name="add")
def cli_add_members(group_regex: str = group_regex_arg,
                    users: typing.List[str] = user_list_arg):
  """
  Adds the members of a group. Any existing members will remain. Any members 
  already a member, will remain a member.
  """
  ug = UGsession(*kthutils.credentials.get_credentials())
  groups = ug.find_group_by_name(group_regex)
  group_kthids = []
  for group in groups:
    group_name = group["name"]
    group_kthid = ug.group_name_to_kthid(group_name)
    group_kthids.append(group_kthid)
  for group_kthid in group_kthids:
    try:
      ug.add_group_members(ug.usernames_to_kthids(users), group_kthid)
    except ValueError as err:
      logging.error(f"Couldn't add users for {group_kthid}: {err}")
@members.command(name="rm")
def cli_remove_members(group_regex: str = group_regex_arg,
                       users: typing.List[str] = user_list_arg):
  """
  Remove the members of a group. Any existing members not named will remain.
  """
  ug = UGsession(*kthutils.credentials.get_credentials())
  groups = ug.find_group_by_name(group_regex)
  group_kthids = []
  for group in groups:
    group_name = group["name"]
    group_kthid = ug.group_name_to_kthid(group_name)
    group_kthids.append(group_kthid)
  for group_kthid in group_kthids:
    try:
      ug.remove_group_members(ug.usernames_to_kthids(users), group_kthid)
    except ValueError as err:
      logging.error(f"Couldn't remove users from {group_kthid}: {err}")

if __name__ == "__main__":
  cli()
