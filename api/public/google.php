<?php
// GET /api/google -> {"rating":4.8,"count":63,"url":"..."}
// DFC's Google rating and review count. Google is asked at most once every
// CACHE_TTL seconds; the cached copy is served in between, and the last good
// copy if Google is unreachable. Key: Railway variable GOOGLE_PLACES_KEY.

const PLACE_ID  = 'ChIJZ7xnE0YlaoQRIwPSJ2LbNgc';            // DFC Home Improvement (service-area listing)
const MAPS_URL  = 'https://maps.app.goo.gl/AUjVDsK2nXdHqPy68';
const CACHE     = '/tmp/google-place.json';
const CACHE_TTL = 6 * 3600;

header('Content-Type: application/json');
header('Cache-Control: public, max-age=3600');

function cached() {
    $raw = @file_get_contents(CACHE);
    $data = $raw ? json_decode($raw, true) : null;
    return is_array($data) ? $data : null;
}


$data = cached();
$fresh = $data && (time() - ($data['fetched_at'] ?? 0) < CACHE_TTL);

if (!$fresh) {
    $key = getenv('GOOGLE_PLACES_KEY');
    if ($key) {
        $ch = curl_init('https://places.googleapis.com/v1/places/' . PLACE_ID);
        curl_setopt_array($ch, [
            CURLOPT_RETURNTRANSFER => true,
            CURLOPT_TIMEOUT        => 8,
            CURLOPT_HTTPHEADER     => [
                'X-Goog-Api-Key: ' . $key,
                'X-Goog-FieldMask: rating,userRatingCount',
            ],
        ]);
        $body = curl_exec($ch);
        $code = curl_getinfo($ch, CURLINFO_HTTP_CODE);
        $res  = ($code === 200 && $body) ? json_decode($body, true) : null;
        if (isset($res['rating'], $res['userRatingCount'])) {
            $data = [
                'rating'     => round((float) $res['rating'], 1),
                'count'      => (int) $res['userRatingCount'],
                'url'        => MAPS_URL,
                'fetched_at' => time(),
            ];
            @file_put_contents(CACHE, json_encode($data), LOCK_EX);
        }
    }
}

if (!$data) {
    http_response_code(503);
    echo '{"error":"google data unavailable"}';
    exit;
}
unset($data['fetched_at']);
echo json_encode($data);
