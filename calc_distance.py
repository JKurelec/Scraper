from geopy.geocoders import Nominatim
from geopy.distance import geodesic

if __name__ == '__main__':
    # Initialize the geocoder
    geolocator = Nominatim(user_agent="distance_calculator")

    # Get the latitude and longitude for the addresses
    location1 = geolocator.geocode("Ozaljska 8, Zagreb, Croatia")
    location2 = geolocator.geocode("Nova Ves 73, Zagreb, Croatia")

    if location1 is None:
        print("Location 1 not found")
    if location2 is None:
        print("Location 2 not found")

    if location1 and location2:
        # Extract latitude and longitude
        coords_1 = (location1.latitude, location1.longitude)
        coords_2 = (location2.latitude, location2.longitude)

        # Calculate the distance
        distance = geodesic(coords_1, coords_2).kilometers

        print(f"Distance: {distance} km")
    else:
        print("Could not find one or both of the locations.")
