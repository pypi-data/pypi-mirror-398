#!/usr/bin/env python3
# -------------------------------------------------------------------------------
# This file is part of Mentat system (https://mentat.cesnet.cz/).
#
# Copyright (C) since 2011 CESNET, z.s.p.o (http://www.ces.net/)
# Use of this source is governed by the MIT license, see LICENSE file.
# -------------------------------------------------------------------------------

"""
Unit test module for testing the :py:mod:`mentat.system` module.
"""

__author__ = "Jan Mach <jan.mach@cesnet.cz>"
__credits__ = "Pavel Kácha <pavel.kacha@cesnet.cz>, Andrea Kropáčová <andrea.kropacova@cesnet.cz>"


import unittest
from pprint import pprint
from unittest.mock import MagicMock, patch

import mentat.system

# -------------------------------------------------------------------------------
# NOTE: Sorry for the long lines in this file. They are deliberate, because the
# assertion permutations are (IMHO) more readable this way.
# -------------------------------------------------------------------------------


class TestMentatStorage(unittest.TestCase):
    """
    Unit test class for testing the :py:mod:`mentat.system` module.
    """

    #
    # Turn on more verbose output, which includes print-out of constructed
    # objects. This will really clutter your console, usable only for test
    # debugging.
    #
    verbose = False

    def test_01_analyze_process_ps(self):
        """
        Basic tests of single process analysis.
        """
        self.maxDiff = None

        tests = [
            (
                "4861 python3         python3 /usr/local/bin/mentat-storage.py",
                {
                    "args": None,
                    "exec": "mentat-storage.py",
                    "name": "mentat-storage.py",
                    "paralel": False,
                    "pid": 4861,
                    "process": "python3",
                    "psline": "4861 python3         python3 /usr/local/bin/mentat-storage.py",
                },
            ),
            (
                "4868 python3         python3 /usr/local/bin/mentat-enricher.py --paralel --count 3",
                {
                    "args": "--paralel --count 3",
                    "exec": "mentat-enricher.py",
                    "name": "mentat-enricher.py",
                    "paralel": True,
                    "pid": 4868,
                    "process": "python3",
                    "psline": "4868 python3         python3 /usr/local/bin/mentat-enricher.py --paralel --count 3",
                },
            ),
        ]

        for psline, expected in tests:
            self.assertEqual(mentat.system.analyze_process_ps(psline), expected)

    def test_02_analyze_process_list_ps(self):
        """
        Test process list analysis.
        """
        self.maxDiff = None

        # PIDs we want to analyze
        pids = [4861, 4868]

        fake_ps_lines = [
            b"PID COMMAND ARGS\n",
            b"4861 python3         python3 /usr/local/bin/mentat-storage.py\n",
            b"4868 python3         python3 /usr/local/bin/mentat-enricher.py\n",
            # Extra processes that should be ignored:
            b"9999 vim             vim /usr/local/bin/mentat-inspector.py\n",
            b"1234 bash            bash -c something\n",
        ]

        mock_popen = MagicMock()
        mock_popen.__enter__.return_value = mock_popen
        mock_popen.stdout = fake_ps_lines

        with patch("subprocess.Popen", return_value=mock_popen):
            result = mentat.system.analyze_process_list_ps(pids)

        self.assertIn("mentat-storage.py", result)
        self.assertIn(4861, result["mentat-storage.py"])
        self.assertIn("mentat-enricher.py", result)
        self.assertIn(4868, result["mentat-enricher.py"])

        # Should not include inspector or others
        self.assertNotIn("mentat-inspector.py", result)
        self.assertEqual(len(result), 2)  # exactly storage + enricher

    def test_03_analyze_pid_file(self):
        """
        Perform basic tests of single PID file analysis.
        """
        self.maxDiff = None

        if self.verbose:
            print("Single PID file:")
            pprint(mentat.system.analyze_pid_file("mentat-storage.py.pid", "/var/mentat/run/mentat-storage.py.pid"))

    def test_04_analyze_pid_files(self):
        """
        Perform basic tests of PID files analysis.
        """
        self.maxDiff = None

        if self.verbose:
            print("All PID files:")
            pprint(mentat.system.analyze_pid_files("/var/mentat/run"))

    def test_05_analyze_cron_file(self):
        """
        Perform basic tests of single cron file analysis.
        """
        self.maxDiff = None

        if self.verbose:
            print("Single cron file:")
            pprint(
                mentat.system.analyze_cron_file(
                    "mentat-statistician-py.cron",
                    "/etc/mentat/cron/mentat-statistician-py.cron",
                    {},
                )
            )

    def test_06_analyze_cron_files(self):
        """
        Perform basic tests of cron files analysis.
        """
        self.maxDiff = None

        if self.verbose:
            print("All cron files:")
            pprint(mentat.system.analyze_cron_files("/etc/mentat/cron", "/etc/cron.d"))

    def test_07_analyze_log_file(self):
        """
        Perform basic tests of single log file analysis.
        """
        self.maxDiff = None

        if self.verbose:
            print("Single log file:")
            pprint(mentat.system.analyze_log_file("mentat-storage.py.log", "/var/mentat/log/mentat-storage.py.log"))

    def test_08_analyze_log_files(self):
        """
        Perform basic tests of log files analysis.
        """
        self.maxDiff = None

        if self.verbose:
            print("All log files:")
            pprint(mentat.system.analyze_log_files("/var/mentat/log"))

    def test_11_module_status(self):
        """
        Perform the basic Mentat system tests.
        """
        self.maxDiff = None

        modules = mentat.system.make_module_list(
            [
                {"exec": "mentat-storage.py", "args": []},
                {"exec": "mentat-enricher.py", "args": []},
                {"exec": "mentat-inspector.py", "args": []},
            ]
        )
        cronjobs = mentat.system.make_cronjob_list(
            [
                {"name": "geoipupdate"},
                {"name": "mentat-cleanup-py"},
                {"name": "mentat-precache-py"},
                {"name": "mentat-statistician-py"},
            ]
        )

        if self.verbose:
            print("System status:")
            pprint(
                mentat.system.system_status(
                    modules,
                    cronjobs,
                    "/etc/mentat",
                    "/etc/cron.d",
                    "/var/mentat/log",
                    "/var/mentat/run",
                )
            )

        # self.assertTrue(
        #    mentat.system.system_status(
        #        modules,
        #        cronjobs,
        #        '/etc/mentat',
        #        '/etc/cron.d',
        #        '/var/mentat/log',
        #        '/var/mentat/run'
        #    )
        # )


# -------------------------------------------------------------------------------


if __name__ == "__main__":
    unittest.main()
