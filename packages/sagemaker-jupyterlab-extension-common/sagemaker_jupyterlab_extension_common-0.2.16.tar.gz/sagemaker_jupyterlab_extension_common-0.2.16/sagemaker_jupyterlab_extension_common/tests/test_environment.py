import pytest
from unittest.mock import patch, mock_open, AsyncMock

from sagemaker_jupyterlab_extension_common.util.environment import (
    Environment,
    EnvironmentDetector,
)


class TestEnvironmentDetector:
    @pytest.fixture(autouse=True)
    def clear_cache(self):
        """Clear cache before each test"""
        EnvironmentDetector.clear_env_cache()
        yield
        EnvironmentDetector.clear_env_cache()

    @pytest.mark.asyncio
    async def test_unknown_environment_not_cached(self):
        """Test that UNKNOWN environment is not cached and allows retry"""
        with patch.object(
            EnvironmentDetector, "_detect_environment", new_callable=AsyncMock
        ) as mock_detect:
            # First call returns UNKNOWN
            mock_detect.return_value = Environment.UNKNOWN
            result1 = await EnvironmentDetector.get_environment()
            assert result1 == Environment.UNKNOWN
            assert EnvironmentDetector._cached_env is None

            # Second call should retry detection (not use cache)
            mock_detect.return_value = Environment.MD_IAM
            result2 = await EnvironmentDetector.get_environment()
            assert result2 == Environment.MD_IAM
            assert EnvironmentDetector._cached_env == Environment.MD_IAM
            assert mock_detect.call_count == 2

    @pytest.mark.asyncio
    async def test_valid_environment_cached(self):
        """Test that valid environments are cached"""
        with patch.object(
            EnvironmentDetector, "_detect_environment", new_callable=AsyncMock
        ) as mock_detect:
            mock_detect.return_value = Environment.STUDIO_IAM
            result1 = await EnvironmentDetector.get_environment()
            assert result1 == Environment.STUDIO_IAM
            assert EnvironmentDetector._cached_env == Environment.STUDIO_IAM

            # Second call should use cache
            result2 = await EnvironmentDetector.get_environment()
            assert result2 == Environment.STUDIO_IAM
            assert mock_detect.call_count == 1

    @pytest.mark.asyncio
    async def test_all_md_environments_cached(self):
        """Test that all MD environment types are cached"""
        for env in [Environment.MD_IAM, Environment.MD_IDC, Environment.MD_SAML]:
            EnvironmentDetector.clear_env_cache()
            with patch.object(
                EnvironmentDetector, "_detect_environment", new_callable=AsyncMock
            ) as mock_detect:
                mock_detect.return_value = env
                result = await EnvironmentDetector.get_environment()
                assert result == env
                assert EnvironmentDetector._cached_env == env

    @pytest.mark.asyncio
    async def test_studio_environments_cached(self):
        """Test that Studio environment types are cached"""
        for env in [Environment.STUDIO_IAM, Environment.STUDIO_SSO]:
            EnvironmentDetector.clear_env_cache()
            with patch.object(
                EnvironmentDetector, "_detect_environment", new_callable=AsyncMock
            ) as mock_detect:
                mock_detect.return_value = env
                result = await EnvironmentDetector.get_environment()
                assert result == env
                assert EnvironmentDetector._cached_env == env

    @pytest.mark.asyncio
    async def test_multiple_unknown_calls_keep_retrying(self):
        """Test that multiple UNKNOWN results keep retrying without caching"""
        with patch.object(
            EnvironmentDetector, "_detect_environment", new_callable=AsyncMock
        ) as mock_detect:
            mock_detect.return_value = Environment.UNKNOWN

            result1 = await EnvironmentDetector.get_environment()
            assert result1 == Environment.UNKNOWN
            assert EnvironmentDetector._cached_env is None

            result2 = await EnvironmentDetector.get_environment()
            assert result2 == Environment.UNKNOWN
            assert EnvironmentDetector._cached_env is None

            result3 = await EnvironmentDetector.get_environment()
            assert result3 == Environment.UNKNOWN
            assert EnvironmentDetector._cached_env is None

            assert mock_detect.call_count == 3

    @pytest.mark.asyncio
    async def test_unknown_then_valid_eventually_caches(self):
        """Test race condition: UNKNOWN → UNKNOWN → Valid eventually caches"""
        with patch.object(
            EnvironmentDetector, "_detect_environment", new_callable=AsyncMock
        ) as mock_detect:
            mock_detect.side_effect = [
                Environment.UNKNOWN,
                Environment.UNKNOWN,
                Environment.MD_IAM,
            ]

            result1 = await EnvironmentDetector.get_environment()
            assert result1 == Environment.UNKNOWN
            assert EnvironmentDetector._cached_env is None

            result2 = await EnvironmentDetector.get_environment()
            assert result2 == Environment.UNKNOWN
            assert EnvironmentDetector._cached_env is None

            result3 = await EnvironmentDetector.get_environment()
            assert result3 == Environment.MD_IAM
            assert EnvironmentDetector._cached_env == Environment.MD_IAM

            # Fourth call uses cache
            result4 = await EnvironmentDetector.get_environment()
            assert result4 == Environment.MD_IAM
            assert mock_detect.call_count == 3

    @pytest.mark.asyncio
    async def test_clear_cache_allows_redetection(self):
        """Test that clearing cache allows environment redetection"""
        with patch.object(
            EnvironmentDetector, "_detect_environment", new_callable=AsyncMock
        ) as mock_detect:
            mock_detect.return_value = Environment.STUDIO_IAM
            result1 = await EnvironmentDetector.get_environment()
            assert result1 == Environment.STUDIO_IAM
            assert mock_detect.call_count == 1

            EnvironmentDetector.clear_env_cache()
            assert EnvironmentDetector._cached_env is None

            mock_detect.return_value = Environment.MD_IDC
            result2 = await EnvironmentDetector.get_environment()
            assert result2 == Environment.MD_IDC
            assert mock_detect.call_count == 2

    def test_is_smai_environment_with_studio_iam_cached(self):
        """Test is_smai_environment returns True when STUDIO_IAM is cached"""
        EnvironmentDetector._cached_env = Environment.STUDIO_IAM
        assert EnvironmentDetector.is_smai_environment() is True

    def test_is_smai_environment_with_studio_sso_cached(self):
        """Test is_smai_environment returns True when STUDIO_SSO is cached"""
        EnvironmentDetector._cached_env = Environment.STUDIO_SSO
        assert EnvironmentDetector.is_smai_environment() is True

    def test_is_smai_environment_with_non_smai_cached(self):
        """Test is_smai_environment returns False for non-SMAI environments"""
        for env in [
            Environment.MD_IAM,
            Environment.MD_IDC,
            Environment.MD_SAML,
            Environment.UNKNOWN,
        ]:
            EnvironmentDetector._cached_env = env
            assert EnvironmentDetector.is_smai_environment() is False

    def test_is_smai_environment_no_cache_studio_metadata(self):
        """Test is_smai_environment returns True when metadata indicates Studio"""
        metadata = '{"ResourceArn": "arn:aws:sagemaker:us-west-2:123456789012:app/d-123/user/app", "DomainId": "d-123"}'
        with patch("builtins.open", mock_open(read_data=metadata)):
            result = EnvironmentDetector.is_smai_environment()
            assert result is True

    def test_is_smai_environment_no_cache_md_metadata(self):
        """Test is_smai_environment returns False when metadata indicates MD"""
        metadata = '{"ResourceArn": "arn:aws:sagemaker:us-west-2:123456789012:app/d-123/user/app", "AdditionalMetadata": {"DataZoneScopeName": "test"}}'
        with patch("builtins.open", mock_open(read_data=metadata)):
            result = EnvironmentDetector.is_smai_environment()
            assert result is False

    def test_is_smai_environment_no_cache_file_error(self):
        """Test is_smai_environment returns False when file cannot be read"""
        with patch("builtins.open", side_effect=FileNotFoundError()):
            result = EnvironmentDetector.is_smai_environment()
            assert result is False
