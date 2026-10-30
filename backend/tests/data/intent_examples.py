"""Multilingual intent examples: five per intent per language.

Used by the unit tests (safety labels must be caught by the rule fast path)
and by ``scripts/intent_eval.py`` for a live accuracy run against the model.
Sentences are deliberately short, like real telecalling turns, and include
Hinglish and code-mixed phrasing.
"""

EXAMPLES: dict[str, dict[str, list[str]]] = {
    "settlement_query": {
        "en-IN": [
            "When will my settlement come?",
            "Why is today's settlement delayed?",
            "How long does settlement take on weekends?",
            "Has my settlement been processed?",
            "My settlement amount is short this time.",
        ],
        "hi-IN": [
            "मेरा सेटलमेंट कब आएगा?",
            "आज का सेटलमेंट देर क्यों हो रहा है?",
            "सेटलमेंट में पैसे कम क्यों आए?",
            "कल का सेटलमेंट अभी तक नहीं आया।",
            "वीकेंड में सेटलमेंट कितने दिन में आता है?",
        ],
        "kn-IN": [
            "ನನ್ನ ಸೆಟಲ್ಮೆಂಟ್ ಯಾವಾಗ ಬರುತ್ತದೆ?",
            "ಇಂದಿನ ಸೆಟಲ್ಮೆಂಟ್ ತಡವಾಗಿದೆ ಏಕೆ?",
            "ಸೆಟಲ್ಮೆಂಟ್‌ನಲ್ಲಿ ಹಣ ಕಡಿಮೆ ಬಂದಿದೆ.",
            "ನಿನ್ನೆಯ ಸೆಟಲ್ಮೆಂಟ್ ಇನ್ನೂ ಬಂದಿಲ್ಲ.",
            "ವಾರಾಂತ್ಯದಲ್ಲಿ ಸೆಟಲ್ಮೆಂಟ್ ಎಷ್ಟು ದಿನ ತೆಗೆದುಕೊಳ್ಳುತ್ತದೆ?",
        ],
    },
    "transaction_issue": {
        "en-IN": [
            "A customer's payment failed but money left their account.",
            "My transaction is stuck on pending.",
            "The payment shows failed in the app.",
            "A payment came through but the amount is wrong.",
            "I cannot see a transaction in my history.",
        ],
        "hi-IN": [
            "ग्राहक का पेमेंट फेल हो गया पर पैसे कट गए।",
            "मेरा ट्रांजैक्शन पेंडिंग में अटका है।",
            "ऐप में पेमेंट फेल दिखा रहा है।",
            "पेमेंट आया है पर रकम गलत है।",
            "मुझे हिस्ट्री में ट्रांजैक्शन नहीं दिख रहा।",
        ],
        "kn-IN": [
            "ಗ್ರಾಹಕರ ಪೇಮೆಂಟ್ ಫೇಲ್ ಆಯಿತು ಆದರೆ ಹಣ ಕಟ್ಟಿಹೋಯಿತು.",
            "ನನ್ನ ಟ್ರಾನ್ಸಾಕ್ಷನ್ ಪೆಂಡಿಂಗ್‌ನಲ್ಲಿ ಇದೆ.",
            "ಆಪ್‌ನಲ್ಲಿ ಪೇಮೆಂಟ್ ಫೇಲ್ ತೋರಿಸುತ್ತಿದೆ.",
            "ಪೇಮೆಂಟ್ ಬಂದಿದೆ ಆದರೆ ಮೊತ್ತ ತಪ್ಪಾಗಿದೆ.",
            "ನನ್ನ ಹಿಸ್ಟರಿಯಲ್ಲಿ ಟ್ರಾನ್ಸಾಕ್ಷನ್ ಕಾಣುತ್ತಿಲ್ಲ.",
        ],
    },
    "qr_code_issue": {
        "en-IN": [
            "My Paytm QR code is not working.",
            "Customers cannot scan my QR code.",
            "The QR code is not showing in the app.",
            "I need a new QR code for my shop.",
            "The QR code print is damaged, can I get another?",
        ],
        "hi-IN": [
            "मेरा पेटीएम क्यूआर कोड काम नहीं कर रहा।",
            "ग्राहक मेरा क्यूआर कोड स्कैन नहीं कर पा रहे।",
            "ऐप में क्यूआर कोड नहीं दिख रहा।",
            "मुझे दुकान के लिए नया क्यूआर कोड चाहिए।",
            "क्यूआर कोड का प्रिंट खराब हो गया है।",
        ],
        "kn-IN": [
            "ನನ್ನ ಪೇಟಿಎಂ ಕ್ಯೂಆರ್ ಕೋಡ್ ಕೆಲಸ ಮಾಡುತ್ತಿಲ್ಲ.",
            "ಗ್ರಾಹಕರು ನನ್ನ ಕ್ಯೂಆರ್ ಕೋಡ್ ಸ್ಕ್ಯಾನ್ ಮಾಡಲು ಆಗುತ್ತಿಲ್ಲ.",
            "ಆಪ್‌ನಲ್ಲಿ ಕ್ಯೂಆರ್ ಕೋಡ್ ಕಾಣುತ್ತಿಲ್ಲ.",
            "ನನ್ನ ಅಂಗಡಿಗೆ ಹೊಸ ಕ್ಯೂಆರ್ ಕೋಡ್ ಬೇಕು.",
            "ಕ್ಯೂಆರ್ ಕೋಡ್ ಪ್ರಿಂಟ್ ಹಾಳಾಗಿದೆ.",
        ],
    },
    "device_issue": {
        "en-IN": [
            "The Paytm device is not switching on.",
            "My card machine is not connecting to the network.",
            "The device screen is blank.",
            "The machine beeps but does not print.",
            "My device keeps restarting.",
        ],
        "hi-IN": [
            "पेटीएम डिवाइस चालू नहीं हो रहा।",
            "कार्ड मशीन नेटवर्क से कनेक्ट नहीं हो रही।",
            "डिवाइस की स्क्रीन खाली है।",
            "मशीन बीप करती है पर प्रिंट नहीं करती।",
            "मेरा डिवाइस बार-बार रीस्टार्ट हो रहा है।",
        ],
        "kn-IN": [
            "ಪೇಟಿಎಂ ಡಿವೈಸ್ ಆನ್ ಆಗುತ್ತಿಲ್ಲ.",
            "ಕಾರ್ಡ್ ಮೆಷಿನ್ ನೆಟ್‌ವರ್ಕ್‌ಗೆ ಸಂಪರ್ಕ ಆಗುತ್ತಿಲ್ಲ.",
            "ಡಿವೈಸ್ ಸ್ಕ್ರೀನ್ ಖಾಲಿ ಇದೆ.",
            "ಮೆಷಿನ್ ಬೀಪ್ ಮಾಡುತ್ತದೆ ಆದರೆ ಪ್ರಿಂಟ್ ಆಗುತ್ತಿಲ್ಲ.",
            "ನನ್ನ ಡಿವೈಸ್ ಪದೇ ಪದೇ ರೀಸ್ಟಾರ್ಟ್ ಆಗುತ್ತಿದೆ.",
        ],
    },
    "refund_query": {
        "en-IN": [
            "When will the refund reach the customer?",
            "The refund is still pending after five days.",
            "How do I process a refund?",
            "The customer says the refund did not arrive.",
            "Can you check the refund status for this order?",
        ],
        "hi-IN": [
            "रिफंड ग्राहक तक कब पहुंचेगा?",
            "पांच दिन हो गए रिफंड अभी भी पेंडिंग है।",
            "रिफंड कैसे करें?",
            "ग्राहक कह रहा है रिफंड नहीं आया।",
            "इस ऑर्डर का रिफंड स्टेटस देखिए।",
        ],
        "kn-IN": [
            "ರಿಫಂಡ್ ಗ್ರಾಹಕರಿಗೆ ಯಾವಾಗ ತಲುಪುತ್ತದೆ?",
            "ಐದು ದಿನ ಆಯಿತು, ರಿಫಂಡ್ ಇನ್ನೂ ಪೆಂಡಿಂಗ್ ಇದೆ.",
            "ರಿಫಂಡ್ ಹೇಗೆ ಮಾಡಬೇಕು?",
            "ಗ್ರಾಹಕರು ರಿಫಂಡ್ ಬಂದಿಲ್ಲ ಎನ್ನುತ್ತಿದ್ದಾರೆ.",
            "ಈ ಆರ್ಡರ್‌ನ ರಿಫಂಡ್ ಸ್ಟೇಟಸ್ ನೋಡಿ.",
        ],
    },
    "loan_interest": {
        "en-IN": [
            "I want to know about a merchant loan.",
            "Am I eligible for a Paytm loan?",
            "What is the interest rate on the loan?",
            "How much EMI will I have to pay?",
            "Can I get a loan for my shop?",
        ],
        "hi-IN": [
            "मुझे मर्चेंट लोन के बारे में जानना है।",
            "क्या मुझे पेटीएम लोन मिल सकता है?",
            "लोन पर ब्याज कितना है?",
            "ईएमआई कितनी देनी होगी?",
            "दुकान के लिए लोन मिलेगा?",
        ],
        "kn-IN": [
            "ನನಗೆ ಮರ್ಚೆಂಟ್ ಲೋನ್ ಬಗ್ಗೆ ತಿಳಿಯಬೇಕು.",
            "ನನಗೆ ಪೇಟಿಎಂ ಲೋನ್ ಸಿಗುತ್ತದೆಯೇ?",
            "ಲೋನ್‌ಗೆ ಬಡ್ಡಿ ಎಷ್ಟು?",
            "ಇಎಂಐ ಎಷ್ಟು ಕಟ್ಟಬೇಕು?",
            "ಅಂಗಡಿಗೆ ಲೋನ್ ಸಿಗುತ್ತದೆಯೇ?",
        ],
    },
    "soundbox_issue": {
        "en-IN": [
            "My soundbox is not announcing payments.",
            "The soundbox volume is too low.",
            "The soundbox says the wrong amount.",
            "My soundbox is offline since morning.",
            "The soundbox keeps disconnecting from WiFi.",
        ],
        "hi-IN": [
            "मेरा साउंडबॉक्स पेमेंट नहीं बोल रहा।",
            "साउंडबॉक्स की आवाज़ बहुत कम है।",
            "साउंडबॉक्स गलत रकम बोल रहा है।",
            "मेरा साउंडबॉक्स सुबह से ऑफलाइन है।",
            "साउंडबॉक्स वाईफाई से बार-बार डिस्कनेक्ट होता है।",
        ],
        "kn-IN": [
            "ನನ್ನ ಸೌಂಡ್‌ಬಾಕ್ಸ್ ಪೇಮೆಂಟ್ ಹೇಳುತ್ತಿಲ್ಲ.",
            "ಸೌಂಡ್‌ಬಾಕ್ಸ್ ಧ್ವನಿ ತುಂಬಾ ಕಡಿಮೆ ಇದೆ.",
            "ಸೌಂಡ್‌ಬಾಕ್ಸ್ ತಪ್ಪು ಮೊತ್ತ ಹೇಳುತ್ತಿದೆ.",
            "ನನ್ನ ಸೌಂಡ್‌ಬಾಕ್ಸ್ ಬೆಳಗ್ಗಿನಿಂದ ಆಫ್‌ಲೈನ್ ಇದೆ.",
            "ಸೌಂಡ್‌ಬಾಕ್ಸ್ ವೈಫೈನಿಂದ ಪದೇ ಪದೇ ಡಿಸ್ಕನೆಕ್ಟ್ ಆಗುತ್ತದೆ.",
        ],
    },
    "charges_query": {
        "en-IN": [
            "Why was a fee deducted from my payment?",
            "What charges does Paytm take on a QR payment?",
            "This month's charges look too high.",
            "Is there a charge for soundbox payments?",
            "Explain the deduction on this transaction.",
        ],
        "hi-IN": [
            "मेरे पेमेंट से फीस क्यों कटी?",
            "क्यूआर पेमेंट पर पेटीएम कितना चार्ज लेता है?",
            "इस महीने के चार्ज बहुत ज्यादा लग रहे हैं।",
            "साउंडबॉक्स पेमेंट पर चार्ज है क्या?",
            "इस ट्रांजैक्शन की कटौती समझाइए।",
        ],
        "kn-IN": [
            "ನನ್ನ ಪೇಮೆಂಟ್‌ನಿಂದ ಫೀಸ್ ಏಕೆ ಕಡಿತವಾಯಿತು?",
            "ಕ್ಯೂಆರ್ ಪೇಮೆಂಟ್‌ಗೆ ಪೇಟಿಎಂ ಎಷ್ಟು ಚಾರ್ಜ್ ತೆಗೆದುಕೊಳ್ಳುತ್ತದೆ?",
            "ಈ ತಿಂಗಳ ಚಾರ್ಜ್ ತುಂಬಾ ಜಾಸ್ತಿ ಇದೆ.",
            "ಸೌಂಡ್‌ಬಾಕ್ಸ್ ಪೇಮೆಂಟ್‌ಗೆ ಚಾರ್ಜ್ ಇದೆಯೇ?",
            "ಈ ಟ್ರಾನ್ಸಾಕ್ಷನ್‌ನ ಕಡಿತ ವಿವರಿಸಿ.",
        ],
    },
    "onboarding_kyc": {
        "en-IN": [
            "How do I sign up as a Paytm merchant?",
            "Which documents do I need for KYC?",
            "My KYC is stuck in review.",
            "How long does merchant verification take?",
            "Can I update my shop address in my account?",
        ],
        "hi-IN": [
            "पेटीएम मर्चेंट के तौर पर रजिस्टर कैसे करें?",
            "केवाईसी के लिए कौन से डाक्यूमेंट चाहिए?",
            "मेरी केवाईसी रिव्यू में अटकी है।",
            "मर्चेंट वेरिफिकेशन में कितने दिन लगते हैं?",
            "अकाउंट में दुकान का पता कैसे बदलें?",
        ],
        "kn-IN": [
            "ಪೇಟಿಎಂ ಮರ್ಚೆಂಟ್ ಆಗಿ ನೋಂದಣಿ ಹೇಗೆ ಮಾಡಬೇಕು?",
            "ಕೆವೈಸಿಗೆ ಯಾವ ದಾಖಲೆಗಳು ಬೇಕು?",
            "ನನ್ನ ಕೆವೈಸಿ ರಿವ್ಯೂನಲ್ಲಿ ಇದೆ.",
            "ಮರ್ಚೆಂಟ್ ವೆರಿಫಿಕೇಶನ್‌ಗೆ ಎಷ್ಟು ದಿನ ಬೇಕು?",
            "ಅಕೌಂಟ್‌ನಲ್ಲಿ ಅಂಗಡಿ ವಿಳಾಸ ಹೇಗೆ ಬದಲಾಯಿಸಬೇಕು?",
        ],
    },
    "language_choice": {
        "en-IN": [
            "English.",
            "I want to speak in English.",
            "Can we talk in Hindi?",
            "Kannada please.",
            "Let's continue in Hindi.",
        ],
        "hi-IN": [
            "हिंदी।",
            "हिंदी में बात करें।",
            "मुझे हिंदी में बोलिए।",
            "कन्नड़ में बात करनी है।",
            "अंग्रेजी में बात करें।",
        ],
        "kn-IN": [
            "ಕನ್ನಡ.",
            "ಕನ್ನಡದಲ್ಲಿ ಮಾತನಾಡಿ.",
            "ನನಗೆ ಕನ್ನಡ ಬೇಕು.",
            "ಇಂಗ್ಲಿಷ್‌ನಲ್ಲಿ ಮಾತನಾಡಿ.",
            "ಹಿಂದಿಯಲ್ಲಿ ಮಾತನಾಡಿ.",
        ],
    },
    "confirmation_yes": {
        "en-IN": [
            "Yes.",
            "Yes, that's correct.",
            "Okay, go ahead.",
            "Sure, continue.",
            "Yeah, I understand.",
        ],
        "hi-IN": [
            "हाँ।",
            "हाँ, सही है।",
            "जी हाँ, बताइए।",
            "ठीक है, आगे बढ़िए।",
            "हां, समझ गया।",
        ],
        "kn-IN": [
            "ಹೌದು.",
            "ಹೌದು, ಸರಿ.",
            "ಸರಿ, ಮುಂದುವರಿಸಿ.",
            "ಆಗಲಿ, ಹೇಳಿ.",
            "ಹೌದು, ಅರ್ಥ ಆಯಿತು.",
        ],
    },
    "confirmation_no": {
        "en-IN": [
            "No.",
            "No, not now.",
            "Nope, that's not right.",
            "No thanks, not needed.",
            "No, I don't want that.",
        ],
        "hi-IN": [
            "नहीं।",
            "नहीं, अभी नहीं।",
            "ना, ऐसा नहीं है।",
            "नहीं चाहिए।",
            "नहीं, मुझे नहीं चाहिए।",
        ],
        "kn-IN": [
            "ಇಲ್ಲ.",
            "ಇಲ್ಲ, ಈಗ ಬೇಡ.",
            "ಇಲ್ಲ, ಬೇಡ.",
            "ಇಲ್ಲ, ನನಗೆ ಬೇಕಿಲ್ಲ.",
            "ಇಲ್ಲ, ಅದು ಸರಿ ಇಲ್ಲ.",
        ],
    },
    "human_request": {
        "en-IN": [
            "I want to talk to a human.",
            "Connect me to a real person.",
            "Can I speak to a customer care agent?",
            "Give me your customer support number.",
            "Let me talk to a representative.",
        ],
        "hi-IN": [
            "मुझे इंसान से बात करनी है।",
            "कस्टमर केयर से बात कराइए।",
            "एजेंट से बात करवाइए।",
            "मुझे ग्राहक सेवा से जोड़िए।",
            "किसी व्यक्ति से बात करनी है।",
        ],
        "kn-IN": [
            "ನಾನು ಮನುಷ್ಯನ ಜೊತೆ ಮಾತನಾಡಬೇಕು.",
            "ಏಜೆಂಟ್ ಜೊತೆ ಮಾತನಾಡಿಸಿ.",
            "ಗ್ರಾಹಕ ಸೇವೆಗೆ ಕರೆ ಮಾಡಿ.",
            "ನನಗೆ ಮಾನವನ ಜೊತೆ ಮಾತು ಬೇಕು.",
            "ವ್ಯಕ್ತಿ ಜೊತೆ ಮಾತನಾಡಿಸಿ.",
        ],
    },
    "callback_request": {
        "en-IN": [
            "Call me back in ten minutes.",
            "Please call later, I'm busy.",
            "Call me tomorrow morning.",
            "Can you call back after lunch?",
            "I'll talk later, call me after five.",
        ],
        "hi-IN": [
            "बाद में कॉल करना।",
            "मुझे फिर कॉल करना।",
            "कल कॉल करना।",
            "अभी नहीं, बाद में कॉल करना।",
            "मुझे कॉल करना शाम को।",
        ],
        "kn-IN": [
            "ನಂತರ ಕರೆ ಮಾಡಿ.",
            "ಮತ್ತೆ ಕರೆ ಮಾಡಿ.",
            "ನಾಳೆ ಕರೆ ಮಾಡಿ.",
            "ಈಗ ಬೇಡ, ನಂತರ ಕರೆ ಮಾಡಿ.",
            "ಸ್ವಲ್ಪ ಹೊತ್ತಿನ ನಂತರ ಕರೆ ಮಾಡಿ.",
        ],
    },
    "opt_out": {
        "en-IN": [
            "Stop calling me.",
            "Please don't call this number again.",
            "I'm not interested, remove my number.",
            "Unsubscribe me from these calls.",
            "Do not call me anymore.",
        ],
        "hi-IN": [
            "मुझे कॉल मत करो।",
            "मुझे कॉल मत करें, मुझे ज़रूरत नहीं है।",
            "मेरा नंबर हटाओ।",
            "मुझे इंटरेस्ट नहीं है।",
            "अब बंद करो ये कॉल।",
        ],
        "kn-IN": [
            "ನನಗೆ ಕರೆ ಮಾಡಬೇಡಿ.",
            "ಈ ನಂಬರ್‌ಗೆ ಕರೆ ಮಾಡಬೇಡಿ.",
            "ನನಗೆ ಆಸಕ್ತಿ ಇಲ್ಲ.",
            "ಇದನ್ನು ನಿಲ್ಲಿಸಿ.",
            "ನನ್ನ ನಂಬರ್ ತೆಗೆಯಿರಿ.",
        ],
    },
    "objection": {
        "en-IN": [
            "I already have another QR provider.",
            "The charges are too high for me.",
            "I don't trust these machines.",
            "I need to think about it.",
            "Why should I switch to Paytm?",
        ],
        "hi-IN": [
            "मेरे पास पहले से दूसरा क्यूआर प्रोवाइडर है।",
            "मुझे चार्ज बहुत ज्यादा लगते हैं।",
            "मुझे इन मशीनों पर भरोसा नहीं है।",
            "मुझे सोचने का समय चाहिए।",
            "मैं पेटीएम पर क्यों आऊं?",
        ],
        "kn-IN": [
            "ನನ್ನ ಬಳಿ ಈಗಾಗಲೇ ಬೇರೆ ಕ್ಯೂಆರ್ ಪ್ರೊವೈಡರ್ ಇದೆ.",
            "ನನಗೆ ಚಾರ್ಜ್ ತುಂಬಾ ಜಾಸ್ತಿ ಅನಿಸುತ್ತದೆ.",
            "ಈ ಮೆಷಿನ್‌ಗಳ ಮೇಲೆ ನನಗೆ ನಂಬಿಕೆ ಇಲ್ಲ.",
            "ನನಗೆ ಸ್ವಲ್ಪ ಯೋಚಿಸಲು ಸಮಯ ಬೇಕು.",
            "ನಾನು ಪೇಟಿಎಂಗೆ ಏಕೆ ಬದಲಾಗಬೇಕು?",
        ],
    },
    "other": {
        "en-IN": [
            "Hello.",
            "Good morning.",
            "Who is this?",
            "Thank you, bye.",
            "Can you hear me?",
        ],
        "hi-IN": [
            "नमस्ते।",
            "सुप्रभात।",
            "कौन बोल रहा है?",
            "धन्यवाद, नमस्कार।",
            "आप सुन रहे हैं?",
        ],
        "kn-IN": [
            "ನಮಸ್ಕಾರ.",
            "ಶುಭೋದಯ.",
            "ಯಾರು ಮಾತನಾಡುತ್ತಿದ್ದೀರಿ?",
            "ಧನ್ಯವಾದ, ಬೈ.",
            "ನೀವು ಕೇಳುತ್ತಿದ್ದೀರಾ?",
        ],
    },
}

LANGUAGES: tuple[str, ...] = ("en-IN", "hi-IN", "kn-IN")
