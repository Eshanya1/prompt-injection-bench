from prompt_injection_bench.corpus import load_attack_corpus
from prompt_injection_bench.defenses.base import DefenseAction
from prompt_injection_bench.defenses.structural_spotlight import (
    StructuralSpotlightDefense,
    datamark,
    delimit,
)

_by_id = {e.id: e for e in load_attack_corpus()}


def test_delimit_wraps_content_in_untrusted_document_tags():
    result = delimit("hello world")
    assert result.startswith("<untrusted_document>")
    assert result.endswith("</untrusted_document>")


def test_datamark_is_lossless_over_word_content():
    original = "The quick brown fox jumps"
    marked = datamark(original)
    recovered = marked.replace("^", " ")
    assert recovered == original


def test_datamark_preserves_unicode_content():
    original = "café résumé naïve"
    marked = datamark(original)
    assert "café" in marked.split("^")
    assert "résumé" in marked.split("^")


def test_benign_text_passes_through_transformed_not_blocked():
    defense = StructuralSpotlightDefense()
    result = defense.screen("A plain, unremarkable paragraph about gardening.")
    assert result.action == DefenseAction.TRANSFORM
    assert result.flagged is False


def test_nested_quoted_injection_still_gets_delimited_as_untrusted():
    """Even content that quotes an injection 'for illustration' is still
    wholly untrusted -- the delimiter wraps the whole document regardless
    of internal framing, since this defense doesn't parse structure."""
    doc = _by_id["atk-nested-01"].text
    defense = StructuralSpotlightDefense()
    result = defense.screen(doc)
    assert result.text.startswith("<untrusted_document>")
    assert "ignore" not in result.text.split("\n")[0].lower()


def test_wrap_system_prompt_adds_hardening_clause_mentioning_the_tag():
    defense = StructuralSpotlightDefense()
    wrapped = defense.wrap_system_prompt("Base prompt.")
    assert "Base prompt." in wrapped
    assert "<untrusted_document>" in wrapped
    assert "never" in wrapped.lower()
