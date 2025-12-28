# https://just.systems/man/en/


# REQUIRES

docker := require("docker")
find := require("find")
rm := require("rm")
uv := require("uv")


# SETTINGS

set dotenv-load := true


# VARIABLES

PACKAGE := "tempestwx"
REPOSITORY := "tempestwx"
SOURCES := "src"
TESTS := "tests"


# DEFAULTS

default:
    @just --list


# IMPORTS

import 'tasks/check.just'
import 'tasks/clean.just'
import 'tasks/format.just'
import 'tasks/install.just'
import 'tasks/package.just'
import 'tasks/release.just'
