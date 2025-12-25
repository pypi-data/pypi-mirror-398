"""
Generiert einfache Soundeffekte für Chessy
Führe dieses Script einmal aus um die Sound-Dateien zu erstellen.
"""

import os
import struct
import math

DIR_PATH = os.path.dirname(os.path.realpath(__file__))
SOUNDS_DIR = os.path.join(DIR_PATH, "sounds")


def generate_sine_wave(frequency, duration, sample_rate=44100, amplitude=0.5):
    """Generiert eine Sinuswelle"""
    num_samples = int(sample_rate * duration)
    samples = []
    for i in range(num_samples):
        t = i / sample_rate
        # Fade in/out für weicheren Sound
        fade = min(1.0, min(i, num_samples - i) / (sample_rate * 0.01))
        value = amplitude * fade * math.sin(2 * math.pi * frequency * t)
        samples.append(int(value * 32767))
    return samples


def generate_click(duration=0.05, sample_rate=44100):
    """Generiert einen kurzen Klick-Sound"""
    num_samples = int(sample_rate * duration)
    samples = []
    for i in range(num_samples):
        decay = 1.0 - (i / num_samples)
        noise = (hash(i) % 65536 - 32768) / 32768
        value = decay * noise * 0.3
        samples.append(int(value * 32767))
    return samples


def generate_capture_sound(sample_rate=44100):
    """Generiert einen Capture-Sound (tiefer Ton)"""
    samples = generate_sine_wave(200, 0.15, sample_rate, 0.4)
    samples2 = generate_sine_wave(150, 0.1, sample_rate, 0.3)
    return samples + samples2


def generate_check_sound(sample_rate=44100):
    """Generiert einen Schach-Warnton (hoher Ton)"""
    samples = generate_sine_wave(800, 0.1, sample_rate, 0.4)
    samples2 = generate_sine_wave(1000, 0.1, sample_rate, 0.3)
    return samples + samples2


def generate_castle_sound(sample_rate=44100):
    """Generiert einen Rochade-Sound"""
    samples = generate_sine_wave(300, 0.1, sample_rate, 0.3)
    samples2 = generate_sine_wave(400, 0.1, sample_rate, 0.3)
    return samples + samples2


def generate_game_over_sound(sample_rate=44100):
    """Generiert einen Spielende-Sound"""
    samples = []
    frequencies = [523, 659, 784, 1047]  # C-E-G-C (C-Dur Akkord)
    for freq in frequencies:
        samples.extend(generate_sine_wave(freq, 0.2, sample_rate, 0.25))
    return samples


def save_wav(filename, samples, sample_rate=44100):
    """Speichert Samples als WAV-Datei"""
    num_samples = len(samples)
    num_channels = 1
    bits_per_sample = 16
    byte_rate = sample_rate * num_channels * bits_per_sample // 8
    block_align = num_channels * bits_per_sample // 8
    data_size = num_samples * block_align

    with open(filename, "wb") as f:
        # RIFF Header
        f.write(b"RIFF")
        f.write(struct.pack("<I", 36 + data_size))
        f.write(b"WAVE")

        # fmt Chunk
        f.write(b"fmt ")
        f.write(struct.pack("<I", 16))  # Chunk size
        f.write(struct.pack("<H", 1))  # Audio format (PCM)
        f.write(struct.pack("<H", num_channels))
        f.write(struct.pack("<I", sample_rate))
        f.write(struct.pack("<I", byte_rate))
        f.write(struct.pack("<H", block_align))
        f.write(struct.pack("<H", bits_per_sample))

        # data Chunk
        f.write(b"data")
        f.write(struct.pack("<I", data_size))
        for sample in samples:
            f.write(struct.pack("<h", max(-32768, min(32767, sample))))


def main():
    """Generiert alle Soundeffekte"""
    if not os.path.exists(SOUNDS_DIR):
        os.makedirs(SOUNDS_DIR)

    print("Generiere Soundeffekte...")

    # Move Sound
    move_samples = generate_click(0.08)
    save_wav(os.path.join(SOUNDS_DIR, "move.wav"), move_samples)
    print("  ✓ move.wav")

    # Capture Sound
    capture_samples = generate_capture_sound()
    save_wav(os.path.join(SOUNDS_DIR, "capture.wav"), capture_samples)
    print("  ✓ capture.wav")

    # Check Sound
    check_samples = generate_check_sound()
    save_wav(os.path.join(SOUNDS_DIR, "check.wav"), check_samples)
    print("  ✓ check.wav")

    # Castle Sound
    castle_samples = generate_castle_sound()
    save_wav(os.path.join(SOUNDS_DIR, "castle.wav"), castle_samples)
    print("  ✓ castle.wav")

    # Game Over Sound
    game_over_samples = generate_game_over_sound()
    save_wav(os.path.join(SOUNDS_DIR, "game_over.wav"), game_over_samples)
    print("  ✓ game_over.wav")

    print("\nAlle Soundeffekte wurden generiert!")
    print(f"Speicherort: {SOUNDS_DIR}")


if __name__ == "__main__":
    main()
