import hashlib


def sha1_hash(to_hash):
    try:
        message_digest = hashlib.sha256()
        string_m = str(to_hash)
        byte_m = bytes(string_m, encoding='utf')
        message_digest.update(byte_m)
        return message_digest.hexdigest()
    except TypeError as e:
        raise "Unable to generate SHA-256 hash for input string" from e


def _safe_re_search(regex_str, text):
    global DEBUG
    m = None
    try:
        m = re.search(regex_str, text)
    except Exception:
        try:
            regex_str = regex_str.replace("(?i)", "")
            m = re.search(regex_str, text, re.IGNORECASE)
        except Exception as e:
            if DEBUG:
                log_message(str(e))
    return m

def sanitize_text(text, begin, end):
    text_len = len(text)
    s_begin = max(begin - 20, 0)
    s_end = min(end + 20, text_len)
    sanitized_text = f"{text[s_begin:begin]}<REDACTED>{text[end:s_end]}"
    snippet_text = text[s_begin:s_end]
    return sanitized_text, snippet_text


def match_regex(regex_config, text):
    for c in regex_config["rules"]:
        regex_str = c["regex"]
        if m := _safe_re_search(regex_str, text):
            begin = m.regs[0][0]
            end = m.regs[0][1]
            matched_text = text[begin:end]
            sanitized_text, snippet_text = sanitize_text(text, begin, end)
            return c, matched_text, sanitized_text, snippet_text
    return None, None, None, None