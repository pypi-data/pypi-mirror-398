#!/usr/bin/env python3
# -------------------------------------------------------------------------------
# This file is part of Mentat system (https://mentat.cesnet.cz/).
#
# Copyright (C) since 2011 CESNET, z.s.p.o (http://www.ces.net/)
# Use of this source is governed by the MIT license, see LICENSE file.
# -------------------------------------------------------------------------------


"""
This Mentat module is a script providing periodical event reports to target groups.

This script is implemented using the :py:mod:`pyzenkit.zenscript` framework and
so it provides all of its core features. See the documentation for more in-depth
details.

It is further based on :py:mod:`mentat.script.fetcher` module, which provides
database fetching and message post-processing capabilities.


Usage examples
--------------------------------------------------------------------------------

.. code-block:: shell

    # Display help message and exit.
    mentat-reporter.py --help

    # Run in debug mode (enable output of debugging information to terminal).
    mentat-reporter.py --debug

    # Run with insanely increased logging level.
    mentat-reporter.py --log-level debug

    # Run in TEST DATA mode and MAIL TEST mode, force all reports to go to
    # 'admin@domain.org'. In test data mode only events tagged with 'Test'
    # category will be processed (useful for debugging). In mail test mode
    # all generated reports will be redirected to configured admin email (root
    # by default) instead of original contact, which is again useful for
    # debugging or testing.
    mentat-reporter.py --mail-test-mode --test-data --mail-to admin@domain.org

    # Force reporter to use different email report template and localization.
    mentat-reporter.py --template-id another --locale cs


Available script commands
--------------------------------------------------------------------------------

``report`` (*default*)
    Generate report containing overall Mentat system performance statistics
    within configured time interval thresholds.


Brief overview of reporting algorithm
--------------------------------------------------------------------------------

Reporting algorithm follows these steps:

#. For all groups found in database:

    #. For all event severities (``info``, ``low``, ``medium``, ``high``, ``critical``):

        #. Fetch reporting configuration settings.
        #. Fetch events with given severity, that appeared in database in given
           time window and belonging to that particular group.
        #. Filter events with configured reporting filters.
        #. Remove events from detectors with low credibility.
        #. Threshold already reported events.
        #. Fetch relapsed events.
        #. Generate *target*, *summary* and/or *extra* reports and store them to database.
        #. Send reports via email to target abuse contacts.

"""

__author__ = "Jan Mach <jan.mach@cesnet.cz>"
__credits__ = "Pavel Kácha <pavel.kacha@cesnet.cz>, Andrea Kropáčová <andrea.kropacova@cesnet.cz>"

import contextlib
import datetime
import errno
import fcntl
import os
import time

import pyzenkit.utils

import mentat.const
import mentat.plugin.app.mailer
import mentat.reports.event
import mentat.reports.utils
import mentat.script.fetcher
from mentat.datatype.sqldb import GroupModel, ReporterStateModel
from mentat.reports.data import ReportingProperties


class SimpleFlock:  # pylint: disable=locally-disabled,too-few-public-methods
    """
    Provides the simplest possible interface to flock-based file locking. Intended
    for use with the `with` syntax. It will create/truncate/delete the lock file
    as necessary.

    Resource: https://github.com/derpston/python-simpleflock
    """

    def __init__(self, path, timeout=None):
        self._path = path
        self._timeout = timeout
        self._fd = None

    def __enter__(self):
        self._fd = os.open(self._path, os.O_CREAT)
        start_lock_search = time.time()
        while True:
            try:
                fcntl.flock(self._fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
                # Lock acquired!
                return
            except OSError as ex:
                if ex.errno != errno.EAGAIN:  # Resource temporarily unavailable
                    raise
                if self._timeout is not None and time.time() > (start_lock_search + self._timeout):
                    # Exceeded the user-specified timeout.
                    raise

            # It would be nice to avoid an arbitrary sleep here, but spinning
            # without a delay is also undesirable.
            time.sleep(0.1)

    def __exit__(self, *args):
        fcntl.flock(self._fd, fcntl.LOCK_UN)
        os.close(self._fd)
        self._fd = None

        # Try to remove the lock file, but don't try too hard because it is
        # unnecessary. This is mostly to help the user see whether a lock
        # exists by examining the filesystem.
        with contextlib.suppress(Exception):
            os.unlink(self._path)


class MentatReporterScript(mentat.script.fetcher.FetcherScript):
    """
    Implementation of Mentat module (script) providing periodical statistical
    overview for message processing performance analysis.
    """

    #
    # Class constants.
    #

    # List of configuration keys.
    CORECFG_REPORTER = "__core__reporter"
    CONFIG_REPORTS_DIR = "reports_dir"
    CONFIG_TEMPLATES_DIR = "templates_dir"
    CONFIG_TEMPLATE_VARS = "template_vars"
    CONFIG_DEFAULT_LOCALE = mentat.const.CKEY_CORE_REPORTER_DEFAULTLOCALE
    CONFIG_DEFAULT_TIMEZONE = mentat.const.CKEY_CORE_REPORTER_DEFAULTTIMEZONE
    CONFIG_FORCE_MODE = "force_mode"
    CONFIG_FORCE_TEMPLATE = "force_template"
    CONFIG_FORCE_LOCALE = "force_locale"
    CONFIG_FORCE_TIMEZONE = "force_timezone"
    CONFIG_TEST_DATA = "test_data"

    def __init__(self):
        """
        Initialize reporter script object. This method overrides the base
        implementation in :py:func:`mentat.script.fetcher.FetcherScript.__init__`
        and it aims to even more simplify the script object creation by providing
        configuration values for parent contructor.
        """
        # Declare private attributes.
        self.sqlservice = None
        self.mailerservice = None
        self.reporter = None

        super().__init__(
            description="mentat-reporter.py - Mentat system event reporting",
            #
            # Load additional application-level plugins.
            #
            plugins=[mentat.plugin.app.mailer.MailerPlugin()],
        )

    def _sub_stage_init(self, **kwargs):
        """
        **SUBCLASS HOOK**: Perform additional custom initialization actions.

        This method is called from the main constructor in :py:func:`pyzenkit.baseapp.BaseApp.__init__`
        as a part of the **__init__** stage of application`s life cycle.

        :param kwargs: Various additional parameters passed down from constructor.
        """
        # Override default 'interval' value.
        self.config[self.CONFIG_INTERVAL] = "10_minutes"

        # Override default 'adjust_thresholds' value.
        self.config[self.CONFIG_ADJUST_THRESHOLDS] = True

    def _init_argparser(self, **kwargs):
        """
        Initialize script command line argument parser. This method overrides the
        base implementation in :py:func:`pyzenkit.zenscript.ZenScript._init_argparser`
        and it must return valid :py:class:`argparse.ArgumentParser` object. It
        appends additional command line options custom for this script object.

        This method is called from the main constructor in :py:func:`pyzenkit.baseapp.BaseApp.__init__`
        as a part of the **__init__** stage of application`s life cycle.

        :param kwargs: Various additional parameters passed down from object constructor.
        :return: Valid argument parser object.
        :rtype: argparse.ArgumentParser
        """
        argparser = super()._init_argparser(**kwargs)

        #
        # Create and populate options group for custom script arguments.
        #
        arggroup_script = argparser.add_argument_group("custom script arguments")

        arggroup_script.add_argument(
            "--force-mode",
            type=str,
            default=None,
            help="force a reporting mode setting",
        )
        arggroup_script.add_argument(
            "--force-template",
            type=str,
            default=None,
            help="force a template for generating reports",
        )
        arggroup_script.add_argument(
            "--force-locale",
            type=str,
            default=None,
            help="force a locale for generating reports",
        )
        arggroup_script.add_argument(
            "--force-timezone",
            type=str,
            default=None,
            help="force a timezone for generating reports",
        )
        arggroup_script.add_argument(
            "--test-data",
            action="store_true",
            default=None,
            help="use test data for reporting (flag)",
        )

        return argparser

    def _init_config(self, cfgs, **kwargs):
        """
        Initialize default script configurations. This method overrides the base
        implementation in :py:func:`pyzenkit.zenscript.ZenScript._init_config`
        and it appends additional configurations via ``cfgs`` parameter.

        This method is called from the main constructor in :py:func:`pyzenkit.baseapp.BaseApp.__init__`
        as a part of the **__init__** stage of application`s life cycle.

        :param list cfgs: Additional set of configurations.
        :param kwargs: Various additional parameters passed down from constructor.
        :return: Default configuration structure.
        :rtype: dict
        """
        cfgs = (
            (self.CONFIG_FORCE_MODE, None),
            (self.CONFIG_FORCE_TEMPLATE, None),
            (self.CONFIG_FORCE_LOCALE, None),
            (self.CONFIG_FORCE_TIMEZONE, None),
            (self.CONFIG_TEST_DATA, False),
        ) + cfgs
        return super()._init_config(cfgs, **kwargs)

    def _sub_stage_evaluate(self, analysis):
        """
        **SUBCLASS HOOK**: Perform additional evaluation actions in **evaluate** stage.

        Gets called from :py:func:`~BaseApp._stage_evaluate` and it is a **EVALUATE SUBSTAGE 01**.
        """
        if analysis.get(self.RLANKEY_COMMAND) == "report":
            if analysis["report"]["groups"]:
                self.logger.info(
                    "List of groups with any reports: %s",
                    ", ".join(analysis["report"]["groups"]),
                )
            if analysis["report"]["summary_ids"]:
                self.logger.info(
                    "List of generated summary reports: %s",
                    ", ".join(analysis["report"]["summary_ids"]),
                )
            if analysis["report"]["extra_ids"]:
                self.logger.info(
                    "List of generated extra reports: %s",
                    ", ".join(analysis["report"]["extra_ids"]),
                )
            if analysis["report"]["target_ids"]:
                self.logger.info(
                    "List of generated target reports: %s",
                    ", ".join(analysis["report"]["target_ids"]),
                )
            if analysis["report"]["mails_to"]:
                self.logger.info(
                    "List of report destinations: %s",
                    ", ".join(analysis["report"]["mails_to"]),
                )

    # ---------------------------------------------------------------------------

    def get_default_command(self):
        """
        Return the name of the default script command. This command will be executed
        in case it is not explicitly selected either by command line option, or
        by configuration file directive.

        :return: Name of the default command.
        :rtype: str
        """
        return "report"

    def cbk_command_report(self):
        """
        Implementation of the **report** command (*default*).

        Calculate statistics for messages stored into database within configured
        time interval thresholds.
        """
        result = {"reports": {}}

        #
        # Use locking mechanism to ensure there is always only one reporter
        # instance running.
        #
        with SimpleFlock("/var/tmp/mentat-reporter.py", 5):
            groups_dict = {}
            settings_dict = {}
            for group in self._fetch_groups_enabled():
                groups_dict[group.name] = group
                settings_dict[group.name] = mentat.reports.utils.ReportingSettings(
                    group,
                    self.sqlservice,
                    force_mode=self.c(self.CONFIG_FORCE_MODE),
                    force_template=self.c(self.CONFIG_FORCE_TEMPLATE),
                    force_locale=self.c(self.CONFIG_FORCE_LOCALE),
                    force_timezone=self.c(self.CONFIG_FORCE_TIMEZONE),
                    default_locale=self.config[self.CORECFG_REPORTER][self.CONFIG_DEFAULT_LOCALE],
                    default_timezone=self.config[self.CORECFG_REPORTER][self.CONFIG_DEFAULT_TIMEZONE],
                )
            whoismodule = mentat.services.whois.SqldbWhoisModule()
            whoismodule.setup()

            # Instantinate the reporter object.
            reporter = mentat.reports.event.EventReporter(
                self.logger,
                pyzenkit.utils.get_resource_path_fr(self.config[self.CORECFG_REPORTER][self.CONFIG_REPORTS_DIR]),
                pyzenkit.utils.get_resource_path_fr(self.config[self.CORECFG_REPORTER][self.CONFIG_TEMPLATES_DIR]),
                self.config[mentat.const.CKEY_CORE_REPORTER][mentat.const.CKEY_CORE_REPORTER_FALLBACK],
                mentat.const.DFLT_REPORTING_LOCALE,
                mentat.const.DFLT_REPORTING_TIMEZONE,
                self.eventservice,
                self.sqlservice,
                self.mailerservice,
                groups_dict,
                settings_dict,
                whoismodule,
                self.c(self.CONFIG_REGULAR),
            )

            # Adjust time interval thresholds.
            time_h = self.calculate_upper_threshold(
                time_high=self.c(self.CONFIG_TIME_HIGH),
                interval=self.c(self.CONFIG_INTERVAL),
                adjust=self.c(self.CONFIG_REGULAR),
            )
            time_h = time_h.replace(microsecond=0)
            self.logger.info(
                "Upper event report calculation time interval threshold: %s (%s)",
                time_h.isoformat(),
                time_h.timestamp(),
            )
            if self.c(self.CONFIG_TEST_DATA):
                self.logger.info(
                    "Running in 'TESTDATA' mode: Reporting will be performed only for events tagged with 'Test' category."
                )

            # Perform reporting for each severity.
            for severity in mentat.const.EVENT_SEVERITIES:
                reporter_state = (
                    self.sqlservice.session.query(ReporterStateModel)
                    .filter(ReporterStateModel.severity == severity)
                    .one_or_none()
                )
                period = mentat.reports.utils.get_reporting_timings()[severity]["per"]

                # Determine the lower bound of the reporting window.
                if reporter_state is not None:
                    time_l = reporter_state.last_successful_run
                else:
                    time_l = time_h - period
                    reporter_state = ReporterStateModel(last_successful_run=time_l, severity=severity)

                if self.c(self.CONFIG_REGULAR) and (time_l + period) > time_h:
                    self.logger.debug(
                        "Skipping reporting for event severity '%s' and period '%s': At %s it is too soon, waiting until %s.",
                        severity,
                        period,
                        time_h.isoformat(),
                        (time_l + period).isoformat(),
                    )
                    result[severity] = {"result": "skipped-too-soon"}
                    continue

                # Perform reporting for all configured and enabled groups.
                for group in groups_dict.values():
                    reporting_properties = ReportingProperties(
                        group,
                        severity,
                        time_l,
                        time_h,
                        self.config[self.CORECFG_REPORTER][self.CONFIG_TEMPLATE_VARS],
                        self.c(self.CONFIG_TEST_DATA),
                    )
                    result["reports"][group.name] = self._report_for_group(reporter, reporting_properties)

                reporter_state.last_successful_run = time_h
                self.sqlservice.session.add(reporter_state)
                self.sqlservice.session.commit()

            # Cleanup thresholding cache after the reporting.
            result["cleanup"] = reporter.cleanup(time_h)

        return result

    # ---------------------------------------------------------------------------

    def _report_for_group(self, reporter, reporting_properties):
        """
        Perform event reporting for given group.

        :param mentat.reports.event.EventReporter reporter: Event reporter.
        :param mentat.reports.data.ReportingProperties reporting_properties: Properties of the current reporting.
        :return: Dictionary structure containing information about reporting result.
        :rtype: dict
        """
        result = {}

        # Proceed to actual reporting.
        result[reporting_properties.severity] = reporter.report(reporting_properties)

        # Evaluate reporting results.
        if result[reporting_properties.severity]["result"] == "reported":
            for report_type in ["summary", "target"]:
                if f"{report_type}_id" in result[reporting_properties.severity]:
                    self.logger.info(
                        "%s: Generated %s report '%s' with severity '%s' and time interval %s -> %s (%s).",
                        reporting_properties.group.name,
                        report_type,
                        result[reporting_properties.severity][f"{report_type}_id"],
                        reporting_properties.severity,
                        reporting_properties.lower_time_bound.isoformat(),
                        reporting_properties.upper_time_bound.isoformat(),
                        str(reporting_properties.upper_time_bound - reporting_properties.lower_time_bound),
                    )
        elif result[reporting_properties.severity]["result"] == "skipped-no-events":
            self.logger.debug(
                "%s: Skipped reporting for severity '%s' and time interval %s -> %s (%s): No events to report.",
                reporting_properties.group.name,
                reporting_properties.severity,
                reporting_properties.lower_time_bound.isoformat(),
                reporting_properties.upper_time_bound.isoformat(),
                str(reporting_properties.upper_time_bound - reporting_properties.lower_time_bound),
            )

        return result

    # ---------------------------------------------------------------------------

    def _fetch_groups_from_events(self, time_h):
        """
        Fetch all group names from events database for a given time window.

        :return: Set of all group names as strings.
        :rtype: set
        """
        # Calculate lower threshold of considered events by using the longest period for reporting.
        period = datetime.timedelta(
            seconds=mentat.const.REPORTING_INTERVALS[mentat.const.REPORTING_TIMING_DEFAULT_LOW_PER]
        )
        time_l = time_h - period
        _, events = self.eventservice.search_events({"st_from": time_l, "st_to": time_h, "groups": ["__ANY__"]})
        # Uniquify the found groups.
        result = []
        for e in events:
            result.extend(e.get_source_groups())
            result.extend(e.get_target_groups())
        return set(result)

    # ---------------------------------------------------------------------------

    def _fetch_groups_enabled(self):
        """
        Fetch all group objects from main database with ``enabled`` attribute
        set to ``True``.

        :return: List of all enabled group objects as :py:class:`mentat.datatype.sqldb.GroupModel`.
        :rtype: list
        """
        groups = self.sqlservice.session.query(GroupModel).filter(GroupModel.enabled).order_by(GroupModel.name).all()
        self.sqlservice.session.commit()

        self.logger.debug("Found total of %d enabled group(s) in main database.", len(groups))
        return groups


def main():
    MentatReporterScript().run()
