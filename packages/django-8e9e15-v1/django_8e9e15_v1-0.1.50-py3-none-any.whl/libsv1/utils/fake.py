class FakeUtils:
    @staticmethod
    def image_url(width=500, height=500):
        return f"https://dummyimage.com/{width}x{height}"

    @staticmethod
    def location(as_point=False):
        from django.contrib.gis.geos import Point
        import random
        location = {
            "lat": random.uniform(-90, 90),
            "lng": random.uniform(-180, 180),
        }
        if as_point:
            return Point(x=location['lng'], y=location['lat'], srid=4326)
        return location

