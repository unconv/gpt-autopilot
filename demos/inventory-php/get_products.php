<?php
header('Content-Type: application/json');

if(file_exists('products.json')) {
   $products = json_decode(file_get_contents('products.json'), true);
   echo json_encode(['products' => $products]);
} else {
   echo json_encode(['products' => []]);
}
?>
