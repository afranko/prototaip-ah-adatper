# ---------------------------------------------------------------------------- #
#                          PROTOTAIP ARROWHEAD ADAPTER                         #
# ---------------------------------------------------------------------------- #

# ---------------------------------------------------------------------------- #
#                                    IMPORTS                                   #
# ---------------------------------------------------------------------------- #
import json
import nbconvert
import nbformat
import os
import pathlib
import sys

import system_setup

from fnmatch import fnmatch
from loguru import logger
from nbclient import NotebookClient
from pathlib import Path
from typing import List

from config import readConfig, Config

# ---------------------------------------------------------------------------- #
#                               ARROWHEAD LIBRARY                              #
# ---------------------------------------------------------------------------- #
from arrowhead_client.client.implementations import AsyncClient
from arrowhead_client.system import ArrowheadSystem

from arrowhead_client.request import Request
from arrowhead_client.constants import CoreSystem

# ---------------------------------------------------------------------------- #
#                                   CONSTANTS                                  #
# ---------------------------------------------------------------------------- #
IPYNB_EXT = "*.ipynb"

def pynb_execute(nbRoot: str, path: str, data: any, sname: str) -> any:
    """
    This function executes a jupyter notebook as regular python file

    Args:
        fpath (Path): path for the nb file
        data (any): input data
        sname (str): service name

    Raises:
        ChildProcessError: Any error during execution

    Returns:
        any: output of the notebook
    """
    
    # ----------------------------- CONVERT NOTEBOOK ----------------------------- #
    nbPath = Path(nbRoot, path + ".ipynb")

    try:
        # ------------------------------- CREATE SCRIPT ------------------------------ #
        nb = nbformat.read(nbPath, as_version=4)
        script, _ = nbconvert.PythonExporter().from_notebook_node(nb)

        script_local = {"data_input": json.dumps(data)}
        exec(script, None, script_local)
        return script_local["output"]
        # ! 'output' must be declared
        
    except Exception as e:
        logger.exception("Cannot execute notebbok: {}, due to: {}", sname, e)
        raise ChildProcessError
    
def jpnb_execute(nbRoot: str, path: str, data: any, sname: str) -> any:
    """
    This function executes a jupyter notebook as ipynb

    Args:
        fpath (Path): path for the nb file
        data (any): input data
        sname (str): service name

    Raises:
        ChildProcessError: Any error during execution

    Returns:
        any: output of the notebook
    """

    # ----------------------------- CREATE INPUTFILE ----------------------------- #
    with open(Path(nbRoot, path + "-inputdata.json"),'w') as f:
        f.write(''.join(json.dumps(data)))

    nbPath = Path(nbRoot, path + ".ipynb")

    try:
        nb = nbformat.read(nbPath, as_version=4)
        client = NotebookClient(nb, resources={'metadata': {'path': Path(nbRoot, path).parent}})
        client.execute()
        nbformat.write(nb, nbPath)
    except Exception as e:
        logger.exception("Cannot execute notebbok: {}, due to: {}", sname, e)
        raise ChildProcessError

    # ----------------------------- REMOVE INPUTFILE ----------------------------- #
    try:
        os.remove(Path(nbRoot, path + "-inputdata.json"))
    except OSError as e:
        logger.exception("Cannot remove input file for '{}', due to {}", sname, e)

    return nb.cells[-1]["outputs"][-1]["text"]

def makeptThread(nbRoot: str, path: str, name: str, _provider: AsyncClient) -> callable:
    """
    It's a function factory closure

    Args:
        nbRoot (str): root path for notebooks
        path (str): path for the actual notebook
        name (str): name of the service
        _provider (AsyncClient): provider client

    Returns:
        callable: provided service
    """
    @_provider.provided_service(
        service_definition=name,
        service_uri=path,
        protocol='HTTP',
        method='POST',
        payload_format='JSON',
        access_policy='CERTIFICATE',
        data_model=any
    )
    async def ptThread(req: Request[any]) -> any:
        """
        This function executes a notebook based on the input data

        Args:
            req (Request[any]): input data from webservice

        Raises:
            ValueError: Bad request
            ChildProcessError: Cannot execute notebook properly

        Returns:
            any: output of the notebook
        """

        try:
            data = json.loads(req.body)
            logger.debug(name +": Input data: {}", data)
        except Exception as e:
            logger.exception("Cannot run service: {}, due to: {}", name, e)
            raise ValueError

        # ------------------------------ EXECUTE SCRIPT ------------------------------ #
        #output = jpnb_execute(nbRoot, path, data, name)
        output = pynb_execute(nbRoot, path, data, name)

        logger.debug(name +": Output data: {}", output)
        return output
    return ptThread

def main():
    config = readConfig()

    logger.info("Application has been started!")

    cPath = Path(config.certpath)

    # ------------------------------ CONNECTION TEST ----------------------------- #
    

    # -------------------------- CONFIG PROVIDER SYSTEM -------------------------- #
    provider_sys, sysid = ArrowheadSystem.with_certfile(
        system_name=config.provider.sysName,
        address=config.provider.uri,
        port=config.provider.port,
        certfile=cPath / 'prototaip.crt.pem'
    ), config.provider.sysid

    if config.autoSetup.sysReg:
        sysid = system_setup.setupSystem(config, provider_sys)
    
    logger.info("Provider system has been created with ID: {}!", sysid)    

    # -------------------------- CONFIG PROVIDER CLIENT -------------------------- #

    provider = AsyncClient.create(
        system_name=config.provider.sysName,
        address=config.provider.uri,
        port=config.provider.port,
        config={
            'service_registry': {
            'system_name': CoreSystem.SERVICE_REGISTRY,
            'address': config.core.serviceRegistry.uri,
            'port': config.core.serviceRegistry.port,
            },
            'orchestrator': {
                'system_name': CoreSystem.ORCHESTRATOR,
                'address': config.core.orchestrator.uri,
                'port': config.core.orchestrator.port,
            },
            'authorization': {
                'system_name': CoreSystem.AUTHORIZATION,
                'address': config.core.authorization.uri,
                'port': config.core.authorization.port,
            },
        },
        keyfile=cPath / 'prototaip.key.pem',
        certfile=cPath / 'prototaip.crt.pem',
        cafile=cPath / 'sysop.ca'
    )

    # ---------------------- CREATING AND REGISTER SERVICES ---------------------- #
    services = list()

    for path, _, files in os.walk(config.nbpath):
        for name in files:
            if fnmatch(name, IPYNB_EXT):
                services.append(pathlib.PurePath(path, name))
    
    logger.debug("The following services will be created: {}", [str(service.stem).replace(" ", "-").replace("_", "-") for service in services])

    # ----------------------------- GET SERVICE NAMES ---------------------------- #
    service_ids = list()

    for service in services:
        spath = str(service.relative_to(config.nbpath).with_suffix('')).replace(" ", "-").replace("_", "-")
        sname = str(service.stem).replace(" ", "-").replace("_", "-")

        # ----------------------------- DEFINING SERVICE ----------------------------- #
        makeptThread(config.nbpath, spath, sname, provider)

        # ----------------------------- REGISTER SERVICE ----------------------------- #
        if config.autoSetup.serviceReg:
            try:
                service_ids.append(system_setup.registerService(provider_sys, spath, sname))
                logger.debug('Service "{}" registered successfully!', sname)
            except Exception:
                logger.warning('Service "{}" cannot be registered!', sname)

    logger.info("Services have been registered!")

    # ----------------------------- SETUP AUTH RULES ----------------------------- #
    if config.autoSetup.authRules and config.autoSetup.serviceReg:
        authids = system_setup.setupAuth(config, service_ids, sysid)
        logger.info("Authorization rules has been set up!")

    # ------------------------------ WAIT FOR SIGNAL ----------------------------- #
    provider.run_forever()

    logger.warning("Graceful shutdown! Please wait...")

    # ----------------------------- REMOVE AUTH RULES ---------------------------- #
    if config.autoSetup.authRules and config.autoSetup.serviceReg:
        system_setup.removeAuth(authids)
        logger.info("Authorization rules has been removed successfully!")

    # ------------------------------ REMOVE SERVICES ----------------------------- #
    if config.autoSetup.serviceReg:
        for service_id in service_ids:
            system_setup.removeService(service_id)
        logger.info("Services has been unregistered successfully!")

    # ------------------------------- REMOVE SYSTEM ------------------------------ #
    if config.autoSetup.sysReg:
        system_setup.removeSystem(sysid)
        logger.info("System has been removed successfully!")

    logger.info("Application has been shuted down gracefully!")

if __name__ == "__main__":
    main()