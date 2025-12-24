import { JupyterFrontEnd, JupyterFrontEndPlugin } from '@jupyterlab/application';
import { pluginIds } from '../../constants';
import { ShortcutCommunicator } from '../../services/shortcutcommunicator';

/**
 * Plugin to handle pulling up CommandPalette
 */
const CommandPalettePlugin: JupyterFrontEndPlugin<void> = {
  id: pluginIds.CommandPalettePlugin,
  autoStart: true,
  activate: async (app: JupyterFrontEnd) => {
    const shortcutCommunicator = new ShortcutCommunicator();

    app.restored.then(async () => {
      shortcutCommunicator.initialize();
    });
  },
};

export { CommandPalettePlugin };
