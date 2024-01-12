# Test Cloud

## Certificates

To generate certificates for your core systems, use your local cloud master certificate and the [AH Cert tool]. If you have generated all of them, them put the certs into the corresponding directory: `[coresystem]/certificates`. For example *authorization* certs go into the `authorization/certificates` directory. If you don't own a local cloud yet, then you can create the master cert with the other ones. You can save your master cert to `tools/certs` folder - you'll need it later!

[AH Cert Tool]: https://aitia.ai/hu/downloads/ah-cert-gen/

### Using existing certs

All folders already contain certifactes as placeholder examples, but they can be used as valid certificates with the test cloud, only if all services - including the test cloud itself - run on `192.168.0.100`.

## Settings

You have to configure the core systems for yourself, by changing `application.properties` files in the corresponding directories.

The following settings should be changed accordingly:

- `spring.datasource.url`
- `domain.name`
- `domain.port`
- `server.ssl.key-store-password`
- `server.ssl.key-password`
- `server.ssl.trust-store-password`

Only for authorzation and orchestration:

- `sr_address`
- `sr_port`

## Setup local cloud

1. Execute `docker-compose -f docker-compose-db.yml up -d` and wait for the container to run.
2. Enter the container: `docker exec -it arrowhead-database-paa-test /bin/bash`
3. Execute the following command: `mysql -u root -p`
4. In the MYSQL CLI, run the following quieres:
   1. `CREATE USER 'ah'@'%' IDENTIFIED BY 'arrowhead';`
   2. `GRANT CREATE, ALTER, DROP, INSERT, UPDATE, DELETE, SELECT, REFERENCES, RELOAD on Databases.arrowhead TO 'ah'@'%';`
   3. `FLUSH PRIVILEGES;`
5. Leave the MYSQL CLI and also the docker container.
6. Execute `docker-compose -f docker-compose-core.yml up -d` and wait for the container to run.

## Run local cloud

When you have done wiht setting up the local cloud it is already running. If you have to reboot your machine, you dont have to perform the setup operation again, only execute the following:

1. Execute `docker-compose -f docker-compose-db.yml up -d` and wait for the container to run.
1. Execute `docker-compose -f docker-compose-core.yml up -d` and wait for the container to run.
