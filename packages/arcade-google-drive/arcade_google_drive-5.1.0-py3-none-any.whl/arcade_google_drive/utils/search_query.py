from arcade_google_drive.models import GoogleDriveFileType, get_google_drive_mime_type


class SearchQueryBuilder:
    """Utility class for building Google Drive search queries."""

    @staticmethod
    def _escape_query(query: str) -> str:
        """Escape special characters in the query string for Google Drive search."""
        # Escape backslashes first, then apostrophes
        escaped = query.replace("\\", "\\\\").replace("'", "\\'")
        return escaped

    @staticmethod
    def build_search_query(
        query: str, file_types: list[GoogleDriveFileType] | None, folder_id: str | None = None
    ) -> str:
        """Build the Google Drive search query string."""
        search_terms = []

        # Add the main query
        if query.strip():
            escaped_query = SearchQueryBuilder._escape_query(query.strip())
            search_terms.append(f"fullText contains '{escaped_query}'")

        # Add folder filter
        if folder_id:
            search_terms.append(f"'{folder_id}' in parents")

        # Add file type filters
        if file_types:
            type_conditions = []
            for file_type in file_types:
                mime_types = get_google_drive_mime_type(file_type)
                for mime_type in mime_types:
                    type_conditions.append(f"mimeType = '{mime_type}'")
            if type_conditions:
                search_terms.append(f"({' or '.join(type_conditions)})")

        # Always exclude trashed files
        search_terms.append("trashed = false")

        # Combine all search terms
        return " and ".join(search_terms) if search_terms else "trashed = false"

    @staticmethod
    def _add_date_range_filter(search_terms: list[str], date_range: str) -> None:
        """Add date range filter to search terms."""
        if "last" in date_range.lower():
            if "7 days" in date_range.lower() or "week" in date_range.lower():
                search_terms.append("modifiedTime > '7 days ago'")
            elif "month" in date_range.lower():
                search_terms.append("modifiedTime > '30 days ago'")
            elif "year" in date_range.lower():
                search_terms.append("modifiedTime > '365 days ago'")
        elif " to " in date_range:
            try:
                start_date, end_date = date_range.split(" to ")
                date_condition = (
                    f"modifiedTime >= '{start_date.strip()}' "
                    f"and modifiedTime <= '{end_date.strip()}'"
                )
                search_terms.append(date_condition)
            except ValueError:
                pass  # Invalid date format, skip date filtering
