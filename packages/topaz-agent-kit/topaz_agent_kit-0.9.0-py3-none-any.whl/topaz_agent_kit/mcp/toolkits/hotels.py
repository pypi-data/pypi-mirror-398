import os
from typing import Any, Dict, Optional

from fastmcp import FastMCP
from amadeus import Client, ResponseError

from topaz_agent_kit.utils.logger import Logger
from topaz_agent_kit.mcp.decorators import tool_metadata, ToolTimeout
from topaz_agent_kit.mcp.toolkits.common import CommonMCPTools

class HotelsMCPTools:
    def __init__(self) -> None:
        self._logger = Logger("MCP.Hotels")
        self._common = CommonMCPTools()
        self._amadeus = self._common._load_amadeus_client()

    def register(self, mcp: FastMCP) -> None:
        @mcp.tool(name="hotel_search")
        @tool_metadata(timeout=ToolTimeout.MEDIUM)
        def hotel_search(cityCode: Optional[str] = None, latitude: Optional[float] = None, longitude: Optional[float] = None, radiusKm: Optional[int] = None, chains: Optional[str] = None, amenities: Optional[str] = None, ratings: Optional[str] = None, checkInDate: Optional[str] = None, checkOutDate: Optional[str] = None, adults: int = 1, rooms: Optional[int] = None, currency: Optional[str] = None, page: Optional[int] = None, limit: Optional[int] = None) -> Dict[str, Any]:
            """Search hotel offers: resolve hotelIds by city or geocode, then fetch offers."""
            self._logger.input("hotel_search INPUT: cityCode={} lat={} lon={} radiusKm={} dates {}..{}", cityCode, latitude, longitude, radiusKm, checkInDate, checkOutDate)

            # Step 1: Resolve hotelIds
            hotel_ids: list[str] = []
            try:
                if cityCode:
                    r = self._amadeus.reference_data.locations.hotels.by_city.get(cityCode=cityCode)
                    hotels = getattr(r, "data", []) or []
                    for h in hotels:
                        hid = h.get("hotelId") or h.get("hotel_id") or h.get("id")
                        if hid:
                            hotel_ids.append(str(hid))
                elif latitude is not None and longitude is not None:
                    geocode_params: Dict[str, Any] = {"latitude": latitude, "longitude": longitude}
                    if radiusKm is not None:
                        geocode_params["radius"] = radiusKm
                        geocode_params["radiusUnit"] = "KM"
                    r = self._amadeus.reference_data.locations.hotels.by_geocode.get(**geocode_params)
                    hotels = getattr(r, "data", []) or []
                    for h in hotels:
                        hid = h.get("hotelId") or h.get("hotel_id") or h.get("id")
                        if hid:
                            hotel_ids.append(str(hid))
                else:
                    self._logger.error("hotel_search requires cityCode or (latitude, longitude)")
                    raise RuntimeError("hotel_search requires cityCode or (latitude, longitude)")
            except ResponseError as e:
                self._common._log_response_error("hotel_search (list)", e)
                error_details = {
                    "status_code": getattr(e, "status_code", None),
                    "description": getattr(e, "description", None),
                }
                error_msg = f"Hotel list failed: {error_details.get('description', str(e))} (status: {error_details.get('status_code', 'unknown')})"
                raise RuntimeError(error_msg)

            if not hotel_ids:
                self._logger.warning("No hotels found for the given location criteria")
                return {"data": []}

            # Cap number of IDs to avoid overly long queries
            hotel_ids = hotel_ids[:20]

            # Step 2: Fetch offers for resolved hotelIds
            offer_params: Dict[str, Any] = {
                "hotelIds": ",".join(hotel_ids),
                "adults": adults,
            }
            if checkInDate:
                offer_params["checkInDate"] = checkInDate
            if checkOutDate:
                offer_params["checkOutDate"] = checkOutDate
            if rooms is not None:
                offer_params["roomQuantity"] = rooms
            if currency:
                offer_params["currency"] = currency
            if chains:
                offer_params["chainCodes"] = chains
            if amenities:
                offer_params["amenities"] = amenities
            if ratings:
                offer_params["ratings"] = ratings
            if page is not None:
                offer_params["page[limit]"] = limit or 20
                offer_params["page[offset]"] = (page - 1) * (limit or 20)

            try:
                resp = self._amadeus.shopping.hotel_offers_search.get(**offer_params)
                data = resp.data if hasattr(resp, "data") else []
                self._logger.output("hotel_search OUTPUT: groups={}", len(data))
                return {"data": data}
            except ResponseError as e:
                self._common._log_response_error("hotel_search (offers)", e)
                error_details = {
                    "status_code": getattr(e, "status_code", None),
                    "description": getattr(e, "description", None),
                }
                error_msg = f"Hotel offers search failed: {error_details.get('description', str(e))} (status: {error_details.get('status_code', 'unknown')})"
                raise RuntimeError(error_msg)

        @mcp.tool(name="hotel_offers")
        @tool_metadata(timeout=ToolTimeout.MEDIUM)
        def hotel_offers(hotelIds: Optional[str] = None, cityCode: Optional[str] = None, latitude: Optional[float] = None, longitude: Optional[float] = None, radiusKm: Optional[int] = None, checkInDate: Optional[str] = None, checkOutDate: Optional[str] = None, adults: int = 1, rooms: Optional[int] = None, currency: Optional[str] = None) -> Dict[str, Any]:
            """Get hotel offers. If hotelIds not provided, resolve by city or geocode first."""
            self._logger.input("hotel_offers INPUT: hotelIds={} cityCode={} dates {}..{}", hotelIds, cityCode, checkInDate, checkOutDate)

            resolved_ids: list[str] = []
            if hotelIds:
                resolved_ids = [s for s in str(hotelIds).split(",") if s.strip()]
            else:
                try:
                    if cityCode:
                        r = self._amadeus.reference_data.locations.hotels.by_city.get(cityCode=cityCode)
                        hotels = getattr(r, "data", []) or []
                        for h in hotels:
                            hid = h.get("hotelId") or h.get("hotel_id") or h.get("id")
                            if hid:
                                resolved_ids.append(str(hid))
                    elif latitude is not None and longitude is not None:
                        geocode_params: Dict[str, Any] = {"latitude": latitude, "longitude": longitude}
                        if radiusKm is not None:
                            geocode_params["radius"] = radiusKm
                            geocode_params["radiusUnit"] = "KM"
                        r = self._amadeus.reference_data.locations.hotels.by_geocode.get(**geocode_params)
                        hotels = getattr(r, "data", []) or []
                        for h in hotels:
                            hid = h.get("hotelId") or h.get("hotel_id") or h.get("id")
                            if hid:
                                resolved_ids.append(str(hid))
                    else:
                        self._logger.error("hotel_offers requires hotelIds or (cityCode | latitude/longitude)")
                        raise RuntimeError("hotel_offers requires hotelIds or (cityCode | latitude/longitude)")
                except ResponseError as e:
                    self._common._log_response_error("hotel_offers (list)", e)
                    error_details = {
                        "status_code": getattr(e, "status_code", None),
                        "description": getattr(e, "description", None),
                    }
                    error_msg = f"Hotel list failed: {error_details.get('description', str(e))} (status: {error_details.get('status_code', 'unknown')})"
                    raise RuntimeError(error_msg)

            if not resolved_ids:
                self._logger.warning("No hotels found for the given inputs")
                return {"data": []}

            resolved_ids = resolved_ids[:20]
            params: Dict[str, Any] = {
                "hotelIds": ",".join(resolved_ids),
                "adults": adults,
            }
            if checkInDate:
                params["checkInDate"] = checkInDate
            if checkOutDate:
                params["checkOutDate"] = checkOutDate
            if rooms is not None:
                params["roomQuantity"] = rooms
            if currency:
                params["currency"] = currency
            try:
                resp = self._amadeus.shopping.hotel_offers_search.get(**params)
                data = resp.data if hasattr(resp, "data") else []
                self._logger.output("hotel_offers OUTPUT: groups={}", len(data))
                return {"data": data}
            except ResponseError as e:
                self._common._log_response_error("hotel_offers", e)
                error_details = {
                    "status_code": getattr(e, "status_code", None),
                    "description": getattr(e, "description", None),
                }
                error_msg = f"Hotel offers failed: {error_details.get('description', str(e))} (status: {error_details.get('status_code', 'unknown')})"
                raise RuntimeError(error_msg)

        @mcp.tool(name="hotel_offer_details")
        @tool_metadata(timeout=ToolTimeout.MEDIUM)
        def hotel_offer_details(offerId: str) -> Dict[str, Any]:
            """Get detailed information for a specific hotel offer by offerId.
            
            **Parameters:**
            - offerId (str, REQUIRED): The unique offer ID from hotel_offers search results.
              Extract this from hotel_selection or hotel_offers array.
            
            **Returns:**
            - Dict with "data" key containing the detailed hotel offer with:
              - offerId: The offer identifier
              - hotel: Hotel details (name, address, amenities, etc.)
              - rooms: Room configurations and pricing
              - policies: Cancellation and booking policies
              - price: Pricing breakdown
            
            **Usage:**
            1. Extract offerId from hotel_selection (string ID)
            2. Call: hotel_offer_details(offerId="HOTEL_OFFER_ID")
            3. Use returned offer details for hotel_book
            
            **Common Errors:**
            - "404 Not Found": Offer may be expired or invalid. Solution: Re-run hotel_search to get fresh offers.
            - "Invalid offerId": Wrong format. Solution: Use exact offerId string from hotel_offers array.
            """
            self._logger.input("hotel_offer_details INPUT: offerId={}", offerId)
            try:
                # Some SDK versions expose hotel_offer directly; otherwise fallback to same search filtered by offerId
                resp = self._amadeus.shopping.hotel_offer(offerId).get()  # type: ignore[attr-defined]
                data = resp.data if hasattr(resp, "data") else {}
                self._logger.output("hotel_offer_details OUTPUT: keys={}", list(data.keys()) if isinstance(data, dict) else type(data).__name__)
                return {"data": data}
            except AttributeError:
                # Fallback: not supported by SDK build
                self._logger.error("SDK hotel_offer_details not supported in this SDK build")
                raise RuntimeError("hotel_offer_details not supported by current Amadeus SDK build")
            except ResponseError as e:
                self._common._log_response_error("hotel_offer_details", e)
                error_details = {
                    "status_code": getattr(e, "status_code", None),
                    "description": getattr(e, "description", None),
                }
                error_msg = f"Hotel offer details failed: {error_details.get('description', str(e))} (status: {error_details.get('status_code', 'unknown')})"
                raise RuntimeError(error_msg)

        @mcp.tool(name="hotel_book")
        @tool_metadata(timeout=ToolTimeout.MEDIUM)
        def hotel_book(offerId: str, guests: list[dict], payments: Optional[list[dict]] = None, contacts: Optional[dict] = None) -> Dict[str, Any]:
            """Book a hotel offer by offerId (must revalidate with hotel_offer_details first).
            
            **Parameters:**
            - offerId (str, REQUIRED): The unique offer ID from hotel_offers search results.
              Extract this from hotel_selection or from hotel_offer_details response.
            - guests (List[Dict], REQUIRED): Array of guest objects per Amadeus schema.
              Each guest should include: name {title?, firstName, lastName}, contact {emailAddress, phone {deviceType, countryCallingCode, number}}.
              Typically one guest object per room, with primary guest marked.
            - payments (List[Dict], OPTIONAL): Payment methods. Optional in sandbox/test environment.
              If provided, each payment should include: method ("CREDIT_CARD"), cardTypeCode, cardNumber, 
              expiryDate (MMYY), cardHolderName.
            - contacts (Dict, OPTIONAL): Contact information for booking. Optional in sandbox/test environment.
              If provided, should include: emailAddress, phone {deviceType, countryCallingCode, number}.
            
            **Returns:**
            - Dict with "data" key containing booking confirmation with:
              - bookingId: Unique booking reference
              - confirmation: Booking confirmation code
              - associatedRecords: Additional booking references
              - total: Final pricing breakdown
            
            **Usage:**
            1. First call hotel_offer_details(offerId) to revalidate offer
            2. Build guests array from user_profiles matching traveler_ids (convert travelers to guests format)
            3. Call: hotel_book(offerId="HOTEL_OFFER_ID", guests=guests_array)
            4. Extract bookingId and confirmation from response
            
            **Guest Schema Example:**
            [
              {
                "name": {"firstName": "Alex", "lastName": "Doe"},
                "contact": {
                  "emailAddress": "alex@example.com",
                  "phone": {"deviceType": "MOBILE", "countryCallingCode": "1", "number": "5551234567"}
                }
              }
            ]
            
            **Common Errors:**
            - "Offer not found": Offer expired or invalid. Solution: Re-validate with hotel_offer_details or re-run hotel_search.
            - "Missing guest details": Required fields missing. Solution: Ensure all guests have complete name and contact information.
            """
            self._logger.input("hotel_book INPUT: offerId={} guests={} payments={}", offerId, (len(guests) if isinstance(guests, list) else type(guests).__name__), bool(payments))
            body: Dict[str, Any] = {
                "data": [
                    {
                        "offerId": offerId,
                        "guests": guests,
                    }
                ]
            }
            if contacts is not None:
                body["data"][0]["contacts"] = contacts
            if payments is not None:
                body["data"][0]["payments"] = payments
            try:
                resp = self._amadeus.booking.hotel_bookings.post(body)
                data = resp.data if hasattr(resp, "data") else {}
                self._logger.output("hotel_book OUTPUT: keys={}", list(data.keys()) if isinstance(data, dict) else type(data).__name__)
                return {"data": data}
            except ResponseError as e:
                self._common._log_response_error("hotel_book", e)
                error_details = {
                    "status_code": getattr(e, "status_code", None),
                    "description": getattr(e, "description", None),
                }
                error_msg = f"Hotel booking failed: {error_details.get('description', str(e))} (status: {error_details.get('status_code', 'unknown')})"
                raise RuntimeError(error_msg)
