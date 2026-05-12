import json
import boto3
import uuid
import re
import math
from datetime import datetime

BUCKET_NAME = "YOUR-BUCKET-NAME"  # <-- Replace with your actual bucket name e.g. cs524-aisiri-website-2026

s3 = boto3.client("s3")

# ─── Sentiment Analysis ───────────────────────────────────────────────────────

POSITIVE_WORDS = set([
    "good","great","excellent","amazing","wonderful","fantastic","love","best",
    "happy","joy","beautiful","awesome","outstanding","superb","brilliant",
    "perfect","delightful","pleasant","positive","enjoy","enjoyed","exciting",
    "impressive","nice","pleased","glad","cheerful","friendly","helpful","fun"
])

NEGATIVE_WORDS = set([
    "bad","terrible","awful","horrible","worst","hate","poor","disappointing",
    "sad","ugly","boring","mediocre","dreadful","annoying","frustrating",
    "negative","unpleasant","difficult","problem","issue","wrong","failure",
    "failed","broken","useless","slow","expensive","weak","poor","lacking"
])

def analyze_sentiment(text):
    words = re.findall(r'\b\w+\b', text.lower())
    total = len(words) if words else 1
    pos = sum(1 for w in words if w in POSITIVE_WORDS)
    neg = sum(1 for w in words if w in NEGATIVE_WORDS)
    neu = total - pos - neg

    pos_score = round(pos / total, 4)
    neg_score = round(neg / total, 4)
    neu_score = round(neu / total, 4)

    if pos > neg:
        label = "Positive"
    elif neg > pos:
        label = "Negative"
    else:
        label = "Neutral"

    return {
        "label": label,
        "scores": {
            "positive": pos_score,
            "neutral":  neu_score,
            "negative": neg_score
        }
    }

# ─── Entity Extraction ────────────────────────────────────────────────────────

PERSON_TITLES  = {"mr","mrs","ms","dr","prof","professor","sir","president","ceo","director"}
ORG_SUFFIXES   = {"university","institute","college","corporation","corp","inc","llc","ltd",
                  "company","co","organization","org","foundation","school","academy","lab"}
LOC_KEYWORDS   = {"city","country","state","river","mountain","ocean","lake","street",
                  "avenue","road","park","island","continent","region","district","county"}
DATE_KEYWORDS  = {"january","february","march","april","may","june","july","august",
                  "september","october","november","december","monday","tuesday","wednesday",
                  "thursday","friday","saturday","sunday","today","yesterday","tomorrow"}

def extract_entities(text):
    entities = []
    seen = set()
    sentences = re.split(r'[.!?]', text)

    for sentence in sentences:
        words = sentence.split()
        i = 0
        while i < len(words):
            word = words[i].strip(".,!?\"'()[]")
            word_lower = word.lower()

            # Multi-word proper noun detection
            if word and word[0].isupper() and word_lower not in {"the","a","an","in","on","at","of","and","or","but","is","was","are","were"}:
                phrase = word
                j = i + 1
                while j < len(words):
                    nw = words[j].strip(".,!?\"'()[]")
                    if nw and nw[0].isupper():
                        phrase += " " + nw
                        j += 1
                    else:
                        break

                phrase_lower = phrase.lower()
                phrase_words = phrase_lower.split()

                if phrase_lower not in seen and len(phrase) > 1:
                    seen.add(phrase_lower)
                    entity_type = "OTHER"

                    if word_lower in PERSON_TITLES:
                        entity_type = "PERSON"
                    elif any(w in ORG_SUFFIXES for w in phrase_words):
                        entity_type = "ORGANIZATION"
                    elif any(w in LOC_KEYWORDS for w in phrase_words):
                        entity_type = "LOCATION"
                    elif any(w in DATE_KEYWORDS for w in phrase_words):
                        entity_type = "DATE"
                    elif len(phrase_words) >= 2:
                        entity_type = "PERSON"
                    else:
                        entity_type = "OTHER"

                    entities.append({"text": phrase, "type": entity_type})
                i = j
            else:
                # Check for date keywords
                if word_lower in DATE_KEYWORDS and word_lower not in seen:
                    seen.add(word_lower)
                    entities.append({"text": word, "type": "DATE"})
                i += 1

    return entities[:15]  # Return top 15 entities

# ─── Key Phrase Extraction ────────────────────────────────────────────────────

STOP_WORDS = set([
    "the","a","an","and","or","but","in","on","at","to","for","of","with",
    "by","from","is","was","are","were","be","been","being","have","has","had",
    "do","does","did","will","would","could","should","may","might","shall",
    "this","that","these","those","it","its","i","you","he","she","we","they",
    "my","your","his","her","our","their","what","which","who","how","when",
    "where","why","not","no","so","if","as","up","out","about","into","than"
])

def extract_key_phrases(text):
    sentences = re.split(r'[.!?]', text)
    phrases = []
    seen = set()

    for sentence in sentences:
        words = re.findall(r'\b[a-zA-Z]+\b', sentence)
        i = 0
        while i < len(words):
            if words[i].lower() not in STOP_WORDS and len(words[i]) > 2:
                phrase_words = [words[i]]
                j = i + 1
                while j < len(words) and j < i + 4:
                    if words[j].lower() not in STOP_WORDS:
                        phrase_words.append(words[j])
                        j += 1
                    else:
                        break
                phrase = " ".join(phrase_words)
                phrase_lower = phrase.lower()
                if phrase_lower not in seen and len(phrase_words) >= 1:
                    seen.add(phrase_lower)
                    phrases.append(phrase)
                i = j
            else:
                i += 1

    # Score by length (longer = more meaningful)
    phrases.sort(key=lambda p: len(p.split()), reverse=True)
    return phrases[:10]

# ─── Readability Score ────────────────────────────────────────────────────────

def compute_readability(text):
    sentences = [s.strip() for s in re.split(r'[.!?]', text) if s.strip()]
    words     = re.findall(r'\b\w+\b', text)
    syllables  = sum(count_syllables(w) for w in words)

    num_sentences = max(len(sentences), 1)
    num_words     = max(len(words), 1)
    num_syllables = max(syllables, 1)

    # Flesch Reading Ease
    score = 206.835 - 1.015 * (num_words / num_sentences) - 84.6 * (num_syllables / num_words)
    score = max(0, min(100, round(score, 1)))

    if score >= 90:   level = "Very Easy"
    elif score >= 80: level = "Easy"
    elif score >= 70: level = "Fairly Easy"
    elif score >= 60: level = "Standard"
    elif score >= 50: level = "Fairly Difficult"
    elif score >= 30: level = "Difficult"
    else:             level = "Very Difficult"

    avg_wps = round(num_words / num_sentences, 1)

    return {
        "score":          score,
        "level":          level,
        "word_count":     num_words,
        "sentence_count": num_sentences,
        "avg_words_per_sentence": avg_wps
    }

def count_syllables(word):
    word = word.lower()
    vowels = "aeiouy"
    count = 0
    prev_vowel = False
    for ch in word:
        is_vowel = ch in vowels
        if is_vowel and not prev_vowel:
            count += 1
        prev_vowel = is_vowel
    if word.endswith("e") and count > 1:
        count -= 1
    return max(1, count)

# ─── Lambda Handler ───────────────────────────────────────────────────────────

def lambda_handler(event, context):
    # Handle CORS preflight
    if event.get("requestContext", {}).get("http", {}).get("method") == "OPTIONS":
        return {
            "statusCode": 200,
            "headers": {
                "Access-Control-Allow-Origin":  "*",
                "Access-Control-Allow-Methods": "POST, OPTIONS",
                "Access-Control-Allow-Headers": "content-type"
            },
            "body": ""
        }

    try:
        # Parse body
        body = event.get("body", {})
        if isinstance(body, str):
            body = json.loads(body)

        text = body.get("text", "").strip()

        if not text:
            return {
                "statusCode": 400,
                "headers": {"Access-Control-Allow-Origin": "*"},
                "body": json.dumps({"error": "No text provided"})
            }

        # Run all analyses
        sentiment   = analyze_sentiment(text)
        entities    = extract_entities(text)
        key_phrases = extract_key_phrases(text)
        readability = compute_readability(text)

        result = {
            "sentiment":   sentiment,
            "entities":    entities,
            "key_phrases": key_phrases,
            "readability": readability,
            "timestamp":   datetime.utcnow().isoformat()
        }

        # Store result in S3
        file_key = f"results/{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:8]}.json"
        s3.put_object(
            Bucket=BUCKET_NAME,
            Key=file_key,
            Body=json.dumps(result, indent=2),
            ContentType="application/json"
        )

        return {
            "statusCode": 200,
            "headers": {
                "Access-Control-Allow-Origin":  "*",
                "Access-Control-Allow-Methods": "POST, OPTIONS",
                "Access-Control-Allow-Headers": "content-type",
                "Content-Type": "application/json"
            },
            "body": json.dumps(result)
        }

    except Exception as e:
        return {
            "statusCode": 500,
            "headers": {"Access-Control-Allow-Origin": "*"},
            "body": json.dumps({"error": str(e)})
        }
