const loadShortbreadScript = () => {
  const script = document.createElement('script');
  script.src = 'https://prod.assets.shortbread.aws.dev/shortbread.js';
  script.type = 'text/javascript';
  script.async = true;
  document.head.appendChild(script);
  script.onload = () => ((window as any).AWSCShortbreadInstance = initialShortbread());

  const link = document.createElement('link');
  link.href = 'https://prod.assets.shortbread.aws.dev/shortbread.css';
  link.rel = 'stylesheet';
  // Make CSS non-blocking
  link.media = 'none';
  link.onload = () => (link.media = 'all');
  link.onerror = () => (link.media = 'all');
  document.head.appendChild(link);
};

const getShortbread = () => (window as any).AWSCShortbreadInstance;

const initialShortbread = () => {
  const shortbread = (window as any).AWSCShortbread({
    domain: window.location.hostname,
    hasConsoleNavFooter: true,
  });
  shortbread.checkForCookieConsent();
  return shortbread;
};

export { loadShortbreadScript, getShortbread };
