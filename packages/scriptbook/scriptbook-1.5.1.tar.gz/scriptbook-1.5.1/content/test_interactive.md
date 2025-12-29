# 交互式输入测试

这个文档测试交互式输入功能。

## 1. read命令测试

`read`命令等待用户输入：

```bash {"title": "read命令测试"}
echo "请输入你的名字："
read name
echo "你好, $name!"
```

## 2. 交互式程序测试

使用`cat`等待输入（Ctrl+D结束）：

```bash {"title": "cat交互测试"}
echo "输入一些文本，按Ctrl+D结束："
cat
```

## 3. 多行输入测试

使用`while read`循环：

```bash {"title": "多行输入测试"}
echo "输入多行文本，输入'end'结束："
while read line; do
    if [ "$line" = "end" ]; then
        break
    fi
    echo "你输入了: $line"
done
```

## 4. 密码输入测试

使用`-s`选项隐藏输入：

```bash {"title": "密码输入测试"}
echo "请输入密码："
read -s password
echo "密码已接收（不显示）"
```