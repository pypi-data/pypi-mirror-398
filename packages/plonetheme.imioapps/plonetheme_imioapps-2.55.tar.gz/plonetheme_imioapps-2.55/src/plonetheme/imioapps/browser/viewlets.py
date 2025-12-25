# -*- coding: utf-8 -*-
#
# Copyright (c) 2015 by Imio.be
#
# GNU General Public License (GPL)
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA
# 02110-1301, USA.
#

from imio.helpers.workflow import get_state_infos
from plone import api
from plone.app.layout.viewlets import ViewletBase
from Products.Five.browser.pagetemplatefile import ViewPageTemplateFile


class EmptyViewlet(ViewletBase):
    """This will display an empty viewlet, it is used to be able to define CSS
       arbitrary between existing viewlets."""
    render = ViewPageTemplateFile('./templates/empty.pt')


class WorkflowState(ViewletBase):
    '''This viewlet displays the workflow state.'''

    def state_infos(self):
        return get_state_infos(self.context)

    index = ViewPageTemplateFile("templates/viewlet_workflowstate.pt")


class HelpViewlet(ViewletBase):
    index = ViewPageTemplateFile('templates/help.pt')

    def update(self):
        super(HelpViewlet, self).update()
        self.help_url = api.portal.get_registry_record(
            'plonetheme.imioapps.interfaces.IPlonethemeImioappsSettings.help_url', default='')
