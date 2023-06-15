function collision(head, array) {
for(let i = 0; i < array.length; i++) {
if(head.x == array[i].x && head.y == array[i].y) {
return true;
}
}
return false;
}
