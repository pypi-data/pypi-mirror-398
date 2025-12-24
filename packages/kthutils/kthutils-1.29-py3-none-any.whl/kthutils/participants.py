import json
import logging
import operator
import re
import sys

from rich import print
import typer
try:
  from typing import Annotated
except ImportError:
  from typing_extensions import Annotated

import kthutils.credentials
import weblogin
import weblogin.kth
import cachetools as ct
import functools as ft
import csv
course_code_arg = typer.Argument(help="The course code, something like DD1310")
semester_arg = typer.Argument(help="The semester, something like HT2023")
raw_opt = typer.Option(help="Print the raw JSON data and exit. "
                            "This ignores all other options.")
delimiter_opt = typer.Option(help="The delimiter to use for CSV output. "
                                  "Defaults to tab to be useful in the "
                                  "terminal.")
course_round_opt = typer.Option(help="Print the course round "
                                     "in the CSV output.")
ladok_round_opt = typer.Option(help="Print the Ladok course round UID "
                                    "in the CSV output.")
personnummer_opt = typer.Option(help="Print the personnummer "
                                     "in the CSV output.")
programme_opt = typer.Option(help="Print the programme code "
                                  "in the CSV output.")


class ParticipantsSession:
  """
  Maintains a session to the course participants API.
  """
  BASE_URL = "https://app.kth.se/studentlistor/kurstillfallen"

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
    key=ft.partial(ct.keys.hashkey, "get_all_data"))
  def get_all_data(self, course_code, semester):
    """
    Returns all the data from the search results.
    - `course_code` is something like "DD1310" and
    - `semester` is something like "HT2023" (for Autumn 2023).
    """
    data = {
      "courseCode": course_code,
      "term": semester
    }
    response = self.__session.get(f"{self.BASE_URL}"
                        f"/api/studentlistor/courseroundparticipants",
                      params=data)
    try:
      return response.json()
    except Exception as err:
      err.response = response
      raise err

cli = typer.Typer(name="participants",
                  help="Interacts with the KTH course participants lists")

@cli.command(name="ls")
def cli_ls(course_code: Annotated[str, course_code_arg],
           semester: Annotated[str, semester_arg],
           raw: Annotated[bool, raw_opt] = False,
           delimiter: Annotated[str, delimiter_opt] = "\t",
           course_round: Annotated[bool, course_round_opt] = True,
           ladok_round: Annotated[bool, ladok_round_opt] = False,
           personnummer: Annotated[bool, personnummer_opt] = False,
           programme: Annotated[bool, programme_opt] = True,):
  """
  Lists all students in the list of expected participants.
  The columns of the CSV output is the following:

  - The course round (optional)

  - The Ladok course round code (optional)

  - The personnummer (optional)

  - The full name (first name and last name, in that order, separated by space)

  - The email address

  - The programme code (optional)

  - The funka codes (comma separated, in one column)

  The funka codes are divided into two categories, R and P.

  R-stöd: Anpassningar som rör rum, tid och fysisk omständighet anses normalt 
  beviljade av examinator.

  - R0: 50% längre skrivtid vid skriftlig salsexamination

  - R1: 25% längre skrivtid vid skriftlig salsexamination

  - R2: Tentera i mindre grupp

  - R3: Tentera i mindre grupp med skärmar som avgränsar sittplatserna i SAL

  - R4: Tentera helt enskilt

  - R5: Examination i mindre grupp med skärmar som avgränsar sittplatserna i RUM

  - R6: Examination i tillgänglighetsanpassade lokaler

  - R7: Möjlighet till liggande vila under examinationstillfället

  - R8: Skriva på dator ALLTID

  - R9: Höj- och sänkbart bord

  - R10: Ljud avskärmning: Hörselkåpor

  - R13: Pauser under första timmen

  - R14: Kortare pauser under examinationstillfället

  - R15: Anpassad tentamenslydelse som examinator tillgodoser

  - R16: Anpassad tentamenslydelse som examinationsadministrationsgruppen 
    tillgodoser

  - R17: Tentamen utskriven i A3-format

  - R19: Delad tentamen

  - R20: Upplästa frågor ALLTID

  - R21: Utbildningstolkning

  - R22: Teknisk utrustning eller annan utrustning

  - R23: Medicinsk utrustning

  - R24: Medicinsk utrustning + 20 minuter förlängd skrivtid

  - R28: Skrivhjälp

  - R33: Personlig assistent med under examinationstillfället

  - R100: Övriga anpassningar som tillgodoses under examination med anmälan i 
    Ladok

  - RANTSTOD: Anteckningsstöd

  P-stöd: Pedagogiska anpassningar ska i vissa fall prövas av examinator i samråd 
  med berörd programansvarig alternativt grundutbildningsansvarig eller 
  studierektor och funkahandläggare.

  - P8: Skriva på dator vid behov

  - P18: Förlängd tid vid hemtentamen/uppgifter/rapporter/projekt

  - P20: Upplästa frågor vid behov

  - P29: Muntlig examination som komplettering till skriftlig examination

  - P30: Rörelsehjälpmedel till exempel rullstol

  - P31: Assistans- eller ledarhund

  - P32: Redovisa i mindre grupp

  - P100: Övriga anpassningar som tillgodoses vid examination utan en anmälan i 
    Ladok

  A more detailed coverage of the funka codes can be found at

  https://intra.kth.se/polopoly_fs/1.907952.1601461801!/Copy%20of%20Matris%20190522%20version10.pdf
  """
  ps = ParticipantsSession(*kthutils.credentials.get_credentials())
  data = ps.get_all_data(course_code, semester)
  if raw:
    print(json.dumps(data, indent=2))
    return
  csvout = csv.writer(sys.stdout, delimiter=delimiter)
  for participant in data["participants"]:
    columns = []
    if course_round:
      columns.append(participant["courseRound"])
    if ladok_round:
      columns.append(participant["courseRoundsCode"])
    if personnummer:
      columns.append(participant['personnumer'])
    columns.append(f"{participant['firstName']} {participant['lastName']}")
    columns.append(participant["email"])
    if programme:
      columns.append(participant["programCode"])
    columns.append(", ".join(participant["funkaCode"]))
    csvout.writerow(columns)

if __name__ == "__main__":
  cli()
