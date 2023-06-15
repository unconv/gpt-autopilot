#include <raylib.h>

#define MOVEMENT_SPEED 4

int main() {
    const int screenWidth = 800;
    const int screenHeight = 450;

    InitWindow(screenWidth, screenHeight, "Pong Game");
    SetTargetFPS(60);

    Rectangle player1 = {0, screenHeight / 2 - 50, 10, 100};
    Rectangle player2 = {screenWidth - 10, screenHeight / 2 - 50, 10, 100};
    Vector2 ballPosition = {screenWidth / 2, screenHeight / 2};
    Vector2 ballSpeed = {3, 3};
    int player1Score = 0;
    int player2Score = 0;

    while (!WindowShouldClose()) {
        if(IsKeyDown(KEY_W)) player1.y -= MOVEMENT_SPEED;
        if(IsKeyDown(KEY_S)) player1.y += MOVEMENT_SPEED;
        if(IsKeyDown(KEY_UP)) player2.y -= MOVEMENT_SPEED;
        if(IsKeyDown(KEY_DOWN)) player2.y += MOVEMENT_SPEED;

        if(CheckCollisionRecs(player1, (Rectangle){ballPosition.x, ballPosition.y, 10, 10})) ballSpeed.x *= -1;
        if(CheckCollisionRecs(player2, (Rectangle){ballPosition.x, ballPosition.y, 10, 10})) ballSpeed.x *= -1;

        ballPosition.x += ballSpeed.x;
        ballPosition.y += ballSpeed.y;

        if(ballPosition.y >= screenHeight || ballPosition.y <= 0) ballSpeed.y *= -1;

        if(ballPosition.x >= screenWidth) {
            ballPosition = (Vector2){screenWidth / 2, screenHeight / 2};
            ballSpeed.x *= -1;
            player1Score++;
        }

        if(ballPosition.x <= 0) {
            ballPosition = (Vector2){screenWidth / 2, screenHeight / 2};
            ballSpeed.x *= -1;
            player2Score++;
        }

        BeginDrawing();
        ClearBackground(BLACK);
        DrawRectangleRec(player1, WHITE);
        DrawRectangleRec(player2, WHITE);
        DrawCircleV(ballPosition, 10, WHITE);
        DrawText(TextFormat("%i", player1Score), 20, 20, 20, WHITE);
        DrawText(TextFormat("%i", player2Score), screenWidth - 40, 20, 20, WHITE);
        EndDrawing();
    }

    CloseWindow();
    return 0;
}
