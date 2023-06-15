document.addEventListener('DOMContentLoaded', function () {
    document.querySelector('button').addEventListener('click', function () {
        fetch('/joke').then(response => response.json()).then(data => {
            document.querySelector('#joke').innerHTML = data.joke;
        });
    });
});
