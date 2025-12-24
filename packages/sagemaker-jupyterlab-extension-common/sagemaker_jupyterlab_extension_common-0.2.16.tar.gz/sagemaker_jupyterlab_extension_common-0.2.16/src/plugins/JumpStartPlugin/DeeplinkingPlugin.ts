import { JupyterFrontEnd, JupyterFrontEndPlugin, IRouter } from '@jupyterlab/application';
import { getLoggerForPlugin, pluginIds } from '../../constants';
import { executeOpenNotebook } from './utils';
import { ILogger } from '../LoggerPlugin';

/**
 * Plugin to download and open a jumpstart notebook
 */
const DeepLinkingPlugin: JupyterFrontEndPlugin<void> = {
  id: pluginIds.JumpStartDeeplinkingPlugin,
  requires: [IRouter, ILogger],
  autoStart: true,
  activate: async (app: JupyterFrontEnd, router: IRouter, baseLogger: ILogger) => {
    const { commands } = app;
    const commandName = 'jumpstart:open-notebook-for-deeplinking';
    const logger = getLoggerForPlugin(baseLogger, pluginIds.JumpStartDeeplinkingPlugin);

    commands.addCommand(commandName, {
      execute: () => executeOpenNotebook(router, app, logger),
    });

    router.register({
      command: commandName,
      pattern: new RegExp('[?]command=open-jumpstart-notebook'),
      rank: 10, // arbitrary ranking to lift this pattern
    });
  },
};

export { DeepLinkingPlugin };
