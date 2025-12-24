import { ServerConnection } from '@jupyterlab/services';
import { URLExt } from '@jupyterlab/coreutils';
import { SUCCESS_RESPONSE_STATUS } from '../constants';

enum OPTIONS_TYPE {
  POST = 'POST',
  GET = 'GET',
  PUT = 'PUT',
}

type OptionsType = OPTIONS_TYPE;

class ApiError extends Error {
  readonly errorStatus: number;
  readonly errorCode?: string;
  readonly cause?: any;
  constructor(message: string, errorStatus: number, errorCode?: string, cause?: any) {
    super(message);
    this.errorStatus = errorStatus;
    this.errorCode = errorCode;
    this.cause = cause;
    Object.setPrototypeOf(this, ApiError.prototype);
  }
}

/**
 * Function call to make API calls for the plugin
 */
const fetchApiResponse = async (
  endpoint: string,
  type: OptionsType,
  body?: string,
  headers?: Record<string, string>,
) => {
  // @TODO: add in logger
  const serverSettings = ServerConnection.makeSettings({});
  const requestUrl = URLExt.join(serverSettings.baseUrl, endpoint);
  const init: RequestInit = { method: type };
  if (body) {
    init['body'] = body;
  }
  if (headers) {
    init['headers'] = headers;
  }

  const response = await ServerConnection.makeRequest(requestUrl, init, serverSettings);

  if (!SUCCESS_RESPONSE_STATUS.includes(response.status)) {
    const body = await response.json();
    const errorCode = body.errorCode ?? undefined;
    const errorMessage = body.errorMessage ?? 'unable to fetch data';
    throw new ApiError(errorMessage, response.status, errorCode);
  }
  return response;
};

export { fetchApiResponse, OPTIONS_TYPE, ApiError };
