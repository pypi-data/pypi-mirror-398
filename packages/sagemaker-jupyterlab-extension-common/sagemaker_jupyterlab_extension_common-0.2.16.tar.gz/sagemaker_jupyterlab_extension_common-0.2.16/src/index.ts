import {
  DeepLinkingPlugin,
  PanoramaPlugin,
  QDeveloperPlugin,
  CommandPalettePlugin,
  RecoveryModePlugin,
} from './plugins';
import { ILogger, logSchemas, LoggerPlugin, SchemaDefinition } from './plugins';

export { ILogger, logSchemas, SchemaDefinition };
export default [
  PanoramaPlugin,
  LoggerPlugin,
  DeepLinkingPlugin,
  QDeveloperPlugin,
  CommandPalettePlugin,
  RecoveryModePlugin,
];
