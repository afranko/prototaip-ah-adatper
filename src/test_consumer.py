# ---------------------------------------------------------------------------- #
#                                 TEST CONSUMER                                #
# ---------------------------------------------------------------------------- #

# ---------------------------------- IMPORTS --------------------------------- #
import sys

import system_setup

from loguru import logger
from pathlib import Path
from simple_term_menu import TerminalMenu

from arrowhead_client.system import ArrowheadSystem
from arrowhead_client.client.implementations import SyncClient
from arrowhead_client.constants import CoreSystem

from config import readConfig, Config

# --------------------------------- CONSTANTS -------------------------------- #

#! You can change these
CONSUMER_ADDR = "192.168.0.100"
CONSUMER_PORT = 12210
CONSUMER_SYS_NAME = "test-consumer"
PROVIDER_SERVICE_NAME = "echo"

EXIT_TEXT = "Exit"

# ---------------------------------------------------------------------------- #
#                                    SCRIPT                                    #
# ---------------------------------------------------------------------------- #
def sendReq(consumer: SyncClient) -> None:
    """
    This function initiates a request to a predefined arrowhead services. It is
    tailored for testing purposes.

    Args:
        consumer (SyncClient): consumer client to be used
    """
    try:
        consumer.add_orchestration_rule(PROVIDER_SERVICE_NAME, 'POST', payload_format = "JSON")
        echo_response = consumer.consume_service(PROVIDER_SERVICE_NAME, json={'msg': PROVIDER_SERVICE_NAME})

        logger.info("Test has been succesuful! Response: {}", echo_response)
    except Exception as e:
        logger.exception("Test has failed! Response: {}", e)

def main():
    # ----------------------------------- INIT ----------------------------------- #
    c = readConfig()

    logger.info("Test consumer application has been started!")

    consumer_sys = ArrowheadSystem(
        system_name=CONSUMER_SYS_NAME,
        address=CONSUMER_ADDR,
        port=CONSUMER_PORT
    )

    sysid = system_setup.setupSystem(c, consumer_sys)
    logger.info("System has been succesfully set up! Consumer system ID: {}", sysid)

    cPath = Path(c.certpath)

    consumer = SyncClient.create(
        system_name=CONSUMER_SYS_NAME,
        address=CONSUMER_ADDR,
        port=CONSUMER_PORT,
        config={
            'service_registry': {
            'system_name': CoreSystem.SERVICE_REGISTRY,
            'address': c.core.serviceRegistry.uri,
            'port': c.core.serviceRegistry.port,
            },
            'orchestrator': {
                'system_name': CoreSystem.ORCHESTRATOR,
                'address': c.core.orchestrator.uri,
                'port': c.core.orchestrator.port,
            },
            'authorization': {
                'system_name': CoreSystem.AUTHORIZATION,
                'address': c.core.authorization.uri,
                'port': c.core.authorization.port,
            },
        },
        keyfile=cPath / 'test-consumer/test-consumer.key.pem',
        certfile=cPath / 'test-consumer/test-consumer.crt.pem',
        cafile=cPath / 'sysop.ca'
    )
    
    consumer.setup()

    logger.debug("Consumer client has been created! Enter menu...")

    # ----------------------------------- MENU ----------------------------------- #
    exit = False
    options = ["Send an HTTPS request to the provider", EXIT_TEXT]
    terminal_menu = TerminalMenu(options, title="Consumer system ID: {}".format(sysid))

    while not exit:
        menu_entry_index = terminal_menu.show()

        if options[menu_entry_index] != EXIT_TEXT:
            sendReq(consumer)
        else:
            exit = True

    # ----------------------------- GRACEFUL SHUTDOWN ---------------------------- #
    system_setup.removeSystem(sysid)
    logger.info("Graceful exit! Please wait...")
    sys.exit(0)

if __name__ == "__main__":
    main()
