import { css } from '@emotion/css';

const StatusBarWidget = css`
  color: red;
  height: 100%;
  display: flex;
  flex-flow: row;
  align-items: center;
`;

const DialogBox = css`
  font-size: var(--jp-content-font-size1);
  line-height: var(--jp-content-line-height);
  max-width: 30rem;
`;

const DialogTitle = css`
  display: flex;
  flex-flow: row;
  justify-content: center;
`;

const DialogAlertIcon = css`
  padding-left: 0.25em;
  padding-right: 0.5em;
  display: inline;
  color: red;

  svg {
    width: var(--jp-ui-font-size2);
    height: var(--jp-ui-font-size2);
  }
`;

const StatusBarAlertIcon = css`
  padding-top: 0.25em;
  padding-right: 0.5em;
  display: inline;
  color: red;

  svg {
    width: var(--jp-ui-font-size2);
    height: var(--jp-ui-font-size2);
  }
`;

export { StatusBarWidget, DialogBox, DialogTitle, DialogAlertIcon, StatusBarAlertIcon };
