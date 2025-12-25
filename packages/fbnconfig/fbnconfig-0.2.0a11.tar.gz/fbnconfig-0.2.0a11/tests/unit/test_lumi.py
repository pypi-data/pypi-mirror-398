import csv
import hashlib
import io
import json
import textwrap
from datetime import datetime
from types import SimpleNamespace
from typing import Any, Dict, List, Optional
from unittest.mock import patch

import httpx
import pytest
from respx import Route, Router, mock

from fbnconfig import lumi
from fbnconfig.backoff_handler import BackoffHandler
from fbnconfig.lumi import TaskStatus
from fbnconfig.property import DefinitionRef, Domain

TEST_BASE = "https://foo.lusid.com"


def response_hook(response: httpx.Response):
    response.raise_for_status()


@pytest.fixture(scope="module", autouse=True)
def dont_sleep():
    with patch("time.sleep", return_value=None) as _fixture:
        yield _fixture


def setup_sql_background_routes(
    respx_mock: Router,
    content: Optional[str] = None,
    execution_id: str = "abcdefg",
    task_status: TaskStatus = TaskStatus.RAN_TO_COMPLETION,
    status_code: Optional[List[int]] = None,
    result_data: Optional[Any] = None,
) -> dict[str, Route]:
    routes = {
        "put": respx_mock.put(
            "/honeycomb/api/SqlBackground",
            # # don't pass values as arguments if they're set to none
            **dict(
                filter(
                    lambda item: item[1] is not None,
                    {"content": content, "headers": [("Content-type", "text/plain")]}.items(),
                )
            ),
        ).mock(
            side_effect=[
                httpx.Response(
                    status_code.pop() if status_code else 202, json={"executionId": execution_id}
                )
            ]
        ),
        "status": respx_mock.get(f"/honeycomb/api/SqlBackground/{execution_id}").mock(
            side_effect=[
                httpx.Response(status_code.pop() if status_code else 200, json={"status": task_status})
            ]
        ),
        "result": respx_mock.get(f"/honeycomb/api/SqlBackground/{execution_id}/jsonproper").mock(
            side_effect=[httpx.Response(status_code.pop() if status_code else 200, json=result_data)]
        ),
    }

    return routes


@pytest.mark.respx(base_url=TEST_BASE)
class DescribeViewRef:
    client = httpx.Client(base_url=TEST_BASE, event_hooks={"response": [response_hook]})
    view_attach_content = textwrap.dedent("""\
                select r.Version from sys.registration as r
                where name = 'views.test.view1'
                order by r.Version asc
                limit 1
            """)

    def test_attach_when_exists(self, respx_mock, monkeypatch):
        # given a view in lumi
        setup_sql_background_routes(
            respx_mock, content=self.view_attach_content, result_data=["one row"]
        )

        client = self.client
        # when we attach
        sut = lumi.ViewRef(id="abc", provider="views.test.view1")
        sut.attach(client)
        assert sut._version == "one row"

    def test_attach_when_not_exists(self, respx_mock):
        setup_sql_background_routes(respx_mock, content=self.view_attach_content, result_data=[])
        # given no matching views exist yet

        client = self.client
        # when we attach a view ref
        sut = lumi.ViewRef(id="abc", provider="views.test.view1")
        # then it raises
        with pytest.raises(RuntimeError) as ex:
            sut.attach(client)
        assert "Failed to attach ref to views.test.view1" in str(ex.value)

    @mock(assert_all_called=False)
    def test_attach_when_http_error(self, respx_mock):
        # given the query fails
        routes: dict[str, Route] = setup_sql_background_routes(
            respx_mock, content=self.view_attach_content, status_code=[400]
        )

        client = self.client
        # when we attach a view ref
        sut = lumi.ViewRef(id="abc", provider="views.test.view1")
        # http error is raised
        with pytest.raises(httpx.HTTPStatusError):
            sut.attach(client)
        assert routes["put"].call_count == 1

    def test_dump(self):
        sut = lumi.ViewRef(
            id="lumi-example-ref",
            provider="Views.fbnconfig.existing_view"
        )

        result = sut.model_dump(context={"style": "dump"})

        # id field is globally excluded, so it won't appear in dumps
        assert "id" not in result
        assert result["provider"] == "Views.fbnconfig.existing_view"


# constructs the row from sys.file
def make_sys_file(sql: str, metadata: Dict, version: int) -> Dict:
    return {"Content": f"{sql}--- MetaData --- " + json.dumps(metadata), "Version": version}


@pytest.mark.respx(base_url=TEST_BASE)
class DescribeViewResource:
    client = httpx.Client(base_url=TEST_BASE, event_hooks={"response": [response_hook]})

    @staticmethod
    def setup_class():
        # reduce time waiting for registration
        lumi.ViewResource.Registration.tries = 3
        lumi.ViewResource.Registration.wait_time = 0

    def test_create(self, respx_mock):
        exec_id = "abcdefg"

        expected = textwrap.dedent("""\
                   @x = use Sys.Admin.SetupView
                   --provider="Views.Unit.Test"
                   --description="a view"
                   ----
                   select * from foo;
                   enduse;
                   select * from @x;
               """)
        # setup_sql_background_routes(respx_mock, content=expected, result_data={})

        expected_registration = textwrap.dedent("""\
                    select Version from sys.registration where Name='Views.Unit.Test'
                    order by Version asc
                    limit 1
                """)

        put: Route = respx_mock.put(
            "/honeycomb/api/SqlBackground", headers=[("Content-type", "text/plain")]
        ).mock(side_effect=[httpx.Response(202, json={"executionId": exec_id})] * 2)

        respx_mock.get(f"/honeycomb/api/SqlBackground/{exec_id}").mock(
            side_effect=[httpx.Response(200, json={"status": TaskStatus.RAN_TO_COMPLETION})] * 2
        )

        respx_mock.get(f"/honeycomb/api/SqlBackground/{exec_id}/jsonproper").mock(
            side_effect=[httpx.Response(200, json={}), httpx.Response(200, json=[{"Version": 1}])]
        )
        # setup_sql_background_routes(
        #     respx_mock,
        #     content=expected_registration,
        #     execution_id="123",
        #     result_data=[{"Version": 1}])

        # given a view to create
        sut = lumi.ViewResource(
            id="my-view", provider="Views.Unit.Test", sql="select * from foo;", description="a view"
        )
        # when we do
        state = sut.create(self.client)
        # the state is returned
        respx_mock.assert_all_called()
        assert put.calls[0].request.content.decode("utf8") == expected
        assert put.calls[1].request.content.decode("utf8") == expected_registration
        assert state == {"provider": "Views.Unit.Test"}

    def test_create_waits_for_registration(self, respx_mock):
        exec_id = "abcdefg"
        put: Route = respx_mock.put(
            "/honeycomb/api/SqlBackground", headers=[("Content-type", "text/plain")]
        ).mock(side_effect=[httpx.Response(202, json={"executionId": exec_id})] * 4)
        respx_mock.get(f"/honeycomb/api/SqlBackground/{exec_id}").mock(
            side_effect=[
                # Query creation + 3x registration
                httpx.Response(200, json={"status": TaskStatus.RAN_TO_COMPLETION})
            ]
            * 4
        )

        respx_mock.get(f"/honeycomb/api/SqlBackground/{exec_id}/jsonproper").mock(
            side_effect=[httpx.Response(200, json={})]
            +
            # and the registration check was performed a second time
            # because no version came back on the first check
            [httpx.Response(200, json=[])] * 2
            + [httpx.Response(200, json=[{"Version": "1"}])]
        )

        expected = textwrap.dedent("""\
                    select Version from sys.registration where Name='Views.Unit.Test'
                    order by Version asc
                    limit 1
                """)

        # given a view to create
        sut = lumi.ViewResource(
            id="my-view", provider="Views.Unit.Test", sql="select * from foo;", description="a view"
        )
        # when we do
        state = sut.create(self.client)
        respx_mock.assert_all_called()
        assert put.calls[1].request.content.decode("utf8") == expected
        # the state is returned
        assert state == {"provider": "Views.Unit.Test"}

    def test_create_completes_if_registration_incomplete(self, respx_mock, capsys):
        exec_id = "abcdefg"
        put: Route = respx_mock.put(
            "/honeycomb/api/SqlBackground", headers=[("Content-type", "text/plain")]
        ).mock(side_effect=[httpx.Response(202, json={"executionId": exec_id})] * 4)
        respx_mock.get(f"/honeycomb/api/SqlBackground/{exec_id}").mock(
            side_effect=[
                # Query creation + 3x registration
                httpx.Response(200, json={"status": TaskStatus.RAN_TO_COMPLETION})
            ]
            * 4
        )

        respx_mock.get(f"/honeycomb/api/SqlBackground/{exec_id}/jsonproper").mock(
            side_effect=[httpx.Response(200, json={})] + [httpx.Response(200, json=[])] * 3
        )

        # given a view to create
        sut = lumi.ViewResource(
            id="my-view", provider="Views.Unit.Test", sql="select * from foo;", description="a view"
        )
        # when we do
        state = sut.create(self.client)
        # the state is returned even though the registration did not
        # complete in time
        assert state == {"provider": "Views.Unit.Test"}
        # and the registration check was performed 3 times
        expected = textwrap.dedent("""\
            select Version from sys.registration where Name='Views.Unit.Test'
            order by Version asc
            limit 1
        """)
        respx_mock.assert_all_called()
        assert put.calls[1].request.content.decode("utf8") == expected

        # check warning is returned
        captured = capsys.readouterr()
        assert captured.err == (
            f"warning: no view registration after "
            f"{lumi.ViewResource.Registration.tries}"
            f" tries for Views.Unit.Test"
        )

    def test_create_with_saved_option(self, respx_mock):
        exec_id = "abcdefg"
        put: Route = respx_mock.put(
            "/honeycomb/api/SqlBackground", headers=[("Content-type", "text/plain")]
        ).mock(side_effect=[httpx.Response(202, json={"executionId": exec_id})] * 2)
        respx_mock.get(f"/honeycomb/api/SqlBackground/{exec_id}").mock(
            side_effect=[httpx.Response(200, json={"status": TaskStatus.RAN_TO_COMPLETION})] * 2
        )

        respx_mock.get(f"/honeycomb/api/SqlBackground/{exec_id}/jsonproper").mock(
            side_effect=[httpx.Response(200, json={}), httpx.Response(200, json=[{"Version": 1}])]
        )

        # given a desired view with one of the saved options
        # (ones which impact the stored view in lumi)
        sut = lumi.ViewResource(
            id="my-view",
            provider="Views.Unit.Test",
            sql="select * from foo;",
            description="a view",
            documentation_link="http://example.com",
        )
        # when we create it
        state = sut.create(self.client)
        assert state == {"provider": "Views.Unit.Test"}
        # and a create request was sent with an =
        request = put.calls[0].request
        expected = textwrap.dedent("""\
            @x = use Sys.Admin.SetupView
            --provider="Views.Unit.Test"
            --description="a view"
            --documentationLink="http://example.com"
            ----
            select * from foo;
            enduse;
            select * from @x;
        """)
        assert request.content.decode("utf8") == expected

    def test_create_with_saved_bool_option(self, respx_mock):
        exec_id = "abcdefg"
        put: Route = respx_mock.put(
            "/honeycomb/api/SqlBackground", headers=[("Content-type", "text/plain")]
        ).mock(side_effect=[httpx.Response(202, json={"executionId": exec_id})] * 2)
        respx_mock.get(f"/honeycomb/api/SqlBackground/{exec_id}").mock(
            side_effect=[httpx.Response(200, json={"status": TaskStatus.RAN_TO_COMPLETION})] * 2
        )

        respx_mock.get(f"/honeycomb/api/SqlBackground/{exec_id}/jsonproper").mock(
            side_effect=[httpx.Response(200, json={}), httpx.Response(200, json=[{"Version": 1}])]
        )

        # given a desired state with a boolean saved option
        # variableShape
        sut = lumi.ViewResource(
            id="my-view",
            provider="Views.Unit.Test",
            sql="select * from foo;",
            description="a view",
            variable_shape=True,
        )
        # when we create
        state = sut.create(self.client)
        assert state == {"provider": "Views.Unit.Test"}
        # the create adds the option without an =
        request = put.calls[0].request
        expected = textwrap.dedent("""\
            @x = use Sys.Admin.SetupView
            --provider="Views.Unit.Test"
            --description="a view"
            --variableShape
            ----
            select * from foo;
            enduse;
            select * from @x;
        """)
        assert request.content.decode("utf8") == expected

    def test_create_with_test_option(self, respx_mock):
        exec_id = "abcdefg"
        put: Route = respx_mock.put(
            "/honeycomb/api/SqlBackground", headers=[("Content-type", "text/plain")]
        ).mock(side_effect=[httpx.Response(202, json={"executionId": exec_id})] * 2)
        respx_mock.get(f"/honeycomb/api/SqlBackground/{exec_id}").mock(
            side_effect=[httpx.Response(200, json={"status": TaskStatus.RAN_TO_COMPLETION})] * 2
        )

        respx_mock.get(f"/honeycomb/api/SqlBackground/{exec_id}/jsonproper").mock(
            side_effect=[httpx.Response(200, json={}), httpx.Response(200, json=[{"Version": 1}])]
        )

        # given desired includes limit, an option which is used for
        # running the view but does not get saved
        sut = lumi.ViewResource(
            id="my-view",
            provider="Views.Unit.Test",
            sql="select * from foo;",
            description="a view",
            limit=42,
        )
        # when we create
        state = sut.create(self.client)
        assert state == {"provider": "Views.Unit.Test"}
        # the test option gets sent and is not quoted because
        # it's an int
        request = put.calls[0].request
        expected = textwrap.dedent("""\
            @x = use Sys.Admin.SetupView
            --provider="Views.Unit.Test"
            --limit=42
            --description="a view"
            ----
            select * from foo;
            enduse;
            select * from @x;
        """)
        assert request.content.decode("utf8") == expected

    def test_create_parameter(self, respx_mock):
        exec_id = "abcdefg"
        put: Route = respx_mock.put(
            "/honeycomb/api/SqlBackground", headers=[("Content-type", "text/plain")]
        ).mock(side_effect=[httpx.Response(202, json={"executionId": exec_id})] * 2)
        respx_mock.get(f"/honeycomb/api/SqlBackground/{exec_id}").mock(
            side_effect=[httpx.Response(200, json={"status": TaskStatus.RAN_TO_COMPLETION})] * 2
        )

        respx_mock.get(f"/honeycomb/api/SqlBackground/{exec_id}/jsonproper").mock(
            side_effect=[httpx.Response(200, json={}), httpx.Response(200, json=[{"Version": 1}])]
        )

        # given a desired with a parameter
        sut = lumi.ViewResource(
            id="my-view",
            provider="Views.Unit.Test",
            sql="select * from foo;",
            description="a view",
            parameters=[
                lumi.Parameter(
                    name="p1",
                    type=lumi.ParameterType.Int,
                    value=23,
                    set_as_default_value=False,
                    tooltip="p1 is nice",
                )
            ],
        )
        # when we create it
        state = sut.create(self.client)
        assert state == {"provider": "Views.Unit.Test"}
        # the parameter is added at the end of the options
        request = put.calls[0].request
        expected = textwrap.dedent("""\
            @x = use Sys.Admin.SetupView
            --provider="Views.Unit.Test"
            --description="a view"
            --parameters
            p1,Int,23,false,"p1 is nice"
            ----
            select * from foo;
            enduse;
            select * from @x;
        """)
        assert request.content.decode("utf8") == expected

    def test_create_parameter_escaped(self, respx_mock):
        exec_id = "abcdefg"
        put: Route = respx_mock.put(
            "/honeycomb/api/SqlBackground", headers=[("Content-type", "text/plain")]
        ).mock(side_effect=[httpx.Response(202, json={"executionId": exec_id})] * 2)
        respx_mock.get(f"/honeycomb/api/SqlBackground/{exec_id}").mock(
            side_effect=[httpx.Response(200, json={"status": TaskStatus.RAN_TO_COMPLETION})] * 2
        )

        respx_mock.get(f"/honeycomb/api/SqlBackground/{exec_id}/jsonproper").mock(
            side_effect=[httpx.Response(200, json={}), httpx.Response(200, json=[{"Version": 1}])]
        )

        # given a desired with a text parameter where the value
        # includes a double quote
        sut = lumi.ViewResource(
            id="my-view",
            provider="Views.Unit.Test",
            sql="select * from foo;",
            description="a view",
            parameters=[
                lumi.Parameter(
                    name="p1",
                    type=lumi.ParameterType.Text,
                    value='embedded " quote',
                    set_as_default_value=False,
                    tooltip="p1 is nice",
                )
            ],
        )
        # when we create
        state = sut.create(self.client)
        assert state == {"provider": "Views.Unit.Test"}
        # the text is wrapped in quotes and the embedded quote
        # gets escaped
        request = put.calls[0].request
        expected = textwrap.dedent("""\
            @x = use Sys.Admin.SetupView
            --provider="Views.Unit.Test"
            --description="a view"
            --parameters
            p1,Text,"embedded "" quote",false,"p1 is nice"
            ----
            select * from foo;
            enduse;
            select * from @x;
        """)
        assert request.content.decode("utf8") == expected

    def test_create_parameter_no_tooltip(self, respx_mock):
        exec_id = "abcdefg"
        put: Route = respx_mock.put(
            "/honeycomb/api/SqlBackground", headers=[("Content-type", "text/plain")]
        ).mock(side_effect=[httpx.Response(202, json={"executionId": exec_id})] * 2)
        respx_mock.get(f"/honeycomb/api/SqlBackground/{exec_id}").mock(
            side_effect=[httpx.Response(200, json={"status": TaskStatus.RAN_TO_COMPLETION})] * 2
        )

        respx_mock.get(f"/honeycomb/api/SqlBackground/{exec_id}/jsonproper").mock(
            side_effect=[httpx.Response(200, json={}), httpx.Response(200, json=[{"Version": 1}])]
        )

        # given a desired with a parameter
        sut = lumi.ViewResource(
            id="my-view",
            provider="Views.Unit.Test",
            sql="select * from foo;",
            description="a view",
            parameters=[
                lumi.Parameter(
                    name="p1", type=lumi.ParameterType.Int, value=23, set_as_default_value=False
                )
            ],
        )
        # when we create it
        state = sut.create(self.client)
        assert state == {"provider": "Views.Unit.Test"}
        # the parameter is added at the end of the options
        request = put.calls[0].request
        expected = textwrap.dedent("""\
            @x = use Sys.Admin.SetupView
            --provider="Views.Unit.Test"
            --description="a view"
            --parameters
            p1,Int,23,false
            ----
            select * from foo;
            enduse;
            select * from @x;
        """)
        assert request.content.decode("utf8") == expected

    def test_create_scalar_variable(self, respx_mock):
        exec_id = "abcdefg"
        put: Route = respx_mock.put(
            "/honeycomb/api/SqlBackground", headers=[("Content-type", "text/plain")]
        ).mock(side_effect=[httpx.Response(202, json={"executionId": exec_id})] * 2)
        respx_mock.get(f"/honeycomb/api/SqlBackground/{exec_id}").mock(
            side_effect=[httpx.Response(200, json={"status": TaskStatus.RAN_TO_COMPLETION})] * 2
        )

        respx_mock.get(f"/honeycomb/api/SqlBackground/{exec_id}/jsonproper").mock(
            side_effect=[httpx.Response(200, json={}), httpx.Response(200, json=[{"Version": 1}])]
        )

        # given a desired with a variable which is the default value
        # for a parameter
        p1_value = lumi.Variable(name="p1_value", type=lumi.VariableType.Scalar, sql="select 1 + 2")
        sut = lumi.ViewResource(
            id="my-view",
            provider="Views.Unit.Test",
            sql="select * from foo;",
            description="a view",
            variables=[p1_value],
            parameters=[
                lumi.Parameter(
                    name="p1",
                    type=lumi.ParameterType.Int,
                    value=p1_value,
                    set_as_default_value=False,
                    tooltip="p1 is nice",
                )
            ],
        )
        # when we create
        state = sut.create(self.client)
        assert state == {"provider": "Views.Unit.Test"}
        # the parameter is added at the end of the options
        request = put.calls[0].request
        expected = textwrap.dedent("""\
            @@p1_value = select 1 + 2;
            @x = use Sys.Admin.SetupView with @@p1_value
            --provider="Views.Unit.Test"
            --description="a view"
            --parameters
            p1,Int,@@p1_value,false,"p1 is nice"
            ----
            select * from foo;
            enduse;
            select * from @x;
        """)
        assert request.content.decode("utf8") == expected

    def test_create_table_variable(self, respx_mock):
        exec_id = "abcdefg"
        put: Route = respx_mock.put(
            "/honeycomb/api/SqlBackground", headers=[("Content-type", "text/plain")]
        ).mock(side_effect=[httpx.Response(202, json={"executionId": exec_id})] * 2)
        respx_mock.get(f"/honeycomb/api/SqlBackground/{exec_id}").mock(
            side_effect=[httpx.Response(200, json={"status": TaskStatus.RAN_TO_COMPLETION})] * 2
        )

        respx_mock.get(f"/honeycomb/api/SqlBackground/{exec_id}/jsonproper").mock(
            side_effect=[httpx.Response(200, json={}), httpx.Response(200, json=[{"Version": 1}])]
        )

        # given a desired with a table variable used as a
        # parameter
        p2_value = lumi.Variable(
            name="p2_value",
            type=lumi.VariableType.Table,
            sql="""select * from ( values(1, 2, 3), (4, 5, 6))""",
        )
        sut = lumi.ViewResource(
            id="my-view",
            provider="Views.Unit.Test",
            sql="select * from @p2;",
            description="a view",
            variables=[p2_value],
            parameters=[
                lumi.Parameter(
                    name="p2",
                    type=lumi.ParameterType.Table,
                    value=p2_value,
                    is_mandatory=False,
                    tooltip="p2 is nice",
                )
            ],
        )
        # when we create
        state = sut.create(self.client)
        assert state == {"provider": "Views.Unit.Test"}
        # the parameter is added at the end of the options
        request = put.calls[0].request
        expected = textwrap.dedent("""\
            @p2_value = select * from ( values(1, 2, 3), (4, 5, 6));
            @x = use Sys.Admin.SetupView with @p2_value
            --provider="Views.Unit.Test"
            --description="a view"
            --parameters
            p2,Table,@p2_value,false,"p2 is nice"
            ----
            select * from @p2;
            enduse;
            select * from @x;
        """)
        assert request.content.decode("utf8") == expected

    def test_create_two_variables(self, respx_mock):
        exec_id = "abcdefg"
        put: Route = respx_mock.put(
            "/honeycomb/api/SqlBackground", headers=[("Content-type", "text/plain")]
        ).mock(side_effect=[httpx.Response(202, json={"executionId": exec_id})] * 2)
        respx_mock.get(f"/honeycomb/api/SqlBackground/{exec_id}").mock(
            side_effect=[httpx.Response(200, json={"status": TaskStatus.RAN_TO_COMPLETION})] * 2
        )

        respx_mock.get(f"/honeycomb/api/SqlBackground/{exec_id}/jsonproper").mock(
            side_effect=[httpx.Response(200, json={}), httpx.Response(200, json=[{"Version": 1}])]
        )

        # given a desired with a one table and one scalar
        # for a parameter
        p1_value = lumi.Variable(name="p1_value", type=lumi.VariableType.Scalar, sql="select 1 + 2")
        p2_value = lumi.Variable(
            name="p2_value",
            type=lumi.VariableType.Table,
            sql="""select * from ( values(1, 2, 3), (4, 5, 6))""",
        )
        # the table is used as a parameter
        sut = lumi.ViewResource(
            id="my-view",
            provider="Views.Unit.Test",
            sql="select * from @p2;",
            description="a view",
            variables=[p1_value, p2_value],
            parameters=[
                lumi.Parameter(
                    name="p2",
                    type=lumi.ParameterType.Table,
                    value=p2_value,
                    is_mandatory=False,
                    tooltip="p2 is nice",
                )
            ],
        )
        # when we create
        state = sut.create(self.client)
        assert state == {"provider": "Views.Unit.Test"}
        # the vars are initialised, the with statement includes them
        # and the table parameter is included
        request = put.calls[0].request
        expected = textwrap.dedent("""\
            @@p1_value = select 1 + 2;
            @p2_value = select * from ( values(1, 2, 3), (4, 5, 6));
            @x = use Sys.Admin.SetupView with @@p1_value, @p2_value
            --provider="Views.Unit.Test"
            --description="a view"
            --parameters
            p2,Table,@p2_value,false,"p2 is nice"
            ----
            select * from @p2;
            enduse;
            select * from @x;
        """)
        assert request.content.decode("utf8") == expected

    def test_update_with_no_changes(self, respx_mock):
        exec_id = "abcdefg"
        put: Route = respx_mock.put(
            "/honeycomb/api/SqlBackground", headers=[("Content-type", "text/plain")]
        ).mock(side_effect=[httpx.Response(202, json={"executionId": exec_id})])
        respx_mock.get(f"/honeycomb/api/SqlBackground/{exec_id}").mock(
            side_effect=[httpx.Response(200, json={"status": TaskStatus.RAN_TO_COMPLETION})]
        )

        respx_mock.get(f"/honeycomb/api/SqlBackground/{exec_id}/jsonproper").mock(
            side_effect=[
                httpx.Response(
                    200,
                    json=[
                        make_sys_file(
                            "select * from foo", {"Description": "a view", "Parameters": []}, version=1
                        )
                    ],
                )
            ]
        )

        # and a desired state that is the same;
        # new line at the end of script should not count as change
        sut = lumi.ViewResource(
            id="my-view",
            provider="Views.Unit.Test",
            sql="""select * from foo
            """,
            description="a view",
        )
        old_state = SimpleNamespace(provider="Views.Unit.Test")
        # when we update it
        state = sut.update(self.client, old_state)
        # then the state is None
        assert state is None
        # and the read query was sent
        request = put.calls[0].request
        assert request.method == "PUT"
        expected = textwrap.dedent("""\
            select f.Content, r.Version from sys.file as f
            join sys.registration as r on r.Name = 'Views.Unit.Test'
            where path = 'databaseproviders/Views/Unit/Test.sql'
            order by r.Version asc
            limit 1
        """)
        assert request.content.decode() == expected
        # and we read the remote but didn't write anything
        assert len(respx_mock.calls) == 3

    def test_update_with_test_option_means_no_change(self, respx_mock):
        # given an existing remote
        exec_id = "abcdefg"
        respx_mock.put("/honeycomb/api/SqlBackground", headers=[("Content-type", "text/plain")]).mock(
            side_effect=[httpx.Response(202, json={"executionId": exec_id})]
        )
        respx_mock.get(f"/honeycomb/api/SqlBackground/{exec_id}").mock(
            side_effect=[httpx.Response(200, json={"status": TaskStatus.RAN_TO_COMPLETION})]
        )

        respx_mock.get(f"/honeycomb/api/SqlBackground/{exec_id}/jsonproper").mock(
            side_effect=[
                httpx.Response(
                    200,
                    json=[
                        make_sys_file(
                            "select * from foo", {"Description": "a view", "Parameters": []}, version=1
                        )
                    ],
                )
            ]
        )

        # and a desired that is the same except we add test_options
        # limit, useDryRun, groupby, filter
        sut = lumi.ViewResource(
            id="my-view",
            provider="Views.Unit.Test",
            sql="select * from foo",
            description="a view",
            limit=42,
            use_dry_run=True,
            group_by="one",
            filter="something",
        )
        old_state = SimpleNamespace(provider="Views.Unit.Test")
        # when we update it
        state = sut.update(self.client, old_state)
        # then the state is None because test_options are not saved
        assert state is None

    def test_update_with_extra_saved_option(self, respx_mock):
        # given an existing remote
        exec_id = "abcdefg"
        put: Route = respx_mock.put(
            "/honeycomb/api/SqlBackground", headers=[("Content-type", "text/plain")]
        ).mock(
            # Read, update, registration check
            side_effect=[httpx.Response(202, json={"executionId": exec_id})] * 3
        )

        respx_mock.get(f"/honeycomb/api/SqlBackground/{exec_id}").mock(
            side_effect=[httpx.Response(200, json={"status": TaskStatus.RAN_TO_COMPLETION})] * 3
        )

        respx_mock.get(f"/honeycomb/api/SqlBackground/{exec_id}/jsonproper").mock(
            side_effect=[
                # read
                httpx.Response(
                    200,
                    json=[
                        make_sys_file(
                            "select * from foo", {"Description": "a view", "Parameters": []}, version=1
                        )
                    ],
                ),
                httpx.Response(200, json=[]),
                # registration check
                httpx.Response(200, json=[{"Version": 2}]),
            ]
        )

        # and a desired adds a saved option (documentationLink)
        sut = lumi.ViewResource(
            id="my-view",
            provider="Views.Unit.Test",
            sql="select * from foo",
            description="a view",
            documentation_link="http://example.com",
        )
        old_state = SimpleNamespace(provider="Views.Unit.Test")
        # when we update it
        state = sut.update(self.client, old_state)
        # then a change is detected
        assert state == {"provider": "Views.Unit.Test"}
        # and we created a new view
        request = put.calls[1].request
        assert request.method == "PUT"
        expected = textwrap.dedent("""\
            @x = use Sys.Admin.SetupView
            --provider="Views.Unit.Test"
            --description="a view"
            --documentationLink="http://example.com"
            ----
            select * from foo
            enduse;
            select * from @x;
        """)
        assert request.content.decode("utf8") == expected

    def test_update_does_registration_check(self, respx_mock):
        # given an existing remote
        exec_id = "abcdefg"
        put: Route = respx_mock.put(
            "/honeycomb/api/SqlBackground", headers=[("Content-type", "text/plain")]
        ).mock(
            # Read, update, 2xregistration check
            side_effect=[httpx.Response(202, json={"executionId": exec_id})] * 4
        )

        respx_mock.get(f"/honeycomb/api/SqlBackground/{exec_id}").mock(
            side_effect=[httpx.Response(200, json={"status": TaskStatus.RAN_TO_COMPLETION})] * 4
        )

        respx_mock.get(f"/honeycomb/api/SqlBackground/{exec_id}/jsonproper").mock(
            side_effect=[
                # read
                httpx.Response(
                    200,
                    json=[
                        make_sys_file(
                            "select * from foo", {"Description": "a view", "Parameters": []}, version=1
                        )
                    ],
                ),
                httpx.Response(200, json=[]),  # update
                httpx.Response(200, json=[{"Version": 1}]),  # registration false
                httpx.Response(200, json=[{"Version": 2}]),  # registration complete
            ]
        )

        # and a desired makes a change
        sut = lumi.ViewResource(
            id="my-view",
            provider="Views.Unit.Test",
            sql="select * from foo",
            description="a view",
            documentation_link="http://example.com",
        )
        old_state = SimpleNamespace(provider="Views.Unit.Test")
        # when we update it
        state = sut.update(self.client, old_state)
        # then a change is detected
        assert state == {"provider": "Views.Unit.Test"}
        # and the registration check was performed twice
        # because the version before update was 1 and we wait until it's increased
        check2 = put.calls[3].request
        expected = textwrap.dedent("""\
            select Version from sys.registration where Name='Views.Unit.Test'
            order by Version asc
            limit 1
        """)
        assert check2.content.decode("utf8") == expected

    def test_update_completes_when_registration_version_does_not_update(self, respx_mock):
        exec_id = "abcdefg"
        put: Route = respx_mock.put(
            "/honeycomb/api/SqlBackground", headers=[("Content-type", "text/plain")]
        ).mock(
            # Read, update, 3xregistration check
            side_effect=[httpx.Response(202, json={"executionId": exec_id})] * 5
        )

        respx_mock.get(f"/honeycomb/api/SqlBackground/{exec_id}").mock(
            side_effect=[httpx.Response(200, json={"status": TaskStatus.RAN_TO_COMPLETION})] * 5
        )

        respx_mock.get(f"/honeycomb/api/SqlBackground/{exec_id}/jsonproper").mock(
            side_effect=[
                # read
                httpx.Response(
                    200,
                    json=[
                        make_sys_file(
                            "select * from foo", {"Description": "a view", "Parameters": []}, version=1
                        )
                    ],
                ),
                # register within the 3 tries
                httpx.Response(200, json=[]),  # update
                httpx.Response(200, json=[{"Version": 1}]),  # registration false
                httpx.Response(200, json=[{"Version": 1}]),  # registration false
                httpx.Response(200, json=[{"Version": 1}]),  # registration false
            ]
        )

        # and a desired makes a change
        sut = lumi.ViewResource(
            id="my-view",
            provider="Views.Unit.Test",
            sql="select * from foo",
            description="a view",
            documentation_link="http://example.com",
        )
        old_state = SimpleNamespace(provider="Views.Unit.Test")
        # when we update it
        state = sut.update(self.client, old_state)
        # then a state is returned even though the reg check didn't complete
        assert state == {"provider": "Views.Unit.Test"}
        # and the registration check was 3 times
        # because the version didn't update
        check = put.calls[4].request
        expected = textwrap.dedent("""\
            select Version from sys.registration where Name='Views.Unit.Test'
            order by Version asc
            limit 1
        """)
        assert check.content.decode("utf8") == expected

    def test_update_completes_when_no_registration_rows_returned(self, respx_mock):
        # given an existing remote where the view is not going to
        # register within the 3 tries
        exec_id = "abcdefg"
        put: Route = respx_mock.put(
            "/honeycomb/api/SqlBackground", headers=[("Content-type", "text/plain")]
        ).mock(
            # Read, update, 3xregistration check
            side_effect=[httpx.Response(202, json={"executionId": exec_id})] * 5
        )

        respx_mock.get(f"/honeycomb/api/SqlBackground/{exec_id}").mock(
            side_effect=[httpx.Response(200, json={"status": TaskStatus.RAN_TO_COMPLETION})] * 5
        )

        respx_mock.get(f"/honeycomb/api/SqlBackground/{exec_id}/jsonproper").mock(
            side_effect=[
                # read
                httpx.Response(
                    200,
                    json=[
                        make_sys_file(
                            "select * from foo", {"Description": "a view", "Parameters": []}, version=1
                        )
                    ],
                ),
                httpx.Response(200, json=[]),  # update
                httpx.Response(200, json=[{"Version": 1}]),  # registration false
                httpx.Response(200, json=[{"Version": 1}]),  # registration false
                httpx.Response(200, json=[]),  # no rows returned
            ]
        )

        # and a desired makes a change
        sut = lumi.ViewResource(
            id="my-view",
            provider="Views.Unit.Test",
            sql="select * from foo",
            description="a view",
            documentation_link="http://example.com",
        )
        old_state = SimpleNamespace(provider="Views.Unit.Test")
        # when we update it
        state = sut.update(self.client, old_state)
        # then a state is returned even though the reg check didn't complete
        assert state == {"provider": "Views.Unit.Test"}
        # and the registration check was 3 times
        # because the version didn't update
        check = put.calls[4].request
        expected = textwrap.dedent("""\
            select Version from sys.registration where Name='Views.Unit.Test'
            order by Version asc
            limit 1
        """)
        assert check.content.decode("utf8") == expected

    def test_update_defaulted_saved_option(self, respx_mock):
        # given an existing View created without the variableShape option
        exec_id = "abcdefg"
        respx_mock.put("/honeycomb/api/SqlBackground", headers=[("Content-type", "text/plain")]).mock(
            side_effect=[httpx.Response(202, json={"executionId": exec_id})] * 3
        )

        respx_mock.get(f"/honeycomb/api/SqlBackground/{exec_id}").mock(
            side_effect=[httpx.Response(200, json={"status": TaskStatus.RAN_TO_COMPLETION})] * 3
        )

        respx_mock.get(f"/honeycomb/api/SqlBackground/{exec_id}/jsonproper").mock(
            side_effect=[
                # read
                httpx.Response(
                    200,
                    json=[
                        make_sys_file(
                            "select * from foo",
                            {
                                "Description": "a view",
                                "Parameters": [],
                                "IsWithinDirectProviderView": False,
                            },
                            version=1,
                        )
                    ],
                ),
                # update
                httpx.Response(200, json=[]),
                # registration check
                httpx.Response(200, json=[{"Version": 2}]),
            ]
        )

        # and the desired leaves it empty
        sut = lumi.ViewResource(
            id="my-view", provider="Views.Unit.Test", sql="select * from foo", description="a view"
        )
        old_state = SimpleNamespace(provider="Views.Unit.Test")
        # when we update it
        state = sut.update(self.client, old_state)
        # then no change is detected because False is a server default
        # and the user has not specified it
        assert state is None

    def test_update_with_modified_saved_option(self, respx_mock):
        # given an existing remote
        exec_id = "abcdefg"
        put: Route = respx_mock.put(
            "/honeycomb/api/SqlBackground", headers=[("Content-type", "text/plain")]
        ).mock(side_effect=[httpx.Response(202, json={"executionId": exec_id})] * 3)

        respx_mock.get(f"/honeycomb/api/SqlBackground/{exec_id}").mock(
            side_effect=[httpx.Response(200, json={"status": TaskStatus.RAN_TO_COMPLETION})] * 3
        )

        respx_mock.get(f"/honeycomb/api/SqlBackground/{exec_id}/jsonproper").mock(
            side_effect=[
                # read
                httpx.Response(
                    200,
                    json=[
                        make_sys_file(
                            "select * from foo",
                            {"Description": "a view", "Parameters": [], "DocumentationLink": "bar.com"},
                            version=1,
                        )
                    ],
                ),
                # update
                httpx.Response(200, json=[]),
                # registration check
                httpx.Response(200, json=[{"Version": 2}]),
            ]
        )

        # and a desired adds a saved option (documentationLink)
        sut = lumi.ViewResource(
            id="my-view",
            provider="Views.Unit.Test",
            sql="select * from foo",
            description="a view",
            documentation_link="foo.com",
        )
        old_state = SimpleNamespace(provider="Views.Unit.Test")
        # when we update it
        state = sut.update(self.client, old_state)
        # then a change is detected
        assert state == {"provider": "Views.Unit.Test"}
        # and we created a new view
        request = put.calls[1].request
        assert request.method == "PUT"
        expected = textwrap.dedent("""\
            @x = use Sys.Admin.SetupView
            --provider="Views.Unit.Test"
            --description="a view"
            --documentationLink="foo.com"
            ----
            select * from foo
            enduse;
            select * from @x;
        """)
        assert request.content.decode("utf8") == expected

    def test_update_with_modified_sql(self, respx_mock):
        # given an existing remote
        exec_id = "abcdefg"
        put: Route = respx_mock.put(
            "/honeycomb/api/SqlBackground", headers=[("Content-type", "text/plain")]
        ).mock(side_effect=[httpx.Response(202, json={"executionId": exec_id})] * 3)

        respx_mock.get(f"/honeycomb/api/SqlBackground/{exec_id}").mock(
            side_effect=[httpx.Response(200, json={"status": TaskStatus.RAN_TO_COMPLETION})] * 3
        )

        respx_mock.get(f"/honeycomb/api/SqlBackground/{exec_id}/jsonproper").mock(
            side_effect=[
                httpx.Response(
                    200,
                    json=[
                        make_sys_file(
                            "select * from foo", {"Description": "a view", "Parameters": []}, version=1
                        )
                    ],
                ),
                # update
                httpx.Response(200, json=[]),
                # registration check
                httpx.Response(200, json=[{"Version": 2}]),
            ]
        )
        # and a desired changes the sql
        sut = lumi.ViewResource(
            id="my-view",
            provider="Views.Unit.Test",
            sql="select * from something_else",
            description="a view",
        )
        old_state = SimpleNamespace(provider="Views.Unit.Test")
        # when we update it
        state = sut.update(self.client, old_state)
        # then a change is detected
        assert state == {"provider": "Views.Unit.Test"}
        # and we created a new view
        request = put.calls[1].request
        assert request.method == "PUT"
        expected = textwrap.dedent("""\
            @x = use Sys.Admin.SetupView
            --provider="Views.Unit.Test"
            --description="a view"
            ----
            select * from something_else
            enduse;
            select * from @x;
        """)
        assert request.content.decode("utf8") == expected

    def test_update_with_extra_parameter(self, respx_mock):
        # given an existing remote
        exec_id = "abcdefg"
        put: Route = respx_mock.put(
            "/honeycomb/api/SqlBackground", headers=[("Content-type", "text/plain")]
        ).mock(side_effect=[httpx.Response(202, json={"executionId": exec_id})] * 3)

        respx_mock.get(f"/honeycomb/api/SqlBackground/{exec_id}").mock(
            side_effect=[httpx.Response(200, json={"status": TaskStatus.RAN_TO_COMPLETION})] * 3
        )

        respx_mock.get(f"/honeycomb/api/SqlBackground/{exec_id}/jsonproper").mock(
            side_effect=[
                httpx.Response(
                    200,
                    json=[
                        make_sys_file(
                            "select * from foo", {"Description": "a view", "Parameters": []}, version=1
                        )
                    ],
                ),
                # update
                httpx.Response(200, json=[]),
                # registration check
                httpx.Response(200, json=[{"Version": 2}]),
            ]
        )
        # and a desired that is the same but adds a parameter
        sut = lumi.ViewResource(
            id="my-view",
            provider="Views.Unit.Test",
            sql="select * from foo",
            description="a view",
            parameters=[
                lumi.Parameter(
                    name="p1",
                    type=lumi.ParameterType.Int,
                    value=23,
                    set_as_default_value=False,
                    tooltip="p1 is nice",
                )
            ],
        )
        old_state = SimpleNamespace(provider="Views.Unit.Test")
        # when we update it
        state = sut.update(self.client, old_state)
        # then the new parameter change is detected
        assert state == {"provider": "Views.Unit.Test"}
        # and we update the view with the parameter
        request = put.calls[1].request
        assert request.method == "PUT"
        expected = textwrap.dedent("""\
            @x = use Sys.Admin.SetupView
            --provider="Views.Unit.Test"
            --description="a view"
            --parameters
            p1,Int,23,false,"p1 is nice"
            ----
            select * from foo
            enduse;
            select * from @x;
        """)
        assert request.content.decode("utf8") == expected

    def test_update_with_removed_parameter(self, respx_mock):
        # given an existing view with one parameter
        exec_id = "abcdefg"
        put: Route = respx_mock.put(
            "/honeycomb/api/SqlBackground", headers=[("Content-type", "text/plain")]
        ).mock(side_effect=[httpx.Response(202, json={"executionId": exec_id})] * 3)

        respx_mock.get(f"/honeycomb/api/SqlBackground/{exec_id}").mock(
            side_effect=[httpx.Response(200, json={"status": TaskStatus.RAN_TO_COMPLETION})] * 3
        )

        respx_mock.get(f"/honeycomb/api/SqlBackground/{exec_id}/jsonproper").mock(
            side_effect=[
                httpx.Response(
                    200,
                    json=[
                        make_sys_file(
                            "select * from foo",
                            {
                                "Description": "a view",
                                "Parameters": [{"Name": "existing", "Type": "Text"}],
                            },
                            version=1,
                        )
                    ],
                ),
                # update
                httpx.Response(200, json=[]),
                # registration check
                httpx.Response(200, json=[{"Version": 2}]),
            ]
        )
        # and a desired that removes the parameter
        sut = lumi.ViewResource(
            id="my-view", provider="Views.Unit.Test", sql="select * from foo", description="a view"
        )
        old_state = SimpleNamespace(provider="Views.Unit.Test")
        # when we update it
        state = sut.update(self.client, old_state)
        # then the parameter change is detected
        assert state == {"provider": "Views.Unit.Test"}
        # and we created a new view with none
        request = put.calls[1].request
        assert request.method == "PUT"
        expected = textwrap.dedent("""\
            @x = use Sys.Admin.SetupView
            --provider="Views.Unit.Test"
            --description="a view"
            ----
            select * from foo
            enduse;
            select * from @x;
        """)
        assert request.content.decode("utf8") == expected

    def test_update_with_modified_parameter(self, respx_mock):
        # given an existing view with integer parameter p1
        exec_id = "abcdefg"
        put: Route = respx_mock.put(
            "/honeycomb/api/SqlBackground", headers=[("Content-type", "text/plain")]
        ).mock(side_effect=[httpx.Response(202, json={"executionId": exec_id})] * 3)

        respx_mock.get(f"/honeycomb/api/SqlBackground/{exec_id}").mock(
            side_effect=[httpx.Response(200, json={"status": TaskStatus.RAN_TO_COMPLETION})] * 3
        )

        respx_mock.get(f"/honeycomb/api/SqlBackground/{exec_id}/jsonproper").mock(
            side_effect=[
                # read
                httpx.Response(
                    200,
                    json=[
                        make_sys_file(
                            "select * from foo",
                            {"Description": "a view", "Parameters": [{"Name": "p1", "Type": "Int"}]},
                            version=1,
                        )
                    ],
                ),
                httpx.Response(200, json=[]),  # update
                httpx.Response(200, json=[{"Version": 2}]),  # registration check
            ]
        )
        # and a desired that changes the parameter type to text
        sut = lumi.ViewResource(
            id="my-view",
            provider="Views.Unit.Test",
            sql="select * from foo",
            description="a view",
            parameters=[
                lumi.Parameter(
                    name="p1",
                    type=lumi.ParameterType.Text,
                    value="some text",
                    set_as_default_value=False,
                    tooltip="p1 is nice",
                )
            ],
        )
        old_state = SimpleNamespace(provider="Views.Unit.Test")
        # when we update it
        state = sut.update(self.client, old_state)
        # then the parameter change is detected
        assert state == {"provider": "Views.Unit.Test"}
        # and we modify the view with a text parameter
        request = put.calls[1].request
        assert request.method == "PUT"
        expected = textwrap.dedent("""\
            @x = use Sys.Admin.SetupView
            --provider="Views.Unit.Test"
            --description="a view"
            --parameters
            p1,Text,"some text",false,"p1 is nice"
            ----
            select * from foo
            enduse;
            select * from @x;
        """)
        assert request.content.decode("utf8") == expected

    def test_update_useasdefault_changes_value(self, respx_mock):
        # given an existing view with integer parameter p1
        # with a default of zero
        exec_id = "abcdefg"
        put: Route = respx_mock.put(
            "/honeycomb/api/SqlBackground", headers=[("Content-type", "text/plain")]
        ).mock(side_effect=[httpx.Response(202, json={"executionId": exec_id})] * 3)

        respx_mock.get(f"/honeycomb/api/SqlBackground/{exec_id}").mock(
            side_effect=[httpx.Response(200, json={"status": TaskStatus.RAN_TO_COMPLETION})] * 3
        )

        respx_mock.get(f"/honeycomb/api/SqlBackground/{exec_id}/jsonproper").mock(
            side_effect=[
                httpx.Response(
                    200,
                    json=[
                        make_sys_file(
                            "select * from foo",
                            {
                                "Description": "a view",
                                "Parameters": [
                                    {
                                        "Name": "p1",
                                        "Type": "Int",
                                        "DefaultValue": 0,
                                        "Description": "p1 is nice",
                                    }
                                ],
                            },
                            version=1,
                        )
                    ],
                ),
                httpx.Response(200, json=[]),  # update
                httpx.Response(200, json=[{"Version": 2}]),  # registration check
            ]
        )
        # and a desired with setAsDefault=true which means to use the value as a default
        sut = lumi.ViewResource(
            id="my-view",
            provider="Views.Unit.Test",
            sql="select * from foo",
            description="a view",
            parameters=[
                lumi.Parameter(
                    name="p1",
                    type=lumi.ParameterType.Int,
                    value=20,
                    set_as_default_value=True,
                    tooltip="p1 is nice",
                )
            ],
        )
        old_state = SimpleNamespace(provider="Views.Unit.Test")
        # when we update it
        state = sut.update(self.client, old_state)
        # then the parameter change is detected
        assert state == {"provider": "Views.Unit.Test"}
        # and we modify the view with the new value
        request = put.calls[1].request
        assert request.method == "PUT"
        expected = textwrap.dedent("""\
            @x = use Sys.Admin.SetupView
            --provider="Views.Unit.Test"
            --description="a view"
            --parameters
            p1,Int,20,true,"p1 is nice"
            ----
            select * from foo
            enduse;
            select * from @x;
        """)
        assert request.content.decode("utf8") == expected

    def test_update_useasdefault_same_value(self, respx_mock):
        # given an existing view with integer parameter p1
        # with a default of 20
        exec_id = "abcdefg"
        respx_mock.put("/honeycomb/api/SqlBackground", headers=[("Content-type", "text/plain")]).mock(
            side_effect=[httpx.Response(202, json={"executionId": exec_id})] * 3
        )

        respx_mock.get(f"/honeycomb/api/SqlBackground/{exec_id}").mock(
            side_effect=[httpx.Response(200, json={"status": TaskStatus.RAN_TO_COMPLETION})] * 3
        )

        respx_mock.get(f"/honeycomb/api/SqlBackground/{exec_id}/jsonproper").mock(
            side_effect=[
                # read
                httpx.Response(
                    200,
                    json=[
                        make_sys_file(
                            "select * from foo",
                            {
                                "Description": "a view",
                                "Parameters": [
                                    {
                                        "Name": "p1",
                                        "Type": "Int",
                                        "DefaultValue": 20,
                                        "Description": "p1 is nice",
                                    }
                                ],
                            },
                            version=1,
                        )
                    ],
                ),
                httpx.Response(200, json=[]),  # update
                httpx.Response(200, json=[{"Version": 2}]),  # registration check
            ]
        )
        # and a desired with setAsDefault but a value also 20
        sut = lumi.ViewResource(
            id="my-view",
            provider="Views.Unit.Test",
            sql="select * from foo",
            description="a view",
            parameters=[
                lumi.Parameter(
                    name="p1",
                    type=lumi.ParameterType.Int,
                    value=20,
                    set_as_default_value=True,
                    tooltip="p1 is nice",
                )
            ],
        )
        old_state = SimpleNamespace(provider="Views.Unit.Test")
        # when we update it
        state = sut.update(self.client, old_state)
        # then there is no change
        assert state is None

    def test_update_with_renamed_parameter(self, respx_mock):
        # given an existing view with integer parameter p1
        exec_id = "abcdefg"
        put: Route = respx_mock.put(
            "/honeycomb/api/SqlBackground", headers=[("Content-type", "text/plain")]
        ).mock(side_effect=[httpx.Response(202, json={"executionId": exec_id})] * 3)

        respx_mock.get(f"/honeycomb/api/SqlBackground/{exec_id}").mock(
            side_effect=[httpx.Response(200, json={"status": TaskStatus.RAN_TO_COMPLETION})] * 3
        )

        respx_mock.get(f"/honeycomb/api/SqlBackground/{exec_id}/jsonproper").mock(
            side_effect=[
                # read
                httpx.Response(
                    200,
                    json=[
                        make_sys_file(
                            "select * from foo",
                            {
                                "Description": "a view",
                                "Parameters": [{"Name": "p1", "Type": "Int", "ExtraField": "boo"}],
                            },
                            version=1,
                        )
                    ],
                ),
                httpx.Response(200, json=[]),  # update
                httpx.Response(200, json=[{"Version": 2}]),  # registration check
            ]
        )
        # and a desired renames p1 to p2
        sut = lumi.ViewResource(
            id="my-view",
            provider="Views.Unit.Test",
            sql="select * from foo",
            description="a view",
            parameters=[
                lumi.Parameter(
                    name="p2",
                    type=lumi.ParameterType.Int,
                    value=12,
                    set_as_default_value=False,
                    tooltip="p1 is nice",
                )
            ],
        )
        old_state = SimpleNamespace(provider="Views.Unit.Test")
        # when we update it
        state = sut.update(self.client, old_state)
        # then the parameter change is detected
        assert state == {"provider": "Views.Unit.Test"}
        # and we modify the view to only have p2
        request = put.calls[1].request
        assert request.method == "PUT"
        expected = textwrap.dedent("""\
            @x = use Sys.Admin.SetupView
            --provider="Views.Unit.Test"
            --description="a view"
            --parameters
            p2,Int,12,false,"p1 is nice"
            ----
            select * from foo
            enduse;
            select * from @x;
        """)
        assert request.content.decode("utf8") == expected

    def test_update_provider_name(self, respx_mock):
        exec_id = "abcdefg"
        put: Route = respx_mock.put(
            "/honeycomb/api/SqlBackground", headers=[("Content-type", "text/plain")]
        ).mock(side_effect=[httpx.Response(202, json={"executionId": exec_id})] * 4)

        respx_mock.get(f"/honeycomb/api/SqlBackground/{exec_id}").mock(
            side_effect=[httpx.Response(200, json={"status": TaskStatus.RAN_TO_COMPLETION})] * 4
        )

        respx_mock.get(f"/honeycomb/api/SqlBackground/{exec_id}/jsonproper").mock(
            side_effect=[
                httpx.Response(200, json=[]),  # delete
                httpx.Response(200, json=[]),  # de-reg complete
                httpx.Response(200, json=[]),  # update
                httpx.Response(200, json=[{"Version": 1}]),  # reg complete
            ]
        )

        # given a view which has been created with a provider name
        old_state = SimpleNamespace(provider="Views.Unit.Test")
        # when we change the provider name
        sut = lumi.ViewResource(
            id="my-view", provider="Views.Unit.NotTheSame", sql="select * from foo", description="a view"
        )
        # and update
        sut.update(self.client, old_state)
        # then the existing provider gets deleted
        first = put.calls[0].request
        expected = textwrap.dedent("""\
            @x = use Sys.Admin.SetupView
            --provider=Views.Unit.Test
            --deleteProvider
            ----
            select 1 as deleting
            enduse;
            select * from @x;
        """)
        assert first.content.decode() == expected
        # and a new one gets created
        request = put.calls[2].request
        expected = textwrap.dedent("""\
            @x = use Sys.Admin.SetupView
            --provider="Views.Unit.NotTheSame"
            --description="a view"
            ----
            select * from foo
            enduse;
            select * from @x;
        """)
        assert request.content.decode("utf8") == expected

    def test_update_with_no_changes_and_table_param(self, respx_mock):
        # given an existing remote

        exec_id = "abcdefg"
        put: Route = respx_mock.put(
            "/honeycomb/api/SqlBackground", headers=[("Content-type", "text/plain")]
        ).mock(side_effect=[httpx.Response(202, json={"executionId": exec_id})])

        respx_mock.get(f"/honeycomb/api/SqlBackground/{exec_id}").mock(
            side_effect=[httpx.Response(200, json={"status": TaskStatus.RAN_TO_COMPLETION})]
        )

        respx_mock.get(f"/honeycomb/api/SqlBackground/{exec_id}/jsonproper").mock(
            side_effect=[
                httpx.Response(
                    200,
                    json=[
                        make_sys_file(
                            "select * from #PARAMETERVALUE(p1);",
                            {
                                "Description": "a view",
                                "Parameters": [
                                    {
                                        "Columns": [
                                            {
                                                "IsPrimaryKey": "false",
                                                "IsMain": "false",
                                                "IsRequiredByProvider": "false",
                                                "MandatoryForActions": None,
                                                "ClientIds": None,
                                                "Name": "3 + 4",
                                                "Type": "BigInt",
                                                "Description": None,
                                                "DisplayName": "3 + 4",
                                                "ConditionUsage": 0,
                                                "SampleValues": None,
                                                "AllowedValues": None,
                                            }
                                        ],
                                        "Name": "p1",
                                        "Type": "Table",
                                        "Description": "I am a description"
                                        "\nAvailable columns:\n3 + 4 (BigInt)",
                                        "DisplayName": "p1",
                                        "ConditionUsage": 0,
                                    },
                                    {
                                        "Columns": [
                                            {
                                                "IsPrimaryKey": "false",
                                                "IsMain": "false",
                                                "IsRequiredByProvider": "false",
                                                "MandatoryForActions": None,
                                                "ClientIds": None,
                                                "Name": "5 + 6",
                                                "Type": "BigInt",
                                                "Description": None,
                                                "DisplayName": "5 + 6",
                                                "ConditionUsage": 0,
                                                "SampleValues": None,
                                                "AllowedValues": None,
                                            }
                                        ],
                                        "Name": "p2",
                                        "Type": "Table",
                                        "Description": "\nAvailable columns:\n5 + 6 (BigInt)",
                                        "DisplayName": "p2",
                                        "ConditionUsage": 0,
                                    },
                                ],
                            },
                            version=1,
                        )
                    ],
                )
            ]
        )

        p1_value = lumi.Variable(name="p1", type=lumi.VariableType.Table, sql="select * from 3 + 4")

        p2_value = lumi.Variable(name="p2", type=lumi.VariableType.Table, sql="select a,b,c from Test")
        # and a desired state that is the same;
        # new line at the end of script should not count as change
        sut = lumi.ViewResource(
            id="my-view",
            provider="Views.Unit.Test",
            sql="""select * from #PARAMETERVALUE(p1);""",
            description="a view",
            parameters=[
                lumi.Parameter(
                    name="p1",
                    value=p1_value,
                    is_mandatory=False,
                    tooltip="I am a description",
                    type=lumi.ParameterType.Table,
                ),
                lumi.Parameter(
                    name="p2",
                    value=p2_value,
                    is_mandatory=False,
                    type=lumi.ParameterType.Table,
                    tooltip="",
                ),
            ],
        )

        old_state = SimpleNamespace(provider="Views.Unit.Test")
        # when we update it
        state = sut.update(self.client, old_state)
        # then the state is None
        assert state is None
        # and the read query was sent
        request = put.calls[0].request
        assert request.method == "PUT"
        expected = textwrap.dedent("""\
               select f.Content, r.Version from sys.file as f
               join sys.registration as r on r.Name = 'Views.Unit.Test'
               where path = 'databaseproviders/Views/Unit/Test.sql'
               order by r.Version asc
               limit 1
           """)
        assert request.content.decode() == expected
        # and we read the remote but didn't write anything
        assert len(respx_mock.calls) == 3

    @staticmethod
    def test_deps_none():
        sut = lumi.ViewResource(
            id="my-view", provider="Views.Unit.Test", sql="select * from foo", description="a view"
        )
        assert sut.deps() == []

    @staticmethod
    def test_deps_extra():
        sut = lumi.ViewResource(
            id="my-view",
            provider="Views.Unit.Test",
            sql="select * from foo",
            description="a view",
            dependencies=[1, 2, 3],
        )
        assert sut.deps() == [1, 2, 3]

    @staticmethod
    def test_deps_with_inline_resource():
        # given an inline resource
        prop_key = DefinitionRef(
            id="test-key", domain=Domain.Instrument, scope="TestScope", code="TestCode"
        )
        inline = lumi.InlinePropertiesResource(
            id="test-inline-props",
            provider="NewProvider",  # Different provider
            properties=[
                lumi.InlineProperty(
                    key=prop_key,
                    name="Test Property",
                    data_type=lumi.InlineDataType.Text,
                    description="A test property",
                )
            ],
        )
        # when we make a view that depends on it (eg because it references some of the
        # columns)
        sut = lumi.ViewResource(
            id="my-view",
            provider="Views.Unit.Test",
            sql="select * from foo",
            description="a view",
            dependencies=[inline],
        )
        # then the dependencies include the inline
        assert sut.deps() == [inline]

    def test_delete(self, respx_mock):
        exec_id = "abcdefg"
        put: Route = respx_mock.put(
            "/honeycomb/api/SqlBackground", headers=[("Content-type", "text/plain")]
        ).mock(side_effect=[httpx.Response(202, json={"executionId": exec_id})] * 2)

        respx_mock.get(f"/honeycomb/api/SqlBackground/{exec_id}").mock(
            side_effect=[httpx.Response(200, json={"status": TaskStatus.RAN_TO_COMPLETION})] * 2
        )

        respx_mock.get(f"/honeycomb/api/SqlBackground/{exec_id}/jsonproper").mock(
            side_effect=[
                # delete
                httpx.Response(200, json=[]),  # delete
                httpx.Response(200, json=[]),  # de-registration check
            ]
        )
        sut = lumi.ViewResource(
            id="my-view", provider="Views.Unit.Test", sql="""select * from 2+2""", description="a view"
        )

        # given a view that exists in the remote
        old_state = SimpleNamespace(provider="Views.Unit.Test")
        # when we delete it
        sut.delete(self.client, old_state)
        # then sql to remove the view
        request = put.calls[0].request
        expected = textwrap.dedent("""\
            @x = use Sys.Admin.SetupView
            --provider=Views.Unit.Test
            --deleteProvider
            ----
            select 1 as deleting
            enduse;
            select * from @x;
        """)
        assert request.content.decode() == expected

    def test_delete_does_registration_check(self, respx_mock):
        exec_id = "abcdefg"
        put: Route = respx_mock.put(
            "/honeycomb/api/SqlBackground", headers=[("Content-type", "text/plain")]
        ).mock(side_effect=[httpx.Response(202, json={"executionId": exec_id})] * 3)

        respx_mock.get(f"/honeycomb/api/SqlBackground/{exec_id}").mock(
            side_effect=[httpx.Response(200, json={"status": TaskStatus.RAN_TO_COMPLETION})] * 3
        )

        respx_mock.get(f"/honeycomb/api/SqlBackground/{exec_id}/jsonproper").mock(
            side_effect=[
                httpx.Response(200, json=[]),  # delete
                httpx.Response(200, json=[{"Version": 5}]),  # still registered
                httpx.Response(200, json=[]),  # deregistered
            ]
        )

        sut = lumi.ViewResource(
            id="my-view", provider="Views.Unit.Test", sql="""select * from 2+2""", description="a view"
        )

        # given a view that exists in the remote
        old_state = SimpleNamespace(provider="Views.Unit.Test")
        # when we delete it
        sut.delete(self.client, old_state)
        # the registration check was performed twice because we waited for
        # the view to be removed
        check = put.calls[2].request
        expected = textwrap.dedent("""\
            select Version from sys.registration where Name='Views.Unit.Test'
            order by Version asc
            limit 1
        """)
        assert check.content.decode("utf8") == expected

    def test_delete_completes_when_reg_incomplete(self, respx_mock, capsys):
        # given de-registration takes more than 3 tries
        exec_id = "abcdefg"
        put: Route = respx_mock.put(
            "/honeycomb/api/SqlBackground", headers=[("Content-type", "text/plain")]
        ).mock(side_effect=[httpx.Response(202, json={"executionId": exec_id})] * 4)

        respx_mock.get(f"/honeycomb/api/SqlBackground/{exec_id}").mock(
            side_effect=[httpx.Response(200, json={"status": TaskStatus.RAN_TO_COMPLETION})] * 4
        )

        respx_mock.get(f"/honeycomb/api/SqlBackground/{exec_id}/jsonproper").mock(
            side_effect=[
                httpx.Response(200, json=[]),  # delete
                httpx.Response(200, json=[{"Version": 5}]),  # still registered
                httpx.Response(200, json=[{"Version": 5}]),  # still registered
                httpx.Response(200, json=[{"Version": 5}]),  # still registered
            ]
        )

        sut = lumi.ViewResource(
            id="my-view", provider="Views.Unit.Test", sql="""select * from 2+2""", description="a view"
        )
        # given a view that exists in the remnte
        old_state = SimpleNamespace(provider="Views.Unit.Test")
        # when we delete it
        sut.delete(self.client, old_state)
        # a delete was sent and the registration check was performed 3 times
        check = put.calls[3].request
        expected = textwrap.dedent("""\
            select Version from sys.registration where Name='Views.Unit.Test'
            order by Version asc
            limit 1
        """)
        assert check.content.decode("utf8") == expected
        # check warning is returned
        captured = capsys.readouterr()
        assert captured.err == (
            f"warning: no view deregistration after "
            f"{lumi.ViewResource.Registration.tries}"
            f" tries for Views.Unit.Test"
        )

    def test_dump(self):
        sut = lumi.ViewResource(
            id="my-view",
            provider="Views.Unit.Test",
            sql="select * from foo;",
            description="a view",
            documentation_link="http://example.com/docs",
            variable_shape=True,
            parameters=[
                lumi.Parameter(
                    name="p1",
                    type=lumi.ParameterType.Int,
                    value=23,
                    set_as_default_value=True,
                    tooltip="Parameter 1"
                )
            ]
        )
        result = sut.model_dump(context={"style": "dump"})
        # id field is globally excluded, so it won't appear in dumps
        assert "id" not in result
        assert result["provider"] == "Views.Unit.Test"
        assert result["sql"] == "select * from foo;"
        assert result["description"] == "a view"
        assert result["documentation_link"] == "http://example.com/docs"
        assert result["variable_shape"] is True
        assert len(result["parameters"]) == 1
        assert result["parameters"][0]["name"] == "p1"
        assert result["parameters"][0]["type"] == "Int"
        assert result["parameters"][0]["value"] == 23

    def test_undump(self):
        data = {
            "provider": "Views.Unit.Test",
            "sql": "select * from foo;",
            "description": "a view for undump testing",
            "documentation_link": "http://example.com/docs",
            "variable_shape": True,
            "parameters": [
                {
                    "name": "p1",
                    "type": "Int",
                    "value": 23,
                    "set_as_default_value": True,
                    "tooltip": "Parameter 1"
                }
            ]
        }
        result = lumi.ViewResource.model_validate(data, context={"style": "dump", "id": "my-view"})
        assert result.id == "my-view"
        assert result.provider == "Views.Unit.Test"
        assert result.sql == "select * from foo;"
        assert result.description == "a view for undump testing"
        assert result.documentation_link == "http://example.com/docs"
        assert result.variable_shape is True
        assert len(result.parameters) == 1
        assert result.parameters[0].name == "p1"
        assert result.parameters[0].type == lumi.ParameterType.Int
        assert result.parameters[0].value == 23


@pytest.mark.respx(base_url=TEST_BASE)
class DescribeBackoffHandler:
    client = httpx.Client(base_url=TEST_BASE, event_hooks={"response": [response_hook]})

    @staticmethod
    def test_pause_time_smaller_than_max_pause_time():
        backoff_handler_test = BackoffHandler(pause_time=0.5, max_pause_time=20, beta=1.0001)
        backoff_handler_test.sleep()
        pytest.approx(0.50005, backoff_handler_test.pause_time, 0.00001)

    @staticmethod
    def test_pause_time_equals_max_pause_time():
        backoff_handler_test = BackoffHandler(pause_time=2, max_pause_time=2, beta=1.001)
        backoff_handler_test.sleep()
        assert backoff_handler_test.pause_time == 2

    @staticmethod
    def test_pause_time_bigger_than_max_pause_time():
        with pytest.raises(ValueError) as ex:
            BackoffHandler(pause_time=100, max_pause_time=20, beta=1.1)
            assert "Pause time must be between 0.1 and 20, both inclusive." in str(ex.value)

    @staticmethod
    def test_default_optional_values():
        backoff_handler_test = BackoffHandler()
        backoff_handler_test.sleep()
        pytest.approx(0.1005012520859401, backoff_handler_test.pause_time, 0.00001)

    @staticmethod
    def test_call_1000_times_pause_time_equals_max_pause_time():
        backoff_handler_test = BackoffHandler()
        # I have checked that this is constant after 922 requests
        for i in range(1000):
            backoff_handler_test._update_pause_time()
        assert backoff_handler_test.pause_time == 10


@pytest.mark.respx(base_url=TEST_BASE)
class DescribeQuery:
    client = httpx.Client(base_url=TEST_BASE, event_hooks={"response": [response_hook]})

    def test_wait_for_background_switch_case_correct(self, respx_mock):
        exec_id = "abcdefg"
        respx_mock.get(f"/honeycomb/api/SqlBackground/{exec_id}").mock(
            side_effect=[
                httpx.Response(200, json={"status": TaskStatus.WAITING_FOR_ACTIVATION}),
                httpx.Response(200, json={"status": TaskStatus.WAITING_TO_RUN}),
                httpx.Response(200, json={"status": TaskStatus.CREATED}),
                httpx.Response(200, json={"status": TaskStatus.WAITING_FOR_CHILDREN_TO_COMPLETE}),
                httpx.Response(200, json={"status": TaskStatus.RUNNING}),
                httpx.Response(200, json={"status": TaskStatus.RAN_TO_COMPLETION}),
            ]
        )
        assert lumi.wait_for_background(client=self.client, execution_id=exec_id) is False
        assert lumi.wait_for_background(client=self.client, execution_id=exec_id) is False
        assert lumi.wait_for_background(client=self.client, execution_id=exec_id) is False
        assert lumi.wait_for_background(client=self.client, execution_id=exec_id) is False
        assert lumi.wait_for_background(client=self.client, execution_id=exec_id) is False
        assert lumi.wait_for_background(client=self.client, execution_id=exec_id) is True

    @pytest.mark.parametrize("status", [TaskStatus.FAULTED, TaskStatus.CANCELED])
    def test_wait_for_background_status_faulted_throws(self, respx_mock, status):
        exec_id = "abcdefg"
        respx_mock.get(f"/honeycomb/api/SqlBackground/{exec_id}").mock(
            side_effect=[
                httpx.Response(200, json={"status": TaskStatus.WAITING_FOR_ACTIVATION}),
                httpx.Response(200, json={"status": status}),
            ]
        )
        assert lumi.wait_for_background(client=self.client, execution_id=exec_id) is False
        with pytest.raises(RuntimeError) as ex:
            lumi.wait_for_background(client=self.client, execution_id=exec_id)
        assert str(ex.value) == f"Error, query {status}\n"

    def test_wait_for_background_status_unknown_throws(self, respx_mock):
        exec_id = "abcdefg"
        respx_mock.get(f"/honeycomb/api/SqlBackground/{exec_id}").mock(
            side_effect=[
                httpx.Response(200, json={"status": TaskStatus.WAITING_FOR_ACTIVATION}),
                httpx.Response(200, json={"status": "someunknownstatus"}),
            ]
        )
        assert lumi.wait_for_background(client=self.client, execution_id=exec_id) is False
        with pytest.raises(RuntimeError) as ex:
            lumi.wait_for_background(client=self.client, execution_id=exec_id)
        assert str(ex.value) == "Unknown status: someunknownstatus. Execution id: abcdefg"


@pytest.mark.respx(base_url=TEST_BASE)
class DescribeInlinePropertiesResource:
    client = httpx.Client(base_url=TEST_BASE, event_hooks={"response": [response_hook]})

    @pytest.fixture()
    def default_content(self):
        return [{
            "Content": """Key,Name,DataType,Description,IsMain,AsAt\n"""
                       """Domain/Scope/Code,PropName,Boolean,A description,false,""",
            "Error": "",
        }]

    def test_create_no_properties(self, respx_mock: Router, default_content):
        setup_sql_background_routes(respx_mock, result_data=default_content)
        # given an inline properties resource with zero properties
        sut = lumi.InlinePropertiesResource(
            id="test-inline-props",
            provider="TestProvider",
            properties=[
            ],
        )
        # when we create it
        sut.create(self.client)
        # then the request sql creates the provider extension but with no properties
        expected = textwrap.dedent("""\
            select * from Sys.Admin.Lusid.Provider.Configure
                where Provider = 'TestProvider'
                and WriteAction = 'Set'\n
            ;
        """)
        lumi_query = respx_mock.calls[0].request.content
        assert lumi_query.decode() == expected

    def test_create_basic_properties(self, respx_mock: Router, default_content):
        setup_sql_background_routes(respx_mock, result_data=default_content)
        # given an inline properties resource with basic properties
        prop_one = DefinitionRef(
            id="test-key-1", domain=Domain.Instrument, scope="TestScope", code="Prop1"
        )
        prop_two = DefinitionRef(
            id="test-key-2", domain=Domain.Instrument, scope="TestScope", code="Prop2"
        )
        sut = lumi.InlinePropertiesResource(
            id="test-inline-props",
            provider="TestProvider",
            properties=[
                lumi.InlineProperty(
                    key=prop_one,
                    name="Test Property",
                    data_type=lumi.InlineDataType.Text,
                    description="A test property",
                ),
                lumi.InlineProperty(
                    key=prop_two,
                    name="Test Another",
                    data_type=lumi.InlineDataType.Text,
                    description="Another test property",
                )
            ],
        )
        # when we create it
        state = sut.create(self.client)
        # then the request sql matches
        expected = textwrap.dedent("""\
            @keysToCatalog = values
                ('Instrument/TestScope/Prop1', 'Test Property', 'Text', 'A test property', null, null),('Instrument/TestScope/Prop2', 'Test Another', 'Text', 'Another test property', null, null)
            ;
            @config = select
                column1 as [Key], column2 as Name, column3 as DataType, column4 as Description, column5 as IsMain, column6 as AsAt
                from @keysToCatalog
            ;
            select * from Sys.Admin.Lusid.Provider.Configure
                where Provider = 'TestProvider'
                and Configuration = @config
                and WriteAction = 'Set'\n
            ;
        """)  # noqa: E501
        lumi_query = respx_mock.calls[0].request.content
        assert lumi_query.decode() == expected
        # and the state is returned
        assert state == {
            "provider": "TestProvider",
            "source_version": "139695101b9b129d76abd7456b3223c3c1d31789b80dc20b752e46963ae56375",
            "remote_version": "8b16bcb769741f61d25e92f4966ea3694fd643bd7fdb7d11c72ad7ade7ca05dd",
            "extension": None
        }

    def test_create_with_asat(self, respx_mock: Router, default_content):
        setup_sql_background_routes(respx_mock, result_data=default_content)
        # given an inline properties resource with basic properties
        prop_key = DefinitionRef(
            id="test-key", domain=Domain.Instrument, scope="TestScope", code="TestCode"
        )
        sut = lumi.InlinePropertiesResource(
            id="test-inline-props",
            provider="TestProvider",
            properties=[
                lumi.InlineProperty(
                    key=prop_key,
                    name="Test Property",
                    data_type=lumi.InlineDataType.Text,
                    description="A test property",
                    as_at=datetime(2025, 2, 3, 15, 41),
                )
            ],
        )
        # when we create it
        state = sut.create(self.client)
        # then the request sql matches
        expected = textwrap.dedent("""\
            @keysToCatalog = values
                ('Instrument/TestScope/TestCode', 'Test Property', 'Text', 'A test property', null, '2025-02-03 15:41:00')
            ;
            @config = select
                column1 as [Key], column2 as Name, column3 as DataType, column4 as Description, column5 as IsMain, column6 as AsAt
                from @keysToCatalog
            ;
            select * from Sys.Admin.Lusid.Provider.Configure
                where Provider = 'TestProvider'
                and Configuration = @config
                and WriteAction = 'Set'\n
            ;
        """)  # noqa
        lumi_query = respx_mock.calls[0].request.content
        assert lumi_query.decode() == expected
        # and the state is returned
        assert state == {
            "provider": "TestProvider",
            "source_version": "bc34d5f5a40b4cbb20dd2035cbe849f7c75f81210657035a9bb108290e3512ad",
            "remote_version": "8b16bcb769741f61d25e92f4966ea3694fd643bd7fdb7d11c72ad7ade7ca05dd",
            "extension": None
        }

    def test_create_with_provider_extension(self, respx_mock, default_content):
        setup_sql_background_routes(respx_mock, result_data=default_content)
        prop_key = DefinitionRef(
            id="test-key", domain=Domain.Instrument, scope="TestScope", code="TestCode"
        )
        # given an inline properties resource with provider extension
        sut = lumi.InlinePropertiesResource(
            id="test-inline-props",
            provider="TestProvider",
            provider_name_extension="Extension",
            properties=[
                lumi.InlineProperty(
                    key=prop_key,
                    name="Test Property",
                    data_type=lumi.InlineDataType.Text,
                    description="A test property",
                )
            ],
        )
        # when we create it
        state = sut.create(self.client)
        # then the state includes the extension
        assert state is not None
        assert state["extension"] == "Extension"
        # and the request sql matches includes extension
        expected = textwrap.dedent("""\
            @keysToCatalog = values
                ('Instrument/TestScope/TestCode', 'Test Property', 'Text', 'A test property', null, null)
            ;
            @config = select
                column1 as [Key], column2 as Name, column3 as DataType, column4 as Description, column5 as IsMain, column6 as AsAt
                from @keysToCatalog
            ;
            select * from Sys.Admin.Lusid.Provider.Configure
                where Provider = 'TestProvider'
                and Configuration = @config
                and WriteAction = 'Set'
                and ProviderNameExtension = 'Extension'
            ;
        """)  # noqa: E501
        lumi_query = respx_mock.calls[0].request.content
        assert lumi_query.decode() == expected

    def test_create_multiple_properties_with_optional_fields(self, respx_mock, default_content):
        setup_sql_background_routes(respx_mock, result_data=default_content)
        # given two properties to inline where one isMain and AsAt
        prop_key1 = DefinitionRef(id="key1", domain=Domain.Instrument, scope="Scope1", code="Code1")
        prop_key2 = DefinitionRef(id="key2", domain=Domain.Portfolio, scope="Scope2", code="Code2")
        sut = lumi.InlinePropertiesResource(
            id="test-inline-props",
            provider="TestProvider",
            properties=[
                lumi.InlineProperty(
                    key=prop_key1,
                    name="Property 1",
                    data_type=lumi.InlineDataType.Text,
                    description="First property",
                    is_main=True,
                    as_at=datetime(2023, 1, 1, 12, 0, 0),
                ),
                lumi.InlineProperty(
                    key=prop_key2,
                    name="Property 2",
                    data_type=lumi.InlineDataType.Decimal,
                    description="Second property",
                    is_main=False,
                ),
            ],
        )
        # when we create it
        sut.create(self.client)
        # then the SQL includes all columns and values
        expected = textwrap.dedent("""\
            @keysToCatalog = values
                ('Instrument/Scope1/Code1', 'Property 1', 'Text', 'First property', true, '2023-01-01 12:00:00'),('Portfolio/Scope2/Code2', 'Property 2', 'Decimal', 'Second property', false, null)
            ;
            @config = select
                column1 as [Key], column2 as Name, column3 as DataType, column4 as Description, column5 as IsMain, column6 as AsAt
                from @keysToCatalog
            ;
            select * from Sys.Admin.Lusid.Provider.Configure
                where Provider = 'TestProvider'
                and Configuration = @config
                and WriteAction = 'Set'\n
            ;
        """)  # noqa
        lumi_query = respx_mock.calls[0].request.content
        assert lumi_query.decode() == expected

    def test_create_custom_entity(self, respx_mock, default_content):
        setup_sql_background_routes(respx_mock, result_data=default_content)
        # given an inline properties resource for a custom entity
        sut = lumi.InlinePropertiesResource(
            id="test-inline-props",
            provider="TestProvider",
            properties=[
                lumi.InlineProperty(
                    name="Test Property",
                    field="cefield",
                    data_type=lumi.InlineDataType.Text,
                    description="A test field",
                    as_at=datetime(2025, 2, 3, 15, 41),
                )
            ],
        )
        # when the sql is generated
        sut.create(self.client)
        # then the property key in the sql is just the field
        expected = textwrap.dedent("""\
            @keysToCatalog = values
                ('cefield', 'Test Property', 'Text', 'A test field', null, '2025-02-03 15:41:00')
            ;
            @config = select
                column1 as [Key], column2 as Name, column3 as DataType, column4 as Description, column5 as IsMain, column6 as AsAt
                from @keysToCatalog
            ;
            select * from Sys.Admin.Lusid.Provider.Configure
                where Provider = 'TestProvider'
                and Configuration = @config
                and WriteAction = 'Set'\n
            ;
        """)  # noqa
        lumi_query = respx_mock.calls[0].request.content
        assert lumi_query.decode() == expected

    def test_create_sql_structured_property(self, respx_mock, default_content):
        setup_sql_background_routes(respx_mock, result_data=default_content)
        # given an inline properties resource for a property which is structured (non scalar)
        prop_key = DefinitionRef(
            id="test-key", domain=Domain.Instrument, scope="TestScope", code="TestCode"
        )
        sut = lumi.InlinePropertiesResource(
            id="test-inline-props",
            provider="TestProvider",
            properties=[
                lumi.InlineProperty(
                    key=prop_key,
                    name="Test Property",
                    field="subfield",
                    data_type=lumi.InlineDataType.Text,
                    description="A test property",
                    as_at=datetime(2025, 2, 3, 15, 41),
                )
            ],
        )
        # when the sql is generated
        sut.create(self.client)
        # then the property key is the domain/scope/code.field
        expected = textwrap.dedent("""\
            @keysToCatalog = values
                ('Instrument/TestScope/TestCode.subfield', 'Test Property', 'Text', 'A test property', null, '2025-02-03 15:41:00')
            ;
            @config = select
                column1 as [Key], column2 as Name, column3 as DataType, column4 as Description, column5 as IsMain, column6 as AsAt
                from @keysToCatalog
            ;
            select * from Sys.Admin.Lusid.Provider.Configure
                where Provider = 'TestProvider'
                and Configuration = @config
                and WriteAction = 'Set'\n
            ;
        """)  # noqa
        lumi_query = respx_mock.calls[0].request.content
        assert lumi_query.decode() == expected

    def make_csv(self, dict_data):
        output = io.StringIO()
        writer = csv.DictWriter(output, fieldnames=dict_data.keys())
        writer.writeheader()
        writer.writerow(dict_data)
        return output.getvalue()

    def test_read_existing_properties(self, respx_mock):  # noqa: E501
        # given an instrument property is already inlined
        prop_key = DefinitionRef(
            id="test-key", domain=Domain.Instrument, scope="TestScope", code="TestCode"
        )
        # mock the csv response from lumi
        existing = {
            "Key": "Instrument/TestScope/TestCode",
            "Name": "Test Property",
            "DataType": "Text",
            "Description": "A test property"
        }
        csv_content = self.make_csv(existing)
        setup_sql_background_routes(respx_mock, result_data=[{"Content": csv_content, "Error": ""}])
        # when we read it
        sut = lumi.InlinePropertiesResource(
            id="test-inline-props",
            provider="TestProvider",
            properties=[
                lumi.InlineProperty(
                    key=prop_key,
                    name="Test Property",
                    data_type=lumi.InlineDataType.Text,
                    description="A test property",
                )
            ],
        )
        old_state = SimpleNamespace(provider="TestProvider", extension=None)
        result = sut.read(self.client, old_state)
        # then we get the parsed properties keyed by the property
        assert result == {
            "Instrument/TestScope/TestCode": {
                "AsAt": None,
                "Name": "Test Property",
                "DataType": "Text",
                "Description": "A test property",
                "IsMain": None
            }
        }
        # and the SQL request to read is right
        request = respx_mock.calls[0].request
        actual = request.content.decode("utf8")
        expected = textwrap.dedent("""\
            select Content from Sys.File
                where Path = 'config/lusid/factories/testproviderproviderfactory.csv'
            ;
        """)  # noqa
        assert actual == expected

    def test_read_existing_with_extension(self, respx_mock):  # noqa: E501
        # given an instrument property is already inlined
        prop_key = DefinitionRef(
            id="test-key", domain=Domain.Instrument, scope="TestScope", code="TestCode"
        )
        # mock the csv response from lumi
        existing = {
            "Key": "Instrument/TestScope/TestCode",
            "Name": "Test Property",
            "DataType": "Text",
            "Description": "A test property"
        }
        csv_content = self.make_csv(existing)
        setup_sql_background_routes(respx_mock, result_data=[{"Content": csv_content}])
        # when we read it
        sut = lumi.InlinePropertiesResource(
            id="test-inline-props",
            provider="TestProvider",
            properties=[
                lumi.InlineProperty(
                    key=prop_key,
                    name="Test Property",
                    data_type=lumi.InlineDataType.Text,
                    description="A test property",
                )
            ],
        )
        old_state = SimpleNamespace(provider="TestProvider", extension="Ext")
        result = sut.read(self.client, old_state)
        # then we get the parsed properties keyed by the property
        assert result == {
            "Instrument/TestScope/TestCode": {
                "AsAt": None,
                "Name": "Test Property",
                "DataType": "Text",
                "Description": "A test property",
                "IsMain": None
            }
        }
        # and path in the query, inserts the extension into the factory name
        request = respx_mock.calls[0].request
        actual = request.content.decode("utf8")
        expected = textwrap.dedent("""\
            select Content from Sys.File
                where Path = 'config/lusid/factories/ext_testproviderproviderfactory.csv'
            ;
        """)  # noqa
        assert actual == expected

    def test_update_no_changes(self, respx_mock):
        # given an instrument property is already inlined
        prop_key = DefinitionRef(
            id="test-key", domain=Domain.Instrument, scope="TestScope", code="TestCode"
        )
        # mock the csv response from lumi
        existing = {
            "Key": "Instrument/TestScope/TestCode",
            "Name": "Test Property",
            "DataType": "Text",
            "Description": "A test property"
        }
        csv_content = self.make_csv(existing)
        setup_sql_background_routes(respx_mock, result_data=[{"Content": csv_content}])
        # and a desired state with the same content hash
        sut = lumi.InlinePropertiesResource(
            id="test-inline-props",
            provider="TestProvider",
            properties=[
                lumi.InlineProperty(
                    key=prop_key,
                    name="Test Property",
                    data_type=lumi.InlineDataType.Text,
                    description="A test property",
                )
            ],
        )
        # create matching state hashes
        desired = sut.model_dump(mode="json", by_alias=True, exclude_none=True)
        source_version = hashlib.sha256(json.dumps(desired, sort_keys=True).encode()).hexdigest()
        remote_version = hashlib.sha256(
            json.dumps({
                "Instrument/TestScope/TestCode": {
                    "Name": "Test Property",
                    "DataType": "Text",
                    "Description": "A test property",
                    "IsMain": None,
                    "AsAt": None,
                }
            }, sort_keys=True,
            ).encode()
        ).hexdigest()
        old_state = SimpleNamespace(
            source_version=source_version,
            remote_version=remote_version,
            provider="TestProvider",
            extension=None,
        )
        # when we update
        result = sut.update(self.client, old_state)
        # then no update is performed
        assert result is None

    def test_update_with_changes(self, respx_mock):
        # given an instrument property is already inlined
        prop_key = DefinitionRef(
            id="test-key", domain=Domain.Instrument, scope="TestScope", code="TestCode"
        )
        #     mock the csv response from lumi
        existing = {
            "Key": "Instrument/TestScope/TestCode",
            "Name": "Test Property",
            "DataType": "Text",
            "Description": "Old Description"
        }
        csv_content = self.make_csv(existing)
        setup_sql_background_routes(respx_mock, result_data=[{"Content": csv_content, "Error": ""}])
        #     mock the read
        routes = setup_sql_background_routes(respx_mock, result_data=[
            {"Content": csv_content, "Error": ""}
        ])
        #     mock the create
        exec_id = "abcdefg"
        routes["put"].mock(
            side_effect=[
                httpx.Response(202, json={"executionId": exec_id}),  # read
                httpx.Response(202, json={"executionId": exec_id}),  # create
            ]
        )
        routes["result"].mock(
            side_effect=[
                httpx.Response(200, json=[{"Content": csv_content}]),  # read result
                httpx.Response(200, json=[{"Content": csv_content, "Error": ""}]),  # create result
            ]
        )
        routes["status"].mock(
            side_effect=[
                httpx.Response(200, json={"status": TaskStatus.RAN_TO_COMPLETION}),  # read
                httpx.Response(200, json={"status": TaskStatus.RAN_TO_COMPLETION}),  # create
            ]
        )
        # when we rename the column and change the description
        sut = lumi.InlinePropertiesResource(
            id="test-inline-props",
            provider="TestProvider",
            properties=[
                lumi.InlineProperty(
                    key=prop_key,
                    name="Updated Property",  # Changed name
                    data_type=lumi.InlineDataType.Text,
                    description="Updated description",  # Changed description
                )
            ],
        )
        old_state = SimpleNamespace(
            source_version="old_version",
            remote_version="old_remote_version",
            provider="TestProvider",
            extension=None,
        )
        result = sut.update(self.client, old_state)
        # then create is called and state is returned
        assert result is not None
        assert result["provider"] == "TestProvider"

    def test_update_provider_change_triggers_delete(self, respx_mock):
        exec_id = "abcdefg"
        existing = {
            "Key": "Instrument/TestScope/TestCode",
            "Name": "Test Property",
            "DataType": "Text",
            "Description": "Old Description"
        }
        csv_content = self.make_csv(existing)
        # Setup for read + delete + create operations (3 total)
        respx_mock.put("/honeycomb/api/SqlBackground", headers=[("Content-type", "text/plain")]).mock(
            return_value=httpx.Response(202, json={"executionId": exec_id})
        )
        respx_mock.get(f"/honeycomb/api/SqlBackground/{exec_id}").mock(
            return_value=httpx.Response(200, json={"status": TaskStatus.RAN_TO_COMPLETION}),  # read
        )
        respx_mock.get(f"/honeycomb/api/SqlBackground/{exec_id}/jsonproper").mock(
                return_value=httpx.Response(200, json=[{"Content": csv_content, "Error": ""}]),
        )
        # given an existing inline
        old_state = SimpleNamespace(
            source_version="old_version",
            remote_version="old_remote_version",
            provider="OldProvider",  # Different from current
            extension=None,
        )
        # when we update the desired with a new provider name
        prop_key = DefinitionRef(
            id="test-key", domain=Domain.Instrument, scope="TestScope", code="TestCode"
        )
        sut = lumi.InlinePropertiesResource(
            id="test-inline-props",
            provider="NewProvider",  # Different provider
            properties=[
                lumi.InlineProperty(
                    key=prop_key,
                    name="Test Property",
                    data_type=lumi.InlineDataType.Text,
                    description="A test property",
                )
            ],
        )
        new_state = sut.update(self.client, old_state)
        # then delete is called first, then create
        del_request = respx_mock.calls[0].request.content.decode()
        assert del_request == textwrap.dedent("""\
            select *
                from Sys.Admin.Lusid.Provider.Configure
                where Provider = 'OldProvider'
                and WriteAction = 'Reset'\n
            ;
        """)
        assert new_state == {
            "provider": "NewProvider",
            "extension": None,
            "remote_version": "323b73ace7abb1e03a9b50166d725ede4945ab215736970e5afba7165f624d20",
            "source_version": "6a92efc7df690b538e5d530e2b4808c842e85fbe84a5b5ee88cf8a4a4bf7f0ae"
        }

    def test_update_extension_calls_delete(self, respx_mock):
        exec_id = "abcdefg"
        #     mock the csv response from lumi
        existing = {
            "Key": "Instrument/TestScope/TestCode",
            "Name": "Test Property",
            "DataType": "Text",
            "Description": "Old Description"
        }
        csv_content = self.make_csv(existing)
        # Setup for read + delete + create operations (3 total)
        respx_mock.put("/honeycomb/api/SqlBackground", headers=[("Content-type", "text/plain")]).mock(
            return_value=httpx.Response(202, json={"executionId": exec_id})
        )
        respx_mock.get(f"/honeycomb/api/SqlBackground/{exec_id}").mock(
            return_value=httpx.Response(200, json={"status": TaskStatus.RAN_TO_COMPLETION}),  # read
        )
        respx_mock.get(f"/honeycomb/api/SqlBackground/{exec_id}/jsonproper").mock(
                return_value=httpx.Response(200, json=[{"Content": csv_content, "Error": ""}]),
        )
        # given an existing inline
        old_state = SimpleNamespace(
            source_version="old_version",
            remote_version="old_remote_version",
            provider="OldProvider",  # Different from current
            extension=None,
        )
        # when we update the extension
        prop_key = DefinitionRef(
            id="test-key", domain=Domain.Instrument, scope="TestScope", code="TestCode"
        )
        sut = lumi.InlinePropertiesResource(
            id="test-inline-props",
            provider="OldProvider",
            provider_name_extension="NewExt",
            properties=[
                lumi.InlineProperty(
                    key=prop_key,
                    name="Test Property",
                    data_type=lumi.InlineDataType.Text,
                    description="A test property",
                )
            ],
        )
        new_state = sut.update(self.client, old_state)
        # then delete is called first, then create
        del_request = respx_mock.calls[0].request.content.decode()
        assert del_request == textwrap.dedent("""\
            select *
                from Sys.Admin.Lusid.Provider.Configure
                where Provider = 'OldProvider'
                and WriteAction = 'Reset'\n
            ;
        """)
        assert new_state == {
            "provider": "OldProvider",
            "extension": "NewExt",
            "remote_version": "323b73ace7abb1e03a9b50166d725ede4945ab215736970e5afba7165f624d20",
            "source_version": "e57c2d65ac17bda7b0f93f1eaadeecb204595530fa665b49f920720001d6a52a"
        }

    def test_delete(self, respx_mock):
        setup_sql_background_routes(respx_mock, result_data=[])
        # given an existing inline
        old_state = SimpleNamespace(
            source_version="old_version",
            remote_version="old_remote_version",
            provider="OldProvider",  # Different from current
            extension="extension",
        )
        # when we delete it
        lumi.InlinePropertiesResource.delete(self.client, old_state)
        # then the writeaction is reset which removes the inline
        del_request = respx_mock.calls[0].request.content.decode()
        expected = textwrap.dedent("""\
           select *
               from Sys.Admin.Lusid.Provider.Configure
               where Provider = 'OldProvider'
               and WriteAction = 'Reset'
               and ProviderNameExtension = 'extension'
           ;
        """)
        assert expected == del_request

    def test_deps_lusid_provider(self):
        # given an inline properties resource with basic properties
        prop_key = DefinitionRef(
            id="test-key", domain=Domain.Instrument, scope="TestScope", code="TestCode"
        )
        sut = lumi.InlinePropertiesResource(
            id="test-inline-props",
            provider="TestProvider",
            properties=[
                lumi.InlineProperty(
                    key=prop_key,
                    name="Test Property",
                    data_type=lumi.InlineDataType.Text,
                    description="A test property",
                )
            ],
        )
        # when we get the dependencies the property definition is returned
        assert sut.deps() == [prop_key]

    def test_deps_custom_entity(self):
        # given an inline properties resource for a custom entity provider
        sut = lumi.InlinePropertiesResource(
            id="test-inline-props",
            provider="TestProvider",
            properties=[
                lumi.InlineProperty(
                    field="action",
                    name="Test Property",
                    data_type=lumi.InlineDataType.Text,
                    description="A test property",
                )
            ],
        )
        # when we get the dependencies there are none
        assert sut.deps() == []

    def test_dump(self):
        # given a inline prop
        prop_key = DefinitionRef(
            id="test-key", domain=Domain.Instrument, scope="TestScope", code="TestCode"
        )
        sut = lumi.InlinePropertiesResource(
            id="test-inline-props",
            provider="TestProvider",
            properties=[
                lumi.InlineProperty(
                    key=prop_key,
                    name="Test Property",
                    data_type=lumi.InlineDataType.Boolean,
                    description="A test property",
                )
            ],
        )
        # when we dump it
        dump = sut.model_dump(by_alias=True, round_trip=True, exclude_none=True, context={
            "style": "dump"
        })
        # then everything gets dumped out and the property is ref'd
        assert dump == {
           "provider": "TestProvider",
           "properties": [
               {
                   "dataType": lumi.InlineDataType.Boolean,
                   "description": "A test property",
                   "key": {"$ref": "test-key"},
                   "name": "Test Property",
               },
           ],
       }

    def test_undump(self):
        # given a dump
        prop_key = DefinitionRef(
            id="test-key", domain=Domain.Instrument, scope="TestScope", code="TestCode"
        )
        dump = {
           "provider": "TestProvider",
           "properties": [
               {
                   "dataType": "Text",
                   "description": "A test property",
                   "key": {"$ref": "test-key"},
                   "name": "Test Property",
               },
           ],
        }
        # when we undump
        sut = lumi.InlinePropertiesResource.model_validate(dump, context={
            "id": "something-unique",
            "$refs": {
                "test-key": prop_key
            }
        })
        # then the id is extracted from the context
        assert sut.id == "something-unique"
        # and the property reference has been wired in
        assert sut.properties[0].key == prop_key
