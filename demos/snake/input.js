let direction;
document.addEventListener('keydown', changeDirection);
function changeDirection(event) {
let key = event.keyCode;
if( key == 37 && direction != 'RIGHT') direction = 'LEFT';
else if(key == 38 && direction != 'DOWN') direction = 'UP';
else if(key == 39 && direction != 'LEFT') direction = 'RIGHT';
else if(key == 40 && direction != 'UP') direction = 'DOWN';
}
