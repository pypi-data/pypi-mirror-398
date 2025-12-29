"""
Place / Location Shapes

For storing geographic location data in Solid Pods.
Useful for check-ins, location history, and location-based apps.

Namespaces used:
- schema: http://schema.org/
- geo: http://www.w3.org/2003/01/geo/wgs84_pos#
- dcterms: http://purl.org/dc/terms/
"""

from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, Field

# Namespace constants
SCHEMA = "http://schema.org/"
GEO = "http://www.w3.org/2003/01/geo/wgs84_pos#"
DCTERMS = "http://purl.org/dc/terms/"
RDF = "http://www.w3.org/1999/02/22-rdf-syntax-ns#"


class Place(BaseModel):
    """
    A place or location.
    
    Can represent a physical location, venue, or point of interest.
    
    Properties:
        id: Place URI
        name: Place name
        description: Description of the place
        latitude: GPS latitude
        longitude: GPS longitude
        address: Street address
        city: City name
        country: Country name
        postal_code: Postal/ZIP code
        url: Website or more info
    
    Example:
        >>> from pyldo.shapes import Place
        >>> 
        >>> place = Place(
        ...     name="Eiffel Tower",
        ...     latitude=48.8584,
        ...     longitude=2.2945,
        ...     city="Paris",
        ...     country="France"
        ... )
    """
    
    id: Optional[str] = Field(
        default=None,
        alias="@id",
        description="Place URI"
    )
    
    type_: Optional[list[str]] = Field(
        default=None,
        alias="http://www.w3.org/1999/02/22-rdf-syntax-ns#type",
        description="RDF types (schema:Place)"
    )
    
    # Basic info
    name: Optional[str] = Field(
        default=None,
        alias="http://schema.org/name",
        description="Place name"
    )
    
    description: Optional[str] = Field(
        default=None,
        alias="http://schema.org/description",
        description="Description of the place"
    )
    
    # Coordinates
    latitude: Optional[float] = Field(
        default=None,
        alias="http://schema.org/latitude",
        description="GPS latitude"
    )
    
    longitude: Optional[float] = Field(
        default=None,
        alias="http://schema.org/longitude",
        description="GPS longitude"
    )
    
    # Alternative coordinate format (WGS84)
    lat: Optional[float] = Field(
        default=None,
        alias="http://www.w3.org/2003/01/geo/wgs84_pos#lat",
        description="WGS84 latitude"
    )
    
    long: Optional[float] = Field(
        default=None,
        alias="http://www.w3.org/2003/01/geo/wgs84_pos#long",
        description="WGS84 longitude"
    )
    
    elevation: Optional[float] = Field(
        default=None,
        alias="http://schema.org/elevation",
        description="Elevation in meters"
    )
    
    # Address components
    address: Optional[str] = Field(
        default=None,
        alias="http://schema.org/streetAddress",
        description="Street address"
    )
    
    city: Optional[str] = Field(
        default=None,
        alias="http://schema.org/addressLocality",
        description="City name"
    )
    
    region: Optional[str] = Field(
        default=None,
        alias="http://schema.org/addressRegion",
        description="State/region"
    )
    
    country: Optional[str] = Field(
        default=None,
        alias="http://schema.org/addressCountry",
        description="Country"
    )
    
    postal_code: Optional[str] = Field(
        default=None,
        alias="http://schema.org/postalCode",
        description="Postal/ZIP code"
    )
    
    # Additional info
    url: Optional[str] = Field(
        default=None,
        alias="http://schema.org/url",
        description="Website or more info"
    )
    
    telephone: Optional[str] = Field(
        default=None,
        alias="http://schema.org/telephone",
        description="Phone number"
    )
    
    # Categories
    category: Optional[str] = Field(
        default=None,
        alias="http://schema.org/category",
        description="Place category (restaurant, museum, etc.)"
    )
    
    # Photo
    photo: Optional[str] = Field(
        default=None,
        alias="http://schema.org/photo",
        description="Photo of the place"
    )

    model_config = {
        "populate_by_name": True,
        "extra": "allow",
    }


class GeoCoordinates(BaseModel):
    """
    Simple geographic coordinates.
    
    A lightweight shape for just lat/long coordinates.
    
    Properties:
        id: Coordinates URI
        latitude: GPS latitude
        longitude: GPS longitude
        accuracy: Accuracy in meters
    
    Example:
        >>> coords = GeoCoordinates(
        ...     latitude=37.7749,
        ...     longitude=-122.4194,
        ...     accuracy=10
        ... )
    """
    
    id: Optional[str] = Field(
        default=None,
        alias="@id",
        description="Coordinates URI"
    )
    
    type_: Optional[list[str]] = Field(
        default=None,
        alias="http://www.w3.org/1999/02/22-rdf-syntax-ns#type",
        description="RDF types (schema:GeoCoordinates)"
    )
    
    latitude: Optional[float] = Field(
        default=None,
        alias="http://schema.org/latitude",
        description="GPS latitude"
    )
    
    longitude: Optional[float] = Field(
        default=None,
        alias="http://schema.org/longitude",
        description="GPS longitude"
    )
    
    accuracy: Optional[float] = Field(
        default=None,
        alias="http://schema.org/geoRadius",
        description="Accuracy in meters"
    )
    
    elevation: Optional[float] = Field(
        default=None,
        alias="http://schema.org/elevation",
        description="Elevation in meters"
    )

    model_config = {
        "populate_by_name": True,
        "extra": "allow",
    }


class CheckIn(BaseModel):
    """
    A location check-in.
    
    Records when a user was at a specific place.
    
    Properties:
        id: Check-in URI
        place: The place checked into
        timestamp: When the check-in occurred
        actor: Who checked in (WebID)
        note: Optional note about the visit
    
    Example:
        >>> from pyldo.shapes import CheckIn
        >>> 
        >>> checkin = CheckIn(
        ...     place="https://pod/places/eiffel-tower",
        ...     timestamp="2024-01-15T14:30:00Z",
        ...     actor="https://alice.pod/profile/card#me",
        ...     note="Beautiful view!"
        ... )
    """
    
    id: Optional[str] = Field(
        default=None,
        alias="@id",
        description="Check-in URI"
    )
    
    type_: Optional[list[str]] = Field(
        default=None,
        alias="http://www.w3.org/1999/02/22-rdf-syntax-ns#type",
        description="RDF types"
    )
    
    place: Optional[str] = Field(
        default=None,
        alias="http://schema.org/location",
        description="The place checked into"
    )
    
    timestamp: Optional[str] = Field(
        default=None,
        alias="http://schema.org/dateCreated",
        description="When the check-in occurred"
    )
    
    actor: Optional[str] = Field(
        default=None,
        alias="http://schema.org/actor",
        description="Who checked in (WebID)"
    )
    
    note: Optional[str] = Field(
        default=None,
        alias="http://schema.org/text",
        description="Optional note about the visit"
    )
    
    # Coordinates at time of check-in
    latitude: Optional[float] = Field(
        default=None,
        alias="http://schema.org/latitude",
        description="Latitude at check-in"
    )
    
    longitude: Optional[float] = Field(
        default=None,
        alias="http://schema.org/longitude",
        description="Longitude at check-in"
    )

    model_config = {
        "populate_by_name": True,
        "extra": "allow",
    }


# Rebuild models
Place.model_rebuild()
GeoCoordinates.model_rebuild()
CheckIn.model_rebuild()
