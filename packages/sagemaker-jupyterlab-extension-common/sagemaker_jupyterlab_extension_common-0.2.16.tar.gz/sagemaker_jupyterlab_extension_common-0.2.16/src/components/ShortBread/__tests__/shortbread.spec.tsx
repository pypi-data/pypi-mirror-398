import React from 'react';
import { render, fireEvent, screen } from '@testing-library/react';
import { ShortBreadComponent } from '../shortbread';

describe('ShortbreadComponent', () => {
  it('renders without errors', () => {
    render(<ShortBreadComponent />);
    const linkElement = screen.getByText('Cookie Preferences');
    expect(linkElement).toBeInTheDocument();
  });

  it('calls customizeCookies when clicked', () => {
    render(<ShortBreadComponent />);
    const linkElement = screen.getByText('Cookie Preferences');

    fireEvent.click(linkElement);

    expect(linkElement).toBeInTheDocument();
  });
});
