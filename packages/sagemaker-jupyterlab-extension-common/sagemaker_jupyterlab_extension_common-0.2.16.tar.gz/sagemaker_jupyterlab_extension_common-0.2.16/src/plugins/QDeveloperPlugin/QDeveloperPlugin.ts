import { JupyterFrontEnd, JupyterFrontEndPlugin } from '@jupyterlab/application';
import { pluginIds } from '../../constants';
import { UserMetaDataService } from '../../services/usermetadata';

/**
 * Plugin to receive and store credentials for Q developer (IDC access token & Q profile ARN)
 */
const QDeveloperPlugin: JupyterFrontEndPlugin<void> = {
  id: pluginIds.QDeveloperPlugin,
  autoStart: true,
  activate: async (app: JupyterFrontEnd) => {
    const userMetadataService = new UserMetaDataService(app);
    await userMetadataService.updateInitialLanguageModelConfig();

    app.restored.then(async () => {
      userMetadataService.initialize();
    });
  },
};

export { QDeveloperPlugin };
