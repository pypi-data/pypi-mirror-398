#!/usr/bin/env python3
# -------------------------------------------------------------------------------
# This file is part of Mentat system (https://mentat.cesnet.cz/).
#
# Copyright (C) since 2011 CESNET, z.s.p.o (http://www.ces.net/)
# Use of this source is governed by the MIT license, see LICENSE file.
# -------------------------------------------------------------------------------


"""
This module contains utilities for obtaining Mentat configuration parameters.
"""

import os
from datetime import timedelta
from functools import cache
from typing import Optional

import pyzenkit.jsonconf
import pyzenkit.utils

import mentat.const


@cache
def get_cleanup_threshold() -> Optional[timedelta]:
    """
    Extract the smallest event cleanup threshold from cleanup module configuration.
    If module not present, return None
    """
    try:
        from mentat.module.cleanup import (  # pylint: disable=locally-disabled,import-outside-toplevel
            THRESHOLDS,
            MentatCleanupScript,
        )

        cleanup_cfg = pyzenkit.jsonconf.json_load(
            pyzenkit.utils.get_resource_path(os.path.join(mentat.const.PATH_CFG, "mentat-cleanup.py.conf"))
        )
    except (ImportError, FileNotFoundError):
        return None

    cfg_key = MentatCleanupScript.CONFIG_EVENTS

    return min(THRESHOLDS[rule["threshold_type"]]["d"] for rule in cleanup_cfg[cfg_key])
