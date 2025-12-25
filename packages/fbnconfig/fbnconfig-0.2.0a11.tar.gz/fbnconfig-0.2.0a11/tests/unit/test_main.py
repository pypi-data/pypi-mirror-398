import os
import textwrap
from unittest.mock import Mock, patch

import httpx
import pytest
from click.testing import CliRunner

from fbnconfig import main

log_entity = "deployment"


class DescribeRun:
    @patch.dict(os.environ, {"FBN_ACCESS_TOKEN": "xxxxx"})
    @pytest.mark.respx(base_url="https://foo.lusid.com")
    def test_handles_http_exceptions(self, respx_mock):
        # given a config script that does not deploy any resources
        # (it will only call the log endpoint)
        script = textwrap.dedent("""\
            from fbnconfig import Deployment
            def configure(env):
                return Deployment('test1', [])
        """)
        runner = CliRunner()
        # and the log endpoint which returns 500
        respx_mock.get(f"/api/api/customentities/~{log_entity}").mock(
            return_value=httpx.Response(500, json={})
        )
        with runner.isolated_filesystem():
            with open("script.py", "w") as f:
                f.write(script)
            # when we run the cli with the script
            result = runner.invoke(
                main.cli, ["run", "-e", "https://foo.lusid.com", "-t", "xxxxyyy", "script.py"]
            )
            # then the exit code is failure
            assert result.exit_code == 1, result.output
            # and the 500 is reported to the console
            assert "The server responded with 500" in result.output

    @patch.dict(os.environ, {"FBN_ACCESS_TOKEN": "xxxxx"})
    @pytest.mark.respx(base_url="https://foo.lusid.com")
    def test_handles_invalid_token_http_exceptions(self, respx_mock):
        # given a config script that does not deploy any resources
        # (it will only call the log endpoint)
        script = textwrap.dedent("""\
                from fbnconfig import Deployment
                def configure(env):
                    return Deployment('test1', [])
            """)
        runner = CliRunner()
        # and the log endpoint which returns 401 due to invalid token
        respx_mock.get(f"/api/api/customentities/~{log_entity}").mock(
            return_value=httpx.Response(401, json={})
        )
        with runner.isolated_filesystem():
            with open("script.py", "w") as f:
                f.write(script)
            # when we run the cli with the script
            result = runner.invoke(
                main.cli, ["run", "-e", "https://foo.lusid.com", "-t", "xxxxyyy", "script.py"]
            )
            # then the exit code is failure
            assert result.exit_code == 1, result.output
            # and the 401 is reported to the console
            assert "The server responded with 401" in result.output
            assert "Unauthorized" in result.output
            assert "the provided access token" in result.output

    @patch.dict(os.environ, {"FBN_ACCESS_TOKEN": "xxxxx"})
    @pytest.mark.respx(base_url="https://foo.lusid.com")
    def test_handles_http_exceptions_with_404_detail(self, respx_mock):
        # given a config script that does not deploy any resources
        # (it will only call the log endpoint)
        script = textwrap.dedent("""\
               from fbnconfig import Deployment
               def configure(env):
                   return Deployment('test1', [])
           """)
        runner = CliRunner()
        # and the log endpoint which returns 404
        respx_mock.get(f"/api/api/customentities/~{log_entity}").mock(
            return_value=httpx.Response(404, json={"detail": "Some message"})
        )
        with runner.isolated_filesystem():
            with open("script.py", "w") as f:
                f.write(script)
            # when we run the cli with the script
            result = runner.invoke(
                main.cli, ["run", "-e", "https://foo.lusid.com", "-t", "xxxxyyy", "script.py"]
            )
            # then the exit code is failure
            assert result.exit_code == 1, result.output
            # and the detail message is reported to the console
            assert "Some message" in result.output

    @patch.dict(os.environ, {"FBN_ACCESS_TOKEN": "xxxxx"})
    @pytest.mark.respx(base_url="https://foo.lusid.com")
    def test_handles_access_denied_exceptions(self, respx_mock):
        # given a config script that does not deploy any resources
        # (it will only call the log endpoint)
        script = textwrap.dedent("""\
                    from fbnconfig import Deployment
                    def configure(env):
                        return Deployment('test1', [])
                """)
        runner = CliRunner()
        # and the log endpoint which returns 401 due to invalid token
        respx_mock.get(f"/api/api/customentities/~{log_entity}").mock(
            return_value=httpx.Response(
                403,
                json={
                    "name": "AccessDenied",
                    "errorDetails": [],
                    "status": 403,
                    "detail": "Access to perform the requested action cannot "
                    "be granted due to insufficient privileges. "
                    "Please contact your organisation's "
                    "administrator.",
                    "instance": "https://foo.lusid.com" "/app/insights/logs/0AB123:001A",
                },
            )
        )
        with runner.isolated_filesystem():
            with open("script.py", "w") as f:
                f.write(script)
            # when we run the cli with the script
            result = runner.invoke(
                main.cli, ["run", "-e", "https://foo.lusid.com", "-t", "xxxxyyy", "script.py"]
            )
            # then the exit code is failure
            assert result.exit_code == 1, result.output
            # and the 403 is reported to the console
            assert "The server responded with 403" in result.output
            assert (
                "Access to perform the requested action cannot be "
                "granted due to insufficient privileges"
            ) in result.output

    @patch.dict(os.environ, {"FBN_ACCESS_TOKEN": "xxxxx"})
    @patch("fbnconfig.log.list_resources_for_deployment", return_value=[])
    def test_loads_module(self, mock_log):
        script = textwrap.dedent("""\
            from fbnconfig import Deployment
            def configure(env):
                return Deployment('test1', [])
        """)
        runner = CliRunner()
        with runner.isolated_filesystem():
            with open("script.py", "w") as f:
                f.write(script)
            result = runner.invoke(
                main.cli, ["run", "-e", "https://foo.lusid.com", "-t", "xxxxyyy", "script.py"]
            )
            assert result.exit_code == 0, result.output
            assert len(mock_log.mock_calls) == 1

    @patch.dict(os.environ, {"FBN_ACCESS_TOKEN": "xxxxx"})
    @patch("fbnconfig.log.list_resources_for_deployment", return_value=[])
    def test_loads_module_subfolder(self, mock_log):
        script = textwrap.dedent("""\
            from fbnconfig import Deployment
            def configure(env):
                return Deployment('test1', [])
        """)
        runner = CliRunner()
        with runner.isolated_filesystem():
            os.mkdir("subfolder")
            with open("subfolder/script.py", "w") as f:
                f.write(script)
            result = runner.invoke(
                main.cli, ["run", "-e", "https://foo.lusid.com", "-t", "xxxxyyy", "subfolder/script.py"]
            )
            assert result.exit_code == 0, result.output
            assert len(mock_log.mock_calls) == 1

    @patch.dict(os.environ, {"FBN_ACCESS_TOKEN": "xxxxx"})
    @patch("fbnconfig.log.list_resources_for_deployment", return_value=[])
    def test_error_module_syntax_error(self, mock_log):
        # given a config with a syntax error
        script = textwrap.dedent("""\
            from fbnconfig import NOT_EXISTS
            def configure(env):
                return Deployment('test1', [])
        """)
        runner = CliRunner()
        with runner.isolated_filesystem():
            with open("script.py", "w") as f:
                f.write(script)
            # when we try to run it
            result = runner.invoke(
                main.cli, ["run", "-e", "https://foo.lusid.com", "-t", "xxxxyyy", "script.py"]
            )
            # it fails
            assert result.exit_code == 1, result.output
            # and prints an explantion
            assert "Failed importing" in result.output

    @patch.dict(os.environ, {"FBN_ACCESS_TOKEN": "xxxxx"})
    @patch("fbnconfig.log.list_resources_for_deployment", return_value=[])
    def test_error_module_no_configure_func(self, mock_log):
        # given a config without a configure function
        script = textwrap.dedent("""\
            from fbnconfig import Deployment
            def not_the_configure(env):
                return Deployment('test1', [])
        """)
        runner = CliRunner()
        with runner.isolated_filesystem():
            with open("script.py", "w") as f:
                f.write(script)
            # when we try to run it
            result = runner.invoke(
                main.cli, ["run", "-e", "https://foo.lusid.com", "-t", "xxxxyyy", "script.py"]
            )
            # it fails
            assert result.exit_code == 1, result.output
            # and prints the reason
            assert "No configure function" in result.output

    @patch.dict(os.environ, {"FBN_ACCESS_TOKEN": "xxxxx"})
    @patch("fbnconfig.log.list_resources_for_deployment", return_value=[])
    def test_loads_module_with_import(self, mock_log):
        # given script imports subscript from the same folder
        script = textwrap.dedent("""\
            from fbnconfig import Deployment
            import subscript
            def configure(env):
                grant = subscript.foo()
                return Deployment('test1', [])
        """)
        subscript = textwrap.dedent("""\
            from fbnconfig import access
            def foo():
                return access.Grant.ALLOW
        """)
        runner = CliRunner()
        with runner.isolated_filesystem():
            with open("script.py", "w") as f:
                f.write(script)
            with open("subscript.py", "w") as f:
                f.write(subscript)
            # when we run the cli
            result = runner.invoke(
                main.cli, ["run", "-e", "https://foo.lusid.com", "-t", "xxxxyyy", "script.py"]
            )
            # then it passes showing the import worked
            assert result.exit_code == 0, result.output
            assert len(mock_log.mock_calls) == 1

    @patch.dict(os.environ, {"FBN_ACCESS_TOKEN": "xxxxx"})
    @patch("fbnconfig.log.list_resources_for_deployment", return_value=[])
    def test_loads_module_with_folder_import(self, mock_log):
        # given script imports subscript from another folder
        script = textwrap.dedent("""\
            from fbnconfig import Deployment
            from folder import subscript
            def configure(env):
                grant = subscript.foo()
                return Deployment('test1', [])
        """)
        subscript = textwrap.dedent("""\
            from fbnconfig import access
            def foo():
                return access.Grant.ALLOW
        """)
        runner = CliRunner()
        with runner.isolated_filesystem():
            os.mkdir("folder")
            with open("script.py", "w") as f:
                f.write(script)
            with open("folder/subscript.py", "w") as f:
                f.write(subscript)
            # when we run the cli
            result = runner.invoke(
                main.cli, ["run", "-e", "https://foo.lusid.com", "-t", "xxxxyyy", "script.py"]
            )
            # the import works
            assert result.exit_code == 0, result.output
            assert len(mock_log.mock_calls) == 1


class DescribeSetup:
    @patch("fbnconfig.log.setup")
    def test_with_token_option(self, mock_setup):
        runner = CliRunner()
        result = runner.invoke(main.cli, ["setup", "-e", "https://foo.lusid.com", "-t", "xxxxyyy"])
        assert result.exit_code == 0
        assert len(mock_setup.mock_calls) == 1

    @patch.dict(os.environ, {"FBN_ACCESS_TOKEN": "xxxxx"})
    @patch("fbnconfig.log.setup")
    def test_with_token_env(self, mock_setup):
        runner = CliRunner()
        result = runner.invoke(main.cli, ["setup", "-e", "https://foo.lusid.com"])
        assert result.exit_code == 0
        assert len(mock_setup.mock_calls) == 1

    @patch.dict(os.environ, {"NOT_THE_TOKEN": "xxxxx"}, clear=True)
    @patch("fbnconfig.log.setup")
    def test_without_token(self, mock_setup):
        runner = CliRunner()
        result = runner.invoke(main.cli, ["setup", "-e", "https://foo.lusid.com"])
        assert result.exit_code == 2, result.output
        assert "Missing option '-t'" in result.output
        assert len(mock_setup.mock_calls) == 0

    @patch("fbnconfig.log.setup")
    def test_with_env_option(self, mock_setup):
        runner = CliRunner()
        result = runner.invoke(main.cli, ["setup", "-e", "https://foo.lusid.com", "-t", "xxxxyyy"])
        assert result.exit_code == 0
        assert len(mock_setup.mock_calls) == 1

    @patch.dict(os.environ, {"LUSID_ENV": "https://foo.lusid.com"})
    @patch("fbnconfig.log.setup")
    def test_with_env_env(self, mock_setup):
        runner = CliRunner()
        result = runner.invoke(main.cli, ["setup", "-t", "xxxxyyy"])
        assert result.exit_code == 0
        assert len(mock_setup.mock_calls) == 1

    @patch.dict(os.environ, {"NOT_THE_ENV": "https://foo.lusid.com"}, clear=True)
    @patch("fbnconfig.log.setup")
    def test_without_env(self, mock_setup):
        runner = CliRunner()
        result = runner.invoke(main.cli, ["setup", "-t", "xxxxyyy"])
        assert result.exit_code == 2, result.output
        assert "Missing option '-e'" in result.output
        assert len(mock_setup.mock_calls) == 0

    @pytest.mark.respx(base_url="https://foo.lusid.com")
    def test_handles_http_exceptions(self, respx_mock):
        respx_mock.post("/api/api/propertydefinitions").mock(return_value=httpx.Response(400, json={}))
        runner = CliRunner()
        result = runner.invoke(main.cli, ["setup", "-e", "https://foo.lusid.com", "-t", "x"])
        assert result.exit_code == 1
        # then the exit code is failure
        assert result.exit_code == 1, result.output
        # and the 500 is reported to the console
        assert "The server responded with 400" in result.output


def test_help():
    runner = CliRunner()
    result = runner.invoke(main.cli, ["--help"])
    assert result.exit_code == 0
    assert "Usage" in result.output
    assert "setup" in result.output
    assert "log" in result.output


def test_version():
    runner = CliRunner()
    result = runner.invoke(main.cli, ["--version"])
    assert result.exit_code == 0
    assert "0.0.1" in result.output


class DescribeLogList:
    @patch.dict(
        os.environ, {"FBN_ACCESS_TOKEN": "xxxxx", "LUSID_ENV": "https://foo.lusid.com"}, clear=True
    )
    @patch("fbnconfig.log.list_resources_for_deployment")
    def test_with_token(self, mock_list_resources_for_deployment):
        runner = CliRunner()
        result = runner.invoke(main.cli, ["log", "list", "test"])
        assert result.exit_code == 0
        assert len(mock_list_resources_for_deployment.mock_calls) == 2

    @patch.dict(os.environ, {"NOT_THE_TOKEN": "xxxxx", "LUSID_ENV": "https://foo.lusid.com"}, clear=True)
    @patch("fbnconfig.log.list_deployments")
    def test_without_token(self, mock_list_deployments):
        runner = CliRunner()
        result = runner.invoke(main.cli, ["log", "list"])
        assert result.exit_code == 2, result.output
        assert "Missing option '-t'" in result.output
        assert len(mock_list_deployments.mock_calls) == 0

    @pytest.mark.respx(base_url="https://foo.lusid.com")
    def test_handles_http_exceptions(self, respx_mock):
        respx_mock.get(f"/api/api/customentities/~{log_entity}").mock(
            return_value=httpx.Response(400, json={})
        )
        runner = CliRunner()
        result = runner.invoke(main.cli, ["log", "list", "-e", "https://foo.lusid.com", "-t", "xxtoken"])
        assert result.exit_code == 1
        # then the exit code is failure
        assert result.exit_code == 1, result.output
        # and the 500 is reported to the console
        assert "The server responded with 400" in result.output


@pytest.mark.respx(base_url="https://foo.lusid.com")
class DescribeLogGet:
    @patch.dict(os.environ, {"FBN_ACCESS_TOKEN": "xx", "LUSID_ENV": "https://foo.lusid.com"}, clear=True)
    @patch("fbnconfig.log.get_resource")
    def test_with_token(self, mock_get_resource):
        runner = CliRunner()
        result = runner.invoke(main.cli, ["log", "get", "test", "test"])
        assert result.exit_code == 0
        assert len(mock_get_resource.mock_calls) == 2

    def test_handles_http_exceptions(self, respx_mock):
        respx_mock.get(f"/api/api/customentities/~{log_entity}").mock(
            return_value=httpx.Response(400, json={})
        )
        runner = CliRunner()
        result = runner.invoke(
            main.cli,
            ["log", "get", "-e", "https://foo.lusid.com", "-t", "xxtoken", "deployment", "resourceId"],
        )
        # then the exit code is failure
        assert result.exit_code == 1, result.output
        # and the 500 is reported to the console
        assert "The server responded with 400" in result.output


@patch.dict(os.environ, {"FBN_ACCESS_TOKEN": "xxxxx", "LUSID_ENV": "https://foo.lusid.com"}, clear=True)
class DescribeDependencies:
    @patch("fbnconfig.log.get_dependencies_map")
    def test_with_some_dependencies(self, mock_get_deps: Mock):
        mock_get_deps.return_value = {}, {"a": ["b"], "c": ["d"]}
        runner = CliRunner()
        result = runner.invoke(main.cli, ["log", "deps", "deploy", "resource"])
        assert result.exit_code == 0
        mock_get_deps.assert_called_once()


@patch.dict(os.environ, {"FBN_ACCESS_TOKEN": "xxxxx", "LUSID_ENV": "https://foo.lusid.com"}, clear=True)
class DescribeDependants:
    @patch("fbnconfig.log.get_dependents_map")
    def test_with_some_dependencies(self, mock_get_uses_map: Mock):
        mock_get_uses_map.return_value = {}, {"a": ["b", "c"]}
        runner = CliRunner()
        result = runner.invoke(main.cli, ["log", "uses", "deploy", "resource"])
        assert result.exit_code == 0
        mock_get_uses_map.assert_called_once()


@patch.dict(os.environ, {"FBN_ACCESS_TOKEN": "xxxxx", "LUSID_ENV": "https://foo.lusid.com"}, clear=True)
class DescribeRemove:
    @patch("fbnconfig.log.get_dependents_map")
    @patch("fbnconfig.log.get_resource")
    def test_given_resource_does_not_exist(
        self, mock_get_resources: Mock, mock_get_dependents_map: Mock
    ):
        mock_get_resources.return_value = []
        runner = CliRunner()
        result = runner.invoke(main.cli, ["log", "rm", "mydeployment", "someresource"])
        assert result.exit_code == 2, result.output
        mock_get_resources.assert_called_once()
        mock_get_dependents_map.assert_not_called()

    @patch("fbnconfig.log.remove")
    @patch("fbnconfig.log.get_dependents_map")
    @patch("fbnconfig.log.get_resource")
    def test_given_resource_exists_with_uses_and_no_force(
            self, mock_get_resources: Mock, mock_get_dependents_map: Mock, mock_remove: Mock
    ):
        # given resource1 has a dependency on somedeps
        mock_get_resources.return_value = ["someresource"]
        mock_get_dependents_map.return_value = {}, {"someresource": ["somedeps"]}
        # when we try to remove it without a force option
        runner = CliRunner()
        result = runner.invoke(main.cli, ["log", "rm", "mydeployment", "someresource"])
        # then we exit failure, tell the user why
        assert result.exit_code == 2, result.output
        mock_get_dependents_map.assert_called_once()
        assert "Cannot remove entry for 'someresource' as ['somedeps'] depends on it" in result.output
        # and remove does not get called
        mock_remove.assert_not_called()

    @patch("fbnconfig.log.get_resource")
    @patch("fbnconfig.log.remove")
    @patch("fbnconfig.log.get_dependents_map")
    def test_given_resource_exists_with_uses_and_force_then_rm(
        self, mock_get_dependents_map: Mock, mock_remove: Mock, mock_get_resources: Mock
    ):
        mock_get_resources.return_value = ["resource_1"]
        mock_get_dependents_map.return_value = {}, {"someresource": ["somedeps"]}
        runner = CliRunner()
        result = runner.invoke(main.cli, ["log", "rm", "mydeployment", "someresource", "--force"])
        assert result.exit_code == 0
        mock_get_dependents_map.assert_called_once()
        mock_remove.assert_called_once()

    @patch("fbnconfig.log.get_resource")
    @patch("fbnconfig.log.remove")
    @patch("fbnconfig.log.get_dependents_map")
    def test_given_resource_exists_with_uses_and_force_and_recursive_then_rm(
        self, mock_get_dependents_map: Mock, mock_remove: Mock, mock_get_resources: Mock
    ):
        mock_get_resources.return_value = ["resource_1"]
        mock_get_dependents_map.return_value = {}, {"someresource": ["somedeps", "somedeps"]}
        runner = CliRunner()
        result = runner.invoke(
            main.cli, ["log", "rm", "mydeployment", "someresource", "--force", "--recursive"]
        )
        assert result.exit_code == 0
        mock_get_dependents_map.assert_called_once()
        assert mock_remove.call_count == 3
