from idioma import Translator


def test_translate_thai_hello():
    translator = Translator()
    assert translator.translate('안녕하세요').text == 'hello'


def test_translate_thai_hello_src_none_auto():
    translator = Translator()
    assert translator.translate('안녕하세요', src=None).text == 'hello'


def test_translate_thai_lang_detect():
    translator = Translator()
    assert translator.detect('안녕하세요').lang == 'ko'


def test_translate_legacy_russian_lang_hello():
    translator = Translator()
    assert translator.translate_legacy(
        'Привет', src='ru', dest='en').text == 'Hello'


def test_translate_russian_lang_hello_evade_rate_limit(capsys):
    translator = Translator(raise_exception=True)
    for i in range(300):
        translated = translator.translate(
            f'Привет #{i}', src='ru', dest='en').text
        print(f"Translated: {translated}")
        assert translated in [f'Hello #{i}', f'Hi #{i}', f'Hi: #{i}', f"Hi: {i}"]
