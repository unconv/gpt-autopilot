const canvas = document.getElementById('game');
const context = canvas.getContext('2d');
canvas.width = 800;
canvas.height = 600;

const box = 20;
let score = 0;

const ground = new Image();
ground.src = 'img/ground.png';

const foodImg = new Image();
foodImg.src = 'img/food.png';

let food = {x: Math.floor(Math.random()*canvas.width/box), y: Math.floor(Math.random()*canvas.height/box)};

let snake = [];
snake[0] = {x: 10, y: 10};
