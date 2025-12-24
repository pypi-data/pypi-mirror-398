import { injectPanoramaScript } from '../utils';

describe('injectPanoramaScript', () => {
  it('should return an error if region is undefined', () => {
    const region = undefined;

    expect(() => {
      injectPanoramaScript(region);
    }).toThrow('Failed to get region');
  });

  it('should return a script tag if an AWSRegion is provided for Prod stage', () => {
    const region = 'us-west-2';
    const stage = 'prod';

    injectPanoramaScript(region, stage);
    const scriptTag = document.querySelector('script');
    const expectedDataConfig =
      '{"appEntity": "aws-sagemaker", "region": "us-west-2", "service" :"sagemaker-jupyterlab", "domain": "Prod"}';

    expect(!!scriptTag).toBe(true);
    expect(scriptTag?.getAttribute('data-config')).toBe(expectedDataConfig);
  });

  it('should return a script tag if an AWSRegion is provided for NonProd stage', () => {
    const region = 'us-west-2';
    const stage = 'devo';

    injectPanoramaScript(region, stage);
    const scriptTag = document.querySelector('script');
    const expectedDataConfig =
      '{"appEntity": "aws-sagemaker", "region": "us-west-2", "service" :"sagemaker-jupyterlab", "domain": "Prod"}';

    expect(!!scriptTag).toBe(true);
    expect(scriptTag?.getAttribute('data-config')).toBe(expectedDataConfig);
  });
});
