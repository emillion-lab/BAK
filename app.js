// ------ разпознаване на международни автобусни направления ------
// Скрейпнатите данни често нямат intl флаг → познаваме по името на града.
var __INTL_RE = /(истанб|istanbul|одрин|edirne|бурса|bursa|измир|izmir|анкара|ankara|анталия|antalya|солун|thessalon|атина|athen|скопие|skopje|битоля|bitola|охрид|ohrid|белград|belgrad|ниш|\bnis\b|нови сад|novi sad|букурещ|bucharest|bucure|русе-букурещ|крайова|craiova|тимишоара|timis|загреб|zagreb|любляна|ljubljan|сараево|saraje|подгорица|podgoric|тирана|tiran|прищина|pristin|priştin|виена|vienna|wien|мюнхен|munich|münchen|берлин|berlin|хамбург|hamburg|кьолн|cologne|köln|щутгарт|stuttgart|франкфурт|frankfurt|дюселдорф|dусseldorf|прага|prague|praha|братислава|bratislav|будапеща|budapest|варшава|warsaw|warszaw|краков|krakow|милано|milan|рим|\broma\b|\brome\b|венеция|venice|venezia|болоня|bologna|торино|turin|неапол|naples|napoli|флоренция|florence|firenze|барселона|barcelona|мадрид|madrid|валенсия|valencia|лисабон|lisbon|порто|porto|париж|paris|лион|lyon|марсилия|marseille|брюксел|brussels|амстердам|amsterdam|ротердам|rotterdam|цюрих|zurich|zürich|женева|geneva|базел|basel|берн|\bbern\b|лондон|london|стокхолм|stockholm|осло|\boslo\b|копенхаген|copenhagen|хелзинки|helsinki|кишинев|chisinau|chişin|киев|kyiv|kiev|одеса|odesa|odessa|москва|moscow)/i;
function isIntlBus(o){
  if(!o) return false;
  if(o.intl === true) return true;
  var txt = [o.origin, o.from, o.name, o.to, o.operator].filter(Boolean).join(' ');
  return __INTL_RE.test(txt);
}
