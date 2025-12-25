"""
Sonarr Tools for Acton Agent

This module provides FunctionTool-based tools for interacting with Sonarr API.
All tools use the modern FunctionTool pattern with Pydantic schemas.

Usage:
    from acton_agent_tools import get_sonarr_toolset

    # Get the toolset with configuration
    toolset = get_sonarr_toolset(
        base_url="http://localhost:8989",
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


class SonarrConfig(ConfigSchema):
    """Configuration schema for Sonarr tools."""

    base_url: str = Field(..., description="Sonarr base URL (e.g., http://localhost:8989)")
    api_key: str = Field(..., description="Sonarr API key")


def _make_request(
    method: str,
    endpoint: str,
    params: dict | None = None,
    json_data: dict | None = None,
    base_url: str | None = None,
    api_key: str | None = None,
) -> str:
    """
    Make HTTP request to Sonarr API.

    Args:
        method: HTTP method (GET, POST, PUT, DELETE)
        endpoint: API endpoint (e.g., "/api/v3/series")
        params: Query parameters
        json_data: JSON body for POST/PUT requests
        base_url: Sonarr base URL
        api_key: Sonarr API key

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


def _format_series_list(output: str) -> str:
    """Convert series list output to Markdown table."""
    try:
        series_list = json.loads(output)
        if not isinstance(series_list, list):
            return output

        if not series_list:
            return "# 📺 Sonarr Series Library\n\n*No series found in library.*"

        # Build Markdown table
        md = "# 📺 Sonarr Series Library\n\n"
        md += "| ID | Title | Year | Status | Network | Monitored | Seasons | Episodes | Downloaded | % Complete | Next Airing |\n"
        md += "|---:|:---|:---:|:---|:---|:---:|---:|---:|---:|---:|:---|\n"

        for series in series_list:
            series_id = series.get("id", "N/A")
            title = series.get("title", "Unknown")
            year = series.get("year", "N/A")
            status = series.get("status", "Unknown")
            network = series.get("network", "Unknown")
            monitored = "✅" if series.get("monitored") else "❌"

            # Statistics
            stats = series.get("statistics", {})
            season_count = series.get("seasonCount", 0)
            episode_count = stats.get("episodeCount", 0)
            episode_file_count = stats.get("episodeFileCount", 0)
            percent = round(stats.get("percentOfEpisodes", 0), 1)

            next_airing = series.get("nextAiring", "N/A")
            if next_airing != "N/A" and "T" in str(next_airing):
                next_airing = next_airing.split("T")[0]

            md += f"| {series_id} | {title} | {year} | {status} | {network} | {monitored} | {season_count} | {episode_count} | {episode_file_count} | {percent}% | {next_airing} |\n"

        total_episodes = sum(s.get("statistics", {}).get("episodeCount", 0) for s in series_list)
        total_downloaded = sum(s.get("statistics", {}).get("episodeFileCount", 0) for s in series_list)

        md += "\n---\n\n"
        md += f"**📊 Summary:** {len(series_list)} series • {total_episodes} episodes • {total_downloaded} downloaded ({round(total_downloaded / total_episodes * 100 if total_episodes > 0 else 0, 1)}%)\n"
    except (json.JSONDecodeError, KeyError, TypeError, ZeroDivisionError):
        return output
    else:
        return md


def _format_series_detail(output: str) -> str:
    """Convert series detail output to formatted Markdown."""
    try:
        series = json.loads(output)
        if not isinstance(series, dict):
            return output

        title = series.get("title", "Unknown Series")
        year = series.get("year", "N/A")
        md = f"# 📺 {title} ({year})\n\n"

        # Overview section
        md += "## 📋 Overview\n\n"
        overview = series.get("overview", "No overview available.")
        md += f"{overview}\n\n"

        # Basic Information
        md += "## Information\n\n"
        md += f"- **Sonarr ID:** {series.get('id', 'N/A')}\n"
        md += f"- **Status:** {series.get('status', 'Unknown')}\n"
        md += f"- **Network:** {series.get('network', 'Unknown')}\n"
        md += f"- **Air Time:** {series.get('airTime', 'Unknown')}\n"
        md += f"- **Series Type:** {series.get('seriesType', 'Standard')}\n"
        md += f"- **Runtime:** {series.get('runtime', 0)} minutes\n"
        md += f"- **Certification:** {series.get('certification', 'Not Rated')}\n"
        md += f"- **Ended:** {'Yes' if series.get('ended') else 'No'}\n\n"

        # External IDs
        md += "## 🔗 External IDs\n\n"
        md += f"- **TVDB ID:** {series.get('tvdbId', 'N/A')}\n"
        md += f"- **TMDB ID:** {series.get('tmdbId', 'N/A')}\n"
        md += f"- **IMDB ID:** {series.get('imdbId', 'N/A')}\n\n"

        # Genres
        genres = series.get("genres", [])
        if genres:
            md += f"**Genres:** {', '.join(genres)}\n\n"

        # Sonarr Configuration
        md += "## ⚙️ Sonarr Configuration\n\n"
        md += f"- **Monitored:** {'✅ Yes' if series.get('monitored') else '❌ No'}\n"
        md += f"- **Quality Profile ID:** {series.get('qualityProfileId', 'N/A')}\n"
        md += f"- **Path:** `{series.get('path', 'N/A')}`\n"
        md += f"- **Root Folder:** `{series.get('rootFolderPath', 'N/A')}`\n"
        md += f"- **Season Folder:** {'✅ Yes' if series.get('seasonFolder') else '❌ No'}\n\n"

        # Statistics
        stats = series.get("statistics", {})
        if stats:
            md += "## 📊 Statistics\n\n"
            md += f"- **Total Episodes:** {stats.get('episodeCount', 0)}\n"
            md += f"- **Downloaded Episodes:** {stats.get('episodeFileCount', 0)}\n"
            md += f"- **Season Count:** {series.get('seasonCount', 0)}\n"
            md += f"- **Total Size:** {round(stats.get('sizeOnDisk', 0) / (1024**3), 2)} GB\n"
            md += f"- **Completion:** {round(stats.get('percentOfEpisodes', 0), 1)}%\n\n"

        # Seasons
        seasons = series.get("seasons", [])
        if seasons:
            md += "## 📺 Seasons\n\n"
            md += "| Season | Monitored | Episodes | Downloaded | % Complete |\n"
            md += "|---:|:---:|---:|---:|---:|\n"

            for season in seasons:
                if season.get("seasonNumber", 0) == 0:
                    continue  # Skip specials for clarity

                season_num = season.get("seasonNumber", "N/A")
                monitored = "✅" if season.get("monitored") else "❌"

                season_stats = season.get("statistics", {})
                episode_count = season_stats.get("episodeCount", 0)
                episode_file_count = season_stats.get("episodeFileCount", 0)
                percent = round(season_stats.get("percentOfEpisodes", 0), 1)

                md += f"| {season_num} | {monitored} | {episode_count} | {episode_file_count} | {percent}% |\n"

            md += "\n"
    except (json.JSONDecodeError, KeyError, TypeError):
        return output
    else:
        return md


def _format_episode_list(output: str) -> str:
    """Convert episode list output to Markdown table."""
    try:
        episodes = json.loads(output)
        if not isinstance(episodes, list):
            return output

        if not episodes:
            return "# 📺 Sonarr Episodes\n\n*No episodes found.*"

        md = "# 📺 Sonarr Episodes\n\n"
        md += "| ID | Episode | Title | Air Date | Runtime | Monitored | Downloaded | File ID |\n"
        md += "|---:|:---|:---|:---|---:|:---:|:---:|:---|\n"

        for ep in episodes:
            ep_id = ep.get("id", "N/A")
            season_num = ep.get("seasonNumber", 0)
            episode_num = ep.get("episodeNumber", 0)
            episode_str = f"S{season_num:02d}E{episode_num:02d}"
            title = ep.get("title", "Unknown")
            air_date = ep.get("airDate", "N/A")
            runtime = ep.get("runtime", 0)
            monitored = "✅" if ep.get("monitored") else "❌"
            has_file = "✅" if ep.get("hasFile") else "❌"
            file_id = ep.get("episodeFileId", "-")

            md += f"| {ep_id} | {episode_str} | {title} | {air_date} | {runtime} min | {monitored} | {has_file} | {file_id} |\n"

        downloaded = sum(1 for ep in episodes if ep.get("hasFile"))
        md += f"\n---\n\n**Total Episodes:** {len(episodes)} • **Downloaded:** {downloaded} ({round(downloaded / len(episodes) * 100, 1)}%)\n"
    except (json.JSONDecodeError, KeyError, TypeError, ZeroDivisionError):
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
            return "# 🔍 Sonarr Series Search\n\n*No results found.*"

        md = f"# 🔍 Sonarr Series Search Results\n\n**Found {len(items)} results**\n\n"
        md += "| # | Title | Year | Status | Network | Type | Seasons | In Library | TVDB | IMDB | Overview |\n"
        md += "|---:|:---|:---:|:---|:---|:---|---:|:---:|:---:|:---:|:---|\n"

        for idx, item in enumerate(items, 1):
            title = item.get("title", "Unknown")
            year = item.get("year", "N/A")
            status = item.get("status", "Unknown")
            network = item.get("network", "Unknown")
            series_type = item.get("seriesType", "Standard")
            season_count = item.get("seasonCount", 0)
            in_library = "✅" if item.get("id", 0) > 0 else "❌"
            tvdb_id = item.get("tvdbId", "N/A")
            imdb_id = item.get("imdbId", "N/A")

            overview = item.get("overview", "")
            if overview:
                overview = overview[:100] + "..." if len(overview) > 100 else overview
                overview = overview.replace("|", "\\|")
            else:
                overview = "-"

            md += f"| {idx} | {title} | {year} | {status} | {network} | {series_type} | {season_count} | {in_library} | {tvdb_id} | {imdb_id} | {overview} |\n"

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
            return "# 📥 Sonarr Download Queue\n\n*Queue is empty.*"

        md = "# 📥 Sonarr Download Queue\n\n"
        md += "| ID | Series | Episode | Status | Progress | Quality | Size | ETA | Protocol |\n"
        md += "|---:|:---|:---|:---|---:|:---|---:|:---|:---|\n"

        for item in records:
            item_id = item.get("id", "N/A")

            series = item.get("series", {})
            series_title = series.get("title", item.get("title", "Unknown"))

            episode = item.get("episode", {})
            season_num = episode.get("seasonNumber", 0)
            episode_num = episode.get("episodeNumber", 0)
            episode_str = f"S{season_num:02d}E{episode_num:02d}"

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

            md += f"| {item_id} | {series_title} | {episode_str} | {status} | {progress}% | {quality} | {size_gb} GB | {eta} | {protocol} |\n"

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
            return "# 📅 Sonarr Calendar\n\n*No upcoming episodes.*"

        md = "# 📅 Sonarr Upcoming Episodes\n\n"
        md += "| Air Date | Series | Episode | Title | Runtime | Downloaded |\n"
        md += "|:---|:---|:---|:---|---:|:---|\n"

        for item in items:
            air_date = item.get("airDate", "N/A")

            series = item.get("series", {})
            series_title = series.get("title", "Unknown")

            season_num = item.get("seasonNumber", 0)
            episode_num = item.get("episodeNumber", 0)
            episode_str = f"S{season_num:02d}E{episode_num:02d}"

            title = item.get("title", "Unknown")
            runtime = item.get("runtime", 0)
            has_file = "✅" if item.get("hasFile") else "❌"

            md += f"| {air_date} | {series_title} | {episode_str} | {title} | {runtime} min | {has_file} |\n"

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
            return "# 📜 Sonarr History\n\n*No history records.*"

        md = "# 📜 Sonarr History\n\n"
        md += "| Date | Event | Series | Episode | Quality | Source | Release |\n"
        md += "|:---|:---|:---|:---|:---|:---|:---|\n"

        for record in records:
            date = record.get("date", "N/A")
            if date != "N/A" and "T" in str(date):
                date = date.split("T")[0]

            event_type = record.get("eventType", "Unknown")

            series = record.get("series", {})
            series_title = series.get("title", "Unknown")

            episode = record.get("episode", {})
            season_num = episode.get("seasonNumber", 0)
            episode_num = episode.get("episodeNumber", 0)
            episode_str = f"S{season_num:02d}E{episode_num:02d}"

            quality = record.get("quality", {}).get("quality", {}).get("name", "Unknown")

            data_obj = record.get("data", {})
            indexer = data_obj.get("indexer", "Unknown")
            release_group = data_obj.get("releaseGroup", "Unknown")

            md += f"| {date} | {event_type} | {series_title} | {episode_str} | {quality} | {indexer} | {release_group} |\n"

        total_records = data.get("totalRecords", len(records))
        md += f"\n---\n\n**Total Records:** {total_records}\n"
    except (json.JSONDecodeError, KeyError, TypeError):
        return output
    else:
        return md


def _format_wanted(output: str) -> str:
    """Convert wanted/missing output to Markdown table."""
    try:
        data = json.loads(output)
        if not isinstance(data, dict):
            return output

        records = data.get("records", [])
        if not records:
            return "# 🔍 Sonarr Wanted Episodes\n\n*No wanted episodes.*"

        md = "# 🔍 Sonarr Wanted Episodes\n\n"
        md += "| Series | Episode | Title | Air Date | Monitored | Last Search |\n"
        md += "|:---|:---|:---|:---|:---:|:---|\n"

        for record in records:
            series = record.get("series", {})
            series_title = series.get("title", "Unknown")

            season_num = record.get("seasonNumber", 0)
            episode_num = record.get("episodeNumber", 0)
            episode_str = f"S{season_num:02d}E{episode_num:02d}"

            title = record.get("title", "Unknown")
            air_date = record.get("airDate", "N/A")
            monitored = "✅" if record.get("monitored") else "❌"

            last_search_time = record.get("lastSearchTime", "Never")
            if last_search_time != "Never" and "T" in str(last_search_time):
                last_search_time = last_search_time.split("T")[0]

            md += f"| {series_title} | {episode_str} | {title} | {air_date} | {monitored} | {last_search_time} |\n"

        total_records = data.get("totalRecords", len(records))
        md += f"\n---\n\n**Total Wanted:** {total_records}\n"
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

        md = "# ⚙️ Sonarr System Status\n\n"
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
            return "# 🎯 Sonarr Quality Profiles\n\n*No quality profiles configured.*"

        md = "# 🎯 Sonarr Quality Profiles\n\n"
        md += "| ID | Name | Upgrade Allowed | Cutoff | Min Format Score |\n"
        md += "|---:|:---|:---:|:---|---:|\n"

        for profile in profiles:
            profile_id = profile.get("id", "N/A")
            name = profile.get("name", "Unknown")
            upgrade_allowed = "✅" if profile.get("upgradeAllowed", True) else "❌"

            cutoff = profile.get("cutoff", 0)
            cutoff_item = next((item for item in profile.get("items", []) if item.get("id") == cutoff), {})
            cutoff_name = cutoff_item.get("name", str(cutoff))

            min_format_score = profile.get("minFormatScore", 0)

            md += f"| {profile_id} | {name} | {upgrade_allowed} | {cutoff_name} | {min_format_score} |\n"

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
            return "# 📁 Sonarr Root Folders\n\n*No root folders configured.*"

        md = "# 📁 Sonarr Root Folders\n\n"
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
            return "# 💿 Sonarr Disk Space\n\n*No disk space information available.*"

        md = "# 💿 Sonarr Disk Space\n\n"
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


class GetSeriesInput(ToolInputSchema):
    """Input schema for getting series."""

    tvdb_id: int | None = Field(None, description="Filter by TVDB ID", alias="tvdbId")
    include_season_images: bool | None = Field(False, description="Include season images", alias="includeSeasonImages")
    id: int | None = Field(None, description="Filter by series ID")


class GetSeriesByIdInput(ToolInputSchema):
    """Input schema for getting series by ID."""

    id: int = Field(..., description="Sonarr series ID")
    include_season_images: bool | None = Field(False, description="Include season images", alias="includeSeasonImages")


class AddSeriesInput(ToolInputSchema):
    """Input schema for adding a series."""

    title: str = Field(..., description="Series title")
    tvdb_id: int = Field(..., description="TVDB ID of the series", alias="tvdbId")
    quality_profile_id: int = Field(..., description="Quality profile ID", alias="qualityProfileId")
    root_folder_path: str = Field(..., description="Root folder path", alias="rootFolderPath")
    monitored: bool = Field(True, description="Whether to monitor the series")
    season_folder: bool = Field(True, description="Use season folders", alias="seasonFolder")
    search_for_missing_episodes: bool = Field(
        False, description="Search for missing episodes after adding", alias="searchForMissingEpisodes"
    )


class UpdateSeriesInput(ToolInputSchema):
    """Input schema for updating a series."""

    id: int = Field(..., description="Sonarr series ID")
    monitored: bool | None = Field(None, description="Monitor status")
    quality_profile_id: int | None = Field(None, description="Quality profile ID", alias="qualityProfileId")
    season_folder: bool | None = Field(None, description="Use season folders", alias="seasonFolder")
    series_type: str | None = Field(None, description="Series type: standard, daily, anime", alias="seriesType")
    path: str | None = Field(None, description="Series path")


class DeleteSeriesInput(ToolInputSchema):
    """Input schema for deleting a series."""

    id: int = Field(..., description="Sonarr series ID")
    delete_files: bool = Field(False, description="Delete series files from disk", alias="deleteFiles")
    add_import_list_exclusion: bool = Field(
        False, description="Add to import exclusion list", alias="addImportListExclusion"
    )


class SearchSeriesInput(ToolInputSchema):
    """Input schema for searching series."""

    term: str = Field(..., description="Search term (series title or TVDB ID with 'tvdb:' prefix)")


class GetEpisodesInput(ToolInputSchema):
    """Input schema for getting episodes."""

    series_id: int = Field(..., description="Series ID", alias="seriesId")
    season_number: int | None = Field(None, description="Filter by season number", alias="seasonNumber")
    episode_file_id: int | None = Field(None, description="Filter by episode file ID", alias="episodeFileId")
    include_images: bool | None = Field(False, description="Include episode images", alias="includeImages")


class UpdateEpisodeInput(ToolInputSchema):
    """Input schema for updating an episode."""

    id: int = Field(..., description="Episode ID")
    monitored: bool | None = Field(None, description="Monitor status")


class GetQueueInput(ToolInputSchema):
    """Input schema for getting queue."""

    page: int | None = Field(1, description="Page number")
    page_size: int | None = Field(20, description="Items per page", alias="pageSize")
    include_unknown_series_items: bool | None = Field(
        False, description="Include unknown series", alias="includeUnknownSeriesItems"
    )


class DeleteQueueItemInput(ToolInputSchema):
    """Input schema for deleting queue item."""

    id: int = Field(..., description="Queue item ID")
    remove_from_client: bool = Field(True, description="Remove from download client", alias="removeFromClient")
    blocklist: bool = Field(False, description="Add to blocklist")
    skip_redownload: bool = Field(False, description="Skip automatic redownload", alias="skipRedownload")


class GetCalendarInput(ToolInputSchema):
    """Input schema for getting calendar."""

    start: str | None = Field(None, description="Start date in ISO format (YYYY-MM-DD)")
    end: str | None = Field(None, description="End date in ISO format (YYYY-MM-DD)")
    unmonitored: bool | None = Field(False, description="Include unmonitored episodes")
    include_series: bool | None = Field(
        True, description="Include full series details with each episode", alias="includeSeries"
    )


class TriggerSeriesSearchInput(ToolInputSchema):
    """Input schema for triggering series search."""

    series_id: int = Field(..., description="Series ID to search for", alias="seriesId")


class TriggerEpisodeSearchInput(ToolInputSchema):
    """Input schema for triggering episode search."""

    episode_ids: list[int] = Field(..., description="Episode IDs to search for", alias="episodeIds")


class GetHistoryInput(ToolInputSchema):
    """Input schema for getting history."""

    page: int | None = Field(1, description="Page number")
    page_size: int | None = Field(20, description="Items per page", alias="pageSize")
    sort_key: str | None = Field("date", description="Sort field", alias="sortKey")
    episode_id: int | None = Field(None, description="Filter by episode ID", alias="episodeId")


class GetWantedInput(ToolInputSchema):
    """Input schema for getting wanted episodes."""

    page: int | None = Field(1, description="Page number")
    page_size: int | None = Field(20, description="Items per page", alias="pageSize")
    sort_key: str | None = Field("airDateUtc", description="Sort field", alias="sortKey")
    include_series: bool | None = Field(True, description="Include series details", alias="includeSeries")


# =============================================================================
# CUSTOM TOOL CLASSES
# =============================================================================


class SonarrGetSeriesTool(FunctionTool):
    """Tool for getting series list with formatted output."""

    def process_output(self, output: str) -> str:
        """Process output using _format_series_list."""
        return _format_series_list(output)


class SonarrGetSeriesByIdTool(FunctionTool):
    """Tool for getting series details with formatted output."""

    def process_output(self, output: str) -> str:
        """Process output using _format_series_detail."""
        return _format_series_detail(output)


class SonarrSearchSeriesTool(FunctionTool):
    """Tool for searching series with formatted output."""

    def process_output(self, output: str) -> str:
        """Process output using _format_search_results."""
        return _format_search_results(output)


class SonarrGetEpisodesTool(FunctionTool):
    """Tool for getting episodes with formatted output."""

    def process_output(self, output: str) -> str:
        """Process output using _format_episode_list."""
        return _format_episode_list(output)


class SonarrGetQueueTool(FunctionTool):
    """Tool for getting queue with formatted output."""

    def process_output(self, output: str) -> str:
        """Process output using _format_queue."""
        return _format_queue(output)


class SonarrGetCalendarTool(FunctionTool):
    """Tool for getting calendar with formatted output."""

    def process_output(self, output: str) -> str:
        """Process output using _format_calendar."""
        return _format_calendar(output)


class SonarrGetSystemStatusTool(FunctionTool):
    """Tool for getting system status with formatted output."""

    def process_output(self, output: str) -> str:
        """Process output using _format_system_status."""
        return _format_system_status(output)


class SonarrGetQualityProfilesTool(FunctionTool):
    """Tool for getting quality profiles with formatted output."""

    def process_output(self, output: str) -> str:
        """Process output using _format_quality_profiles."""
        return _format_quality_profiles(output)


class SonarrGetRootFoldersTool(FunctionTool):
    """Tool for getting root folders with formatted output."""

    def process_output(self, output: str) -> str:
        """Process output using _format_root_folders."""
        return _format_root_folders(output)


class SonarrGetHistoryTool(FunctionTool):
    """Tool for getting history with formatted output."""

    def process_output(self, output: str) -> str:
        """Process output using _format_history."""
        return _format_history(output)


class SonarrGetDiskSpaceTool(FunctionTool):
    """Tool for getting disk space with formatted output."""

    def process_output(self, output: str) -> str:
        """Process output using _format_disk_space."""
        return _format_disk_space(output)


class SonarrGetWantedTool(FunctionTool):
    """Tool for getting wanted episodes with formatted output."""

    def process_output(self, output: str) -> str:
        """Process output using _format_wanted."""
        return _format_wanted(output)


# =============================================================================
# TOOL FUNCTIONS
# =============================================================================


def get_series(
    base_url: str, api_key: str, tvdb_id: int | None = None, include_season_images: bool = False, id: int | None = None
) -> str:
    """Get all TV series from Sonarr library."""
    params = {}
    if tvdb_id:
        params["tvdbId"] = tvdb_id
    if include_season_images:
        params["includeSeasonImages"] = include_season_images
    if id:
        params["id"] = id

    return _make_request(
        "GET", "/api/v3/series", params=params if params else None, base_url=base_url, api_key=api_key
    )


def get_series_by_id(base_url: str, api_key: str, id: int, include_season_images: bool = False) -> str:
    """Get detailed information about a specific series by its Sonarr ID."""
    params = {"includeSeasonImages": include_season_images} if include_season_images else None
    return _make_request("GET", f"/api/v3/series/{id}", params=params, base_url=base_url, api_key=api_key)


def add_series(
    base_url: str,
    api_key: str,
    title: str,
    tvdb_id: int,
    quality_profile_id: int,
    root_folder_path: str,
    monitored: bool = True,
    season_folder: bool = True,
    search_for_missing_episodes: bool = False,
) -> str:
    """Add a new TV series to Sonarr."""
    data = {
        "title": title,
        "tvdbId": tvdb_id,
        "qualityProfileId": quality_profile_id,
        "rootFolderPath": root_folder_path,
        "monitored": monitored,
        "seasonFolder": season_folder,
        "addOptions": {"searchForMissingEpisodes": search_for_missing_episodes},
    }
    return _make_request("POST", "/api/v3/series", json_data=data, base_url=base_url, api_key=api_key)


def update_series(
    base_url: str,
    api_key: str,
    id: int,
    monitored: bool | None = None,
    quality_profile_id: int | None = None,
    season_folder: bool | None = None,
    series_type: str | None = None,
    path: str | None = None,
) -> str:
    """Update an existing series in Sonarr."""
    # First get the current series data
    current = json.loads(_make_request("GET", f"/api/v3/series/{id}", base_url=base_url, api_key=api_key))

    # Update fields
    if monitored is not None:
        current["monitored"] = monitored
    if quality_profile_id is not None:
        current["qualityProfileId"] = quality_profile_id
    if season_folder is not None:
        current["seasonFolder"] = season_folder
    if series_type is not None:
        current["seriesType"] = series_type
    if path is not None:
        current["path"] = path

    return _make_request("PUT", f"/api/v3/series/{id}", json_data=current, base_url=base_url, api_key=api_key)


def delete_series(
    base_url: str, api_key: str, id: int, delete_files: bool = False, add_import_list_exclusion: bool = False
) -> str:
    """Delete a series from Sonarr by its ID."""
    params = {"deleteFiles": delete_files, "addImportListExclusion": add_import_list_exclusion}
    return _make_request("DELETE", f"/api/v3/series/{id}", params=params, base_url=base_url, api_key=api_key)


def search_series(base_url: str, api_key: str, term: str) -> str:
    """Search for TV series to add to Sonarr using a search term."""
    params = {"term": term}
    return _make_request("GET", "/api/v3/series/lookup", params=params, base_url=base_url, api_key=api_key)


def get_episodes(
    base_url: str,
    api_key: str,
    series_id: int,
    season_number: int | None = None,
    episode_file_id: int | None = None,
    include_images: bool = False,
) -> str:
    """Get episodes for a series with download status."""
    params = {"seriesId": series_id}
    if season_number is not None:
        params["seasonNumber"] = season_number
    if episode_file_id is not None:
        params["episodeFileId"] = episode_file_id
    if include_images:
        params["includeImages"] = include_images

    return _make_request("GET", "/api/v3/episode", params=params, base_url=base_url, api_key=api_key)


def update_episode(base_url: str, api_key: str, id: int, monitored: bool | None = None) -> str:
    """Update an episode (typically to change monitored status)."""
    # First get the current episode data
    current = json.loads(_make_request("GET", f"/api/v3/episode/{id}", base_url=base_url, api_key=api_key))

    # Update fields
    if monitored is not None:
        current["monitored"] = monitored

    return _make_request("PUT", f"/api/v3/episode/{id}", json_data=current, base_url=base_url, api_key=api_key)


def get_queue(
    base_url: str, api_key: str, page: int = 1, page_size: int = 20, include_unknown_series_items: bool = False
) -> str:
    """Get the current download queue in Sonarr with pagination support."""
    params = {"page": page, "pageSize": page_size, "includeUnknownSeriesItems": include_unknown_series_items}
    return _make_request("GET", "/api/v3/queue", params=params, base_url=base_url, api_key=api_key)


def delete_queue_item(
    base_url: str,
    api_key: str,
    id: int,
    remove_from_client: bool = True,
    blocklist: bool = False,
    skip_redownload: bool = False,
) -> str:
    """Remove an item from the download queue."""
    params = {"removeFromClient": remove_from_client, "blocklist": blocklist, "skipRedownload": skip_redownload}
    return _make_request("DELETE", f"/api/v3/queue/{id}", params=params, base_url=base_url, api_key=api_key)


def get_calendar(
    base_url: str,
    api_key: str,
    start: str | None = None,
    end: str | None = None,
    unmonitored: bool = False,
    include_series: bool = True,
) -> str:
    """Get upcoming episode air dates in a date range."""
    params = {}
    if start:
        params["start"] = start
    if end:
        params["end"] = end
    if unmonitored:
        params["unmonitored"] = unmonitored
    if include_series:
        params["includeSeries"] = include_series

    return _make_request(
        "GET", "/api/v3/calendar", params=params if params else None, base_url=base_url, api_key=api_key
    )


def get_system_status(base_url: str, api_key: str) -> str:
    """Get Sonarr system status."""
    return _make_request("GET", "/api/v3/system/status", base_url=base_url, api_key=api_key)


def get_quality_profiles(base_url: str, api_key: str) -> str:
    """Get all quality profiles configured in Sonarr."""
    return _make_request("GET", "/api/v3/qualityprofile", base_url=base_url, api_key=api_key)


def get_root_folders(base_url: str, api_key: str) -> str:
    """Get all root folders configured in Sonarr."""
    return _make_request("GET", "/api/v3/rootfolder", base_url=base_url, api_key=api_key)


def trigger_series_search(base_url: str, api_key: str, series_id: int) -> str:
    """Trigger a search for all missing episodes of a series."""
    data = {"name": "SeriesSearch", "seriesId": series_id}
    return _make_request("POST", "/api/v3/command", json_data=data, base_url=base_url, api_key=api_key)


def trigger_episode_search(base_url: str, api_key: str, episode_ids: list[int]) -> str:
    """Trigger a search for specific episodes."""
    data = {"name": "EpisodeSearch", "episodeIds": episode_ids}
    return _make_request("POST", "/api/v3/command", json_data=data, base_url=base_url, api_key=api_key)


def get_history(
    base_url: str,
    api_key: str,
    page: int = 1,
    page_size: int = 20,
    sort_key: str = "date",
    episode_id: int | None = None,
) -> str:
    """Get Sonarr history with pagination and filtering."""
    params = {"page": page, "pageSize": page_size, "sortKey": sort_key}
    if episode_id:
        params["episodeId"] = episode_id

    return _make_request("GET", "/api/v3/history", params=params, base_url=base_url, api_key=api_key)


def get_disk_space(base_url: str, api_key: str) -> str:
    """Get disk space information for all root folders."""
    return _make_request("GET", "/api/v3/diskspace", base_url=base_url, api_key=api_key)


def get_wanted_missing(
    base_url: str,
    api_key: str,
    page: int = 1,
    page_size: int = 20,
    sort_key: str = "airDateUtc",
    include_series: bool = True,
) -> str:
    """Get missing episodes that are monitored."""
    params = {"page": page, "pageSize": page_size, "sortKey": sort_key, "includeSeries": include_series}
    return _make_request("GET", "/api/v3/wanted/missing", params=params, base_url=base_url, api_key=api_key)


def get_wanted_cutoff(
    base_url: str,
    api_key: str,
    page: int = 1,
    page_size: int = 20,
    sort_key: str = "airDateUtc",
    include_series: bool = True,
) -> str:
    """Get episodes that don't meet quality cutoff criteria."""
    params = {"page": page, "pageSize": page_size, "sortKey": sort_key, "includeSeries": include_series}
    return _make_request("GET", "/api/v3/wanted/cutoff", params=params, base_url=base_url, api_key=api_key)


# =============================================================================
# CREATE TOOLS
# =============================================================================

sonarr_get_series_tool = SonarrGetSeriesTool(
    name="sonarr_get_series",
    description="Get all TV series from Sonarr library. Returns detailed statistics including: episodeCount (total episodes), episodeFileCount (downloaded episodes), seasons array with monitored status per season, percentOfEpisodes (download percentage), and series monitoring status. Use this to check download progress and monitored seasons.",
    func=get_series,
    input_schema=GetSeriesInput,
    config_schema=SonarrConfig,
)

sonarr_get_series_by_id_tool = SonarrGetSeriesByIdTool(
    name="sonarr_get_series_by_id",
    description="Get detailed information about a specific series by its Sonarr ID. Returns complete series data including: episodeCount, episodeFileCount, seasons array (with monitored status and statistics per season), download percentages, quality profile, root folder path, and monitoring status. Essential for checking download status and season monitoring.",
    func=get_series_by_id,
    input_schema=GetSeriesByIdInput,
    config_schema=SonarrConfig,
)

sonarr_add_series_tool = FunctionTool(
    name="sonarr_add_series",
    description="Add a new TV series to Sonarr. Requires TVDB ID, title, quality profile, and root folder path. Note: The full path will be {rootFolderPath}/{seriesTitle}.",
    func=add_series,
    input_schema=AddSeriesInput,
    config_schema=SonarrConfig,
)

sonarr_update_series_tool = FunctionTool(
    name="sonarr_update_series",
    description="Update an existing series in Sonarr. Can update monitored status, quality profile, season folder setting, etc.",
    func=update_series,
    input_schema=UpdateSeriesInput,
    config_schema=SonarrConfig,
)

sonarr_delete_series_tool = FunctionTool(
    name="sonarr_delete_series",
    description="Delete a series from Sonarr by its ID",
    func=delete_series,
    input_schema=DeleteSeriesInput,
    config_schema=SonarrConfig,
)

sonarr_search_series_tool = SonarrSearchSeriesTool(
    name="sonarr_search_series",
    description="Search for TV series to add to Sonarr using a search term. Returns detailed search results with TVDB/TMDB/IMDB IDs, status, network, series type, episode counts, and indicates if series is already in library.",
    func=search_series,
    input_schema=SearchSeriesInput,
    config_schema=SonarrConfig,
)

sonarr_get_episodes_tool = SonarrGetEpisodesTool(
    name="sonarr_get_episodes",
    description="Get episodes for a series with download status. Returns array of episodes with: title, episode numbers, air dates, runtime, monitored status, hasFile (whether downloaded), and episodeFileId. Use seriesId (required) and optionally seasonNumber to filter. Essential for checking which specific episodes are downloaded or monitored.",
    func=get_episodes,
    input_schema=GetEpisodesInput,
    config_schema=SonarrConfig,
)

sonarr_update_episode_tool = FunctionTool(
    name="sonarr_update_episode",
    description="Update an episode (typically to change monitored status)",
    func=update_episode,
    input_schema=UpdateEpisodeInput,
    config_schema=SonarrConfig,
)

sonarr_get_queue_tool = SonarrGetQueueTool(
    name="sonarr_get_queue",
    description="Get the current download queue in Sonarr with pagination support. Shows series, episode, download progress, quality, size, ETA, and protocol for each item in queue.",
    func=get_queue,
    input_schema=GetQueueInput,
    config_schema=SonarrConfig,
)

sonarr_delete_queue_item_tool = FunctionTool(
    name="sonarr_delete_queue_item",
    description="Remove an item from the download queue",
    func=delete_queue_item,
    input_schema=DeleteQueueItemInput,
    config_schema=SonarrConfig,
)

sonarr_get_calendar_tool = SonarrGetCalendarTool(
    name="sonarr_get_calendar",
    description="Get upcoming episode air dates in a date range. Returns episodes with air dates, titles, series information, runtime, and download status. REQUIRED: Use ISO format dates (YYYY-MM-DD) for start and end parameters. For 'this week' calculate the date range from current date. Set includeSeries=true to get series details with each episode. Use this to answer questions about upcoming releases.",
    func=get_calendar,
    input_schema=GetCalendarInput,
    config_schema=SonarrConfig,
)

sonarr_get_system_status_tool = SonarrGetSystemStatusTool(
    name="sonarr_get_system_status",
    description="Get Sonarr system status including version, startup time, platform information, database details, and configuration settings.",
    func=get_system_status,
    config_schema=SonarrConfig,
)

sonarr_get_quality_profiles_tool = SonarrGetQualityProfilesTool(
    name="sonarr_get_quality_profiles",
    description="Get all quality profiles configured in Sonarr with upgrade settings, cutoff, minimum format score, and language preferences.",
    func=get_quality_profiles,
    config_schema=SonarrConfig,
)

sonarr_get_root_folders_tool = SonarrGetRootFoldersTool(
    name="sonarr_get_root_folders",
    description="Get all root folders configured in Sonarr with free/total space, accessibility status, and unmapped folders count.",
    func=get_root_folders,
    config_schema=SonarrConfig,
)

sonarr_trigger_series_search_tool = FunctionTool(
    name="sonarr_trigger_series_search",
    description="Trigger a search for all missing episodes of a series",
    func=trigger_series_search,
    input_schema=TriggerSeriesSearchInput,
    config_schema=SonarrConfig,
)

sonarr_trigger_episode_search_tool = FunctionTool(
    name="sonarr_trigger_episode_search",
    description="Trigger a search for specific episodes",
    func=trigger_episode_search,
    input_schema=TriggerEpisodeSearchInput,
    config_schema=SonarrConfig,
)

sonarr_get_history_tool = SonarrGetHistoryTool(
    name="sonarr_get_history",
    description="Get Sonarr history with pagination and filtering. Shows date, event type, series title, episode, quality, source indexer, and release name for all historical actions.",
    func=get_history,
    input_schema=GetHistoryInput,
    config_schema=SonarrConfig,
)

sonarr_get_disk_space_tool = SonarrGetDiskSpaceTool(
    name="sonarr_get_disk_space",
    description="Get disk space information for all root folders. Shows free and total space with percentage free for each storage location.",
    func=get_disk_space,
    config_schema=SonarrConfig,
)

sonarr_get_wanted_missing_tool = SonarrGetWantedTool(
    name="sonarr_get_wanted_missing",
    description="Get missing episodes that are monitored. Shows series, episode, title, air date, monitored status, and last search time for episodes not yet downloaded.",
    func=get_wanted_missing,
    input_schema=GetWantedInput,
    config_schema=SonarrConfig,
)

sonarr_get_wanted_cutoff_tool = SonarrGetWantedTool(
    name="sonarr_get_wanted_cutoff",
    description="Get episodes that don't meet quality cutoff criteria. Shows series, episode, title, air date, monitored status, and last search time for episodes that need quality upgrades.",
    func=get_wanted_cutoff,
    input_schema=GetWantedInput,
    config_schema=SonarrConfig,
)

# Collection of all Sonarr tools
SONARR_TOOLS = [
    sonarr_get_series_tool,
    sonarr_get_series_by_id_tool,
    sonarr_add_series_tool,
    sonarr_update_series_tool,
    sonarr_delete_series_tool,
    sonarr_search_series_tool,
    sonarr_get_episodes_tool,
    sonarr_update_episode_tool,
    sonarr_get_queue_tool,
    sonarr_delete_queue_item_tool,
    sonarr_get_calendar_tool,
    sonarr_get_system_status_tool,
    sonarr_get_quality_profiles_tool,
    sonarr_get_root_folders_tool,
    sonarr_trigger_series_search_tool,
    sonarr_trigger_episode_search_tool,
    sonarr_get_history_tool,
    sonarr_get_disk_space_tool,
    sonarr_get_wanted_missing_tool,
    sonarr_get_wanted_cutoff_tool,
]


def get_sonarr_toolset(base_url: str, api_key: str) -> ToolSet:
    """
    Get Sonarr toolset for TV series management.

    Args:
        base_url: Sonarr base URL (e.g., "http://localhost:8989")
        api_key: Sonarr API key

    Returns:
        ToolSet configured with Sonarr tools
    """
    config = {"base_url": base_url.rstrip("/"), "api_key": api_key}

    return ToolSet(
        name="sonarr_tools",
        description="Tools for managing Sonarr TV series library - search, add, monitor, and download TV shows",
        tools=SONARR_TOOLS,
        config=config,
        config_schema=SonarrConfig,
    )
