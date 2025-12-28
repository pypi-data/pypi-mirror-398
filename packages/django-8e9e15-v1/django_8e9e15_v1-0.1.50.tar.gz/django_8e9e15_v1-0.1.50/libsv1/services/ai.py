import requests
from django.conf import settings
import asyncio
from libsv1.utils.string import StringUtils


class AiService:
    @staticmethod
    def gpt_send_request(prompt, api_key=settings.OPENAI_API_KEY, model='gpt-4.1', timeout=900, result_as_text=False):

        # openai.api_key = settings.OPENAI_API_KEY
        # response = openai.chat.completions.create(
        #     model="gpt-4o",
        #     messages=[{
        #         "role": "user",
        #         "content": prompt
        #     }],
        # )
        # content = response.choices[0].message.content

        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {api_key}',
        }
        payload = {
            # "model": "gpt-4o",
            # "model": "gpt-4.1-nano",
            # "model": "gpt-3.5-turbo",
            "model": model,
            "max_tokens": 32768,
            "temperature": 0.0,
            "top_p": 1.0,
            "messages": [
                {
                    "role": "system",
                    "content": "You are a helpful assistant that outputs only valid JSON."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            "response_format": {
                "type": "json_object"
            },
        }

        # print(prompt)
        # exit()


        try:
            response = requests.request(
                method='POST',
                url="https://api.openai.com/v1/chat/completions",
                json=payload,
                headers=headers,
                timeout=timeout
            )

            # print(' ')
            # print('GLOBAL ERROR', response)
            # print('URL:', response.url)
            # print('REASON:', response.reason)
            # print('REQUEST BODY:', response.request.body)
            # print('JSON:', response.json())
            # print(' ')
        except Exception as e:
            raise Exception(f'requests.request | Exception: {str(e)}') from e

        try:
            response.raise_for_status()
        except Exception as e:
            raise Exception(f'raise_for_status | Exception: {str(e)}') from e

        try:
            response = response.json()
        except Exception as e:
            raise Exception(f'response.json | Exception: {str(e)}') from e

        try:
            text = response['choices'][0]['message']['content']
        except Exception as e:
            raise Exception(f'message.content | Exception: {str(e)}') from e

        if result_as_text:
            return text

        try:
            return StringUtils.parse_json_from_string(text)
        except Exception as e:
            raise Exception(f'parse json | Exception: {str(e)}') from e

    @staticmethod
    async def async_gpt_send_request(prompt, api_key=None, model=None, timeout=None):
        return await asyncio.to_thread(AiService.gpt_send_request, prompt, api_key, model, timeout)

    @staticmethod
    def gpt_send_multi_request(prompt, api_key=None, model=None, timeout=None, count=2):
        async def async_tasks(prompt, api_key, model, timeout, count):
            tasks = []
            for i in range(count):
                tasks.append(AiService.async_gpt_send_request(prompt, api_key, model, timeout))
            return await asyncio.gather(*tasks)
        return asyncio.run(async_tasks(prompt, api_key, model, timeout, count))

    # ---------------------------------------------------------

    @staticmethod
    def gemini_send_request(prompt, api_key, model='gemini-2.5-pro', timeout=40):

        headers = {
            'Content-Type': 'application/json',
            'x-goog-api-key': api_key,
        }
        payload = {
            "contents": [{
                "parts": [{"text": prompt}]
            }],
            "generationConfig": {
                # "response_mime_type": "application/json", # not use by default !!! or use without params only
                "temperature": 0.2,
            }
        }

        try:
            response = requests.request(
                method='POST',
                url=f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent",
                # url="https://generativelanguage.googleapis.com/v1/models/gemini-2.5-pro:generateContent",
                json=payload,
                headers=headers,
                timeout=timeout
            )

            # print(' ')
            # print('GLOBAL ERROR', response)
            # print('URL:', response.url)
            # print('REASON:', response.reason)
            # print('REQUEST BODY:', response.request.body)
            # print('JSON:', response.json())
            # print(' ')
        except Exception as e:
            raise Exception(f'requests.request | Exception: {str(e)}') from e

        try:
            response.raise_for_status()
        except Exception as e:
            raise Exception(f'raise_for_status | Exception: {str(e)}') from e

        try:
            response = response.json()
        except Exception as e:
            raise Exception(f'response.json | Exception: {str(e)}') from e

        if 'error' in response:
            error_details = response['error']
            raise Exception(f'response api | Error: {error_details.get('message')}')

        try:
            text = response['candidates'][0]['content']['parts'][0]['text']
        except Exception as e:
            raise Exception(f'response->text | Error: {str(e)}') from e

        return text
