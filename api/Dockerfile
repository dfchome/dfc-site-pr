# dfc-api: small PHP service for the marketing site's server-side features.
# The web service (Caddy) proxies /api/* here over Railway's private network.
# Secrets come from Railway variables, never from this public repo.
FROM php:8.3-cli-alpine
COPY public /app
# [::] listens on IPv6 (Railway private networking) and IPv4.
CMD ["sh", "-c", "exec php -S [::]:${PORT:-8080} -t /app /app/index.php"]
