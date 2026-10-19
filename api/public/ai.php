<?php
/**
 * AI Kitchen Inspiration tool: server side.
 *
 *   POST /api/ai-preview      photo + prompt -> Google's image model (key never leaves the server)
 *   POST /api/ai-save         park one generated design so the lead email can link to it
 *   GET  /api/ai-design/NAME  serve a parked design
 *
 * Ported from the Fox Remodeling / McManus builds. Differences on Railway:
 *  - the key is the GOOGLE_AI_KEY Railway variable, not a private PHP file;
 *  - the visitor's IP arrives in X-Real-IP / X-Forwarded-For (we sit behind
 *    Railway's edge and the site's Caddy), so REMOTE_ADDR is useless here;
 *  - designs are written to the Railway volume at /data (survives deploys),
 *    falling back to /tmp if no volume is mounted.
 */
declare(strict_types=1);

function ai_out(array $body, int $code = 200): never {
    http_response_code($code);
    header('Content-Type: application/json');
    header('X-Content-Type-Options: nosniff');
    echo json_encode($body);
    exit;
}

function ai_client_ip(): string {
    $real = trim((string)($_SERVER['HTTP_X_REAL_IP'] ?? ''));
    if ($real !== '') return $real;
    $xff = (string)($_SERVER['HTTP_X_FORWARDED_FOR'] ?? '');
    if ($xff !== '') return trim(explode(',', $xff)[0]);
    return (string)($_SERVER['REMOTE_ADDR'] ?? '0.0.0.0');
}

/* Every generation costs money and the endpoint is public, so: 12 an hour
   per visitor, and a hard ceiling for the whole site per day. */
function ai_throttle(string $bucket, int $perHour, int $perDay): void {
    $dir = sys_get_temp_dir() . '/dfc-ai';
    @mkdir($dir, 0700, true);
    $mine = $dir . '/' . $bucket . '-' . hash('sha256', ai_client_ip() . date('Y-m-d-H')) . '.cnt';
    $n = (int)@file_get_contents($mine);
    if ($n >= $perHour) ai_out(['error' => 'You have reached the limit for this hour. Please try again later.'], 429);
    $all = $dir . '/' . $bucket . '-all-' . date('Y-m-d') . '.cnt';
    $t = (int)@file_get_contents($all);
    if ($t >= $perDay) ai_out(['error' => 'The design tool is very busy today. Please try again tomorrow, or give us a call.'], 429);
    @file_put_contents($mine, (string)($n + 1), LOCK_EX);
    @file_put_contents($all, (string)($t + 1), LOCK_EX);
}

function ai_store(): string {
    $root = is_dir('/data') && is_writable('/data') ? '/data/ai-designs' : sys_get_temp_dir() . '/ai-designs';
    @mkdir($root, 0755, true);
    return $root;
}

$path = parse_url($_SERVER['REQUEST_URI'] ?? '/', PHP_URL_PATH);

/* ── serve a saved design ─────────────────────────────────────────────── */
if (preg_match('#^/api/ai-design/([0-9]{8}-[0-9a-f]{16}\.(png|jpg))$#', $path, $m)) {
    $file = ai_store() . '/' . $m[1];
    if (!is_file($file)) { http_response_code(404); exit; }
    header('Content-Type: ' . ($m[2] === 'png' ? 'image/png' : 'image/jpeg'));
    header('Cache-Control: public, max-age=31536000, immutable');
    header('X-Robots-Tag: noindex');
    readfile($file);
    exit;
}

if (($_SERVER['REQUEST_METHOD'] ?? '') !== 'POST') ai_out(['error' => 'POST only'], 405);
$in = json_decode((string)file_get_contents('php://input'), true) ?: [];

/* ── generate ─────────────────────────────────────────────────────────── */
if ($path === '/api/ai-preview') {
    $key   = (string)getenv('GOOGLE_AI_KEY');
    $model = (string)(getenv('GOOGLE_AI_MODEL') ?: 'gemini-2.5-flash-image');
    if ($key === '') ai_out(['error' => 'The design tool is not configured yet.'], 500);

    $prompt = (string)($in['prompt'] ?? '');
    $image  = (string)($in['image'] ?? '');
    $mime   = (string)($in['mimeType'] ?? 'image/jpeg');
    if ($prompt === '' || $image === '') ai_out(['error' => 'Missing image or prompt.'], 400);
    if (!in_array($mime, ['image/jpeg', 'image/png', 'image/webp', 'image/heic'], true)) {
        ai_out(['error' => 'That image format is not supported. Please use a JPG or PNG.'], 400);
    }
    if (strlen($image) > 8 * 1024 * 1024) ai_out(['error' => 'That photo is too large.'], 413);
    if (strlen($prompt) > 4000) ai_out(['error' => 'Those notes are too long.'], 413);

    ai_throttle('gen', 12, 300);

    $payload = json_encode([
        'contents' => [['parts' => [
            ['text' => $prompt],
            ['inlineData' => ['mimeType' => $mime, 'data' => $image]],
        ]]],
        'generationConfig' => ['responseModalities' => ['IMAGE']],
    ]);
    $ch = curl_init("https://generativelanguage.googleapis.com/v1beta/models/{$model}:generateContent?key={$key}");
    curl_setopt_array($ch, [
        CURLOPT_RETURNTRANSFER => true,
        CURLOPT_POST           => true,
        CURLOPT_HTTPHEADER     => ['Content-Type: application/json'],
        CURLOPT_POSTFIELDS     => $payload,
        CURLOPT_TIMEOUT        => 120,
    ]);
    $res = curl_exec($ch);
    if ($res === false) ai_out(['error' => 'The design service did not respond. Please try again.'], 502);
    $code = (int)curl_getinfo($ch, CURLINFO_HTTP_CODE);
    http_response_code($code);
    header('Content-Type: application/json');
    echo $res;   // passed straight through: the page reads candidates[].content.parts[].inlineData
    exit;
}

/* ── save ─────────────────────────────────────────────────────────────── */
if ($path === '/api/ai-save') {
    ai_throttle('save', 12, 300);
    $data = (string)($in['image'] ?? '');
    if ($data === '') ai_out(['error' => 'Nothing to save.'], 400);
    if (strlen($data) > 12 * 1024 * 1024) ai_out(['error' => 'Image too large.'], 413);
    $raw = base64_decode($data, true);
    if ($raw === false || $raw === '') ai_out(['error' => 'Image could not be read.'], 400);
    // Trust the bytes, never the declared type.
    $info = @getimagesizefromstring($raw);
    $ext  = match ($info['mime'] ?? '') { 'image/png' => 'png', 'image/jpeg' => 'jpg', default => null };
    if ($ext === null) ai_out(['error' => 'Only PNG or JPEG can be saved.'], 400);

    $root = ai_store();
    // Housekeeping: a design only needs to outlive the follow-up call.
    foreach (glob($root . '/*.{png,jpg}', GLOB_BRACE) ?: [] as $old) {
        if (filemtime($old) < time() - 90 * 86400) @unlink($old);
    }
    $name = date('Ymd') . '-' . bin2hex(random_bytes(8)) . '.' . $ext;
    if (@file_put_contents($root . '/' . $name, $raw) === false) ai_out(['error' => 'Could not save the image.'], 500);
    ai_out(['ok' => true, 'url' => '/api/ai-design/' . $name]);
}

ai_out(['error' => 'not found'], 404);
