document.getElementById('jokeButton').addEventListener('click', function() {
    fetch('/api/joke')
       .then(response => response.json())
       .then(data => document.getElementById('joke').innerText = data);
});
