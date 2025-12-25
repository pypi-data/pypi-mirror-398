# -*- coding: utf-8 -*-
#
# File: Install.py
#
# Copyright (c) 2013 by Imio.be
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

__author__ = """Gauthier BASTIEN <gauthier.bastien@imio.be>, Stéphan Geulette <stephan.geulette@imio.be>"""
__docformat__ = 'plaintext'

from Products.CMFCore.utils import getToolByName


def uninstall(self, reinstall=False):
    """
        Uninstall step needed to call uninstall profile !
    """
    if not reinstall:
        setup_tool = getToolByName(self, 'portal_setup')
        setup_tool.runAllImportStepsFromProfile('profile-plonetheme.imioapps:uninstall')
    return "Ran all uninstall steps."
