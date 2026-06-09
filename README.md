# IDE Human Typing Coder

这是一个本地测试用的 IDE 打字模拟器。它不会自动寻找窗口，也不会在后台隐藏运行；你需要自己打开 VS Code 或 IDEA 的编辑器，倒计时期间手动聚焦目标文件，然后程序才会用键盘事件输入内容。

它会随机生成 Python、Java、Markdown、Skill 文档等内容，并使用不固定节奏输入：

- 每个字符、单词、换行后的等待时间都有随机抖动。
- 会分批输入，中间随机停顿，模拟短暂思考。
- 可选地制造少量拼写错误，再用退格修正。
- 支持全局热键暂停、继续和停止。

请只把它用于本机自动化和交互测试，不要用于伪造人工工作状态或绕过监控。

## 快速开始

正常情况下不需要额外配置。clone 后执行这几条命令即可：

```powershell
git clone https://github.com/Cathyqg/coding-auto.git
cd coding-auto

python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

如果 PowerShell 不允许激活虚拟环境，先运行：

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\.venv\Scripts\Activate.ps1
```

推荐第一次这样运行，默认只生成 Python 内容，并带浏览器休息但不点击网页：

```powershell
python -m human_typing_coder --browser-breaks --browser-clicks 0 --profile normal
```

如果要运行至少 1 小时，并混合生成 Python、Java、Markdown、Skill 内容：

```powershell
python -m human_typing_coder --session-minutes 60 --browser-breaks --browser-clicks 0 --content-types python java markdown skill --profile normal
```

运行前先打开 VS Code 或 IDEA，打开一个目标文件或草稿文件。命令启动后会倒计时，倒计时期间点击 IDE 的代码编辑区域，让光标停在你希望开始输入的位置。

## 参数怎么选

你一般只需要改下面几个参数。

`--profile normal`

打字速度档位：

- `careful`：慢一点，停顿更多
- `normal`：默认，比较自然
- `fast`：快一点，停顿更少

`--browser-breaks`

开启“写一段代码后切到浏览器看一会儿再回来”的模拟。不加这个参数时，只会写代码，不会打开浏览器。

`--browser-clicks 0`

浏览器休息时只移动鼠标和滚动页面，不随机点击网页内容。这个最稳，推荐先用。

`--content-types python java markdown skill`

控制生成内容类型。可以只写一个，也可以写多个：

- `python`：生成 Python 示例代码
- `java`：生成 Java 示例代码
- `markdown`：生成 Markdown 笔记
- `skill`：生成类似 `SKILL.md` 的技能说明文档

默认只生成 `python`。混合生成时建议打开普通草稿文件，或者确认你能接受不同语言内容写在同一个编辑器里。

`--session-minutes 60`

持续生成和输入内容，直到总运行时间至少达到 60 分钟。代码输入和浏览器休息都算在这个总时间里。你可以改成其他时间，例如 `--session-minutes 30` 或 `--session-minutes 90`。

`--min-lines 80 --max-lines 140`

每一段随机生成 80 到 140 行内容。不写也可以，默认是 70 到 130 行。

`--countdown 8`

开始前倒计时 8 秒，给你时间切到 IDE 并点击编辑器。默认就是 8 秒。

常用组合：

```powershell
# 推荐：写代码 + 浏览器休息 + 不点击网页
python -m human_typing_coder --browser-breaks --browser-clicks 0 --profile normal

# 至少跑 1 小时，混合生成 Python、Java、Markdown、Skill
python -m human_typing_coder --session-minutes 60 --browser-breaks --browser-clicks 0 --content-types python java markdown skill --profile normal

# 跑 30 分钟，只生成 Python 和 Markdown
python -m human_typing_coder --session-minutes 30 --browser-breaks --browser-clicks 0 --content-types python markdown

# 写少一点
python -m human_typing_coder --profile normal --min-lines 40 --max-lines 80

# 写多一点
python -m human_typing_coder --profile normal --min-lines 150 --max-lines 260

# 只写代码，不打开浏览器
python -m human_typing_coder --profile normal

# 浏览器休息时允许少量页面表面点击
python -m human_typing_coder --browser-breaks --profile normal
```

默认不传 `--seed` 时，每次启动都会生成不同内容。只有你显式传 `--seed 42` 这类固定随机种子时，才会更容易复现同一批内容和节奏。

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

预览混合内容：

```powershell
python -m human_typing_coder --preview --content-types python java markdown skill
```

## 开始输入

1. 打开 VS Code 或 IDEA。
2. 新建或打开一个目标文件。只生成 Python 时可以用 `.py`；混合内容时建议用普通草稿文件。
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

# 混合生成 Python、Java、Markdown、Skill
python -m human_typing_coder --content-types python java markdown skill

# 至少运行 1 小时
python -m human_typing_coder --session-minutes 60 --browser-breaks --browser-clicks 0 --content-types python java markdown skill

# 设置安全运行上限，避免意外长时间运行
python -m human_typing_coder --max-minutes 5
```

注意：`--max-minutes` 只是安全上限，不是固定写代码时间。实际停止点由生成内容长度、随机停顿和你的停止热键共同决定。使用 `--session-minutes` 时，如果目标时长超过默认安全上限，程序会自动把安全上限延后 5 分钟。

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
