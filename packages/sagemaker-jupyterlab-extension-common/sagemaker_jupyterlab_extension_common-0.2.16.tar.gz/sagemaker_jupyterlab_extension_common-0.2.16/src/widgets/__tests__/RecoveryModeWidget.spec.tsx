import { render } from '@testing-library/react';
import { RecoveryModeWidget } from '../RecoveryModeWidget';

describe('RecoveryModeWidget', () => {
  it('should render without errors', () => {
    const recoveryModeWidget = new RecoveryModeWidget();
    const { container } = render(recoveryModeWidget.render());
    expect(container).toBeTruthy();
  });
});
