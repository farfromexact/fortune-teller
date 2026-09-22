# 观变

《周易》启发的决策与复盘原型。它不作命运预言，也不替代医疗、法律或投资意见。

## 部署到 Streamlit Community Cloud

仓库：[farfromexact/fortune-teller](https://github.com/farfromexact/fortune-teller)

1. 将包含 `streamlit_app.py`、`guanbian_engine.py`、`guanbian_records.py`、`requirements.txt` 和 `app/iching.ts` 的改动推送到 GitHub 的 `main` 分支。
2. 在 [share.streamlit.io](https://share.streamlit.io/) 登录并创建应用，选择仓库 `farfromexact/fortune-teller`、分支 `main`、入口文件 `streamlit_app.py`。
3. 无需设置 API key 或 Secrets。依赖由根目录的 `requirements.txt` 安装；样式由 `.streamlit/config.toml` 配置。

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
- 六次投掷、卦象、变卦、追问、行动与复盘流程均可使用。问题文本目前仍不影响随机卦象，也尚未驱动个性化解读。
- Streamlit Community Cloud 不保证本地文件持久化，本版**不提供账号同步**。档案仅存在当前会话；用户需下载 JSON 备份，并在之后导入。不要将个人问题写入公开仓库。
- 原网页保存在浏览器 `localStorage` 中的旧记录不会自动迁移到 Streamlit 版；切换后仍可在原网页查看，但这版导入仅接受自己下载的观变 JSON 备份。
- 内容卡片是现代编辑性转译，不冒充《周易》卦辞、爻辞或古注。逐条校勘完成前只提供[原典索引](https://ctext.org/book-of-changes)。

## 原网页版本

如需继续开发 React/Vinext 版本：

```powershell
npm install
npm run dev
npm run build
```
