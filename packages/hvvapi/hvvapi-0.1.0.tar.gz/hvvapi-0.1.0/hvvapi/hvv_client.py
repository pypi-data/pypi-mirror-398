import hmac
import hashlib
import base64
import json
import requests
from typing import Dict, Any, Optional


class HVVClient:
    """Client for the HVV Geofox GTI API"""
    
    BASE_URL = "http://gti.geofox.de"
    
    def __init__(self, username: str, password: str):
        self.username = username
        self.password = password
        
    def _create_signature(self, body: str) -> str:
        """Create HMAC-SHA1 signature for authentication"""
        key = self.password.encode('utf-8')
        message = body.encode('utf-8')
        signature = hmac.new(key, message, hashlib.sha1).digest()
        return base64.b64encode(signature).decode('utf-8')
    
    def _make_request(self, endpoint: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Make authenticated request to the API"""
        url = f"{self.BASE_URL}{endpoint}"
        body = json.dumps(data)
        signature = self._create_signature(body)
        
        headers = {
            'Content-Type': 'application/json;charset=UTF-8',
            'Accept': 'application/json',
            'geofox-auth-type': 'HmacSHA1',
            'geofox-auth-user': self.username,
            'geofox-auth-signature': signature,
        }
        
        response = requests.post(url, data=body, headers=headers)
        response.raise_for_status()
        return response.json()
    
    def init(self) -> Dict[str, Any]:
        """Get system information"""
        return self._make_request('/gti/public/init', {})
    
    def check_name(self, name: str, type_: str = "STATION", max_list: int = 10) -> Dict[str, Any]:
        """Find stations, addresses or POIs"""
        data = {
            "theName": {
                "name": name,
                "type": type_
            },
            "maxList": max_list,
            "coordinateType": "EPSG_4326"
        }
        return self._make_request('/gti/public/checkName', data)
    
    def get_route(self, start: Dict[str, Any], dest: Dict[str, Any], 
                  time: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
        """Get route between two locations"""
        data = {
            "start": start,
            "dest": dest,
            "version": 63,
            "filterType": "HVV_LISTED"
        }
        if time:
            data["time"] = time
        return self._make_request('/gti/public/getRoute', data)
    
    def departure_list(self, station: Dict[str, Any], max_list: int = 10, 
                      time: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
        """Get departure list for a station"""
        data = {
            "station": {
                "id": station.get("id"),
                "type": station.get("type")
            },
            "time": time or {"date": "heute", "time": "jetzt"},
            "maxList": max_list,
            "version": 63,
            "filterType": "HVV_LISTED"
        }
        return self._make_request('/gti/public/departureList', data)
    
    def departure_course(self, departure_id: str) -> Dict[str, Any]:
        """Get course of a departure"""
        data = {
            "id": departure_id,
            "version": 63
        }
        return self._make_request('/gti/public/departureCourse', data)
    
    def list_stations(self, data_id: Optional[str] = None) -> Dict[str, Any]:
        """List all stations"""
        data = {
            "version": 63,
            "filterType": "HVV_LISTED"
        }
        if data_id:
            data["dataId"] = data_id
        return self._make_request('/gti/public/listStations', data)
    
    def list_lines(self, data_id: Optional[str] = None) -> Dict[str, Any]:
        """List all lines"""
        data = {
            "version": 63,
            "filterType": "HVV_LISTED"
        }
        if data_id:
            data["dataId"] = data_id
        return self._make_request('/gti/public/listLines', data)
    
    def get_announcements(self) -> Dict[str, Any]:
        """Get current announcements"""
        data = {
            "version": 63,
            "filterType": "HVV_LISTED"
        }
        return self._make_request('/gti/public/getAnnouncements', data)
    
    def check_postal_code(self, postal_code: str) -> Dict[str, Any]:
        """Check if postal code is in HVV area"""
        data = {
            "postalCode": postal_code,
            "version": 63
        }
        return self._make_request('/gti/public/checkPostalCode', data)
    
    def get_station_information(self, station: Dict[str, Any]) -> Dict[str, Any]:
        """Get additional station information"""
        data = {
            "station": station,
            "version": 63
        }
        return self._make_request('/gti/public/getStationInformation', data)
    
    def tariff_meta_data(self) -> Dict[str, Any]:
        """Get tariff metadata"""
        data = {
            "version": 63,
            "filterType": "HVV_LISTED"
        }
        return self._make_request('/gti/public/tariffMetaData', data)
    
    def tariff_zone_neighbours(self) -> Dict[str, Any]:
        """Get tariff zone neighbours"""
        data = {
            "version": 63,
            "filterType": "HVV_LISTED"
        }
        return self._make_request('/gti/public/tariffZoneNeighbours', data)
    
    def ticket_list(self) -> Dict[str, Any]:
        """Get list of available tickets"""
        data = {
            "version": 63,
            "filterType": "HVV_LISTED"
        }
        return self._make_request('/gti/public/ticketList', data)
    
    def get_vehicle_map(self, bbox: Dict[str, float]) -> Dict[str, Any]:
        """Get vehicle positions in bounding box"""
        data = {
            "boundingBox": bbox,
            "version": 63,
            "filterType": "HVV_LISTED"
        }
        return self._make_request('/gti/public/getVehicleMap', data)
