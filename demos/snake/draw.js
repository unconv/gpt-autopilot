function draw() {
context.clearRect(0, 0, canvas.width, canvas.height);
context.fillStyle = 'black';
context.fillRect(0, 0, canvas.width, canvas.height);
for(let i = 0; i < snake.length; i++) {
context.fillStyle = (i == 0)?'green':'white';
context.fillRect(snake[i].x*box, snake[i].y*box, box, box);
}
context.fillStyle = 'red';
context.fillRect(food.x*box, food.y*box, box, box);
if(gameOver) {
context.fillStyle = 'white';
context.font = '50px Arial';
context.fillText('Game Over', canvas.width/2, canvas.height/2);
}
}
