"""Multilingual intent examples: five per intent per language.

The intent list is the brief's section 5.3, exactly. Merchant-issue detail
rides in the separate ``topic`` field, so the examples below do not invent
labels to carry it.

Used by the unit tests (labels in ``CRITICAL_INTENTS`` must be caught by the
rule fast path) and by ``scripts/intent_eval.py`` for a live accuracy run
against the model. Sentences are deliberately short, like real telecalling
turns, and include Hinglish and code-mixed phrasing.
"""

EXAMPLES: dict[str, dict[str, list[str]]] = {
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
    "device_issue": {
        "en-IN": [
            "My soundbox is not announcing payments.",
            "The soundbox volume is too low.",
            "My card machine is not connecting to the network.",
            "The device screen is blank.",
            "My device keeps restarting.",
        ],
        "hi-IN": [
            "मेरा साउंडबॉक्स पेमेंट नहीं बोल रहा।",
            "साउंडबॉक्स की आवाज़ बहुत कम है।",
            "कार्ड मशीन नेटवर्क से कनेक्ट नहीं हो रही।",
            "डिवाइस की स्क्रीन खाली है।",
            "मेरा डिवाइस बार बार रीस्टार्ट हो रहा है।",
        ],
        "kn-IN": [
            "ನನ್ನ ಸೌಂಡ್‌ಬಾಕ್ಸ್ ಪೇಮೆಂಟ್ ಹೇಳುತ್ತಿಲ್ಲ.",
            "ಸೌಂಡ್‌ಬಾಕ್ಸ್ ಧ್ವನಿ ತುಂಬಾ ಕಡಿಮೆ ಇದೆ.",
            "ಕಾರ್ಡ್ ಮೆಷಿನ್ ನೆಟ್‌ವರ್ಕ್‌ಗೆ ಸಂಪರ್ಕ ಆಗುತ್ತಿಲ್ಲ.",
            "ಡಿವೈಸ್ ಸ್ಕ್ರೀನ್ ಖಾಲಿ ಇದೆ.",
            "ನನ್ನ ಡಿವೈಸ್ ಮತ್ತೆ ಮತ್ತೆ ರೀಸ್ಟಾರ್ಟ್ ಆಗುತ್ತಿದೆ.",
        ],
    },
    "ticket_request": {
        "en-IN": [
            "I want to raise a complaint about this.",
            "Please file a ticket for me.",
            "Create a support ticket for my soundbox.",
            "I need a complaint number.",
            "Can you register a complaint?",
        ],
        "hi-IN": [
            "मैं इसकी शिकायत दर्ज करना चाहता हूँ।",
            "मेरी शिकायत दर्ज कर दीजिए।",
            "साउंडबॉक्स के लिए टिकट बनाइए।",
            "मुझे शिकायत नंबर चाहिए।",
            "कंप्लेंट दर्ज करवाइए।",
        ],
        "kn-IN": [
            "ಇದರ ಬಗ್ಗೆ ದೂರು ದಾಖಲಿಸಬೇಕು.",
            "ನನಗೆ ಒಂದು ಟಿಕೆಟ್ ಮಾಡಿ.",
            "ಸೌಂಡ್‌ಬಾಕ್ಸ್‌ಗೆ ದೂರು ನೀಡಿ.",
            "ದೂರು ಸಂಖ್ಯೆ ಬೇಕು.",
            "ಕಂಪ್ಲೇಂಟ್ ದಾಖಲಿಸಿ.",
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
    "device_offer_interest": {
        "en-IN": [
            "I'm interested in a new soundbox.",
            "Send me the offer for the new machine.",
            "I want a new machine for my shop.",
            "What plans do you have for a soundbox?",
            "Interested in a second device.",
        ],
        "hi-IN": [
            "मुझे नया साउंडबॉक्स चाहिए।",
            "ऑफर भेजिए।",
            "मुझे नया मशीन चाहिए।",
            "साउंडबॉक्स के प्लान बताइए।",
            "दूसरा डिवाइस लेना है।",
        ],
        "kn-IN": [
            "ನನಗೆ ಹೊಸ ಸೌಂಡ್‌ಬಾಕ್ಸ್ ಬೇಕು.",
            "ಆಫರ್ ಕಳುಹಿಸಿ.",
            "ನನಗೆ ಹೊಸ ಮಷೀನ್ ಬೇಕು.",
            "ಸೌಂಡ್‌ಬಾಕ್ಸ್ ಪ್ಲಾನ್ ತಿಳಿಸಿ.",
            "ಎರಡನೇ ಡಿವೈಸ್ ಬೇಕು.",
        ],
    },
    "policy_question": {
        "en-IN": [
            "What is the settlement cut-off time?",
            "How are the charges calculated?",
            "Which documents are needed for KYC?",
            "What is the refund policy?",
            "Can I change my registered number?",
        ],
        "hi-IN": [
            "सेटलमेंट का कट-ऑफ समय क्या है?",
            "चार्ज कैसे लगते हैं?",
            "केवाईसी के लिए कौन से डाक्यूमेंट चाहिए?",
            "रिफंड की पॉलिसी क्या है?",
            "रजिस्टर्ड नंबर कैसे बदलें?",
        ],
        "kn-IN": [
            "ಸೆಟಲ್ಮೆಂಟ್ ಕಟ್-ಆಫ್ ಸಮಯ ಏನು?",
            "ಚಾರ್ಜ್ ಹೇಗೆ ಲೆಕ್ಕ ಹಾಕುತ್ತಾರೆ?",
            "ಕೆವೈಸಿಗೆ ಯಾವ ದಾಖಲೆಗಳು ಬೇಕು?",
            "ರಿಫಂಡ್ ಪಾಲಿಸಿ ಏನು?",
            "ನೋಂದಾಯಿತ ನಂಬರ್ ಹೇಗೆ ಬದಲಾಯಿಸಬೇಕು?",
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
    "repeat_complaint": {
        "en-IN": [
            "This is still not fixed.",
            "I called before and nothing happened.",
            "The same problem is happening again.",
            "This issue has been open for a week.",
            "It is the third time I am calling about this.",
        ],
        "hi-IN": [
            "यह अभी भी ठीक नहीं हुआ है।",
            "मैं पहले भी कॉल कर चुका हूँ।",
            "फिर से वही समस्या हो रही है।",
            "यह समस्या एक हफ्ते से खुली है।",
            "मैं तीसरी बार कॉल कर रहा हूँ।",
        ],
        "kn-IN": [
            "ಇದು ಇನ್ನೂ ಸರಿ ಆಗಿಲ್ಲ.",
            "ನಾನು ಮೊದಲು ಕೂಡ ಕರೆ ಮಾಡಿದ್ದೆ.",
            "ಮತ್ತೆ ಅದೇ ಸಮಸ್ಯೆ ಬರುತ್ತಿದೆ.",
            "ಈ ಸಮಸ್ಯೆ ಒಂದು ವಾರದಿಂದ ಇದೆ.",
            "ಇದು ಮೂರನೇ ಬಾರಿ ಕರೆ ಮಾಡುತ್ತಿದ್ದೇನೆ.",
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
    "smalltalk": {
        "en-IN": [
            "Hello.",
            "Good morning.",
            "Who is this?",
            "Thank you, bye.",
            "How are you?",
        ],
        "hi-IN": [
            "नमस्ते।",
            "सुप्रभात।",
            "कौन बोल रहा है?",
            "धन्यवाद, नमस्कार।",
            "आप कैसे हैं?",
        ],
        "kn-IN": [
            "ನಮಸ್ಕಾರ.",
            "ಶುಭೋದಯ.",
            "ಯಾರು ಮಾತನಾಡುತ್ತಿದ್ದೀರಿ?",
            "ಧನ್ಯವಾದ, ಬೈ.",
            "ನೀವು ಹೇಗಿದ್ದೀರಿ?",
        ],
    },
    "out_of_scope": {
        "en-IN": [
            "Can you refund last month's charges?",
            "Please increase my loan limit.",
            "Can you approve my loan today?",
            "What will the weather be tomorrow?",
            "Transfer the money to another account.",
        ],
        "hi-IN": [
            "पिछले महीने का रिफंड कर दीजिए।",
            "मेरी लोन लिमिट बढ़ा दीजिए।",
            "आज ही लोन अप्रूव कर दीजिए।",
            "कल मौसम कैसा रहेगा?",
            "पैसे दूसरे अकाउंट में भेज दीजिए।",
        ],
        "kn-IN": [
            "ಕಳೆದ ತಿಂಗಳ ಚಾರ್ಜ್ ರಿಫಂಡ್ ಮಾಡಿ.",
            "ನನ್ನ ಲೋನ್ ಲಿಮಿಟ್ ಹೆಚ್ಚಿಸಿ.",
            "ಇವತ್ತೇ ಲೋನ್ ಅಪ್ರೂವ್ ಮಾಡಿ.",
            "ನಾಳೆ ಹವಾಮಾನ ಹೇಗಿರುತ್ತದೆ?",
            "ಹಣವನ್ನು ಬೇರೆ ಅಕೌಂಟ್‌ಗೆ ಕಳುಹಿಸಿ.",
        ],
    },
}

LANGUAGES: tuple[str, ...] = ("en-IN", "hi-IN", "kn-IN")
