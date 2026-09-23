# 观变

《周易》启发的决策与复盘原型。它不作命运预言，也不替代医疗、法律或投资意见。

## 部署到 Streamlit Community Cloud

仓库：[farfromexact/fortune-teller](https://github.com/farfromexact/fortune-teller)

1. 将应用代码、`guanbian_*.py`、`requirements.txt` 和 `app/iching.ts` 推送到 GitHub 的 `main` 分支，**不推送密钥**。
2. 在 [share.streamlit.io](https://share.streamlit.io/) 登录并创建应用，选择仓库 `farfromexact/fortune-teller`、分支 `main`、入口文件 `streamlit_app.py`。
3. 基础功能无需密钥；启用 AI 时，在应用的 Secrets 中填写下方配置。依赖由根目录的 `requirements.txt` 安装；样式由 `.streamlit/config.toml` 配置。

```toml
DEEPSEEK_API_KEY = "替换为你自己的密钥"
DEEPSEEK_MODEL = "deepseek-flash"
```

本地可复制 `.streamlit/secrets.toml.example` 为 `.streamlit/secrets.toml` 再填写；真实文件已被 Git 忽略。也支持同名环境变量（优先于 Secrets）。本地 Secrets **不会自动部署到 Community Cloud**，需要在云端单独设置。密钥曾通过聊天或其他公开渠道发送时，建议在 DeepSeek 后台轮换。

本地预览：

```powershell
python -m pip install -r requirements.txt
python -m streamlit run streamlit_app.py
```

本地测试：

```powershell
python -m unittest discover -s tests -p "test_*.py"
```

### 与原网页版本的区别

- Streamlit 入口是独立的 Python 界面；原来的 Next.js/Vinext 代码仍保留，不会直接在 Streamlit 上运行。
- 六十四卦名称、卦象、现代主题与行动建议直接读取 `app/iching.ts`，避免维护两套会漂移的数据；若原始目录格式变化，启动会明确报错。
- 问题和可选生辰背景用于 DeepSeek 个性化建议，不影响六次随机投掷。未启用模型时显示明确标记的基础反思提示。
- Streamlit Community Cloud 不保证本地文件持久化，本版**不提供账号同步**。档案仅存在当前会话；用户需下载 JSON 备份，并在之后导入。不要将个人问题写入公开仓库。
- 原网页保存在浏览器 `localStorage` 中的旧记录不会自动迁移到 Streamlit 版；切换后仍可在原网页查看，但这版导入仅接受自己下载的观变 JSON 备份。
- 内容卡片是现代编辑性转译，不冒充《周易》卦辞、爻辞或古注。逐条校勘完成前只提供[原典索引](https://ctext.org/book-of-changes)。

### DeepSeek 解读与数据边界

- 仅在点击“生成建议”或“发送追问”时，由服务端请求官方 `https://api.deepseek.com/chat/completions`。使用 [JSON mode](https://api-docs.deepseek.com/guides/json_mode/)，并校验字段、长度、完成状态和固定卦象 ID；校验不通过、超时、余额不足等会显示错误，不伪造成功，也不自动重复扣费请求。
- 向模型发送问题、本卦/变卦、由下至上的爻值、动爻位置、现代编辑主题、可选四柱，以及追问所需的原回答。不发送 API 密钥到浏览器，不发送原始生日到模型。回答作为纯文本展示。
- 模型给出五段式建议和可选的生辰反思；三次追问沿用原卦，原回答保持不变。保存时保留模型名称、提示词版本、时间、上下文指纹及回答快照，复盘不会重新调用模型。
- 对命中的医疗、法律、投资、自伤、人身安全问题，使用本地边界提示，不发送模型请求。关键词识别和提示词不能保证覆盖所有变体；模型也仍可能出错，不适合作为高风险决策依据。
- 原型每会话最多 12 次模型请求；这不是抗滥用、全站限额或付费体系。公开推广前需另加登录、服务端限流/总预算和内容评估；在模型平台设置可承受的预算，勿直接无限开放付费密钥。

### 可选生辰背景

- 默认“不提供”；支持公历日期 + 可选时刻自动排盘，或用户手动填三/四柱。不会要求姓名、性别、身份证或出生地。
- 采用 [lunar-python 1.4.8](https://github.com/6tail/lunar-python)（MIT）：固定 UTC+8、立春换年、节令换月、日柱零点换日（sect=2）。晚子时时柱沿用该库的规则。不自动校正真太阳时或历史夏令时；境外或历史夏令时出生者需先换算。
- 时间不详时不填时柱；若当日首尾年/月柱不同，也留空相应柱，避免伪精确。手填仅检查六十甲子格式，不证明四柱历法一致。
- 原始生日只在会话中用于排盘；保存/导出只含派生四柱、规则和不确定性说明。四柱仍属个人信息，请私密保管备份。此功能增加互动和文化背景，**不代表预测准确率提高**，不推演大运、命格吉凶或终身命运。

### 铜钱仪式、风向卡与短答案

- 起卦台采用本地 SVG 铜钱、CSS 3D 翻转与落定动效；每次三枚钱面的 2/3 值由 Python 服务端独立生成，动画展示的正反面、成爻总数和档案记录共用同一结果。重复事件按本次起卦 ID + 投掷序号去重，不因动画或网络重试改卦。六次完成后由用户进入结果，保留最后一次动画。
- 提供“简洁模式”，也尊重浏览器的 `prefers-reduced-motion` 设置。简洁模式保留原生 Streamlit 投掷按钮；没有动画也能完成全部流程。没有声音、外部图片或动效服务请求。
- 结果页展示“此问风向”卡，内容来自现有卦象目录的现代编辑性提示，不是个人预测，也不是每日运势。可在浏览器本地生成 1080 × 1350 PNG，另有 SVG 备用下载；图片不包含问题、生辰、AI 私人建议或档案编号。
- 新 AI 提示词 v2 在同一次请求中生成短答案与完整解读。短答案展示关注点、第一项行动和重新考虑的现实信号；第一项行动直接使用详细回答的原字段，避免两套建议。完整解读默认折叠。旧 v1 快照仍能导入，仅展示原文摘录，不重新调用模型或改写历史。
- `assets/ritual.html`、`assets/ritual.css`、`assets/ritual.js` 和 `assets/wind_export.js` 必须随应用部署。交互采用 [Streamlit Components v2](https://docs.streamlit.io/develop/concepts/custom-components/components-v2/examples)，依赖版本仍为 `streamlit==1.56.0`。

组件及规则回归测试：

```powershell
python -m unittest discover -s tests -p "test_*.py"
node --experimental-strip-types --test --test-isolation=none tests/iching-engine.test.mjs tests/ritual-component.test.mjs
```

### 记录版本与爻序修正

新记录使用引擎 v2：六次投掷由下至上，目录二进制由上至下，映射前反转爻序。已加入屯、蒙、泰、否和单动爻回归测试，以及 4096 种六爻状态测试。

JSON 备份 v2 保存可选生辰、AI 快照和追问，仍可导入 v1。旧记录保留当时的 v1 卦名映射并展示错误提示，不悄悄改写历史。原 React 网页也修正了新起卦映射并保留旧记录版本。备份上限 5 MB / 100 条；不包含密钥。

## 原网页版本

如需继续开发 React/Vinext 版本：

```powershell
npm install
npm run dev
npm run build
```
