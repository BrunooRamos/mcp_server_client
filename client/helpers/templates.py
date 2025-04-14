"""
Plantillas predefinidas para diferentes tipos de respuestas.
"""

# Templates para Airbnb
AIRBNB_SEARCH_TEMPLATE = {
    "type": "airbnb_search",
    "data": {
        "results": [
            {
                "id": "",
                "title": "",
                "description": "",
                "price": 0,
                "location": {
                    "latitude": 0,
                    "longitude": 0
                },
                "images": [],
                "amenities": [],
                "rating": 0,
                "reviews": 0
            }
        ],
        "total_results": 0,
        "search_params": {
            "location": "",
            "check_in": "",
            "check_out": "",
            "guests": 0
        }
    }
}

AIRBNB_LISTING_DETAILS_TEMPLATE = {
    "type": "airbnb_listing_details",
    "data": {
        "id": "",
        "title": "",
        "description": "",
        "images": [],
        "price": {
            "amount": 0,
            "currency": ""
        },
        "amenities": [],
        "host": {
            "name": "",
            "rating": 0
        },
        "location": {
            "address": "",
            "latitude": 0,
            "longitude": 0
        },
        "availability": {
            "check_in": "",
            "check_out": ""
        },
        "policies": [],
        "reviews": [
            {
                "rating": 0,
                "comment": "",
                "date": ""
            }
        ]
    }
}

# Templates para Google Maps
GOOGLE_MAPS_PLACES_TEMPLATE = {
    "type": "maps_search_places",
    "data": {
        "results": [
            {
                "name": "",
                "address": "",
                "location": {
                    "latitude": 0,
                    "longitude": 0
                },
                "types": [],
                "rating": 0,
                "user_ratings_total": 0,
                "opening_hours": {
                    "open_now": False,
                    "weekday_text": []
                }
            }
        ],
        "search_params": {
            "location": "",
            "radius": 0,
            "type": ""
        }
    }
}

GOOGLE_MAPS_DIRECTIONS_TEMPLATE = {
    "type": "maps_directions",
    "data": {
        "routes": [
            {
                "distance": {
                    "text": "",
                    "value": 0
                },
                "duration": {
                    "text": "",
                    "value": 0
                },
                "steps": [
                    {
                        "instructions": "",
                        "distance": {
                            "text": "",
                            "value": 0
                        },
                        "duration": {
                            "text": "",
                            "value": 0
                        },
                        "start_location": {
                            "latitude": 0,
                            "longitude": 0
                        },
                        "end_location": {
                            "latitude": 0,
                            "longitude": 0
                        }
                    }
                ]
            }
        ],
        "origin": "",
        "destination": "",
        "mode": ""
    }
}

# Diccionario de plantillas
TEMPLATES = {
    "airbnb_search": AIRBNB_SEARCH_TEMPLATE,
    "airbnb_listing_details": AIRBNB_LISTING_DETAILS_TEMPLATE,
    "maps_search_places": GOOGLE_MAPS_PLACES_TEMPLATE,
    "maps_directions": GOOGLE_MAPS_DIRECTIONS_TEMPLATE
} 