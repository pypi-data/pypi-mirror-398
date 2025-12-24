import { JupyterFrontEnd, JupyterFrontEndPlugin } from '@jupyterlab/application';
import { IStatusBar } from '@jupyterlab/statusbar';
import { openDialog, RecoveryModeWidget } from '../../widgets/RecoveryModeWidget';
import { fetchApiResponse, OPTIONS_TYPE } from '../../services';

const RecoveryModePlugin: JupyterFrontEndPlugin<void> = {
  id: 'recoverymode:plugin',
  autoStart: true,
  requires: [IStatusBar],
  activate: async (app: JupyterFrontEnd, statusBar: IStatusBar) => {
    app.restored.then(async () => {
      const isRecoveryMode = await getRecoveryModeStatus();
      if (isRecoveryMode) {
        const recoveryModeSymlinkStatus = await fetchApiResponse('/aws/sagemaker/api/recovery-mode', OPTIONS_TYPE.POST);
        if (recoveryModeSymlinkStatus.status !== 200 && recoveryModeSymlinkStatus.status !== 201) {
          // eslint-disable-next-line no-console
          console.error(`Failed to create Recovery Mode Symlink, status: ${recoveryModeSymlinkStatus.status}`);
        }

        const widget = new RecoveryModeWidget();
        statusBar.registerStatusItem('recoverymode:statusbar', {
          align: 'right',
          item: widget,
          rank: 1000,
        });
        // eslint-disable-next-line no-console
        await openDialog().catch((err) => console.error('Error opening recovery mode dialog:', err));
      }
    });
  },
};

/**
 * Fetches the recovery mode status from the Jupyter server API.
 * @returns A promise that resolves to `true` if recovery mode is enabled, `false` otherwise.
 */
async function getRecoveryModeStatus(): Promise<boolean> {
  try {
    const response = await fetchApiResponse('/aws/sagemaker/api/recovery-mode', OPTIONS_TYPE.GET);

    if (!response.ok) {
      return false;
    }

    const data = await response.json();
    return data.sagemakerRecoveryMode === 'true';
  } catch (error) {
    return false;
  }
}

export { RecoveryModePlugin };
