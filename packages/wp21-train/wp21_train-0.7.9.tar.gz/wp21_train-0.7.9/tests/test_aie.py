import wp21_train as train
import os

def test_aie_parser_populates_data():
    test_dir  = os.path.dirname(__file__)
    test_file = os.path.join(test_dir,'profile_funct_28_0.xml')
    
    parser = train.parser.aie_parser(test_file)

    assert parser._data     , "Parser didn't collect any data"
    assert parser._meta_data, "Parser didn't collect any meta-data"
