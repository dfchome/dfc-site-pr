<?php
// Router for dfc-api. Every request reaches this file (php -S router script).
$path = parse_url($_SERVER['REQUEST_URI'] ?? '/', PHP_URL_PATH);

if ($path === '/api/google') {
    require __DIR__ . '/google.php';
    exit;
}
if ($path === '/api/health') {
    header('Content-Type: application/json');
    echo '{"ok":true}';
    exit;
}
http_response_code(404);
header('Content-Type: application/json');
echo '{"error":"not found"}';
