let gameOver = false;
function update() {
if(!gameOver) {
let snakeX = snake[0].x;
let snakeY = snake[0].y;
if(direction == 'LEFT') snakeX--;
if(direction == 'UP') snakeY--;
if(direction == 'RIGHT') snakeX++;
if(direction == 'DOWN') snakeY++;

snakeX = snakeX < 0 ? canvas.width/box - 1 : snakeX >= canvas.width/box ? 0 : snakeX;
snakeY = snakeY < 0 ? canvas.height/box - 1 : snakeY >= canvas.height/box ? 0 : snakeY;

if(snakeX == food.x && snakeY == food.y) {
score++;
food = {x: Math.floor(Math.random()*canvas.width/box), y: Math.floor(Math.random()*canvas.height/box)};
} else {
snake.pop();
}

let newHead = {x: snakeX, y: snakeY};

if(collision(newHead, snake)) {
gameOver = true;
}

snake.unshift(newHead);
}
}
