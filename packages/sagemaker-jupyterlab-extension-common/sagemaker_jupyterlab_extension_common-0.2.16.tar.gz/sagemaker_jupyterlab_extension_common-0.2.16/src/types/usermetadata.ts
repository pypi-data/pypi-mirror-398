interface UserMetaData {
  accessToken: string;
  profileArn?: string;
  enabledFeatures?: string[];
  qSettings?: QSettings;
}

interface QSettings {
  auth_mode: AuthMode;
  q_enabled: boolean;
}

enum AuthMode {
  IAM = 'IAM',
  SSO = 'IDC',
  SAML = 'SAML',
}

interface AccessToken {
  idc_access_token: string;
}

interface QDevProfile {
  q_dev_profile_arn: string;
}

interface EnabledFeatures {
  enabled_features: string[];
}

enum AppEnvironment {
  SMStudio = 'SageMaker Studio',
  SMStudioSSO = 'SageMaker Studio SSO',
  MD_IAM = 'MD_IAM',
  MD_IDC = 'MD_IDC',
  MD_SAML = 'MD_SAML',
}

interface LanguageModelConfig {
  model_provider_id?: string | null;
}

interface AuthDetailsOutput {
  isQDeveloperEnabled: boolean;
  environment: AppEnvironment;
}

export {
  UserMetaData,
  AccessToken,
  QDevProfile,
  EnabledFeatures,
  QSettings,
  AppEnvironment,
  AuthMode,
  LanguageModelConfig,
  AuthDetailsOutput,
};
