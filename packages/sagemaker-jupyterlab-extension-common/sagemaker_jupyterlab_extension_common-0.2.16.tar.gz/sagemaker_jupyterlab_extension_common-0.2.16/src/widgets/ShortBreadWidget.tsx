import React from 'react';
import { ReactWidget } from '@jupyterlab/apputils';

import { ShortBreadComponent } from '../components';

class ShortBreadWidget extends ReactWidget {
  render() {
    return <ShortBreadComponent />;
  }
}

export { ShortBreadWidget };
