"""Tests for Radarr tools."""

import json

from acton_agent_tools.radarr_tools import (
    RadarrConfig,
    RadarrGetCalendarTool,
    RadarrGetDiskSpaceTool,
    RadarrGetHistoryTool,
    RadarrGetMovieByIdTool,
    RadarrGetMoviesTool,
    RadarrGetQualityProfilesTool,
    RadarrGetQueueTool,
    RadarrGetRootFoldersTool,
    RadarrGetSystemStatusTool,
    RadarrSearchMoviesTool,
    _format_calendar,
    _format_disk_space,
    _format_history,
    _format_movie_detail,
    _format_movie_list,
    _format_quality_profiles,
    _format_queue,
    _format_root_folders,
    _format_search_results,
    _format_system_status,
    get_radarr_toolset,
)


class TestFormatters:
    """Test formatting functions."""

    def test_format_movie_list_empty(self):
        """Test formatting empty movie list."""
        output = json.dumps([])
        result = _format_movie_list(output)
        assert "No movies found" in result

    def test_format_movie_list_with_movies(self):
        """Test formatting movie list with data."""
        output = json.dumps([
            {
                "id": 1,
                "title": "Test Movie",
                "year": 2024,
                "status": "released",
                "monitored": True,
                "hasFile": True,
                "sizeOnDisk": 1073741824,  # 1 GB
                "movieFile": {"quality": {"quality": {"name": "Bluray-1080p"}}},
                "tmdbId": 12345,
                "imdbId": "tt1234567",
            }
        ])
        result = _format_movie_list(output)
        assert "Test Movie" in result
        assert "2024" in result
        assert "Bluray-1080p" in result

    def test_format_movie_detail(self):
        """Test formatting movie detail."""
        output = json.dumps({
            "id": 1,
            "title": "Test Movie",
            "year": 2024,
            "overview": "A test movie",
            "status": "released",
            "tmdbId": 12345,
            "imdbId": "tt1234567",
            "hasFile": True,
            "movieFile": {
                "id": 1,
                "relativePath": "Test Movie (2024)/Test Movie (2024).mkv",
                "quality": {"quality": {"name": "Bluray-1080p"}},
                "size": 1073741824,
            },
        })
        result = _format_movie_detail(output)
        assert "Test Movie" in result
        assert "2024" in result
        assert "A test movie" in result
        assert "Downloaded" in result

    def test_format_search_results_empty(self):
        """Test formatting empty search results."""
        output = json.dumps([])
        result = _format_search_results(output)
        assert "No results found" in result

    def test_format_search_results_with_data(self):
        """Test formatting search results with data."""
        output = json.dumps([
            {
                "title": "Test Movie",
                "year": 2024,
                "status": "released",
                "studio": "Test Studio",
                "tmdbId": 12345,
                "imdbId": "tt1234567",
                "genres": ["Action", "Thriller"],
                "overview": "A test movie overview",
            }
        ])
        result = _format_search_results(output)
        assert "Test Movie" in result
        assert "2024" in result
        assert "Test Studio" in result

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
                    "movie": {"title": "Test Movie"},
                    "status": "downloading",
                    "size": 1073741824,
                    "sizeleft": 536870912,
                    "quality": {"quality": {"name": "Bluray-1080p"}},
                    "timeleft": "00:30:00",
                    "protocol": "torrent",
                }
            ]
        })
        result = _format_queue(output)
        assert "Test Movie" in result
        assert "downloading" in result

    def test_format_calendar_empty(self):
        """Test formatting empty calendar."""
        output = json.dumps([])
        result = _format_calendar(output)
        assert "No upcoming releases" in result

    def test_format_history_empty(self):
        """Test formatting empty history."""
        output = json.dumps({"records": []})
        result = _format_history(output)
        assert "No history records" in result

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

    def test_radarr_get_movies_tool_process_output(self):
        """Test RadarrGetMoviesTool process_output."""
        tool = RadarrGetMoviesTool(
            name="test",
            description="test",
            func=lambda base_url, api_key: "test",
            config_schema=RadarrConfig,
        )
        output = json.dumps([])
        result = tool.process_output(output)
        assert "No movies found" in result

    def test_radarr_get_movie_by_id_tool_process_output(self):
        """Test RadarrGetMovieByIdTool process_output."""
        tool = RadarrGetMovieByIdTool(
            name="test",
            description="test",
            func=lambda base_url, api_key, id: "test",
            config_schema=RadarrConfig,
        )
        output = json.dumps({"id": 1, "title": "Test", "year": 2024})
        result = tool.process_output(output)
        assert "Test" in result

    def test_radarr_search_movies_tool_process_output(self):
        """Test RadarrSearchMoviesTool process_output."""
        tool = RadarrSearchMoviesTool(
            name="test",
            description="test",
            func=lambda base_url, api_key, term: "test",
            config_schema=RadarrConfig,
        )
        output = json.dumps([])
        result = tool.process_output(output)
        assert "No results found" in result

    def test_radarr_get_queue_tool_process_output(self):
        """Test RadarrGetQueueTool process_output."""
        tool = RadarrGetQueueTool(
            name="test",
            description="test",
            func=lambda base_url, api_key: "test",
            config_schema=RadarrConfig,
        )
        output = json.dumps({"records": []})
        result = tool.process_output(output)
        assert "Queue is empty" in result

    def test_radarr_get_calendar_tool_process_output(self):
        """Test RadarrGetCalendarTool process_output."""
        tool = RadarrGetCalendarTool(
            name="test",
            description="test",
            func=lambda base_url, api_key: "test",
            config_schema=RadarrConfig,
        )
        output = json.dumps([])
        result = tool.process_output(output)
        assert "No upcoming releases" in result

    def test_radarr_get_system_status_tool_process_output(self):
        """Test RadarrGetSystemStatusTool process_output."""
        tool = RadarrGetSystemStatusTool(
            name="test",
            description="test",
            func=lambda base_url, api_key: "test",
            config_schema=RadarrConfig,
        )
        output = json.dumps({"version": "4.0.0"})
        result = tool.process_output(output)
        assert "4.0.0" in result

    def test_radarr_get_quality_profiles_tool_process_output(self):
        """Test RadarrGetQualityProfilesTool process_output."""
        tool = RadarrGetQualityProfilesTool(
            name="test",
            description="test",
            func=lambda base_url, api_key: "test",
            config_schema=RadarrConfig,
        )
        output = json.dumps([])
        result = tool.process_output(output)
        assert "No quality profiles" in result

    def test_radarr_get_root_folders_tool_process_output(self):
        """Test RadarrGetRootFoldersTool process_output."""
        tool = RadarrGetRootFoldersTool(
            name="test",
            description="test",
            func=lambda base_url, api_key: "test",
            config_schema=RadarrConfig,
        )
        output = json.dumps([])
        result = tool.process_output(output)
        assert "No root folders" in result

    def test_radarr_get_history_tool_process_output(self):
        """Test RadarrGetHistoryTool process_output."""
        tool = RadarrGetHistoryTool(
            name="test",
            description="test",
            func=lambda base_url, api_key: "test",
            config_schema=RadarrConfig,
        )
        output = json.dumps({"records": []})
        result = tool.process_output(output)
        assert "No history records" in result

    def test_radarr_get_disk_space_tool_process_output(self):
        """Test RadarrGetDiskSpaceTool process_output."""
        tool = RadarrGetDiskSpaceTool(
            name="test",
            description="test",
            func=lambda base_url, api_key: "test",
            config_schema=RadarrConfig,
        )
        output = json.dumps([])
        result = tool.process_output(output)
        assert "No disk space information" in result


class TestRadarrToolset:
    """Test Radarr toolset creation."""

    def test_get_radarr_toolset(self):
        """Test creating Radarr toolset."""
        toolset = get_radarr_toolset(
            base_url="http://localhost:7878",
            api_key="test_api_key",
        )
        assert toolset.name == "radarr_tools"
        assert len(toolset.tools) > 0
        assert toolset.config["base_url"] == "http://localhost:7878"
        assert toolset.config["api_key"] == "test_api_key"
