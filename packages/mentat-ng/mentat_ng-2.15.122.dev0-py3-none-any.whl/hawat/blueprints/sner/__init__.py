#!/usr/bin/env python3
# -------------------------------------------------------------------------------
# This file is part of Mentat system (https://mentat.cesnet.cz/).
#
# Copyright (C) since 2011 CESNET, z.s.p.o (http://www.ces.net/)
# Use of this source is governed by the MIT license, see LICENSE file.
# -------------------------------------------------------------------------------


"""
This pluggable module provides access to `Sner <https://sner-hub.flab.cesnet.cz/>`__
service operated by `CESNET, a.l.e. <https://www.cesnet.cz/>`__. It is implemented
upon custom :py:mod:`mentat.services.sner` module.


Provided endpoints
------------------

``/snippet/sner/search``
    Endpoint providing API search form for querying Sner service and formating
    result as JSON document containing HTML snippets.

    * *Authentication:* login required
    * *Authorization:* based on group memberships (more info in is_authorized method)
    * *Methods:* ``GET``, ``POST``
"""

__author__ = "Jakub Judiny <Jakub.Judiny@cesnet.cz>"
__credits__ = "Pavel Kácha <pavel.kacha@cesnet.cz>, Andrea Kropáčová <andrea.kropacova@cesnet.cz>"

import flask
import flask_login
import markupsafe
from flask_babel import lazy_gettext

import hawat.acl
import hawat.const
import hawat.db
import mentat.services.sner
import mentat.services.whois
from hawat.base import HawatBlueprint
from hawat.blueprints.sner.forms import SNERSearchForm
from hawat.utils import URLParamsBuilder
from hawat.view import RenderableView
from hawat.view.mixin import SnippetMixin
from mentat.const import tr_

BLUEPRINT_NAME = "sner"
"""Name of the blueprint as module global constant."""


class AbstractSearchView(RenderableView):
    """
    Application view providing base search capabilities for SNER service.

    The querying is implemented using :py:mod:`mentat.services.sner` module.
    """

    authentication = True

    @classmethod
    def get_view_title(cls, **kwargs):
        return lazy_gettext("Search SNER")

    @classmethod
    def get_menu_title(cls, **kwargs):
        return lazy_gettext("Search SNER")

    @classmethod
    def is_authorized(cls, results):
        """
        Check whether the current user is authorized to perform this search.

        Authorization is performed based on IP addresses in the results and
        their corresponding Mentat groups (looked up via whois).

        A user is allowed to search an IP or hostname in SNER if:
        - they are a maintainer, or
        - they are a member or manager of at least one resolved group
        """
        if hawat.acl.PERMISSION_POWER.can():
            return True

        whois_manager = mentat.services.whois.WhoisServiceManager(flask.current_app.mconfig)
        whois_service = whois_manager.service()
        user_groups = flask_login.current_user.get_all_group_names()
        for result in results:
            result_groups = whois_service.lookup_abuse(result.get("address"))
            for user_group_name in user_groups:
                if user_group_name in result_groups:
                    return True
        return False

    def dispatch_request(self):
        """
        Mandatory interface required by the :py:func:`flask.views.View.dispatch_request`.
        Will be called by the *Flask* framework to service the request.
        """
        form = SNERSearchForm(flask.request.args, meta={"csrf": False})

        if hawat.const.FORM_ACTION_SUBMIT in flask.request.args:
            if form.validate():
                form_data = form.data
                sner_service = mentat.services.sner.service()
                self.response_context.update(
                    search_item=form.search.data,
                    form_data=form_data,
                )

                try:
                    lookup_result = sner_service.lookup_ip_or_hostname(form.search.data)
                    if lookup_result is not None:
                        result, is_ip = lookup_result
                        if self.is_authorized(result):
                            self.response_context.update(
                                search_result=result,
                                search_url=sner_service.get_web_url(form.search.data, is_ip),
                            )

                except Exception as exc:
                    self.flash(
                        markupsafe.Markup(
                            lazy_gettext("<b>This search was not successful.</b> SNER returned error: ") + str(exc)
                        ),
                        hawat.const.FLASH_FAILURE,
                    )

        self.response_context.update(
            search_form=form,
            request_args=flask.request.args,
        )
        return self.generate_response()


class SnippetSearchView(SnippetMixin, AbstractSearchView):
    """
    View responsible for querying SNER service and presenting the results
    in the form of JSON document containing ready to use HTML page snippets.
    """

    methods = ["GET", "POST"]

    renders = ["label", "full"]

    snippets = [
        {
            "name": "hostnames",
            "condition": lambda x: x.get("search_result", False),
        }
    ]

    @classmethod
    def get_view_name(cls):
        return "sptsearch"


# -------------------------------------------------------------------------------


class SNERBlueprint(HawatBlueprint):
    """Pluggable module - SNER service (*sner*)."""

    @classmethod
    def get_module_title(cls):
        return lazy_gettext("SNER service")

    def register_app(self, app):
        mentat.services.sner.init(app.mconfig)

        # Register object additional data services provided by this module.
        app.set_oads(
            hawat.const.AODS_IP4,
            SnippetSearchView,
            URLParamsBuilder({"submit": tr_("Search")}).add_rule("search").add_kwrule("render", False, True),
        )
        app.set_oads(
            hawat.const.AODS_IP6,
            SnippetSearchView,
            URLParamsBuilder({"submit": tr_("Search")}).add_rule("search").add_kwrule("render", False, True),
        )
        app.set_oads(
            hawat.const.AODS_HOSTNAME,
            SnippetSearchView,
            URLParamsBuilder({"submit": tr_("Search")}).add_rule("search").add_kwrule("render", False, True),
        )


# -------------------------------------------------------------------------------


def get_blueprint():
    """
    Mandatory interface for :py:mod:`hawat.Hawat` and factory function. This function
    must return a valid instance of :py:class:`hawat.app.HawatBlueprint` or
    :py:class:`flask.Blueprint`.
    """

    hbp = SNERBlueprint(
        BLUEPRINT_NAME,
        __name__,
        template_folder="templates",
    )

    hbp.register_view_class(SnippetSearchView, f"/snippet/{BLUEPRINT_NAME}/search")

    return hbp
