import never_jscore

ctx = never_jscore.Context()

# 注入 hook
ctx.compile('''
      function aaa(body) {
          $terminate({ body: body });
      };
  ''')

# 第一次执行
ctx.clear_hook_data()  # ⚠️ 清空旧数据（可选，如果是第一次可以省略）
try:
    ctx.evaluate('aaa("data1")')
except:
    pass
data1 = ctx.get_hook_data()  # 获取第一次的数据
print(data1)  # {"body": "data1"}

# 第二次执行
ctx.clear_hook_data()  # ⚠️ 清空第一次的数据
try:
    ctx.evaluate('aaa("data2")')
except:
    pass
data2 = ctx.get_hook_data()  # 获取第二次的数据
print(data2)  # {"body": "data2"}

# 可以多次读取同一个数据
data2_again = ctx.get_hook_data()  # 仍然是 {"body": "data2"}