import os
from rara_tools.parsers.mets_alto_parsers.mets_alto_parser import DocumentMeta, SectionMeta
from tests.test_utils import read_json_file

ROOT_DIR = os.path.join("tests", "test_data", "digitizer_output", "mets_alto")

NO_METS_DATA_FILE = "empty_mets_sections.json"

def doc_iterator():
    """ Yields METS/ALTO digitizer outputs.
    """
    test_file_paths = [
        os.path.join(ROOT_DIR, file_name)
        for file_name in os.listdir(ROOT_DIR)
        if file_name != NO_METS_DATA_FILE
    ]
    for file_path in test_file_paths:
        doc = read_json_file(file_path)
        yield doc

def test_keyword_extraction():
    """ Checks, if at least one batch of keywords
    is found for each document.
    """
    for digitizer_output in doc_iterator():
        doc_meta = DocumentMeta(digitizer_output)
        keywords_found = False
        for section in doc_meta.sections_meta:
            keywords = section.keywords
            if keywords:
                keywords_found = True
                break
        assert keywords_found

def test_empty_mets_data_will_pass():
    """ If no METS sections are present in the
    digitizer output, the parser should not break.
    """
    empty_mets_data = read_json_file(os.path.join(ROOT_DIR, NO_METS_DATA_FILE))
    doc_meta = DocumentMeta(empty_mets_data)
    assert doc_meta.to_dict()

def test_sections_meta_ids_and_keywords_extraction():
    """ Tests using SectionMeta class directly.
    """
    for digitizer_output in doc_iterator():
        texts = digitizer_output.get("texts")

        for item in texts:
            section_meta = SectionMeta(item)

            unique_id = section_meta.unique_id
            sequence_nr = section_meta.sequence_number
            keywords = section_meta.keywords

            output = {"unique_id": unique_id, "sequence_nr": sequence_nr, "keywords": keywords}
            assert output


def test_doc_meta_extraction():
    for digitizer_output in doc_iterator():
        doc_meta = DocumentMeta(digitizer_output)
        #print(doc_meta.to_dict())
        assert doc_meta.to_dict()