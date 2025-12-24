
from docu_ocr.structured import StructuredExtractor


def test_resume_extraction():
    text = """
    Contact
    Email: test@example.com
    Phone: 1234567890
    Location: Test City
    Summary
    Experienced developer.
    Education
    BSc Computer Science | Test University | 2020-2024
    Skills
    @ Languages: Python, JavaScript
    Experience
    Developer | TestCorp | 2021-2023
    """
    extractor = StructuredExtractor(text)
    result = extractor.extract()
    assert result["classification"]["type"] == "resume"
    assert "contact" in result["sections"]
    assert result["entities"]["emails"] == ["test@example.com"]
    assert result["entities"]["phones"] == ["1234567890"]


def test_letter_extraction():
    text = """
    Dear John,
    This is a test letter.
    Sincerely,
    Jane Doe
    """
    extractor = StructuredExtractor(text)
    result = extractor.extract()
    assert result["classification"]["type"] == "letter"


# Add more tests for invoices, reports, etc. as needed
