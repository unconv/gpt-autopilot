#include "raylib.h"
#include "includes/snake.h"
#include <stdlib.h>

// Size of our snake and fruit blocks
#define BLOCK_SIZE 20

int main()
{
    // Initialization
    //--------------------------------------------------------------------------------------
    int screenWidth = 800;
    int screenHeight = 600;

    Snake snake;
    initSnake(&snake, screenWidth, screenHeight, BLOCK_SIZE);
    
    Vector2 fruit;
    fruit.x = BLOCK_SIZE * 5;
    fruit.y = BLOCK_SIZE * 5;

    // Raylib window configuration
    InitWindow(screenWidth, screenHeight, "raylib [core] example - basic window");
    SetTargetFPS(15);               // Set our game to run at 60 frames-per-second

    // Main game loop
    while (!WindowShouldClose())    // Detect window close button or ESC key
    {
        // Update
        //----------------------------------------------------------------------------------
        updateSnake(&snake, screenWidth, screenHeight, BLOCK_SIZE, &fruit);
        
        if (checkCollision(&snake)) break;
        
        // Draw
        //----------------------------------------------------------------------------------
        BeginDrawing();

        ClearBackground(RAYWHITE);
        
        // Draw our game elements
        drawSnake(&snake);
        drawFruit(&fruit, BLOCK_SIZE);

        EndDrawing();
        //----------------------------------------------------------------------------------
    }

    // De-Initialization
    //--------------------------------------------------------------------------------------
    CloseWindow();        // Close window and OpenGL context
    //--------------------------------------------------------------------------------------

    return 0;
}
