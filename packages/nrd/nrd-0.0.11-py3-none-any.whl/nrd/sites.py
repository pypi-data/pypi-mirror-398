#!/usr/bin/env python

import subprocess
import json

output=subprocess.check_output(["herd","parked","--json"])
sites=json.loads(output)
secured_sites = [
    site for site in sites
    if site.get("secured") == " X"
]
