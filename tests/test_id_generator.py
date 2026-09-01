from splash.lib.id_generator import IDGenerator


def test_random_character_generation_rejects_biased_byte_values(monkeypatch):
    monkeypatch.setattr(
        'splash.lib.id_generator.token_bytes',
        lambda _length: bytes((0, 35, 36, 251, 252, 255)),
    )

    assert IDGenerator._random_chars(5) == 'A9A9A'


def test_generated_id_preserves_requested_length_and_prefix():
    generated = IDGenerator.generate(64, prefix='delete')

    assert len(generated) == 64
    assert generated.startswith('DELETE-')
