import { JupyterFrontEnd } from '@jupyterlab/application';
import { AppEnvironment } from '../../types';
import { DEFAULT_LANGUAGE_MODEL, UserMetaDataService } from '../usermetadata';
import { MOCK_COOKIE } from './utils.spec';

let userMetadataService: UserMetaDataService;

describe('userMetadataService sm', () => {
  beforeEach(async () => {
    userMetadataService = new UserMetaDataService({} as JupyterFrontEnd);
    userMetadataService['region'] = 'us-west-2';
    jest
      .spyOn(userMetadataService as any, 'postAuthDetails')
      .mockResolvedValue({ isQDeveloperEnabled: true, environment: AppEnvironment.SMStudio });
  });

  afterEach(() => {
    jest.restoreAllMocks();
  });

  it('should not initialize event listener if in sagemaker app environment', async () => {
    jest.spyOn(userMetadataService as any, 'updateMetadata').mockImplementation();

    const addEventListenerSpy = jest.spyOn(window, 'addEventListener');
    userMetadataService.initialize();
    const response = await userMetadataService['postAuthDetails']();
    expect(response?.isQDeveloperEnabled).toBeTruthy();
    expect(addEventListenerSpy).not.toHaveBeenCalled();
  });

  it('app environment is sm if we have accesstoken', async () => {
    const response = await userMetadataService['postAuthDetails']();
    expect(response?.isQDeveloperEnabled).toBeTruthy();
  });
});

describe('userMetadataService non sm', () => {
  beforeEach(async () => {
    userMetadataService = new UserMetaDataService({} as JupyterFrontEnd);
    userMetadataService['region'] = 'us-west-2';
    jest
      .spyOn(userMetadataService as any, 'postAuthDetails')
      .mockResolvedValue({ isQDeveloperEnabled: false, environment: AppEnvironment.MD_IAM });
  });

  afterEach(() => {
    jest.restoreAllMocks();
  });

  it('should be defined', () => {
    expect(userMetadataService).toBeDefined();
    expect(userMetadataService.initialize).toBeDefined();
  });

  it('should add an event listener', async () => {
    const addEventListenerSpy = jest.spyOn(window, 'addEventListener');
    userMetadataService.initialize();
    await userMetadataService['postAuthDetails']();
    expect(addEventListenerSpy).toHaveBeenCalled();
  });

  it("app environment is not sm if we don't have accesstoken", async () => {
    const response = await userMetadataService['postAuthDetails']();
    expect(response?.isQDeveloperEnabled).toBeFalsy();
  });

  it('should short circuit updateInitialLanguageModelConfig if auth mode is IAM', async () => {
    const postAuthDetailsSpy = jest.spyOn(userMetadataService as any, 'postAuthDetails');
    const updateLanguageModelConfigSpy = jest.spyOn(userMetadataService as any, 'updateLanguageModelConfig');
    jest.spyOn(document, 'cookie', 'get').mockReturnValue(MOCK_COOKIE);

    await userMetadataService.updateInitialLanguageModelConfig();

    expect(postAuthDetailsSpy).not.toHaveBeenCalled();
    expect(updateLanguageModelConfigSpy).toHaveBeenCalledWith(DEFAULT_LANGUAGE_MODEL);
  });

  it('should post a message to the parent window that contains JL_COMMON_PLUGIN_LOADED when event listener is added.', async () => {
    const postMessageSpy = jest.spyOn(window, 'postMessage');
    userMetadataService.initialize();
    await userMetadataService['postAuthDetails']();
    expect(postMessageSpy).toHaveBeenCalledWith('JL_COMMON_PLUGIN_LOADED', '*');
  });

  it('isMessageOriginValid should return true if current origin is included in allowed domains (localhost dev example)', async () => {
    jest.spyOn(userMetadataService as any, 'isLocalhost').mockReturnValue(true);
    expect(
      userMetadataService['isMessageOriginValid'](
        new MessageEvent('message', { data: 'test', origin: 'http://localhost:5173' }),
      ),
    ).toEqual(true);
  });

  const domains = [
    ['http://localhost:5173', 'not allowed'],
    ['http://google.com', 'not allowed'],
    ['https://dzd_5tmhoefz7b8g87.sagemaker.us-west-2.on.aws', 'allowed'],
    ['https://dzd_5tmhoefz7b8g87.sagemaker-gamma.us-west-2.on.aws', 'allowed'],
    ['https://dzd_5tmhoefz7b8g87.sagemaker.us-west-2.on.aws.invalid.com', 'not allowed'],
    ['https://dzd_5tmhoefz7b8g87.datazone.us-west-2.on.aws', 'allowed'],
    ['https://dzd_5tmhoefz7b8g87.datazone.us-east-1.on.aws', 'allowed'],
    ['https://dzd_5tmhoefz7b8g87.datazone.ap-southeast-1.on.aws', 'allowed'],
    ['https://dzd_5tmhoefz7b8g87.sagemaker.us-east-1.on.aws', 'allowed'],
    ['https://dzd_5tmhoefz7b8g87.sagemaker.us-east-1.on.aws.org', 'not allowed'],
  ];

  test.each(domains)('%p is %p to post messages to this extension', async (originUrl, expected) => {
    jest.spyOn(userMetadataService as any, 'isLocalhost').mockReturnValue(false);
    expect(
      userMetadataService['isMessageOriginValid'](new MessageEvent('message', { data: 'test', origin: originUrl })),
    ).toEqual(expected === 'allowed');
  });
});
