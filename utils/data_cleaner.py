

def extract_features(raw_packet: dict):
    
    features = [
        len(raw_packet['src_ip']),
        len(raw_packet['dst_ip']),
        1 if raw_packet['protocol'] == 'TCP' else 0,
        raw_packet['packet_size'],
        1 if raw_packet['flags'] == 'SYN' else 0,
        raw_packet['payload_entropy']
    ]
    return features
