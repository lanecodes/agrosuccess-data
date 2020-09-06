"""
make_succession_model_file.py
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Load succesion rules from graph database and write it to file.
"""
import logging

import config
from convert_json import serialize_succession_model
from model import assemble_succession_model
from graph import get_default_driver, read_eco_transitions

logging.basicConfig(level=logging.INFO)


if __name__ == '__main__':
    logging.info(f'Loading model {config.MODEL_ID} from graph database at '
                 f'{config.HOST}:{config.PORT}')
    trans_rules = list(read_eco_transitions(get_default_driver(),
                                            config.MODEL_ID))
    model = assemble_succession_model(config.MODEL_ID, trans_rules)
    logging.info(f'Loaded {len(trans_rules)} transition rules from graph')
    serialized_model = serialize_succession_model(model)
    with open(config.OUTPUT_JSON_FILE, 'w') as out_file:
        out_file.write(serialized_model)
    logging.info(f'Finished serializing model to {config.OUTPUT_JSON_FILE}')
