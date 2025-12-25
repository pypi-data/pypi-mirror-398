"""
Radarr Tools for Acton Agent

This module provides FunctionTool-based tools for interacting with Radarr API.
All tools use the modern FunctionTool pattern with Pydantic schemas.

Usage:
    from acton_agent_tools import get_radarr_toolset

    # Get the toolset with configuration
    toolset = get_radarr_toolset(
        base_url="http://localhost:7878",
        api_key="your_api_key_here"
    )

    # Use with agent
    agent.register_toolset(toolset)
"""

import json

import requests
from acton_agent.tools import ConfigSchema, FunctionTool, ToolInputSchema, ToolSet
from pydantic import Field


# =============================================================================
# CONFIGURATION
# =============================================================================


class RadarrConfig(ConfigSchema):
    """Configuration schema for Radarr tools."""

    base_url: str = Field(..., description="Radarr base URL (e.g., http://localhost:7878)")
    api_key: str = Field(..., description="Radarr API key")


def _make_request(
    method: str,
    endpoint: str,
    params: dict | None = None,
    json_data: dict | None = None,
    base_url: str | None = None,
    api_key: str | None = None,
) -> str:
    """
    Make HTTP request to Radarr API.

    Args:
        method: HTTP method (GET, POST, PUT, DELETE)
        endpoint: API endpoint (e.g., "/api/v3/movie")
        params: Query parameters
        json_data: JSON body for POST/PUT requests
        base_url: Radarr base URL
        api_key: Radarr API key

    Returns:
        JSON response as string
    """
    if not base_url or not api_key:
        raise ValueError("base_url and api_key are required")

    url = f"{base_url}{endpoint}"
    headers = {"X-Api-Key": api_key}

    response = requests.request(method=method, url=url, headers=headers, params=params, json=json_data, timeout=30)
    response.raise_for_status()

    if response.text:
        return response.text
    return json.dumps({"success": True, "status_code": response.status_code})


def _format_movie_list(output: str) -> str:
    """Convert movie list output to Markdown table."""
    try:
        movies = json.loads(output)
        if not isinstance(movies, list):
            return output

        if not movies:
            return "# 📽️ Radarr Movie Library\n\n*No movies found in library.*"

        # Build Markdown table
        md = "# 📽️ Radarr Movie Library\n\n"
        md += "| ID | Title | Year | Status | Monitored | Downloaded | File Size | Quality | TMDB | IMDB |\n"
        md += "|---:|:---|:---:|:---|:---:|:---:|---:|:---|:---:|:---|\n"

        total_size = 0
        for movie in movies:
            movie_id = movie.get("id", "N/A")
            title = movie.get("title", "Unknown")
            year = movie.get("year", "N/A")
            status = movie.get("status", "Unknown")
            monitored = "✅" if movie.get("monitored") else "❌"
            has_file = "✅" if movie.get("hasFile") else "❌"

            # File size
            size_on_disk = movie.get("sizeOnDisk", 0)
            if size_on_disk:
                size_gb = round(size_on_disk / (1024**3), 2)
                total_size += size_on_disk
                size_str = f"{size_gb} GB"
            else:
                size_str = "-"

            # Get quality from movie file
            quality = "-"
            movie_file = movie.get("movieFile", {})
            if movie_file:
                quality_info = movie_file.get("quality", {}).get("quality", {})
                quality = quality_info.get("name", "-")

            tmdb_id = movie.get("tmdbId", "N/A")
            imdb_id = movie.get("imdbId", "N/A")

            md += f"| {movie_id} | {title} | {year} | {status} | {monitored} | {has_file} | {size_str} | {quality} | {tmdb_id} | {imdb_id} |\n"

        downloaded = sum(1 for m in movies if m.get("hasFile"))
        total_size_gb = round(total_size / (1024**3), 2)

        md += "\n---\n\n"
        md += f"**📊 Summary:** {len(movies)} movies total • {downloaded} downloaded ({round(downloaded / len(movies) * 100, 1)}%) • {total_size_gb} GB total\n"
    except (json.JSONDecodeError, KeyError, TypeError, ZeroDivisionError):
        return output
    else:
        return md


def _format_movie_detail(output: str) -> str:
    """Convert movie detail output to formatted Markdown."""
    try:
        movie = json.loads(output)
        if not isinstance(movie, dict):
            return output

        title = movie.get("title", "Unknown Movie")
        year = movie.get("year", "N/A")
        md = f"# 🎬 {title} ({year})\n\n"

        # Overview section
        md += "## 📋 Overview\n\n"
        overview = movie.get("overview", "No overview available.")
        md += f"{overview}\n\n"

        # Basic Information
        md += "## Information\n\n"
        md += f"- **Radarr ID:** {movie.get('id', 'N/A')}\n"
        md += f"- **Status:** {movie.get('status', 'Unknown')}\n"
        md += f"- **Original Title:** {movie.get('originalTitle', 'N/A')}\n"
        md += f"- **Studio:** {movie.get('studio', 'Unknown')}\n"
        md += f"- **Runtime:** {movie.get('runtime', 0)} minutes\n"
        md += f"- **Certification:** {movie.get('certification', 'Not Rated')}\n\n"

        # External IDs
        md += "## 🔗 External IDs\n\n"
        md += f"- **TMDB ID:** {movie.get('tmdbId', 'N/A')}\n"
        md += f"- **IMDB ID:** {movie.get('imdbId', 'N/A')}\n\n"

        # Release Dates
        md += "## 📅 Release Information\n\n"
        if movie.get("inCinemas"):
            md += f"- **In Cinemas:** {movie.get('inCinemas')}\n"
        if movie.get("digitalRelease"):
            md += f"- **Digital Release:** {movie.get('digitalRelease')}\n"
        if movie.get("physicalRelease"):
            md += f"- **Physical Release:** {movie.get('physicalRelease')}\n"
        md += "\n"

        # Genres and Keywords
        genres = movie.get("genres", [])
        if genres:
            md += f"**Genres:** {', '.join(genres)}\n\n"

        keywords = movie.get("keywords", [])
        if keywords:
            md += f"**Keywords:** {', '.join(keywords[:10])}\n\n"

        # Radarr Configuration
        md += "## ⚙️ Radarr Configuration\n\n"
        md += f"- **Monitored:** {'✅ Yes' if movie.get('monitored') else '❌ No'}\n"
        md += f"- **Quality Profile ID:** {movie.get('qualityProfileId', 'N/A')}\n"
        md += f"- **Minimum Availability:** {movie.get('minimumAvailability', 'N/A')}\n"
        md += f"- **Path:** `{movie.get('path', 'N/A')}`\n"
        md += f"- **Root Folder:** `{movie.get('rootFolderPath', 'N/A')}`\n\n"

        # File Details
        md += "## 💾 File Status\n\n"
        if movie.get("hasFile"):
            md += "**Status:** ✅ Downloaded\n\n"

            movie_file = movie.get("movieFile", {})
            if movie_file:
                md += "### File Details\n\n"
                md += f"- **File ID:** {movie_file.get('id', 'N/A')}\n"
                md += f"- **Relative Path:** `{movie_file.get('relativePath', 'N/A')}`\n"

                quality_info = movie_file.get("quality", {}).get("quality", {})
                md += f"- **Quality:** {quality_info.get('name', 'Unknown')}\n"

                size_bytes = movie_file.get("size", 0)
                size_gb = round(size_bytes / (1024**3), 2) if size_bytes > 0 else 0
                size_mb = round(size_bytes / (1024**2), 2) if size_bytes > 0 else 0
                md += f"- **Size:** {size_gb} GB ({size_mb} MB)\n"

                media_info = movie_file.get("mediaInfo", {})
                if media_info:
                    md += f"- **Video Codec:** {media_info.get('videoCodec', 'N/A')}\n"
                    md += f"- **Audio Codec:** {media_info.get('audioCodec', 'N/A')}\n"
                    md += f"- **Resolution:** {media_info.get('resolution', 'N/A')}\n"
                    md += f"- **Runtime:** {media_info.get('runTime', 'N/A')}\n"

                md += f"- **Date Added:** {movie_file.get('dateAdded', 'N/A')}\n"
        else:
            md += "**Status:** ❌ Not Downloaded\n\n"
            md += f"- **Size on Disk:** {movie.get('sizeOnDisk', 0)} bytes\n"
            md += f"- **Available:** {'Yes' if movie.get('isAvailable') else 'No'}\n"
    except (json.JSONDecodeError, KeyError, TypeError):
        return output
    else:
        return md


def _format_search_results(output: str) -> str:
    """Convert search results to Markdown table."""
    try:
        items = json.loads(output)
        if not isinstance(items, list):
            return output

        if not items:
            return "# 🔍 Radarr Movie Search\n\n*No results found.*"

        md = f"# 🔍 Radarr Movie Search Results\n\n**Found {len(items)} results**\n\n"
        md += "| # | Title | Year | Status | Studio | In Library | TMDB | IMDB | Genres | Overview |\n"
        md += "|---:|:---|:---:|:---|:---|:---:|:---:|:---:|:---|:---|\n"

        for idx, item in enumerate(items, 1):
            title = item.get("title", "Unknown")
            year = item.get("year", "N/A")
            status = item.get("status", "Unknown")
            studio = item.get("studio", "Unknown")
            in_library = "✅" if item.get("hasFile") or item.get("id", 0) > 0 else "❌"
            tmdb_id = item.get("tmdbId", "N/A")
            imdb_id = item.get("imdbId", "N/A")

            genres = item.get("genres", [])
            genres_str = ", ".join(genres[:3]) if genres else "-"
            if len(genres) > 3:
                genres_str += "..."

            overview = item.get("overview", "")
            if overview:
                overview = overview[:100] + "..." if len(overview) > 100 else overview
                overview = overview.replace("|", "\\|")
            else:
                overview = "-"

            md += f"| {idx} | {title} | {year} | {status} | {studio} | {in_library} | {tmdb_id} | {imdb_id} | {genres_str} | {overview} |\n"

        md += f"\n---\n\n**Total Results:** {len(items)}\n"
    except (json.JSONDecodeError, KeyError, TypeError):
        return output
    else:
        return md


def _format_queue(output: str) -> str:
    """Convert queue output to Markdown table."""
    try:
        data = json.loads(output)
        if not isinstance(data, dict):
            return output

        records = data.get("records", [])
        if not records:
            return "# 📥 Radarr Download Queue\n\n*Queue is empty.*"

        md = "# 📥 Radarr Download Queue\n\n"
        md += "| ID | Movie | Status | Progress | Quality | Size | ETA | Protocol |\n"
        md += "|---:|:---|:---|---:|:---|---:|:---|:---|\n"

        for item in records:
            item_id = item.get("id", "N/A")
            movie = item.get("movie", {})
            title = movie.get("title", item.get("title", "Unknown"))
            status = item.get("status", "Unknown")

            size_bytes = item.get("size", 0)
            sizeleft = item.get("sizeleft", 0)
            progress = 0
            if size_bytes > 0:
                progress = round((1 - sizeleft / size_bytes) * 100, 1)

            quality = item.get("quality", {}).get("quality", {}).get("name", "Unknown")
            size_gb = round(size_bytes / (1024**3), 2) if size_bytes > 0 else 0
            eta = item.get("timeleft", "Unknown")
            protocol = item.get("protocol", "Unknown")

            md += f"| {item_id} | {title} | {status} | {progress}% | {quality} | {size_gb} GB | {eta} | {protocol} |\n"

        md += f"\n---\n\n**Items in Queue:** {len(records)}\n"
    except (json.JSONDecodeError, KeyError, TypeError, ZeroDivisionError):
        return output
    else:
        return md


def _format_calendar(output: str) -> str:
    """Convert calendar output to Markdown table."""
    try:
        items = json.loads(output)
        if not isinstance(items, list):
            return output

        if not items:
            return "# 📅 Radarr Calendar\n\n*No upcoming releases.*"

        md = "# 📅 Radarr Upcoming Releases\n\n"
        md += "| Title | Year | Release Type | Release Date | Status | Downloaded | Quality |\n"
        md += "|:---|:---:|:---|:---|:---|:---:|:---|\n"

        for item in items:
            title = item.get("title", "Unknown")
            year = item.get("year", "N/A")

            # Determine release type and date
            release_type = "Unknown"
            release_date = "N/A"
            if item.get("physicalRelease"):
                release_type = "Physical"
                release_date = item.get("physicalRelease", "N/A")
            elif item.get("digitalRelease"):
                release_type = "Digital"
                release_date = item.get("digitalRelease", "N/A")
            elif item.get("inCinemas"):
                release_type = "Cinema"
                release_date = item.get("inCinemas", "N/A")

            # Format date
            if release_date != "N/A" and "T" in str(release_date):
                release_date = release_date.split("T")[0]

            status = item.get("status", "Unknown")
            has_file = "✅" if item.get("hasFile") else "❌"

            quality = "-"
            movie_file = item.get("movieFile", {})
            if movie_file:
                quality_info = movie_file.get("quality", {}).get("quality", {})
                quality = quality_info.get("name", "-")

            md += f"| {title} | {year} | {release_type} | {release_date} | {status} | {has_file} | {quality} |\n"

        md += f"\n---\n\n**Total Upcoming:** {len(items)}\n"
    except (json.JSONDecodeError, KeyError, TypeError):
        return output
    else:
        return md


def _format_history(output: str) -> str:
    """Convert history output to Markdown table."""
    try:
        data = json.loads(output)
        if not isinstance(data, dict):
            return output

        records = data.get("records", [])
        if not records:
            return "# 📜 Radarr History\n\n*No history records.*"

        md = "# 📜 Radarr History\n\n"
        md += "| Date | Event | Movie | Quality | Source | Release |\n"
        md += "|:---|:---|:---|:---|:---|:---|\n"

        for record in records:
            date = record.get("date", "N/A")
            if date != "N/A" and "T" in str(date):
                date = date.split("T")[0]

            event_type = record.get("eventType", "Unknown")
            movie = record.get("movie", {})
            movie_title = movie.get("title", "Unknown")

            quality = record.get("quality", {}).get("quality", {}).get("name", "Unknown")

            data_obj = record.get("data", {})
            indexer = data_obj.get("indexer", "Unknown")
            release_name = data_obj.get("releaseGroup", "Unknown")

            md += f"| {date} | {event_type} | {movie_title} | {quality} | {indexer} | {release_name} |\n"

        total_records = data.get("totalRecords", len(records))
        md += f"\n---\n\n**Total Records:** {total_records}\n"
    except (json.JSONDecodeError, KeyError, TypeError):
        return output
    else:
        return md


def _format_system_status(output: str) -> str:
    """Convert system status to formatted Markdown."""
    try:
        status = json.loads(output)
        if not isinstance(status, dict):
            return output

        md = "# ⚙️ Radarr System Status\n\n"
        md += f"- **Version:** {status.get('version', 'Unknown')}\n"
        md += f"- **Build Time:** {status.get('buildTime', 'Unknown')}\n"
        md += f"- **Is Debug:** {status.get('isDebug', False)}\n"
        md += f"- **Is Production:** {status.get('isProduction', True)}\n"
        md += f"- **Is Admin:** {status.get('isAdmin', False)}\n"
        md += f"- **Is User Interactive:** {status.get('isUserInteractive', True)}\n"
        md += f"- **Startup Path:** `{status.get('startupPath', 'Unknown')}`\n"
        md += f"- **App Data:** `{status.get('appData', 'Unknown')}`\n"
        md += f"- **OS Name:** {status.get('osName', 'Unknown')}\n"
        md += f"- **OS Version:** {status.get('osVersion', 'Unknown')}\n"
        md += f"- **Is Mono Runtime:** {status.get('isMonoRuntime', False)}\n"
        md += f"- **Is .NET Core:** {status.get('isNetCore', True)}\n"
        md += f"- **Is Linux:** {status.get('isLinux', False)}\n"
        md += f"- **Is macOS:** {status.get('isOsx', False)}\n"
        md += f"- **Is Windows:** {status.get('isWindows', False)}\n"
        md += f"- **Is Docker:** {status.get('isDocker', False)}\n"
        md += f"- **Mode:** {status.get('mode', 'Unknown')}\n"
        md += f"- **Branch:** {status.get('branch', 'Unknown')}\n"
        md += f"- **Authentication:** {status.get('authentication', 'None')}\n"
        md += f"- **SQLite Version:** {status.get('sqliteVersion', 'Unknown')}\n"
        md += f"- **Migration Version:** {status.get('migrationVersion', 'Unknown')}\n"
        md += f"- **URL Base:** {status.get('urlBase', '/')}\n"
        md += f"- **Runtime Version:** {status.get('runtimeVersion', 'Unknown')}\n"
        md += f"- **Runtime Name:** {status.get('runtimeName', 'Unknown')}\n"
        md += f"- **Start Time:** {status.get('startTime', 'Unknown')}\n"
        md += f"- **Package Version:** {status.get('packageVersion', 'Unknown')}\n"
        md += f"- **Package Author:** {status.get('packageAuthor', 'Unknown')}\n"
        md += f"- **Package Update Mechanism:** {status.get('packageUpdateMechanism', 'Unknown')}\n"
    except (json.JSONDecodeError, KeyError, TypeError):
        return output
    else:
        return md


def _format_quality_profiles(output: str) -> str:
    """Convert quality profiles to Markdown table."""
    try:
        profiles = json.loads(output)
        if not isinstance(profiles, list):
            return output

        if not profiles:
            return "# 🎯 Radarr Quality Profiles\n\n*No quality profiles configured.*"

        md = "# 🎯 Radarr Quality Profiles\n\n"
        md += "| ID | Name | Upgrade Allowed | Cutoff | Min Format Score | Language |\n"
        md += "|---:|:---|:---:|:---|---:|:---|\n"

        for profile in profiles:
            profile_id = profile.get("id", "N/A")
            name = profile.get("name", "Unknown")
            upgrade_allowed = "✅" if profile.get("upgradeAllowed", True) else "❌"

            cutoff = profile.get("cutoff", 0)
            cutoff_item = next((item for item in profile.get("items", []) if item.get("id") == cutoff), {})
            cutoff_name = cutoff_item.get("name", str(cutoff))

            min_format_score = profile.get("minFormatScore", 0)
            language = profile.get("language", {}).get("name", "Unknown")

            md += f"| {profile_id} | {name} | {upgrade_allowed} | {cutoff_name} | {min_format_score} | {language} |\n"

        md += f"\n---\n\n**Total Profiles:** {len(profiles)}\n"
    except (json.JSONDecodeError, KeyError, TypeError):
        return output
    else:
        return md


def _format_root_folders(output: str) -> str:
    """Convert root folders to Markdown table."""
    try:
        folders = json.loads(output)
        if not isinstance(folders, list):
            return output

        if not folders:
            return "# 📁 Radarr Root Folders\n\n*No root folders configured.*"

        md = "# 📁 Radarr Root Folders\n\n"
        md += "| ID | Path | Free Space | Total Space | Accessible | Unmapped Folders |\n"
        md += "|---:|:---|---:|---:|:---:|---:|\n"

        for folder in folders:
            folder_id = folder.get("id", "N/A")
            path = folder.get("path", "Unknown")

            free_bytes = folder.get("freeSpace", 0)
            total_bytes = folder.get("totalSpace", 0)
            free_gb = round(free_bytes / (1024**3), 2)
            total_gb = round(total_bytes / (1024**3), 2)

            accessible = "✅" if folder.get("accessible", True) else "❌"

            unmapped_folders = folder.get("unmappedFolders", [])
            unmapped_count = len(unmapped_folders) if unmapped_folders else 0

            md += f"| {folder_id} | `{path}` | {free_gb} GB | {total_gb} GB | {accessible} | {unmapped_count} |\n"

        md += f"\n---\n\n**Total Folders:** {len(folders)}\n"
    except (json.JSONDecodeError, KeyError, TypeError):
        return output
    else:
        return md


def _format_disk_space(output: str) -> str:
    """Convert disk space to Markdown table."""
    try:
        spaces = json.loads(output)
        if not isinstance(spaces, list):
            return output

        if not spaces:
            return "# 💿 Radarr Disk Space\n\n*No disk space information available.*"

        md = "# 💿 Radarr Disk Space\n\n"
        md += "| Path | Label | Free Space | Total Space | % Free |\n"
        md += "|:---|:---|---:|---:|---:|\n"

        for space in spaces:
            path = space.get("path", "Unknown")
            label = space.get("label", "N/A")

            free_bytes = space.get("freeSpace", 0)
            total_bytes = space.get("totalSpace", 0)

            free_gb = round(free_bytes / (1024**3), 2)
            total_gb = round(total_bytes / (1024**3), 2)

            percent_free = round((free_bytes / total_bytes * 100), 1) if total_bytes > 0 else 0

            md += f"| `{path}` | {label} | {free_gb} GB | {total_gb} GB | {percent_free}% |\n"

        total_free = sum(s.get("freeSpace", 0) for s in spaces)
        total_space = sum(s.get("totalSpace", 0) for s in spaces)
        md += f"\n---\n\n**Total Free:** {round(total_free / (1024**3), 2)} GB | **Total Space:** {round(total_space / (1024**3), 2)} GB\n"
    except (json.JSONDecodeError, KeyError, TypeError, ZeroDivisionError):
        return output
    else:
        return md


# =============================================================================
# INPUT SCHEMAS
# =============================================================================


class GetMoviesInput(ToolInputSchema):
    """Input schema for getting movies."""

    tmdb_id: int | None = Field(None, description="Filter by TMDB ID", alias="tmdbId")


class GetMovieByIdInput(ToolInputSchema):
    """Input schema for getting movie by ID."""

    id: int = Field(..., description="Radarr movie ID")


class AddMovieInput(ToolInputSchema):
    """Input schema for adding a movie."""

    title: str = Field(..., description="Movie title")
    tmdb_id: int = Field(..., description="TMDB ID of the movie", alias="tmdbId")
    quality_profile_id: int = Field(..., description="Quality profile ID", alias="qualityProfileId")
    root_folder_path: str = Field(..., description="Root folder path", alias="rootFolderPath")
    monitored: bool = Field(True, description="Whether to monitor the movie")
    search_for_movie: bool = Field(False, description="Search for movie after adding", alias="searchForMovie")


class UpdateMovieInput(ToolInputSchema):
    """Input schema for updating a movie."""

    id: int = Field(..., description="Radarr movie ID")
    monitored: bool | None = Field(None, description="Monitor status")
    quality_profile_id: int | None = Field(None, description="Quality profile ID", alias="qualityProfileId")
    minimum_availability: str | None = Field(None, description="Minimum availability", alias="minimumAvailability")
    tags: list[int] | None = Field(None, description="Tag IDs")


class DeleteMovieInput(ToolInputSchema):
    """Input schema for deleting a movie."""

    id: int = Field(..., description="Radarr movie ID")
    delete_files: bool = Field(False, description="Delete movie files from disk", alias="deleteFiles")
    add_import_exclusion: bool = Field(False, description="Add to import exclusion list", alias="addImportExclusion")


class SearchMoviesInput(ToolInputSchema):
    """Input schema for searching movies."""

    term: str = Field(..., description="Search term (movie title or TMDB ID with 'tmdb:' prefix)")


class GetQueueInput(ToolInputSchema):
    """Input schema for getting queue."""

    page: int | None = Field(1, description="Page number")
    page_size: int | None = Field(20, description="Items per page", alias="pageSize")
    include_unknown_movie_items: bool | None = Field(
        False, description="Include unknown movies", alias="includeUnknownMovieItems"
    )


class DeleteQueueItemInput(ToolInputSchema):
    """Input schema for deleting queue item."""

    id: int = Field(..., description="Queue item ID")
    remove_from_client: bool = Field(True, description="Remove from download client", alias="removeFromClient")
    blocklist: bool = Field(False, description="Add to blocklist")


class GetCalendarInput(ToolInputSchema):
    """Input schema for getting calendar."""

    start: str | None = Field(None, description="Start date in ISO format (YYYY-MM-DD)")
    end: str | None = Field(None, description="End date in ISO format (YYYY-MM-DD)")
    unmonitored: bool | None = Field(False, description="Include unmonitored movies")


class TriggerSearchInput(ToolInputSchema):
    """Input schema for triggering search."""

    movie_ids: list[int] = Field(..., description="Movie IDs to search for", alias="movieIds")


class GetHistoryInput(ToolInputSchema):
    """Input schema for getting history."""

    page: int | None = Field(1, description="Page number")
    page_size: int | None = Field(20, description="Items per page", alias="pageSize")
    sort_key: str | None = Field("date", description="Sort field", alias="sortKey")
    movie_id: int | None = Field(None, description="Filter by movie ID", alias="movieId")


# =============================================================================
# CUSTOM TOOL CLASSES
# =============================================================================


class RadarrGetMoviesTool(FunctionTool):
    """Tool for getting movies list with formatted output."""

    def process_output(self, output: str) -> str:
        """Process output using _format_movie_list."""
        return _format_movie_list(output)


class RadarrGetMovieByIdTool(FunctionTool):
    """Tool for getting movie details with formatted output."""

    def process_output(self, output: str) -> str:
        """Process output using _format_movie_detail."""
        return _format_movie_detail(output)


class RadarrSearchMoviesTool(FunctionTool):
    """Tool for searching movies with formatted output."""

    def process_output(self, output: str) -> str:
        """Process output using _format_search_results."""
        return _format_search_results(output)


class RadarrGetQueueTool(FunctionTool):
    """Tool for getting queue with formatted output."""

    def process_output(self, output: str) -> str:
        """Process output using _format_queue."""
        return _format_queue(output)


class RadarrGetCalendarTool(FunctionTool):
    """Tool for getting calendar with formatted output."""

    def process_output(self, output: str) -> str:
        """Process output using _format_calendar."""
        return _format_calendar(output)


class RadarrGetSystemStatusTool(FunctionTool):
    """Tool for getting system status with formatted output."""

    def process_output(self, output: str) -> str:
        """Process output using _format_system_status."""
        return _format_system_status(output)


class RadarrGetQualityProfilesTool(FunctionTool):
    """Tool for getting quality profiles with formatted output."""

    def process_output(self, output: str) -> str:
        """Process output using _format_quality_profiles."""
        return _format_quality_profiles(output)


class RadarrGetRootFoldersTool(FunctionTool):
    """Tool for getting root folders with formatted output."""

    def process_output(self, output: str) -> str:
        """Process output using _format_root_folders."""
        return _format_root_folders(output)


class RadarrGetHistoryTool(FunctionTool):
    """Tool for getting history with formatted output."""

    def process_output(self, output: str) -> str:
        """Process output using _format_history."""
        return _format_history(output)


class RadarrGetDiskSpaceTool(FunctionTool):
    """Tool for getting disk space with formatted output."""

    def process_output(self, output: str) -> str:
        """Process output using _format_disk_space."""
        return _format_disk_space(output)


# =============================================================================
# TOOL FUNCTIONS
# =============================================================================


def get_movies(base_url: str, api_key: str, tmdb_id: int | None = None) -> str:
    """Get all movies from Radarr library."""
    params = {"tmdbId": tmdb_id} if tmdb_id else None
    return _make_request("GET", "/api/v3/movie", params=params, base_url=base_url, api_key=api_key)


def get_movie_by_id(base_url: str, api_key: str, id: int) -> str:
    """Get detailed information about a specific movie by its Radarr ID."""
    return _make_request("GET", f"/api/v3/movie/{id}", base_url=base_url, api_key=api_key)


def add_movie(
    base_url: str,
    api_key: str,
    title: str,
    tmdb_id: int,
    quality_profile_id: int,
    root_folder_path: str,
    monitored: bool = True,
    search_for_movie: bool = False,
) -> str:
    """Add a new movie to Radarr."""
    data = {
        "title": title,
        "tmdbId": tmdb_id,
        "qualityProfileId": quality_profile_id,
        "rootFolderPath": root_folder_path,
        "monitored": monitored,
        "addOptions": {"searchForMovie": search_for_movie},
    }
    return _make_request("POST", "/api/v3/movie", json_data=data, base_url=base_url, api_key=api_key)


def update_movie(
    base_url: str,
    api_key: str,
    id: int,
    monitored: bool | None = None,
    quality_profile_id: int | None = None,
    minimum_availability: str | None = None,
    tags: list[int] | None = None,
) -> str:
    """Update an existing movie in Radarr."""
    # First get the current movie data
    current = json.loads(_make_request("GET", f"/api/v3/movie/{id}", base_url=base_url, api_key=api_key))

    # Update fields
    if monitored is not None:
        current["monitored"] = monitored
    if quality_profile_id is not None:
        current["qualityProfileId"] = quality_profile_id
    if minimum_availability is not None:
        current["minimumAvailability"] = minimum_availability
    if tags is not None:
        current["tags"] = tags

    return _make_request("PUT", f"/api/v3/movie/{id}", json_data=current, base_url=base_url, api_key=api_key)


def delete_movie(
    base_url: str, api_key: str, id: int, delete_files: bool = False, add_import_exclusion: bool = False
) -> str:
    """Delete a movie from Radarr by its ID."""
    params = {"deleteFiles": delete_files, "addImportExclusion": add_import_exclusion}
    return _make_request("DELETE", f"/api/v3/movie/{id}", params=params, base_url=base_url, api_key=api_key)


def search_movies(base_url: str, api_key: str, term: str) -> str:
    """Search for movies to add to Radarr using a search term."""
    params = {"term": term}
    return _make_request("GET", "/api/v3/movie/lookup", params=params, base_url=base_url, api_key=api_key)


def get_queue(
    base_url: str, api_key: str, page: int = 1, page_size: int = 20, include_unknown_movie_items: bool = False
) -> str:
    """Get the current download queue in Radarr with pagination support."""
    params = {"page": page, "pageSize": page_size, "includeUnknownMovieItems": include_unknown_movie_items}
    return _make_request("GET", "/api/v3/queue", params=params, base_url=base_url, api_key=api_key)


def delete_queue_item(
    base_url: str, api_key: str, id: int, remove_from_client: bool = True, blocklist: bool = False
) -> str:
    """Remove an item from the download queue."""
    params = {"removeFromClient": remove_from_client, "blocklist": blocklist}
    return _make_request("DELETE", f"/api/v3/queue/{id}", params=params, base_url=base_url, api_key=api_key)


def get_calendar(
    base_url: str, api_key: str, start: str | None = None, end: str | None = None, unmonitored: bool = False
) -> str:
    """Get upcoming movie releases in a date range."""
    params = {}
    if start:
        params["start"] = start
    if end:
        params["end"] = end
    if unmonitored:
        params["unmonitored"] = unmonitored

    return _make_request("GET", "/api/v3/calendar", params=params, base_url=base_url, api_key=api_key)


def get_system_status(base_url: str, api_key: str) -> str:
    """Get Radarr system status."""
    return _make_request("GET", "/api/v3/system/status", base_url=base_url, api_key=api_key)


def get_quality_profiles(base_url: str, api_key: str) -> str:
    """Get all quality profiles configured in Radarr."""
    return _make_request("GET", "/api/v3/qualityprofile", base_url=base_url, api_key=api_key)


def get_root_folders(base_url: str, api_key: str) -> str:
    """Get all root folders configured in Radarr."""
    return _make_request("GET", "/api/v3/rootfolder", base_url=base_url, api_key=api_key)


def trigger_search(base_url: str, api_key: str, movie_ids: list[int]) -> str:
    """Trigger a search for specific movies."""
    data = {"name": "MoviesSearch", "movieIds": movie_ids}
    return _make_request("POST", "/api/v3/command", json_data=data, base_url=base_url, api_key=api_key)


def get_history(
    base_url: str, api_key: str, page: int = 1, page_size: int = 20, sort_key: str = "date", movie_id: int | None = None
) -> str:
    """Get Radarr history with pagination and filtering."""
    params = {"page": page, "pageSize": page_size, "sortKey": sort_key}
    if movie_id:
        params["movieId"] = movie_id

    return _make_request("GET", "/api/v3/history", params=params, base_url=base_url, api_key=api_key)


def get_disk_space(base_url: str, api_key: str) -> str:
    """Get disk space information for all root folders."""
    return _make_request("GET", "/api/v3/diskspace", base_url=base_url, api_key=api_key)


# =============================================================================
# CREATE TOOLS
# =============================================================================

radarr_get_movies_tool = RadarrGetMoviesTool(
    name="radarr_get_movies",
    description="Get all movies from Radarr library. Returns array of movies with: title, year, hasFile (download status), monitored status, quality profile, ratings, and file details. Use this to get library overview or check download counts. For detailed info on a specific movie, use radarr_get_movie_by_id instead.",
    func=get_movies,
    input_schema=GetMoviesInput,
    config_schema=RadarrConfig,
)

radarr_get_movie_by_id_tool = RadarrGetMovieByIdTool(
    name="radarr_get_movie_by_id",
    description="Get detailed information about a specific movie by its Radarr ID. Returns complete movie data including: title, year, hasFile (download status), movieFile (file details if downloaded), monitored status, quality profile, ratings, and overview. Essential for checking if a movie is downloaded.",
    func=get_movie_by_id,
    input_schema=GetMovieByIdInput,
    config_schema=RadarrConfig,
)

radarr_add_movie_tool = FunctionTool(
    name="radarr_add_movie",
    description="Add a new movie to Radarr. Requires TMDB ID, title, quality profile, and root folder path. Note: The full path will be {rootFolderPath}/{movieTitle}.",
    func=add_movie,
    input_schema=AddMovieInput,
    config_schema=RadarrConfig,
)

radarr_update_movie_tool = FunctionTool(
    name="radarr_update_movie",
    description="Update an existing movie in Radarr. Can update monitored status, quality profile, tags, etc.",
    func=update_movie,
    input_schema=UpdateMovieInput,
    config_schema=RadarrConfig,
)

radarr_delete_movie_tool = FunctionTool(
    name="radarr_delete_movie",
    description="Delete a movie from Radarr by its ID",
    func=delete_movie,
    input_schema=DeleteMovieInput,
    config_schema=RadarrConfig,
)

radarr_search_movies_tool = RadarrSearchMoviesTool(
    name="radarr_search_movies",
    description="Search for movies to add to Radarr using a search term. Returns detailed search results with TMDB/IMDB IDs, status, studio, genres, and indicates if movie is already in library.",
    func=search_movies,
    input_schema=SearchMoviesInput,
    config_schema=RadarrConfig,
)

radarr_get_queue_tool = RadarrGetQueueTool(
    name="radarr_get_queue",
    description="Get the current download queue in Radarr with pagination support. Shows download progress, quality, size, ETA, and protocol for each item in queue.",
    func=get_queue,
    input_schema=GetQueueInput,
    config_schema=RadarrConfig,
)

radarr_delete_queue_item_tool = FunctionTool(
    name="radarr_delete_queue_item",
    description="Remove an item from the download queue",
    func=delete_queue_item,
    input_schema=DeleteQueueItemInput,
    config_schema=RadarrConfig,
)

radarr_get_calendar_tool = RadarrGetCalendarTool(
    name="radarr_get_calendar",
    description="Get upcoming movie releases in a date range. Returns movies with release dates (cinema, digital, physical), download status, and file information. REQUIRED: Use ISO format dates (YYYY-MM-DD) for start and end parameters. For 'this week' calculate the date range from current date. Use this to answer questions about upcoming movie releases.",
    func=get_calendar,
    input_schema=GetCalendarInput,
    config_schema=RadarrConfig,
)

radarr_get_system_status_tool = RadarrGetSystemStatusTool(
    name="radarr_get_system_status",
    description="Get Radarr system status including version, startup time, platform information, database details, and configuration settings.",
    func=get_system_status,
    config_schema=RadarrConfig,
)

radarr_get_quality_profiles_tool = RadarrGetQualityProfilesTool(
    name="radarr_get_quality_profiles",
    description="Get all quality profiles configured in Radarr with upgrade settings, cutoff, minimum format score, and language preferences.",
    func=get_quality_profiles,
    config_schema=RadarrConfig,
)

radarr_get_root_folders_tool = RadarrGetRootFoldersTool(
    name="radarr_get_root_folders",
    description="Get all root folders configured in Radarr with free/total space, accessibility status, and unmapped folders count.",
    func=get_root_folders,
    config_schema=RadarrConfig,
)

radarr_trigger_search_tool = FunctionTool(
    name="radarr_trigger_search",
    description="Trigger a search for a specific movie",
    func=trigger_search,
    input_schema=TriggerSearchInput,
    config_schema=RadarrConfig,
)

radarr_get_history_tool = RadarrGetHistoryTool(
    name="radarr_get_history",
    description="Get Radarr history with pagination and filtering. Shows date, event type, movie title, quality, source indexer, and release name for all historical actions.",
    func=get_history,
    input_schema=GetHistoryInput,
    config_schema=RadarrConfig,
)

radarr_get_disk_space_tool = RadarrGetDiskSpaceTool(
    name="radarr_get_disk_space",
    description="Get disk space information for all root folders. Shows free and total space with percentage free for each storage location.",
    func=get_disk_space,
    config_schema=RadarrConfig,
)

# Collection of all Radarr tools
RADARR_TOOLS = [
    radarr_get_movies_tool,
    radarr_get_movie_by_id_tool,
    radarr_add_movie_tool,
    radarr_update_movie_tool,
    radarr_delete_movie_tool,
    radarr_search_movies_tool,
    radarr_get_queue_tool,
    radarr_delete_queue_item_tool,
    radarr_get_calendar_tool,
    radarr_get_system_status_tool,
    radarr_get_quality_profiles_tool,
    radarr_get_root_folders_tool,
    radarr_trigger_search_tool,
    radarr_get_history_tool,
    radarr_get_disk_space_tool,
]


def get_radarr_toolset(base_url: str, api_key: str) -> ToolSet:
    """
    Get Radarr toolset for movie management.

    Args:
        base_url: Radarr base URL (e.g., "http://localhost:7878")
        api_key: Radarr API key

    Returns:
        ToolSet configured with Radarr tools
    """
    config = {"base_url": base_url.rstrip("/"), "api_key": api_key}

    return ToolSet(
        name="radarr_tools",
        description="Tools for managing Radarr movie library - search, add, monitor, and download movies",
        tools=RADARR_TOOLS,
        config=config,
        config_schema=RadarrConfig,
    )
