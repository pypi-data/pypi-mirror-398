import os
from dotenv import load_dotenv, find_dotenv
from typing import Any, Dict, Optional

from fastmcp import FastMCP
from amadeus import Client, ResponseError

from topaz_agent_kit.utils.logger import Logger
from topaz_agent_kit.mcp.decorators import tool_metadata, ToolTimeout
from topaz_agent_kit.mcp.toolkits.common import CommonMCPTools


class FlightsMCPTools:
    def __init__(self) -> None:
        self._logger = Logger("MCP.Flights")
        self._common = CommonMCPTools()
        self._amadeus = self._common._load_amadeus_client()
    

    def register(self, mcp: FastMCP) -> None:
        
        @mcp.tool(name="flight_search")
        @tool_metadata(timeout=ToolTimeout.MEDIUM)
        def flight_search(originLocationCode: str, destinationLocationCode: str, departureDate: str, returnDate: Optional[str] = None, adults: int = 1, travelClass: Optional[str] = None, nonStop: Optional[bool] = None, max: Optional[int] = None, currencyCode: Optional[str] = None, includedCarriers: Optional[str] = None, excludedCarriers: Optional[str] = None, children: Optional[int] = None, infants: Optional[int] = None) -> Dict[str, Any]:
            """Search flight offers between two locations. Dates in YYYY-MM-DD."""
            self._logger.input("flight_search INPUT: {} -> {} on {}", originLocationCode, destinationLocationCode, departureDate)
            params: Dict[str, Any] = {
                "originLocationCode": originLocationCode,
                "destinationLocationCode": destinationLocationCode,
                "departureDate": departureDate,
                "adults": adults,
            }
            if returnDate:
                params["returnDate"] = returnDate
            if travelClass:
                params["travelClass"] = travelClass
            if nonStop is not None:
                params["nonStop"] = bool(nonStop)
            if max is not None:
                params["max"] = max
            if currencyCode:
                params["currencyCode"] = currencyCode
            if includedCarriers:
                params["includedAirlineCodes"] = includedCarriers
            if excludedCarriers:
                params["excludedAirlineCodes"] = excludedCarriers
            if children is not None:
                params["children"] = children
            if infants is not None:
                params["infants"] = infants
            try:
                resp = self._amadeus.shopping.flight_offers_search.get(**params)
                data = resp.data if hasattr(resp, "data") else []
                self._logger.output("flight_search OUTPUT: offers={}", len(data))
                return {"data": data}
            except ResponseError as e:
                self._common._log_response_error("flight_search", e)
                error_details = {
                    "status_code": getattr(e, "status_code", None),
                    "description": getattr(e, "description", None),
                }
                error_msg = f"Flight search failed: {error_details.get('description', str(e))} (status: {error_details.get('status_code', 'unknown')})"
                raise RuntimeError(error_msg)

        @mcp.tool(name="flight_price")
        @tool_metadata(timeout=ToolTimeout.MEDIUM)
        def flight_price(flightOffer: Dict[str, Any], currencyCode: Optional[str] = None) -> Dict[str, Any]:
            """Price and validate a flight offer returned from search.
            
            **Parameters:**
            - flightOffer (Dict[str, Any], REQUIRED): The COMPLETE flight offer object from flight_offers array.
              CRITICAL: Must include ALL required fields: id, type, source, itineraries, travelerPricings, validatingAirlineCodes.
              DO NOT create simplified objects - use the complete offer as-is from flight_offers.
              Example: Find the offer in flight_offers where offer.id matches flightOfferId, then pass that entire object.
            - currencyCode (str, OPTIONAL): ISO 4217 currency code (e.g., "USD", "EUR"). Defaults to offer currency if not provided.
            
            **Returns:**
            - Dict with "data" key containing the priced flight offer object with updated pricing and validation status.
              This priced offer MUST be used for flight_book (do not use original offer for booking).
            
            **Usage:**
            1. Extract flightOfferId from flight_selection
            2. Find matching offer in flight_offers array: offer = [o for o in flight_offers if o.get("id") == flightOfferId][0]
            3. Call: flight_price(flightOffer=offer, currencyCode="USD")
            4. Use the returned priced offer for flight_book
            
            **Common Errors:**
            - "Missing required fields": You passed a simplified object. Solution: Use the COMPLETE offer from flight_offers array.
            - "400 Bad Request": Offer may be expired or invalid. Solution: Re-run flight_search to get fresh offers.
            """
            self._logger.input("flight_price INPUT: offer_id={} currency={} flightOffer_keys={}", 
                              flightOffer.get("id"), currencyCode, list(flightOffer.keys()))
            self._logger.debug("flight_price INPUT flightOffer: {}", flightOffer)
            
            # Validate that flightOffer contains required fields
            required_fields = ["id", "type", "source", "itineraries", "travelerPricings", "validatingAirlineCodes"]
            missing_fields = [field for field in required_fields if field not in flightOffer]
            
            if missing_fields:
                error_msg = f"Flight offer missing required fields: {', '.join(missing_fields)}. Received fields: {list(flightOffer.keys())}. Ensure you pass the COMPLETE flight offer object from flight_offers array, not a simplified version."
                self._logger.error("flight_price validation failed: {}", error_msg)
                raise RuntimeError(error_msg)
            
            body: Dict[str, Any] = {"data": {"type": "flight-offers-pricing", "flightOffers": [flightOffer]}}
            if currencyCode:
                body["data"]["currencyCode"] = currencyCode
            self._logger.debug("flight_price REQUEST body: {}", body)
            try:
                resp = self._amadeus.shopping.flight_offers.pricing.post(body)
                priced = resp.data if hasattr(resp, "data") else {}
                self._logger.output("flight_price OUTPUT: keys={} ", list(priced.keys()) if isinstance(priced, dict) else type(priced).__name__)
                return {"data": priced}
            except ResponseError as e:
                self._common._log_response_error("flight_price", e)
                error_details = {
                    "status_code": getattr(e, "status_code", None),
                    "description": getattr(e, "description", None),
                }
                error_msg = f"Flight pricing failed: {error_details.get('description', str(e))} (status: {error_details.get('status_code', 'unknown')})"
                raise RuntimeError(error_msg)

        @mcp.tool(name="flight_seatmap")
        @tool_metadata(timeout=ToolTimeout.MEDIUM)
        def flight_seatmap(flightOffer: Optional[Dict[str, Any]] = None, offerId: Optional[str] = None) -> Dict[str, Any]:
            """Retrieve seatmaps for a priced flight offer (pass offer object or id)."""
            self._logger.input("flight_seatmap INPUT: offerId={} hasOffer={}", offerId, bool(flightOffer))
            if not flightOffer and not offerId:
                self._logger.error("seatmap requires flightOffer or offerId")
                raise RuntimeError("seatmap requires flightOffer or offerId")
            body: Dict[str, Any]
            if flightOffer:
                body = {"data": [{"type": "flight-offers", "flightOffers": [flightOffer]}]}
            else:
                body = {"data": [{"type": "flight-offers", "flightOffers": [{"id": offerId}]}]}
            try:
                resp = self._amadeus.shopping.seatmaps.post(body)
                data = resp.data if hasattr(resp, "data") else []
                self._logger.output("flight_seatmap OUTPUT: maps={}", len(data))
                return {"data": data}
            except ResponseError as e:
                self._common._log_response_error("flight_seatmap", e)
                error_details = {
                    "status_code": getattr(e, "status_code", None),
                    "description": getattr(e, "description", None),
                }
                error_msg = f"Flight seatmap failed: {error_details.get('description', str(e))} (status: {error_details.get('status_code', 'unknown')})"
                raise RuntimeError(error_msg)

        @mcp.tool(name="route_price_metrics")
        @tool_metadata(timeout=ToolTimeout.QUICK)
        def route_price_metrics(origin: str, destination: str, startDate: str, endDate: str, currencyCode: Optional[str] = None) -> Dict[str, Any]:
            """Price metrics by date between origin and destination (YYYY-MM-DD range)."""
            self._logger.input("route_price_metrics INPUT: {}-{} {}..{}", origin, destination, startDate, endDate)
            # Route price metrics may not be directly available via SDK; fallback not implemented here
            try:
                # If unsupported, raise a meaningful error for now
                raise ResponseError("Itinerary price metrics endpoint not supported by SDK in this build")
            except ResponseError as e:
                self._logger.error("SDK route_price_metrics not available: {}", e)
                raise RuntimeError(str(e))

        @mcp.tool(name="airline_lookup")
        @tool_metadata(timeout=ToolTimeout.QUICK)
        def airline_lookup(iataCodes: str) -> Dict[str, Any]:
            """Lookup airline names by IATA codes (comma-separated)."""
            self._logger.input("airline_lookup INPUT: codes={}", iataCodes)
            try:
                resp = self._amadeus.reference_data.airlines.get(airlineCodes=iataCodes)
                data = resp.data if hasattr(resp, "data") else []
                self._logger.output("airline_lookup OUTPUT: count={}", len(data))
                return {"data": data}
            except ResponseError as e:
                self._common._log_response_error("airline_lookup", e)
                error_details = {
                    "status_code": getattr(e, "status_code", None),
                    "description": getattr(e, "description", None),
                }
                error_msg = f"Airline lookup failed: {error_details.get('description', str(e))} (status: {error_details.get('status_code', 'unknown')})"
                raise RuntimeError(error_msg)



        @mcp.tool(name="flight_book")
        @tool_metadata(timeout=ToolTimeout.MEDIUM)
        def flight_book(pricedFlightOffer: Dict[str, Any], travelers: list[dict], payments: Optional[list[dict]] = None, contacts: Optional[dict] = None) -> Dict[str, Any]:
            """Book a flight order from a PRICED flight offer (must be from flight_price response).
            
            **Parameters:**
            - pricedFlightOffer (Dict[str, Any], REQUIRED): The COMPLETE priced flight offer from flight_price response.
              CRITICAL: MUST use the offer returned by flight_price, NOT the original search offer.
              The priced offer contains validated pricing and must include: id, type, source, itineraries, travelerPricings.
            - travelers (List[Dict], REQUIRED): Array of traveler objects per Amadeus schema.
              Each traveler must include: id (unique identifier), dateOfBirth (YYYY-MM-DD), 
              name {firstName, lastName}, contact {emailAddress, phones [{deviceType, countryCallingCode, number}]}, 
              documents [{documentType: "PASSPORT", number, expiryDate, issuanceCountry, nationality, holder}].
              Mark primary contact with contact {emailAddress, phones}.
            - payments (List[Dict], OPTIONAL): Payment methods. Optional in sandbox/test environment.
              If provided, each payment should include: method ("CREDIT_CARD"), cardTypeCode, cardNumber, 
              expiryDate (MMYY), cardHolderName.
            - contacts (Dict, OPTIONAL): Contact information. Optional in sandbox/test environment.
              If provided, should include: emailAddress, phones [{deviceType, countryCallingCode, number}].
            
            **Returns:**
            - Dict with "data" key containing booking confirmation with:
              - orderId: Unique booking reference
              - pnr: Passenger Name Record (booking confirmation code)
              - associatedRecords: Additional booking references
              - total: Final pricing breakdown
            
            **Usage:**
            1. First call flight_price to get priced offer
            2. Build travelers array from user_profiles matching traveler_ids
            3. Call: flight_book(pricedFlightOffer=priced_offer, travelers=travelers_array)
            4. Extract orderId and pnr from response for booking confirmation
            
            **Traveler Schema Example:**
            [
              {
                "id": "1",
                "dateOfBirth": "1990-01-15",
                "name": {"firstName": "Alex", "lastName": "Doe"},
                "contact": {
                  "emailAddress": "alex@example.com",
                  "phones": [{"deviceType": "MOBILE", "countryCallingCode": "1", "number": "5551234567"}]
                },
                "documents": [{
                  "documentType": "PASSPORT",
                  "number": "AB123456",
                  "expiryDate": "2030-12-31",
                  "issuanceCountry": "US",
                  "nationality": "US",
                  "holder": true
                }]
              }
            ]
            
            **Common Errors:**
            - "Invalid priced offer": You used original search offer instead of flight_price result. Solution: Use the offer from flight_price response.
            - "Missing traveler details": Required fields missing. Solution: Ensure all travelers have complete name, contact, documents.
            """
            self._logger.input("flight_book INPUT: offer_id={} travelers={} payments={} ", pricedFlightOffer.get("id"), (len(travelers) if isinstance(travelers, list) else type(travelers).__name__), bool(payments))
            body: Dict[str, Any] = {
                "data": {
                    "type": "flight-order",
                    "flightOffers": [pricedFlightOffer],
                    "travelers": travelers,
                }
            }
            if contacts is not None:
                body["data"]["contacts"] = contacts
            if payments is not None:
                body["data"]["payments"] = payments
            try:
                resp = self._amadeus.booking.flight_orders.post(body)
                data = resp.data if hasattr(resp, "data") else {}
                self._logger.output("flight_book OUTPUT: keys={}", list(data.keys()) if isinstance(data, dict) else type(data).__name__)
                return {"data": data}
            except ResponseError as e:
                self._common._log_response_error("flight_book", e)
                error_details = {
                    "status_code": getattr(e, "status_code", None),
                    "description": getattr(e, "description", None),
                }
                error_msg = f"Flight booking failed: {error_details.get('description', str(e))} (status: {error_details.get('status_code', 'unknown')})"
                raise RuntimeError(error_msg)

        @mcp.tool(name="flight_order_get")
        @tool_metadata(timeout=ToolTimeout.QUICK)
        def flight_order_get(orderId: str) -> Dict[str, Any]:
            """Retrieve a flight order by ID."""
            self._logger.input("flight_order_get INPUT: orderId={}", orderId)
            try:
                resp = self._amadeus.booking.flight_order(orderId).get()  # type: ignore[attr-defined]
                data = resp.data if hasattr(resp, "data") else {}
                self._logger.output("flight_order_get OUTPUT: keys={}", list(data.keys()) if isinstance(data, dict) else type(data).__name__)
                return {"data": data}
            except AttributeError:
                self._logger.error("SDK flight_order_get not supported in this SDK build")
                raise RuntimeError("flight_order_get not supported by current Amadeus SDK build")
            except ResponseError as e:
                self._common._log_response_error("flight_order_get", e)
                error_details = {
                    "status_code": getattr(e, "status_code", None),
                    "description": getattr(e, "description", None),
                }
                error_msg = f"Flight order get failed: {error_details.get('description', str(e))} (status: {error_details.get('status_code', 'unknown')})"
                raise RuntimeError(error_msg)

        @mcp.tool(name="flight_order_cancel")
        @tool_metadata(timeout=ToolTimeout.MEDIUM)
        def flight_order_cancel(orderId: str) -> Dict[str, Any]:
            """Cancel a flight order by ID (if allowed by fare rules)."""
            self._logger.input("flight_order_cancel INPUT: orderId={}", orderId)
            try:
                resp = self._amadeus.booking.flight_order(orderId).delete()  # type: ignore[attr-defined]
                data = resp.data if hasattr(resp, "data") else {}
                self._logger.output("flight_order_cancel OUTPUT: status={} keys={}", getattr(resp, "status_code", None), list(data.keys()) if isinstance(data, dict) else type(data).__name__)
                return {"data": data}
            except AttributeError:
                self._logger.error("SDK flight_order_cancel not supported in this SDK build")
                raise RuntimeError("flight_order_cancel not supported by current Amadeus SDK build")
            except ResponseError as e:
                self._common._log_response_error("flight_order_cancel", e)
                error_details = {
                    "status_code": getattr(e, "status_code", None),
                    "description": getattr(e, "description", None),
                }
                error_msg = f"Flight order cancel failed: {error_details.get('description', str(e))} (status: {error_details.get('status_code', 'unknown')})"
                raise RuntimeError(error_msg)
