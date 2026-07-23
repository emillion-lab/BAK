# Discovery Report — източници за BAK/SEV

curl_cffi наличен: **да**

| Източник | Метод | Работи | Чист JSON | Детайли |
|---|---|:--:|:--:|---|
| Арена 8888 | WordPress REST | ✅ | ✅ | 5 записа чист JSON |
| visitsofia | WordPress/Drupal API | ❌ | — | няма платформено API |
| НДК | WordPress/Drupal API | ❌ | — | няма платформено API |
| theatre.art.bg | WordPress/Drupal API | ❌ | — | няма платформено API |
| bilet.bg | JSON блоб/LD | ❌ | — | нищо структурирано (2 ld+json блока, 733811b) |
| visitsofia | JSON блоб/LD | ❌ | — | нищо структурирано (0 ld+json блока, 24765b) |
| Eventim HTML | JSON блоб | ❌ | — | не се зарежда: <HTTPError 520: '<none>'> |
| Арена 8888 | JSON блоб/LD | ❌ | — | нищо структурирано (0 ld+json блока, 169251b) |
| Eventim API v1 | curl_cffi chrome131 | ✅ | ✅ | 128b ключове: ['facets', 'page', 'products', 'results', 'totalPages', 'totalResults'] / urllib: БЛОКИРАН |
| Eventim API v2 | curl_cffi chrome131 | ✅ | ✅ | 133b ключове: ['facets', 'page', 'productGroups', 'results', 'totalPages', 'totalResults'] / urllib: БЛОКИРАН |
| БДЖ live | curl_cffi chrome131 | ❌ | — | Timeout('Failed to perform, curl: (28) Connection timed out after 20001 milliseconds. See https://curl.se/libcurl/c/libc / urllib: блокиран |
| Eventim HTML | curl_cffi chrome131 | ✅ | — | 450914b / urllib: БЛОКИРАН |

## Печеливши комбинации (чист JSON): 3
- **Арена 8888** → WordPress REST — `https://arenaarmeecsofia.net/wp-json/wp/v2/posts?per_page=5`
- **Eventim API v1** → curl_cffi chrome131 — `https://public-api.eventim.com/websearch/search/api/explorat`
- **Eventim API v2** → curl_cffi chrome131 — `https://public-api.eventim.com/websearch/search/api/explorat`
