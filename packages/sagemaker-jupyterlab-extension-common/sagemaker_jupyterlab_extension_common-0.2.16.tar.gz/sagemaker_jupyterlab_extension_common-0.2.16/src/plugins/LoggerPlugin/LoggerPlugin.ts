import { JupyterFrontEnd, JupyterFrontEndPlugin } from '@jupyterlab/application';
import { allowedSchemas, logSchemas, pluginIds } from '../../constants';
import { ILogger } from '../../types';
import { getSession } from './utils';
import { makeRemoteHandler } from './handlers';
import { Logger } from './logger';
import { SchemaDefinition } from '../../constants';
import { EventLog } from '@jupyterlab/jupyterlab-telemetry';

const REMOTE_RETRIES = 2;
const REMOTE_FLUSH_INTERVAL_IN_MS = 5000;
const REMOTE_MAX_BUFFER_SIZE = 10000;
const ENDPOINT_URL = 'aws/sagemaker/api/eventlog';

const LoggerPlugin: JupyterFrontEndPlugin<ILogger> = {
  id: pluginIds.LoggerPlugin,
  autoStart: true,
  provides: ILogger,
  activate: (_: JupyterFrontEnd) => {
    const loggerSession = getSession(pluginIds.LoggerPlugin);
    const context = {
      SessionId: loggerSession.id,
    };

    const remoteHandler = makeRemoteHandler(
      REMOTE_RETRIES,
      REMOTE_FLUSH_INTERVAL_IN_MS,
      REMOTE_MAX_BUFFER_SIZE,
      ENDPOINT_URL,
    );
    const eventLog = new EventLog({
      allowedSchemas,
      handlers: [remoteHandler],
    });
    const logger = new Logger(eventLog, logSchemas.operationalLogger, context);

    return logger;
  },
};

export { ILogger, LoggerPlugin, logSchemas, SchemaDefinition };
