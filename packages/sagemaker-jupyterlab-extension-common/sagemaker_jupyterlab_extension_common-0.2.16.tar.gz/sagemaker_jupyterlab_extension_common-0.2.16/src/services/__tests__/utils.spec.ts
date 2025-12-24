import { getCookie } from '../utils';

export const MOCK_COOKIE =
  '_xsrf=2|259aaae6|c3282d57f810271958aa3a896ab7b6e0|1733183843; awsccc=eyJlIjoxLCJwIjoxLCJmIjoxLCJhIjoxLCJpIjoiMTFmYjViMzAtMjU0Zi00Yzg4LTliZDMtZGE5YzVkZjE0YzcyIiwidiI6IjEifQ==; authMode=Iam; redirectURL=https://us-west-2.console.aws.amazon.com/sagemaker/home?region=us-west-2#/studio/open/d-aivzjgylajco/gg; studioUserProfileName=gg; expiryTime=1735039822000';

describe('getCookie', () => {
  it('read the cookie value correctly', () => {
    jest.spyOn(document, 'cookie', 'get').mockReturnValue(MOCK_COOKIE);

    const authMode = getCookie('authMode');
    expect(authMode).toBe('Iam');

    const nonExistantCookie = getCookie('nonExistantCookieKey');
    expect(nonExistantCookie).toBeUndefined();
  });
});
