<?php
$products = [];

if(file_exists('products.json')) {
   $products = json_decode(file_get_contents('products.json'), true);
}

$product = json_decode(file_get_contents('php://input'), true);
$products[] = $product;

file_put_contents('products.json', json_encode($products));

echo json_encode(['success' => true]);
?>
