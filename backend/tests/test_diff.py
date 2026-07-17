from app.diff import diff_words


def test_perfect_match():
    result = diff_words("the quick brown fox", "the quick brown fox")
    assert result["accuracy"] == 100.0
    assert result["correct"] == 4
    assert result["wrong"] == 0
    assert result["missed"] == 0
    assert result["extra"] == 0
    assert [w["status"] for w in result["word_diff"]] == ["correct"] * 4


def test_one_wrong_word():
    result = diff_words("the quick brown fox", "the quick red fox")
    assert result["correct"] == 3
    assert result["wrong"] == 1
    assert result["missed"] == 0
    assert result["extra"] == 0
    assert result["accuracy"] == 75.0
    wrong_entries = [w for w in result["word_diff"] if w["status"] == "wrong"]
    assert wrong_entries == [{"word": "brown", "status": "wrong", "typed": "red"}]


def test_missed_word_mid_sentence():
    result = diff_words(
        "the quick brown fox jumps", "the quick fox jumps"
    )
    assert result["correct"] == 4
    assert result["missed"] == 1
    assert result["wrong"] == 0
    assert result["extra"] == 0
    assert result["accuracy"] == 80.0
    missed_entries = [w for w in result["word_diff"] if w["status"] == "missed"]
    assert missed_entries == [{"word": "brown", "status": "missed"}]


def test_extra_word():
    result = diff_words("the quick brown fox", "the quick brown red fox")
    assert result["correct"] == 4
    assert result["extra"] == 1
    assert result["wrong"] == 0
    assert result["missed"] == 0
    assert result["accuracy"] == 100.0
    extra_entries = [w for w in result["word_diff"] if w["status"] == "extra"]
    assert extra_entries == [{"word": "red", "status": "extra"}]


def test_punctuation_and_case_differences():
    result = diff_words("Hello, World! How are you?", "hello world how are you")
    assert result["correct"] == 5
    assert result["wrong"] == 0
    assert result["missed"] == 0
    assert result["extra"] == 0
    assert result["accuracy"] == 100.0
    assert [w["word"] for w in result["word_diff"]] == [
        "Hello,",
        "World!",
        "How",
        "are",
        "you?",
    ]


def test_empty_typed_input():
    result = diff_words("the quick brown fox", "")
    assert result["correct"] == 0
    assert result["missed"] == 4
    assert result["wrong"] == 0
    assert result["extra"] == 0
    assert result["accuracy"] == 0.0
    assert [w["status"] for w in result["word_diff"]] == ["missed"] * 4


def test_empty_reference_and_typed():
    result = diff_words("", "")
    assert result["total_words"] == 0
    assert result["accuracy"] == 0.0
    assert result["word_diff"] == []


def test_empty_reference_with_typed_text():
    result = diff_words("", "hello world")
    assert result["total_words"] == 0
    assert result["accuracy"] == 0.0
    assert result["extra"] == 2
    assert [w["status"] for w in result["word_diff"]] == ["extra", "extra"]
