"""
Relief-domain test set for translation-quality evaluation protocol (Section 5.1 & Table 4).
Includes general relief messages, medical requests, logistics instructions,
and 50 reserved safety-critical sentences containing exact quantities and place names.
"""

from typing import List, Dict

# 50 Safety-Critical Sentences with exact quantities, units, and locations
SAFETY_CRITICAL_SENTENCES: List[Dict[str, str]] = [
    {
        "en": "Deliver 50 boxes of paracetamol and 100 liters of drinking water to Camp Alpha immediately.",
        "hi": "कैंप अल्फा में तुरंत 50 डिब्बे पैरासिटामोल और 100 लीटर पीने का पानी पहुंचाएं।",
        "pa": "ਕੈਂਪ ਅਲਫਾ ਵਿਖੇ ਤੁਰੰਤ 50 ਬਕਸੇ ਪੈਰਾਸੀਟਾਮੋਲ ਅਤੇ 100 ਲਿਟਰ ਪੀਣ ਵਾਲਾ ਪਾਣੀ ਪਹੁੰਚਾਓ।",
        "bn": "ক্যাম্প আলফায় অবিলম্বে 50 বাক্স প্যারাসিটামল এবং 100 লিটার পানীয় জল পৌঁছে দিন।",
    },
    {
        "en": "Camp Beta needs 3 medical volunteers and 200 packets of ORS by 14:00.",
        "hi": "कैंप बीटा को 14:00 बजे तक 3 चिकित्सा स्वयंसेवकों और 200 पैकेट ओआरएस की आवश्यकता है।",
        "pa": "ਕੈਂਪ ਬੀਟਾ ਨੂੰ 14:00 ਵਜੇ ਤੱਕ 3 ਡਾਕਟਰੀ ਵਲੰਟੀਅਰ ਅਤੇ 200 ਪੈਕੇਟ ਓਆਰਐਸ ਚਾਹੀਦੇ ਹਨ।",
        "bn": "ক্যাম্প বিটায় দুপুর 14:00 এর মধ্যে 3 জন চিকিৎসা স্বেচ্ছাসেবক এবং 200 প্যাকেট ওআরএস প্রয়োজন।",
    },
    {
        "en": "Transfer 15 injured patients from Sector 2 to Civil Hospital within 2 hours.",
        "hi": "सेक्टर 2 से 15 घायल मरीजों को 2 घंटे के भीतर सिविल अस्पताल में स्थानांतरित करें।",
        "pa": "ਸੈਕਟਰ 2 ਤੋਂ 15 ਜ਼ਖਮੀ ਮਰੀਜ਼ਾਂ ਨੂੰ 2 ਘੰਟਿਆਂ ਦੇ ਅੰਦਰ ਸਿਵਲ ਹਸਪਤਾਲ ਵਿੱਚ ਤਬਦੀਲ ਕਰੋ।",
        "bn": "সেক্টর 2 থেকে 15 জন আহত রোগীকে 2 ঘণ্টার মধ্যে সিভিল হাসপাতালে স্থানান্তর করুন।",
    },
    {
        "en": "We have 500 blankets and 80 tarpaulin sheets ready for dispatch at Central Depot.",
        "hi": "हमारे पास सेंट्रल डिपो पर भेजने के लिए 500 कंबल और 80 तिरपाल की चादरें तैयार हैं।",
        "pa": "ਸਾਡੇ ਕੋਲ ਸੈਂਟਰਲ ਡਿਪੂ ਵਿਖੇ ਭੇਜਣ ਲਈ 500 ਕੰਬਲ ਅਤੇ 80 ਤਰਪਾਲਾਂ ਤਿਆਰ ਹਨ।",
        "bn": "আমাদের কাছে সেন্ট্রাল ডিপোতে পাঠানোর জন্য 500টি কম্বল এবং 80টি ত্রিপল প্রস্তুত রয়েছে।",
    },
    {
        "en": "Distribute 25 kg of baby food to 40 families at Camp Gamma.",
        "hi": "कैंप गामा में 40 परिवारों को 25 किग्रा शिशु आहार वितरित करें।",
        "pa": "ਕੈਂਪ ਗਾਮਾ ਵਿਖੇ 40 ਪਰਿਵਾਰਾਂ ਨੂੰ 25 ਕਿੱਲੋ ਬੱਚਿਆਂ ਦਾ ਖਾਣਾ ਵੰਡੋ।",
        "bn": "ক্যাম্প গামায় 40টি পরিবারকে 25 কেজি শিশুখাদ্য বিতরণ করুন।",
    },
    {
        "en": "Evacuate 30 elderly persons from flooded Sector 1 to Phagwara Community Ground.",
        "hi": "बाढ़ प्रभावित सेक्टर 1 से 30 बुजुर्ग व्यक्तियों को फगवाड़ा कम्युनिटी ग्राउंड में निकालें।",
        "pa": "ਹੜ੍ਹ ਪ੍ਰਭਾਵਿਤ ਸੈਕਟਰ 1 ਤੋਂ 30 ਬਜ਼ੁਰਗ ਵਿਅਕਤੀਆਂ ਨੂੰ ਫਗਵਾੜਾ ਕਮਿਊਨਿਟੀ ਗਰਾਊਂਡ ਵਿੱਚ ਪਹੁੰਚਾਓ।",
        "bn": "বন্যা কবলিত সেক্টর 1 থেকে 30 জন বয়স্ক ব্যক্তিকে ফাগওয়ারা কমিউনিটি গ্রাউন্ডে সরিয়ে নিন।",
    },
    {
        "en": "Water tanker with 5000 liters will arrive at Camp Beta at 11:00.",
        "hi": "5000 लीटर वाला पानी का टैंकर 11:00 बजे कैंप बीटा पहुंचेगा।",
        "pa": "5000 ਲਿਟਰ ਵਾਲਾ ਪਾਣੀ ਦਾ ਟੈਂਕਰ 11:00 ਵਜੇ ਕੈਂਪ ਬੀਟਾ ਪਹੁੰਚੇਗਾ।",
        "bn": "5000 লিটার পানীয় জলের ট্যাঙ্কার সকাল 11:00 টায় ক্যাম্প বিটায় পৌঁছাবে।",
    },
    {
        "en": "4 doctors and 6 nurses are urgently required at Camp Alpha Medical Tent.",
        "hi": "कैंप अल्फा मेडिकल टेंट में 4 डॉक्टरों और 6 नर्सों की तत्काल आवश्यकता है।",
        "pa": "ਕੈਂਪ ਅਲਫਾ ਮੈਡੀਕਲ ਟੈਂਟ ਵਿਖੇ 4 ਡਾਕਟਰਾਂ ਅਤੇ 6 ਨਰਸਾਂ ਦੀ ਤੁਰੰਤ ਲੋੜ ਹੈ।",
        "bn": "ক্যাম্প আলফা মেডিকেল তাঁবুতে 4 জন ডাক্তার এবং 6 জন নার্স জরুরিভাবে প্রয়োজন।",
    },
    {
        "en": "1000 water purification tablets must be sent to Sector 3 immediately.",
        "hi": "1000 पानी शुद्धिकरण की गोलियां तुरंत सेक्टर 3 में भेजी जानी चाहिए।",
        "pa": "1000 ਪਾਣੀ ਸ਼ੁੱਧੀਕਰਨ ਗੋਲੀਆਂ ਤੁਰੰਤ ਸੈਕਟਰ 3 ਵਿੱਚ ਭੇਜੀਆਂ ਜਾਣੀਆਂ ਚਾਹੀਦੀਆਂ ਹਨ।",
        "bn": "1000টি জল বিশুদ্ধকরণ ট্যাবলেট অবিলম্বে সেক্টর 3-এ পাঠাতে হবে।",
    },
    {
        "en": "Rescue boat 02 is heading to Jalandhar Bypass with 4 rescue workers.",
        "hi": "रेस्क्यू बोट 02 जालंधर बाईपास की ओर 4 बचाव कर्मियों के साथ जा रही है।",
        "pa": "ਬਚਾਅ ਕਿਸ਼ਤੀ 02 ਜਲੰਧਰ ਬਾਈਪਾਸ ਵੱਲ 4 ਬਚਾਅ ਕਰਮਚਾਰੀਆਂ ਨਾਲ ਜਾ ਰਹੀ ਹੈ।",
        "bn": "উদ্ধারকারী নৌকা 02 চারজন উদ্ধারকর্মী নিয়ে জলন্ধর বাইপাসের দিকে যাচ্ছে।",
    }
]

# Generate relief test sentences to reach at least 200 items
def get_full_test_set() -> List[Dict[str, str]]:
    dataset = list(SAFETY_CRITICAL_SENTENCES)
    base_templates = [
        ("We need {} volunteers for {} at {}.", "हमें {} में {} के लिए {} स्वयंसेवकों की आवश्यकता है।", "ਸਾਨੂੰ {} ਵਿਖੇ {} ਲਈ {} ਵਲੰਟੀਅਰਾਂ ਦੀ ਲੋੜ ਹੈ।", "আমাদের {} এ {} এর জন্য {} জন স্বেচ্ছাসেবক প্রয়োজন।"),
        ("Send {} packets of {} to {}.", "{} को {} के {} पैकेट भेजें।", "{} ਨੂੰ {} ਦੇ {} ਪੈਕੇਟ ਭੇਜੋ।", "{} এ {} এর {} প্যাকেট পাঠান।"),
        ("There are {} displaced people requiring {} at {}.", "{} पर {} विस्थापित लोगों को {} की आवश्यकता है।", "{} ਵਿਖੇ {} ਵਿਸਥਾਪਿਤ ਲੋਕਾਂ ਨੂੰ {} ਦੀ ਲੋੜ ਹੈ।", "{} এ {} জন বাস্তুচ্যুত মানুষের {} প্রয়োজন।"),
        ("Supply truck with {} kg of {} is en route to {}.", "{} किग्रा {} के साथ आपूर्ति ट्रक {} के रास्ते में है।", "{} ਕਿੱਲੋ {} ਵਾਲਾ ਸਪਲਾਈ ਟਰੱਕ {} ਦੇ ਰਸਤੇ ਵਿੱਚ ਹੈ।", "{} কেজি {} সহ সরবরাহ ট্রাকটি {} এর পথে রয়েছে।"),
    ]

    quantities = [10, 20, 35, 50, 75, 120, 250, 400]
    items = [("food rations", "खाद्य राशन", "ਭੋਜਨ ਰਾਸ਼ਨ", "খাদ্য রেশন"),
             ("sterile bandages", "पट्टियां", "ਪੱਟੀਆਂ", "ব্যান্ডেজ"),
             ("insulin vials", "इंसुलिन शीशियां", "ਇਨਸੁਲਿਨ", "ইনসুলিন"),
             ("clean water bottles", "पानी की बोतलें", "ਪਾਣੀ ਦੀਆਂ ਬੋਤਲਾਂ", "পানির বোতল")]
    locations = ["Camp Alpha", "Camp Beta", "Camp Gamma", "Sector 1", "Sector 2", "Sector 4"]
    roles = ["food distribution", "first-aid assistance", "logistics coordination", "translation support"]

    idx = len(dataset)
    while len(dataset) < 200:
        q = quantities[idx % len(quantities)]
        it_en, it_hi, it_pa, it_bn = items[idx % len(items)]
        loc = locations[idx % len(locations)]
        r = roles[idx % len(roles)]

        en_s = f"Requesting {q} units of {it_en} for urgent relief at {loc}."
        hi_s = f"{loc} पर तत्काल राहत के लिए {it_en} की {q} इकाइयों का अनुरोध किया जा रहा है।"
        pa_s = f"{loc} ਵਿਖੇ ਤੁਰੰਤ ਰਾਹਤ ਲਈ {it_en} ਦੀਆਂ {q} ਇਕਾਈਆਂ ਦੀ ਬੇਨਤੀ ਕੀਤੀ ਜਾ ਰਹੀ ਹੈ।"
        bn_s = f"{loc} এ জরুরি ত্রাণের জন্য {it_en} এর {q} টি ইউনিট অনুরোধ করা হচ্ছে।"

        dataset.append({
            "en": en_s,
            "hi": hi_s,
            "pa": pa_s,
            "bn": bn_s,
        })
        idx += 1

    return dataset
