/* eslint-disable no-console */
import retry from 'p-retry';
import { Slot } from '@lumino/signaling';
import { ServerConnection } from '@jupyterlab/services';
import { PageConfig } from '@jupyterlab/coreutils';
import { EventLog } from '@jupyterlab/jupyterlab-telemetry';

const sendEvents = (events: EventLog.IRecordedEvent[], retries: number, endpoint_url: string) => {
  const baseUrl = PageConfig.getBaseUrl();
  const url = `${baseUrl}${endpoint_url}`;
  const settings = ServerConnection.makeSettings({ baseUrl });
  const options = {
    method: 'POST',
    body: JSON.stringify({ events }),
  };

  const retryable = async () => {
    let response: Response;
    try {
      response = await ServerConnection.makeRequest(url, options, settings);
    } catch (error) {
      // p-retry won't attempt a retry if the error encountered is a TypeError. fetch throws a TypeError when a network
      // error occurs which means that we won't retry sending events on a network error that could be transient even if
      // a subsequent retry could succeed.
      // https://github.com/sindresorhus/p-retry/issues/37
      if (error instanceof TypeError) {
        Object.setPrototypeOf(error, Error.prototype);
      }
      throw error;
    }
    if (!response.ok) {
      throw new Error(response.statusText);
    }
  };

  const onFailedAttempt = (error: any) => {
    console.warn({
      message: `Deliver events attempt (${error.attemptNumber}) with (${error.retriesLeft}) retries remaining.`,
      error,
    });
  };

  const retryableOptions = {
    retries,
    onFailedAttempt,
  };

  return retry(retryable, retryableOptions).catch((error) => {
    console.error({
      message: `Failed to deliver events after (${retryableOptions.retries}) retries.`,
      error,
      events,
    });
  });
};

type Handler = Slot<EventLog, EventLog.IRecordedEvent[]>;

const makeRemoteHandler = (
  retries: number,
  flushIntervalInMS: number,
  maxBufferSize: number,
  endpoint: string,
): Handler => {
  const eventBuffer: EventLog.IRecordedEvent[] = [];

  const flushBuffer = () => {
    const recordedEvents = eventBuffer.splice(0);
    sendEvents(recordedEvents, retries, endpoint);
  };

  setInterval(flushBuffer, flushIntervalInMS);

  return (eventLog, recordedEvents) => {
    // Discard newest recorded events if additional events would exceed the max buffer size.
    const remaining = maxBufferSize - eventBuffer.length;
    eventBuffer.push(...recordedEvents.slice(0, remaining));

    if (recordedEvents.length > remaining) {
      flushBuffer();
      // TODO: connect this with a signal, and emit the error in a separate Logger
      console.log('Logger plugin max buffer size exceeded.');
    }
  };
};

export { makeRemoteHandler };
