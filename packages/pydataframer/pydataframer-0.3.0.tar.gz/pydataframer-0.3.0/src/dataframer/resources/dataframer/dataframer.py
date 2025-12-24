# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

import httpx

from .chat import (
    ChatResource,
    AsyncChatResource,
    ChatResourceWithRawResponse,
    AsyncChatResourceWithRawResponse,
    ChatResourceWithStreamingResponse,
    AsyncChatResourceWithStreamingResponse,
)
from .files import (
    FilesResource,
    AsyncFilesResource,
    FilesResourceWithRawResponse,
    AsyncFilesResourceWithRawResponse,
    FilesResourceWithStreamingResponse,
    AsyncFilesResourceWithStreamingResponse,
)
from .analyze import (
    AnalyzeResource,
    AsyncAnalyzeResource,
    AnalyzeResourceWithRawResponse,
    AsyncAnalyzeResourceWithRawResponse,
    AnalyzeResourceWithStreamingResponse,
    AsyncAnalyzeResourceWithStreamingResponse,
)
from ..._types import Body, Query, Headers, NotGiven, not_given
from .datasets import (
    DatasetsResource,
    AsyncDatasetsResource,
    DatasetsResourceWithRawResponse,
    AsyncDatasetsResourceWithRawResponse,
    DatasetsResourceWithStreamingResponse,
    AsyncDatasetsResourceWithStreamingResponse,
)
from .generate import (
    GenerateResource,
    AsyncGenerateResource,
    GenerateResourceWithRawResponse,
    AsyncGenerateResourceWithRawResponse,
    GenerateResourceWithStreamingResponse,
    AsyncGenerateResourceWithStreamingResponse,
)
from .red_team import (
    RedTeamResource,
    AsyncRedTeamResource,
    RedTeamResourceWithRawResponse,
    AsyncRedTeamResourceWithRawResponse,
    RedTeamResourceWithStreamingResponse,
    AsyncRedTeamResourceWithStreamingResponse,
)
from ..._compat import cached_property
from .runs.runs import (
    RunsResource,
    AsyncRunsResource,
    RunsResourceWithRawResponse,
    AsyncRunsResourceWithRawResponse,
    RunsResourceWithStreamingResponse,
    AsyncRunsResourceWithStreamingResponse,
)
from ..._resource import SyncAPIResource, AsyncAPIResource
from ..._response import (
    to_raw_response_wrapper,
    to_streamed_response_wrapper,
    async_to_raw_response_wrapper,
    async_to_streamed_response_wrapper,
)
from .specs.specs import (
    SpecsResource,
    AsyncSpecsResource,
    SpecsResourceWithRawResponse,
    AsyncSpecsResourceWithRawResponse,
    SpecsResourceWithStreamingResponse,
    AsyncSpecsResourceWithStreamingResponse,
)
from .human_labels import (
    HumanLabelsResource,
    AsyncHumanLabelsResource,
    HumanLabelsResourceWithRawResponse,
    AsyncHumanLabelsResourceWithRawResponse,
    HumanLabelsResourceWithStreamingResponse,
    AsyncHumanLabelsResourceWithStreamingResponse,
)
from .red_team_runs import (
    RedTeamRunsResource,
    AsyncRedTeamRunsResource,
    RedTeamRunsResourceWithRawResponse,
    AsyncRedTeamRunsResourceWithRawResponse,
    RedTeamRunsResourceWithStreamingResponse,
    AsyncRedTeamRunsResourceWithStreamingResponse,
)
from ..._base_client import make_request_options
from .red_team_specs import (
    RedTeamSpecsResource,
    AsyncRedTeamSpecsResource,
    RedTeamSpecsResourceWithRawResponse,
    AsyncRedTeamSpecsResourceWithRawResponse,
    RedTeamSpecsResourceWithStreamingResponse,
    AsyncRedTeamSpecsResourceWithStreamingResponse,
)
from .evaluations.evaluations import (
    EvaluationsResource,
    AsyncEvaluationsResource,
    EvaluationsResourceWithRawResponse,
    AsyncEvaluationsResourceWithRawResponse,
    EvaluationsResourceWithStreamingResponse,
    AsyncEvaluationsResourceWithStreamingResponse,
)
from ...types.dataframer_list_models_response import DataframerListModelsResponse
from ...types.dataframer_check_health_response import DataframerCheckHealthResponse
from ...types.dataframer_list_historical_runs_response import DataframerListHistoricalRunsResponse

__all__ = ["DataframerResource", "AsyncDataframerResource"]


class DataframerResource(SyncAPIResource):
    @cached_property
    def analyze(self) -> AnalyzeResource:
        return AnalyzeResource(self._client)

    @cached_property
    def chat(self) -> ChatResource:
        return ChatResource(self._client)

    @cached_property
    def datasets(self) -> DatasetsResource:
        return DatasetsResource(self._client)

    @cached_property
    def evaluations(self) -> EvaluationsResource:
        return EvaluationsResource(self._client)

    @cached_property
    def files(self) -> FilesResource:
        return FilesResource(self._client)

    @cached_property
    def generate(self) -> GenerateResource:
        return GenerateResource(self._client)

    @cached_property
    def human_labels(self) -> HumanLabelsResource:
        return HumanLabelsResource(self._client)

    @cached_property
    def red_team_runs(self) -> RedTeamRunsResource:
        return RedTeamRunsResource(self._client)

    @cached_property
    def red_team_specs(self) -> RedTeamSpecsResource:
        return RedTeamSpecsResource(self._client)

    @cached_property
    def red_team(self) -> RedTeamResource:
        return RedTeamResource(self._client)

    @cached_property
    def runs(self) -> RunsResource:
        return RunsResource(self._client)

    @cached_property
    def specs(self) -> SpecsResource:
        return SpecsResource(self._client)

    @cached_property
    def with_raw_response(self) -> DataframerResourceWithRawResponse:
        """
        This property can be used as a prefix for any HTTP method call to return
        the raw response object instead of the parsed content.

        For more information, see https://www.github.com/aimonlabs/dataframer-python-sdk#accessing-raw-response-data-eg-headers
        """
        return DataframerResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> DataframerResourceWithStreamingResponse:
        """
        An alternative to `.with_raw_response` that doesn't eagerly read the response body.

        For more information, see https://www.github.com/aimonlabs/dataframer-python-sdk#with_streaming_response
        """
        return DataframerResourceWithStreamingResponse(self)

    def check_health(
        self,
        *,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> DataframerCheckHealthResponse:
        """Health check endpoint for dataframer service"""
        return self._get(
            "/api/dataframer/health/",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=DataframerCheckHealthResponse,
        )

    def list_historical_runs(
        self,
        *,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> DataframerListHistoricalRunsResponse:
        """Get all historical runs"""
        return self._get(
            "/api/dataframer/historical-runs/",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=DataframerListHistoricalRunsResponse,
        )

    def list_models(
        self,
        *,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> DataframerListModelsResponse:
        """Return list of supported models"""
        return self._get(
            "/api/dataframer/models/",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=DataframerListModelsResponse,
        )


class AsyncDataframerResource(AsyncAPIResource):
    @cached_property
    def analyze(self) -> AsyncAnalyzeResource:
        return AsyncAnalyzeResource(self._client)

    @cached_property
    def chat(self) -> AsyncChatResource:
        return AsyncChatResource(self._client)

    @cached_property
    def datasets(self) -> AsyncDatasetsResource:
        return AsyncDatasetsResource(self._client)

    @cached_property
    def evaluations(self) -> AsyncEvaluationsResource:
        return AsyncEvaluationsResource(self._client)

    @cached_property
    def files(self) -> AsyncFilesResource:
        return AsyncFilesResource(self._client)

    @cached_property
    def generate(self) -> AsyncGenerateResource:
        return AsyncGenerateResource(self._client)

    @cached_property
    def human_labels(self) -> AsyncHumanLabelsResource:
        return AsyncHumanLabelsResource(self._client)

    @cached_property
    def red_team_runs(self) -> AsyncRedTeamRunsResource:
        return AsyncRedTeamRunsResource(self._client)

    @cached_property
    def red_team_specs(self) -> AsyncRedTeamSpecsResource:
        return AsyncRedTeamSpecsResource(self._client)

    @cached_property
    def red_team(self) -> AsyncRedTeamResource:
        return AsyncRedTeamResource(self._client)

    @cached_property
    def runs(self) -> AsyncRunsResource:
        return AsyncRunsResource(self._client)

    @cached_property
    def specs(self) -> AsyncSpecsResource:
        return AsyncSpecsResource(self._client)

    @cached_property
    def with_raw_response(self) -> AsyncDataframerResourceWithRawResponse:
        """
        This property can be used as a prefix for any HTTP method call to return
        the raw response object instead of the parsed content.

        For more information, see https://www.github.com/aimonlabs/dataframer-python-sdk#accessing-raw-response-data-eg-headers
        """
        return AsyncDataframerResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> AsyncDataframerResourceWithStreamingResponse:
        """
        An alternative to `.with_raw_response` that doesn't eagerly read the response body.

        For more information, see https://www.github.com/aimonlabs/dataframer-python-sdk#with_streaming_response
        """
        return AsyncDataframerResourceWithStreamingResponse(self)

    async def check_health(
        self,
        *,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> DataframerCheckHealthResponse:
        """Health check endpoint for dataframer service"""
        return await self._get(
            "/api/dataframer/health/",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=DataframerCheckHealthResponse,
        )

    async def list_historical_runs(
        self,
        *,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> DataframerListHistoricalRunsResponse:
        """Get all historical runs"""
        return await self._get(
            "/api/dataframer/historical-runs/",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=DataframerListHistoricalRunsResponse,
        )

    async def list_models(
        self,
        *,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> DataframerListModelsResponse:
        """Return list of supported models"""
        return await self._get(
            "/api/dataframer/models/",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=DataframerListModelsResponse,
        )


class DataframerResourceWithRawResponse:
    def __init__(self, dataframer: DataframerResource) -> None:
        self._dataframer = dataframer

        self.check_health = to_raw_response_wrapper(
            dataframer.check_health,
        )
        self.list_historical_runs = to_raw_response_wrapper(
            dataframer.list_historical_runs,
        )
        self.list_models = to_raw_response_wrapper(
            dataframer.list_models,
        )

    @cached_property
    def analyze(self) -> AnalyzeResourceWithRawResponse:
        return AnalyzeResourceWithRawResponse(self._dataframer.analyze)

    @cached_property
    def chat(self) -> ChatResourceWithRawResponse:
        return ChatResourceWithRawResponse(self._dataframer.chat)

    @cached_property
    def datasets(self) -> DatasetsResourceWithRawResponse:
        return DatasetsResourceWithRawResponse(self._dataframer.datasets)

    @cached_property
    def evaluations(self) -> EvaluationsResourceWithRawResponse:
        return EvaluationsResourceWithRawResponse(self._dataframer.evaluations)

    @cached_property
    def files(self) -> FilesResourceWithRawResponse:
        return FilesResourceWithRawResponse(self._dataframer.files)

    @cached_property
    def generate(self) -> GenerateResourceWithRawResponse:
        return GenerateResourceWithRawResponse(self._dataframer.generate)

    @cached_property
    def human_labels(self) -> HumanLabelsResourceWithRawResponse:
        return HumanLabelsResourceWithRawResponse(self._dataframer.human_labels)

    @cached_property
    def red_team_runs(self) -> RedTeamRunsResourceWithRawResponse:
        return RedTeamRunsResourceWithRawResponse(self._dataframer.red_team_runs)

    @cached_property
    def red_team_specs(self) -> RedTeamSpecsResourceWithRawResponse:
        return RedTeamSpecsResourceWithRawResponse(self._dataframer.red_team_specs)

    @cached_property
    def red_team(self) -> RedTeamResourceWithRawResponse:
        return RedTeamResourceWithRawResponse(self._dataframer.red_team)

    @cached_property
    def runs(self) -> RunsResourceWithRawResponse:
        return RunsResourceWithRawResponse(self._dataframer.runs)

    @cached_property
    def specs(self) -> SpecsResourceWithRawResponse:
        return SpecsResourceWithRawResponse(self._dataframer.specs)


class AsyncDataframerResourceWithRawResponse:
    def __init__(self, dataframer: AsyncDataframerResource) -> None:
        self._dataframer = dataframer

        self.check_health = async_to_raw_response_wrapper(
            dataframer.check_health,
        )
        self.list_historical_runs = async_to_raw_response_wrapper(
            dataframer.list_historical_runs,
        )
        self.list_models = async_to_raw_response_wrapper(
            dataframer.list_models,
        )

    @cached_property
    def analyze(self) -> AsyncAnalyzeResourceWithRawResponse:
        return AsyncAnalyzeResourceWithRawResponse(self._dataframer.analyze)

    @cached_property
    def chat(self) -> AsyncChatResourceWithRawResponse:
        return AsyncChatResourceWithRawResponse(self._dataframer.chat)

    @cached_property
    def datasets(self) -> AsyncDatasetsResourceWithRawResponse:
        return AsyncDatasetsResourceWithRawResponse(self._dataframer.datasets)

    @cached_property
    def evaluations(self) -> AsyncEvaluationsResourceWithRawResponse:
        return AsyncEvaluationsResourceWithRawResponse(self._dataframer.evaluations)

    @cached_property
    def files(self) -> AsyncFilesResourceWithRawResponse:
        return AsyncFilesResourceWithRawResponse(self._dataframer.files)

    @cached_property
    def generate(self) -> AsyncGenerateResourceWithRawResponse:
        return AsyncGenerateResourceWithRawResponse(self._dataframer.generate)

    @cached_property
    def human_labels(self) -> AsyncHumanLabelsResourceWithRawResponse:
        return AsyncHumanLabelsResourceWithRawResponse(self._dataframer.human_labels)

    @cached_property
    def red_team_runs(self) -> AsyncRedTeamRunsResourceWithRawResponse:
        return AsyncRedTeamRunsResourceWithRawResponse(self._dataframer.red_team_runs)

    @cached_property
    def red_team_specs(self) -> AsyncRedTeamSpecsResourceWithRawResponse:
        return AsyncRedTeamSpecsResourceWithRawResponse(self._dataframer.red_team_specs)

    @cached_property
    def red_team(self) -> AsyncRedTeamResourceWithRawResponse:
        return AsyncRedTeamResourceWithRawResponse(self._dataframer.red_team)

    @cached_property
    def runs(self) -> AsyncRunsResourceWithRawResponse:
        return AsyncRunsResourceWithRawResponse(self._dataframer.runs)

    @cached_property
    def specs(self) -> AsyncSpecsResourceWithRawResponse:
        return AsyncSpecsResourceWithRawResponse(self._dataframer.specs)


class DataframerResourceWithStreamingResponse:
    def __init__(self, dataframer: DataframerResource) -> None:
        self._dataframer = dataframer

        self.check_health = to_streamed_response_wrapper(
            dataframer.check_health,
        )
        self.list_historical_runs = to_streamed_response_wrapper(
            dataframer.list_historical_runs,
        )
        self.list_models = to_streamed_response_wrapper(
            dataframer.list_models,
        )

    @cached_property
    def analyze(self) -> AnalyzeResourceWithStreamingResponse:
        return AnalyzeResourceWithStreamingResponse(self._dataframer.analyze)

    @cached_property
    def chat(self) -> ChatResourceWithStreamingResponse:
        return ChatResourceWithStreamingResponse(self._dataframer.chat)

    @cached_property
    def datasets(self) -> DatasetsResourceWithStreamingResponse:
        return DatasetsResourceWithStreamingResponse(self._dataframer.datasets)

    @cached_property
    def evaluations(self) -> EvaluationsResourceWithStreamingResponse:
        return EvaluationsResourceWithStreamingResponse(self._dataframer.evaluations)

    @cached_property
    def files(self) -> FilesResourceWithStreamingResponse:
        return FilesResourceWithStreamingResponse(self._dataframer.files)

    @cached_property
    def generate(self) -> GenerateResourceWithStreamingResponse:
        return GenerateResourceWithStreamingResponse(self._dataframer.generate)

    @cached_property
    def human_labels(self) -> HumanLabelsResourceWithStreamingResponse:
        return HumanLabelsResourceWithStreamingResponse(self._dataframer.human_labels)

    @cached_property
    def red_team_runs(self) -> RedTeamRunsResourceWithStreamingResponse:
        return RedTeamRunsResourceWithStreamingResponse(self._dataframer.red_team_runs)

    @cached_property
    def red_team_specs(self) -> RedTeamSpecsResourceWithStreamingResponse:
        return RedTeamSpecsResourceWithStreamingResponse(self._dataframer.red_team_specs)

    @cached_property
    def red_team(self) -> RedTeamResourceWithStreamingResponse:
        return RedTeamResourceWithStreamingResponse(self._dataframer.red_team)

    @cached_property
    def runs(self) -> RunsResourceWithStreamingResponse:
        return RunsResourceWithStreamingResponse(self._dataframer.runs)

    @cached_property
    def specs(self) -> SpecsResourceWithStreamingResponse:
        return SpecsResourceWithStreamingResponse(self._dataframer.specs)


class AsyncDataframerResourceWithStreamingResponse:
    def __init__(self, dataframer: AsyncDataframerResource) -> None:
        self._dataframer = dataframer

        self.check_health = async_to_streamed_response_wrapper(
            dataframer.check_health,
        )
        self.list_historical_runs = async_to_streamed_response_wrapper(
            dataframer.list_historical_runs,
        )
        self.list_models = async_to_streamed_response_wrapper(
            dataframer.list_models,
        )

    @cached_property
    def analyze(self) -> AsyncAnalyzeResourceWithStreamingResponse:
        return AsyncAnalyzeResourceWithStreamingResponse(self._dataframer.analyze)

    @cached_property
    def chat(self) -> AsyncChatResourceWithStreamingResponse:
        return AsyncChatResourceWithStreamingResponse(self._dataframer.chat)

    @cached_property
    def datasets(self) -> AsyncDatasetsResourceWithStreamingResponse:
        return AsyncDatasetsResourceWithStreamingResponse(self._dataframer.datasets)

    @cached_property
    def evaluations(self) -> AsyncEvaluationsResourceWithStreamingResponse:
        return AsyncEvaluationsResourceWithStreamingResponse(self._dataframer.evaluations)

    @cached_property
    def files(self) -> AsyncFilesResourceWithStreamingResponse:
        return AsyncFilesResourceWithStreamingResponse(self._dataframer.files)

    @cached_property
    def generate(self) -> AsyncGenerateResourceWithStreamingResponse:
        return AsyncGenerateResourceWithStreamingResponse(self._dataframer.generate)

    @cached_property
    def human_labels(self) -> AsyncHumanLabelsResourceWithStreamingResponse:
        return AsyncHumanLabelsResourceWithStreamingResponse(self._dataframer.human_labels)

    @cached_property
    def red_team_runs(self) -> AsyncRedTeamRunsResourceWithStreamingResponse:
        return AsyncRedTeamRunsResourceWithStreamingResponse(self._dataframer.red_team_runs)

    @cached_property
    def red_team_specs(self) -> AsyncRedTeamSpecsResourceWithStreamingResponse:
        return AsyncRedTeamSpecsResourceWithStreamingResponse(self._dataframer.red_team_specs)

    @cached_property
    def red_team(self) -> AsyncRedTeamResourceWithStreamingResponse:
        return AsyncRedTeamResourceWithStreamingResponse(self._dataframer.red_team)

    @cached_property
    def runs(self) -> AsyncRunsResourceWithStreamingResponse:
        return AsyncRunsResourceWithStreamingResponse(self._dataframer.runs)

    @cached_property
    def specs(self) -> AsyncSpecsResourceWithStreamingResponse:
        return AsyncSpecsResourceWithStreamingResponse(self._dataframer.specs)
