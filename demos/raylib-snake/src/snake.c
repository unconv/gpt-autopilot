#include "includes/snake.h"
#include <stdlib.h>
#include <string.h>

void initSnake(Snake *snake, int screenWidth, int screenHeight, int blockSize) {
    snake->position = (Vector2){screenWidth / 2, screenHeight / 2};
    snake->direction = (Vector2){blockSize, 0};
    snake->speed = blockSize;
    snake->bodyCount = 1;
    snake->size = blockSize;
    snake->color = GREEN;

    for(int i = 0; i < MAX_SNAKE_BODY; i++) {
        snake->body[i] = (Vector2){0, 0};
    }
}

void updateSnake(Snake *snake, int screenWidth, int screenHeight, int blockSize, Vector2 *fruit) {
    if (IsKeyPressed(KEY_RIGHT)) snake->direction = (Vector2){blockSize, 0};
    if (IsKeyPressed(KEY_LEFT)) snake->direction = (Vector2){-blockSize, 0};
    if (IsKeyPressed(KEY_UP)) snake->direction = (Vector2){0, -blockSize};
    if (IsKeyPressed(KEY_DOWN)) snake->direction = (Vector2){0, blockSize};

    // Move snake body
    for (int i = snake->bodyCount - 1; i > 0; i--) {
        snake->body[i] = snake->body[i-1];
    }

    // Move snake head
    snake->position.x += snake->direction.x;
    snake->position.y += snake->direction.y;

    // Wrap around screen edges
    if (snake->position.x >= screenWidth) {
        snake->position.x = 0;
    } else if (snake->position.x < 0) {
        snake->position.x = screenWidth - blockSize;
    } else if (snake->position.y >= screenHeight) {
        snake->position.y = 0;
    } else if (snake->position.y < 0) {
        snake->position.y = screenHeight - blockSize;
    }

    // Check fruit collision
    if(snake->position.x == fruit->x && snake->position.y == fruit->y) {
        snake->bodyCount++;
        fruit->x = GetRandomValue(0, (screenWidth / blockSize) - 1) * blockSize;
        fruit->y = GetRandomValue(0, (screenHeight / blockSize) - 1) * blockSize;
    }

    // Update head position to body
    snake->body[0] = snake->position;
}

bool checkCollision(Snake *snake) {
    for(int i = 1; i < snake->bodyCount; i++) {
        if(snake->body[0].x == snake->body[i].x && snake->body[0].y == snake->body[i].y) {
            return true;
        }
    }
    return false;
}

void drawSnake(Snake *snake) {
    for(int i = 0; i < snake->bodyCount; i++) {
        DrawRectangleV(snake->body[i], (Vector2){snake->size, snake->size}, snake->color);
    }
}

void drawFruit(Vector2 *fruitPosition, int blockSize) {
    DrawRectangleV(*fruitPosition, (Vector2){blockSize, blockSize}, RED);
}
