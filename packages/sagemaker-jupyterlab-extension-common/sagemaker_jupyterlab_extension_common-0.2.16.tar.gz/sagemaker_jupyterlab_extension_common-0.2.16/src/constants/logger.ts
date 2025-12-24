import { EventLog } from '@jupyterlab/jupyterlab-telemetry';
import { ILogger } from '../plugins';
import { makeRemoteHandler } from '../plugins/LoggerPlugin/handlers';
import { pluginIds } from './common';

type SchemaDefinition = { schemaId: string; schemaVersion: number };
type SchemaDefinitions = { [schemaName: string]: SchemaDefinition };

const logSchemas: SchemaDefinitions = {
  operationalLogger: {
    schemaId: 'http://sagemaker.studio.jupyterlab.ui.log.schema',
    schemaVersion: 1,
  },
  performance: {
    schemaId: 'http://sagemaker.studio.jupyterlab.ui.performance.schema',
    schemaVersion: 1,
  },
};

const allowedSchemas = Object.keys(logSchemas).map((schemaName) => logSchemas[schemaName].schemaId);

// The server extension will be able to inject context including account id and space
// name if corresponding field is set to '__INJECT__'.
const CONTEXT_INJECT_PLACEHOLDER = '__INJECT__';

// eslint-disable-next-line @typescript-eslint/no-var-requires
const { name, version } = require('../../package.json');

const getLoggerForPlugin = (baseLogger: ILogger, pluginId: string, schema?: SchemaDefinition) => {
  const eventLogMapping = {
    [pluginIds.JumpStartDeeplinkingPlugin]: getJumpStartEventLog(),
  };
  return baseLogger.child(
    {
      ExtensionName: name,
      ExtensionVersion: version,
      PluginId: pluginId,
    },
    schema,
    eventLogMapping[pluginId] ?? undefined,
  );
};

const getJumpStartEventLog = () => {
  const REMOTE_RETRIES = 2;
  const REMOTE_FLUSH_INTERVAL_IN_MS = 5000;
  const REMOTE_MAX_BUFFER_SIZE = 10000;
  const ENDPOINT_URL = 'aws/sagemaker/api/jumpstart/eventlog';
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
  return eventLog;
};

export {
  logSchemas,
  allowedSchemas,
  SchemaDefinition,
  SchemaDefinitions,
  CONTEXT_INJECT_PLACEHOLDER,
  getLoggerForPlugin,
};
