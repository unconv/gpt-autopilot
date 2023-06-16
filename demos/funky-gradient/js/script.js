document.body.addEventListener('mousemove', function (e) {
  var x = e.pageX - this.offsetLeft;
  var y = e.pageY - this.offsetTop;
  var xc = Math.round(x / this.offsetWidth * 255);
  var yc = Math.round(y / this.offsetHeight * 255);
  this.style.background = 'linear-gradient(' + xc + 'deg, rgb(100,' + yc + ',150), rgb(' + xc + ',' + yc + ',100))';
});
