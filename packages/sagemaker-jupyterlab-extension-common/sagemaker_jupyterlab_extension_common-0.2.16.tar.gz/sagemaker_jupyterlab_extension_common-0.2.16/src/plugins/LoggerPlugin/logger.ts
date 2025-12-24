import { ChildLogContext, ILogger, LogArguments, LogArgumentsContext, LogLevel } from '../../types';
import { CONTEXT_INJECT_PLACEHOLDER, SchemaDefinition } from '../../constants';
import { EventLog } from '@jupyterlab/jupyterlab-telemetry';

class Logger implements ILogger {
  private readonly eventLog: EventLog;
  private readonly context: LogArgumentsContext & ChildLogContext;
  private readonly schema: SchemaDefinition;

  constructor(
    eventlog: EventLog,
    schema: SchemaDefinition,
    context: Omit<LogArgumentsContext, 'AccountId' | 'SpaceName'>,
  ) {
    this.eventLog = eventlog;
    this.schema = schema;
    this.context = {
      ...context,
      // The server extension will be able to inject context including account id and space
      // name if corresponding field is set to '__INJECT__'.
      AccountId: CONTEXT_INJECT_PLACEHOLDER,
      SpaceName: CONTEXT_INJECT_PLACEHOLDER,
    };
  }

  private format(logArguments: LogArguments, level: LogLevel) {
    if ('Error' in logArguments && logArguments.Error !== undefined) {
      const formattedLogArguments = {
        ...logArguments,
        Name: logArguments.Error.name,
        Message: logArguments.Error.message,
        Stack: logArguments.Error.stack,
        Level: level,
        Context: this.context,
      };
      delete logArguments['Error'];
      return formattedLogArguments;
    }

    return {
      ...logArguments,
      Level: level,
      Context: this.context,
    };
  }

  private record(logArguments: LogArguments, level: LogLevel) {
    return this.eventLog.recordEvent({
      version: this.schema.schemaVersion,
      schema: this.schema.schemaId,
      body: this.format(logArguments, level),
    });
  }

  trace = (logArguments: LogArguments) => this.record(logArguments, LogLevel.TRACE);

  debug = (logArguments: LogArguments) => this.record(logArguments, LogLevel.DEBUG);

  info = (logArguments: LogArguments) => this.record(logArguments, LogLevel.INFO);

  warn = (logArguments: LogArguments) => this.record(logArguments, LogLevel.WARN);

  error = (logArguments: LogArguments) => this.record(logArguments, LogLevel.ERROR);

  fatal = (logArguments: LogArguments) => this.record(logArguments, LogLevel.FATAL);

  child = (childContext: ChildLogContext, schema?: SchemaDefinition, eventLog?: EventLog) => {
    const loggerSchema = schema || this.schema;
    const loggerEventLog = eventLog || this.eventLog;
    return new Logger(loggerEventLog, loggerSchema, { ...this.context, ...childContext });
  };
}

export { Logger };
