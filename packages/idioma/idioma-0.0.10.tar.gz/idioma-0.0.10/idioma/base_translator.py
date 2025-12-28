# -*- coding: utf-8 -*-
"""
A Translation module.

You can translate text using this module.
"""
import json
import random
import typing
from abc import ABC, abstractmethod

import httpcore
import httpx
from httpx import Timeout

from idioma import utils
from idioma.constants import (
    DEFAULT_CLIENT_SERVICE_URLS,
    DEFAULT_FALLBACK_SERVICE_URLS,
    DEFAULT_USER_AGENT, LANGCODES, LANGUAGES, SPECIAL_CASES,
    DEFAULT_RAISE_EXCEPTION, DUMMY_DATA
)
from idioma.exceptions import EmptyTranslationData
from idioma.gtoken import TokenAcquirer
from idioma.models import Translated, Detected, TranslatedPart
from idioma.retry_transport import RetryTransport


class BaseTranslator(ABC):
    EXCLUDES = ('en', 'ca', 'fr')
    RPC_ID = 'MkEWBc'
    POST_PARAMS = {
        'rpcids': RPC_ID,
        'bl': 'boq_translate-webserver_20201207.13_p0',
        'soc-app': 1,
        'soc-platform': 1,
        'soc-device': 1,
        'rt': 'c',
    }
    """Google Translate ajax API implementation class

    You have to create an instance of Translator to use this API

    :param service_urls: google translate url list. URLs will be used randomly.
                         For example ``['translate.google.com', 'translate.google.co.kr']``
                         To preferably use the non webapp api, service url should be translate.googleapis.com
    :type service_urls: a sequence of strings

    :param user_agent: the User-Agent header to send when making requests.
    :type user_agent: :class:`str`

    :param proxies: proxies configuration.
                    Dictionary mapping protocol or protocol and host to the URL of the proxy
                    For example ``{'http': 'foo.bar:3128', 'http://host.name': 'foo.bar:4012'}``
    :type proxies: dictionary

    :param timeout: Definition of timeout for httpx library.
                    Will be used for every request.
    :type timeout: number or a double of numbers
    :param proxies: proxies configuration.
                    Dictionary mapping protocol or protocol and host to the URL of the proxy
                    For example ``{'http': 'foo.bar:3128', 'http://host.name': 'foo.bar:4012'}``
    :param raise_exception: if `True` then raise exception if smth will go wrong
    :param http2: whether to use HTTP2 (default: True)
    :param use_fallback: use a fallback method
    :type raise_exception: boolean
    """

    def __init__(self, service_urls=DEFAULT_CLIENT_SERVICE_URLS,
                 user_agent=DEFAULT_USER_AGENT,
                 raise_exception=DEFAULT_RAISE_EXCEPTION,
                 proxies: typing.Dict[str, httpcore.AsyncHTTPProxy] = None,
                 timeout: Timeout = 30,
                 http2=True,
                 use_fallback=False,
                 lazy_client: bool = False):

        # for aenter
        self.http2 = http2
        self.proxies = proxies
        self.user_agent = user_agent
        self.timeout = timeout

        if use_fallback:
            self.service_urls = DEFAULT_FALLBACK_SERVICE_URLS
            self.client_type = 'gtx'
            pass
        else:
            # default way of working: use the defined values from user app
            self.service_urls = service_urls
            self.client_type = 'tw-ob'
            self.token_acquirer = None

        self.raise_exception = raise_exception
        self.client = None

        if not lazy_client:
            self._ensure_client()

    def _create_client(self):
        retry_transport = RetryTransport(
            wrapped_transport=httpx.HTTPTransport(retries=10),
            retryable_methods={'GET', 'POST'},
            # Google would take too "sorry" page sometimes with 302
            retry_status_codes={302}
        )
        # httpx<0.28 uses `proxies=...`, httpx>=0.28 uses `proxy=...`
        try:
            return httpx.Client(
                http2=self.http2,
                proxies=self.proxies,
                transport=retry_transport,
                timeout=self.timeout
            )
        except TypeError:
            return httpx.Client(
                http2=self.http2,
                proxy=self.proxies,
                transport=retry_transport,
                timeout=self.timeout
            )

    def _ensure_client(self):
        """Ensure self.client is initialized and configured."""
        if self.client is not None:
            return

        self.client = self._create_client()
        self.client.headers.update({
            'User-Agent': self.user_agent,
            'Referer': 'https://translate.google.com',
        })
        if self.timeout is not None:
            self.client.timeout = self.timeout

        # token acquirer depends on the client, so ensure it's bound to the same one
        if (
            getattr(self, "client_type", None) != "gtx"
            and getattr(self, "token_acquirer", None) is None
            and getattr(self, "service_urls", None)
        ):
            self.token_acquirer = self._get_token_acquirer()

    def _get_token_acquirer(self):
        return TokenAcquirer(client=self.client, host=self.service_urls[0])

    @classmethod
    def _build_rpc_request(cls, text: str, dest: str, src: str):
        return json.dumps([[
            [
                cls.RPC_ID,
                json.dumps([[text, src, dest, True], [None]],
                           separators=(',', ':')),
                None,
                'generic',
            ],
        ]], separators=(',', ':'))

    def _pick_service_url(self):
        if len(self.service_urls) == 1:
            return self.service_urls[0]
        return random.choice(self.service_urls)

    @staticmethod
    def _parse_extra_data(data):
        response_parts_name_mapping = {
            0: 'translation',
            1: 'all-translations',
            2: 'original-language',
            5: 'possible-translations',
            6: 'confidence',
            7: 'possible-mistakes',
            8: 'language',
            11: 'synonyms',
            12: 'definitions',
            13: 'examples',
            14: 'see-also',
        }

        extra = {}

        for index, category in response_parts_name_mapping.items():
            extra[category] = data[index] if (
                    index < len(data) and data[index]) else None

        return extra

    @staticmethod
    def validate_normalize_src_dest(src, dest):
        dest = dest.lower().split('_', 1)[0]
        if src:
            src = src.lower().split('_', 1)[0]
        else:
            src = 'auto'

        if src != 'auto' and src not in LANGUAGES:
            if src in SPECIAL_CASES:
                src = SPECIAL_CASES[src]
            elif src in LANGCODES:
                src = LANGCODES[src]
            else:
                raise ValueError('invalid source language')

        if dest not in LANGUAGES:
            if dest in SPECIAL_CASES:
                dest = SPECIAL_CASES[dest]
            elif dest in LANGCODES:
                dest = LANGCODES[dest]
            else:
                raise ValueError('invalid destination language')
        return src, dest

    def parse_response(self, src, dest, origin, data, response: httpx.Response):
        token_found = False
        square_bracket_counts = [0, 0]
        resp = ''
        for line in data.split('\n'):
            token_found = token_found or f'"{self.RPC_ID}"' in line[:30]
            if not token_found:
                continue

            is_in_string = False
            for index, char in enumerate(line):
                if char == '\"' and line[max(0, index - 1)] != '\\':
                    is_in_string = not is_in_string
                if not is_in_string:
                    if char == '[':
                        square_bracket_counts[0] += 1
                    elif char == ']':
                        square_bracket_counts[1] += 1

            resp += line
            if square_bracket_counts[0] == square_bracket_counts[1]:
                break

        data = json.loads(resp)
        if data[0][2] is None:
            # Failed translation
            raise EmptyTranslationData(f"Empty translation data: {data}")
        parsed = json.loads(data[0][2])
        # not sure
        should_spacing = parsed[1][0][0][3]
        translated_parts = list(map(lambda part: TranslatedPart(part[0],
                                                                part[1] if len(
                                                                    part) >= 2 else []),
                                    parsed[1][0][0][5]))
        translated = (' ' if should_spacing else '').join(
            map(lambda part: part.text, translated_parts))

        if src == 'auto':
            try:
                src = parsed[2]
            except:
                pass
        if src == 'auto':
            try:
                src = parsed[0][2]
            except:
                pass

        # currently not available
        confidence = None

        origin_pronunciation = None
        try:
            origin_pronunciation = parsed[0][0]
        except:
            pass

        pronunciation = None
        try:
            pronunciation = parsed[1][0][0][1]
        except:
            pass

        extra_data = {
            'confidence': confidence,
            'parts': translated_parts,
            'origin_pronunciation': origin_pronunciation,
            'parsed': parsed,
        }
        result = Translated(src=src, dest=dest, origin=origin,
                            text=translated, pronunciation=pronunciation,
                            parts=translated_parts,
                            extra_data=extra_data,
                            response=response)
        return result

    @abstractmethod
    def translate(self, text: str, dest='en', src=None):
        pass

    def extract_source_language_and_confidence(self, data, response):
        # actual source language that will be recognized by Google Translator when the
        # src passed is equal to auto.
        src = ''
        confidence = 0.0
        try:
            if len(data[8][0]) > 1:
                src = data[8][0]
                confidence = data[8][-2]
            else:
                src = ''.join(data[8][0])
                confidence = data[8][-2][0]
        except Exception:  # pragma: nocover
            pass
        result = Detected(lang=src, confidence=confidence, response=response)

        return result

    def parse_legacy_response(self, data, src, dest, origin, response):
        # this code will be updated when the format is changed.
        translated = ''.join([d[0] if d[0] else '' for d in data[0]])

        extra_data = self._parse_extra_data(data)

        # actual source language that will be recognized by Google Translator when the
        # src passed is equal to auto.
        try:
            src = data[2]
        except Exception:  # pragma: nocover
            pass

        pron = origin
        try:
            pron = data[0][1][-2]
        except Exception:  # pragma: nocover
            pass

        if pron is None:
            try:
                pron = data[0][1][2]
            except:  # pragma: nocover
                pass

        if dest in self.EXCLUDES and pron == origin:
            pron = translated

        # put final values into a new Translated object
        result = Translated(src=src, dest=dest, origin=origin,
                            text=translated, pronunciation=pron,
                            extra_data=extra_data,
                            parts=[],
                            response=response)

        return result

    @abstractmethod
    def detect(self, text: str):
        pass

    @abstractmethod
    def detect_legacy(self, text, **kwargs):
        pass

    def handle_legacy_translate_response(self, response, text):
        if response.status_code == 200:
            data = utils.format_json(response.text)
            return data, response

        if self.raise_exception:
            raise Exception('Unexpected status code "{}" from {}'.format(
                response.status_code, self.service_urls))

        DUMMY_DATA[0][0][0] = text
        return DUMMY_DATA, response
