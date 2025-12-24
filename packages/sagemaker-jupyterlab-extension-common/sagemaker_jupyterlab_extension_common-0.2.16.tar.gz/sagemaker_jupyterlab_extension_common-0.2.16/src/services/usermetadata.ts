import { JupyterFrontEnd, LabShell } from '@jupyterlab/application';
import {
  Q_DEVELOPER_CODE_COMPLETIONS_CACHE_ENDPOINT,
  SAGEMAKER_AUTH_DETAILS_ENDPOINT,
  SAGEMAKER_CLEAR_CACHE_ENDPOINT,
  SAGEMAKER_AI_CONFIG_ENDPOINT as SAGEMAKER_LANGUAGE_MODEL_CONFIG_ENDPOINT,
} from '../constants';
import {
  AccessToken,
  AppEnvironment,
  AuthDetailsOutput,
  LanguageModelConfig,
  QDevProfile,
  UserMetaData,
  EnabledFeatures,
  AuthMode,
  QSettings,
} from '../types/usermetadata';
import { OPTIONS_TYPE, fetchApiResponse } from './fetchapi';
import wcmatch from 'wildcard-match';
import { getCookie } from './utils';

const ENDPOINT = 'api/contents';
const PLUGIN_LOADED_MESSAGE = 'JL_COMMON_PLUGIN_LOADED';
const TOGGLE_AI_CHAT_MESSAGE = 'MD_TOGGLE_AI_CHAT';
const AWS_DIRECTORY = '.aws';
const SSO_DIRECTORY = AWS_DIRECTORY + '/sso';
const Q_PROFILE_DIRECTORY = AWS_DIRECTORY + '/amazon_q';
const ENABLED_FEATURES_DIRECTORY = AWS_DIRECTORY + '/enabled_features';
const MD_ENVIRONMENT_LOADED_MESSAGE = 'MD_ENVIRONMENT_LOADED';

export const DEFAULT_LANGUAGE_MODEL = 'amazon-q:Q-Developer';

const SM_INTERVAL_TIME = 5 * 60 * 1000; // 5 minutes

class UserMetaDataService {
  private smInterval: NodeJS.Timeout | undefined;

  constructor(private app: JupyterFrontEnd) {}

  public async initialize() {
    const details = await this.postAuthDetails();
    if (details?.environment === AppEnvironment.SMStudioSSO) {
      if (details.isQDeveloperEnabled) {
        this.initializeSMInterval();
      }
    } else if (details?.environment && this.isMD(details.environment)) {
      this.initializeTwoWayIframeCommunication();
    }
  }

  private async initializeSMInterval(): Promise<void> {
    if (!this.smInterval) {
      this.smInterval = setInterval(async () => {
        await this.postAuthDetails();
      }, SM_INTERVAL_TIME);
    }
  }

  private async updateMetadata(metadata: UserMetaData) {
    await this.createDirectoryIfDoesNotExist(AWS_DIRECTORY, '.aws');
    await this.createDirectoryIfDoesNotExist(SSO_DIRECTORY, 'sso');
    await this.createDirectoryIfDoesNotExist(Q_PROFILE_DIRECTORY, 'amazon_q');
    await this.createDirectoryIfDoesNotExist(ENABLED_FEATURES_DIRECTORY, 'enabled_features');

    await this.putMetadataFile(SSO_DIRECTORY, 'idc_access_token', 'json', { idc_access_token: metadata.accessToken });

    await this.putMetadataFile(Q_PROFILE_DIRECTORY, 'q_dev_profile', 'json', {
      q_dev_profile_arn: metadata.profileArn ?? '',
    });

    await this.putMetadataFile(Q_PROFILE_DIRECTORY, 'settings', 'json', {
      auth_mode: metadata.qSettings?.auth_mode ?? AuthMode.IAM,
      q_enabled: metadata.qSettings?.q_enabled ?? false,
    });

    await this.putMetadataFile(ENABLED_FEATURES_DIRECTORY, 'enabled_features', 'json', {
      enabled_features: metadata.enabledFeatures ?? [],
    });

    // clear environment cache in case the environment has changed.
    await fetchApiResponse(SAGEMAKER_CLEAR_CACHE_ENDPOINT, OPTIONS_TYPE.POST);
    // clear environment cache in Q developer code completions extension
    await fetchApiResponse(Q_DEVELOPER_CODE_COMPLETIONS_CACHE_ENDPOINT, OPTIONS_TYPE.POST);
    window.postMessage(MD_ENVIRONMENT_LOADED_MESSAGE);
  }

  public async updateInitialLanguageModelConfig(): Promise<void> {
    const authMode = getCookie('authMode')?.toUpperCase();
    const config = await this.getLanguageModelConfig();
    if (authMode === 'IAM') {
      // in IAM mode, if no model is selected update to Q
      if (!config?.model_provider_id) {
        await this.updateLanguageModelConfig(DEFAULT_LANGUAGE_MODEL);
      }
      return;
    }

    const details = await this.postAuthDetails();
    if (details?.environment === AppEnvironment.SMStudioSSO) {
      // in SSO mode, if Q Developer is enabled and Q is not selected update to Q
      // in SSO mode, if Q Developer is not enabled and no model is selected update to Q
      if (details.isQDeveloperEnabled) {
        if (config?.model_provider_id !== DEFAULT_LANGUAGE_MODEL) {
          await this.updateLanguageModelConfig(DEFAULT_LANGUAGE_MODEL);
        }
      } else {
        if (!config?.model_provider_id) {
          await this.updateLanguageModelConfig(DEFAULT_LANGUAGE_MODEL);
        }
      }
    } else if (details?.environment && this.isMD(details.environment)) {
      if (!config?.model_provider_id) {
        await this.updateLanguageModelConfig(DEFAULT_LANGUAGE_MODEL);
      }
    }
  }

  private async getLanguageModelConfig(): Promise<LanguageModelConfig | undefined> {
    try {
      const response = await fetchApiResponse(SAGEMAKER_LANGUAGE_MODEL_CONFIG_ENDPOINT, OPTIONS_TYPE.GET);
      return (await response.json()) as LanguageModelConfig;
    } catch {
      return undefined;
    }
  }

  private async updateLanguageModelConfig(modelProviderId: string | null): Promise<void> {
    try {
      await fetchApiResponse(
        SAGEMAKER_LANGUAGE_MODEL_CONFIG_ENDPOINT,
        OPTIONS_TYPE.POST,
        JSON.stringify({
          model_provider_id: modelProviderId,
        }),
      );
    } catch {
      return undefined;
    }
  }

  private async postAuthDetails(): Promise<AuthDetailsOutput | undefined> {
    try {
      const response = await fetchApiResponse(SAGEMAKER_AUTH_DETAILS_ENDPOINT, OPTIONS_TYPE.POST);
      return (await response.json()) as AuthDetailsOutput;
    } catch {
      return undefined;
    }
  }

  private async getDirectory(path: string, returnContent?: boolean): Promise<Response | undefined> {
    try {
      return await fetchApiResponse(`${ENDPOINT}/${path}?content=${returnContent ? 1 : 0}`, OPTIONS_TYPE.GET);
    } catch {
      return undefined;
    }
  }

  private putDirectory = async (path: string, name: string): Promise<Response> =>
    await fetchApiResponse(
      `${ENDPOINT}/${path}`,
      OPTIONS_TYPE.PUT,
      JSON.stringify({ type: 'directory', format: 'text', name }),
    );

  private isMessageOriginValid = (event: MessageEvent) => {
    const allowedDomainPatterns = [
      'https://**.v2.*.beta.app.*.aws.dev',
      'https://**.ui.*.aws.dev',
      'https://**.v2.*-gamma.*.on.aws',
      'https://**.datazone.*.on.aws',
      'https://**.sagemaker.*.on.aws',
      'https://**.sagemaker-gamma.*.on.aws',
    ];
    return this.isLocalhost()
      ? event.origin === 'http://localhost:5173'
      : allowedDomainPatterns.some((pattern) => wcmatch(pattern)(event.origin));
  };

  private putMetadataFile = async (
    path: string,
    name: string,
    ext: string,
    content: AccessToken | QDevProfile | EnabledFeatures | QSettings,
  ): Promise<Response> =>
    await fetchApiResponse(
      `${ENDPOINT}/${path ? `${path}/${name}.${ext}` : `/${name}.${ext}`}`,
      OPTIONS_TYPE.PUT,
      JSON.stringify({
        content: JSON.stringify(content),
        format: 'text',
        name: `${name}.${ext}`,
        type: 'file',
      }),
    );

  /**
   * Send a message to the parent window when the plugin is ready to receive user metadata.
   * NOTE: since this message is sent using an unrestricted domain origin, do not pass any sensitive
   * information using this method. This is strictly for handshaking.
   */
  private sendMessageWhenReadyToReceiveUserMetadata(): void {
    window.top?.postMessage(PLUGIN_LOADED_MESSAGE, '*');
  }

  private messageListener = async (event: MessageEvent): Promise<void> => {
    if (!this.isMessageOriginValid(event)) return;

    /**
     * When a Q toggle event is passed into the iframe from the parent,
     * this toggles visibility of the Q chat window.
     */
    if (event.data === TOGGLE_AI_CHAT_MESSAGE) {
      this.toggleAIChat(this.app);
      return;
    }

    try {
      const metadata = JSON.parse(event.data) as UserMetaData;

      if (!('accessToken' in metadata)) throw new Error('IAM Identity Center access token not found.');

      this.updateMetadata(metadata);
    } catch (err) {
      // create notification service to post error notification in UI.
    }
  };

  private async createDirectoryIfDoesNotExist(path: string, name: string) {
    const exists = await this.getDirectory(path, false);
    if (!exists) {
      await this.putDirectory(path, name);
    }
  }

  private isLocalhost() {
    return ['localhost', '127.0.0.1'].some((condition) => document.location.href.includes(condition));
  }

  private isMD(environment: AppEnvironment): boolean {
    return [AppEnvironment.MD_IAM, AppEnvironment.MD_IDC, AppEnvironment.MD_SAML].includes(environment);
  }

  /**
   * This method adds an event listener for listening to messages from the parent window
   * and sends a message to the parent window when the message listener has been added.
   * This prevents messages from the parent window from being sent before the plugin has been loaded.
   */
  private initializeTwoWayIframeCommunication(): void {
    window.addEventListener('message', this.messageListener);
    this.sendMessageWhenReadyToReceiveUserMetadata();
  }

  /**
   * Controls showing and hiding of Q window programmatically.
   */
  private toggleAIChat(app: JupyterFrontEnd): void {
    const JUPYTER_AI_CHAT_WIDGET_ID = 'jupyter-ai::chat';
    if (app.shell instanceof LabShell) {
      const leftWidgets = Array.from(app.shell.widgets('left'));
      const rightWidgets = Array.from(app.shell.widgets('right'));
      const widgets = [...leftWidgets, ...rightWidgets];
      const chatWidget = widgets.find((widget) => widget.id === JUPYTER_AI_CHAT_WIDGET_ID);

      if (chatWidget) {
        if (chatWidget.isHidden) {
          app.shell.activateById(JUPYTER_AI_CHAT_WIDGET_ID);
        } else {
          if (rightWidgets.find((widget) => widget.id === JUPYTER_AI_CHAT_WIDGET_ID)) {
            app.shell.collapseRight();
          } else {
            app.shell.collapseLeft();
          }
        }
      }
    }
  }
}

export { UserMetaDataService };
