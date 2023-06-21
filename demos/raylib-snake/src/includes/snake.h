#ifndef SNAKE_H
#define SNAKE_H

#include "raylib.h"
#include <stdbool.h>

#define MAX_SNAKE_BODY 256

typedef struct Snake {
    Vector2 position;
    Vector2 direction;
    Vector2 body[MAX_SNAKE_BODY];
    int speed;
    int bodyCount;
    int size;
    Color color;
} Snake;

void initSnake(Snake *snake, int screenWidth, int screenHeight, int blockSize);
void updateSnake(Snake *snake, int screenWidth, int screenHeight, int blockSize, Vector2 *fruit);
bool checkCollision(Snake *snake);
void drawSnake(Snake *snake);
void drawFruit(Vector2 *fruitPosition, int blockSize);

#endif
