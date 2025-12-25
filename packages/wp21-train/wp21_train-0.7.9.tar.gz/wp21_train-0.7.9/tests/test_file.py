from wp21_train.parser import hls_parser
from wp21_train.savers import json_adapter
from wp21_train.savers import root_adapter
from wp21_train.savers import pickle_adapter
from wp21_train.parser import aie_parser

import os

def test_aie_parser_and_saver():
    test_dir  = os.path.dirname(__file__)
    test_file = os.path.join(test_dir, 'profile_funct_28_0.xml')

    parser = aie_parser(test_file)

    assert parser._data     , "Parsed data are empty"
    assert parser._meta_data, "Parsed meta-data are empty"
    
    json_aie = json_adapter('test_aie'  , parser._data, parser._meta_data)
    root_aie = root_adapter('test_aie'  , parser._data, parser._meta_data)
    pkl_aie  = pickle_adapter('test_aie', parser._data, parser._meta_data)

    json_aie.write_data()
    root_aie.write_data()
    pkl_aie .write_data()

    assert os.path.isfile('test_aie.json'), "JSON file not created"
    assert os.path.isfile('test_aie.root'), "ROOT file not created"
    assert os.path.isfile('test_aie.pkl' ), "PICKLE file not created"
