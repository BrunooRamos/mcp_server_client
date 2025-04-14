import { MCPServer } from '@modelcontextprotocol/sdk';
import fetch from 'node-fetch';
import { URLSearchParams } from 'url';
class GoogleMapsServer extends MCPServer {
    constructor() {
        super();
        this.apiKey = process.env.GOOGLE_MAPS_API_KEY || '';
        if (!this.apiKey) {
            throw new Error('GOOGLE_MAPS_API_KEY environment variable is required');
        }
    }
    async makeRequest(endpoint, params) {
        const searchParams = new URLSearchParams({
            ...params,
            key: this.apiKey
        });
        const url = `https://maps.googleapis.com/maps/api/${endpoint}?${searchParams}`;
        const response = await fetch(url);
        return response.json();
    }
    async maps_geocode(address) {
        const result = await this.makeRequest('geocode/json', { address });
        if (result.status !== 'OK') {
            throw new Error(`Geocoding failed: ${result.status}`);
        }
        return {
            location: result.results[0].geometry.location,
            formatted_address: result.results[0].formatted_address,
            place_id: result.results[0].place_id
        };
    }
    async maps_reverse_geocode(latitude, longitude) {
        const result = await this.makeRequest('geocode/json', {
            latlng: `${latitude},${longitude}`
        });
        if (result.status !== 'OK') {
            throw new Error(`Reverse geocoding failed: ${result.status}`);
        }
        return {
            formatted_address: result.results[0].formatted_address,
            place_id: result.results[0].place_id,
            address_components: result.results[0].address_components
        };
    }
    async maps_search_places(query, location, radius) {
        const params = { query };
        if (location && radius) {
            params.location = `${location.latitude},${location.longitude}`;
            params.radius = radius.toString();
        }
        const result = await this.makeRequest('place/textsearch/json', params);
        if (result.status !== 'OK') {
            throw new Error(`Place search failed: ${result.status}`);
        }
        return result.results.map((place) => ({
            name: place.name,
            address: place.formatted_address,
            location: place.geometry.location,
            place_id: place.place_id
        }));
    }
    async maps_place_details(place_id) {
        const result = await this.makeRequest('place/details/json', {
            place_id,
            fields: 'name,formatted_address,formatted_phone_number,website,rating,reviews,opening_hours,photos'
        });
        if (result.status !== 'OK') {
            throw new Error(`Place details failed: ${result.status}`);
        }
        return {
            name: result.result.name,
            address: result.result.formatted_address,
            phone: result.result.formatted_phone_number,
            website: result.result.website,
            rating: result.result.rating,
            reviews: result.result.reviews,
            opening_hours: result.result.opening_hours,
            photos: result.result.photos
        };
    }
    async maps_distance_matrix(origins, destinations, mode = 'driving') {
        const result = await this.makeRequest('distancematrix/json', {
            origins: origins.join('|'),
            destinations: destinations.join('|'),
            mode
        });
        if (result.status !== 'OK') {
            throw new Error(`Distance matrix failed: ${result.status}`);
        }
        return {
            origin_addresses: result.origin_addresses,
            destination_addresses: result.destination_addresses,
            rows: result.rows
        };
    }
    async maps_elevation(locations) {
        const locationsStr = locations.map(loc => `${loc.latitude},${loc.longitude}`).join('|');
        const result = await this.makeRequest('elevation/json', {
            locations: locationsStr
        });
        if (result.status !== 'OK') {
            throw new Error(`Elevation data failed: ${result.status}`);
        }
        return result.results.map((elevation) => ({
            location: elevation.location,
            elevation: elevation.elevation,
            resolution: elevation.resolution
        }));
    }
    async maps_directions(origin, destination, mode = 'driving') {
        const result = await this.makeRequest('directions/json', {
            origin,
            destination,
            mode
        });
        if (result.status !== 'OK') {
            throw new Error(`Directions failed: ${result.status}`);
        }
        const route = result.routes[0];
        return {
            summary: route.summary,
            legs: route.legs.map((leg) => ({
                distance: leg.distance,
                duration: leg.duration,
                steps: leg.steps.map((step) => ({
                    instruction: step.html_instructions,
                    distance: step.distance,
                    duration: step.duration
                }))
            }))
        };
    }
}
const server = new GoogleMapsServer();
server.run();
//# sourceMappingURL=index.js.map