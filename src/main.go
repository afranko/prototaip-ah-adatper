package main

import (
	"flag"
	"os"
	"path/filepath"
	"strings"
	"time"

	"github.com/rs/zerolog"
	"github.com/rs/zerolog/log"
	"gopkg.in/yaml.v3"
)

type coreSys struct {
	Addr string
	Port int
}

type system struct {
	SerivceRegistry coreSys `yaml:"service-registry"`
	Authorizator    coreSys
	Orchestrator    coreSys
}

type cLog struct {
	ToFile bool `yaml:"to-file"`
	Path   string
}

type config struct {
	CLog    cLog   `yaml:"log"`
	Systems system `yaml:"systems"`
}

func initApp() config {
	/* ---------------------------- COMMAND LINE ARG ---------------------------- */
	cPath := flag.String("c", "config.yml", "Path for the config file (relative to the application)")
	dDebug := flag.Bool("D", false, "Turn on debug mode for logging")
	flag.Parse()

	/* ------------------------------ SET LOG LEVEL ----------------------------- */
	zerolog.SetGlobalLevel(zerolog.InfoLevel)
	if *dDebug {
		zerolog.SetGlobalLevel(zerolog.DebugLevel)
	}

	log.Debug().Str("config-file-path", *cPath).Send()

	/* -------------------------------- READ FILE ------------------------------- */
	f, err := os.ReadFile(*cPath)

	if err != nil {
		log.Fatal().Err(err).Msg("Config file cannot be opened!")
	}

	var c config
	err = yaml.Unmarshal(f, &c)
	if err != nil {
		log.Fatal().Err(err).Msg("Config file cannot be unmarshaled!")
	}

	log.Debug().Interface("config", c).Msg("Config file has been succesfully read!")

	return c
}

func registerService() {
}

func main() {
	c := initApp()

	/* ------------------------------ SET FILE LOG ------------------------------ */

	if c.CLog.ToFile {
		/* ------------------------------ OPEN LOG FILE ----------------------------- */
		p := strings.TrimPrefix(c.CLog.Path, "/")
		p = strings.TrimSuffix(p, "/")

		if err := os.MkdirAll(filepath.Join(p), 0770); err != nil {
			log.Fatal().Err(err).Msg("Desired log directory cannot be used!")
		}

		l, err := os.Create(filepath.Join(p, time.Now().Format(time.RFC3339Nano)+".log"))

		if err != nil {
			log.Fatal().Err(err).Msg("Log file cannot be created!")
		}

		defer l.Close()

		/* ------------------------------- SET LOGGERS ------------------------------ */
		consoleWriter := zerolog.ConsoleWriter{Out: os.Stdout}
		multi := zerolog.MultiLevelWriter(consoleWriter)

		log.Logger = zerolog.New(multi).With().Timestamp().Logger()
	}

	log.Info().Msg("Application has been started!")
	// registerService()
}
