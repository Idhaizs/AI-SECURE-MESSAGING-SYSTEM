import re
import os
import requests
import google.generativeai as genai
from config import Config

# Configure Gemini
genai.configure(api_key=Config.GEMINI_API_KEY)

# Phishing keywords
PHISHING_KEYWORDS = [
    'click here', 'verify your account', 'your account has been suspended',
    'confirm your identity', 'update your password', 'bank account',
    'credit card', 'ssn', 'social security', 'urgent action required',
    'you have won', 'claim your prize', 'limited time offer',
    'password expired', 'login immediately', 'verify now',
    'account compromised', 'unusual activity', 'reset password immediately'
]

SUSPICIOUS_EXTENSIONS = ['.exe', '.bat', '.cmd', '.scr', '.vbs', '.ps1', '.jar', '.apk']

MALICIOUS_URL_PATTERNS = [
    r'bit\.ly', r'tinyurl\.com', r'goo\.gl', r't\.co',
    r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}',
    r'[a-z0-9]{20,}\.(com|net|org)',
]


def detect_phishing_text(message: str) -> dict:
    message_lower = message.lower()
    
    # Rule-based check
    found_keywords = [kw for kw in PHISHING_KEYWORDS if kw in message_lower]
    
    # URL extraction
    urls = re.findall(r'https?://[^\s]+', message)
    suspicious_urls = []
    for url in urls:
        for pattern in MALICIOUS_URL_PATTERNS:
            if re.search(pattern, url):
                suspicious_urls.append(url)
                break
    
    is_suspicious = len(found_keywords) > 0 or len(suspicious_urls) > 0
    
    result = {
        'is_suspicious': is_suspicious,
        'threat_type': 'none',
        'detail': '',
        'keywords_found': found_keywords,
        'suspicious_urls': suspicious_urls
    }
    
    if suspicious_urls:
        result['threat_type'] = 'malicious_link'
        result['detail'] = f"Suspicious URLs detected: {', '.join(suspicious_urls)}"
    elif found_keywords:
        result['threat_type'] = 'phishing'
        result['detail'] = f"Phishing keywords detected: {', '.join(found_keywords)}"
    
    return result


def scan_with_gemini(message: str) -> dict:
    try:
        model = genai.GenerativeModel('gemini-1.5-flash')
        prompt = f"""Analyze this message for cybersecurity threats. 
        Check for: phishing attempts, malicious links, social engineering, spam, suspicious content.
        Message: "{message}"
        
        Respond in JSON format only:
        {{
            "is_suspicious": true/false,
            "threat_type": "none/phishing/malicious_link/spam/social_engineering",
            "confidence": "low/medium/high",
            "reason": "brief explanation"
        }}"""
        
        response = model.generate_content(prompt)
        text = response.text.strip()
        
        # Extract JSON from response
        import json
        json_match = re.search(r'\{.*\}', text, re.DOTALL)
        if json_match:
            result = json.loads(json_match.group())
            return result
    except Exception as e:
        pass
    
    return {
        'is_suspicious': False,
        'threat_type': 'none',
        'confidence': 'low',
        'reason': 'Gemini scan unavailable'
    }


def scan_file_virustotal(file_hash: str) -> dict:
    try:
        url = f"https://www.virustotal.com/api/v3/files/{file_hash}"
        headers = {"x-apikey": Config.VIRUSTOTAL_API_KEY}
        response = requests.get(url, headers=headers, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            stats = data.get('data', {}).get('attributes', {}).get('last_analysis_stats', {})
            malicious = stats.get('malicious', 0)
            suspicious = stats.get('suspicious', 0)
            
            return {
                'is_malicious': malicious > 0 or suspicious > 0,
                'malicious_count': malicious,
                'suspicious_count': suspicious,
                'scan_result': 'malicious' if malicious > 0 else ('suspicious' if suspicious > 0 else 'clean')
            }
        elif response.status_code == 404:
            return {'is_malicious': False, 'scan_result': 'clean', 'note': 'Not found in VirusTotal database'}
    except Exception as e:
        pass
    
    return {'is_malicious': False, 'scan_result': 'pending', 'note': 'VirusTotal scan failed'}


def check_file_extension(filename: str) -> dict:
    ext = os.path.splitext(filename)[1].lower()
    is_suspicious = ext in SUSPICIOUS_EXTENSIONS
    return {
        'is_suspicious': is_suspicious,
        'extension': ext,
        'threat_type': 'suspicious_attachment' if is_suspicious else 'none',
        'detail': f"Suspicious file extension: {ext}" if is_suspicious else ''
    }


def full_message_scan(message: str) -> dict:
    # Rule-based detection first (fast)
    rule_result = detect_phishing_text(message)
    
    # If rule-based finds threat, also verify with Gemini
    if rule_result['is_suspicious']:
        gemini_result = scan_with_gemini(message)
        return {
            'is_suspicious': True,
            'threat_type': rule_result['threat_type'],
            'detail': rule_result['detail'],
            'gemini_confirms': gemini_result.get('is_suspicious', False)
        }
    
    # If rule-based clean, still do Gemini scan
    gemini_result = scan_with_gemini(message)
    return {
        'is_suspicious': gemini_result.get('is_suspicious', False),
        'threat_type': gemini_result.get('threat_type', 'none'),
        'detail': gemini_result.get('reason', ''),
        'gemini_confirms': True
    }
