# PrototAIp Arrowhead Adapter

## Test Local Cloud

For setting up a test cloud check the `tools` folder.

## Generate certs for your services

To generate certificates for your services, use your local cloud master certificate and the [AH Cert tool]. If you want to use the test local cloud, then generate the certs for you local cloud first, then for PrototAIp. (Check `tools/README.md`).

The cert for PrototAIp must be named as `prototaip` (or the system name in the config)! Put your cert into `certs` folder! For using them you have to convert PKCS12 cert to PEM by executing the following commands (in Linux):

- `openssl pkcs12 -in path.p12 -out newfile.key.pem -nocerts -nodes`
- `openssl pkcs12 -in path.p12 -out newfile.crt.pem -clcerts -nokeys`

`sysop.ca` is also needed in order to using the client!

[AH Cert Tool]: https://aitia.ai/hu/downloads/ah-cert-gen/

For using certain settings (autosetup) you have to present the `sysop` certificates as well!

### Using existing certs

All folders already contain certifactes as placeholder examples, but they can be used as valid certificates with the test cloud, only if all services (and the test cloud itself) run on `192.168.0.100`.

## Configuration and running

### Help Flag

PrototAIp Arrowhead Adapter (PAA) accepts flags when it's executed. To display help menu call it with `-h` flag.

### Logging and Debug Flag

If it's enabled, PAA creates logfile to a folder - default: the `log` folder in the same folder where the source file is placed. If `log` (or the given folder) doesn't exist it creates it and populates it with corresponding log files - each run has its own logfile, where the name of the file is the following `timestamp.log`.

To set the log level of the application to `DEBUG` start it with `-d` flag, however it is only recommended, when you test it.

### Config file

PAA reads all config from a YAML file. The default location of the config file must be the same folder where the source file is located and has to be named as: `config.yml`. To override this execute PAA with `-c [UNIX path of config file]` and PAA reads the config file from the specified location.

The example config file is in the root folder: `config.yml.example`.

### Config properties

The `core` properties are needed for reaching the local cloud, `uri` is always a string, while `port` is number.

```yaml
core:
  service-registry:
    uri:  "192.168.0.100"
    port: 8443

  authorization:
    uri:  "192.168.0.100"
    port: 8445

  orchestrator:
    uri:  "192.168.0.100"
    port: 8441
```

`provider` propeties contains the settings for the PPA system and services (runnable `.ipynb` files). `sys-name` shouldn't be changed, however you can, but in this case it's your responsibility to have the same system name in the certifiactes!

`sysid` is the ID of the provider system in the AH local cloud if you have registered it manually. If you want to use the `auto-config` (see later), then it will be omitted!

```yaml
provider:
  sys-name: "prototaip"
  uri:      "192.168.0.100"
  port:     9556
  sysid:    0    
```

The `to-file` prop of the `log` enables creating log file, while `path` accepts any UNIX path to set the path for logfiles. It always will be a folder - if it doesn't exists PAA will create it (assuming the it has the required rights)

```yaml
log:
  to-file:  false
  path:     "log"
```

`auto-setup` enables using the sysop certs of the local cloud to automatically setup all settings. It is **!IMPORTANT!** to understand that you have to own sysop certs to use this mode!

`sys-reg` enables to register the provider systems as a new system in the AH local cloud. If you want to manually register it, then disable this setting.
`service-reg` enables to register the provider services - i.e. all `.ipynb` exacutables - as a new service in the AH local cloud. If you want to manually register them, then disable this setting.
`auth-rules` enables to set authorization rules in the AH local cloud. If you want to set them, then disable this setting. If you want to use this setting, then you have to provide a list of ID-s of consumer systems as `consumers` that can consume your services.

```yaml
auto-setup:
  sys-reg:            true
  service-reg:        true
  auth-rules:         true
  consumers:
    - 255
```

Both `certpath` and `nbpath` accept a UNIX path for the certifications and the executable `.ipynb` files, respectively.

```yaml
certpath: "./../certs"

nbpath: "./../files"
```

### Notebook naming restrictions

Notebook naming has the following restriction:

- They can have only specific ASCII characters (uppercase and lowercase alphabet, number, dash or underscore)
- Notebook names have to be unique globally (in this provder system, but not in the local cloud)
- All underscore will be converted to dash, thus if names differ only in dash and underscore characters, then they are not unique
- Names can be maximum 63 characters long

Notebooks will be created as separate services, where filename will be the service name. However, files can be in subfolder or organized in any way within the `nbpath` root folder, the only thing that matters is the uniqueness of the filenames.

### How to handle service I/O in notebooks

- **Input**: Notebook takes the body of the HTTP request that uses the service. Each service is registered in the local cloud which takes JSON body, however it is not mandatory. It is up to you, how to parse the body.
- **Output**: The body of the response can be set in any notebook file. Again it is recommended to be JSON - even it is empty. To set the body, simply create and assign variable `output` in any cell.

For further example see the `files/echo.ipynb` which is recommended to have in your PrototAIp instance for testing purposes.

## Integrate PAA into an existing docker container

The following `DOCKERFILE` snippet helps you to integrate PAA into your image/container. At the end of the snippet you have to change `PORT` according to your specific settings. If your project structured in other way, then you have to adjust the path accordingly.

**!IMPORTANT!** At some point you have to start PAA (`src/main.py`) in your container, typically as the last command.

```Docker
FROM python:3.12

## Pip dependencies
RUN pip install --upgrade pip

# Install production dependencies
COPY requirements.txt /tmp/requirements.txt
COPY client-library-python /tmp/client-library-python
RUN pip install -r /tmp/requirements.txt && \
    rm /tmp/requirements.txt

RUN python -m build /tmp/client-library-python
RUN python -m pip install /tmp/client-library-python/dist/arrowhead-client-0.5.0a0.tar.gz

EXPOSE [PORT]
```

## Test consumer

The cert for the test-consumer must be named as `test-consumer`, must be placed into `certs/test-consumer` in PEM format!

The test consumer does not accept any flags, but provide a CLI to ease its usage. It can only send a dummy JSON message in HTTP POST request to test only one specific service. The defaults settings include consuming an "echo" service, but the test consumer can be tweaked to your specific needs. It doesn't use any config file, all properties are hardcoded in the sourcecode.

- `CONSUMER_ADDR`
- `CONSUMER_ADDR`
- `PROVIDER_SERVICE_NAME` - this one is responsible for consuming the requested service

The CLI displays the system ID of the conusmer, so the suggested testing procedure is the following:

1. Start test-consumer
2. Edit PrototAIp-adapter `consumers` property in `config.yml` accordingly.
3. Start PrototAIp-adapter
4. Run test-consume process in CLI
5. Shut PrototAIp-adapter
6. Exit test-consumer via CLI
