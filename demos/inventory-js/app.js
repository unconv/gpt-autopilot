document.addEventListener('DOMContentLoaded', function () {
  var form = document.getElementById('productForm');
  var table = document.getElementById('productTable');
  var totalArea = document.getElementById('totalPrice');
  var products = JSON.parse(localStorage.getItem('products')) || [];

  products.forEach(function(product) {
    addProductToTable(product);
    updateTotalPrice(product);
  })

  form.addEventListener('submit', function (e) {
    e.preventDefault();

    var name = form.productName.value;
    var quantity = parseInt(form.quantity.value, 10);
    var price = parseFloat(form.price.value);

    var product = {
      name: name,
      quantity: quantity,
      price: price
    };

    products.push(product);
    localStorage.setItem('products', JSON.stringify(products));

    addProductToTable(product);
    updateTotalPrice(product);

    form.productName.value = '';
    form.quantity.value = '';
    form.price.value = '';
  });

  function addProductToTable(product) {
    var row = table.insertRow(-1);
    row.insertCell(0).textContent = product.name;
    row.insertCell(1).textContent = product.quantity;
    row.insertCell(2).textContent = product.price;
  }

  function updateTotalPrice(product) {
    var total = parseFloat(totalArea.textContent);
    total += product.price * product.quantity;
    totalArea.textContent = total.toFixed(2);
  }
});
