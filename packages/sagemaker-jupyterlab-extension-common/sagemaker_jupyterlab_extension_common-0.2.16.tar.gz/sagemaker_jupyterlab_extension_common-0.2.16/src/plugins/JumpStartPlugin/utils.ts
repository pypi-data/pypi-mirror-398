import { IRouter, JupyterFrontEnd } from '@jupyterlab/application';
import { URLExt } from '@jupyterlab/coreutils';
import { ApiError, OPTIONS_TYPE, fetchApiResponse } from '../../services';
import { ApiErrorCode } from './constants';
import { ILogger } from '../LoggerPlugin';
import { showErrorMessage } from '@jupyterlab/apputils';
import { i18nStrings } from '../../constants/i18nStrings';
import { v4 as uuidv4 } from 'uuid';

const SERVER_REQUEST_ID_HEADER_KEY = 'x-server-req-id';
const SERVER_REQUEST_ID_MISSING = 'SERVER_REQUEST_ID_MISSING';
const il18stringsError = i18nStrings.JumpStartDeeplinking.errorDialog;

// IRouter pattern could be matched arbitrary number of times.
// This flag is to ensure only trigger downloading and opening jumpstart notebook once during re-direction.
let isPatternMatched = false;

/**
 * Function to open jumpstart notebook
 * @param router
 * @param app
 * @returns
 */
const executeOpenNotebook = async (router: IRouter, app: JupyterFrontEnd, logger: ILogger) => {
  if (isPatternMatched) {
    return;
  }
  try {
    const { search } = router.current;
    if (!search) {
      await showErrorMessageAsync(il18stringsError.invalidRequestErrorMessage);
      logger.error({ Error: new Error('Invalid deep-linking parameters: Query params must be specified') });
      return;
    }
    const {
      key,
      model_id: modelId,
      endpoint_name: endpointName,
      resource_type: resourceType,
      inference_component: inferenceComponent,
      set_default_kernel: setDefaultKernel,
      cluster_id: clusterId,
      hub_name: hubName,
      domain: domain,
      connection_id: connectionId,
      recipe_path: recipePath,
      base_model_name: baseModelName,
      customization_technique: customizationTechnique,
      model_package_group_name: modelPackageGroupName,
      data_set_name: dataSetName,
      data_set_version: dataSetVersion,
    } = URLExt.queryStringToObject(search);
    if (!key) {
      await showErrorMessageAsync(il18stringsError.invalidRequestErrorMessage);
      logger.error({ Error: new Error('Invalid deep-linking parameters: the notebook key must be specified.') });
      return;
    }

    const body = {
      key,
      ...(resourceType && { resource_type: resourceType }),
      ...(modelId && { model_id: modelId }),
      ...(endpointName && { endpoint_name: endpointName }),
      ...(inferenceComponent && { inference_component: inferenceComponent }),
      ...(setDefaultKernel && { set_default_kernel: setDefaultKernel }),
      ...(clusterId && { cluster_id: clusterId }),
      ...(hubName && { hub_name: hubName }),
      ...(connectionId && { connection_id: connectionId }),
      ...(domain && { domain: domain }),
      ...(recipePath && { recipe_path: recipePath }),
      ...(baseModelName && { base_model_name: baseModelName }),
      ...(customizationTechnique && { customization_technique: customizationTechnique }),
      ...(modelPackageGroupName && { model_package_group_name: modelPackageGroupName }),
      ...(dataSetName && { data_set_name: dataSetName }),
      ...(dataSetVersion && { data_set_version: dataSetVersion }),
    };

    const notebookPath = await fetchNotebook(body, logger);
    // use app.restored to make sure only call open notebook command after all the assets are loaded
    app.restored.then(() => {
      app.commands.execute('docmanager:open', { factory: 'Notebook', path: notebookPath });
    });
    logger.info({ Message: 'Successfully loaded the Deeplinking plugin' });
  } catch (error) {
    if (error instanceof ApiError) {
      await showApiRequestErrorMessage(ApiErrorCode[error.errorCode as keyof typeof ApiErrorCode]);
      return;
    }
    await showErrorMessageAsync(il18stringsError.defaultErrorMessage);
    logger.error({ Error: new Error(`Error executing open notebook: ${error}`) });
    return;
  } finally {
    isPatternMatched = true;
  }
};

const fetchNotebook = async (body: object, logger: ILogger) => {
  const clientRequestId = uuidv4();
  logger.info({ Message: 'Fetching Notebook', ClientRequestId: clientRequestId });
  let response;
  try {
    response = await fetchApiResponse('aws/sagemaker/api/jumpstart/notebook', OPTIONS_TYPE.POST, JSON.stringify(body), {
      'x-client-req-id': clientRequestId,
    });
  } catch (error) {
    logger.error({ Error: new Error(`Error executing open notebook: ${error}`), ClientRequestId: clientRequestId });
    throw error;
  }
  const serverRequestId = response.headers.get(SERVER_REQUEST_ID_HEADER_KEY) || SERVER_REQUEST_ID_MISSING;
  logger.info({
    Message: 'Successfully fetched Notebook',
    ClientRequestId: clientRequestId,
    ServerRequestId: serverRequestId,
  });

  const result = await response.json();
  const { notebookPath } = result;
  return notebookPath;
};

const showApiRequestErrorMessage = async (errorCode?: ApiErrorCode) => {
  switch (errorCode) {
    case ApiErrorCode.NOTEBOOK_NOT_AVAILABLE:
      await showErrorMessageAsync(il18stringsError.notebookNotFoundErrorMessage);
      break;
    case ApiErrorCode.NOTEBOOK_SIZE_TOO_LARGE:
      await showErrorMessageAsync(il18stringsError.notebookSizeTooLargeErrorMessage);
      break;
    case ApiErrorCode.INVALID_REQUEST:
      await showErrorMessageAsync(il18stringsError.invalidRequestErrorMessage);
      break;
    case ApiErrorCode.INTERNAL_SERVER_ERROR:
      await showErrorMessageAsync(il18stringsError.defaultErrorMessage);
      break;
    case ApiErrorCode.DOWNLOAD_DIRECTORY_NOT_FOUND:
      await showErrorMessageAsync(il18stringsError.downLoadDirectoryNotFoundMessage);
      break;
    default:
      await showErrorMessageAsync(il18stringsError.defaultErrorMessage);
      break;
  }
};

const showErrorMessageAsync = async (message: string) => {
  return showErrorMessage(il18stringsError.errorTitle, {
    message: message,
  });
};

export { executeOpenNotebook, fetchNotebook };
