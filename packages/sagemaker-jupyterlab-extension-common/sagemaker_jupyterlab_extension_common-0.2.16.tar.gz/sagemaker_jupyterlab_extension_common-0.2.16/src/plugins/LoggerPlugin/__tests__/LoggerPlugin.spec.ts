import { getSession, ISession } from '../utils';
import { ServerConnection } from '@jupyterlab/services';
import { PageConfig } from '@jupyterlab/coreutils';
import { JupyterFrontEnd } from '@jupyterlab/application';
import { CONTEXT_INJECT_PLACEHOLDER, pluginIds } from '../../../constants';
import { LoggerPlugin } from '../LoggerPlugin';
import { EventLog } from '@jupyterlab/jupyterlab-telemetry';

jest.mock('@jupyterlab/services', () => {
  return {
    ServerConnection: {
      makeSettings: jest.fn(),
      makeRequest: jest.fn(),
    },
  };
});

jest.mock('@jupyterlab/coreutils', () => {
  return {
    PageConfig: {
      getBaseUrl: jest.fn(),
    },
  };
});

const mockLoggerSession: ISession = {
  id: '234a3e71-ea79-4c82-b8a4-650cbff8642f',
  startTime: '2021-04-14T22:14:49.158Z',
};

jest.mock('../utils', () => ({
  getSession: jest.fn(),
}));

describe('LoggerPlugin', () => {
  const mockSettings = {};
  const mockBaseUrl = '/';

  beforeAll(() => {
    const mockConsole = () => {
      // Let's keep our test logs clean from expected output.
    };

    jest.spyOn(console, 'error').mockImplementation(mockConsole);
    jest.spyOn(console, 'warn').mockImplementation(mockConsole);
    jest.spyOn(console, 'log').mockImplementation(mockConsole);
    (ServerConnection.makeSettings as jest.Mock).mockReturnValue(mockSettings);
    (PageConfig.getBaseUrl as jest.Mock).mockReturnValue(mockBaseUrl);
    (getSession as jest.Mock).mockReturnValue(mockLoggerSession);
  });

  afterEach(() => {
    jest.clearAllMocks();
  });

  it('can create LoggerPlugin', async () => {
    const appMock = {} as JupyterFrontEnd;

    const logger = LoggerPlugin.activate(appMock);

    const expectedLogger = {
      context: {
        AccountId: CONTEXT_INJECT_PLACEHOLDER,
        SpaceName: CONTEXT_INJECT_PLACEHOLDER,
        SessionId: mockLoggerSession.id,
      },
      eventLog: expect.any(EventLog),
    };

    expect(logger).toMatchObject(expectedLogger);
    expect(typeof logger.trace).toBe('function');
    expect(typeof logger.debug).toBe('function');
    expect(typeof logger.info).toBe('function');
    expect(typeof logger.warn).toBe('function');
    expect(typeof logger.error).toBe('function');
    expect(typeof logger.fatal).toBe('function');
  });

  it('creates session with unique ILOGGER_PLUGIN_ID key', () => {
    const appMock = {} as JupyterFrontEnd;

    LoggerPlugin.activate(appMock);
    expect(getSession).toHaveBeenCalledTimes(1);
    expect(getSession).toHaveBeenCalledWith(pluginIds.LoggerPlugin);
  });
});
