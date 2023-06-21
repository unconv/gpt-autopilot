#!/bin/bash

gcc -o snake_game src/main.c src/snake.c -lraylib -lGL -lm -lpthread -ldl -lrt -lX11
