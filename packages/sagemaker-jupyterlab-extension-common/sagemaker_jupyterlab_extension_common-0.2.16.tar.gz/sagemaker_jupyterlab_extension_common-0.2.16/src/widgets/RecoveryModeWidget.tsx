import React from 'react';
import { ReactWidget } from '@jupyterlab/apputils';
import { Dialog } from '@jupyterlab/apputils';
import { recoveryModeIcon } from '../components/icons';
import { DialogAlertIcon, DialogBox, StatusBarAlertIcon, StatusBarWidget } from './styles/icons/styles';

// Dialog Logic
const openDialog = async () => {
  const dialog = new Dialog({
    title: (
      <div style={{ display: 'flex', alignItems: 'center' }}>
        <recoveryModeIcon.react className={DialogAlertIcon} />
        Runtime is in recovery mode
      </div>
    ),
    body: (
      <div className={DialogBox}>
        <div>Amazon SageMaker Studio is running in recovery mode with limited functionalities</div>
        <br />
        <div>
          Recovery mode allows you to access your Studio application when a configuration issue prevents your normal
          start up. It provides a simplified environment with essential functionality to help you diagnose and fix the
          issue.
        </div>
        <br />
        <div>
          Your original files are still safe and located in <code>/home/sagemaker-user</code>.<br />
          From this environment, you can access them using the following symlink:
          <br />
          <code>/symlink-to-original-home-directory</code> → points to <code>/home/sagemaker-user</code>
        </div>
        <br />
        <div>
          For more information, refer to the{' '}
          <a href="https://docs.aws.amazon.com/sagemaker/latest/dg/studio-updated-troubleshooting.html#studio-updated-troubleshooting-recovery-mode">
            SageMaker Studio troubleshooting guide
          </a>
        </div>
      </div>
    ),
    buttons: [Dialog.okButton({ label: 'Dismiss' })],
  });

  await dialog.launch();
};

// Widget Definition
class RecoveryModeWidget extends ReactWidget {
  constructor() {
    super();
  }

  render(): JSX.Element {
    return (
      <div className={StatusBarWidget} onClick={() => openDialog()} title="Click to view recovery mode information">
        <recoveryModeIcon.react className={StatusBarAlertIcon} />
        Runtime in Recovery Mode
      </div>
    );
  }
}

export { RecoveryModeWidget, openDialog };
