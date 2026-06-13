from evaluation.learning_assessment import RUBRIC, detect_misconception, grade


def test_assessment_grading_and_misconception_detection():
    item = RUBRIC["assignment"]
    assert grade("= assigns and == compares", item)
    assert not grade("they are the same", item)
    assert detect_misconception("they are the same", item)
