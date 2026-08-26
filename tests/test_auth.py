from splash.blueprints.auth import _is_local_redirect


def test_redirect_validation_accepts_only_local_paths():
    assert _is_local_redirect('/images/abc?raw=true')
    assert not _is_local_redirect('https://attacker.example/')
    assert not _is_local_redirect('//attacker.example/')
    assert not _is_local_redirect('relative/path')
