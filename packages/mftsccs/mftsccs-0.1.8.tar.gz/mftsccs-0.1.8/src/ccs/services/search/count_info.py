"""
CountInfo - Count information for query results.
"""

from dataclasses import dataclass
from typing import Any, Dict, List, Optional


@dataclass
class CountInfo:
    """
    Represents count information for a concept in query results.

    Attributes:
        conceptId: The concept being counted
        connectionTypeId: The type of connection being counted
        count: The count value
        connectionType: Character value of the connection type (populated after enrichment)
    """
    conceptId: int = 0
    connectionTypeId: int = 0
    count: int = 0
    connectionType: str = ""

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "conceptId": self.conceptId,
            "connectionTypeId": self.connectionTypeId,
            "count": self.count,
            "connectionType": self.connectionType,
        }


def decode_count_info(count_info_strings: List[str]) -> List[CountInfo]:
    """
    Decode count information strings into CountInfo objects.

    The count info strings come from the API in a specific format that needs
    to be parsed into structured CountInfo objects.

    Args:
        count_info_strings: List of count info strings from API response

    Returns:
        List of CountInfo objects

    Example:
        >>> strings = ["123:456:10", "789:456:5"]
        >>> infos = decode_count_info(strings)
        >>> print(infos[0].conceptId)  # 123
    """
    count_infos: List[CountInfo] = []

    for info_string in count_info_strings:
        if not info_string:
            continue

        try:
            # Parse format: "conceptId:connectionTypeId:count"
            parts = info_string.split(":")
            if len(parts) >= 3:
                count_infos.append(CountInfo(
                    conceptId=int(parts[0]),
                    connectionTypeId=int(parts[1]),
                    count=int(parts[2]),
                ))
            elif len(parts) == 2:
                # Fallback format: "conceptId:count"
                count_infos.append(CountInfo(
                    conceptId=int(parts[0]),
                    count=int(parts[1]),
                ))
        except (ValueError, IndexError):
            # Skip malformed entries
            continue

    return count_infos


async def get_connection_type_for_count(
    count_infos: List[CountInfo]
) -> Dict[int, CountInfo]:
    """
    Enrich count information with connection type names and create lookup dictionary.

    This function fetches the concept for each connectionTypeId and adds the
    characterValue as the connectionType field.

    Args:
        count_infos: List of CountInfo objects to enrich

    Returns:
        Dictionary mapping conceptId to enriched CountInfo

    Example:
        >>> count_infos = [CountInfo(conceptId=123, connectionTypeId=456, count=10)]
        >>> count_dict = await get_connection_type_for_count(count_infos)
        >>> print(count_dict[123].connectionType)  # "the_author"
    """
    from ccs.services.get.get_the_concept import GetTheConcept

    count_dictionary: Dict[int, CountInfo] = {}

    for count_info in count_infos:
        if count_info.connectionTypeId > 0:
            try:
                concept = await GetTheConcept(count_info.connectionTypeId)
                if concept and concept.id != 0:
                    count_info.connectionType = concept.characterValue
            except Exception:
                pass

        count_dictionary[count_info.conceptId] = count_info

    return count_dictionary
