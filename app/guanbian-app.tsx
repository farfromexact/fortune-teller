"use client";

import { useEffect, useMemo, useState } from "react";
import { castLine, lineLabel, resolveReading, SOURCE_NOTE, type LineValue } from "./iching";

type Stage = "ask" | "cast" | "reading" | "journal";
type SavedReading = {
  id: string;
  question: string;
  lines: LineValue[];
  createdAt: string;
  action?: string;
  reviewDate?: string;
  reflection?: string;
  engineVersion?: 1 | 2;
};

const prompts = ["我是否应该接受这份新工作？", "这段关系中，我真正需要看清什么？", "这个合作现在适合继续推进吗？"];
const sensitive = /(自杀|自残|轻生|急救|胸痛|癌症|确诊|用药|律师|诉讼|买入|卖出|股票|期货|币圈|贷款)/;

function Yao({ value, small = false }: { value: LineValue; small?: boolean }) {
  const yang = value === 7 || value === 9;
  const moving = value === 6 || value === 9;
  return (
    <div className={`yao ${small ? "small" : ""} ${moving ? "moving" : ""}`} aria-label={lineLabel(value)}>
      {yang ? <span className="solid" /> : <><span /><span /></>}
      {moving && <b>{value === 9 ? "○" : "×"}</b>}
    </div>
  );
}

export default function GuanbianApp({ user }: { user: { displayName: string } | null }) {
  const [stage, setStage] = useState<Stage>("ask");
  const [question, setQuestion] = useState("");
  const [lines, setLines] = useState<LineValue[]>([]);
  const [saved, setSaved] = useState<SavedReading[]>([]);
  const [action, setAction] = useState("");
  const [reviewDays, setReviewDays] = useState<7 | 30>(7);
  const [reflection, setReflection] = useState("");
  const [followup, setFollowup] = useState("");
  const [followups, setFollowups] = useState<string[]>([]);
  const reading = useMemo(() => lines.length === 6 ? resolveReading(lines) : null, [lines]);
  const highRisk = sensitive.test(question);

  useEffect(() => {
    const data = localStorage.getItem("guanbian-readings");
    if (data) {
      try { setSaved(JSON.parse(data)); } catch { /* ignore malformed local draft */ }
    }
  }, []);

  function begin() {
    if (question.trim().length < 8) return;
    setLines([]);
    setStage("cast");
  }

  function toss() {
    if (lines.length >= 6) return;
    const next = [...lines, castLine()];
    setLines(next);
    if (next.length === 6) window.setTimeout(() => setStage("reading"), 650);
  }

  async function saveReading() {
    if (!reading) return;
    const reviewDate = new Date(Date.now() + reviewDays * 86400000).toISOString();
    const record: SavedReading = {
      id: reading.stableId + "-" + Date.now(),
      question,
      lines,
      action: action.trim(),
      reviewDate,
      createdAt: new Date().toISOString(),
      engineVersion: 2,
    };
    const next = [record, ...saved.filter((item) => item.question !== question)];
    setSaved(next);
    localStorage.setItem("guanbian-readings", JSON.stringify(next));
    if (user) {
      await fetch("/api/readings", { method: "POST", headers: { "content-type": "application/json" }, body: JSON.stringify(record) }).catch(() => null);
    }
    setStage("journal");
  }

  function answerFollowup() {
    if (!followup.trim()) return;
    setFollowups((items) => [...items, followup.trim()]);
    setFollowup("");
  }

  function addReflection(id: string) {
    const next = saved.map((item) => item.id === id ? { ...item, reflection } : item);
    setSaved(next);
    localStorage.setItem("guanbian-readings", JSON.stringify(next));
    setReflection("");
  }

  const currentSaved = saved[0];

  return (
    <main>
      <header>
        <button className="brand" onClick={() => setStage("ask")} aria-label="返回首页">
          <span className="seal">观</span>
          <span><strong>观变</strong><small>以易观时 · 以行验知</small></span>
        </button>
        <div className="header-actions">
          <button className="text-button" onClick={() => setStage("journal")}>变化档案 <em>{saved.length}</em></button>
          {user ? <span className="user">{user.displayName.slice(0, 1)}</span> : <a className="login" href="/signin-with-chatgpt?return_to=%2F">登录同步</a>}
        </div>
      </header>

      {stage === "ask" && (
        <section className="hero">
          <div className="hero-mark" aria-hidden="true"><i /><i /><i /><i /><i /><i /></div>
          <p className="eyebrow">在不确定中，看见变化的方向</p>
          <h1>此刻，你想看清<br /><span>哪一个选择？</span></h1>
          <p className="intro">观变不替你预言命运。它借《周易》的变化视角，帮你整理处境、风险与下一步行动。</p>
          <div className="ask-card">
            <label htmlFor="question">写下一个真实而具体的问题</label>
            <textarea id="question" value={question} onChange={(e) => setQuestion(e.target.value)} maxLength={180} placeholder="例如：我是否应该在未来三个月内转换工作方向？" />
            <div className="ask-foot"><span>{question.length}/180</span><button disabled={question.trim().length < 8} onClick={begin}>开始观变 <b>→</b></button></div>
          </div>
          <div className="examples">
            <span>不知道怎么问？</span>
            {prompts.map((prompt) => <button key={prompt} onClick={() => setQuestion(prompt)}>{prompt}</button>)}
          </div>
          <div className="principles"><span>不作绝对预言</span><span>经典出处可查</span><span>结果留待行动验证</span></div>
        </section>
      )}

      {stage === "cast" && (
        <section className="casting">
          <button className="back" onClick={() => setStage("ask")}>← 修改问题</button>
          <p className="eyebrow">三枚铜钱 · 六次成卦</p>
          <h1>让问题安静下来</h1>
          <p className="question-preview">“{question}”</p>
          <div className="hex-build">
            {[5,4,3,2,1,0].map((index) => (
              <div className="line-row" key={index}>
                <span>{["初","二","三","四","五","上"][index]}</span>
                {lines[index] ? <Yao value={lines[index]} /> : <div className="empty-line" />}
                <small>{lines[index] ? lineLabel(lines[index]) : "待投"}</small>
              </div>
            ))}
          </div>
          <div className={`coins ${lines.length > 0 ? "active" : ""}`} aria-hidden="true"><i>阴</i><i>阳</i><i>变</i></div>
          <button className="toss" onClick={toss} disabled={lines.length >= 6}>
            {lines.length < 6 ? `第 ${lines.length + 1} 次投掷` : "卦象已成"}
          </button>
          <p className="ritual-note">结果由三枚虚拟铜钱独立随机生成，并保留完整投掷记录。</p>
        </section>
      )}

      {stage === "reading" && reading && (
        <section className="reading">
          <button className="back" onClick={() => setStage("ask")}>← 新的问题</button>
          <div className="reading-head">
            <div>
              <p className="eyebrow">第 {reading.primary.number} 卦</p>
              <h1><span>{reading.primary.unicode}</span> {reading.primary.name}</h1>
              <p>{reading.primary.theme}</p>
            </div>
            <div className="change-map">
              <div><strong>本卦</strong>{[...lines].reverse().map((line, i) => <Yao key={i} value={line} small />)}<b>{reading.primary.name}</b></div>
              <span>→<small>{reading.moving.length ? `${reading.moving.join("、")}爻动` : "无动爻"}</small></span>
              <div><strong>变卦</strong>{[...lines].reverse().map((line, i) => <Yao key={i} value={line === 6 ? 7 : line === 9 ? 8 : line} small />)}<b>{reading.changed.name}</b></div>
            </div>
          </div>

          {highRisk && <div className="boundary"><strong>先处理现实中的专业问题</strong><p>这个问题涉及健康、法律、投资或人身安全。以下内容只能帮助梳理想法，不能代替医生、律师、持牌顾问或紧急援助。</p></div>}

          <div className="reading-grid">
            <article><span>01</span><h2>当前局势</h2><p>你正处在“{reading.primary.theme}”的阶段。关键不是立刻得到确定答案，而是辨认哪些条件已经成熟，哪些仍由情绪或期待推动。</p></article>
            <article><span>02</span><h2>关键变化</h2><p>{reading.moving.length ? `第${reading.moving.join("、")}爻发生变化，局势由「${reading.primary.name}」趋向「${reading.changed.name}」。这提示行动会改变关系结构，需要为后续影响留出余地。` : `此卦没有动爻，主题集中在「${reading.primary.name}」本身。与其频繁换方向，更适合先稳定观察并验证当前判断。`}</p></article>
            <article><span>03</span><h2>机会与风险</h2><p>机会在于：{reading.changed.theme}。风险在于把象征当成保证，或只选择符合期待的信息。请用现实证据检验每一个重要判断。</p></article>
            <article className="action"><span>04</span><h2>建议行动</h2><p>{reading.primary.counsel}</p><label>写下一件你愿意验证的小事</label><input value={action} onChange={(e) => setAction(e.target.value)} placeholder="例如：本周约两位业内朋友聊聊真实情况" /></article>
            <article className="classic"><span>05</span><h2>经典依据</h2><div className="quote"><b>{reading.primary.unicode} 《周易》·{reading.primary.traditional}卦</b><p>{reading.primary.theme}</p></div><p className="source">{SOURCE_NOTE}</p><a href={`https://ctext.org/book-of-changes/${reading.primary.number === 1 ? "qian" : reading.primary.number === 2 ? "kun" : ""}`} target="_blank" rel="noreferrer">查看原典来源 ↗</a></article>
          </div>

          <div className="followup">
            <h2>继续追问这一个卦</h2>
            {followups.map((item, index) => <div className="followup-answer" key={item}><b>你问：{item}</b><p>这个追问仍应放回「{reading.primary.name} → {reading.changed.name}」的结构中理解。先区分你能影响的部分与只能观察的部分，再用一个低成本行动获取新信息。卦象不重新生成，原判断也不被悄悄替换。</p><small>基于本次卦象 · 第 {index + 1} 次追问</small></div>)}
            {followups.length < 3 && <div className="followup-input"><input value={followup} onChange={(e) => setFollowup(e.target.value)} placeholder="我最需要防范的盲点是什么？" /><button onClick={answerFollowup}>追问</button></div>}
          </div>

          <div className="save-bar">
            <div><strong>把判断交给时间验证</strong><span>在行动后回来，记录实际发生了什么。</span></div>
            <div className="review-choice"><button className={reviewDays === 7 ? "selected" : ""} onClick={() => setReviewDays(7)}>7天后</button><button className={reviewDays === 30 ? "selected" : ""} onClick={() => setReviewDays(30)}>30天后</button></div>
            <button className="save" onClick={saveReading}>保存到变化档案</button>
          </div>
        </section>
      )}

      {stage === "journal" && (
        <section className="journal">
          <div className="journal-head"><div><p className="eyebrow">变化档案</p><h1>答案不在卦里结束</h1><p>记录行动与结果，慢慢看清属于你自己的变化模式。</p></div><button onClick={() => setStage("ask")}>＋ 新的观变</button></div>
          {!saved.length ? <div className="empty-journal"><span>䷋</span><h2>还没有留下记录</h2><p>完成一次观变并写下行动，档案会从这里开始。</p><button onClick={() => setStage("ask")}>提出第一个问题</button></div> :
            <div className="timeline">
              {saved.map((item) => {
                const result = resolveReading(item.lines, item.engineVersion ?? 1);
                const due = item.reviewDate && new Date(item.reviewDate) <= new Date();
                return <article key={item.id}>
                  <div className="date"><b>{new Date(item.createdAt).getDate()}</b><span>{new Date(item.createdAt).toLocaleDateString("zh-CN", { month: "short" })}</span></div>
                  <div className="record">
                    {!item.engineVersion && <p>旧版记录：保留当时的卦名；旧爻序映射已在新版修正。</p>}
                    <div className="record-top"><span>{result.primary.unicode}</span><div><small>{result.primary.name} → {result.changed.name}</small><h2>{item.question}</h2></div><em className={due ? "due" : ""}>{due ? "等待复盘" : `${Math.max(1, Math.ceil((new Date(item.reviewDate || Date.now()).getTime() - Date.now()) / 86400000))} 天后复盘`}</em></div>
                    {item.action && <p className="record-action"><b>当时决定</b>{item.action}</p>}
                    {item.reflection ? <p className="reflection"><b>后来发生</b>{item.reflection}</p> :
                      <div className="reflect"><input value={reflection} onChange={(e) => setReflection(e.target.value)} placeholder="实际发生了什么？你的判断改变了吗？" /><button onClick={() => addReflection(item.id)}>完成复盘</button></div>}
                  </div>
                </article>;
              })}
            </div>}
          <p className="privacy">{user ? "记录已同步到你的账户；本机也保留一份即时副本。" : "当前为匿名体验，记录仅保存在这台设备。登录后可同步未来的新记录。"}</p>
        </section>
      )}

      <footer><span>观变 · 文化体验与决策参考</span><span>不替代医疗、法律、投资等专业意见</span><a href="https://ctext.org/book-of-changes" target="_blank" rel="noreferrer">原典来源</a></footer>
    </main>
  );
}
