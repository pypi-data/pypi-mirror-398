import { JupyterFrontEnd, JupyterFrontEndPlugin } from '@jupyterlab/application';
import { injectPanoramaScript } from './utils';
import { OPTIONS_TYPE, fetchApiResponse } from '../../services';
import { SAGEMAKER_CONTEXT_ENDPOINT, pluginIds, widgetIds } from '../../constants';
import { ShortBreadWidget } from '../../widgets';
import { IStatusBar } from '@jupyterlab/statusbar';

const mountPanorama = async (app: JupyterFrontEnd) => {
  try {
    await app.started;
    const jupyterLabMain = document.getElementById('main');

    const getStudioContextResponse = await fetchApiResponse(SAGEMAKER_CONTEXT_ENDPOINT, OPTIONS_TYPE.GET);
    const studioContextResponseJson = await getStudioContextResponse.json();
    if (jupyterLabMain) {
      injectPanoramaScript(studioContextResponseJson.region, studioContextResponseJson.stage);
    } else {
      throw new Error('JupyterLab application or region not found in DOM');
    }
  } catch (err) {
    // Log panorama error
  }
};

const PanoramaPlugin: JupyterFrontEndPlugin<void> = {
  id: pluginIds.PanoramaPlugin,
  autoStart: true,
  requires: [IStatusBar],
  activate: (app: JupyterFrontEnd, statusBar: IStatusBar) => {
    mountPanorama(app);

    const shortBreadWidget = new ShortBreadWidget();

    statusBar.registerStatusItem(widgetIds.shortBreadStatus, {
      item: shortBreadWidget,
      align: 'right',
      rank: 599,
      isActive: () => true,
    });
  },
};

export { PanoramaPlugin };
