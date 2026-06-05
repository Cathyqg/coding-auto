# IDE Human Typing Coder

这是一个本地测试用的 IDE 打字模拟器。它不会自动寻找窗口，也不会在后台隐藏运行；你需要自己打开 VS Code 或 IDEA 的编辑器，倒计时期间手动聚焦目标 `.py` 文件，然后程序才会用键盘事件输入代码。

它会随机生成一段 Python 示例代码，并使用不固定节奏输入：

- 每个字符、单词、换行后的等待时间都有随机抖动。
- 会分批输入，中间随机停顿，模拟短暂思考。
- 可选地制造少量拼写错误，再用退格修正。
- 支持全局热键暂停、继续和停止。

请只把它用于本机自动化和交互测试，不要用于伪造人工工作状态或绕过监控。

## 安装

在 PowerShell 中进入项目目录：

```powershell
cd D:\llm\auto-coding
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

如果你的 PowerShell 禁止激活虚拟环境，可以先执行：

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\.venv\Scripts\Activate.ps1
```

## 预览会输入什么

```powershell
python -m human_typing_coder --preview
```

## 开始输入

1. 打开 VS Code 或 IDEA。
2. 新建或打开一个空的 Python 文件。
3. 在终端运行：

```powershell
python -m human_typing_coder --profile normal --min-lines 80 --max-lines 140 --countdown 8
```

4. 倒计时开始后，点击 IDE 里的代码编辑区域，让光标停在你希望开始输入的位置。

默认热键：

- 暂停/继续：`Ctrl+Alt+P`
- 停止：`Ctrl+Alt+Q`
- 紧急停止：把鼠标移动到屏幕左上角，触发 PyAutoGUI failsafe

## 常用参数

```powershell
# 更慢、更像谨慎输入
python -m human_typing_coder --profile careful

# 更快输入，不制造错字
python -m human_typing_coder --profile fast --no-typos

# 指定输入你自己的文件内容
python -m human_typing_coder --source-file D:\tmp\demo.py --profile normal

# 固定随机种子，方便复现同一段代码和节奏
python -m human_typing_coder --seed 42

# 设置安全运行上限，避免意外长时间运行
python -m human_typing_coder --max-minutes 5
```

注意：`--max-minutes` 只是安全上限，不是固定写代码时间。实际停止点由生成内容长度、随机停顿和你的停止热键共同决定。

## 模拟浏览器和鼠标休息

默认不启用浏览器/鼠标动作。需要时显式加 `--browser-breaks`：

```powershell
python -m human_typing_coder --browser-breaks --profile normal
```

开启后，程序会在随机字符间隔后按概率触发一次“浏览器休息”：

- 打开一个本地安全网页 `browser_break_page.html`
- 随机移动鼠标、滚动页面、做少量页面表面点击
- 随机停留一段时间
- 通过 `Alt+Tab` 返回上一个窗口，也就是 IDE

可调参数：

```powershell
# 每写 300 到 700 个字符时考虑一次浏览器休息，触发概率 60%
python -m human_typing_coder --browser-breaks --break-every-chars 300 700 --break-chance 0.6

# 每次浏览器休息停留 5 到 15 秒
python -m human_typing_coder --browser-breaks --break-seconds 5 15

# 只移动和滚动，不点击页面
python -m human_typing_coder --browser-breaks --browser-clicks 0

# 使用你指定的网页，可重复传多个
python -m human_typing_coder --browser-breaks --break-url https://docs.python.org/3/

# 如果 Alt+Tab 回来后 IDE 没有获得焦点，可以指定返回后点击 IDE 的屏幕坐标
python -m human_typing_coder --browser-breaks --return-click 900,520
```

如果使用真实外部网页，建议先用 `--browser-clicks 0`，因为普通网页里按钮、链接、表单很多，随机点击可能产生副作用。
