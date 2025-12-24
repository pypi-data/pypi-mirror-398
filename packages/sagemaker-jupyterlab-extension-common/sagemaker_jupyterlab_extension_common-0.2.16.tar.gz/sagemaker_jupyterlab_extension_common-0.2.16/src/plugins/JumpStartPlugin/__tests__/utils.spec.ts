import { fetchNotebook } from '../utils';
import { ServerConnection } from '@jupyterlab/services';

const mockLogger: ILogger = {
  error: jest.fn(),
  info: jest.fn(),
  child: jest.fn(() => mockLogger),
};

jest.mock('@jupyterlab/services', () => {
  return {
    ServerConnection: {
      makeSettings: jest.fn(),
      makeRequest: jest.fn(),
    },
  };
});

jest.mock('@jupyterlab/apputils', () => jest.fn as jest.Mock);

describe('executeOpenNotebook', () => {
  beforeAll(() => {
    const mockSettings = {};
    const mockResponse = { status: 200, headers: new Headers() } as Response;
    mockResponse.json = () => Promise.resolve({ notebookPath: 'pmm_notebook/notebook.ipynb' });

    (ServerConnection.makeSettings as jest.Mock).mockReturnValue(mockSettings);
    (ServerConnection.makeRequest as jest.Mock).mockReturnValue(Promise.resolve(mockResponse));
  });

  afterEach(() => {
    jest.clearAllMocks();
  });

  it('should return a notebook path when fetching the notebook succeeds', async () => {
    const body = {
      key: 'pmm_notebook/notebook.ipynb',
    };
    const result = await fetchNotebook(body, mockLogger);
    expect(result).toEqual('pmm_notebook/notebook.ipynb');
  });

  it('should throw when fetching the notebook fails', async () => {
    const mockSettings = {};
    const mockResponse = { status: 500 } as Response;
    mockResponse.json = () => Promise.resolve({ notebookPath: 'pmm_notebook/notebook.ipynb' });

    (ServerConnection.makeSettings as jest.Mock).mockImplementation(() => mockSettings);
    (ServerConnection.makeRequest as jest.Mock).mockImplementation(() => mockResponse);
    const body = {
      key: 'pmm_notebook/notebook.ipynb',
    };
    await expect(fetchNotebook(body, mockLogger)).rejects.toThrow(Error);
  });
});
