import asyncio
import time

import pytest

from idioma import AsyncTranslator, Translator

# Number of translations to perform for the test
NUM_TRANSLATIONS = 10  # Adjust this to a small number for the test


@pytest.mark.asyncio
async def test_async_translation():
    async with AsyncTranslator() as translator:
        text_to_translate = "Hello, world!"
        destination_language = "fr"
        translation = await translator.translate(text_to_translate,
                                                 dest=destination_language)
        assert translation is not None
        assert translation.src == "en"  # Ensure the source language is correctly detected
        assert translation.dest == destination_language
        assert translation.text is not None
        assert translation.text == "Bonjour le monde!"  # Check that translation is different from the input text


@pytest.mark.asyncio
async def test_async_translate_thai_lang_detect():
    async with AsyncTranslator() as translator:
        detection = await translator.detect('안녕하세요')
        assert detection.lang == 'ko'


@pytest.mark.asyncio
async def test_async_translate_thai_explicit():
    async with AsyncTranslator() as translator:
        translation = await translator.translate(
            'แต่ส่งได้แค่คำว่าทำไม', src='th', dest='en'
        )
        assert translation.text == 'But can only send the word "why"'


@pytest.mark.asyncio
async def test_async_is_faster_than_sync():
    translator = Translator()
    async_translator = AsyncTranslator()

    async def translate_sync():
        for _ in range(NUM_TRANSLATIONS):
            translation = translator.translate("Hello, world!", dest='fr')
            assert translation.text == "Bonjour le monde!"

    async def translate_async():
        tasks = []
        for _ in range(NUM_TRANSLATIONS):
            task = async_translator.translate("Hello, world!", dest='fr')
            tasks.append(task)
        await asyncio.gather(*tasks)

    sync_start_time = time.time()
    await translate_sync()
    sync_end_time = time.time()
    sync_elapsed_time = sync_end_time - sync_start_time

    async_start_time = time.time()
    await translate_async()
    async_end_time = time.time()
    async_elapsed_time = async_end_time - async_start_time

    # Assert that the asynchronous version is faster than the synchronous
    # version
    assert async_elapsed_time < sync_elapsed_time


@pytest.mark.asyncio
async def test_translate_russian_lang_hello_evade_rate_limit(capsys):
    translator = AsyncTranslator()
    for i in range(300):
        translation = await translator.translate(
            f'Привет #{i}', src='ru', dest='en')
        translated = translation.text
        print(f"Translated: {translated}")
        assert translated in [f'Hello #{i}', f'Hi #{i}', f'Hi: #{i}', f"Hi: {i}"]
