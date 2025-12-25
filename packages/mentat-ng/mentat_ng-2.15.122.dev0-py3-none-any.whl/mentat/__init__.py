#!/usr/bin/env python3
# -------------------------------------------------------------------------------
# This file is part of Mentat system (https://mentat.cesnet.cz/).
#
# Copyright (C) since 2011 CESNET, z.s.p.o (http://www.ces.net/)
# Use of this source is governed by the MIT license, see LICENSE file.
# -------------------------------------------------------------------------------


"""
*Mentat* is a distributed modular SIEM (Security Information and Event Management System)
designed to monitor networks of all sizes. Its architecture enables reception,
storage, analysis, processing and response to a great volume of security incidents
originating from various sources, such as honeypots, network probes, log analysers,
third party detection services, etc. The Mentat system has been developed as an
open-source project.
"""

from importlib.metadata import PackageNotFoundError, version

__author__ = "Jan Mach <jan.mach@cesnet.cz>"
__credits__ = "Pavel Kácha <pavel.kacha@cesnet.cz>, Andrea Kropáčová <andrea.kropacova@cesnet.cz>"

try:
    __version__ = version("mentat-ng")
except PackageNotFoundError:
    __version__ = "0.0.0"
