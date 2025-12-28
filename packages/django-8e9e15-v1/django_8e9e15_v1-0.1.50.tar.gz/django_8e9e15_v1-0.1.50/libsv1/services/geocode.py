import os
import requests
from django.conf import settings


class GeocodeService:

    @staticmethod
    def get_autocomplete(query, language='en-GB', request=None):
        params = {
            'input': query,
            'language': language,
            'key': getattr(settings, 'GOOGLE_GEOCODE_KEY', os.getenv('GOOGLE_GEOCODE_KEY', ''))
        }

        try:
            response = requests.get('https://maps.googleapis.com/maps/api/place/autocomplete/json', params=params)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            if request is not None:
                try:
                    from libsv1.apps.global_system_log.services import GlobalSystemLogAdd
                    from libsv1.utils.base import BaseUtils
                    GlobalSystemLogAdd(request=request, additional_log={'GeocodeService': BaseUtils.log_response_error(locals().get('response'), e)})
                except Exception as e:
                    print(f"GeocodeService: {e}")

        return None

    @staticmethod
    def get_address_by_query(query, language='en-GB', request=None):
        params = {
            'address': query,
            'language': language,
            'key': getattr(settings, 'GOOGLE_GEOCODE_KEY', os.getenv('GOOGLE_GEOCODE_KEY', ''))
        }

        try:
            response = requests.get('https://maps.googleapis.com/maps/api/geocode/json', params=params)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            if request is not None:
                try:
                    from libsv1.apps.global_system_log.services import GlobalSystemLogAdd
                    from libsv1.utils.base import BaseUtils
                    GlobalSystemLogAdd(request=request, additional_log={'GeocodeService': BaseUtils.log_response_error(locals().get('response'), e)})
                except Exception as e:
                    print(f"GeocodeService: {e}")

        return None

    @staticmethod
    def get_address_by_latlng(latlng, language='en-GB', request=None):
        params = {
            'latlng': latlng,
            'language': language,
            'key': getattr(settings, 'GOOGLE_GEOCODE_KEY', os.getenv('GOOGLE_GEOCODE_KEY', ''))
        }

        try:
            response = requests.get('https://maps.googleapis.com/maps/api/geocode/json', params=params)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            if request is not None:
                try:
                    from libsv1.apps.global_system_log.services import GlobalSystemLogAdd
                    from libsv1.utils.base import BaseUtils
                    GlobalSystemLogAdd(request=request, additional_log={'GeocodeService': BaseUtils.log_response_error(locals().get('response'), e)})
                except Exception as e:
                    print(f"GeocodeService: {e}")

        return None

    @staticmethod
    def get_latlng_by_address(address, request=None):
        if not address:
            return {"lat": None, "lng": None}

        params = {
            'query': address,
            'key': getattr(settings, 'GOOGLE_GEOCODE_KEY', os.getenv('GOOGLE_GEOCODE_KEY', ''))
        }

        try:
            response = requests.get('https://maps.googleapis.com/maps/api/geocode/json', params=params)
            response.raise_for_status()
            response_data = response.json()

            if response_data.get('results'):
                location = response_data['results'][0]['geometry']['location']
                return {
                    "lat": location.get('lat'),
                    "lng": location.get('lng'),
                }
        except requests.exceptions.RequestException as e:
            if request is not None:
                try:
                    from libsv1.apps.global_system_log.services import GlobalSystemLogAdd
                    from libsv1.utils.base import BaseUtils
                    GlobalSystemLogAdd(request=request, additional_log={'GeocodeService': BaseUtils.log_response_error(locals().get('response'), e)})
                except Exception as e:
                    print(f"GeocodeService: {e}")

        return {"lat": None, "lng": None}
