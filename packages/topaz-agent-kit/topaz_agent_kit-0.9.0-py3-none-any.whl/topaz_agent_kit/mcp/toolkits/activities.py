import os
from typing import Any, Dict, Optional

from fastmcp import FastMCP
from amadeus import Client, ResponseError

from topaz_agent_kit.utils.logger import Logger
from topaz_agent_kit.mcp.decorators import tool_metadata, ToolTimeout
from topaz_agent_kit.mcp.toolkits.common import CommonMCPTools

class ActivitiesMCPTools:
    def __init__(self) -> None:
        self._logger = Logger("MCP.Activities")
        self._common = CommonMCPTools()
        self._amadeus = self._common._load_amadeus_client()

    def register(self, mcp: FastMCP) -> None:

        @mcp.tool(name="activities_search")
        @tool_metadata(timeout=ToolTimeout.MEDIUM)
        def activities_search(latitude: Optional[float] = None, longitude: Optional[float] = None, radiusKm: Optional[int] = None, north: Optional[float] = None, west: Optional[float] = None, south: Optional[float] = None, east: Optional[float] = None, startDate: Optional[str] = None, endDate: Optional[str] = None, keyword: Optional[str] = None, categories: Optional[str] = None, max: Optional[int] = None, currencyCode: Optional[str] = None) -> Dict[str, Any]:
            """Search activities near a point or within a bounding box."""
            self._logger.input("activities_search INPUT: lat={} lon={} bbox=({}, {}, {}, {})", latitude, longitude, north, west, south, east)
            params: Dict[str, Any] = {}
            if latitude is not None and longitude is not None:
                params.update({"latitude": latitude, "longitude": longitude})
                # Default to a broader search radius if not provided
                if radiusKm is None:
                    radiusKm = 30
                params["radius"] = radiusKm
            elif None not in (north, west, south, east):
                params.update({"north": north, "west": west, "south": south, "east": east})
            else:
                self._logger.error("activities_search requires (latitude, longitude) or bbox north/west/south/east")
                raise RuntimeError("activities_search requires (latitude, longitude) or bbox north/west/south/east")
            if startDate:
                params["startDate"] = startDate
            if endDate:
                params["endDate"] = endDate
            if keyword:
                params["keyword"] = keyword
            if categories:
                params["category"] = categories
            if max is not None:
                params["max"] = max
            if currencyCode:
                params["currencyCode"] = currencyCode
            try:
                # SDK support for activities may vary; attempt and fallback with an error if not available
                resp = self._amadeus.shopping.activities.get(**params)  # type: ignore[attr-defined]
                data = resp.data if hasattr(resp, "data") else []
                self._logger.output("activities_search OUTPUT: count={}", len(data))
                return {"data": data}
            except AttributeError:
                self._logger.error("SDK activities_search not supported in this SDK build")
                raise RuntimeError("activities_search not supported by current Amadeus SDK build")
            except ResponseError as e:
                self._common._log_response_error("activities_search", e)
                error_details = {
                    "status_code": getattr(e, "status_code", None),
                    "description": getattr(e, "description", None),
                }
                error_msg = f"Activities search failed: {error_details.get('description', str(e))} (status: {error_details.get('status_code', 'unknown')})"
                raise RuntimeError(error_msg)

        @mcp.tool(name="activity_details")
        @tool_metadata(timeout=ToolTimeout.MEDIUM)
        def activity_details(activityId: str) -> Dict[str, Any]:
            """Get detailed information for a specific activity."""
            self._logger.input("activity_details INPUT: id={}", activityId)
            try:
                resp = self._amadeus.shopping.activity(activityId).get()  # type: ignore[attr-defined]
                data = resp.data if hasattr(resp, "data") else {}
                self._logger.output("activity_details OUTPUT: keys={}", list(data.keys()) if isinstance(data, dict) else type(data).__name__)
                return {"data": data}
            except AttributeError:
                self._logger.error("SDK activity_details not supported in this SDK build")
                raise RuntimeError("activity_details not supported by current Amadeus SDK build")
            except ResponseError as e:
                self._common._log_response_error("activity_details", e)
                error_details = {
                    "status_code": getattr(e, "status_code", None),
                    "description": getattr(e, "description", None),
                }
                error_msg = f"Activity details failed: {error_details.get('description', str(e))} (status: {error_details.get('status_code', 'unknown')})"
                raise RuntimeError(error_msg)

        @mcp.tool(name="pois_search")
        @tool_metadata(timeout=ToolTimeout.QUICK)
        def pois_search(latitude: Optional[float] = None, longitude: Optional[float] = None, radiusKm: Optional[int] = None, north: Optional[float] = None, west: Optional[float] = None, south: Optional[float] = None, east: Optional[float] = None, categories: Optional[str] = None, keywords: Optional[str] = None, max: Optional[int] = None) -> Dict[str, Any]:
            """Search Points of Interest near a point or within a bounding box."""
            self._logger.input("pois_search INPUT: lat={} lon={} bbox=({}, {}, {}, {})", latitude, longitude, north, west, south, east)
            params: Dict[str, Any] = {}
            if latitude is not None and longitude is not None:
                params.update({"latitude": latitude, "longitude": longitude})
                if radiusKm is not None:
                    params["radius"] = radiusKm
            elif None not in (north, west, south, east):
                params.update({"north": north, "west": west, "south": south, "east": east})
            else:
                self._logger.error("pois_search requires (latitude, longitude) or bbox north/west/south/east")
                raise RuntimeError("pois_search requires (latitude, longitude) or bbox north/west/south/east")
            if categories:
                params["categories"] = categories
            if keywords:
                params["keyword"] = keywords
            if max is not None:
                params["max"] = max
            try:
                resp = self._amadeus.reference_data.locations.points_of_interest.get(**params)  # type: ignore[attr-defined]
                data = resp.data if hasattr(resp, "data") else []
                self._logger.output("pois_search OUTPUT: count={}", len(data))
                return {"data": data}
            except AttributeError:
                self._logger.error("SDK pois_search not supported in this SDK build")
                raise RuntimeError("pois_search not supported by current Amadeus SDK build")
            except ResponseError as e:
                self._common._log_response_error("pois_search", e)
                error_details = {
                    "status_code": getattr(e, "status_code", None),
                    "description": getattr(e, "description", None),
                }
                error_msg = f"POIs search failed: {error_details.get('description', str(e))} (status: {error_details.get('status_code', 'unknown')})"
                raise RuntimeError(error_msg)


