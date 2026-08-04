"""Style fingerprint tests."""

from scapegoat.benchmark.style import fingerprint, fingerprint_distance, style_similarity

IMPROMPTU = "谦逊跟我这辈子没有关系，你们喜欢就好。"
ORGANIZED = (
    "关于这件事，我想说三点。\n"
    "第一，产品体验必须放在首位，这是我一贯的立场。\n"
    "第二，厂商应当正视用户的合理诉求，而不是敷衍了事。\n"
    "第三，我会持续关注后续进展。\n"
    "总之，把用户当回事，才配得上用户的信任。"
)


def test_identical_text_is_maximally_similar():
    assert style_similarity(IMPROMPTU, IMPROMPTU) == 1.0
    assert fingerprint_distance(IMPROMPTU, IMPROMPTU) == 0.0


def test_organized_text_is_far_from_impromptu():
    assert style_similarity(ORGANIZED, IMPROMPTU) < 0.6


def test_length_ratio_dominates_when_form_matches():
    """A 4x-longer text in the same voice still reads as a different form."""

    long_version = IMPROMPTU * 4
    assert style_similarity(long_version, IMPROMPTU) < 0.7


def test_enumeration_is_detected():
    assert fingerprint(ORGANIZED).enumeration_density > 0
    assert fingerprint(IMPROMPTU).enumeration_density == 0


def test_short_clause_ratio_separates_the_two_forms():
    assert fingerprint(IMPROMPTU).short_clause_ratio > fingerprint(ORGANIZED).short_clause_ratio


def test_similarity_is_symmetric_and_bounded():
    a = style_similarity(ORGANIZED, IMPROMPTU)
    b = style_similarity(IMPROMPTU, ORGANIZED)
    assert a == b
    assert 0.0 < a <= 1.0


def test_empty_text_does_not_crash():
    assert 0.0 < style_similarity("", IMPROMPTU) <= 1.0


def test_style_prompt_forbids_deliverable_structure():
    from scapegoat.benchmark.prompts import render_case_prompt
    from scapegoat.benchmark.schema import BenchmarkCase

    case = BenchmarkCase(case_id="t3-x", task="style", situation="随手写一条微博", answer="随便", answer_source="s")
    prompt = render_case_prompt(case)
    assert "不是交付物" in prompt
    assert "80-300字" not in prompt
