<!DOCTYPE html>
<html>
<head>
   <title>Inventory System</title>
   <link rel='stylesheet' type='text/css' href='css/styles.css'>
</head>
<body>
   <div class='header'>Inventory System</div>
   <form class='add-product-form' onsubmit='addProduct(event)'>
      <input type='text' name='name' placeholder='Product Name'>
      <input type='number' name='quantity' placeholder='Quantity'>
      <input type='number' step='0.01' name='price' placeholder='Price'>
      <button type='submit'>Add Product</button>
   </form>

   <table class='product-table'>
      <thead>
         <tr>
            <th>Product Name</th>
            <th>Quantity</th>
            <th>Price</th>
         </tr>
      </thead>
      <tbody>
      </tbody>
   </table>

   <script src='js/script.js'></script>
</body>
</html>
