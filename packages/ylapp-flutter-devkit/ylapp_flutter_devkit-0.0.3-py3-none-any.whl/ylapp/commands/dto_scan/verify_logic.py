import re
from typing import Optional, Set

# --- Copied Logic from gdto_scan.py ---

# `_G_MAP_KEY_RE`：匹配序列化 map 中的键名（形如 "field": ...）
_G_MAP_KEY_RE = re.compile(r"""['"]([A-Za-z_]\w*)['"]\s*:""")
# `_G_JSON_ACCESS_RE`：匹配 `json['field']` 访问的字段名
_G_JSON_ACCESS_RE = re.compile(r"""json\[['"]([A-Za-z_]\w*)['"]\]""")
# `_FIELD_DECL_RE`：在主文件内匹配字段声明，捕获修饰符以支持过滤 static
_FIELD_DECL_RE = re.compile(
    r"""^[ \t]*((?:(?:static|final|const|late)\s+)*)[\w<>\?\[\],\.]+\s+([A-Za-z_]\w*)\s*(?:[;=])""",
    re.MULTILINE,
)

def _strip_comments(content: str) -> str:
    """移除多行与单行注释，避免注释内的关键字误判为字段。"""
    content = re.sub(r"/\*.*?\*/", "", content, flags=re.S)
    content = re.sub(r"//.*", "", content)
    return content

def _extract_main_fields(main_content: str) -> Optional[Set[str]]:
    """从主文件中提取字段声明集合；解析失败返回 None 以触发上层的“字段解析失败”提示。"""
    try:
        cleaned = _strip_comments(main_content)
        fields: Set[str] = set()
        for line in cleaned.splitlines():
            line = line.strip()
            if not line or "(" in line:  # 跳过方法/构造函数等含括号的行
                continue
            match = _FIELD_DECL_RE.match(line)
            if match:
                modifiers = match.group(1) or ""
                field_name = match.group(2)
                # 过滤 static 字段和私有字段
                if "static" in modifiers:
                    continue
                if field_name.startswith("_"):
                    continue
                fields.add(field_name)
        return fields
    except Exception:
        return None

def _extract_g_fields(g_content: str) -> Optional[Set[str]]:
    """从生成文件中提取字段名（map 键 + json 下标访问）；异常时返回 None 供上层判定解析失败。"""
    try:
        cleaned = _strip_comments(g_content)
        fields: Set[str] = set(_G_MAP_KEY_RE.findall(cleaned))
        fields.update(_G_JSON_ACCESS_RE.findall(cleaned))
        return fields
    except Exception:
        return None

# --- Test Cases ---

def test_extraction():
    print("Running verification tests...")

    # Mock Main Dart File Content
    # 包含: 正常字段, static, const, final, private, 注释, 方法, 构造函数
    mock_main_dart = """
    import 'package:json_annotation/json_annotation.dart';

    part 'user_dto.g.dart';

    @JsonSerializable()
    class UserDto {
        /// User ID (Should be extracted)
        int? id;

        // User Name (Should be extracted)
        final String? name;

        /* Multi-line comment 
           String? ignoredInComment; 
        */

        // Static field (Should be IGNORED)
        static const String tableName = "users";

        // Private field (Should be IGNORED)
        String? _internalToken;

        // Late field (Should be extracted)
        late String status;
        
        // Complex type (Should be extracted)
        List<Map<String, int>>? complexData;

        // Constructor (Should be IGNORED due to parenthesis check)
        UserDto({this.id, this.name});

        // Method (Should be IGNORED)
        void update() {
            var temp = "test";
        }
        
        // Function type field (Should be extracted ideally, or ignored? usually DTOs don't have function fields but let's see regex behavior)
        // Regex expects type then name. 'Function? callback;'
        final Function? callback;
    }
    """

    # Mock Generated Dart File Content
    # 包含: json['key'] 读取 和 'key': value 写入
    # 模拟场景: 
    # - id: 存在
    # - name: 存在
    # - status: 存在
    # - complexData: 存在
    # - callback: 缺失 (Simulate MISSING in g.dart)
    # - extraField: 多余 (Simulate EXTRA in g.dart)
    mock_g_dart = """
    // GENERATED CODE - DO NOT MODIFY BY HAND

    part of 'user_dto.dart';

    // **************************************************************************
    // JsonSerializableGenerator
    // **************************************************************************

    UserDto _$UserDtoFromJson(Map<String, dynamic> json) => UserDto(
          id: json['id'] as int?,
          name: json['name'] as String?,
          status: json['status'] as String,
          complexData: (json['complexData'] as List<dynamic>?)
              ?.map((e) => (e as Map<String, dynamic>).map(
                    (k, v) => MapEntry(k, v as int),
                  ))
              .toList(),
          // extraField is accessed here
          extraParam: json['extraField'],
        );

    Map<String, dynamic> _$UserDtoToJson(UserDto instance) => <String, dynamic>{
          'id': instance.id,
          'name': instance.name,
          'status': instance.status,
          'complexData': instance.complexData,
          'extraField': instance.extraParam,
        };
    """

    # 1. Test Main Extraction
    print("\n[Test 1] Extracting Main Fields...")
    main_fields = _extract_main_fields(mock_main_dart)
    print(f"Extracted Main Fields: {main_fields}")
    
    expected_main = {"id", "name", "status", "complexData", "callback"}
    # static 'tableName' should be ignored
    # private '_internalToken' should be ignored
    # constructor/methods should be ignored
    
    assert main_fields is not None
    
    # 检查期望字段是否都存在
    missing_in_result = expected_main - main_fields
    unexpected_in_result = main_fields - expected_main
    
    if not missing_in_result and not unexpected_in_result:
        print("✅ Main extraction PASS")
    else:
        print("❌ Main extraction FAIL")
        if missing_in_result:
            print(f"   Missing expected fields: {missing_in_result}")
        if unexpected_in_result:
            print(f"   Unexpected extracted fields: {unexpected_in_result}")

    # 2. Test Generated Extraction
    print("\n[Test 2] Extracting G Fields...")
    g_fields = _extract_g_fields(mock_g_dart)
    print(f"Extracted G Fields: {g_fields}")
    
    expected_g = {"id", "name", "status", "complexData", "extraField"}
    
    assert g_fields is not None
    
    missing_in_g = expected_g - g_fields
    unexpected_in_g = g_fields - expected_g
    
    if not missing_in_g and not unexpected_in_g:
        print("✅ G extraction PASS")
    else:
        print("❌ G extraction FAIL")
        if missing_in_g:
            print(f"   Missing expected fields: {missing_in_g}")
        if unexpected_in_g:
            print(f"   Unexpected extracted fields: {unexpected_in_g}")

    # 3. Test Diff Logic
    print("\n[Test 3] Testing Diff Logic...")
    
    # Calculate Extra (In G but not in Main) -> 'extraField'
    extra_fields = sorted(g_fields - main_fields)
    expected_extra = ["extraField"]
    
    # Calculate Missing (In Main but not in G) -> 'callback'
    missing_fields = sorted(main_fields - g_fields)
    expected_missing = ["callback"]
    
    print(f"Calculated Extra: {extra_fields}")
    print(f"Calculated Missing: {missing_fields}")
    
    if extra_fields == expected_extra and missing_fields == expected_missing:
        print("✅ Diff Logic PASS")
    else:
        print("❌ Diff Logic FAIL")
        if extra_fields != expected_extra:
             print(f"   Expected Extra: {expected_extra}, Got: {extra_fields}")
        if missing_fields != expected_missing:
             print(f"   Expected Missing: {expected_missing}, Got: {missing_fields}")

if __name__ == "__main__":
    test_extraction()