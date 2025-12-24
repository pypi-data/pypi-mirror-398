const pluginIds = {
  PanoramaPlugin: '@amzn/sagemaker-jupyterlab-extension-common:panorama',
  LoggerPlugin: '@amzn/sagemaker-jupyterlab-extension-common:logger',
  JumpStartDeeplinkingPlugin: '@amzn/sagemaker-jupyterlab-extension-common:jumpstart-deeplinking',
  JumpStartLoggerPlugin: '@amzn/sagemaker-jupyterlab-extension-common:jumpstart-logger',
  QDeveloperPlugin: '@amzn/sagemaker-jupyterlab-extension-common:q-developer',
  CommandPalettePlugin: '@amzn/sagemaker-jupyterlab-extension-common:command-palette',
};

const widgetIds = {
  shortBreadStatus: '@amzn/sagemaker-jupyterlab-extension-common:widget:shortbread-status',
};

export const EXTENSION_ID = '@amzn/sagemaker-jupyterlab-extension-common';

export { pluginIds, widgetIds };
