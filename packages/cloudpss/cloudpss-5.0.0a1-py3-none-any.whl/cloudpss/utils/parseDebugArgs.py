def parse_debug_args(debug=None):
    if not debug or not isinstance(debug, str):
        return None

    tokens = []

    # 1. 先按照非转义的空格拆分字符串，获取每个 token
    current_token = ''
    escaping = False  # 表示当前是否在处理转义字符

    for char in debug:
        if escaping:
            # 如果上一个字符是 '\'，则把当前字符直接添加到 token，并保留 '\' 以供二阶段使用
            current_token += '\\' + char
            escaping = False
        elif char == '\\':
            # 开始转义
            escaping = True
        elif char.isspace():
            # 如果遇到空格 (并且不在转义状态)，说明一个 token 结束
            if current_token:
                tokens.append(current_token)
                current_token = ''
        else:
            # 普通字符，直接添加
            current_token += char

    # 最后一个 token 加入数组（如果有的话）
    if current_token:
        tokens.append(current_token)

    if not tokens:
        return None

    # 2. 对每个 token，找第一个非转义的 '=' 分割 key/value
    entries = []

    for token in tokens:
        key = ''
        value = ''
        has_equal = False
        escaping = False

        # 我们只需要区分第一处真正的 '='
        for char in token:
            if escaping:
                # 处理转义字符
                if char == 'b':
                    escaped_char = '\b'
                elif char == 'f':
                    escaped_char = '\f'
                elif char == 'n':
                    escaped_char = '\n'
                elif char == 'r':
                    escaped_char = '\r'
                elif char == 't':
                    escaped_char = '\t'
                elif char == 'v':
                    escaped_char = '\v'
                else:
                    escaped_char = char
                
                # 直接添加当前字符
                if not has_equal:
                    key += escaped_char
                else:
                    if escaped_char in ['\\', '$']:
                        # 保留转义字符
                        value += '\\' + escaped_char
                    else:
                        value += escaped_char
                escaping = False
            elif char == '\\':
                escaping = True
            elif char == '=' and not has_equal:
                # 遇到第一个非转义的 '=' 时，视为 key/value 分隔
                has_equal = True
            else:
                # 普通字符
                if not has_equal:
                    key += char
                else:
                    value += char

        # 添加 key 和 value 到 entries 列表
        entries.append((key, value))

    return dict(entries)

# 示例用法
# debug_str = r"TASK_CMD=cloudpssrun:mkl DOCKER_MOUNT=/dev/disk/by-id:/dev/disk/by-id:ro\n/home/cloudpss/NR_ADPSS_HVDC37.key:/usr/include/NR_ADPSS_HVDC37.key:ro\n"
# result = parse_debug_args(debug_str)
# print(result)