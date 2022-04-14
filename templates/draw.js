var canvas;
var context;
var x1 = 0;
var x2 = 0;
var y1 = 0;
var y2 = 0;
var paint = false;
var curColor = "#FF5733";

/**
    - Preparing the Canvas : Basic functions
**/
function drawCanvas() {

    canvas = document.getElementById('canvas');
    context = document.getElementById('canvas').getContext("2d");

    $('#canvas').mousedown(function (e) {
        var mouseX = e.pageX - this.offsetLeft;
        var mouseY = e.pageY - this.offsetTop;

        paint = true;
        addClick(e.pageX - this.offsetLeft, e.pageY - this.offsetTop);
        redraw();
    });

    $('#canvas').mousemove(function (e) {
        if (paint) {
            addClick(e.pageX - this.offsetLeft, e.pageY - this.offsetTop, true);
            redraw();
        }
    });

    $('#canvas').mouseup(function (e) {
        paint = false;
    });
}

/**
    - Saves the click postition
**/
function addClick(x, y, dragging) {
    x2 = x;
    y2 = y;
    if (!dragging) {
        x1 = x;
        y1 = y;
    }
}

/**
    - Clear the canvas and redraw
**/
function redraw() {
    
    context.clearRect(0, 0, context.canvas.width, context.canvas.height); // Clears the canvas
    context.strokeStyle = curColor;
    context.lineJoin = "round";
    context.lineWidth = 3;
    context.beginPath();
    context.rect(x1, y1, x2-x1, y2-y1)
    context.closePath();
    context.stroke();

}

/**
    - Encodes the image into a base 64 string.
    - Add the string to an hidden tag of the form so Flask can reach it.
**/
function save() {
    var image = new Image();
    var url = document.getElementById('url');
    image.id = "pic";
    image.src = canvas.toDataURL();
    url.x1 = x1;
    url.x2 = x2;
    url.y1 = y1;
    url.y2 = y2;
}
