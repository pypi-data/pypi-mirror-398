import asyncio
import edge_tts
import os

async def _text_to_audio_file(text) -> None:
    nvlib_folder = "NVLib"
    tts_folder = os.path.join(nvlib_folder, "TTS-Data")
    os.makedirs(tts_folder, exist_ok=True)

    file_path = os.path.join(tts_folder, "speech.mp3")

    if os.path.exists(file_path):
        os.remove(file_path)

    communicate = edge_tts.Communicate(
        text,
        "en-CA-LiamNeural",
        pitch="+5Hz",
        rate="+13%",
    )
    await communicate.save(file_path)


def _play_audio():
    try:
        import pygame
    except ImportError:
        raise RuntimeError(
            "Text-to-Speech requires pygame.\n"
            "Install it with: pip install nvlib-sn[audio]"
        )

    pygame.mixer.init()
    pygame.mixer.music.load("NVLib/TTS-Data/speech.mp3")
    pygame.mixer.music.play()

    while pygame.mixer.music.get_busy():
        pygame.time.Clock().tick(10)

    pygame.mixer.music.stop()
    pygame.mixer.quit()


def say(text):
    try:
        asyncio.run(_text_to_audio_file(text))
        _play_audio()
    except Exception as e:
        print(f"Error in say(): {e}")
