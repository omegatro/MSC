#!/bin/bash

time seq 1 10 | parallel ./generate_nlp_set.sh {}
time seq 1 10 | parallel ./generate_bioit_set.sh {}