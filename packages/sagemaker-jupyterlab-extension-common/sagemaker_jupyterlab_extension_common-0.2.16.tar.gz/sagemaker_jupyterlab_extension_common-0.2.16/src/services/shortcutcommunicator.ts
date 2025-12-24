const TOGGLE_COMMAND_PALETTE_MESSAGE = 'MD_TOGGLE_COMMAND_PALETTE';

class ShortcutCommunicator {
  private boundKeyboardListener: (event: KeyboardEvent) => void;

  constructor() {
    this.boundKeyboardListener = this.keyboardListeners.bind(this);
  }

  public initialize() {
    window.addEventListener('keydown', this.boundKeyboardListener);
  }

  public dispose() {
    window.removeEventListener('keydown', this.boundKeyboardListener);
  }

  private keyboardListeners(event: KeyboardEvent) {
    const isMac = navigator.userAgent.toUpperCase().includes('MAC');

    if (
      (isMac ? event.metaKey && !event.ctrlKey : event.ctrlKey && !event.metaKey) &&
      event.key === 'k' &&
      !event.shiftKey &&
      !event.altKey
    ) {
      event.preventDefault();
      window.top?.postMessage(TOGGLE_COMMAND_PALETTE_MESSAGE, '*');
    }
  }
}

export { ShortcutCommunicator };
