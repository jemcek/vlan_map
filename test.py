#!/usr/bin/python

import command
import definitions

definitions.set_community('Abi6br0TH3r')

(dictionary, native_tagged) = command.get_vlans_info(["sd-ssgtr-ms"], "allinfo-dict", None, None)

from pprint import pprint
pprint(dictionary)


