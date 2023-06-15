function addProduct(event) {
   event.preventDefault();
   const form = document.querySelector('.add-product-form');
   const product = {
      name: form.elements.name.value,
      quantity: form.elements.quantity.value,
      price: form.elements.price.value
   };
   fetch('add_product.php', {
      method: 'POST',
      headers: {
         'Content-Type': 'application/json',
      },
      body: JSON.stringify(product),
   })
   .then((response) => response.json())
   .then((data) => {
      if (data.success) {
         form.reset();
         loadProducts();
      }
   });
}

function loadProducts() {
   const productTable = document.querySelector('.product-table tbody');
   productTable.innerHTML = '';
   fetch('get_products.php')
   .then((response) => response.json())
   .then((data) => {
      let total = 0;
      data.products.forEach((product) => {
         productTable.innerHTML += `<tr><td>${product.name}</td><td>${product.quantity}</td><td>${product.price}</td></tr>`;
         total += parseFloat(product.price);
      });
      productTable.innerHTML += `<tr><th colspan='2'>Total Price</th><td>${total.toFixed(2)}</td></tr>`;
   });
}

addEventListener('DOMContentLoaded', loadProducts);
