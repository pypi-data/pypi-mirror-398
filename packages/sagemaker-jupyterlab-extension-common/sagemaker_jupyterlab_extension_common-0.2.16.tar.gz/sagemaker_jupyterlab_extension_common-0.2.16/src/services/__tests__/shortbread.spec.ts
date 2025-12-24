import { loadShortbreadScript, getShortbread } from '../shortbread';

describe('loadShortbreadScript', () => {
  it('should load the Shortbread script and set up AWSCShortbread', () => {
    const createElementSpy = jest.spyOn(document, 'createElement');
    const appendChildSpy = jest.spyOn(document.head, 'appendChild');

    loadShortbreadScript();

    expect(createElementSpy).toHaveBeenCalledTimes(2);
    expect(appendChildSpy).toHaveBeenCalledTimes(2);

    expect(createElementSpy.mock.calls[0][0]).toBe('script');
    expect(createElementSpy.mock.calls[1][0]).toBe('link');

    const script = createElementSpy.mock.results[0].value;
    const link = createElementSpy.mock.results[1].value;

    expect(script.src).toBe('https://prod.assets.shortbread.aws.dev/shortbread.js');
    expect(script.type).toBe('text/javascript');
    expect(script.async).toBe(true);

    expect(link.href).toBe('https://prod.assets.shortbread.aws.dev/shortbread.css');
    expect(link.rel).toBe('stylesheet');

    createElementSpy.mockRestore();
    appendChildSpy.mockRestore();
  });
});

describe('getShortbread', () => {
  it('should return AWSCShortbreadInstance', () => {
    const mockAWSCShortbreadInstance = { customizeCookies: jest.fn() };
    window.AWSCShortbreadInstance = mockAWSCShortbreadInstance;
    const result = getShortbread();
    expect(result).toBe(mockAWSCShortbreadInstance);
  });
});
