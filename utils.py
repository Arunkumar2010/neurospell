import pandas as pd
import re

def highlight_corrected_text(original_text, corrections):
    """
    Highlights corrected words in Cyberpunk style.
    """
    words = original_text.split()
    highlighted_words = []
    
    # Map index to correction for precise word matching
    # Note: This is simpler than matching by word value to avoid double-highlighting
    correction_map = {c['original'].lower(): c for c in corrections}
    
    for word in words:
        clean_word = re.sub(r'[^\w\s]', '', word).lower()
        if clean_word in correction_map:
            c = correction_map[clean_word]
            corrected = c['corrected']
            error_type = c['type']
            
            # Preserve punctuation
            punc_start = re.search(r'^[^\w\s]+', word)
            punc_end = re.search(r'[^\w\s]+$', word)
            prefix = punc_start.group() if punc_start else ""
            suffix = punc_end.group() if punc_end else ""
            
            orig_html = f"<span style='color:#ff4444;text-decoration:line-through;font-size:0.8em;margin-right:4px;'>{clean_word}</span>"
            
            if error_type == "Real-word":
                color = "#7b2fff"
            else:
                color = "#00ff88"
                
            corr_html = f"<span style='color:{color};border-bottom:1px solid {color}60'>{corrected}</span>"
            
            highlighted_words.append(f"{prefix}{orig_html}{corr_html}{suffix}")
        else:
            highlighted_words.append(word)
            
    return " ".join(highlighted_words)

def create_html_correction_table(corrections):
    """
    Generates a Cyberpunk-styled HTML table for corrections.
    """
    if not corrections:
        return "<div style='color:#4a7a9b;font-family:Share Tech Mono,monospace;'>NO ANOMALIES DETECTED</div>"
    
    rows = ""
    for c in corrections:
        badge_color = "#ff4444" if c['type'] == "Non-word" else "#7b2fff"
        badge_text = c['type'].upper()
        
        rows += f"""
        <tr style='border-bottom:1px solid #0d2844;'>
            <td style='padding:12px;color:#ff4444;font-family:Share Tech Mono,monospace;'>{c['original']}</td>
            <td style='padding:12px;color:#00ff88;font-family:Share Tech Mono,monospace;'>{c['corrected']}</td>
            <td style='padding:12px;'>
                <span style='background:{badge_color}20;color:{badge_color};border:1px solid {badge_color}40;
                padding:2px 8px;border-radius:3px;font-size:9px;letter-spacing:1px;'>{badge_text}</span>
            </td>
            <td style='padding:12px;color:#00c8ff;font-family:Orbitron,monospace;font-size:10px;'>{int(c['confidence']*100)}%</td>
        </tr>
        """
    
    table_html = f"""
    <table style='width:100%;border-collapse:collapse;background:#0a1628;border:1px solid #0d2844;'>
        <thead>
            <tr style='background:#0d284440;text-align:left;'>
                <th style='padding:12px;color:#4a7a9b;font-family:Share Tech Mono,monospace;font-size:10px;'>ORIGINAL WORD</th>
                <th style='padding:12px;color:#4a7a9b;font-family:Share Tech Mono,monospace;font-size:10px;'>CORRECTED WORD</th>
                <th style='padding:12px;color:#4a7a9b;font-family:Share Tech Mono,monospace;font-size:10px;'>ERROR TYPE</th>
                <th style='padding:12px;color:#4a7a9b;font-family:Share Tech Mono,monospace;font-size:10px;'>CONFIDENCE</th>
            </tr>
        </thead>
        <tbody>
            {rows}
        </tbody>
    </table>
    """
    return table_html

def create_correction_table(corrections):
    """
    Converts correction list to a DataFrame for display.
    """
    if not corrections:
        return pd.DataFrame(columns=["Original Word", "Corrected Word", "Error Type", "Confidence"])
    
    # We only take the first 4 fields as requested
    table_data = []
    for c in corrections:
        table_data.append({
            "Original Word": c['original'],
            "Corrected Word": c['corrected'],
            "Error Type": c['type'],
            "Confidence": c['confidence']
        })
    
    return pd.DataFrame(table_data)

def calculate_accuracy(total_words, errors_found):
    """
    Rough accuracy calculation for checking spelling errors.
    """
    if total_words == 0:
        return 100.0
    return round(((total_words - errors_found) / total_words) * 100, 2)
