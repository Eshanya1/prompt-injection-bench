from prompt_injection_bench.corpus import (
    Label,
    Technique,
    assert_corpus_integrity,
    load_attack_corpus,
    load_benign_corpus,
    load_full_corpus,
)


def test_attack_corpus_entries_all_parse_and_are_malicious():
    entries = load_attack_corpus()
    assert len(entries) >= 30
    assert all(e.label == Label.MALICIOUS for e in entries)


def test_every_malicious_entry_declares_a_real_technique():
    for e in load_attack_corpus():
        assert e.technique != Technique.NONE


def test_benign_corpus_has_both_adversarial_and_plain_entries():
    entries = load_benign_corpus()
    labels = {e.label for e in entries}
    assert Label.BENIGN_ADVERSARIAL in labels
    assert Label.BENIGN_PLAIN in labels


def test_full_corpus_ids_are_unique():
    entries = load_full_corpus()
    ids = [e.id for e in entries]
    assert len(ids) == len(set(ids))


def test_malicious_canaries_are_unique():
    canaries = [e.canary for e in load_attack_corpus()]
    assert len(canaries) == len(set(canaries))


def test_assert_corpus_integrity_passes_on_real_corpus():
    assert_corpus_integrity(load_full_corpus())


def test_assert_corpus_integrity_catches_duplicate_ids():
    entries = load_attack_corpus()
    tampered = entries[:2] + [entries[0]]
    import pytest

    with pytest.raises(ValueError, match="duplicate corpus ids"):
        assert_corpus_integrity(tampered)


def test_assert_corpus_integrity_catches_duplicate_canaries():
    import pytest

    entries = load_attack_corpus()
    tampered_second = entries[1].model_copy(update={"canary": entries[0].canary})
    with pytest.raises(ValueError, match="duplicate canaries"):
        assert_corpus_integrity([entries[0], tampered_second])
