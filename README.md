# Saeed TV open data

**بيانات مفتوحة ومجانية يستخدمها موقع Saeed TV.** لا مفاتيح، ولا حسابات، ولا جداول زمنية.

## youtube-channels.json
القنوات الرسمية على يوتيوب لمحطات التلفزيون والإذاعة والصحف ووكالات الأنباء، مأخوذة من [Wikidata](https://www.wikidata.org) (خاصية P2397) ومصنّفة باللغة والبلد.

- الرابط: `https://rfliming76.github.io/saeedtv-open-data/data/youtube-channels.json`
- كل صف: `[channelId, name, [languages], [countries], kind]`
  - اللغات بترميز ISO 639-1.
  - إذا لم تُذكر لغة القناة، تؤخذ اللغة الرسمية لبلدها، بشرط أن يكون للبلد لغة أو لغتان فقط.
- لا تُحذف نسخة سليمة أبداً: إذا جاء رد Wikidata ناقصاً (أقل من 500 قناة)، تبقى النسخة السابقة.

## tv/
قنوات تلفزيون مجانية تبث على الهواء (free-to-air)، من قوائم [iptv-org](https://github.com/iptv-org/iptv) المفتوحة، مقسّمة حسب اللغة.

- الفهرس: `https://rfliming76.github.io/saeedtv-open-data/data/tv/index.json` (عدد القنوات في كل لغة)
- لغة واحدة: `data/tv/<lang>.json` (مثل `ar.json` و`pl.json`)
- كل صف: `[name, url, country, [categories], quality, logo, channelId]`
- تبقى القناة فقط إذا تحققت كل هذه الشروط:
  - رابطها https.
  - ليست للبالغين، وليست مغلقة، وليست في قائمة الحظر لدى iptv-org.
  - لا تحتاج متصفحاً خاصاً ولا رابطاً مُحيلاً.
  - قائمة تشغيلها تُفتح من صفحة ويب على موقع آخر (CORS).

  لذلك يستطيع المتصفح تشغيلها مباشرة.
- إذا خرج تشغيل بأقل من 300 قناة صالحة، تبقى النسخة السابقة.

**التحديث:** عند الطلب فقط، من تبويب Actions ← «Build open data» ← Run workflow، أو من زر صفحة حالة Saeed TV. لا يوجد مؤقّت.

## Sources and licenses
- Data: Wikidata, CC0 1.0 (youtube-channels.json); iptv-org lists, CC0 / Unlicense (tv/). The output files keep those terms.
- Code: MIT.
- IMDb, OMDb and other data with restrictive terms are **not** republished here.
