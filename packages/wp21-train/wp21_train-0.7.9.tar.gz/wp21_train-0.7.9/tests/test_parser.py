import os
import wp21_train as train

def test_hls_parser_populates_data():
    parser = train.parser.hls_parser("tests/csynth.xml")

    print(parser._data)
    print(parser._meta_data)

    assert parser._data     , "Parser didn't collect any data"
    assert parser._meta_data, "Parser didn't collect any meta-data"
