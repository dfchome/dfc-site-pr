<?php
// Router for dfc-api. Every request reaches this file (php -S router script).
$path = parse_url($_SERVER['REQUEST_URI'] ?? '/', PHP_URL_PATH);

if ($path === '/api/google') {
    require __DIR__ . '/google.php';
    exit;
}
if ($path === '/api/ai-preview' || $path === '/api/ai-save' || str_starts_with($path, '/api/ai-design/')) {
    require __DIR__ . '/ai.php';
    exit;
}
if ($path === '/api/health') {
    // Also reports the caller's own IP as this service sees it, so we can
    // confirm the per-visitor limits key on the real visitor (not the proxy).
    $src = !empty($_SERVER['HTTP_X_REAL_IP']) ? 'x-real-ip' : (!empty($_SERVER['HTTP_X_FORWARDED_FOR']) ? 'x-forwarded-for' : 'remote-addr');
    $ip  = $_SERVER['HTTP_X_REAL_IP'] ?? (isset($_SERVER['HTTP_X_FORWARDED_FOR']) ? trim(explode(',', $_SERVER['HTTP_X_FORWARDED_FOR'])[0]) : ($_SERVER['REMOTE_ADDR'] ?? ''));
    header('Content-Type: application/json');
    header('Cache-Control: no-store');
    echo json_encode(['ok' => true, 'you' => $ip, 'via' => $src]);
    exit;
}
http_response_code(404);
header('Content-Type: application/json');
echo '{"error":"not found"}';
