# ---------------------------------------------------------------------------- #
#                                 CONFIG READER                                #
# ---------------------------------------------------------------------------- #

# ---------------------------------- IMPORTS --------------------------------- #
import argparse
import sys
import yaml

from dataclasses import dataclass
from dataclass_wizard import JSONListWizard
from dataclass_wizard.enums import LetterCase
from loguru import logger
from pathlib import Path
from typing import List

# ---------------------------------------------------------------------------- #
#                                  DATACLASSES                                 #
# ---------------------------------------------------------------------------- #

@dataclass
class Sys:
    
    """
    Dataclass to store values for systems
    ...

    Attributes
    ----------
    uri: str
        uri of the systems where it's reachable
    port: int
        port of the system where it runs
    """
    uri: str
    port: int

@dataclass
class ProviderSys(Sys):
    """
    Dataclass to store provider system attributes. Inherites class Sys.
    ...

    Attributes
    ----------
    sysName: str
        name of the provider system (in Arrowhead)
    sysid: int
        ID of the provider system (in Arrowhead)
    """
    sysName: str
    sysid: int

@dataclass
class Core:
    """
    Dataclass to store coresystems.
    ...

    Attributes
    ----------
    serviceRegistry: Sys
        service registry core system
    authorization: Sys
        authorization core system
    orchestrator: Sys
        orchestrator core system
    """
    serviceRegistry: Sys
    authorization: Sys
    orchestrator: Sys

@dataclass
class Clog:
    """
    Dataclass to store log settings.
    ...

    Attributes
    ----------
    toFile: bool
        if set the software will log to a file as well
    path: str
        path for the log file (if one used)
    """
    toFile: bool
    path: str

@dataclass
class AutoSetup:
    """
    Dataclass to store auto setup settings.
    ...

    Attributes
    ----------
    sysReg: bool
        flag for automatic system registration (and cleanup) with !SYSOP! client
    serviceReg: bool
        flag for automatic service registration (and cleanup) with !SYSOP! client
    authRules: bool
        flag for automatic authorization rules registration (and cleanup) with !SYSOP! client
    consumers: List[int]
        list of consumer ID that will be presented in authorization rules
    """
    sysReg: bool
    serviceReg: bool
    authRules: bool
    consumers: List[int]

@dataclass
class Config(JSONListWizard):
    """
    Dataclass for storing configuration that is parsed from JSON
    ...

    Attributes
    ----------
    core: Core
        coresystem settings
    provider: ProviderSys
        provider systems settings
    log: Clog
        log settings
    autoSetup: AutoSetup
        auto setup (and cleanup) settings
    certpath: str
        path for certificates
    nbpath: str
        path for ipython notebook
    """
    class ConfigMeta(JSONListWizard.Meta):
        """
        Metaclass for key transformation
        """
        key_transform_with_load = LetterCase.CAMEL

    core: Core
    provider: ProviderSys
    log: Clog
    autoSetup: AutoSetup
    certpath: str
    nbpath: str

# ---------------------------------------------------------------------------- #
#                                   FUNCTIONS                                  #
# ---------------------------------------------------------------------------- #

def readConfig() -> Config:
    """
    Reads config file that are given as command-line argument

    Returns:
        config (Config): The config data structure from the config file 
    """

    logger.info("Initialization process has been started!")

    # ----------------------------------- ARGS ----------------------------------- #
    parser = argparse.ArgumentParser()

    parser.add_argument("-c", default="./config.yml", help="Path for the config file (relative to the application)")
    parser.add_argument("-d", action=argparse.BooleanOptionalAction, help="Turn on debug mode for logging")

    args = parser.parse_args()

    # ----------------------------------- DEBUG ---------------------------------- #
    if not args.d:
        logger.remove()
        logger.add(sys.stderr, level="INFO")

    logger.debug("config-file-path: {c}", c=args.c)

    # ---------------------------------- CONFIG ---------------------------------- #
    config = None

    try:
        with open(args.c, "r") as stream:
            try:
                c = yaml.safe_load(stream)
                config = Config.from_dict(c)
            except yaml.YAMLError as exc:
                logger.exception(exc)
                sys.exit()
    except EnvironmentError as exc:
        logger.exception(exc)
        sys.exit()

    logger.debug("Config file succesfully read:\n{c}", c=config)

    # ------------------------------------ LOG ----------------------------------- #
    if config.log.toFile:
        logger.add(Path(config.log.path + "/{time}.log"))
        logger.debug("Log file has been created!");

    return config
