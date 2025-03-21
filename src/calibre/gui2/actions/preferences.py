#!/usr/bin/env python


__license__   = 'GPL v3'
__copyright__ = '2010, Kovid Goyal <kovid@kovidgoyal.net>'
__docformat__ = 'restructuredtext en'

from functools import partial

from qt.core import QIcon, Qt

from calibre.constants import DEBUG, ismacos
from calibre.customize.ui import preferences_plugins
from calibre.gui2 import error_dialog, show_restart_warning
from calibre.gui2.actions import InterfaceAction
from calibre.gui2.preferences.main import Preferences


class PreferencesAction(InterfaceAction):

    name = 'Preferences'
    action_spec = (_('Preferences'), 'config.png', _('Configure calibre'), 'Ctrl+P')
    action_add_menu = True
    action_menu_clone_qaction = _('Change calibre behavior')

    def genesis(self):
        pm = self.qaction.menu()
        cm = partial(self.create_menu_action, pm)
        if ismacos:
            pm.addAction(QIcon.ic('config.png'), _('Preferences'), self.do_config)
        cm('welcome wizard', _('Run Welcome wizard'),
                icon='wizard.png', triggered=self.gui.run_wizard)
        cm('plugin updater', _('Get plugins to enhance calibre'),
                icon='plugins/plugin_updater.png', triggered=self.get_plugins)
        pm.addSeparator()
        if not DEBUG:
            cm('restart', _('Restart in debug mode'), icon='debug.png',
                    triggered=self.debug_restart, shortcut='Ctrl+Shift+R')
        cm('restart_without_plugins', _('Restart ignoring third party plugins'), icon='debug.png',
            triggered=self.no_plugins_restart, shortcut='Ctrl+Alt+Shift+R')

        self.preferences_menu = pm
        for x in (self.gui.preferences_action, self.qaction):
            x.triggered.connect(self.do_config)

    def initialization_complete(self):
        # Add the individual preferences to the menu.
        # First, sort them into the same order as shown in the preferences dialog
        plugins = sorted(preferences_plugins(),
                         key=lambda p: p.category_order * 100 + p.name_order)

        pm = self.preferences_menu
        # The space pushes the separator a bit away from the text
        pm.addSection(_('Sections') + ' ')

        config_icon = QIcon.ic('config.png')
        current_cat = 0
        for p in plugins:
            if p.category_order != current_cat:
                current_cat = p.category_order
                cm = pm.addMenu(p.gui_category.replace('&', '&&'))
                cm.setIcon(config_icon)
            self.create_menu_action(cm, p.name, p.gui_name.replace('&', '&&'),
                                    icon=QIcon.ic(p.icon), shortcut=None, shortcut_name=p.gui_name,
                                    triggered=partial(self.do_config, initial_plugin=(p.category, p.name),
                                                      close_after_initial=True))

    def get_plugins(self):
        from calibre.gui2.dialogs.plugin_updater import FILTER_NOT_INSTALLED, PluginUpdaterDialog
        d = PluginUpdaterDialog(self.gui,
                initial_filter=FILTER_NOT_INSTALLED)
        d.exec()
        if d.do_restart:
            self.gui.quit(restart=True)

    def do_config(self, checked=False, initial_plugin=None,
            close_after_initial=False):
        if self.gui.job_manager.has_jobs():
            d = error_dialog(self.gui, _('Cannot configure'),
                    _('Cannot configure while there are running jobs.'))
            d.exec()
            return
        if self.gui.must_restart_before_config:
            do_restart = show_restart_warning(_('Cannot configure before calibre is restarted.'))
            if do_restart:
                self.gui.quit(restart=True)
            return
        d = Preferences(self.gui, initial_plugin=initial_plugin,
                close_after_initial=close_after_initial)
        d.run_wizard_requested.connect(self.gui.run_wizard,
                type=Qt.ConnectionType.QueuedConnection)
        d.exec()
        if d.do_restart:
            self.gui.quit(restart=True)

    def debug_restart(self, *args):
        self.gui.quit(restart=True, debug_on_restart=True)

    def no_plugins_restart(self, *args):
        self.gui.quit(restart=True, no_plugins_on_restart=True)
