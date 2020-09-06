"""
graph.py
~~~~~~~~

Read ecological succession rules for AgroSuccess from the Neo4j graph database.
"""
import logging
from typing import Iterable

from neo4j import Driver, GraphDatabase, Transaction, Record
from neo4j.exceptions import AuthError

import config
from model import EnvrAntecedent, EnvrConsequent, TransitionRule


def get_default_driver() -> Driver:
    """Get a Neo4j database driver using settings in config.py."""
    uri = "bolt://" + 'localhost' + ":" + str(config.PORT)
    try:
        driver = GraphDatabase.driver(uri, auth=(config.USER, config.PASSWORD))
    except ValueError:
        logging.error(f'Could not access database at {uri}. Reivew '
                      'configuration')
        raise
    except AuthError:
        logging.error('Neo4j username or password incorrect. Review '
                      'configuration')
        raise

    return driver


def read_eco_transitions(driver: Driver, model_id: str) -> Iterable[TransitionRule]:
    """Executes database transaction to read ecological transition rules.

    Args:
        driver: Database driver.
        model_id: Name of the specific model version for which to extract the
            ecological transitions from the database.

    Returns:
        Iterable over the complete set of transition rules for the model.
    """
    with driver.session() as session:
        trans_rules = session.read_transaction(eco_transitions_query, model_id)
    return trans_rules


def eco_transitions_query(tx: Transaction, model_id: str) -> Iterable[TransitionRule]:
    """Query the graph for all possible ecological transitions.

    Args:
        tx: Database transaction object.
        model_id: Name of the specific model version for which to extract the
            ecological transitions from the database.

    Returns:
        Iterable over the complete set of transition rules for the model.
    """
    results = tx.run(
        "MATCH (lct1:LandCoverType)<-[:SOURCE]-(t:SuccessionTrajectory) "
        "-[:TARGET]->(lct2:LandCoverType) "
        "WHERE lct1.model_ID=$model_ID AND lct1.code<>lct2.code "
        "WITH lct1, lct2, t MATCH (e:EnvironCondition)-[:CAUSES]->(t) "
        "RETURN lct1.code as start_state, e.succession as succession_pathway, "
        "    e.aspect as aspect, e.pine as pine_seeds, e.oak as oak_seeds, "
        "    e.deciduous as deciduous_seeds, e.water as water, "
        "    lct2.code as target_state, e.delta_t as transition_time;",
        model_ID=model_id
    )
    return [convert_record_to_transition_rule(record) for record in results]


def convert_record_to_transition_rule(record: Record) -> TransitionRule:
    return _get_envr_antecedent(record), _get_envr_consequent(record)


def _get_envr_antecedent(record: Record) -> EnvrAntecedent:
    """Extract ``EnvrAntecedent`` fields from database record."""
    return EnvrAntecedent(
        **{k: record[k] for k in EnvrAntecedent.fields()}
    )


def _get_envr_consequent(record: Record) -> EnvrConsequent:
    """Extract `EnvrConsequent` fields from database record."""
    return EnvrConsequent(
        **{k: record[k] for k in EnvrConsequent.fields()}
    )


if __name__ == "__main__":
    trans_rules = read_eco_transitions(get_default_driver(), config.MODEL_ID)
    print(trans_rules)
