import { render } from '@testing-library/react';
import { ShortBreadWidget } from '../ShortBreadWidget';

describe('ShortBreadWidget', () => {
  it('should render without errors', () => {
    const shortbreadWidget = new ShortBreadWidget();
    const { container } = render(shortbreadWidget.render());
    expect(container).toBeTruthy();
  });
});
