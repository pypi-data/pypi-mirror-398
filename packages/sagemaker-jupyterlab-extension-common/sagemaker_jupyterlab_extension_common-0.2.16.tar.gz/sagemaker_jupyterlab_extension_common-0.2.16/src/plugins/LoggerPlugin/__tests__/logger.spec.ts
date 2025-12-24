import { EventLog } from '@jupyterlab/jupyterlab-telemetry';
import { Logger } from '../logger';
import { CONTEXT_INJECT_PLACEHOLDER, allowedSchemas, logSchemas } from '../../../constants';
import { ILogger } from '../LoggerPlugin';
import { LogLevel } from '../../../types';

describe('Logger', () => {
  let mockHandler: jest.Mock;
  let eventLog: EventLog;
  let logger: ILogger;

  const initialLogContext = {
    SessionId: 'e5d5805d-4faa-4170-90d6-b4cee7b0a070',
  };

  const expectedLogContext = {
    SessionId: 'e5d5805d-4faa-4170-90d6-b4cee7b0a070',
    AccountId: CONTEXT_INJECT_PLACEHOLDER,
    SpaceName: CONTEXT_INJECT_PLACEHOLDER,
  };

  const clientLogArgument = {
    Message: 'test-message',
  };

  beforeAll(() => {
    mockHandler = jest.fn();
    eventLog = new EventLog({
      handlers: [mockHandler],
      allowedSchemas: allowedSchemas,
    });
    logger = new Logger(eventLog, logSchemas.operationalLogger, initialLogContext);
  });

  afterEach(() => {
    mockHandler.mockClear();
  });

  it('sets the account id and space name for the logger when it is created', () => {
    logger = new Logger(eventLog, logSchemas.operationalLogger, initialLogContext);
    expect(logger.context.AccountId).toBe(CONTEXT_INJECT_PLACEHOLDER);
    expect(logger.context.SpaceName).toBe(CONTEXT_INJECT_PLACEHOLDER);
  });

  it('calls EventLog.recordEvent', () => {
    logger.trace(clientLogArgument);

    const expectedRequestBodyObject = {
      ...clientLogArgument,
      Level: LogLevel.TRACE,
      Context: expectedLogContext,
    };

    expect(mockHandler).toHaveBeenCalledWith(expect.any(EventLog), [
      {
        body: expectedRequestBodyObject,
        // publishTime is automatically added by OSS JupyterLab telemetry plugin
        publishTime: expect.any(Date),
        schema: logSchemas.operationalLogger.schemaId,
        version: logSchemas.operationalLogger.schemaVersion,
      },
    ]);
  });
});
