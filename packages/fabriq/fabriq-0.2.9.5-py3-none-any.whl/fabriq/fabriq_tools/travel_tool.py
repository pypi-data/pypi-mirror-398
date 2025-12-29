import re
from amadeus import Client, ResponseError
import os
from typing import List
from datetime import datetime as dt
import pandas as pd


class TravelTool:
    def __init__(self):
        """Initialize the travel tool with an LLM model."""
        self.client = Client(
            client_id=os.getenv("AMADEUS_CLIENT_ID", ""),
            client_secret=os.getenv("AMADEUS_CLIENT_SECRET", ""),
        )
        if not self.client:
            raise ValueError("Pls check your amadeus credentials.")
        self.description = "A tool for retrieving flight offers, availability, and status using the Amadeus API."

    def parse_duration(self, duration_str: str = ""):
        match = re.match(r"PT(?:(\d+)H)?(?:(\d+)M)?", duration_str)
        if not match:
            return "Invalid format"
        hours = int(match.group(1)) if match.group(1) else 0
        minutes = int(match.group(2)) if match.group(2) else 0
        parts = []
        if hours:
            parts.append(f"{hours} hour{'s' if hours != 1 else ''}")
        if minutes:
            parts.append(f"{minutes} minute{'s' if minutes != 1 else ''}")
        return " ".join(parts) if parts else "0 minutes"

    def get_offer_output(self, response, latestDeparture):
        """
        Parses the Amadeus flight offers response into a list of dicts with clean fields.
        Filters out flights departing after latestDeparture.
        """
        output = []
        if response is not None:
            carriers = response.result.get("dictionaries", {}).get("carriers", {})
            currencies = response.result.get("dictionaries", {}).get("currencies", {})
            aircraft = response.result.get("dictionaries", {}).get("aircraft", {})
            for offer in response.data:
                price_info = offer.get("price", {})
                for itinerary in offer.get("itineraries", []):
                    segments = []
                    for segment in itinerary.get("segments", []):
                        dep = segment.get("departure", {})
                        arr = segment.get("arrival", {})
                        carrier_code = segment.get("carrierCode")
                        flight_number = segment.get("number")
                        aircraft_code = segment.get("aircraft", {}).get("code")
                        duration = segment.get("duration", itinerary.get("duration"))
                        segment_dict = {
                            "source": dep.get("iataCode"),
                            "destination": arr.get("iataCode"),
                            "departure_time": dep.get("at"),
                            "arrival_time": arr.get("at"),
                            "departure_terminal": dep.get("terminal"),
                            "arrival_terminal": arr.get("terminal"),
                            "duration": self.parse_duration(duration),
                            "airline_name": carriers.get(carrier_code, carrier_code),
                            "flight_number": flight_number,
                            "carrier_code": carrier_code,
                            "aircraft_code": aircraft.get(aircraft_code, aircraft_code),
                        }
                        segments.append(segment_dict)
                    # Only include if at least one segment
                    if segments:
                        first_dep_time = segments[0].get("departure_time")
                        if first_dep_time:
                            try:
                                offer_departure = dt.strptime(
                                    first_dep_time, "%Y-%m-%dT%H:%M:%S"
                                )
                                if offer_departure > latestDeparture:
                                    continue
                            except Exception:
                                pass
                        output.append(
                            {
                                "price_total": price_info.get("total"),
                                "price_currency": currencies.get(
                                    price_info.get("currency"),
                                    price_info.get("currency"),
                                ),
                                "number_of_stops": len(segments) - 1,
                                "segments": segments,
                            }
                        )
        return output

    def get_avail_output(self, response):
        parsed = []
        for item in response.data:
            segments = item.get("segments", [])
            duration = item.get("duration")
            # For each segment in the flight (could be multi-leg)
            for seg in segments:
                dep = seg.get("departure", {})
                arr = seg.get("arrival", {})
                # Sum all bookable seats across classes for this segment
                bookable_seats = sum(
                    cls.get("numberOfBookableSeats", 0)
                    for cls in seg.get("availabilityClasses", [])
                )
                parsed.append(
                    {
                        "source": dep.get("iataCode"),
                        "destination": arr.get("iataCode"),
                        "departure_time": dep.get("at"),
                        "arrival_time": arr.get("at"),
                        "departure_terminal": dep.get("terminal"),
                        "arrival_terminal": arr.get("terminal"),
                        "number_of_stops": item.get("segments")
                        and len(item["segments"]) - 1,
                        "duration": self.parse_duration(duration),
                        "airline_name": seg.get("carrierCode"),
                        "flight_number": seg.get("number"),
                        "carrier_code": item.get("source"),
                        "aircraft_code": seg.get("aircraft", {}).get("code"),
                        "bookable_seats": bookable_seats,
                    }
                )
        return parsed

    def get_flight_offers(
        self,
        source: str = None,
        destination: str = None,
        adults: int = None,
        departureDateTimeLatest: str = None,
        currencyCode: str = "INR",
        maxOffers: int = 10,
    ):
        if source and destination and departureDateTimeLatest and adults:
            latestDeparture = dt.strptime(departureDateTimeLatest, "%Y-%m-%dT%H:%M:%S")
            try:
                body = dict(
                    originDestinations=[
                        {
                            "id": idx + 1,
                            "originLocationCode": orig,
                            "destinationLocationCode": dest,
                            "departureDateTimeRange": {
                                "date": latestDeparture.strftime("%Y-%m-%d"),
                                # "time": latestDeparture.strftime("%H:%M:%S")
                            },
                        }
                        for idx, (orig, dest) in enumerate(zip(source, destination))
                    ],
                    travelers=[
                        {"id": idx + 1, "travelerType": "ADULT"}
                        for idx in range(adults)
                    ],
                    sources=["GDS"],
                    currencyCode=currencyCode,
                    searchCriteria={"maxFlightOffers": maxOffers},
                )

                response = self.client.shopping.flight_offers_search.post(body)
                offers = self.get_offer_output(response, latestDeparture)[:maxOffers]
                # Flatten the first segment's info to top-level keys
                flattened_offers = []
                for offer in offers:
                    if offer["segments"]:
                        first_segment = offer["segments"][0]
                        flat_offer = {
                            "price_total": offer.get("price_total"),
                            "price_currency": offer.get("price_currency"),
                            "number_of_stops": offer.get("number_of_stops"),
                            "source": first_segment.get("source"),
                            "destination": first_segment.get("destination"),
                            "departure_time": first_segment.get("departure_time"),
                            "arrival_time": first_segment.get("arrival_time"),
                            "departure_terminal": first_segment.get(
                                "departure_terminal"
                            ),
                            "arrival_terminal": first_segment.get("arrival_terminal"),
                            "duration": first_segment.get("duration"),
                            "airline_name": first_segment.get("airline_name"),
                            "flight_number": first_segment.get("flight_number"),
                            "carrier_code": first_segment.get("carrier_code"),
                            "aircraft_code": first_segment.get("aircraft_code"),
                        }
                        flattened_offers.append(flat_offer)
                return pd.DataFrame(flattened_offers)
            except Exception as e:
                print(f"API error: {e}")
                import traceback

                print(traceback.format_exc())
                return None
        else:
            print(
                "Missing one or more required parameters: source, destination, departure, or adults."
            )
            return None

    def get_flight_availability(
        self,
        source: List[str] = None,
        destination: List[str] = None,
        adults: int = None,
        departureDateTimeLatest: str = None,
        directFlight: bool = True,
        currencyCode: str = "INR",
        numResults: int = 10,
    ):
        if source and destination and departureDateTimeLatest and adults:
            latestDeparture = dt.strptime(departureDateTimeLatest, "%Y-%m-%dT%H:%M:%S")
            body = dict(
                originDestinations=[
                    {
                        "id": idx + 1,
                        "originLocationCode": orig,
                        "destinationLocationCode": dest,
                        "departureDateTime": {
                            "date": latestDeparture.strftime("%Y-%m-%d"),
                            "time": latestDeparture.strftime("%H:%M:%S"),
                        },
                    }
                    for idx, (orig, dest) in enumerate(zip(source, destination))
                ],
                travelers=[
                    {"id": idx + 1, "travelerType": "ADULT"} for idx in range(adults)
                ],
                sources=["GDS"],
                nonStop=directFlight,
                currencyCode=currencyCode,
            )
            try:
                response = self.client.shopping.availability.flight_availabilities.post(
                    body=body
                )

                output = self.get_avail_output(response)[:numResults]
                return pd.DataFrame(output)

            except ResponseError as error:
                print(f"API error: {error}")
                return None
        else:
            print(
                "Missing one or more required parameters: source, destination, departure, or adults."
            )
            return None

    def get_flight_status(self, flight_number: str = None, departure: str = None):
        """
        Returns flight status of a given flight
        """
        carrierCode = flight_number[:2]
        flightNumber = flight_number[3:]
        if len(carrierCode) != 2 and not carrierCode.isalpha():
            raise ValueError("Invalid Flight Number.")

        if len(flightNumber) != 4 and not flightNumber.isnumeric():
            raise ValueError("Invalid Flight Number.")
        try:
            response = self.client.schedule.flights.get(
                carrierCode=carrierCode,
                flightNumber=flightNumber,
                scheduledDepartureDate=departure,
            )
            # Parse response to extract required fields and return as pandas DataFrame

            rows = []
            for flight in response.data:
                dep_date = flight.get("scheduledDepartureDate")
                carrier_code = flight.get("flightDesignator", {}).get("carrierCode")
                flight_number = flight.get("flightDesignator", {}).get("flightNumber")
                # Get departure and arrival timings
                dep_time = None
                arr_time = None
                flight_points = flight.get("flightPoints", [])
                if len(flight_points) > 0:
                    dep_timings = (
                        flight_points[0].get("departure", {}).get("timings", [])
                    )
                    for t in dep_timings:
                        if t.get("qualifier") == "STD":
                            dep_time = t.get("value")
                            break
                if len(flight_points) > 1:
                    arr_timings = flight_points[1].get("arrival", {}).get("timings", [])
                    for t in arr_timings:
                        if t.get("qualifier") == "STA":
                            arr_time = t.get("value")
                            break
                # Get duration from segments or legs
                duration = None
                if flight.get("segments"):
                    duration = flight["segments"][0].get("scheduledSegmentDuration")
                elif flight.get("legs"):
                    duration = flight["legs"][0].get("scheduledLegDuration")
                rows.append(
                    {
                        "departure_date": dep_date,
                        "carrier_code": carrier_code,
                        "flight_number": flight_number,
                        "departure_time": dep_time,
                        "arrival_time": arr_time,
                        "duration": self.parse_duration(duration),
                    }
                )
            return pd.DataFrame(rows)
        except ResponseError as error:
            print(f"API error: {error}")
            return None

    def run(self, info_type: str, **kwargs):
        """
        Runs the appropriate method based on info_type.
        info_type: 'offers', 'availability', or 'status'
        kwargs: parameters required by the respective methods
        """
        if info_type == "offers":
            return self.get_flight_offers(
                source=kwargs.get("source"),
                destination=kwargs.get("destination"),
                adults=kwargs.get("adults"),
                departureDateTimeLatest=kwargs.get("departureDateTimeLatest"),
                currencyCode=kwargs.get("currencyCode", "INR"),
                maxOffers=kwargs.get("maxOffers", 10),
            )
        elif info_type == "availability":
            return self.get_flight_availability(
                source=kwargs.get("source"),
                destination=kwargs.get("destination"),
                adults=kwargs.get("adults"),
                departureDateTimeLatest=kwargs.get("departureDateTimeLatest"),
                directFlight=kwargs.get("directFlight", True),
                currencyCode=kwargs.get("currencyCode", "INR"),
                numResults=kwargs.get("numResults", 10),
            )
        elif info_type == "status":
            return self.get_flight_status(
                flight_number=kwargs.get("flight_number"),
                departure=kwargs.get("departure"),
            )
        else:
            raise ValueError(
                f"Unknown info_type: {info_type}. Possible values are: 'offers', 'availability', 'status'."
            )
