import React, { useEffect } from 'react';
import styles from './styles';
import { i18nStrings } from '../../constants';
import { getShortbread, loadShortbreadScript } from '../../services/shortbread';

const ShortBreadComponent = () => {
  useEffect(() => {
    loadShortbreadScript();
  }, []);

  const customizeCookies = () => {
    const shortbread = getShortbread();

    if (shortbread) {
      shortbread.customizeCookies();
    }
  };

  return (
    <div className={styles.ShortBreadFooter}>
      <span onClick={customizeCookies} style={{ cursor: 'pointer' }}>
        {i18nStrings.ShortBread.CookiePreferences}
      </span>
    </div>
  );
};

export { ShortBreadComponent };
