# Saeed TV open data

**بيانات مفتوحة ومجانية يستخدمها موقع Saeed TV.** لا مفاتيح، ولا حسابات، ولا جداول زمنية.

## youtube-channels.json
القنوات الرسمية على يوتيوب لمحطات التلفزيون والإذاعة والصحف ووكالات الأنباء، مأخوذة من [Wikidata](https://www.wikidata.org) (خاصية P2397) ومصنّفة باللغة والبلد.

- الرابط: `https://rfliming76.github.io/saeedtv-open-data/data/youtube-channels.json`
- كل صف: `[channelId, name, [languages], [countries], kind]`
  - اللغات بترميز ISO 639-1.
  - إذا لم تُذكر لغة القناة، تؤخذ اللغة الرسمية لبلدها، بشرط أن يكون للبلد لغة أو لغتان فقط.
- لا تُحذف نسخة سليمة أبداً: إذا جاء رد Wikidata ناقصاً (أقل من 500 قناة)، تبقى النسخة السابقة.

**التحديث:** عند الطلب فقط، من تبويب Actions ← «Build open data» ← Run workflow، أو من زر صفحة حالة Saeed TV. لا يوجد مؤقّت.

## Sources and licenses
- Data: Wikidata, CC0 1.0. The output file is CC0 as well.
- Code: MIT.
- IMDb, OMDb and other data with restrictive terms are **not** republished here.
