"""
Possible NUT Commands as specified in
https://networkupstools.org/docs/developer-guide.chunked/net-protocol.html
"""

import re

from enum import Enum


class NutCommand(Enum):
    GetNumlogins = "GET NUMLOGINS"
    GetUpsdesc = "GET UPSDESC"
    GetVar = "GET VAR"
    GetType = "GET TYPE"
    GetDesc = "GET DESC"
    GetCmddesc = "GET CMDDESC"
    GetTracking = "GET TRACKING"
    ListUps = "LIST UPS"
    ListVar = "LIST VAR"
    ListRw = "LIST RW"
    ListCmd = "LIST CMD"
    ListEnum = "LIST ENUM"
    ListRange = "LIST RANGE"
    ListClient = "LIST CLIENT"
    SetVar = "SET VAR"
    SetTracking = "SET TRACKING"
    Instcmd = "INSTCMD"
    Logout = "LOGOUT"
    Login = "LOGIN"
    Primary = "PRIMARY"
    Fsd = "FSD"
    Password = "PASSWORD"
    Username = "USERNAME"
    StartTls = "STARTTLS"
    Help = "HELP"
    Version = "VER"
    NetVersion = "NETVER"


NUT_COMMANDS_RE = re.compile(
    r"^(?P<cw>GET\sTRACKING|LIST\sUPS|LOGOUT|STARTTLS|HELP|VER|NETVER)|(?P<ca>GET\sNUMLOGINS|GET\sUPSDESC|GET\sVAR|GET\sTYPE|GET\sDESC|GET\sCMDDESC|LIST\sVAR|LIST\sRW|LIST\sCMD|LIST\sENUM|LIST\sRANGE|LIST\sCLIENT|SET\sVAR|SET\sTRACKING|INSTCMD|LOGIN|PRIMARY|FSD|PASSWORD|USERNAME)\s(?P<a>[A-Za-z0-9]+)$",
)
"""
Groups:\n
cw - cmd without args\n
ca - cmd with args\n
a - cmd args
"""
