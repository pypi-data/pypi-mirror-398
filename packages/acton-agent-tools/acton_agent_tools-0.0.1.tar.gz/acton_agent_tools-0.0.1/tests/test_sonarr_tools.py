"""Tests for Sonarr tools."""

import json

from acton_agent_tools.sonarr_tools import (
    SonarrConfig,
    SonarrGetCalendarTool,
    SonarrGetDiskSpaceTool,
    SonarrGetEpisodesTool,
    SonarrGetHistoryTool,
    SonarrGetQualityProfilesTool,
    SonarrGetQueueTool,
    SonarrGetRootFoldersTool,
    SonarrGetSeriesByIdTool,
    SonarrGetSeriesTool,
    SonarrGetSystemStatusTool,
    SonarrGetWantedTool,
    SonarrSearchSeriesTool,
    _format_calendar,
    _format_disk_space,
    _format_episode_list,
    _format_history,
    _format_quality_profiles,
    _format_queue,
    _format_root_folders,
    _format_search_results,
    _format_series_detail,
    _format_series_list,
    _format_system_status,
    _format_wanted,
    get_sonarr_toolset,
)


class TestFormatters:
    """Test formatting functions."""

    def test_format_series_list_empty(self):
        """Test formatting empty series list."""
        output = json.dumps([])
        result = _format_series_list(output)
        assert "No series found" in result

    def test_format_series_list_with_data(self):
        """Test formatting series list with data."""
        output = json.dumps([
            {
                "id": 1,
                "title": "Test Series",
                "year": 2024,
                "status": "continuing",
                "network": "Test Network",
                "monitored": True,
                "seasonCount": 2,
                "statistics": {
                    "episodeCount": 20,
                    "episodeFileCount": 15,
                    "percentOfEpisodes": 75.0,
                },
            }
        ])
        result = _format_series_list(output)
        assert "Test Series" in result
        assert "2024" in result
        assert "Test Network" in result

    def test_format_series_detail(self):
        """Test formatting series detail."""
        output = json.dumps({
            "id": 1,
            "title": "Test Series",
            "year": 2024,
            "overview": "A test series",
            "status": "continuing",
            "network": "Test Network",
            "tvdbId": 12345,
            "imdbId": "tt1234567",
            "monitored": True,
            "statistics": {
                "episodeCount": 20,
                "episodeFileCount": 15,
                "percentOfEpisodes": 75.0,
            },
            "seasons": [
                {
                    "seasonNumber": 1,
                    "monitored": True,
                    "statistics": {
                        "episodeCount": 10,
                        "episodeFileCount": 8,
                        "percentOfEpisodes": 80.0,
                    },
                }
            ],
        })
        result = _format_series_detail(output)
        assert "Test Series" in result
        assert "A test series" in result
        assert "Test Network" in result

    def test_format_episode_list_empty(self):
        """Test formatting empty episode list."""
        output = json.dumps([])
        result = _format_episode_list(output)
        assert "No episodes found" in result

    def test_format_episode_list_with_data(self):
        """Test formatting episode list with data."""
        output = json.dumps([
            {
                "id": 1,
                "seasonNumber": 1,
                "episodeNumber": 1,
                "title": "Pilot",
                "airDate": "2024-01-01",
                "runtime": 45,
                "monitored": True,
                "hasFile": True,
                "episodeFileId": 1,
            }
        ])
        result = _format_episode_list(output)
        assert "Pilot" in result
        assert "S01E01" in result

    def test_format_search_results_empty(self):
        """Test formatting empty search results."""
        output = json.dumps([])
        result = _format_search_results(output)
        assert "No results found" in result

    def test_format_search_results_with_data(self):
        """Test formatting search results with data."""
        output = json.dumps([
            {
                "title": "Test Series",
                "year": 2024,
                "status": "continuing",
                "network": "Test Network",
                "seriesType": "standard",
                "seasonCount": 2,
                "tvdbId": 12345,
                "imdbId": "tt1234567",
                "overview": "A test series overview",
            }
        ])
        result = _format_search_results(output)
        assert "Test Series" in result
        assert "2024" in result

    def test_format_queue_empty(self):
        """Test formatting empty queue."""
        output = json.dumps({"records": []})
        result = _format_queue(output)
        assert "Queue is empty" in result

    def test_format_queue_with_items(self):
        """Test formatting queue with items."""
        output = json.dumps({
            "records": [
                {
                    "id": 1,
                    "series": {"title": "Test Series"},
                    "episode": {"seasonNumber": 1, "episodeNumber": 1},
                    "status": "downloading",
                    "size": 1073741824,
                    "sizeleft": 536870912,
                    "quality": {"quality": {"name": "WEBDL-1080p"}},
                    "timeleft": "00:30:00",
                    "protocol": "torrent",
                }
            ]
        })
        result = _format_queue(output)
        assert "Test Series" in result
        assert "S01E01" in result

    def test_format_calendar_empty(self):
        """Test formatting empty calendar."""
        output = json.dumps([])
        result = _format_calendar(output)
        assert "No upcoming episodes" in result

    def test_format_history_empty(self):
        """Test formatting empty history."""
        output = json.dumps({"records": []})
        result = _format_history(output)
        assert "No history records" in result

    def test_format_wanted_empty(self):
        """Test formatting empty wanted list."""
        output = json.dumps({"records": []})
        result = _format_wanted(output)
        assert "No wanted episodes" in result

    def test_format_system_status(self):
        """Test formatting system status."""
        output = json.dumps({
            "version": "4.0.0",
            "buildTime": "2024-01-01T00:00:00Z",
            "isDebug": False,
            "isProduction": True,
            "osName": "ubuntu",
        })
        result = _format_system_status(output)
        assert "4.0.0" in result
        assert "ubuntu" in result

    def test_format_quality_profiles_empty(self):
        """Test formatting empty quality profiles."""
        output = json.dumps([])
        result = _format_quality_profiles(output)
        assert "No quality profiles" in result

    def test_format_root_folders_empty(self):
        """Test formatting empty root folders."""
        output = json.dumps([])
        result = _format_root_folders(output)
        assert "No root folders" in result

    def test_format_disk_space_empty(self):
        """Test formatting empty disk space."""
        output = json.dumps([])
        result = _format_disk_space(output)
        assert "No disk space information" in result


class TestCustomTools:
    """Test custom tool classes."""

    def test_sonarr_get_series_tool_process_output(self):
        """Test SonarrGetSeriesTool process_output."""
        tool = SonarrGetSeriesTool(
            name="test",
            description="test",
            func=lambda base_url, api_key: "test",
            config_schema=SonarrConfig,
        )
        output = json.dumps([])
        result = tool.process_output(output)
        assert "No series found" in result

    def test_sonarr_get_series_by_id_tool_process_output(self):
        """Test SonarrGetSeriesByIdTool process_output."""
        tool = SonarrGetSeriesByIdTool(
            name="test",
            description="test",
            func=lambda base_url, api_key, id: "test",
            config_schema=SonarrConfig,
        )
        output = json.dumps({"id": 1, "title": "Test", "year": 2024})
        result = tool.process_output(output)
        assert "Test" in result

    def test_sonarr_search_series_tool_process_output(self):
        """Test SonarrSearchSeriesTool process_output."""
        tool = SonarrSearchSeriesTool(
            name="test",
            description="test",
            func=lambda base_url, api_key, term: "test",
            config_schema=SonarrConfig,
        )
        output = json.dumps([])
        result = tool.process_output(output)
        assert "No results found" in result

    def test_sonarr_get_episodes_tool_process_output(self):
        """Test SonarrGetEpisodesTool process_output."""
        tool = SonarrGetEpisodesTool(
            name="test",
            description="test",
            func=lambda base_url, api_key, series_id: "test",
            config_schema=SonarrConfig,
        )
        output = json.dumps([])
        result = tool.process_output(output)
        assert "No episodes found" in result

    def test_sonarr_get_queue_tool_process_output(self):
        """Test SonarrGetQueueTool process_output."""
        tool = SonarrGetQueueTool(
            name="test",
            description="test",
            func=lambda base_url, api_key: "test",
            config_schema=SonarrConfig,
        )
        output = json.dumps({"records": []})
        result = tool.process_output(output)
        assert "Queue is empty" in result

    def test_sonarr_get_calendar_tool_process_output(self):
        """Test SonarrGetCalendarTool process_output."""
        tool = SonarrGetCalendarTool(
            name="test",
            description="test",
            func=lambda base_url, api_key: "test",
            config_schema=SonarrConfig,
        )
        output = json.dumps([])
        result = tool.process_output(output)
        assert "No upcoming episodes" in result

    def test_sonarr_get_system_status_tool_process_output(self):
        """Test SonarrGetSystemStatusTool process_output."""
        tool = SonarrGetSystemStatusTool(
            name="test",
            description="test",
            func=lambda base_url, api_key: "test",
            config_schema=SonarrConfig,
        )
        output = json.dumps({"version": "4.0.0"})
        result = tool.process_output(output)
        assert "4.0.0" in result

    def test_sonarr_get_quality_profiles_tool_process_output(self):
        """Test SonarrGetQualityProfilesTool process_output."""
        tool = SonarrGetQualityProfilesTool(
            name="test",
            description="test",
            func=lambda base_url, api_key: "test",
            config_schema=SonarrConfig,
        )
        output = json.dumps([])
        result = tool.process_output(output)
        assert "No quality profiles" in result

    def test_sonarr_get_root_folders_tool_process_output(self):
        """Test SonarrGetRootFoldersTool process_output."""
        tool = SonarrGetRootFoldersTool(
            name="test",
            description="test",
            func=lambda base_url, api_key: "test",
            config_schema=SonarrConfig,
        )
        output = json.dumps([])
        result = tool.process_output(output)
        assert "No root folders" in result

    def test_sonarr_get_history_tool_process_output(self):
        """Test SonarrGetHistoryTool process_output."""
        tool = SonarrGetHistoryTool(
            name="test",
            description="test",
            func=lambda base_url, api_key: "test",
            config_schema=SonarrConfig,
        )
        output = json.dumps({"records": []})
        result = tool.process_output(output)
        assert "No history records" in result

    def test_sonarr_get_disk_space_tool_process_output(self):
        """Test SonarrGetDiskSpaceTool process_output."""
        tool = SonarrGetDiskSpaceTool(
            name="test",
            description="test",
            func=lambda base_url, api_key: "test",
            config_schema=SonarrConfig,
        )
        output = json.dumps([])
        result = tool.process_output(output)
        assert "No disk space information" in result

    def test_sonarr_get_wanted_tool_process_output(self):
        """Test SonarrGetWantedTool process_output."""
        tool = SonarrGetWantedTool(
            name="test",
            description="test",
            func=lambda base_url, api_key: "test",
            config_schema=SonarrConfig,
        )
        output = json.dumps({"records": []})
        result = tool.process_output(output)
        assert "No wanted episodes" in result


class TestSonarrToolset:
    """Test Sonarr toolset creation."""

    def test_get_sonarr_toolset(self):
        """Test creating Sonarr toolset."""
        toolset = get_sonarr_toolset(
            base_url="http://localhost:8989",
            api_key="test_api_key",
        )
        assert toolset.name == "sonarr_tools"
        assert len(toolset.tools) > 0
        assert toolset.config["base_url"] == "http://localhost:8989"
        assert toolset.config["api_key"] == "test_api_key"
