import pytest
import unittest
from requests_toolbelt.utils import dump
from requests import Session, exceptions
from unittest.mock import patch, Mock
from src.clients.e2e_token_client import E2ETokenClient

class TestE2eTokenClient(unittest.TestCase):

    e2e_token_client_url = "https://public.nflxe2etokens.prod.netflix.net/REST/v1/tokens/mint/metatron"

    test_app_name = "wall_e"

    @patch('requests_toolbelt.utils.dump.dump_all')
    @patch.object(Session, 'get')
    def test_e2e_token_client_success(self, mock_get, mock_dump_all):
        mock_token = "mock_token"

        mock_get.return_value.status_code = 200
        mock_get.return_value.json.return_value = { "token": mock_token }

        e2eTokenClient = E2ETokenClient()
        resp = e2eTokenClient.get_e2e_token(TestE2eTokenClient.test_app_name)
        self.assertEqual(resp["token"], mock_token)
        mock_get.assert_called_once_with(f"{TestE2eTokenClient.e2e_token_client_url}?targetApp={TestE2eTokenClient.test_app_name}")

    @patch('requests_toolbelt.utils.dump.dump_all')
    @patch.object(Session, 'get')
    def test_e2e_token_client_failure(self, mock_get, mock_dump_all):
        failure_msg = "Simulated error"

        mock_response = Mock()
        mock_response.raise_for_status.side_effect = exceptions.HTTPError(failure_msg)

        mock_get.return_value = mock_response

        e2eTokenClient = E2ETokenClient()
        with pytest.raises(exceptions.HTTPError) as excinfo:
            resp = e2eTokenClient.get_e2e_token(TestE2eTokenClient.test_app_name)
        assert str(excinfo.value) == failure_msg
        mock_get.assert_called_once_with(f"{TestE2eTokenClient.e2e_token_client_url}?targetApp={TestE2eTokenClient.test_app_name}")
