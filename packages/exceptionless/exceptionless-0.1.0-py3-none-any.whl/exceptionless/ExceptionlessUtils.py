import requests

from exceptionless.ExceptionlessStatics import EXCEPTIONLESS_API_ROOT

class ExceptionlessUtils:
    @staticmethod
    def validate_api_key(api_key: str) -> bool:
        """Returns true if the Exceptionless API key is valid."""
        url = f"{EXCEPTIONLESS_API_ROOT}/projects/config"
        headers = {
            "Authorization": f"Bearer {api_key}"
        }

        try:
            response = requests.get(url, headers=headers, timeout=10)
            #print(response, response.text)
            if response.status_code == 200:
                return True
            if response.status_code == 401:
                return False
            if response.status_code == 403:
                return False
            return False
        except requests.RequestException:
            return False