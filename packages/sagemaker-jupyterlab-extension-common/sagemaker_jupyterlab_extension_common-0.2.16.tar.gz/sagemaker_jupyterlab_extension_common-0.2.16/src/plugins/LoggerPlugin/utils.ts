import { v4 as uuidv4 } from 'uuid';

interface ISession {
  id: string;
  startTime: string;
}

const getSession = (key: string): ISession => {
  const stored = window.sessionStorage.getItem(key);
  let session: ISession;
  if (stored == null) {
    session = {
      id: uuidv4(),
      startTime: new Date().toISOString(),
    };
    window.sessionStorage.setItem(key, JSON.stringify(session));
  } else {
    session = JSON.parse(stored);
  }

  return session;
};

export { getSession, ISession };
