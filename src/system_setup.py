# ---------------------------------------------------------------------------- #
#                                 SYSTEM SETUP                                 #
# ---------------------------------------------------------------------------- #
#! Warning: This file is for import provider settings (especially authorization
#! rules) to the local cloud. It uses cloud certificates for authorization, which
#! means that it is only suitable if you are the owner of the local cloud.
#! Otherwise your local cloud administrator has to set them up via Arrowhead
#! Mangement Tool.

# ---------------------------------- IMPORT ---------------------------------- #
import sys

from loguru import logger
from pathlib import Path
from typing import List

from arrowhead_client.dto import DTOMixin
from arrowhead_client.client.implementations import SyncClient
from arrowhead_client.system import ArrowheadSystem
from arrowhead_client.service import Service
from arrowhead_client.rules import OrchestrationRule
from arrowhead_client.forms import ServiceRegistrationForm
from arrowhead_client.service import ServiceInterface

from config import Config

# ------------------------------ GLOBAL VARIABLE ----------------------------- #
_setup_client = None

# ----------------------------- PRIVATE FUNCTIONS ---------------------------- #
def _setupClient(c: Config) -> None:
    """
    This function set a sysop client up to perform automated administration

    Args:
        c (Config): config struct
    """

    global _setup_client

    cPath = Path(c.certpath)

    _setup_client = SyncClient.create(
        system_name='sysop',
        address=c.provider.uri,
        port=58923,
        keyfile=cPath / 'sysop.key.pem',
        certfile=cPath / 'sysop.crt.pem',
        cafile=cPath / 'sysop.ca'
    )

    # ------------------------- MANAGAMENT ENDPOINT SETUP ------------------------ #
    _setup_client.orchestration_rules.store(
        OrchestrationRule(
            Service(
                'mgmt_register_service',
                'serviceregistry/mgmt',
                ServiceInterface.from_str('HTTP-SECURE-JSON'),
            ),
            ArrowheadSystem(
                system_name = 'service_registry',
                address = c.core.serviceRegistry.uri,
                port = c.core.serviceRegistry.port
            ),
            'POST',
        )
    )

    _setup_client.orchestration_rules.store(
        OrchestrationRule(
            Service(
                'mgmt_remove_service',
                'serviceregistry/mgmt',
                ServiceInterface.from_str('HTTP-SECURE-JSON'),
            ),
            ArrowheadSystem(
                system_name = 'service_registry',
                address = c.core.serviceRegistry.uri,
                port = c.core.serviceRegistry.port
            ),
            'DELETE',
        )
    )

    _setup_client.orchestration_rules.store(
        OrchestrationRule(
            Service(
                'mgmt_get_systems',
                'serviceregistry/mgmt/systems',
                ServiceInterface('HTTP', 'SECURE', 'JSON'),
            ),
            ArrowheadSystem(
                system_name = 'service_registry',
                address = c.core.serviceRegistry.uri,
                port = c.core.serviceRegistry.port
            ),
            'GET',
        )
    )

    _setup_client.orchestration_rules.store(
        OrchestrationRule(
            Service(
                'mgmt_register_system',
                'serviceregistry/mgmt/systems',
                ServiceInterface('HTTP', 'SECURE', 'JSON'),
            ),
            ArrowheadSystem(
                system_name = 'service_registry',
                address = c.core.serviceRegistry.uri,
                port = c.core.serviceRegistry.port
            ),
            'POST',
        )
    )

    # ONLY FOR CONSUMER TESTING
    _setup_client.orchestration_rules.store(
        OrchestrationRule(
            Service(
                'mgmt_remove_system',
                'serviceregistry/mgmt/systems',
                ServiceInterface('HTTP', 'SECURE', 'JSON'),
            ),
            ArrowheadSystem(
                system_name = 'service_registry',
                address = c.core.serviceRegistry.uri,
                port = c.core.serviceRegistry.port
            ),
            'DELETE',
        )
    )

    _setup_client.orchestration_rules.store(
        OrchestrationRule(
            Service(
                'mgmt_authorization_store',
                'authorization/mgmt/intracloud',
                ServiceInterface('HTTP', 'SECURE', 'JSON'),
            ),
            ArrowheadSystem(
                system_name = 'authorization',
                address = c.core.authorization.uri,
                port = c.core.authorization.port
            ),
            'POST',
        )
    )

    _setup_client.orchestration_rules.store(
        OrchestrationRule(
            Service(
                'mgmt_authorization_remove',
                'authorization/mgmt/intracloud',
                ServiceInterface('HTTP', 'SECURE', 'JSON'),
            ),
            ArrowheadSystem(
                system_name = 'authorization',
                address = c.core.authorization.uri,
                port = c.core.authorization.port
            ),
            'DELETE',
        )
    )

    _setup_client.setup()
    logger.debug("SYSOP client has been set up!")

# ---------------------------------------------------------------------------- #
#                               PUBLIC FUNCTIONS                               #
# ---------------------------------------------------------------------------- #

# ------------------------------- SETUP SYSTEM ------------------------------- #
def setupSystem(c: Config, _system: ArrowheadSystem) -> int:
    """
    This function registers the given AH system into the local cloud's registry

    Args:
        c (Config): config data
        _system (ArrowheadSystem): Arrowhead provider system to be created

    Returns:
        int: system ID
    """
    global _setup_client
    if not _setup_client:
        _setupClient(c)

    try:
        data = _setup_client.consume_service(
            'mgmt_register_system',
            json=_system.dto()
        ).read_json()

    except Exception as e:
        logger.exception("Cannot register system into the cloud! Due to: {}", e)
        sys.exit(127)

    return data['id']

# -------------------------------- SETUP AUTH -------------------------------- #
def setupAuth(c: Config, serviceList: List[int], sysid: int) -> List[int]:
    """
    This function sets the required authorization rules in the local cloud

    Args:
        c (Config): config data
        serviceList (List[int]): list of servive ID-s for which the consumers will be authorized
        sysid (int): ID of the provider system

    Returns:
        List[int]: list of authorization rule ID-s
    """

    global _setup_client
    if not _setup_client:
        _setupClient(c)

    class AuthorizationIntracloudForm(DTOMixin):
        consumer_id: int
        provider_ids: List[int]
        interface_ids: List[int]
        service_definition_ids: List[int]

    ids = list()

    logger.debug("Authorization rules will be registered for the following consumers: {}", c.autoSetup.consumers)

    for consumer in c.autoSetup.consumers:
        form = AuthorizationIntracloudForm(
            consumer_id=consumer,
            provider_ids=[sysid],
            interface_ids=[1],
            service_definition_ids=serviceList,
        )

        try:
            result = _setup_client.consume_service(
                'mgmt_authorization_store',
                json=form.dto()
            )
            ids.append(result.read_json()["count"])
            logger.debug("Authorization rule for consumer ID: '{}' has been set up!", consumer)
    
        except Exception as e:
            logger.exception("Cannot setup authorization rule for consumer {} due to: {}", consumer, e)
    
    return ids

# ----------------------------- REGISTER SERIVCE ----------------------------- #
def registerService(provider_sys: ArrowheadSystem, servicepath: str, servicename: str) -> int:
    """_summary_

    Args:
        provider_sys (ArrowheadSystem): provider system
        servicepath (str): URI of the service
        servicename (str): name of the service

    Raises:
        Exception: if the register request doesn't return with HTTP 2xx - (unauthorized, bad request/service definition)

    Returns:
        int: ID of the registered service 
    """
    global _setup_client

    serviceForm = ServiceRegistrationForm.make(
            Service(
                    servicename,
                    servicepath,
                    ServiceInterface.from_str('HTTP-SECURE-JSON'),
                    'CERTIFICATE'
            ),
            provider_sys
        )

    try:
        register_res = _setup_client.consume_service(
            'mgmt_register_service',
            json=serviceForm.dto(),
        ).read_json()
        
        return register_res['serviceDefinition']['id']
    
    except Exception as e:
        logger.exception("Cannot register service due to: {}", e)
        raise Exception

# ------------------------------ REMOVE SERVICE ------------------------------ #
def removeService(service_id: int) -> None:
    """
    This function unregister the given service from local cloud

    Args:
        service_id (int): ID of ther service to be unregistered
    """

    global _setup_client
    try:
        _setup_client.consume_service(
            'mgmt_remove_service',
            rmid=service_id
        )
        logger.debug("Service '{}' has been unregistered!", service_id)
    except Exception as e:
        logger.exception("Cannot unregister service '{}', due to: {}", service_id, e)

# ------------------------------- REMOVE SYSTEM ------------------------------ #
def removeSystem(_sysid: int):
    """
    This function unregister a system from local cloud

    Args:
        _sysid (int): ID of the provider system to be unregistered
    """

    global _setup_client
    try:
        _setup_client.consume_service(
            'mgmt_remove_system',
            rmid=_sysid
        )
        logger.debug("System'{}' has been removed!", _sysid)

    except Exception as e:
        logger.exception("Cannot remove system '{}', due to: {}", _sysid, e)

# -------------------------------- REMOVE AUTH ------------------------------- #
def removeAuth(authids: List[int]) -> None:
    """
    This function removes registered authorization rules

    Args:
        authids (List[int]): list of authorzation rule ID-s
    """

    global _setup_client
    for authid in authids:
        try:
            _setup_client.consume_service(
                'mgmt_authorization_remove',
                rmid=authid
            )
            logger.debug("Authorization rule '{}' has been removed!", authid)
        except Exception as e:
            logger.exception("Cannot remove authorization rule '{}', due to: {}", authid, e)