

def read(stream, streamer):
    index = 0
    empty = b''
    stream_len = len(stream)
    cp_stream = stream
    matched_index = streamer.matched_index
    key = streamer.key
    is_started = streamer.is_started
    in_double_quotation = streamer.in_double_quotation
    in_escape = streamer.in_escape
    lbrace = streamer.lbrace
    rbrace = streamer.rbrace
    finished = False
    
    for i in range(stream_len):
        c = cp_stream[i]
        if 0 < matched_index < len(key) and c != key[matched_index]:
            matched_index = 0
        if in_double_quotation and not is_started and matched_index < len(key) and c == key[matched_index]:
            matched_index += 1

        if c == ord('\\'):
            if not in_escape:
                in_escape = True
            else:
                in_escape = False
            index += 1
            continue

        if not in_escape and c == ord('"') and not in_double_quotation:
            in_double_quotation = True
        elif not in_escape and c == ord('"') and in_double_quotation:
            in_double_quotation = False

        if not in_double_quotation and is_started and (c == ord('{') or c == ord('[')):
            lbrace += 1

        if not in_double_quotation and is_started and (c == ord('}') or c == ord(']')):
            rbrace += 1

        # for value with brace
        if is_started and lbrace > 0 and rbrace > 0 and lbrace - rbrace == 0:
            finished = True
            index += 1
            break

        # other
        if is_started and not in_double_quotation and c == ord(',') and lbrace == 0 and rbrace == 0:
            finished = True
            break

        if is_started and not in_double_quotation and (c == ord('}') or c == ord(']')) and lbrace == 0 and rbrace == 1:
            finished = True
            break

        index += 1

        if len(key) == matched_index and not is_started and c == ord(':'):
            is_started = True
            stream = stream[index:]
            index = 0

        if in_escape:
            in_escape = False

    if is_started:
        streamer.finished = finished
        stream = stream[:index]
        if not finished:
            streamer.matched_index = matched_index
            streamer.key = key
            streamer.is_started = is_started
            streamer.in_double_quotation = in_double_quotation
            streamer.in_escape = in_escape
            streamer.lbrace = lbrace
            streamer.rbrace = rbrace
        return stream
    else:
        streamer.matched_index = matched_index
        streamer.key = key
        streamer.is_started = is_started
        streamer.in_double_quotation = in_double_quotation
        streamer.in_escape = in_escape
        streamer.lbrace = lbrace
        streamer.rbrace = rbrace
        streamer.is_started = is_started
        return empty
