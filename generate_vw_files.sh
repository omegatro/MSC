#!/bin/bash

seq 1 10 | parallel --bar ./generate_nlp_set.sh {}
time seq 1 10 | parallel ./generate_bioit_set.sh {}